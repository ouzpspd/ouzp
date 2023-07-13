import datetime
import re

from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from django.contrib import messages
from django.core.paginator import Paginator
from django.db.models import Q
from django.shortcuts import render, redirect, get_object_or_404
from django.core.cache import cache
from django.utils import timezone
from django.views import View
from django.core.exceptions import ObjectDoesNotExist
from django.views.generic import DetailView, FormView


from tickets.views import cache_check
from .models import OtpmSpp, OtpmTR
from tickets.parsing import in_work_otpm
from tickets.utils import flush_session_key

from .forms import OtpmPoolForm, CopperForm, OattrForm, SendSPPForm
from .parsing import ckb_parse, dispatch, for_tr_view, for_spp_view, save_comment, spp_send_to, send_to_mko, send_spp, \
    send_spp_check


def filter_otpm_search(search, technologs, group, status):
    """Данный метод фильтрует пул заявок по технологу, группе"""
    if status == 'В работе':
        if group is not None:
            spp_search = OtpmSpp.objects.filter(process=True, user__last_name__in=technologs, type_ticket=group)
        else:
            spp_search = OtpmSpp.objects.filter(process=True, user__last_name__in=technologs)
        result_search = None
    elif status == 'Отслеживается':
        if group is not None:
            spp_search = OtpmSpp.objects.filter(wait=True, user__last_name__in=technologs, type_ticket=group)
        else:
            spp_search = OtpmSpp.objects.filter(wait=True, user__last_name__in=technologs)
        result_search = None
    else:
        if group is not None:
            spp_search = OtpmSpp.objects.filter(Q(process=True) | Q(wait=True)).filter(user__last_name__in=technologs,
                                                                                          type_ticket=group)
        else:
            spp_search = OtpmSpp.objects.filter(Q(process=True) | Q(wait=True)).filter(user__last_name__in=technologs)
        tickets_spp_search = [i.ticket_k for i in spp_search]
        search = [i for i in search if i[0] not in tickets_spp_search]
        result_search = []
        query_technolog = True
        query_spp_ticket_group = True
        for x in search:
            query_technolog = [technolog for technolog in technologs if technolog in x[4]]
            if group:
                query_spp_ticket_group = group in x[-1]
            query = query_technolog and query_spp_ticket_group
            if query:
                result_search.append(x)
        if status == 'Не взята в работу':
            spp_search = None
    return result_search, spp_search


def cache_check_view(func):
    """Данный декоратор осуществляет проверку, что пользователь авторизован в АРМ, и в redis есть его логин/пароль,
     если данных нет, то перенаправляет на страницу Авторизация в ИС Холдинга"""
    def wrapper(self, request, *args, **kwargs):
        # Для CopperFormView пришлось переписать request на self.request, потому что в форме в объекте request
        # находится форма CopperForm и соответственно никакого user там нет. Вообще проверка авторизации в форме
        # наверно и ненужна пока там временно составляется шаблон.
        if not self.request.user.is_authenticated:
            return redirect(f'login/?next={self.request.path}')
        user = User.objects.get(username=self.request.user.username)
        credent = cache.get(user)
        if credent is None:
            response = redirect('login_for_service')
            response['Location'] += '?next={}'.format(self.request.path)
            return response
        return func(self, request, *args, **kwargs)
    return wrapper



class CredentialMixin:
    def get_credential(self, *args, **kwargs):
        user = User.objects.get(username=self.request.user.username)
        credent = cache.get(user)
        username = credent['username']
        password = credent['password']
        return username, password

    def redirect_to_login_for_service(self, *args, **kwargs):
        messages.warning(self.request, 'Нет доступа в ИС Холдинга')
        response = redirect('login_for_service')
        response['Location'] += '?next={}'.format(self.request.path)
        return response


class OtpmPoolView(CredentialMixin, View):
    """Пул задач ОТПМ"""
    @cache_check_view
    def get(self, request):
        username, password = super().get_credential(self)
        request = flush_session_key(request)
        queryset_user_group = User.objects.filter(
            userholdposition__hold_position=request.user.userholdposition.hold_position
        )
        if request.GET:
            form = OtpmPoolForm(request.GET)
            form.fields['technolog'].queryset = queryset_user_group
            if form.is_valid():
                technolog = None if form.cleaned_data['technolog'] is None else form.cleaned_data['technolog'].last_name
                group = None if form.cleaned_data['group'] == 'Все' else form.cleaned_data['group']
                status = None if form.cleaned_data['status'] == 'Все' else form.cleaned_data['status']
                initial_params = {}
                if technolog:
                    initial_params.update({'technolog': technolog})
                if group:
                    initial_params.update({'spp_ticket_group': group})
                if status:
                    initial_params.update({'status': status})
                context = {'otpmpoolform': form}
                search = in_work_otpm(username, password)
                if search[0] == 'Access denied':
                    return super().redirect_to_login_for_service(self)
                technologs = [user.last_name for user in queryset_user_group] if technolog is None else [technolog]
                output_search, spp_process = filter_otpm_search(search, technologs, group, status)
                context.update({'search': output_search, 'spp_process': spp_process})  # 'results': results
                return render(request, 'tickets/otpm.html', context)
        else:
            initial_params = dict({'technolog': request.user.last_name})
            form = OtpmPoolForm(initial=initial_params)
            form.fields['technolog'].queryset = queryset_user_group
            context = {
                'otpmpoolform': form
            }
            return render(request, 'tickets/otpm.html', context)



class CreateSppView(CredentialMixin, View):
    """Заявка СПП"""
    def create_or_update(self, spp_params, current_spp):
        if current_spp:
            current_spp.created = timezone.now()
            #current_spp.process = True
            current_spp.projected = False
            current_spp.save()
        else:
            current_spp = OtpmSpp()
            current_spp.dID = self.kwargs['dID']
            current_spp.ticket_k = spp_params['Заявка К']
            current_spp.type_ticket = spp_params['Тип заявки']
            current_spp.waited = timezone.now()
            current_spp.duration_process = datetime.timedelta(0)
            current_spp.duration_wait = datetime.timedelta(0)
        # current_spp.dID = self.kwargs['dID']
        # current_spp.ticket_k = spp_params['Заявка К']
        current_spp.client = spp_params['Клиент']
        # current_spp.type_ticket = spp_params['Тип заявки']
        current_spp.manager = spp_params['Менеджер']
        current_spp.technolog = spp_params['Технолог']
        current_spp.task_otpm = spp_params['Задача в ОТПМ']
        current_spp.des_tr = spp_params['Состав Заявки ТР']
        current_spp.services = spp_params['Перечень требуемых услуг']
        current_spp.comment = spp_params['Примечание']
        current_spp.created = timezone.now()
        # current_spp.waited = timezone.now()
        current_spp.process = True
        current_spp.uID = spp_params['uID']
        current_spp.trdifperiod = spp_params['trDifPeriod']
        current_spp.trcuratorphone = spp_params['trCuratorPhone']
        current_spp.evaluative_tr = spp_params['Оценочное ТР']
        user = User.objects.get(username=self.request.user.username)
        current_spp.user = user
        # current_spp.duration_process = datetime.timedelta(0)
        # current_spp.duration_wait = datetime.timedelta(0)
        current_spp.stage = self.request.GET.get('stage')
        current_spp.save()
        return current_spp

    @cache_check_view
    def get(self, request, dID):
        try:
            current_spp = OtpmSpp.objects.get(dID=dID)
        except ObjectDoesNotExist:
            current_spp = None

        if current_spp and current_spp.process:
            messages.warning(request, f'{current_spp.user.last_name} уже взял в работу')
            return redirect('otpm')
        username, password = super().get_credential(self)
        spp_params = for_spp_view(username, password, dID)

        if spp_params.get('Access denied'):
            return super().redirect_to_login_for_service(self)
        self.create_or_update(spp_params, current_spp)
        return redirect('spp_view_oattr', dID)

        # try:
        #     spp_params = None
        #     current_spp = OtpmSpp.objects.get(dID=dID)
        #     if current_spp.process:
        #         messages.warning(request, f'{current_spp.user.last_name} уже взял в работу')
        #         return redirect('otpm')
        # except ObjectDoesNotExist:
        #     username, password = super().get_credential(self)
        #     spp_params = for_spp_view(username, password, dID)
        #     if spp_params.get('Access denied') == 'Access denied':
        #         return super().redirect_to_login_for_service(self)
        #     current_spp = None
        # ticket_spp = self.create_or_update(spp_params, current_spp)
        # return redirect('spp_view_oattr', dID) #, ticket_spp.id)


class SppView(DetailView):
    model = OtpmSpp
    slug_field = 'dID'
    context_object_name = 'current_ticket_spp'
    template_name = 'oattr/spp_view_oattr.html'
    def get_object(self):
        current_ticket_spp = get_object_or_404(OtpmSpp, dID=self.kwargs['dID'])
        if self.request.GET.get('action') == 'wait' and current_ticket_spp.process:
            current_ticket_spp.wait = True
            current_ticket_spp.process = False
            current_ticket_spp.waited = timezone.now()
            current_ticket_spp.save()
        elif self.request.GET.get('action') == 'notwait' and current_ticket_spp.wait:
            current_ticket_spp.wait = False
            current_ticket_spp.process = True
            current_ticket_spp.duration_wait += timezone.now() - current_ticket_spp.waited
            current_ticket_spp.save()
        elif self.request.GET.get('action') == 'finish' and current_ticket_spp.process:
            current_ticket_spp.process = False
            current_ticket_spp.projected = True
            current_ticket_spp.duration_process += timezone.now() - current_ticket_spp.created
            current_ticket_spp.save()
        return current_ticket_spp

    # def get(self, request, dID):
    #     #request = flush_session_key(request)
    #     # request.session['ticket_spp_id'] = ticket_spp_id
    #     # request.session['dID'] = dID
    #     current_ticket_spp = get_object_or_404(OtpmSpp, dID=dID) # id=ticket_spp_id
    #
    #     context = {'current_ticket_spp': current_ticket_spp}
    #     return render(request, 'tickets/spp_view_oattr.html', context)

# def spp_view_oattr(request, dID, ticket_spp_id):
#     """Данный метод отображает html-страничку с данными заявки взятой в работу или обработанной. Данные о заявке
#      получает из БД"""
#     request = flush_session_key(request)
#     request.session['ticket_spp_id'] = ticket_spp_id
#     request.session['dID'] = dID
#     current_ticket_spp = get_object_or_404(OtpmSpp, dID=dID, id=ticket_spp_id)
#
#     context = {'current_ticket_spp': current_ticket_spp}
#     return render(request, 'tickets/spp_view_oattr.html', context)
#
#
# def remove_spp_process_oattr(request, ticket_spp_id):
#     """Данный метод удаляет заявку из обрабатываемых заявок"""
#     current_ticket_spp = OtpmSpp.objects.get(id=ticket_spp_id)
#     if current_ticket_spp.wait == True:
#         messages.warning(request, f'Заявка {current_ticket_spp.ticket_k} находится в ожидании')
#         return redirect('spp_view_oattr', current_ticket_spp.dID, current_ticket_spp.id)
#     current_ticket_spp.process = False
#     current_ticket_spp.projected = True
#     current_ticket_spp.duration_process += timezone.now() - current_ticket_spp.created
#     current_ticket_spp.save()
#     messages.success(request, 'Работа по заявке {} завершена'.format(current_ticket_spp.ticket_k))
#     return redirect('otpm')
#
#
# def remove_spp_wait_oattr(request, ticket_spp_id):
#     """Данный метод удаляет заявку из заявок в ожидании"""
#     current_ticket_spp = OtpmSpp.objects.get(id=ticket_spp_id)
#     current_ticket_spp.wait = False
#     current_ticket_spp.process = True
#     current_ticket_spp.duration_wait += timezone.now() - current_ticket_spp.waited
#     current_ticket_spp.save()
#     return redirect('spp_view_oattr', current_ticket_spp.dID) #, current_ticket_spp.id)
#
#
#
#
# def add_spp_wait_oattr(request, ticket_spp_id):
#     """Данный метод добавляет заявку в заявки в ожидании"""
#     current_ticket_spp = OtpmSpp.objects.get(id=ticket_spp_id)
#     current_ticket_spp.wait = True
#     current_ticket_spp.process = False
#     current_ticket_spp.waited = timezone.now()
#     current_ticket_spp.save()
#     return redirect('spp_view_oattr', current_ticket_spp.dID) #, current_ticket_spp.id)


def construct_tr(value_vars, template):
    result = []
    static_vars = {}
    hidden_vars = {}
    repr_string = {}
    repr_string['mounting_line'] = '- Смонтировать кабель %Тип кабеля% от %Точка от% до %Точка до%. ' +\
                                   '%Способ монтажа линии связи%. %Способ крепежа линии связи%.'
    multi_vars = {repr_string['mounting_line']:[]}
    count_lines = [key.strip('from_') for key in value_vars.keys() if key.startswith('from_')]
    for i in count_lines:
        static_vars[f'Тип кабеля {i}'] = value_vars.get(f'cable_{i}')
        static_vars[f'Точка от {i}'] = value_vars.get(f'from_{i}')
        static_vars[f'Точка до {i}'] = value_vars.get(f'to_{i}')
        static_vars[f'Способ монтажа линии связи {i}'] = value_vars.get(f'mounting_{i}')
        static_vars[f'Способ крепежа линии связи {i}'] = value_vars.get(f'fastening_{i}')
        multi_vars[repr_string['mounting_line']].append(f'- Смонтировать кабель %Тип кабеля {i}% от %Точка от {i}%' +
        f' до %Точка до {i}%. %Способ монтажа линии связи {i}%. %Способ крепежа линии связи {i}%.')

    if value_vars.get('no_exit'):
        hidden_vars['Внимание! ТР написано без выезда технолога.'] = 'Внимание! ТР написано без выезда технолога.'
    if value_vars.get('tech_reserve'):
        hidden_vars['- Оставить тех. запас.'] = '- Оставить тех. запас.'
    if value_vars.get('line_test'):
        hidden_vars['- Протестировать линию связи.'] = '- Протестировать линию связи.'
    static_vars['Доступ']= value_vars.get('access')
    static_vars['Согласование'] = value_vars.get('agreement')
    result.append(analyzer_vars(template, static_vars, hidden_vars, multi_vars))
    return result


@cache_check
def create_project_otu(request, trID):
    user = User.objects.get(username=request.user.username)
    credent = cache.get(user)
    username = credent['username']
    password = credent['password']
    id_otu = dispatch(username, password, trID)
    return redirect(f'https://tas.corp.itmh.ru/OtuProject/Edit/{id_otu}')


class CopperFormView(CredentialMixin, FormView):
    template_name = "oattr/copper.html"
    form_class = CopperForm
    success_url = "/otpm/data/"

    @cache_check_view
    def form_valid(self, form):
        username, password = super().get_credential(self)
        value_vars = dict(**form.cleaned_data)
        self.request.session['value_vars'] = value_vars
        return super().form_valid(form)

@cache_check
def data(request):
    user = User.objects.get(username=request.user.username)
    credent = cache.get(user)
    username = credent['username']
    password = credent['password']
    templates = ckb_parse(username, password)
    template = templates.get('Присоединение к СПД по медной линии связи.')
    value_vars = request.session.get('value_vars')
    construct = construct_tr(value_vars, template)
    result_otpm = ''.join(construct)
    extra_line = 2
    counter_str_oattr = result_otpm.count('\n') + extra_line
    request.session['result_otpm'] = result_otpm
    request.session['counter_str_oattr'] = counter_str_oattr
    return redirect('saved_data_oattr')


# @cache_check
# def copper_view(request):
#     user = User.objects.get(username=request.user.username)
#     credent = cache.get(user)
#     username = credent['username']
#     password = credent['password']
#     if request.method == 'POST':
#         form = CopperForm(request.POST)
#         #print(form.errors)
#
#         if form.is_valid():
#             value_vars = dict(**form.cleaned_data)
#             print('cleaned_data')
#             print(form.cleaned_data)
#             templates = ckb_parse(username, password)
#             template = templates.get('Присоединение к СПД по медной линии связи.')
#             construct = construct_tr(value_vars, template)
#             print('construct')
#             print(''.join(construct))
#
#     else:
#         form = CopperForm()
#     return render(request, "oattr/copper.html", { 'form': form })


def add_tr_oattr(request, dID, tID, trID):
    """Данный метод получает данные о ТР из СПП и добавляет ТР новой точки подключения в АРМ"""
    user = User.objects.get(username=request.user.username)
    credent = cache.get(user)
    username = credent['username']
    password = credent['password']
    tr_params = for_tr_view(username, password, dID, tID, trID)

    if tr_params.get('Access denied') == 'Access denied':
        messages.warning(request, 'Нет доступа в ИС Холдинга')
        response = redirect('login_for_service')
        response['Location'] += '?next={}'.format(request.path)
        return response
    else:
        ticket_tr_id = add_tr_to_db(dID, tID, trID, tr_params)
        request.session['ticket_tr_id'] = ticket_tr_id
        context = dict(**tr_params)
        if request.GET.get('action') == 'add':
            context.update({'dID': dID, 'tID': tID, 'trID': trID, 'action': 'add'})
        else:
            context.update({'dID': dID, 'tID': tID, 'trID': trID, 'action': 'edit'})
        return render(request, 'oattr/sppdata.html', context)


def add_tr_to_db(dID, tID, trID, tr_params):
    """Данный метод получает ID заявки СПП, ID ТР, параметры полученные с распарсенной страницы ТР, ID заявки в АРМ.
    создает ТР в АРМ и добавляет в нее данные. Возвращает ID ТР в АРМ"""
    ticket_spp = OtpmSpp.objects.get(dID=dID)
    if ticket_spp.children.filter(ticket_tr=trID):
        ticket_tr = ticket_spp.children.filter(ticket_tr=trID)[0]
    else:
        ticket_tr = OtpmTR()
        ticket_tr.ticket_k = ticket_spp#OtpmSpp.objects.get(dID=dID)
        ticket_tr.ticket_tr = trID
        ticket_tr.ticket_cp = tID
        ticket_tr.vID = tr_params['vID']
    ticket_tr.pps = tr_params['node']
    ticket_tr.info_tr = tr_params['info_tr']
    ticket_tr.services = tr_params['services_plus_desc']
    ticket_tr.address_cp = tr_params['address']
    ticket_tr.place_cp = tr_params['place_connection_point']
    ticket_tr.save()
    ticket_tr_id = ticket_tr.id
    return ticket_tr_id


class SendSppFormView(CredentialMixin, FormView):
    template_name = "oattr/send_spp.html"
    form_class = SendSPPForm
    success_url = "/"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        form = context['form']
        ticket_spp = get_object_or_404(OtpmSpp, dID=self.kwargs['dID'])
        common_types = [('Вернуть менеджеру', 'Вернуть менеджеру'), ('60', 'В работе ОС'), ('70', 'В работе ОРТР')]
        if ticket_spp.type_ticket == "ПТО":
            common_types.append(('84', 'Нормоконтроль и выпуск ТР'))
        else:
            common_types.append(('90', 'Утверждение ТР'))
        form.fields['send_to'].widget.choices = common_types
        context['form'] = form
        return context

    @cache_check_view
    def form_valid(self, form):
        ticket_spp = get_object_or_404(OtpmSpp, dID=self.kwargs['dID'])
        if ticket_spp.projected:
            messages.warning(self.request, f'Заявка {ticket_spp.ticket_k} уже спроектирована')
            return redirect('/')
        if ticket_spp.wait:
            messages.warning(self.request, f'Прежде чем отправлять заявку, необходимо ее вернуть из ожидания.')
            return redirect('send_spp', self.kwargs['dID'])
        username, password = super().get_credential(self)
        send_to = form.cleaned_data['send_to']
        comment = form.cleaned_data['comment']
        if send_to == 'Вернуть менеджеру':
            if comment:
                send_to_mko(username, password, ticket_spp, comment=comment)
                return redirect('/')
            else:
                messages.warning(self.request, f'Для возвращения в ОПП нужен комментарий')
                return redirect('send_spp', self.kwargs['dID'])
        if comment:
            status_code = save_comment(username, password, comment, ticket_spp)
            if status_code != 200:
                messages.warning(self.request, 'Не удалось добавить комментарий в СПП')
                return redirect('spp_view_oattr', self.kwargs['dID'])
        status_code = spp_send_to(username, password, ticket_spp, send_to)
        if status_code != 200:
            messages.warning(self.request, 'Не удалось отправить запрос в СПП')
            return redirect('spp_view_oattr', self.kwargs['dID'])
        ticket_spp.process = False
        ticket_spp.projected = True
        ticket_spp.duration_process += timezone.now() - ticket_spp.created
        ticket_spp.save()
        return super().form_valid(form)


def saved_data_oattr(request):
    """Данный метод отображает редактируемую html-страничку готового ТР"""
    if request.method == 'POST':
        oattrform = OattrForm(request.POST)
        if oattrform.is_valid():
            oattr_field = oattrform.cleaned_data['oattr_field']
            regex = '\n(.+)\r\n-{5,}\r\n'
            match_oattr_field = re.findall(regex, oattr_field)
            changable_titles = '\n'.join(match_oattr_field)
            ticket_tr_id = request.session['ticket_tr_id']
            ticket_tr = OtpmTR.objects.get(id=ticket_tr_id)
            ticket_tr.oattr = oattr_field
            ticket_tr.titles = changable_titles
            ticket_tr.save()
            extra_line = 2
            counter_str_oattr = ticket_tr.oattr.count('\n') + extra_line

            context = {
                'services_plus_desc': ticket_tr.services,
                'counter_str_oattr': counter_str_oattr,
                'oattrform': oattrform,
                'dID': ticket_tr.ticket_k.dID
            }
            return render(request, 'oattr/saved_data_oattr.html', context)
    else:
        ticket_tr_id = request.session.get('ticket_tr_id')
        ticket_tr = OtpmTR.objects.get(id=ticket_tr_id)
        if request.session.get('result_otpm'):
            counter_str_oattr = request.session['counter_str_oattr']
            result_otpm = request.session.get('result_otpm')
            ticket_tr.oattr = result_otpm
            ticket_tr.save()
            oattrform = OattrForm(initial={'oattr_field': ticket_tr.oattr})
        elif ticket_tr.oattr:
            oattrform = OattrForm(initial={'oattr_field': ticket_tr.oattr})
            extra_line = 2
            counter_str_oattr = ticket_tr.oattr.count('\n') + extra_line
        else:
            counter_str_oattr = 10
            oattrform = OattrForm()
        context = {
            'services_plus_desc': ticket_tr.services,
            'counter_str_oattr': counter_str_oattr,
            'oattrform': oattrform,
            'dID': ticket_tr.ticket_k.dID
        }
        return render(request, 'oattr/saved_data_oattr.html', context)


@cache_check
def save_spp(request):
    """Данный метод заполняет поля блока ОРТР в СПП готовым ТР"""
    user = User.objects.get(username=request.user.username)
    credent = cache.get(user)
    username = credent['username']
    password = credent['password']
    ticket_tr_id = request.session.get('ticket_tr_id')
    ticket_tr = OtpmTR.objects.get(id=ticket_tr_id)
    dID = ticket_tr.ticket_k.dID
    tID = ticket_tr.ticket_cp
    trID = ticket_tr.ticket_tr
    req_check = send_spp_check(username, password, dID, tID, trID)
    if req_check.status_code == 200:
        send_spp(username, password, dID, tID, trID, ticket_tr)
        return redirect(f'https://sss.corp.itmh.ru/dem_tr/dem_begin.php?dID={dID}&tID={tID}&trID={trID}')
    else:
        messages.warning(request, 'Нет доступа в ИС Холдинга')
        response = redirect('login_for_service')
        response['Location'] += '?next={}'.format(request.path)
        return response


def analyzer_vars(stroka, static_vars, hidden_vars, multi_vars):
    """Данный метод принимает строковую переменную, содержащую шаблон услуги со страницы
    Типовые блоки технического решения. Ищет в шаблоне блоки <> и сравнивает с аналогичными переменными из СПП.
    По средством доп. словаря формирует итоговый словарь содержащий блоки из СПП, которые
    есть в блоках шаблона(чтобы не выводить неактуальный блок) и блоки шаблона, которых не было в блоках
    из СПП(чтобы не пропустить неучтенный блок)
    Передаем переменные, т.к. переменные из глобал видятся, а из другой функции нет."""
    #    блок для определения необходимости частных строк <>
    list_var_lines = []
    list_var_lines_in = []
    regex_var_lines = '<(.+?)>'
    match_var_lines = re.finditer(regex_var_lines, stroka, flags=re.DOTALL)
    for i in match_var_lines:
        list_var_lines.append(i.group(1))
    for i in list_var_lines:
        if hidden_vars.get(i):
            stroka = stroka.replace('<{}>'.format(i), hidden_vars[i])
        else:
            stroka = stroka.replace('<{}>'.format(i), '  ')
    regex_var_lines_in = '\[(.+?)\]'
    match_var_lines_in = re.finditer(regex_var_lines_in, stroka, flags=re.DOTALL)
    for i in match_var_lines_in:
        list_var_lines_in.append(i.group(1))
    for i in list_var_lines_in:
        if hidden_vars.get(i):
            stroka = stroka.replace('[{}]'.format(i), i)
        else:
            stroka = stroka.replace('[{}]'.format(i), '  ')
    if len(list_var_lines) > 0:
        stroka = stroka.split('  \n')
        stroka = ''.join(stroka)
        stroka = stroka.replace('    ', ' ')
        if '\n\n\n' in stroka:
            stroka = stroka.replace('\n\n\n', '\n')
        elif '\n \n \n \n' in stroka:
            stroka = stroka.replace('\n \n \n \n', '\n\n')

    # блок заполнения повторяющихсся &&
    regex_var_lines = '&(.+?)&'
    match_var_lines = re.finditer(regex_var_lines, stroka, flags=re.DOTALL)
    list_var_lines = [i.group(1) for i in match_var_lines]
    for i in list_var_lines:
        if multi_vars.get(i):
            stroka = stroka.replace(f'&{i}&', '\n'.join(multi_vars[i]))
        else:
            stroka = stroka.replace(f'&{i}&', '  ')


    # блок для заполнения %%
    ckb_vars = {}
    dynamic_vars = {}
    regex = '%([\s\S]+?)%'
    match = re.finditer(regex, stroka, flags=re.DOTALL)  #
    for i in match:
        ckb_vars[i.group(1)] = '%'+i.group(1)+'%'
    for key in static_vars.keys():
        if key in ckb_vars:
            del ckb_vars[key]
            dynamic_vars[key] = static_vars[key]
    dynamic_vars.update(ckb_vars)
    for key in dynamic_vars.keys():
        stroka = stroka.replace('%{}%'.format(key), dynamic_vars[key])
        stroka = stroka.replace(' .', '.')
    stroka = ''.join([stroka[i] for i in range(len(stroka)) if i != len(stroka)-1 and not (stroka[i] == ' ' and stroka[i + 1] == ' ')])
    for i in [';', ',', ':', '.']:
        stroka = stroka.replace(' ' + i, i)
    return stroka