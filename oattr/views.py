import datetime

from django.contrib.auth.models import User
from django.contrib import messages
from django.db.models import Q
from django.shortcuts import render, redirect, get_object_or_404
from django.core.cache import cache
from django.utils import timezone
from django.views import View
from django.core.exceptions import ObjectDoesNotExist
from django.views.generic import DetailView

from .models import OtpmSpp
from tickets.parsing import in_work_otpm, for_spp_view
from tickets.utils import flush_session_key

from .forms import OtpmPoolForm, CopperForm


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
        if not request.user.is_authenticated:
            return redirect(f'login/?next={request.path}')
        user = User.objects.get(username=request.user.username)
        credent = cache.get(user)
        if credent is None:
            response = redirect('login_for_service')
            response['Location'] += '?next={}'.format(request.path)
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
            current_spp.process = True
            current_spp.save()
        else:
            current_spp = OtpmSpp()
            current_spp.dID = self.kwargs['dID']
            current_spp.ticket_k = spp_params['Заявка К']
            current_spp.client = spp_params['Клиент']
            current_spp.type_ticket = spp_params['Тип заявки']
            current_spp.manager = spp_params['Менеджер']
            current_spp.technolog = spp_params['Технолог']
            current_spp.task_otpm = spp_params['Задача в ОТПМ']
            current_spp.des_tr = spp_params['Состав Заявки ТР']
            current_spp.services = spp_params['Перечень требуемых услуг']
            current_spp.comment = spp_params['Примечание']
            current_spp.created = timezone.now()
            current_spp.waited = timezone.now()
            current_spp.process = True
            current_spp.uID = spp_params['uID']
            current_spp.trdifperiod = spp_params['trDifPeriod']
            current_spp.trcuratorphone = spp_params['trCuratorPhone']
            current_spp.evaluative_tr = spp_params['Оценочное ТР']
            user = User.objects.get(username=self.request.user.username)
            current_spp.user = user
            current_spp.duration_process = datetime.timedelta(0)
            current_spp.duration_wait = datetime.timedelta(0)
            current_spp.stage = self.request.GET.get('stage')
            current_spp.save()
        return current_spp

    @cache_check_view
    def get(self, request, dID):
        try:
            spp_params = None
            current_spp = OtpmSpp.objects.get(dID=dID)
            if current_spp.process:
                messages.warning(request, f'{current_spp.user.last_name} уже взял в работу')
                return redirect('otpm')
        except ObjectDoesNotExist:
            username, password = super().get_credential(self)
            spp_params = for_spp_view(username, password, dID)
            if spp_params.get('Access denied') == 'Access denied':
                return super().redirect_to_login_for_service(self)
            current_spp = None
        ticket_spp = self.create_or_update(spp_params, current_spp)
        return redirect('spp_view_oattr', dID) #, ticket_spp.id)


class SppView(DetailView):
    model = OtpmSpp
    slug_field = 'dID'
    context_object_name = 'current_ticket_spp'
    template_name = 'tickets/spp_view_oattr.html'
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


def copper_view(request):
    if request.method == 'POST':
        form = CopperForm(request.POST) #, extra=request.POST.get('ext_field_count'))
        print('errors')
        print(form.errors)
        if form.is_valid():
            print("valid!")
            print(form.cleaned_data)

    else:
        if request.GET:
            print('request')
            print(request)
        form = CopperForm()
        print('get')
    return render(request, "oattr/copper.html", { 'copper_form': form })

