import datetime
import re

from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib.auth.models import User
from django.contrib import messages
from django.db.models import Q
from django.http import QueryDict, HttpResponseServerError
from django.shortcuts import render, redirect, get_object_or_404
from django.core.cache import cache
from django.template import loader
from django.urls import reverse
from django.utils import timezone
from django.views import View
from django.core.exceptions import ObjectDoesNotExist
from django.views.generic import DetailView, FormView

from tickets.models import TR
from .models import OtpmSpp, OtpmTR
from tickets.utils import flush_session_key, get_user_credential_cordis

from .forms import OtpmPoolForm, CopperForm, OattrForm, SendSPPForm, ServiceForm, AddressForm
from .parsing import ckb_parse, get_or_create_otu, for_tr_view, for_spp_view, save_comment, spp_send_to, send_to_mko, send_spp, \
    send_spp_check, in_work_otpm, get_spp_stage, get_spp_addresses, get_spp_addresses, get_nodes_by_address, \
    get_initial_node, get_tentura, Tentura, Specification
from .utils import add_tag_for_services, construct_tr


def handler500(request, *args, **argv):
    return render(request, '500.html', status=500)


def filter_otpm_search(search, technologs, group, status):
    """Данный метод фильтрует пул заявок по технологу, группе"""
    if status == 'В работе':
        if group is not None:
            spp_search = OtpmSpp.objects.filter(process=True, user__last_name__in=technologs, type_ticket=group)
        else:
            spp_search = OtpmSpp.objects.filter(process=True, user__last_name__in=technologs)
    elif status == 'Отслеживается':
        if group is not None:
            spp_search = OtpmSpp.objects.filter(wait=True, user__last_name__in=technologs, type_ticket=group)
        else:
            spp_search = OtpmSpp.objects.filter(wait=True, user__last_name__in=technologs)
    else:
        if group is not None:
            spp_search = OtpmSpp.objects.filter(Q(process=True) | Q(wait=True)).filter(user__last_name__in=technologs,
                                                                                          type_ticket=group)
        else:
            spp_search = OtpmSpp.objects.filter(Q(process=True) | Q(wait=True)).filter(user__last_name__in=technologs)
    tickets_spp_db = [i.ticket_k for i in spp_search]
    tickets_in_search = [i[0] for i in search]

    search = [i for i in search if i[0] not in tickets_spp_db]

    tickets_missing = [i for i in tickets_spp_db if i not in tickets_in_search]
    missing = [i for i in spp_search if i.ticket_k in tickets_missing]
    spp_search = [i for i in spp_search if i not in missing]
    result_search = []
    if status not in ['В работе', 'Отслеживается']:
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
        missing = None
    return result_search, spp_search, missing


# def cache_check_view(func):
#     """Данный декоратор осуществляет проверку, что пользователь авторизован в АРМ, и в redis есть его логин/пароль,
#      если данных нет, то перенаправляет на страницу Авторизация в ИС Холдинга"""
#     def wrapper(self, request, *args, **kwargs):
#         # Для CopperFormView пришлось переписать request на self.request, потому что в форме в объекте request
#         # находится форма CopperForm и соответственно никакого user там нет. Вообще проверка авторизации в форме
#         # наверно и ненужна пока там временно составляется шаблон.
#         if not self.request.user.is_authenticated:
#             return redirect(f'login/?next={self.request.path}')
#         user = User.objects.get(username=self.request.user.username)
#         credent = cache.get(user)
#         if credent is None:
#             response = redirect('login_for_service')
#             response['Location'] += '?next={}'.format(self.request.path)
#             return response
#         return func(self, request, *args, **kwargs)
#     return wrapper



class CredentialMixin:
    def get_credential(self, *args, **kwargs):
        user = User.objects.get(username=self.request.user.username)
        username, password = get_user_credential_cordis(user)
        return (username, password)


class OtpmPoolView(CredentialMixin, LoginRequiredMixin, View):
    """Пул задач ОТПМ"""
    login_url = '/login/'

    def get(self, request):
        username, password = super().get_credential(self)
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
                if not isinstance(search, list):
                    return render(request, 'base.html', {'my_message': 'Нет доступа в СПП'})
                technologs = [user.last_name for user in queryset_user_group] if technolog is None else [technolog]
                output_search, spp_process, missing = filter_otpm_search(search, technologs, group, status)
                context.update({'search': output_search,
                                'spp_process': spp_process,
                                'missing': missing})
                return render(request, 'oattr/pool_oattr.html', context)
        else:
            initial_params = dict({'technolog': request.user.last_name})
            form = OtpmPoolForm(initial=initial_params)
            form.fields['technolog'].queryset = queryset_user_group
            context = {
                'otpmpoolform': form
            }
            return render(request, 'oattr/pool_oattr.html', context)


class CreateSppView(CredentialMixin, View):
    """Заявка СПП"""
    def create_or_update(self, spp_params, current_spp):
        if current_spp:
            current_spp.created = timezone.now()
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
        current_spp.client = spp_params['Клиент']
        current_spp.manager = spp_params['Менеджер']
        current_spp.technolog = spp_params['Технолог']
        current_spp.task_otpm = spp_params['Задача в ОТПМ']
        current_spp.des_tr = spp_params['Состав Заявки ТР']
        current_spp.services = spp_params['Перечень требуемых услуг']
        current_spp.comment = spp_params['Примечание']
        current_spp.created = timezone.now()
        current_spp.process = True
        current_spp.uID = spp_params['uID']
        current_spp.trdifperiod = spp_params['trDifPeriod']
        current_spp.trcuratorphone = spp_params['trCuratorPhone']
        current_spp.difficulty = spp_params['Сложность']
        user = User.objects.get(username=self.request.user.username)
        current_spp.user = user
        current_spp.stage = self.request.GET.get('stage')
        current_spp.save()
        return current_spp


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
            return render(request, 'base.html', {'my_message': 'Нет доступа в СПП'})
        self.create_or_update(spp_params, current_spp)
        return redirect('spp_view_oattr', dID)


class SppView(DetailView):
    """Информация заявки СПП гггг_ннннн"""
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
            tickets_tr = current_ticket_spp.children.all()
            for ticket_tr in tickets_tr:
                if self.request.session.get(ticket_tr.ticket_tr):
                    del self.request.session[ticket_tr.ticket_tr]
        return current_ticket_spp





class CreateProjectOtuView(CredentialMixin, View):
    #@cache_check_view
    def get(self, request, trID):
        username, password = super().get_credential(self)
        id_otu = get_or_create_otu(username, password, trID)
        return redirect(f'https://tas.corp.itmh.ru/OtuProject/Edit/{id_otu}')


class CopperFormView(CredentialMixin, FormView):
    template_name = "oattr/copper.html"
    form_class = CopperForm

    # @cache_check_view
    # def dispatch(self, *args, **kwargs):
    #     """Используется для проверки credential"""
    #     return super().dispatch(*args, **kwargs)

    #@cache_check_view
    def form_valid(self, form):
        username, password = super().get_credential(self)
        value_vars = dict(**form.cleaned_data)
        session_tr_id = self.request.session[str(self.kwargs['trID'])]
        session_tr_id.update({'value_vars': value_vars})
        self.request.session[str(self.kwargs['trID'])] = session_tr_id
        return super().form_valid(form)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        ticket_tr = get_object_or_404(OtpmTR, ticket_tr=self.kwargs['trID'])
        context['ticket_tr'] = ticket_tr
        return context

    def get_success_url(self, **kwargs):
        return reverse('otpm_data', kwargs={'trID': self.kwargs['trID']})
        #return reverse('otpm_service', kwargs={'trID': self.kwargs['trID']})



# class ServiceFormView(CredentialMixin, FormView):
#     template_name = "oattr/services.html"
#     form_class = ServiceForm
#
#     @cache_check_view
#     def dispatch(self, *args, **kwargs):
#         """Используется для проверки credential"""
#         return super().dispatch(*args, **kwargs)
#
#     @cache_check_view
#     def form_valid(self, form):
#         service_vars = dict(**form.cleaned_data)
#         session_tr_id = self.request.session[str(self.kwargs['trID'])]
#         session_tr_id.update({'service_vars': service_vars})
#         self.request.session[str(self.kwargs['trID'])] = session_tr_id
#         return super().form_valid(form)
#
#     def get_context_data(self, **kwargs):
#         context = super().get_context_data(**kwargs)
#         ticket_tr = get_object_or_404(OtpmTR, ticket_tr=self.kwargs['trID'])
#         #services = [service for service in ticket_tr.services if ('Интернет' or 'Хот-спот') not in service]
#         services = {}
#
#
#         tags_services = {'phone': 'Телефон', 'video': 'Видеонаблюдение', 'lvs': 'ЛВС', 'hotspot': 'Хот-спот'}
#         for key, value in tags_services.items():
#             for service in ticket_tr.services:
#                 if service.startswith(value):
#                     if services.get(key):
#                         services[key] = services.get(key) + ', ' + service[len(value):].capitalize()
#                     else:
#                         services.update({key: service})
#
#         context['ticket_tr'] = ticket_tr
#         context['services'] = services
#         return context
#
#     def get_success_url(self, **kwargs):
#         return reverse('otpm_data', kwargs={'trID': self.kwargs['trID']})



def data(request, trID):
    user = User.objects.get(username=request.user.username)
    username, password = get_user_credential_cordis(user)
    templates = ckb_parse(username, password)

    session_tr_id = request.session.get(str(trID), {})
    value_vars = session_tr_id.get('value_vars')
    service_vars = session_tr_id.get('service_vars')
    ticket_tr = OtpmTR.objects.get(ticket_tr=trID)
    construct = construct_tr(value_vars, service_vars, templates, ticket_tr)
    result_otpm = '\n\n'.join(construct)
    extra_line = 2
    counter_str_oattr = result_otpm.count('\n') + extra_line
    session_tr_id.update({'result_otpm': result_otpm, 'counter_str_oattr': counter_str_oattr})
    request.session[str(trID)] = session_tr_id
    return redirect('saved_data_oattr', trID)




def tentura(request):
    user = User.objects.get(username=request.user.username)
    username, password = get_user_credential_cordis(user)
    #get_tentura(username, password)
    tentura = Tentura(username, password, 39203)
    status = tentura.check_active_project_for_user() #connection(username, password, 39203)
    print(status)
    project_context = tentura.get_project_context()
    print(project_context)
    matched_addresses = tentura.get_matched_addresses('Куйбышева, 10')
    print(matched_addresses)
    id_address = 2170
    construction_center = tentura.get_construction_center(2170)
    print(construction_center)
    set_ioc_filter = tentura.set_ioc_filter(project_context)
    print(set_ioc_filter)
    id_gis_objects = tentura.get_id_gis_objects(project_context, id_address)

    gis_objects = tentura.get_params_binded_objects(id_gis_objects, project_context)
    for k, v in gis_objects.items():
        print(k)
        print(v.get('name'))

    gis_object = gis_objects.get(70252)

    result = tentura.add_csp(id_address, 'Куйбышева, 10')
    print(result)
    # result = tentura.add_node(gis_object)
    # print(result)


def specific(request):
    user = User.objects.get(username=request.user.username)
    username, password = get_user_credential_cordis(user)
    otu_project_id = 39421 #37859 #39203
    specification = Specification(username, password, otu_project_id)
    cookie = specification.authenticate()

    csp_resources = [
        {'Name': "# [СПП] [Коннектор RJ-45 (одножильный)]", 'Amount': 1},
    ]

    # prices_sku = specification.get_resource_price_sku(cookie, csp_resources)
    # prices_tao = specification.get_resource_price_tao(, csp_resources)
    # prices = prices_sku | prices_taocookie
    # print(prices)
    inventory_object_id = 131124 #128874
    specification.set_resources(cookie, inventory_object_id, csp_resources, update=False)

    pps_resources = [
        {'Name': "# [СПП] [Коннектор RJ-45 (одножильный)]", 'Amount': 3},
        {'Name': '# [СПП] [Кабель UTP кат.5е 2 пары (внутренний)]', 'Amount': 90},
        {'Name': 'Выезд автомобиля В2В ВОЛС', 'Amount': 1},
        {'Name': 'Присоединение B2B UTP', 'Amount': 1},
    ]

    inventory_object_id = 2268
    specification.set_resources(cookie, inventory_object_id, pps_resources, update=False)



class CreateTrView(CredentialMixin, View):
    """Информация ТР XXXXX"""
    def create_or_update(self, dID, tID, trID, tr_params):
        ticket_spp = OtpmSpp.objects.get(dID=dID)
        if ticket_spp.children.filter(ticket_tr=trID):
            ticket_tr = ticket_spp.children.filter(ticket_tr=trID)[0]
        else:
            ticket_tr = OtpmTR()
            ticket_tr.ticket_k = ticket_spp
            ticket_tr.ticket_tr = trID
            ticket_tr.ticket_cp = tID
        ticket_tr.vID = tr_params['vID']
        ticket_tr.pps = tr_params['node']
        ticket_tr.info_tr = tr_params['info_tr']
        ticket_tr.services = tr_params['services_plus_desc']
        ticket_tr.address_cp = tr_params['address']
        ticket_tr.place_cp = tr_params['place_connection_point']
        ticket_tr.aid = tr_params['aid']
        ticket_tr.tr_without_os = tr_params['tr_without_os']
        ticket_tr.tr_complex_access = tr_params['tr_complex_access']
        ticket_tr.tr_complex_equip = tr_params['tr_complex_equip']
        ticket_tr.tr_turn_off = tr_params['tr_turn_off']
        ticket_tr.tr_complex_access_input = tr_params.get('tr_complex_access_input')
        ticket_tr.tr_complex_equip_input = tr_params.get('tr_complex_equip_input')
        ticket_tr.tr_turn_off_input = tr_params.get('tr_turn_off_input')

        ticket_tr.save()
        ticket_tr_id = ticket_tr.id     # Временно вернул пока в view.data не переделана на использование tr_id в url
        return ticket_tr_id     # Временно вернул пока в view.data не переделана на использование tr_id в url

    #@cache_check_view
    def get(self, request, dID, tID, trID):
        username, password = super().get_credential(self)
        tr_params = for_tr_view(username, password, dID, tID, trID)
        if tr_params.get('Access denied'):
            return render(request, 'base.html', {'my_message': 'Нет доступа в СПП'})

        ticket_tr_id = self.create_or_update(dID, tID, trID, tr_params) # Временно вернул пока в view.data не переделана на использование tr_id в url
        request.session['ticket_tr_id'] = ticket_tr_id # Временно вернул пока в view.data не переделана на использование tr_id в url
        request.session[self.kwargs['trID']] = {}
        session_tr_id = request.session[(self.kwargs['trID'])]
        session_tr_id.update({'action': request.GET.get('action')})
        request.session[(self.kwargs['trID'])] = session_tr_id
        context = dict(**tr_params)
        if request.GET.get('action') == 'add':
            context.update({'dID': dID, 'tID': tID, 'trID': trID, 'action': 'add'})
            #request.session[str(self.kwargs['trID'])].update({'action': request.GET.get('action')})
        elif request.GET.get('action') == 'edit':
            context.update({'dID': dID, 'tID': tID, 'trID': trID, 'action': 'edit'})
            #request.session[str(self.kwargs['trID'])].update({'action': request.GET.get('action')})
        return render(request, 'oattr/sppdata.html', context)


class SendSppFormView(CredentialMixin, FormView):
    template_name = "oattr/send_spp.html"
    form_class = SendSPPForm
    success_url = "/"

    #@cache_check_view
    # def dispatch(self, *args, **kwargs):
    #     """Используется для проверки credential"""
    #     return super().dispatch(*args, **kwargs)


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
        username, password = super().get_credential(self)
        spp_stage = get_spp_stage(username, password, self.kwargs['dID'])
        context['spp_stage'] = spp_stage
        return context

    #@cache_check_view
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
        tickets_tr = ticket_spp.children.all()
        for ticket_tr in tickets_tr:
            if self.request.session.get(ticket_tr.ticket_tr):
                del self.request.session[ticket_tr.ticket_tr]
        return super().form_valid(form)


def saved_data_oattr(request, trID):
    """Данный метод отображает редактируемую html-страничку готового ТР"""
    if request.method == 'POST':
        oattrform = OattrForm(request.POST)
        if oattrform.is_valid():
            oattr_field = oattrform.cleaned_data['oattr_field']
            regex = '\n(.+)\r\n-{5,}\r\n'
            match_oattr_field = re.findall(regex, oattr_field)
            changable_titles = '\n'.join(match_oattr_field)
            ticket_tr = OtpmTR.objects.get(ticket_tr=trID)
            ticket_tr.oattr = oattr_field
            ticket_tr.titles = changable_titles
            ticket_tr.save()
            extra_line = 2
            counter_str_oattr = ticket_tr.oattr.count('\n') + extra_line

            context = {
                'services_plus_desc': ticket_tr.services,
                'counter_str_oattr': counter_str_oattr,
                'oattrform': oattrform,
                'dID': ticket_tr.ticket_k.dID,
                'trID': trID
            }
            return render(request, 'oattr/saved_data_oattr.html', context)
    else:
        session_tr_id = request.session.get(str(trID))
        ticket_tr = OtpmTR.objects.get(ticket_tr=trID)
        if session_tr_id.get('result_otpm'):
            counter_str_oattr = session_tr_id.get('counter_str_oattr')
            result_otpm = session_tr_id.get('result_otpm')
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
            'dID': ticket_tr.ticket_k.dID,
            'trID': trID,
            'ticket_tr': ticket_tr
        }
        return render(request, 'oattr/saved_data_oattr.html', context)


def save_spp(request):
    """Данный метод заполняет поля блока ОТПМ в СПП готовым ТР"""
    user = User.objects.get(username=request.user.username)
    username, password = get_user_credential_cordis(user)
    ticket_tr_id = request.session.get('ticket_tr_id')
    ticket_tr = OtpmTR.objects.get(id=ticket_tr_id)
    dID = ticket_tr.ticket_k.dID
    tID = ticket_tr.ticket_cp
    trID = ticket_tr.ticket_tr
    req_check = send_spp_check(username, password, dID, tID, trID)
    if req_check.status_code == 200:
        send_spp(username, password, ticket_tr)
        return redirect(f'https://sss.corp.itmh.ru/dem_tr/dem_begin.php?dID={dID}&tID={tID}&trID={trID}')
    return render(request, 'base.html', {'my_message': 'Нет доступа в СПП'})


class AddressView(CredentialMixin, View):
    """Поиск адресов в СПП"""
    #@cache_check_view
    def get(self, request, department, trID):
        username, password = super().get_credential(self)
        if department == 'ortr':
            ticket_tr = TR.objects.filter(ticket_tr=trID).last()
        else:
            ticket_tr = OtpmTR.objects.get(ticket_tr=trID)
        if request.GET:
            form = AddressForm(request.GET)
            if form.is_valid():
                city = form.cleaned_data['city']
                street = None if not form.cleaned_data['street'] else form.cleaned_data['street']
                house = None if not form.cleaned_data['house'] else form.cleaned_data['house']

                search = get_spp_addresses(username, password, city, street, house)
                context = {'addressform': form, 'ticket_tr': ticket_tr, 'search': search, 'department': department}
                #get_nodes_by_address(username, password, 154)

                return render(request, 'oattr/addresses.html', context)
        else:
            form = AddressForm()

            search = get_initial_node(username, password, ticket_tr)
            context = {'addressform': form, 'ticket_tr': ticket_tr, 'search': search, 'department': department}
            return render(request, 'oattr/addresses.html', context)


class SelectNodeView(CredentialMixin, View):
    """Выбор узла на адресе для добавления в ТР"""
    #@cache_check_view
    def get(self, request, department, trID, aid):
        username, password = super().get_credential(self)
        if department == 'ortr':
            ticket_tr = TR.objects.filter(ticket_tr=trID).last()
        else:
            ticket_tr = OtpmTR.objects.get(ticket_tr=trID)
        search = get_nodes_by_address(username, password, aid)

        context = {
            'search': search,
            'ticket_tr': ticket_tr,
            'department': department
        }
        return render(request, 'oattr/select_node.html', context)


class UpdateNodeView(CredentialMixin, View):
    """Выбор узла на адресе для добавления в ТР"""
    #@cache_check_view
    def get(self, request, department, trID, vid):
        username, password = super().get_credential(self)
        if department == 'ortr':
            ticket_tr = TR.objects.filter(ticket_tr=trID).last()
            url = reverse('add_tr', kwargs={'dID': ticket_tr.ticket_k.dID, 'tID': ticket_tr.ticket_cp, 'trID': trID})
        else:
            ticket_tr = OtpmTR.objects.get(ticket_tr=trID)
            action = request.session.get(str(self.kwargs['trID'])).get('action')
            query_dictionary = QueryDict('', mutable=True)
            query_dictionary.update({'action': action})
            url = f"{reverse('add_tr_oattr', kwargs={'dID': ticket_tr.ticket_k.dID, 'tID': ticket_tr.ticket_cp, 'trID': trID})}?{query_dictionary.urlencode()}"
        ticket_tr.vID = vid
        ticket_tr.save()
        #send_node_to_spp(username, password, ticket_tr)
        send_spp(username, password, ticket_tr, department)

        # session_tr_id.update({'action': request.GET.get('action')})
        # request.session[(self.kwargs['trID'])] = session_tr_id
        return redirect(url)




