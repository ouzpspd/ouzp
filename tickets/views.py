import requests
from django.contrib.auth.mixins import UserPassesTestMixin, LoginRequiredMixin
from django.shortcuts import render, redirect, get_object_or_404
from django.urls import reverse
from django.views import View
from django.views.generic import DetailView, FormView, ListView
from urllib3.exceptions import NewConnectionError

from oattr.forms import UserRegistrationForm, UserLoginForm, AuthForServiceForm
from oattr.parsing import get_or_create_otu, Tentura, Specification, BundleSpecItems, get_specication_resources
from .models import TR, SPP, OrtrTR
from .forms import LinkForm, HotspotForm, PhoneForm, ItvForm, ShpdForm, \
    VolsForm, CopperForm, WirelessForm, CswForm, CksForm, PortVKForm, PortVMForm, VideoForm, LocalForm, \
    OrtrForm, ContractForm, ListResourcesForm, \
    PassServForm, ChangeServForm, ChangeParamsForm, ListJobsForm, ChangeLogShpdForm, \
    TemplatesHiddenForm, TemplatesStaticForm, ListContractIdForm, ExtendServiceForm, PassTurnoffForm, SearchTicketsForm, \
    PprForm, AddResourcesPprForm, AddCommentForm, TimeTrackingForm, RtkForm, SppDataForm, PpsForm, PassVideoForm

from oattr.models import OtpmSpp


import logging
from django.contrib import messages
from django.contrib.auth import login, logout
from django.contrib.auth.models import User
from django.contrib.auth.decorators import login_required
from django.db.models import Q
from django.http import Http404, HttpResponse, JsonResponse

from django.contrib.auth import update_session_auth_hash
from django.contrib.auth.forms import PasswordChangeForm
from django.core.paginator import Paginator
from django.utils import timezone
from django.contrib.auth.decorators import user_passes_test


import xlwt
from django.db.models import F, Func, Value, CharField
from django.utils import timezone
import datetime
from django.core.exceptions import ObjectDoesNotExist
from django.forms import formset_factory

from .parsing import *
from .parsing import _parsing_vgws_by_node_name
from .parsing import _parsing_model_and_node_client_device_by_device_name
from .parsing import _get_chain_data
from .parsing import _counter_line_services

from .constructing_tr import *
from .constructing_tr import _separate_services_and_subnet_dhcp
from .constructing_tr import _titles
from .constructing_tr import _passage_services

from .utils import *
from .utils import _replace_wda_wds
from .utils import _get_downlink
from .utils import _get_vgw_on_node
from .utils import _get_node_device
from .utils import _get_extra_node_device
from .utils import _get_uplink
from .utils import _get_extra_selected_ono
from .utils import _get_all_chain
from .utils import _tag_service_for_new_serv
from .utils import _readable

from django import template
register = template.Library()


logger = logging.getLogger(__name__)


def registration(request):
    """Данный метод отвечает за регистрацию пользователей в АРМ"""
    if request.method == 'POST':
        form = UserRegistrationForm(request.POST)
        if form.is_valid():
            user = form.save()
            login(request, user)
            messages.success(request, 'Вы успешно зарегистрировались')
            return redirect('/')
        else:
            messages.error(request, 'Ошибка регистрации')
    else:
        form = UserRegistrationForm()
    return render(request, 'tickets/register.html', {'form': form})


def user_login(request):
    """Данный метод отвечает за авторизацию пользователей в АРМ. Если авторизация запрашивается со страницы требующей
    авторизацию, то после авторизации происходит перенаправление на эту страницу. Если пользователь самостоятельно переходит
    на страницу авторизации, то перенаправление осуществляется в его Личное пространство"""
    if request.method == 'POST':
        form = UserLoginForm(data=request.POST)
        if form.is_valid():
            user = form.get_user()
            login(request, user)
            next = request.GET.get('next', '/')
            if next == '/':
                return redirect('/')
            else:
                return redirect(request.GET['next'])
    else:
        form = UserLoginForm()
    return render(request, 'tickets/login.html', {'form': form})


def user_logout(request):
    """Данный метод отвечает за выход авторизованного пользователя"""
    logout(request)
    return redirect('login')


def change_password(request):
    """Данный метод отображает html страничку с формой для изменения пароля пользователя в АРМ"""
    if request.method == 'POST':
        form = PasswordChangeForm(request.user, request.POST)
        if form.is_valid():
            user = form.save()
            update_session_auth_hash(request, user)
            messages.success(request, 'Ваш пароль обновлен!')
            return redirect('change_password')
        else:
            messages.error(request, 'Ошибка')
    else:
        form = PasswordChangeForm(request.user)
    return render(request, 'tickets/change_password.html', {
        'form': form
    })


@login_required(login_url='login/')
def private_page(request):
    """Данный метод в Личном пространстве пользователя отображает все задачи этого пользователя"""
    #request = flush_session_key(request)
    if request.user.groups.filter(name='Сотрудники ОАТТР').exists():
        spp_success = OtpmSpp.objects.filter(user=request.user).order_by('-created')
    else:
        spp_success = SPP.objects.filter(user=request.user).order_by('-created')
    paginator = Paginator(spp_success, 50)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    return render(request, 'tickets/private_page.html', {'page_obj': page_obj})


def group_check_ouzp(user):
    return user.groups.filter(name='Сотрудники ОУЗП').exists()

def group_check_mko(user):
    return user.groups.filter(name='Менеджеры').exists()


def permission_check(perm_groups=[]):
    """Проверка пользователя в составе перечисленных групп"""
    def decorator(func):
        def wrapper(request, *args, **kwargs):
            if not request.user.is_authenticated:
                return redirect(f'/login/?next={request.path}')
            user = User.objects.get(username=request.user.username)
            if not [perm_group for perm_group in perm_groups if user.groups.filter(name=perm_group).exists()]:
                return HttpResponse("Forbidden",
                                    content_type="application/json", status=403)
            return func(request, *args, **kwargs)
        return wrapper
    return decorator


@permission_check(["Сотрудники ОУЗП"])
def ortr(request):
    """Данный метод перенаправляет на страницу Новые заявки, которые находятся в пуле ОРТР/в работе.
        1. Получает данные от redis о логин/пароле
        2. Получает данные о всех заявках в пуле ОРТР с помощью метода in_work_ortr
        3. Получает данные о всех заявках которые уже находятся в БД(в работе)
        4. Удаляет из списка в пуле заявки, которые есть в работе
        5. Формирует итоговый список всех заявок в пуле/в работе"""
    user = User.objects.get(username=request.user.username)
    username, password = get_user_credential_cordis(user)
    search = in_work_ortr(username, password)
    if not isinstance(search, list):
        return render(request, 'base.html', {'my_message': 'Нет доступа в СПП'})
    list_search = []
    for i in search:
        list_search.append(i[0])
    spp_proc = SPP.objects.filter(process=True)
    list_spp_proc = []
    for i in spp_proc:
        list_spp_proc.append(i.ticket_k)
    spp_wait = SPP.objects.filter(wait=True)
    list_spp_wait = []
    return_from_wait = []
    for i in spp_wait:
        if i.ticket_k or i.ticket_k + ' ПТО' in list_search:
            list_spp_wait.append(i.ticket_k)
        else:
            i.wait = False
            i.save()
            return_from_wait.append(i.ticket_k)
    list_search_rem = []
    for i in list_spp_proc:
        for index_j in range(len(list_search)):
            if i in list_search[index_j]:
                list_search_rem.append(index_j)
    for i in list_spp_wait:
        for index_j in range(len(list_search)):
            if i in list_search[index_j]:
                list_search_rem.append(index_j)
    search[:] = [x for i, x in enumerate(search) if i not in list_search_rem]
    if return_from_wait:
        messages.success(request, 'Заявка {} удалена из ожидания'.format(', '.join(return_from_wait)))
    return render(request, 'tickets/ortr.html', {'search': search, 'spp_process': spp_proc})


@permission_check(["Сотрудники ОУЗП"])
def commercial(request):
    """Данный метод перенаправляет на страницу Коммерческие заявки, которые находятся в работе ОРТР.
    1. Получает данные от redis о логин/пароле
    2. Получает данные о коммерческих заявках в пуле ОРТР с помощью метода in_work_ortr
    3. Получает данные о коммерческих заявках которые уже находятся в БД(в работе/в ожидании)
    4. Удаляет из списка в пуле заявки, которые есть в работе/в ожидании
    5. Формирует итоговый список задач в пуле и в работе"""
    user = User.objects.get(username=request.user.username)
    username, password = get_user_credential_cordis(user)
    search = in_work_ortr(username, password)
    if not isinstance(search, list):
        return render(request, 'base.html', {'my_message': 'Нет доступа в СПП'})
    list_search = []
    search[:] = [x for x in search if 'ПТО' not in x[0]]
    for i in search:
        if 'ПТО' not in i[0]:
            list_search.append(i[0])
    spp_process = SPP.objects.filter(Q(process=True) | Q(wait=True)).filter(type_ticket='Коммерческая')
    list_spp_process = []
    for i in spp_process:
        list_spp_process.append(i.ticket_k)
    list_search_rem = []
    for i in list_spp_process:
        for index_j in range(len(list_search)):
            if i in list_search[index_j]:
                list_search_rem.append(index_j)
    search[:] = [x for i, x in enumerate(search) if i not in list_search_rem]
    spp_process = SPP.objects.filter(process=True).filter(type_ticket='Коммерческая')
    return render(request, 'tickets/ortr.html', {'search': search, 'com_search': True, 'spp_process': spp_process})


@permission_check(["Сотрудники ОУЗП"])
def pto(request):
    """Данный метод перенаправляет на страницу ПТО заявки, которые находятся в работе ОРТР.
        1. Получает данные от redis о логин/пароле
        2. Получает данные о ПТО заявках в пуле ОРТР с помощью метода in_work_ortr
        3. Получает данные о ПТО заявках которые уже находятся в БД(в работе/в ожидании)
        4. Удаляет из списка в пуле заявки, которые есть в работе/в ожидании
        5. Формирует итоговый список задач в пуле и в работе"""
    user = User.objects.get(username=request.user.username)
    username, password = get_user_credential_cordis(user)
    search = in_work_ortr(username, password)
    if not isinstance(search, list):
        return render(request, 'base.html', {'my_message': 'Нет доступа в СПП'})
    list_search = []
    search[:] = [x for x in search if 'ПТО' in x[0]]
    for i in search:
        if 'ПТО' in i[0]:
            list_search.append(i[0])
    spp_process = SPP.objects.filter(Q(process=True) | Q(wait=True)).filter(type_ticket='ПТО')
    list_spp_process = []
    for i in spp_process:
        list_spp_process.append(i.ticket_k)
    list_search_rem = []
    for i in list_spp_process:
        for index_j in range(len(list_search)):
            if i in list_search[index_j]:
                list_search_rem.append(index_j)
    search[:] = [x for i, x in enumerate(search) if i not in list_search_rem]
    spp_process = SPP.objects.filter(process=True).filter(type_ticket='ПТО')
    return render(request, 'tickets/ortr.html', {'search': search, 'pto_search': True, 'spp_process': spp_process})


@permission_check(["Сотрудники ОУЗП"])
def wait(request):
    """Данный метод перенаправляет на страницу заявки в ожидании.
            1. Получает данные о всех заявках которые уже находятся в БД(в ожидании)
            2. Формирует итоговый список задач в ожидании"""
    spp_process = SPP.objects.filter(wait=True)
    return render(request, 'tickets/ortr.html', {'wait_search': True, 'spp_process': spp_process})


@permission_check(["Сотрудники ОУЗП"])
def all_com_pto_wait(request):
    """Данный метод перенаправляет на страницу Все заявки, которые находятся в пуле ОРТР/в работе/в ожидании.
        1. Получает данные от redis о логин/пароле
        2. Получает данные о всех заявках в пуле ОРТР с помощью метода in_work_ortr
        3. Получает данные о всех заявках которые уже находятся в БД(в работе/в ожидании)
        4. Удаляет из списка в пуле заявки, которые есть в работе/в ожидании
        5. Формирует итоговый список всех заявок в пуле/в работе/в ожидании"""
    user = User.objects.get(username=request.user.username)
    username, password = get_user_credential_cordis(user)
    search = in_work_ortr(username, password)
    if not isinstance(search, list):
        return render(request, 'base.html', {'my_message': 'Нет доступа в СПП'})
    list_search = []
    for i in search:
        list_search.append(i[0])
    spp_proc_wait_all = SPP.objects.filter(Q(process=True) | Q(wait=True))
    list_spp_proc_wait_all = []
    for i in spp_proc_wait_all:
        list_spp_proc_wait_all.append(i.ticket_k)
    list_search_rem = []
    for i in list_spp_proc_wait_all:
        for index_j in range(len(list_search)):
            if i in list_search[index_j]:
                list_search_rem.append(index_j)
    search[:] = [x for i, x in enumerate(search) if i not in list_search_rem]
    spp_process = SPP.objects.filter(process=True)
    spp_wait = SPP.objects.filter(wait=True)
    return render(request, 'tickets/ortr.html', {'all_search': True, 'search': search, 'spp_process': spp_process, 'spp_wait': spp_wait})



def project_tr(request, dID, tID, trID):
    """Данный метод на входе получает параметры ссылки ТР в СПП, с помощью метода parse_tr получает данные из ТР в СПП,
    формирует последовательность url'ов по которым необходимо пройти для получения данных от пользователя и
    перенаправляет на первый из них. Используется для новой точки подключения."""
    spplink = 'https://sss.corp.itmh.ru/dem_tr/dem_begin.php?dID={}&tID={}&trID={}'.format(dID, tID, trID)
    user = User.objects.get(username=request.user.username)
    ticket_tr = TR.objects.filter(ticket_tr=trID).last()
    oattr = ticket_tr.oattr
    pps = ticket_tr.pps
    pps = pps.strip()
    turnoff = ticket_tr.turnoff
    services_plus_desc = splice_services(ticket_tr.services)
    des_tr = ticket_tr.ticket_k.des_tr
    address = ticket_tr.connection_point
    client = ticket_tr.ticket_k.client
    manager = ticket_tr.ticket_k.manager
    technolog = ticket_tr.ticket_k.technolog
    task_otpm = ticket_tr.ticket_k.task_otpm
    counter_line_services = _counter_line_services(services_plus_desc)
    cks_points = []
    for point in des_tr:
        if next(iter(point.keys())).startswith('г.'):
            cks_points.append(next(iter(point.keys())).split('ул.')[1])

    sreda = get_oattr_sreda(oattr) if oattr else '1'

    tag_service = _tag_service_for_new_serv(services_plus_desc)
    tag_service.insert(0, {'sppdata': None})

    session_tr_id = request.session[str(trID)]
    session_tr_id.update({'services_plus_desc': services_plus_desc})
    session_tr_id.update({'counter_line_services': counter_line_services,
                          'counter_line_services_initial':counter_line_services, 'pps': pps, 'turnoff': turnoff,
                          'sreda': sreda, 'cks_points': cks_points, 'address': address, 'oattr': oattr, 'client': client,
                          'manager': manager, 'technolog': technolog, 'task_otpm': task_otpm, 'tID': tID,
                          'dID': dID,})

    spd = session_tr_id.get('spd')
    if counter_line_services == 0:
        tag_service.append({'data': None})
    elif user.groups.filter(name='Менеджеры').exists():
        tag_service.append({'copper': None})
    else:
        if spd == 'РТК':
            if tag_service[-1] in [{'copper': None}, {'vols': None}, {'wireless': None}]:
                tag_service.pop()
            elif tag_service[-1] == {'data': None} and counter_line_services > 0:
                tag_service.pop()
            tag_service.append({'rtk': None})
        elif spd == 'ППМ':
            if tag_service[-1] in [{'copper': None}, {'vols': None}, {'wireless': None}, {'rtk': None}]:
                tag_service.pop()
            tag_service.append({'data': None})
        elif spd == 'Комтехцентр':
            if tag_service[-1] == {'rtk': None}:
                tag_service.pop()
            elif tag_service[-1] == {'data': None} and counter_line_services > 0:
                tag_service.pop()
            if sreda == '1':
                tag_service.append({'copper': None})
            elif sreda == '2' or sreda == '4':
                tag_service.append({'vols': None})
            elif sreda == '3':
                tag_service.append({'wireless': None})

    response = get_response_with_prev_get_params(request, tag_service, session_tr_id, trID)
    return response


def copper(request, trID):
    """Данный метод отображает html-страничку с параметрами для медной линии связи"""
    if request.method == 'POST':
        copperform = CopperForm(request.POST)
        if copperform.is_valid():
            correct_sreda = copperform.cleaned_data['correct_sreda']
            session_tr_id = request.session[str(trID)]
            sreda = session_tr_id.get('sreda')
            tag_service = session_tr_id.get('tag_service')
            if correct_sreda == sreda:
                logic_csw = copperform.cleaned_data['logic_csw']
                logic_replace_csw = copperform.cleaned_data['logic_replace_csw']
                logic_change_gi_csw = copperform.cleaned_data['logic_change_gi_csw']
                logic_change_csw = copperform.cleaned_data['logic_change_csw']
                port = copperform.cleaned_data['port']
                kad = copperform.cleaned_data['kad']

                session_tr_id.update({'logic_csw': logic_csw, 'logic_replace_csw': logic_replace_csw,
                                      'logic_change_csw': logic_change_csw, 'logic_change_gi_csw': logic_change_gi_csw,
                                      'port': port, 'kad': kad})

                type_pass = session_tr_id.get('type_pass')
                if type_pass:
                    tag_service = append_change_log_shpd(session_tr_id)

                if logic_csw == True:
                    tag_service.append({'csw': None})
                    response = get_response_with_get_params(request, tag_service, session_tr_id, trID)
                    return response
                elif logic_replace_csw == True and logic_change_gi_csw == True or logic_replace_csw == True:
                    tag_service.append({'csw': None})
                    response = get_response_with_get_params(request, tag_service, session_tr_id, trID)
                    return response
                elif logic_change_csw == True and logic_change_gi_csw == True or logic_change_csw == True:
                    if type_pass:
                        if 'Организация/Изменение, СПД' in type_pass and 'Перенос, СПД' not in type_pass:
                            tag_service.append({'pass_serv': None})
                        tag_service.append({'csw': None})
                        response = get_response_with_get_params(request, tag_service, session_tr_id, trID)
                        return response
                elif logic_change_gi_csw == True:
                    if type_pass:
                        tag_service.append({'csw': None})
                        response = get_response_with_get_params(request, tag_service, session_tr_id, trID)
                        return response
                else:
                    tag_service.append({'data': None})
                    response = get_response_with_get_params(request, tag_service, session_tr_id, trID)
                    return response
            else:
                if correct_sreda == '3':
                    tag_service.pop()
                    tag_service.append({'wireless': None})
                elif correct_sreda == '2' or correct_sreda == '4':
                    tag_service.pop()
                    tag_service.append({'vols': None})
                session_tr_id.update({'sreda': correct_sreda})
                response = get_response_with_prev_get_params(request, tag_service, session_tr_id, trID)
                return response
    else:
        user = User.objects.get(username=request.user.username)
        username, password = get_user_credential_cordis(user)
        prev_page, index = backward_page(request, trID)
        session_tr_id = request.session[str(trID)]
        pps = session_tr_id.get('pps')
        services_plus_desc = session_tr_id.get('services_plus_desc')
        tag_service = session_tr_id.get('tag_service')
        type_pass = session_tr_id.get('type_pass')
        if session_tr_id.get('list_switches'):
            list_switches = session_tr_id.get('list_switches')
        else:
            list_switches = parsingByNodename(pps, username, password)
            if not isinstance(list_switches, list):
                return render(request, 'base.html', {'my_message': 'Нет доступа к странице Cordis с коммутаторами'})
            if 'No records to display' in list_switches[0]:
                messages.warning(request, 'Нет коммутаторов на узле {}'.format(list_switches[0][22:]))
                return redirect('spp_view_save', session_tr_id.get('dID'), session_tr_id.get('ticket_spp_id'))

        list_switches, switches_name = add_portconfig_to_list_swiches(list_switches, username, password)
        session_tr_id.update({'list_switches': list_switches})
        request.session[trID] = session_tr_id
        copperform = CopperForm(initial={'correct_sreda': '1', 'kad': switches_name, 'port': 'свободный'})

        if user.groups.filter(name='Менеджеры').exists():
            manager_allowed = (
            'SNR S2990G-24T', 'SNR S2990G-48T', 'SNR S2982G-24TE', 'SNR S2985G-24TC', 'SNR S2985G-48T',
            'D-Link DGS-1210-28/ME', 'SNR S2950-24G', 'Orion Alpha A26', 'SNR S2960-48G',
            'SNR S2962-24T', 'SNR S2965-24T', 'SNR S2965-48T', 'D-Link DES-1210-52/ME',
            'D-Link DES-1228/ME/B1', 'Cisco Cisco WS-C2950')
            list_switches = [switch for switch in list_switches if
                             any(switch[1].startswith(sw) for sw in manager_allowed)]
            if not list_switches:
                messages.warning(request, f'Нет медных коммутаторов на узле {pps}. Требуется полноценное ТР.')
                return redirect('spp_view_save', session_tr_id.get('dID'), session_tr_id.get('ticket_spp_id'))
            ports_all_switches = [switch[10] for switch in list_switches]
            counter_free_ports = 0
            for ports in ports_all_switches:
                for port, value in ports.items():
                    port_free = all([value[0] == '-', value[1] == '-', value[2] == '-', value[3] == 'Заглушка 4094'])
                    if port_free and len(ports) > 30 and not any(_ in port for _ in ['49', '50', '51', '52', 'Gi']):
                        counter_free_ports += 1
                    elif port_free and len(ports) < 30 and not any(_ in port for _ in ['25', '26', '27', '28', 'Gi']):
                        counter_free_ports += 1
            if counter_free_ports < 4:
                messages.warning(request, 'На узле связи недостаточно свободных портов. Требуется решению ОУЗП СПД')
                return redirect('spp_view_save', session_tr_id.get('dID'), session_tr_id.get('ticket_spp_id'))
            copperform.fields['correct_sreda'].widget.choices = [('1', 'UTP'), ]

        context = {
            'pps': pps,
            'oattr': session_tr_id.get('oattr'),
            'list_switches': list_switches,
            'sreda': session_tr_id.get('sreda'),
            'copperform': copperform,
            'back_link': reverse(next(iter(tag_service[index])), kwargs={'trID': trID}) + f'?next_page={prev_page}&index={index}',
            'ticket_spp_id': session_tr_id.get('ticket_spp_id'),
            'dID': session_tr_id.get('dID'),
            'trID': trID
        }
        return render(request, 'tickets/env.html', context)


def vols(request, trID):
    """Данный метод отображает html-страничку с параметрами для ВОЛС"""
    user = User.objects.get(username=request.user.username)
    if request.method == 'POST':
        volsform = VolsForm(request.POST)

        if volsform.is_valid():
            correct_sreda = volsform.cleaned_data['correct_sreda']
            session_tr_id = request.session[str(trID)]
            sreda = session_tr_id.get('sreda')
            tag_service = session_tr_id.get('tag_service')

            if correct_sreda == sreda:
                device_client = volsform.cleaned_data['device_client']
                device_pps = volsform.cleaned_data['device_pps']
                logic_csw = volsform.cleaned_data['logic_csw']
                logic_replace_csw = volsform.cleaned_data['logic_replace_csw']
                logic_change_csw = volsform.cleaned_data['logic_change_csw']
                logic_change_gi_csw = volsform.cleaned_data['logic_change_gi_csw']
                port = volsform.cleaned_data['port']
                kad = volsform.cleaned_data['kad']
                speed_port = volsform.cleaned_data['speed_port']
                session_tr_id.update(**volsform.cleaned_data)

                ppr = volsform.cleaned_data['ppr'] if volsform.cleaned_data['ppr'] else None
                session_tr_id.update({'ppr': ppr})

                type_pass = session_tr_id.get('type_pass')
                if type_pass:
                    tag_service = append_change_log_shpd(session_tr_id)


                if logic_csw == True:
                    device_client = device_client.replace('клиентское оборудование', 'клиентский коммутатор')
                    session_tr_id.update({'device_client': device_client})
                    tag_service.append({'csw': None})
                    response = get_response_with_get_params(request, tag_service, session_tr_id, trID)
                    return response
                elif logic_change_csw == True and logic_change_gi_csw == True or logic_change_csw == True:
                    device_client = device_client.replace(' в клиентское оборудование', '')
                    session_tr_id.update({'device_client': device_client})
                    if type_pass:
                        if 'Организация/Изменение, СПД' in type_pass and 'Перенос, СПД' not in type_pass:
                            tag_service.append({'pass_serv': None})
                        tag_service.append({'csw': None})
                        response = get_response_with_get_params(request, tag_service, session_tr_id, trID)
                        return response
                elif logic_replace_csw == True and logic_change_gi_csw == True or logic_replace_csw == True:
                    device_client = device_client.replace(' в клиентское оборудование', '')
                    session_tr_id.update({'device_client': device_client})
                    if type_pass:
                        tag_service.append({'csw': None})
                        response = get_response_with_get_params(request, tag_service, session_tr_id, trID)
                        return response
                elif logic_change_gi_csw == True:
                    device_client = device_client.replace(' в клиентское оборудование', '')
                    session_tr_id.update({'device_client': device_client})
                    if type_pass:
                        tag_service.append({'csw': None})
                        response = get_response_with_get_params(request, tag_service, session_tr_id, trID)
                        return response
                else:
                    tag_service.append({'data': None})
                    response = get_response_with_get_params(request, tag_service, session_tr_id, trID)
                    return response
            else:
                if correct_sreda == '1':
                    tag_service.pop()
                    tag_service.append({'copper': None})
                elif correct_sreda == '3':
                    tag_service.pop()
                    tag_service.append({'wireless': None})
                elif correct_sreda == '2':
                    tag_service.pop()
                    tag_service.append({'vols': None})
                elif correct_sreda == '4':
                    tag_service.pop()
                    tag_service.append({'vols': None})
                session_tr_id.update({'sreda': correct_sreda})
                response = get_response_with_prev_get_params(request, tag_service, session_tr_id, trID)
                return response
    else:
        user = User.objects.get(username=request.user.username)
        username, password = get_user_credential_cordis(user)
        prev_page, index = backward_page(request, trID)
        session_tr_id = request.session[str(trID)]
        tag_service = session_tr_id.get('tag_service')
        ticket_tr_id = session_tr_id.get('ticket_tr_id')
        ticket_tr = TR.objects.get(id=ticket_tr_id)
        pps = session_tr_id.get('pps')
        sreda = session_tr_id.get('sreda')
        if session_tr_id.get('list_switches'):
            list_switches = session_tr_id.get('list_switches')
        else:
            list_switches = parsingByNodename(pps, username, password)
            if not isinstance(list_switches, list):
                return render(request, 'base.html', {'my_message': 'Нет доступа к странице Cordis с коммутаторами'})
            elif 'No records to display' in list_switches[0]:
                messages.warning(request, 'Нет коммутаторов на узле {}'.format(list_switches[0][22:]))
                return redirect('spp_view_save', session_tr_id.get('dID'), session_tr_id.get('ticket_spp_id'))
        list_switches, switches_name = add_portconfig_to_list_swiches(list_switches, username, password)
        session_tr_id.update({'list_switches': list_switches})
        request.session[trID] = session_tr_id
        if sreda == '2':
            volsform = VolsForm(
                    initial={'correct_sreda': '2',
                            'device_pps': 'конвертер 1310 нм, выставить на конвертере режим работы Auto',
                             'device_client': 'конвертер 1550 нм, выставить на конвертере режим работы Auto',
                             'kad': switches_name,
                             'speed_port': 'Auto',
                             'port': 'свободный'})
        elif sreda == '4':
            volsform = VolsForm(
                        initial={'correct_sreda': '4',
                                'device_pps': 'оптический передатчик SFP WDM, до 3 км, 1310 нм',
                                 'device_client': 'конвертер 1550 нм, выставить на конвертере режим работы Auto',
                                 'kad': switches_name,
                                 'speed_port': '100FD'})
        else:
            volsform = VolsForm()

        context = {
            'pps': pps,
            'oattr': session_tr_id.get('oattr'),
            'list_switches': list_switches,
            'sreda': sreda,
            'turnoff': session_tr_id.get('turnoff'),
            'dID': session_tr_id.get('dID'),
            'ticket_tr': ticket_tr,
            'trID': trID,
            'volsform': volsform,
            'back_link': reverse(next(iter(tag_service[index])), kwargs={'trID': trID}) + f'?next_page={prev_page}&index={index}',
            'ticket_spp_id': session_tr_id.get('ticket_spp_id')
        }
        return render(request, 'tickets/env.html', context)



def wireless(request, trID):
    """Данный метод отображает html-страничку с параметрами для беспроводной среды"""
    if request.method == 'POST':
        wirelessform = WirelessForm(request.POST)

        if wirelessform.is_valid():
            correct_sreda = wirelessform.cleaned_data['correct_sreda']
            session_tr_id = request.session[str(trID)]
            sreda = session_tr_id.get('sreda')
            tag_service = session_tr_id.get('tag_service')
            if correct_sreda == sreda:
                logic_csw = wirelessform.cleaned_data['logic_csw']
                logic_change_csw = wirelessform.cleaned_data['logic_change_csw']
                logic_change_gi_csw = wirelessform.cleaned_data['logic_change_gi_csw']
                session_tr_id.update({**wirelessform.cleaned_data})

                type_pass = session_tr_id.get('type_pass')
                if type_pass:
                    tag_service = append_change_log_shpd(session_tr_id)

                if logic_csw == True:
                    tag_service.append({'csw': None})
                    response = get_response_with_get_params(request, tag_service, session_tr_id, trID)
                    return response
                elif logic_change_csw == True or logic_change_gi_csw == True:
                    if type_pass:
                        if 'Организация/Изменение, СПД' in type_pass and 'Перенос, СПД' not in type_pass:
                            tag_service.append({'pass_serv': None})
                        tag_service.append({'csw': None})
                        response = get_response_with_get_params(request, tag_service, session_tr_id, trID)
                        return response
                else:
                    tag_service.append({'data': None})
                    response = get_response_with_get_params(request, tag_service, session_tr_id, trID)
                    return response
            else:
                if correct_sreda == '1':
                    tag_service.pop()
                    tag_service.append({'copper': None})
                elif correct_sreda == '2' or correct_sreda == '4':
                    tag_service.pop()
                    tag_service.append({'vols': None})
                session_tr_id.update({'sreda': correct_sreda})
                response = get_response_with_prev_get_params(request, tag_service, session_tr_id, trID)
                return response
    else:
        user = User.objects.get(username=request.user.username)
        username, password = get_user_credential_cordis(user)

        prev_page, index = backward_page(request, trID)
        session_tr_id = request.session[str(trID)]
        pps = session_tr_id.get('pps')
        tag_service = session_tr_id.get('tag_service')
        if session_tr_id.get('list_switches'):
            list_switches = session_tr_id.get('list_switches')
        else:
            list_switches = parsingByNodename(pps, username, password)
            if not isinstance(list_switches, list):
                return render(request, 'base.html', {'my_message': 'Нет доступа к странице Cordis с коммутаторами'})
            elif 'No records to display' in list_switches[0]:
                messages.warning(request, 'Нет коммутаторов на узле {}'.format(list_switches[0][22:]))
                return redirect('spp_view_save', session_tr_id.get('dID'), session_tr_id.get('ticket_spp_id'))
        list_switches, switches_name = add_portconfig_to_list_swiches(list_switches, username, password)
        session_tr_id.update({'list_switches': list_switches})

        request.session[trID] = session_tr_id
        wirelessform = WirelessForm(initial={'correct_sreda': '3', 'kad': switches_name, 'port': 'свободный'})
        context = {
            'pps': pps,
            'oattr': session_tr_id.get('oattr'),
            'list_switches': list_switches,
            'sreda': session_tr_id.get('sreda'),
            'turnoff': session_tr_id.get('turnoff'),
            'wirelessform': wirelessform,
            'back_link': reverse(next(iter(tag_service[index])), kwargs={'trID': trID}) + f'?next_page={prev_page}&index={index}',
            'ticket_spp_id': session_tr_id.get('ticket_spp_id'),
            'dID': session_tr_id.get('dID'),
            'trID': trID
        }
        return render(request, 'tickets/env.html', context)


def vgws(request, trID):
    """Данный метод отображает html-страничку со списком тел. шлюзов"""
    user = User.objects.get(username=request.user.username)
    username, password = get_user_credential_cordis(user)
    session_tr_id = request.session[str(trID)]
    pps = session_tr_id.get('pps')
    vgws = _parsing_vgws_by_node_name(username, password, NodeName=pps)
    return render(request, 'tickets/vgws.html', {'vgws': vgws, 'pps': pps})


def csw(request, trID):
    """Данный метод отображает форму с параметрами КК"""
    if request.method == 'POST':
        cswform = CswForm(request.POST)
        if cswform.is_valid():
            session_tr_id = request.session[str(trID)]
            session_tr_id.update({**cswform.cleaned_data})
            if not cswform.cleaned_data['type_install_csw']:
                session_tr_id.update({'logic_csw': True})
            tag_service = session_tr_id.get('tag_service')
            tag_service.append({'data': None})
            response = get_response_with_get_params(request, tag_service, session_tr_id, trID)
            return response
    else:
        session_tr_id = request.session[str(trID)]
        sreda = session_tr_id.get('sreda')
        try:
            session_tr_id['type_pass']
        except KeyError:
            add_serv_install = False
            new_install = True
            logic_change_gi_csw = None
            logic_replace_csw = None
            logic_change_csw = False
        else:
            if session_tr_id.get('logic_change_gi_csw'):
                logic_change_gi_csw = session_tr_id.get('logic_change_gi_csw')
                add_serv_install = False
                new_install = False
                if session_tr_id.get('logic_replace_csw'):
                    logic_replace_csw = True
                else:
                    logic_replace_csw = None
                if session_tr_id.get('logic_change_csw'):
                    logic_change_csw = True
                else:
                    logic_change_csw = False
            elif session_tr_id.get('logic_csw'):
                add_serv_install = session_tr_id.get('logic_csw')
                new_install = False
                logic_change_gi_csw = False
                logic_replace_csw = None
                logic_change_csw = False
            elif session_tr_id.get('logic_replace_csw'):
                logic_replace_csw = session_tr_id.get('logic_replace_csw')
                add_serv_install = False
                new_install = False
                logic_change_gi_csw = False
                logic_change_csw = False
            elif session_tr_id.get('logic_change_csw'):
                logic_change_csw = session_tr_id.get('logic_replace_csw')
                add_serv_install = False
                new_install = False
                logic_change_gi_csw = False
                logic_replace_csw = False

        tag_service = session_tr_id.get('tag_service')
        prev_page, index = backward_page(request, trID)
        if sreda == '2' or sreda == '4':
            cswform = CswForm(initial={'model_csw': 'D-Link DGS-1100-06/ME', 'port_csw': '6'})
        else:
            cswform = CswForm(initial={'model_csw': 'D-Link DGS-1100-06/ME', 'port_csw': '5'})

        context = {
            'cswform': cswform,
            'add_serv_install': add_serv_install,
            'new_install': new_install,
            'logic_change_gi_csw': logic_change_gi_csw,
            'logic_replace_csw': logic_replace_csw,
            'logic_change_csw': logic_change_csw,
            'back_link': reverse(next(iter(tag_service[index])), kwargs={'trID': trID}) + f'?next_page={prev_page}&index={index}',
            'ticket_spp_id': session_tr_id.get('ticket_spp_id'),
            'dID': session_tr_id.get('dID'),
            'trID': trID
        }
        return render(request, 'tickets/csw.html', context)


def data(request, trID):
    """Данный метод определяет какой требуется тип ТР(перенос, организация доп. услуг, организация нов. точки и т.д),
     вызывает соответствующие методы для формирования готового ТР, добавления даты, описания существующего подключения,
      поля Требуется и перенаправляет на метод отображающий готовое ТР"""
    user = User.objects.get(username=request.user.username)
    username, password = get_user_credential_cordis(user)
    templates = ckb_parse(username, password)
    session_tr_id = request.session[str(trID)]
    if session_tr_id.get('rtk_form', {}).get('type_pm') == 'FVNO FTTH':
        msan_exist = ckb_parse_msan_exist(username, password, session_tr_id.get('rtk_form').get('switch_ip'))
        session_tr_id.update({'msan_exist': msan_exist})
    session_tr_id.update({'templates': templates})
    if session_tr_id.get('counter_line_services_initial'):
        counter_line_services = session_tr_id.get('counter_line_services_initial')
    else:
        counter_line_services = 0
    if session_tr_id.get('counter_line_phone'):
        counter_line_services += session_tr_id.get('counter_line_phone')
    if session_tr_id.get('counter_line_hotspot'):
        counter_line_services += session_tr_id.get('counter_line_hotspot')
    if session_tr_id.get('counter_line_itv'):
        counter_line_services += session_tr_id.get('counter_line_itv')
    session_tr_id.update({'counter_line_services': counter_line_services})
    if session_tr_id.get('result_services'):
        del session_tr_id['result_services']
    if session_tr_id.get('result_services_ots'):
        del session_tr_id['result_services_ots']
    value_vars = {}
    for key, value in session_tr_id.items():
        value_vars.update({key: value})
    ticket_tr_id = session_tr_id.get('ticket_tr_id')
    ticket_tr = TR.objects.get(id=ticket_tr_id)
    decision_otpm = ticket_tr.oattr
    type_ticket = ticket_tr.ticket_k.type_ticket
    ticket_k = ticket_tr.ticket_k.ticket_k
    evaluative_tr = ticket_tr.ticket_k.evaluative_tr
    value_vars.update({'type_ticket': type_ticket, 'ticket_k': ticket_k, 'decision_otpm': decision_otpm})
    readable_services = value_vars.get('readable_services')


    if value_vars.get('type_pass') and 'Перенос, СПД' in value_vars.get('type_pass'):
        if (value_vars.get('logic_csw') and 'Организация/Изменение, СПД' in value_vars.get('type_pass')) or (value_vars.get('logic_change_csw') and 'Организация/Изменение, СПД' in value_vars.get('type_pass')):
            pass
        elif value_vars.get('logic_csw'):
            counter_line_services = value_vars.get('counter_exist_line')
            value_vars.update({'counter_line_services': counter_line_services})
            result_services, result_services_ots, value_vars = passage_services_with_install_csw(value_vars)
        elif value_vars.get('logic_replace_csw'):
            result_services, value_vars = exist_enviroment_replace_csw(value_vars)
            if value_vars.get('type_passage') == 'Перевод на гигабит' and value_vars.get(
                    'change_log') == 'Порт/КАД меняются':
                value_vars.update({'result_services': result_services})
                result_services, result_services_ots, value_vars = extend_service(value_vars)
        elif value_vars.get('logic_change_csw') or value_vars.get('logic_change_gi_csw'):
            counter_line_services = 0 # суть в том что организуем линии в блоке переноса КК типа порт в порт, т.к. если меняется лог подк, то орг линий не треб
            value_vars.update({'counter_line_services': counter_line_services})
            result_services, result_services_ots, value_vars = passage_services_with_passage_csw(value_vars)
        elif value_vars.get('type_passage') == 'Перевод на гигабит' and value_vars.get('change_log') == 'Порт и КАД не меняется':
            result_services, result_services_ots, value_vars = extend_service(value_vars)
        elif value_vars.get('type_passage') == 'Перенос логического подключения' and value_vars.get('change_log') == 'Порт и КАД не меняется':
            result_services, result_services_ots, value_vars = passage_track(value_vars)
        elif value_vars.get('type_passage') == 'Восстановление трассы' and value_vars.get('change_log') == 'Порт и КАД не меняется':
            result_services, result_services_ots, value_vars = restore_track(value_vars)
        elif value_vars.get('type_passage') == 'Перенос точки подключения' and value_vars.get('change_log') == 'Порт и КАД не меняется' and value_vars.get('selected_ono')[0][-2].startswith('CSW'):
            result_services, result_services_ots, value_vars = passage_csw_no_install(value_vars)
        else:
            counter_line_services = value_vars.get('counter_line_services')
            if value_vars.get('type_passage') == 'Перенос сервиса в новую точку' or value_vars.get('type_passage') == 'Перевод на гигабит':
                value_vars.update({'counter_line_services': 1})
            else:
                value_vars.update({'counter_line_services': value_vars.get('counter_exist_line')})
            result_services, result_services_ots, value_vars = passage_services(value_vars)
            value_vars.update({'counter_line_services': counter_line_services})
            value_vars.update({'result_services': result_services})
            value_vars.update({'result_services_ots': result_services_ots})


    if value_vars.get('type_pass') and 'Организация/Изменение, СПД' in value_vars.get('type_pass'):
        if value_vars.get('logic_csw'):
            counter_line_services = value_vars.get('counter_line_services') + value_vars.get('counter_exist_line')
            value_vars.update(({'services_plus_desc': value_vars.get('new_job_services')}))
            value_vars.update({'counter_line_services': counter_line_services})
            result_services, result_services_ots, value_vars = extra_services_with_install_csw(value_vars)
        elif value_vars.get('logic_replace_csw') and value_vars.get('logic_change_gi_csw') or value_vars.get('logic_replace_csw'):
            value_vars.update(({'services_plus_desc': value_vars.get('new_job_services')}))
            result_services, result_services_ots, value_vars = extra_services_with_replace_csw(value_vars)
        elif value_vars.get('logic_change_gi_csw') or value_vars.get('logic_change_csw'):
            value_vars.update(({'services_plus_desc': value_vars.get('new_job_services')}))
            result_services, result_services_ots, value_vars = extra_services_with_passage_csw(value_vars)
        else:
            value_vars.update(({'services_plus_desc': value_vars.get('new_job_services')}))
            result_services, result_services_ots, value_vars = client_new(value_vars)
        value_vars.update({'result_services': result_services})
        value_vars.update({'result_services_ots': result_services_ots})
        if value_vars.get('type_passage') and value_vars.get('type_passage') == 'Перевод на гигабит':
            result_services, result_services_ots, value_vars = extend_service(value_vars)
            value_vars.update({'result_services': result_services})
            value_vars.update({'result_services_ots': result_services_ots})

    if value_vars.get('type_pass') and 'Изменение, не СПД' in value_vars.get('type_pass'):
        result_services, result_services_ots, value_vars = change_services(value_vars)

    if value_vars.get('type_pass') and 'Перенос Видеонаблюдение' in value_vars.get('type_pass'):
        result_services, result_services_ots, value_vars = passage_video(value_vars)

    if value_vars.get('type_tr') == 'Не требуется':
        result_services = 'Решение ОУЗП СПД не требуется'
        for service in ticket_tr.services:
            if 'Телефон' in service:
                result_services_ots = ['Решение ОУЗП СПД не требуется']
            else:
                result_services_ots = None

    if value_vars.get('type_tr') == 'Коммерческое' and value_vars.get('con_point') == 'Нов. точка':
        result_services, result_services_ots, value_vars = client_new(value_vars)

    if value_vars.get('type_tr') == 'ПТО':
        if value_vars.get('type_change_node') == 'Замена КАД':
            result_services, value_vars = replace_kad(value_vars)
        elif value_vars.get('type_change_node') == 'Установка дополнительного КАД':
            result_services, value_vars = add_kad(value_vars)
        elif value_vars.get('type_change_node') == 'Установка нового КАД':
            result_services, value_vars = new_kad(value_vars)
        result_services_ots = None

    userlastname = None
    if request.user.is_authenticated:
        if user.groups.filter(name='Менеджеры').exists():
            userlastname = 'МКО ' + request.user.last_name
        else:
            userlastname = 'ОУЗП СПД ' + request.user.last_name
    now = datetime.datetime.now()
    now = now.strftime("%d.%m.%Y")
    need = get_need(value_vars)
    if value_vars.get('type_pass'):
        titles = _titles(result_services, result_services_ots)
        titles = ''.join(titles)
        session_tr_id.update({'titles': titles})
        result_services = '\n\n\n'.join(result_services)
        if evaluative_tr:
            result_services = userlastname + ' ' + now + '\n\n' + 'Оценка' + '\n\n' + value_vars.get(
                'head') + '\n\n' + need + '\n\n' + titles + '\n' + result_services
        else:
            result_services = userlastname + ' ' + now + '\n\n' + value_vars.get('head') +'\n\n'+ need + '\n\n' + titles + '\n' + result_services
    elif value_vars.get('not_required'):
        if evaluative_tr:
            result_services = userlastname + ' ' + now + '\n\n' + 'Оценка' + '\n\n' + result_services
        else:
            result_services = userlastname + ' ' + now + '\n\n' + result_services
    else:
        titles = _titles(result_services, result_services_ots)
        titles = ''.join(titles)
        session_tr_id.update({'titles': titles})
        result_services = '\n\n\n'.join(result_services)
        if evaluative_tr:
            result_services = userlastname + ' ' + now + '\n\n' + 'Оценка' + '\n\n' + titles + '\n' + result_services
        else:
            result_services = userlastname + ' ' + now + '\n\n' + titles + '\n' + result_services
    counter_str_ortr = result_services.count('\n')

    if result_services_ots == None:
        counter_str_ots = 1
    else:
        result_services_ots = '\n\n\n'.join(result_services_ots)
        if evaluative_tr:
            result_services_ots = userlastname + ' ' + now + '\n\n' + 'Оценка' + '\n\n' + result_services_ots
        else:
            result_services_ots = userlastname + ' ' + now + '\n\n' + result_services_ots
        counter_str_ots = result_services_ots.count('\n')
    session_tr_id.update({'kad': value_vars.get('kad') if value_vars.get('kad') else 'Не требуется',
                          'pps': value_vars.get('pps') if value_vars.get('pps') else 'Не требуется',
                          'result_services': result_services,
                          'counter_str_ortr': counter_str_ortr,
                          'result_services_ots': result_services_ots,
                          'counter_str_ots': counter_str_ots
                          })
    request.session[trID] = session_tr_id
    try:
        manlink = request.session['manlink']
    except KeyError:
        manlink = None

    if manlink:
        return redirect('unsaved_data')
    else:
        return redirect(reverse('saved_data', kwargs={'trID': trID}))


def unsaved_data(request):
    """Данный метод отображает нередактируемую html-страничку готового ТР"""
    services_plus_desc = request.session['services_plus_desc']
    oattr = request.session['oattr']
    titles = request.session['titles']
    result_services = request.session['result_services']
    counter_str_ortr = request.session['counter_str_ortr']
    counter_str_ots = request.session['counter_str_ots']
    result_services_ots = request.session['result_services_ots']
    try:
        list_switches = request.session['list_switches']
    except KeyError:
        list_switches = None
    now = datetime.datetime.now()
    context = {
        'services_plus_desc': services_plus_desc,
        'oattr': oattr,
        'titles': titles,
        'result_services': result_services,
        'result_services_ots': result_services_ots,
        'now': now,
        'list_switches': list_switches,
        'counter_str_ortr': counter_str_ortr,
        'counter_str_ots': counter_str_ots
    }
    return render(request, 'tickets/data.html', context)


def saved_data(request, trID):
    """Данный метод отображает редактируемую html-страничку готового ТР"""
    spec_button = False
    session_tr_id = request.session[str(trID)]
    titles = session_tr_id.get('titles')
    ticket_tr_id = session_tr_id.get('ticket_tr_id')
    ticket_tr = TR.objects.get(id=ticket_tr_id)
    if ticket_tr.ticket_k.simplified_tr:
        resources = get_specication_resources(session_tr_id)
        spec_button = resources.get('spec_button')
        pps_resources = resources.get('pps_resources')
        csp_resources = resources.get('csp_resources')
        session_tr_id['pps_resources'] = pps_resources
        session_tr_id['csp_resources'] = csp_resources
    if request.method == 'POST':
        ortrform = OrtrForm(request.POST)
        if ortrform.is_valid():
            result_services_ots = session_tr_id.get('result_services_ots')
            list_switches = session_tr_id.get('list_switches') if session_tr_id.get('list_switches') else None
            ortr_field = ortrform.cleaned_data['ortr_field']
            ots_field = ortrform.cleaned_data['ots_field']
            regex = '\n(.+)\r\n-{5,}\r\n'
            match_ortr_field = re.findall(regex, ortr_field)
            is_exist_ots = bool(ots_field)
            match_ots_field = re.findall(regex, ots_field) if is_exist_ots else []
            changable_titles = '\n'.join(match_ortr_field + match_ots_field)
            pps = ortrform.cleaned_data['pps']
            kad = ortrform.cleaned_data['kad']

            ticket_k = ticket_tr.ticket_k
            ticket_tr.pps = pps
            ticket_tr.kad = kad
            ticket_tr.save()
            ortr_id = session_tr_id.get('ortr_id')
            ortr = OrtrTR.objects.get(id=ortr_id)
            ortr.ortr = ortr_field
            ortr.ots = ots_field
            ortr.titles = changable_titles
            ortr.save()
            counter_str_ortr = ortr.ortr.count('\n')
            if ortr.ots:
                counter_str_ots = ortr.ots.count('\n')
            else:
                counter_str_ots = 1


            context = {
                'ticket_k': ticket_k,
                'result_services_ots': result_services_ots,
                'list_switches': list_switches,
                'counter_str_ortr': counter_str_ortr,
                'counter_str_ots': counter_str_ots,
                'ortrform': ortrform,
                'not_required_tr': True,
                'spec_button': spec_button,
                'ticket_spp_id': session_tr_id.get('ticket_spp_id'),
                'dID': ticket_tr.ticket_k.dID,
                'ticket_tr': ticket_tr,
                'trID': trID
            }

            tag_service = session_tr_id.get('tag_service')
            if tag_service:
                index = tag_service.index(tag_service[-2])
                prev_page = next(iter(tag_service[index]))
                context.update({
                    'not_required_tr': False,
                })
                context.update({
                    'back_link': reverse(next(iter(tag_service[index])), kwargs={'trID': trID}) + f'?next_page={prev_page}&index={index}'
                })

            return render(request, 'tickets/saved_data.html', context)

    else:
        kad = session_tr_id['kad']
        if kad == 'Не требуется':
            pps = 'Не требуется'
        else:
            pps = session_tr_id['pps']
        result_services = session_tr_id['result_services']
        counter_str_ortr = session_tr_id['counter_str_ortr']
        counter_str_ots = session_tr_id['counter_str_ots']
        result_services_ots = session_tr_id['result_services_ots']
        try:
            list_switches = session_tr_id['list_switches']
        except KeyError:
            list_switches = None
        ticket_tr_id = session_tr_id['ticket_tr_id']
        ticket_tr = TR.objects.get(id=ticket_tr_id)
        ticket_k = ticket_tr.ticket_k
        ticket_tr.kad = kad
        ticket_tr.pps = pps
        ticket_tr.save()
        if ticket_tr.ortrtr_set.all():
            ortr = ticket_tr.ortrtr_set.all()[0]
        else:
            ortr = OrtrTR()
        ortr.ticket_tr = ticket_tr
        ortr.ortr = result_services
        ortr.ots = result_services_ots
        ortr.titles = titles
        ortr.save()
        session_tr_id['ortr_id'] = ortr.id
        request.session[trID] = session_tr_id
        ortrform = OrtrForm(initial={'ortr_field': ortr.ortr, 'ots_field': ortr.ots, 'pps': pps, 'kad': kad})
        context = {
            'ticket_k': ticket_k,
            'result_services_ots': result_services_ots,
            'list_switches': list_switches,
            'counter_str_ortr': counter_str_ortr,
            'counter_str_ots': counter_str_ots,
            'ortrform': ortrform,
            'not_required_tr': True,
            'spec_button': spec_button,
            'ticket_spp_id': session_tr_id.get('ticket_spp_id'),
            'ticket_tr': ticket_tr,
            'dID': ticket_tr.ticket_k.dID,
            'trID': trID
        }

        tag_service = session_tr_id.get('tag_service')
        if tag_service:
            index = tag_service.index(tag_service[-2])
            prev_page = next(iter(tag_service[index]))
            context.update({
                'not_required_tr': False,
            })
            context.update({
                'back_link': reverse(next(iter(tag_service[index])), kwargs={'trID': trID}) + f'?next_page={prev_page}&index={index}'
            })

        return render(request, 'tickets/saved_data.html', context)


def edit_tr(request, dID, ticket_spp_id, trID):
    """Данный метод отображает html-страничку для редактирования ТР существующего в БД"""
    if request.method == 'POST':
        ortrform = OrtrForm(request.POST)
        if ortrform.is_valid():
            session_tr_id = request.session[str(trID)]
            ortr_field = ortrform.cleaned_data['ortr_field']
            ots_field = ortrform.cleaned_data['ots_field']
            pps = ortrform.cleaned_data['pps']
            kad = ortrform.cleaned_data['kad']
            regex = '\n(\d{1,2}\..+)\r\n-+\r\n'
            match_ortr_field = re.findall(regex, ortr_field)
            is_exist_ots = bool(ots_field)
            match_ots_field = re.findall(regex, ots_field) if is_exist_ots else []
            changable_titles = '\n'.join(match_ortr_field + match_ots_field)
            ticket_tr_id = session_tr_id.get('ticket_tr_id')
            ticket_tr = TR.objects.get(id=ticket_tr_id)
            ticket_tr.pps = pps
            ticket_tr.kad = kad
            ticket_tr.save()
            ortr_id = session_tr_id.get('ortr_id')
            ortr = OrtrTR.objects.get(id=ortr_id)
            ortr.ortr = ortr_field
            ortr.ots = ots_field
            ortr.titles = changable_titles
            ortr.save()
            counter_str_ortr = ortr.ortr.count('\n')
            if ortr.ots:
                counter_str_ots = ortr.ots.count('\n')
            else:
                counter_str_ots = 1

            context = {
                'services_plus_desc': ticket_tr.services,
                'oattr': ticket_tr.oattr,
                'counter_str_ortr': counter_str_ortr,
                'counter_str_ots': counter_str_ots,
                'ortrform': ortrform,
                'ticket_spp_id': ticket_spp_id,
                'dID': dID,
                'ticket_tr': ticket_tr
            }
            return render(request, 'tickets/edit_tr.html', context)
    else:
        session_tr_id = request.session[str(trID)]
        ticket_spp = SPP.objects.get(dID=dID, id=ticket_spp_id)
        ticket_tr = ticket_spp.children.filter(ticket_tr=trID)[0]
        session_tr_id.update({'ticket_tr_id': ticket_tr.id})
        if not ticket_tr.ortrtr_set.all():
            messages.warning(request, 'Блока ОРТР нет')
            return redirect('spp_view_save', dID, ticket_spp_id)
        ortr = ticket_tr.ortrtr_set.all()[0]
        session_tr_id.update({'ortr_id': ortr.id})
        session_tr_id.update({'technical_solution': trID})
        request.session[trID] = session_tr_id
        counter_str_ortr = ortr.ortr.count('\n')
        if ortr.ots:
            counter_str_ots = ortr.ots.count('\n')
        else:
            counter_str_ots = 1
        ortrform = OrtrForm(initial={'ortr_field': ortr.ortr, 'ots_field': ortr.ots, 'pps': ticket_tr.pps, 'kad': ticket_tr.kad})

        context = {
            'services_plus_desc': ticket_tr.services,
            'oattr': ticket_tr.oattr,
            'counter_str_ortr': counter_str_ortr,
            'counter_str_ots': counter_str_ots,
            'ortrform': ortrform,
            'ticket_spp_id': ticket_spp_id,
            'dID': dID,
            'ticket_tr': ticket_tr
        }
        return render(request, 'tickets/edit_tr.html', context)


def manually_tr(request, dID, tID, trID):
    """Данный метод отображает html-страничку для написания ТР вручную"""
    if request.method == 'POST':
        ortrform = OrtrForm(request.POST)
        if ortrform.is_valid():
            session_tr_id = request.session[str(trID)]
            ticket_spp_id = session_tr_id.get('ticket_spp_id')
            ortr_field = ortrform.cleaned_data['ortr_field']
            ots_field = ortrform.cleaned_data['ots_field']
            pps = ortrform.cleaned_data['pps']
            kad = ortrform.cleaned_data['kad']
            regex = '\n(\d{1,2}\..+)\r\n-+\r\n'
            match_ortr_field = re.findall(regex, ortr_field)
            is_exist_ots = bool(ots_field)
            match_ots_field = re.findall(regex, ots_field) if is_exist_ots else []
            changable_titles = '\n'.join(match_ortr_field + match_ots_field)
            ticket_tr_id = session_tr_id.get('ticket_tr_id')
            ticket_tr = TR.objects.get(id=ticket_tr_id)
            ticket_tr.pps = pps
            ticket_tr.kad = kad
            ticket_tr.save()
            ortr_id = session_tr_id.get('ortr_id')
            ortr = OrtrTR.objects.get(id=ortr_id)
            ortr.ortr = ortr_field
            ortr.ots = ots_field
            ortr.titles = changable_titles
            ortr.save()
            counter_str_ortr = ortr.ortr.count('\n')
            if ortr.ots:
                counter_str_ots = ortr.ots.count('\n')
            else:
                counter_str_ots = 1

            context = {
                'services_plus_desc': ticket_tr.services,
                'oattr': ticket_tr.oattr,
                'counter_str_ortr': counter_str_ortr,
                'counter_str_ots': counter_str_ots,
                'ortrform': ortrform,
                'ticket_spp_id': ticket_spp_id,
                'dID': dID,
                'ticket_tr': ticket_tr
            }
            return render(request, 'tickets/edit_tr.html', context)
    else:
        user = User.objects.get(username=request.user.username)
        username, password = get_user_credential_cordis(user)
        tr_params = for_tr_view(username, password, dID, tID, trID)
        if tr_params.get('Access denied'):
            return render(request, 'base.html', {'my_message': 'Нет доступа к странице СПП с ТР'})
        ticket_spp = SPP.objects.filter(dID=dID).last()
        request.session[trID] = {'ticket_spp_id': ticket_spp.id}
        if ticket_spp.children.filter(ticket_tr=trID):
            return redirect('edit_tr', dID, ticket_spp.id, trID)
        ticket_tr = TR()
        ticket_tr.ticket_k = ticket_spp
        ticket_tr.ticket_tr = trID
        ticket_tr.ticket_cp = tID
        ticket_tr.pps = tr_params['Узел подключения клиента']
        ticket_tr.turnoff = False if tr_params['Отключение'] == 'Нет' else True
        ticket_tr.info_tr = tr_params['Информация для разработки ТР']
        ticket_tr.services = tr_params['Перечень требуемых услуг']
        ticket_tr.connection_point = tr_params['Точка подключения']
        ticket_tr.oattr = tr_params['Решение ОТПМ']
        ticket_tr.vID = tr_params['vID']
        ticket_tr.save()
        ortr = OrtrTR()
        ortr.ticket_tr = ticket_tr
        ortr.save()

        request.session[trID] = {'ticket_spp_id': ticket_spp.id, 'ticket_tr_id': ticket_tr.id,
                              'ortr_id': ortr.id, 'technical_solution': trID, 'dID': dID}

        for service in ticket_tr.services:
            if 'Телефон' in service:
                counter_str_ots = 10
            else:
                counter_str_ots = 1
        ortrform = OrtrForm()

        context = {
            'services_plus_desc': ticket_tr.services,
            'oattr': ticket_tr.oattr,
            'counter_str_ortr': 10,
            'counter_str_ots': counter_str_ots,
            'ortrform': ortrform,
            'ticket_spp_id': ticket_spp.id,
            'dID': dID,
            'ticket_tr': ticket_tr,
            'trID': trID
        }
        return render(request, 'tickets/edit_tr.html', context)


def send_to_spp(request, trID):
    """Данный метод заполняет поля блока ОРТР в СПП готовым ТР"""
    user = User.objects.get(username=request.user.username)
    username, password = get_user_credential_cordis(user)
    session_tr_id = request.session[str(trID)]
    ticket_tr_id = session_tr_id.get('ticket_tr_id')
    ticket_tr = TR.objects.get(id=ticket_tr_id)
    did = ticket_tr.ticket_k.dID
    tid = ticket_tr.ticket_cp
    trid = ticket_tr.ticket_tr
    url = f'https://sss.corp.itmh.ru/dem_tr/dem_point.php?dID={did}&tID={tid}&trID={trid}'
    req_check = requests.get(url, verify=False, auth=HTTPBasicAuth(username, password))
    if req_check.status_code == 200:
        trOTO_AV = ticket_tr.pps
        trOTO_Comm = ticket_tr.kad
        vID = ticket_tr.vID
        if ticket_tr.ortrtr_set.all():
            ortr = ticket_tr.ortrtr_set.all()[0]
            trOTO_Resolution = ortr.ortr
            trOTS_Resolution = ortr.ots
        data = {'trOTO_Resolution': trOTO_Resolution, 'trOTS_Resolution': trOTS_Resolution, 'action': 'saveVariant',
                'trOTO_AV': trOTO_AV, 'trOTO_Comm': trOTO_Comm, 'vID': vID}
        if ticket_tr.ticket_k.simplified_tr:
            data.update({'trOTMPType': '11', 'trArticle': '17'})
        req = requests.post(url, verify=False, auth=HTTPBasicAuth(username, password), data=data)

        return redirect(f'https://sss.corp.itmh.ru/dem_tr/dem_begin.php?dID={did}&tID={tid}&trID={trid}')
    return render(request, 'base.html', {'my_message': 'Нет доступа в СПП'})


def hotspot(request, trID):
    """Данный метод отображает html-страничку c формой для заполнения данных по услуге Хот-спот"""
    if request.method == 'POST':
        hotspotform = HotspotForm(request.POST)
        if hotspotform.is_valid():
            type_hotspot = hotspotform.cleaned_data['type_hotspot']
            hotspot_points = hotspotform.cleaned_data['hotspot_points']
            hotspot_users = hotspotform.cleaned_data['hotspot_users']
            exist_hotspot_client = hotspotform.cleaned_data['exist_hotspot_client']
            hotspot_local_wifi = hotspotform.cleaned_data['hotspot_local_wifi']
            session_tr_id = request.session[str(trID)]
            tag_service = session_tr_id.get('tag_service')
            services_plus_desc = session_tr_id.get('services_plus_desc')
            if hotspot_points:
                counter_line_hotspot = hotspot_points-1
                session_tr_id.update({'counter_line_hotspot': counter_line_hotspot})
            session_tr_id.update({'services_plus_desc': services_plus_desc, 'hotspot_points': str(hotspot_points),
                                  'hotspot_users': str(hotspot_users), 'exist_hotspot_client': exist_hotspot_client,
                                  'hotspot_local_wifi': hotspot_local_wifi, 'type_hotspot': type_hotspot})
            response = get_response_with_get_params(request, tag_service, session_tr_id, trID)
            return response
    else:
        session_tr_id = request.session[str(trID)]
        tag_service = session_tr_id.get('tag_service')
        hotspot_points = session_tr_id.get('hotspot_points')
        hotspot_users = session_tr_id.get('hotspot_users')

        service_name = 'hotspot'
        request, service, prev_page, index = backward_page_service(request, trID, service_name)
        premium = True if 'прем' in service.lower() else False
        back_link = reverse(next(iter(tag_service[index])), kwargs={'trID': trID}) + f'?next_page={prev_page}&index={index}'
        hotspotform = HotspotForm(initial={'hotspot_points': hotspot_points, 'hotspot_users': hotspot_users})
        context = {
            'premium_plus': session_tr_id.get('premium_plus'),
            'premium': premium,
            'hotspotform': hotspotform,
            'service_hotspot': service,
            'back_link': back_link,
            'ticket_spp_id': session_tr_id.get('ticket_spp_id'),
            'dID': session_tr_id.get('dID'),
            'trID': trID
        }
        return render(request, 'tickets/hotspot.html', context)


def phone(request, trID):
    """Данный метод отображает html-страничку c формой для заполнения данных по услуге Телефония"""
    if request.method == 'POST':
        form = PhoneForm(request.POST)
        if form.is_valid():
            type_phone = form.cleaned_data['type_phone']
            vgw = form.cleaned_data['vgw']
            ports_vgw = form.cleaned_data['ports_vgw']
            type_ip_trunk = form.cleaned_data['type_ip_trunk']
            form_exist_vgw_model = form.cleaned_data['form_exist_vgw_model']
            form_exist_vgw_name = form.cleaned_data['form_exist_vgw_name']
            form_exist_vgw_port = form.cleaned_data['form_exist_vgw_port']
            data = {**form.cleaned_data}
            phone_numbers = {k:v for k,v in data.items() if k.startswith('channel_vgw')}
            channels = {}
            for number in phone_numbers.values():
                if number in channels.keys():
                    channels.update({number: channels[number] + 1})
                else:
                    channels.update({number: 1})

            session_tr_id = request.session[str(trID)]
            tag_service = session_tr_id.get('tag_service')
            services_plus_desc = session_tr_id.get('services_plus_desc')
            new_job_services = session_tr_id.get('new_job_services')
            phone_in_pass = session_tr_id.get('phone_in_pass')
            current_index_local = session_tr_id.get('current_index_local')

            if phone_in_pass and phone_in_pass not in services_plus_desc:
                services_plus_desc.append(phone_in_pass)
            for index_service in range(len(services_plus_desc)):
                if 'Телефон' in services_plus_desc[index_service]:
                    if type_phone == 'ak' or type_phone == 'st':
                        if new_job_services:
                            for ind in range(len(new_job_services)):
                                if new_job_services[ind] == services_plus_desc[index_service]:
                                    new_job_services[ind] = new_job_services[ind].strip('\/|')
                                    new_job_services[ind] += '|'

                        services_plus_desc[index_service] = services_plus_desc[index_service].strip('\/|')
                        services_plus_desc[index_service] += '|'
                        if phone_in_pass:
                            phone_in_pass = phone_in_pass.strip('\/')
                            if not phone_in_pass.endswith('|'):
                                phone_in_pass += '|'
                            session_tr_id.update({'phone_in_pass': phone_in_pass})
                        else:
                            if type_phone == 'st':
                                session_tr_id.update({'type_ip_trunk': type_ip_trunk})
                                if type_ip_trunk == 'trunk':
                                    session_tr_id.update({'counter_line_services': 1})
                                elif type_ip_trunk == 'access':
                                    session_tr_id.update({'counter_line_phone': 1})
                            if type_phone == 'ak':
                                session_tr_id.update({'counter_line_phone': 1})
                        sreda = session_tr_id.get('sreda')
                        if sreda == '2' or sreda == '4':
                            if {'vols': None} not in tag_service:
                                tag_service.insert(current_index_local + 1, {'vols': None})
                        elif sreda == '3':
                            if {'wireless': None} not in tag_service:
                                tag_service.insert(current_index_local + 1, {'wireless': None})
                        elif sreda == '1':
                            if {'copper': None} not in tag_service:
                                tag_service.insert(current_index_local + 1, {'copper': None})
                        if {'data': None} in tag_service:
                            tag_service.remove({'data': None})
                    elif type_phone == 'ap':
                        if new_job_services:
                            for ind in range(len(new_job_services)):
                                if new_job_services[ind] == services_plus_desc[index_service]:
                                    new_job_services[ind] = new_job_services[ind].strip('\/|')
                                    new_job_services[ind] += '/'
                        if phone_in_pass:
                            phone_in_pass = phone_in_pass.strip('\/|')
                            phone_in_pass += '/'
                            session_tr_id.update({'phone_in_pass': phone_in_pass})
                        services_plus_desc[index_service] = services_plus_desc[index_service].strip('\/|')
                        services_plus_desc[index_service] += '/'
                        if {'copper': None} not in tag_service:
                            tag_service.insert(current_index_local + 1, {'copper': None})
                    elif type_phone == 'ab':
                        if new_job_services:
                            for ind in range(len(new_job_services)):
                                if new_job_services[ind] == services_plus_desc[index_service]:
                                    new_job_services[ind] = new_job_services[ind].strip('\/|')
                                    new_job_services[ind] += '\\'
                        if phone_in_pass:
                            phone_in_pass = phone_in_pass.strip('\/|')
                            phone_in_pass += '\\'
                            session_tr_id.update({'phone_in_pass': phone_in_pass})
                        services_plus_desc[index_service] = services_plus_desc[index_service].strip('\/|')
                        services_plus_desc[index_service] += '\\'
                        session_tr_id.update({'form_exist_vgw_model': form_exist_vgw_model,
                                              'form_exist_vgw_name': form_exist_vgw_name,
                                             'form_exist_vgw_port': form_exist_vgw_port})

            if phone_in_pass and phone_in_pass not in new_job_services:
                services_plus_desc = [x for x in services_plus_desc if not x.startswith('Телефон')]
            session_tr_id.update({'services_plus_desc': services_plus_desc, 'vgw': vgw, 'channels': channels,
                                  'ports_vgw': ports_vgw, 'type_phone': type_phone})
            response = get_response_with_get_params(request, tag_service, session_tr_id, trID)
            return response
    else:
        user = User.objects.get(username=request.user.username)
        session_tr_id = request.session[str(trID)]
        tag_service = session_tr_id.get('tag_service')
        if session_tr_id.get('counter_line_phone'):
            del session_tr_id['counter_line_phone']
        services_plus_desc = session_tr_id.get('services_plus_desc')
        oattr = session_tr_id.get('oattr')

        service_name = 'phone'
        request, service, prev_page, index = backward_page_service(request, trID, service_name)
        if 'ватс' in service.lower():
            vats = True
            vats_extend = False if 'базов' in service.lower() else True
        else:
            vats = False
            vats_extend = False
        back_link = reverse(next(iter(tag_service[index])), kwargs={'trID': trID}) + f'?next_page={prev_page}&index={index}'
        if request.GET.get('next_page'):
            clear_session_params(
                session_tr_id,
                'type_phone',
                'vgw',
                'channel_vgw',
                'ports_vgw',
                'type_ip_trunk',
                'form_exist_vgw_model',
                'form_exist_vgw_name',
                'form_exist_vgw_port',
                'phone_in_pass'
            )
        session_tr_id.update({'current_service': service, 'current_index_local': index + 1})
        counter_line_services = session_tr_id.get('counter_line_services')
        if counter_line_services:
            session_tr_id.update({'counter_line_services_before_phone': counter_line_services})
        else:
            session_tr_id.update({'counter_line_services_before_phone': 0})
        request.session[trID] = session_tr_id



        form = PhoneForm(initial={
                                'type_phone': 's',
                                #'vgw': 'Не требуется',
                            })
        if user.groups.filter(name='Менеджеры').exists():
            form.fields['type_phone'].widget.choices = [('s', 'SIP, по логину/паролю'),]
        context = {
            'service_vgw': service,
            'vats': vats,
            'vats_extend': vats_extend,
            'oattr': oattr,
            'form': form,
            'back_link': back_link,
            'ticket_spp_id': session_tr_id.get('ticket_spp_id'),
            'dID': session_tr_id.get('dID'),
            'trID': trID
        }
        return render(request, 'tickets/phone.html', context)


def local(request, trID):
    """Данный метод отображает html-страничку c формой для выбора СКС/ЛВС"""
    if request.method == 'POST':
        localform = LocalForm(request.POST)
        if localform.is_valid():
            local_type = localform.cleaned_data['local_type']
            session_tr_id = request.session[str(trID)]
            session_tr_id.update({**localform.cleaned_data})
            tag_service = session_tr_id.get('tag_service')
            service = session_tr_id.get('current_service')
            services_plus_desc = session_tr_id.get('services_plus_desc')
            new_job_services = session_tr_id.get('new_job_services')
            if local_type == 'Под видеонаблюдение':
                if new_job_services:
                    new_job_services[:] = [x for x in new_job_services if not x.startswith('ЛВС')]
                services_plus_desc[:] = [x for x in services_plus_desc if not x.startswith('ЛВС')]
            else:
                if service not in services_plus_desc:
                    if new_job_services:
                        new_job_services.append(service)
                    services_plus_desc.append(service)
            response = get_response_with_get_params(request, tag_service, session_tr_id, trID)
            return response
    else:
        user = User.objects.get(username=request.user.username)
        session_tr_id = request.session[str(trID)]
        tag_service = session_tr_id.get('tag_service')
        service_name = 'local'
        request, service, prev_page, index = backward_page_service(request, trID, service_name)
        back_link = reverse(next(iter(tag_service[index])), kwargs={'trID': trID}) + f'?next_page={prev_page}&index={index}'

        session_tr_id.update({'current_service': service, 'current_index_local': index + 1})
        request.session[trID] = session_tr_id
        localform = LocalForm()
        if user.groups.filter(name='Менеджеры').exists():
            localform.fields['local_type'].widget.choices = [
                ('sks_standart', 'СКС Стандарт (без использования кабель-канала)'),
                ('sks_business', 'СКС Бизнес (с использованием кабель-канала)'),
                ('lvs_standart', 'ЛВС Стандарт (без использования кабель-канала)'),
                ('lvs_business', 'ЛВС Бизнес (с использованием кабель-канала)'),
            ]
        context = {
            'service_lvs': service,
            'localform': localform,
            'back_link': back_link,
            'ticket_spp_id': session_tr_id.get('ticket_spp_id'),
            'dID': session_tr_id.get('dID'),
            'trID': trID
        }
        return render(request, 'tickets/local.html', context)


def itv(request, trID):
    """Данный метод отображает html-страничку c формой для заполнения данных по услуге Вебург.ТВ"""
    if request.method == 'POST':
        itvform = ItvForm(request.POST)
        if itvform.is_valid():
            type_itv = itvform.cleaned_data['type_itv']
            cnt_itv = itvform.cleaned_data['cnt_itv']
            need_line_itv = itvform.cleaned_data['need_line_itv']
            router_itv = itvform.cleaned_data['router_itv']
            session_tr_id = request.session[str(trID)]
            services_plus_desc = session_tr_id.get('services_plus_desc')
            tag_service = session_tr_id.get('tag_service')
            selected_ono = session_tr_id.get('selected_ono')
            new_job_services = session_tr_id.get('new_job_services')
            if not new_job_services and type_itv == 'novlexist':
                messages.warning(request, 'Нельзя выбрать "В vlan действующей услуги ШПД" при проектирование в новой точке.')
                return redirect('spp_view_save', session_tr_id.get('dID'), session_tr_id.get('ticket_spp_id'))
            if len(services_plus_desc) == 1 and type_itv == 'novlexist' and selected_ono[0][-4].endswith('/32') and need_line_itv is False:
                messages.warning(request, 'В ШПД с маской /32 Вебург.ТВ организовано. ТР не требуется.')
                return redirect('spp_view_save', session_tr_id.get('dID'), session_tr_id.get('ticket_spp_id'))
            shpd_exist = [serv for serv in services_plus_desc if serv.startswith('Интернет,')]
            if not shpd_exist and type_itv == 'novl':
                messages.warning(request, 'Для Вебург.ТВ в vlan организуемой услуги ШПД требуется услуга ШПД в перечне услуг.')
                return redirect('spp_view_save', session_tr_id.get('dID'), session_tr_id.get('ticket_spp_id'))


            for index_service in range(len(services_plus_desc)):
                if 'iTV' in services_plus_desc[index_service]:
                    if type_itv == 'vl':
                        if new_job_services:
                            for ind in range(len(new_job_services)):
                                if new_job_services[ind] == services_plus_desc[index_service] and not services_plus_desc[index_service].endswith('|'):
                                    new_job_services[ind] += '|'

                        session_tr_id.update({'counter_line_itv': cnt_itv})

                        sreda = session_tr_id.get('sreda')
                        if sreda == '2' or sreda == '4':
                            if {'vols': None} not in tag_service:
                                tag_service.append({'vols': None})
                        elif sreda == '3':
                            if {'wireless': None} not in tag_service:
                                tag_service.append({'wireless': None})
                        elif sreda == '1':
                            if {'copper': None} not in tag_service:
                                tag_service.append({'copper': None})
                        if {'data': None} in tag_service:
                            tag_service.remove({'data': None})
                    else:
                        if session_tr_id.get('counter_line_itv'):
                            del session_tr_id['counter_line_itv']
            session_tr_id.update({'new_job_services': new_job_services, 'services_plus_desc': services_plus_desc,
                                  'type_itv': type_itv, 'cnt_itv': cnt_itv, 'router_itv': router_itv,
                                  'need_line_itv': need_line_itv})
            response = get_response_with_get_params(request, tag_service, session_tr_id, trID)
            return response
    else:
        user = User.objects.get(username=request.user.username)
        service_name = 'itv'
        session_tr_id = request.session[str(trID)]
        tag_service = session_tr_id.get('tag_service')
        request, service, prev_page, index = backward_page_service(request, trID, service_name)
        back_link = reverse(next(iter(tag_service[index])), kwargs={'trID': trID}) + f'?next_page={prev_page}&index={index}'

        session_tr_id.update({'current_service': service})
        request.session[trID] = session_tr_id


        itvform = ItvForm()
        if user.groups.filter(name='Менеджеры').exists():
            con_point = session_tr_id.get('con_point')
            if con_point == 'Нов. точка':
                itvform.fields['type_itv'].widget.choices = [('novl', 'В vlan организуемой услуги ШПД'),]
            elif con_point == 'Сущ. точка':
                itvform.fields['type_itv'].widget.choices = [('novlexist', 'В vlan действующей услуги ШПД'),]
        return render(request, 'tickets/itv.html', {
            'itvform': itvform,
            'service_itv': service,
            'back_link': back_link,
            'ticket_spp_id': session_tr_id.get('ticket_spp_id'),
            'dID': session_tr_id.get('dID'),
            'trID': trID
        })


def cks(request, trID):
    """Данный метод отображает html-страничку c формой для заполнения данных по услуге ЦКС"""
    if request.method == 'POST':
        cksform = CksForm(request.POST)
        if cksform.is_valid():
            pointA = cksform.cleaned_data['pointA']
            pointB = cksform.cleaned_data['pointB']
            policer_cks = cksform.cleaned_data['policer_cks']
            type_cks = cksform.cleaned_data['type_cks']
            exist_service = cksform.cleaned_data['exist_service']
            session_tr_id = request.session[str(trID)]
            if type_cks and type_cks == 'trunk':
                session_tr_id.update({'counter_line_services': 1})
            all_cks_in_tr = session_tr_id.get('all_cks_in_tr') if session_tr_id.get('all_cks_in_tr') else dict()
            service = session_tr_id.get('current_service')
            tag_service = session_tr_id.get('tag_service')
            all_cks_in_tr.update({service:{'pointA': pointA, 'pointB': pointB, 'policer_cks': policer_cks,
                                           'type_cks': type_cks, 'exist_service': exist_service}})
            session_tr_id.update({'all_cks_in_tr': all_cks_in_tr})
            response = get_response_with_get_params(request, tag_service, session_tr_id, trID)
            return response
    else:
        user = User.objects.get(username=request.user.username)
        service_name = 'cks'
        session_tr_id = request.session[str(trID)]
        tag_service = session_tr_id.get('tag_service')
        request, service, prev_page, index = backward_page_service(request, trID, service_name)
        back_link = reverse(next(iter(tag_service[index])), kwargs={'trID': trID}) + f'?next_page={prev_page}&index={index}'
        session_tr_id.update({'current_service': service})
        request.session[trID] = session_tr_id
        types_change_service = session_tr_id.get('types_change_service')
        trunk_turnoff_on, trunk_turnoff_off = trunk_turnoff_shpd_cks_vk_vm(service, types_change_service)
        list_cks = session_tr_id.get('cks_points')
        cksform = CksForm(initial={'pointA': list_cks[0], 'pointB': list_cks[1]}) if len(list_cks) == 2 else CksForm()
        return render(request, 'tickets/cks.html', {
            'cksform': cksform,
            'list_strok': list_cks if len(list_cks) != 2 else None,
            'services_cks': service,
            'trunk_turnoff_on': trunk_turnoff_on,
            'trunk_turnoff_off': trunk_turnoff_off,
            'back_link': back_link,
            'ticket_spp_id': session_tr_id.get('ticket_spp_id'),
            'dID': session_tr_id.get('dID'),
            'trID': trID
        })


def shpd(request, trID):
    """Данный метод отображает html-страничку c формой для заполнения данных по услуге ШПД"""
    if request.method == 'POST':
        shpdform = ShpdForm(request.POST)
        if shpdform.is_valid():
            router_shpd = shpdform.cleaned_data['router']
            type_shpd = shpdform.cleaned_data['type_shpd']
            exist_service = shpdform.cleaned_data['exist_service']
            session_tr_id = request.session[str(trID)]
            if type_shpd == 'trunk':
                session_tr_id.update({'counter_line_services': 1})

            all_shpd_in_tr = session_tr_id.get('all_shpd_in_tr') if session_tr_id.get('all_shpd_in_tr') else dict()
            service = session_tr_id.get('current_service')
            tag_service = session_tr_id.get('tag_service')
            all_shpd_in_tr.update({service:{'router_shpd': router_shpd, 'type_shpd': type_shpd, 'exist_service': exist_service}})
            session_tr_id.update({'all_shpd_in_tr': all_shpd_in_tr})
            response = get_response_with_get_params(request, tag_service, session_tr_id, trID)
            return response
    else:
        service_name = 'shpd'
        request, service, prev_page, index = backward_page_service(request, trID, service_name)
        session_tr_id = request.session[str(trID)]
        types_change_service = session_tr_id.get('types_change_service')
        tag_service = session_tr_id.get('tag_service')
        back_link = reverse(next(iter(tag_service[index])), kwargs={'trID': trID}) + f'?next_page={prev_page}&index={index}'
        session_tr_id.update({'current_service': service})
        request.session[trID] = session_tr_id
        trunk_turnoff_on, trunk_turnoff_off = trunk_turnoff_shpd_cks_vk_vm(service, types_change_service)
        shpdform = ShpdForm(initial={'shpd': 'access'})
        if 'Интернет, DHCP' in service:
            shpdform.fields['type_shpd'].widget.choices = [('access', 'access')]
        context = {
            'shpdform': shpdform,
            'services_shpd': service,
            'trunk_turnoff_on': trunk_turnoff_on,
            'trunk_turnoff_off': trunk_turnoff_off,
            'back_link': back_link,
            'trID': trID,
            'ticket_spp_id': session_tr_id.get('ticket_spp_id'),
            'dID': session_tr_id.get('dID')
        }
        return render(request, 'tickets/shpd.html', context)


def portvk(request, trID):
    """Данный метод отображает html-страничку c формой для заполнения данных по услуге Порт ВЛС"""
    if request.method == 'POST':
        portvkform = PortVKForm(request.POST)
        if portvkform.is_valid():
            type_vk = portvkform.cleaned_data['type_vk']
            exist_vk = '"{}"'.format(portvkform.cleaned_data['exist_vk'])
            policer_vk = portvkform.cleaned_data['policer_vk']
            type_portvk = portvkform.cleaned_data['type_portvk']
            exist_service = portvkform.cleaned_data['exist_service']
            session_tr_id = request.session[str(trID)]
            if type_portvk == 'trunk':
                session_tr_id.update({'counter_line_services': 1})
            all_portvk_in_tr = session_tr_id.get('all_portvk_in_tr') if session_tr_id.get('all_portvk_in_tr') else dict()
            service = session_tr_id.get('current_service')
            all_portvk_in_tr.update({service:{'type_vk': type_vk, 'exist_vk': exist_vk, 'policer_vk': policer_vk,
                                              'type_portvk': type_portvk, 'exist_service': exist_service}})
            session_tr_id.update({'all_portvk_in_tr': all_portvk_in_tr})
            tag_service = session_tr_id.get('tag_service')
            response = get_response_with_get_params(request, tag_service, session_tr_id, trID)
            return response
    else:
        mess = '(<a href="https://ckb.itmh.ru/x/gQdaH" target ="_blank">смотри документ</a>, раздел "Схема. ЦКС между'
        service_name = 'portvk'
        session_tr_id = request.session[str(trID)]
        ticket_tr_id = session_tr_id.get('ticket_tr_id')
        ticket_tr = TR.objects.get(id=ticket_tr_id)
        spd = session_tr_id.get('spd')
        if spd == 'РТК':
            messages.warning(request, 'Порт ВЛС через РТК не предоставляется.')
            return redirect('spp_view_save', ticket_tr.ticket_k.dID, ticket_tr.ticket_k.id)

        request, service, prev_page, index = backward_page_service(request, trID, service_name)

        tag_service = session_tr_id.get('tag_service')
        back_link = reverse(next(iter(tag_service[index])), kwargs={'trID': trID}) + f'?next_page={prev_page}&index={index}'
        session_tr_id.update({'current_service': service})
        types_change_service = session_tr_id.get('types_change_service')
        trunk_turnoff_on, trunk_turnoff_off = trunk_turnoff_shpd_cks_vk_vm(service, types_change_service)
        request.session[trID] = session_tr_id
        portvkform = PortVKForm()
        context = {'portvkform': portvkform,
                   'services_vk': service,
                   'trunk_turnoff_on': trunk_turnoff_on,
                   'trunk_turnoff_off': trunk_turnoff_off,
                   'back_link': back_link,
                   'ticket_spp_id': session_tr_id.get('ticket_spp_id'),
                   'dID': session_tr_id.get('dID'),
                   'trID': trID,
                   }
        return render(request, 'tickets/portvk.html', context)


def portvm(request, trID):
    """Данный метод отображает html-страничку c формой для заполнения данных по услуге Порт ВМ"""
    if request.method == 'POST':
        portvmform = PortVMForm(request.POST)
        if portvmform.is_valid():
            type_vm = portvmform.cleaned_data['type_vm']
            exist_vm = '"{}"'.format(portvmform.cleaned_data['exist_vm'])
            policer_vm = portvmform.cleaned_data['policer_vm']
            vm_inet = portvmform.cleaned_data['vm_inet']
            type_portvm = portvmform.cleaned_data['type_portvm']
            exist_service_vm = portvmform.cleaned_data['exist_service_vm']
            session_tr_id = request.session[str(trID)]
            if type_portvm == 'trunk':
                session_tr_id.update({'counter_line_services': 1})
            session_tr_id.update({'policer_vm': policer_vm, 'type_vm': type_vm, 'exist_vm': exist_vm, 'vm_inet': vm_inet,
                                  'type_portvm': type_portvm, 'exist_service_vm': exist_service_vm})
            tag_service = session_tr_id.get('tag_service')
            response = get_response_with_get_params(request, tag_service, session_tr_id, trID)
            return response
    else:
        service_name = 'portvm'
        request, service, prev_page, index = backward_page_service(request, trID, service_name)
        session_tr_id = request.session[str(trID)]
        tag_service = session_tr_id.get('tag_service')
        back_link = reverse(next(iter(tag_service[index])), kwargs={'trID': trID}) + f'?next_page={prev_page}&index={index}'
        session_tr_id.update({'current_service': service})
        types_change_service = session_tr_id.get('types_change_service')
        trunk_turnoff_on, trunk_turnoff_off = trunk_turnoff_shpd_cks_vk_vm(service, types_change_service)
        request.session[trID] = session_tr_id
        portvmform = PortVMForm()
        context = {'portvmform': portvmform,
                   'services_vm': service,
                   'trunk_turnoff_on': trunk_turnoff_on,
                   'trunk_turnoff_off': trunk_turnoff_off,
                   'back_link': back_link,
                   'ticket_spp_id': session_tr_id.get('ticket_spp_id'),
                   'dID': session_tr_id.get('dID'),
                   'trID': trID,
                   }
        return render(request, 'tickets/portvm.html', context)


def video(request, trID):
    """Данный метод отображает html-страничку c формой для заполнения данных по услуге Видеонаблюдение"""
    if request.method == 'POST':
        videoform = VideoForm(request.POST)
        if videoform.is_valid():
            session_tr_id = request.session[str(trID)]
            tag_service = session_tr_id.get('tag_service')
            session_tr_id.update({**videoform.cleaned_data})
            response = get_response_with_get_params(request, tag_service, session_tr_id, trID)
            return response
    else:
        session_tr_id = request.session[str(trID)]
        tag_service = session_tr_id.get('tag_service')
        service_name = 'video'
        request, service, prev_page, index = backward_page_service(request, trID, service_name)
        back_link = reverse(next(iter(tag_service[index])), kwargs={'trID': trID}) + f'?next_page={prev_page}&index={index}'
        session_tr_id.update({'current_service': service})
        request.session[trID] = session_tr_id
        videoform = VideoForm()
        context = {
            'service_video': service,
            'videoform': videoform,
            'task_otpm': session_tr_id.get('task_otpm'),
            'back_link': back_link,
            'ticket_spp_id': session_tr_id.get('ticket_spp_id'),
            'dID': session_tr_id.get('dID'),
            'trID': trID
        }
        return render(request, 'tickets/video.html', context)


def get_resources(request, trID):
    """Данный метод получает от пользователя номер договора. с помощью метода get_contract_id получает ID договора.
     С помощью метода get_contract_resources получает ресурсы с контракта. Отправляет пользователя на страницу, где
    отображаются эти ресурсы.
    Если несколько договоров удовлетворяющих поиску - перенаправляет на страницу выбора конкретного договора."""
    user = User.objects.get(username=request.user.username)
    username, password = get_user_credential_cordis(user)
    if request.method == 'POST':
        contractform = ContractForm(request.POST)
        if contractform.is_valid():
            contract = contractform.cleaned_data['contract']
            contract_id = get_contract_id(username, password, contract)
            session_tr_id = request.session[str(trID)]
            if isinstance(contract_id, list):
                session_tr_id.update({'contract_id': contract_id, 'contract': contract})
                request.session[trID] = session_tr_id
                return redirect('contract_id_formset', trID)
            else:
                if contract_id == 'Такого договора не найдено':
                    messages.warning(request, 'Договора не найдено')
                    return redirect('get_resources', trID)
                ono = get_contract_resources(username, password, contract_id)
                table = get_cis_resources(username, password, contract_id)
                cameras = check_contract_video(username, password, table, contract_id)
                if cameras:
                    session_tr_id.update({'cameras': cameras})
                phone_address = check_contract_phone_exist(table)
                if phone_address:
                    session_tr_id.update({'phone_address': phone_address})
                session_tr_id.update({'ono': ono, 'contract': contract})
                request.session[trID] = session_tr_id
                return redirect('resources_formset', trID)
    else:
        contractform = ContractForm()
    return render(request, 'tickets/contract.html', {'contractform': contractform, 'trID': trID})


def add_spp(request, dID):
    """Данный метод принимает параметр заявки СПП, проверяет наличие данных в БД с таким параметром. Если в БД есть
     ТР с таким параметром, то помечает данную заявку как новую версию, если нет, то помечает как версию 1.
     Получает данные с помощью метода for_spp_view и добавляет в БД. Перенаправляет на метод spp_view_save"""
    user = User.objects.get(username=request.user.username)
    username, password = get_user_credential_cordis(user)
    spp_params = for_spp_view(username, password, dID)
    if spp_params.get('Access denied') == 'Access denied':
        return render(request, 'base.html', {'my_message': 'Нет доступа в СПП'})
    elif not spp_params.get('ТР по упрощенной схеме') and user.groups.filter(name='Менеджеры').exists():
        messages.warning(request, 'Нельзя взять в работу неупрощенное ТР')
        return redirect('mko')
    try:
        current_spp = SPP.objects.filter(dID=dID).latest('created')
    except ObjectDoesNotExist:
        if spp_params['ТР по упрощенной схеме'] is True:
            accept_to_ortr(username, password, dID, spp_params['uID'], spp_params['trDifPeriod'],
                           spp_params['trCuratorPhone'])
            spp_params = for_spp_view(username, password, dID)
        version = 1
        ticket_spp = SPP()
        ticket_spp.dID = dID
        ticket_spp.ticket_k = spp_params['Заявка К']
        ticket_spp.client = spp_params['Клиент']
        ticket_spp.type_ticket = spp_params['Тип заявки']
        ticket_spp.manager = spp_params['Менеджер']
        ticket_spp.technolog = spp_params['Технолог']
        ticket_spp.task_otpm = spp_params['Задача в ОТПМ']
        ticket_spp.des_tr = spp_params['Состав Заявки ТР']
        ticket_spp.services = spp_params['Перечень требуемых услуг']
        ticket_spp.comment = spp_params['Примечание']
        ticket_spp.version = version
        ticket_spp.process = True
        ticket_spp.uID = spp_params['uID']
        ticket_spp.trdifperiod = spp_params['trDifPeriod']
        ticket_spp.trcuratorphone = spp_params['trCuratorPhone']
        ticket_spp.simplified_tr = spp_params['ТР по упрощенной схеме']
        ticket_spp.evaluative_tr = spp_params['Оценочное ТР']
        user = User.objects.get(username=request.user.username)
        ticket_spp.user = user
        ticket_spp.save()
        return redirect('spp_view_save', dID, ticket_spp.id)
    else:
        if current_spp.process == True:
            messages.warning(request, '{} уже взял в работу'.format(current_spp.user.last_name))
            if user.groups.filter(name='Менеджеры').exists():
                return redirect('mko')
            return redirect('ortr')
        if spp_params['ТР по упрощенной схеме'] is True:
            accept_to_ortr(username, password, dID, spp_params['uID'], spp_params['trDifPeriod'],
                           spp_params['trCuratorPhone'])
            spp_params = for_spp_view(username, password, dID)
        exist_dID = len(SPP.objects.filter(dID=dID))
        version = exist_dID + 1
        ticket_spp = SPP()
        ticket_spp.dID = dID
        ticket_spp.ticket_k = spp_params['Заявка К']
        ticket_spp.client = spp_params['Клиент']
        ticket_spp.type_ticket = spp_params['Тип заявки']
        ticket_spp.manager = spp_params['Менеджер']
        ticket_spp.technolog = spp_params['Технолог']
        ticket_spp.task_otpm = spp_params['Задача в ОТПМ']
        ticket_spp.des_tr = spp_params['Состав Заявки ТР']
        ticket_spp.services = spp_params['Перечень требуемых услуг']
        ticket_spp.comment = spp_params['Примечание']
        ticket_spp.version = version
        ticket_spp.process = True
        ticket_spp.uID = spp_params['uID']
        ticket_spp.trdifperiod = spp_params['trDifPeriod']
        ticket_spp.trcuratorphone = spp_params['trCuratorPhone']
        ticket_spp.simplified_tr = spp_params['ТР по упрощенной схеме']
        ticket_spp.evaluative_tr = spp_params['Оценочное ТР']
        user = User.objects.get(username=request.user.username)
        ticket_spp.user = user
        ticket_spp.save()
        return redirect('spp_view_save', dID, ticket_spp.id)


def remove_spp_process(request, ticket_spp_id):
    """Данный метод удаляет заявку из обрабатываемых заявок"""
    user = User.objects.get(username=request.user.username)
    current_ticket_spp = SPP.objects.get(id=ticket_spp_id)
    current_ticket_spp.process = False
    current_ticket_spp.projected = False
    current_ticket_spp.save()
    tickets_tr = current_ticket_spp.children.all()
    for ticket_tr in tickets_tr:
        if request.session.get(ticket_tr.ticket_tr):
            del request.session[ticket_tr.ticket_tr]
    messages.success(request, 'Работа по заявке {} завершена'.format(current_ticket_spp.ticket_k))
    if user.groups.filter(name='Менеджеры').exists():
        return redirect('mko')
    return redirect('ortr')


def remove_spp_wait(request, ticket_spp_id):
    """Данный метод удаляет заявку из заявок в ожидании"""
    current_ticket_spp = SPP.objects.get(id=ticket_spp_id)
    current_ticket_spp.wait = False
    current_ticket_spp.save()
    tickets_tr = current_ticket_spp.children.all()
    for ticket_tr in tickets_tr:
        if request.session.get(ticket_tr.ticket_tr):
            del request.session[ticket_tr.ticket_tr]
    messages.success(request, 'Заявка {} возвращена из ожидания'.format(current_ticket_spp.ticket_k))
    return redirect('ortr')


def add_spp_wait(request, ticket_spp_id):
    """Данный метод добавляет заявку в заявки в ожидании"""
    current_ticket_spp = SPP.objects.get(id=ticket_spp_id)
    current_ticket_spp.wait = True
    current_ticket_spp.was_waiting = True
    current_ticket_spp.process = False
    current_ticket_spp.projected = False
    current_ticket_spp.save()
    messages.success(request, 'Заявка {} перемещена в ожидание'.format(current_ticket_spp.ticket_k))
    return redirect('wait')


def spp_view_save(request, dID, ticket_spp_id):
    """Данный метод отображает html-страничку с данными заявки взятой в работу или обработанной. Данные о заявке
     получает из БД"""
    #request = flush_session_key(request)

    # request.session['ticket_spp_id'] = ticket_spp_id  # проверить что ничего не ломается и удалить
    # request.session['dID'] = dID
    current_ticket_spp = get_object_or_404(SPP, dID=dID, id=ticket_spp_id)

    context = {'current_ticket_spp': current_ticket_spp}
    return render(request, 'tickets/spp_view_save.html', context)


def spp_view(request, dID):
    """Данный метод отображает html-страничку с данными заявки находящейся в пуле ОРТР. Данные о заявке получает
    с помощью метода for_spp_view из СПП."""
    user = User.objects.get(username=request.user.username)
    username, password = get_user_credential_cordis(user)
    spp_params = for_spp_view(username, password, dID)
    if spp_params.get('Access denied') == 'Access denied':
        return render(request, 'base.html', {'my_message': 'Нет доступа в СПП'})
    return render(request, 'tickets/spp_view.html', {'spp_params': spp_params})


def add_tr_to_db(dID, tID, trID, tr_params, ticket_spp_id):
    """Данный метод получает ID заявки СПП, ID ТР, параметры полученные с распарсенной страницы ТР, ID заявки в АРМ.
    создает ТР в АРМ и добавляет в нее данные. Возвращает ID ТР в АРМ"""
    ticket_spp = SPP.objects.get(dID=dID, id=ticket_spp_id)
    if ticket_spp.children.filter(ticket_tr=trID):
        ticket_tr = ticket_spp.children.filter(ticket_tr=trID)[0]
    else:
        ticket_tr = TR()
    ticket_tr.ticket_k = ticket_spp
    ticket_tr.ticket_tr = trID
    ticket_tr.ticket_cp = tID
    ticket_tr.pps = tr_params['Узел подключения клиента']
    ticket_tr.turnoff = False if tr_params['Отключение'] == 'Нет' else True
    ticket_tr.info_tr = tr_params['Информация для разработки ТР']
    ticket_tr.services = tr_params['Перечень требуемых услуг']
    ticket_tr.connection_point = tr_params['Точка подключения']
    ticket_tr.oattr = tr_params['Решение ОТПМ']
    ticket_tr.vID = tr_params['vID']
    ticket_tr.aid = tr_params['aid']
    ticket_tr.id_otu_project = tr_params['id_otu_project']
    ticket_tr.save()
    ticket_tr_id = ticket_tr.id
    return ticket_tr_id


def tr_view_save(request, dID, ticket_spp_id, trID):
    """Данный метод отображает html-страничку c данными обработанного ТР из БД АРМ"""
    ticket_spp = SPP.objects.get(dID=dID, id=ticket_spp_id)
    #get_object_or_404 не используется т.к. 'RelatedManager' object has no attribute 'get_object_or_404'
    try:
        ticket_tr = ticket_spp.children.get(ticket_tr=trID)
    except TR.DoesNotExist:
        raise Http404("ТР не создавалось")

    try:
        ortr = ticket_tr.ortrtr_set.all()[0]
    except IndexError:
        raise Http404("Блока ОРТР нет")
    return render(request, 'tickets/tr_view_save.html', {'ticket_tr': ticket_tr, 'ortr': ortr})


def tr_view(request, dID, tID, trID):
    """Данный метод отображает html-страничку c данными ТР из СПП"""
    user = User.objects.get(username=request.user.username)
    username, password = get_user_credential_cordis(user)
    ticket_tr = for_tr_view(username, password, dID, tID, trID)
    if ticket_tr.get('Access denied') == 'Access denied':
        return render(request, 'base.html', {'my_message': 'Нет доступа в СПП'})
    return render(request, 'tickets/tr_view.html', {'ticket_tr': ticket_tr})


def get_title_tr(request):
    """Данный метод очищает сессию и перенаправляет на get_resources"""
    #flush_session_key(request)
    not_exists_trid = 1
    request.session[not_exists_trid] = {}
    return redirect('get_resources', not_exists_trid)


def title_tr(request, trID):
    """Данный метод отображает html-страничку с шапкой ТР"""
    session_tr_id = request.session[str(trID)]
    head = session_tr_id.get('head')
    del request.session[str(trID)]
    return render(request, 'tickets/title_tr.html', {'head': head})


def contract_id_formset(request, trID):
    """Данный метод отображает форму, в которой пользователь выбирает 1 из договоров наиболее удовлетворяющих
     поисковому запросу договора, с помощью метода get_contract_resources получает ресурсы с этого договора
      и перенаправляет на форму для выбора ресурса для работ.
      Если выбрано более одного или ни одного договора возвращает эту же форму повторно."""
    user = User.objects.get(username=request.user.username)
    username, password = get_user_credential_cordis(user)
    session_tr_id = request.session[str(trID)]
    contract_id = session_tr_id.get('contract_id')
    ListContractIdFormSet = formset_factory(ListContractIdForm, extra=len(contract_id))
    if request.method == 'POST':
        formset = ListContractIdFormSet(request.POST)
        if formset.is_valid():
            data = formset.cleaned_data

            selected_contract_id = []
            unselected_contract_id = []
            selected = zip(contract_id, data)
            for contract_id, data in selected:
                if bool(data):
                    selected_contract_id.append(contract_id.get('id'))
            if selected_contract_id:
                if len(selected_contract_id) > 1:
                    messages.warning(request, 'Было выбрано более 1 ресурса')
                    return redirect('contract_id_formset', trID)
                else:
                    ono = get_contract_resources(username, password, selected_contract_id[0])

                    if ono:
                        table = get_cis_resources(username, password, selected_contract_id[0])
                        phone_address = check_contract_phone_exist(table)
                        if phone_address:
                            session_tr_id.update({'phone_address': phone_address})
                        session_tr_id.update({'ono': ono})
                        request.session[trID] = session_tr_id
                        return redirect('resources_formset', trID)
                    else:
                        messages.warning(request, 'На контракте нет ресурсов')
                        return redirect('contract_id_formset', trID)
            else:
                messages.warning(request, 'Контракты не выбраны')
                return redirect('contract_id_formset', trID)
    else:
        formset = ListContractIdFormSet()
        context = {
            'contract_id': contract_id,
            'formset': formset,
            'trID': trID
        }
        return render(request, 'tickets/contract_id_formset.html', context)


def resources_formset(request, trID):
    """Данный метод получает спискок ресурсов с выбранного договора. Формирует форму, в которой пользователь выбирает
     только 1 ресурс, который будет участвовать в ТР. По коммутатору этого ресурса метод добавляет все ресурсы с данным
      коммутатором в итоговый список. Если выбрано более одного или ни одного ресурса возвращает эту же форму повторно.
      По точке подключения(город, улица) проверяет наличие телефонии на договоре. Отправляет пользователя на страницу
      формирования заголовка."""
    session_tr_id = request.session[str(trID)]
    ono = session_tr_id.get('ono')

    ListResourcesFormSet = formset_factory(ListResourcesForm, extra=len(ono))
    if request.method == 'POST':
        formset = ListResourcesFormSet(request.POST)
        if formset.is_valid():
            phone_address = session_tr_id.get('phone_address')
            cameras = session_tr_id.get('cameras')
            data = formset.cleaned_data
            selected_ono = []
            unselected_ono = []
            selected = zip(ono, data)
            for ono, data in selected:
                if bool(data):
                    selected_ono.append(ono)
                else:
                    unselected_ono.append(ono)
            if selected_ono:
                if len(selected_ono) > 1:
                    messages.warning(request, 'Было выбрано более 1 ресурса')
                    return redirect('resources_formset', trID)
                else:
                    for i in unselected_ono:
                        if selected_ono[0][-2] == i[-2]:
                            selected_ono.append(i)
                    if cameras:
                        client_ip_addresses = get_ip_from_subset(selected_ono[0][-4])
                        cameras = [camera for camera in cameras if camera.get('ip') in client_ip_addresses]
                        session_tr_id.update({'cameras': cameras})
                    if phone_address:
                        if any(phone_addr in selected_ono[0][3] for phone_addr in phone_address):
                            phone_exist = True
                        else:
                            phone_exist = False
                    else:
                        phone_exist = False
                    session_tr_id.update({'phone_exist': phone_exist, 'selected_ono': selected_ono})
                    request.session[trID] = session_tr_id
                    return redirect('forming_header', trID)
            else:
                messages.warning(request, 'Ресурсы не выбраны')
                return redirect('resources_formset', trID)
    else:
        if session_tr_id.get('ticket_tr_id'):
            ticket_tr_id = session_tr_id.get('ticket_tr_id')
            ticket_tr = TR.objects.get(id=ticket_tr_id)
            task_otpm = ticket_tr.ticket_k.task_otpm
        else:
            task_otpm = None
        formset = ListResourcesFormSet()
        ono_for_formset = []
        for resource_for_formset in ono:
            resource_for_formset.pop(2)
            resource_for_formset.pop(1)
            resource_for_formset.pop(0)
            ono_for_formset.append(resource_for_formset)
        context = {
            'ono_for_formset': ono_for_formset,
            'formset': formset,
            'task_otpm': task_otpm,
            'trID': trID
        }
        return render(request, 'tickets/resources_formset.html', context)


def job_formset(request, trID):
    """Данный метод получает спискок услуг из ТР. Отображает форму, в которой пользователь для каждой услуги выбирает
    необходимое действие(перенос, изменение, организация) и формируется соответствующие списки услуг."""
    session_tr_id = request.session[str(trID)]
    head = session_tr_id.get('head')
    ticket_tr_id = session_tr_id.get('ticket_tr_id')
    ticket_tr = TR.objects.get(id=ticket_tr_id)
    oattr = ticket_tr.oattr
    pps = ticket_tr.pps
    services = splice_services(ticket_tr.services)

    ListJobsFormSet = formset_factory(ListJobsForm, extra=len(services))
    if request.method == 'POST':
        formset = ListJobsFormSet(request.POST)
        if formset.is_valid():
            pass_job_services = []
            change_job_services = []
            new_job_services = []
            data = formset.cleaned_data
            selected = zip(services, data)
            for services, data in selected:
                if data == {'jobs': 'Организация/Изменение, СПД'}:
                    new_job_services.append(services)
                elif data == {'jobs': 'Перенос, СПД'}:
                    pass_job_services.append(services)
                elif data == {'jobs': 'Изменение, не СПД'}:
                    change_job_services.append(services)
                elif data == {'jobs': 'Не требуется'}:
                    pass
            tag_service = []
            tag_service.append({'job_formset': None})
            session_tr_id.update({'tag_service': tag_service, 'new_job_services': new_job_services,
                                  'pass_job_services': pass_job_services, 'change_job_services': change_job_services})
            request.session[trID] = session_tr_id
            return redirect('project_tr_exist_cl', trID)
    else:
        ticket_tr_id = session_tr_id.get('ticket_tr_id')
        ticket_tr = TR.objects.get(id=ticket_tr_id)
        dID = ticket_tr.ticket_k.dID
        session_tr_id.update({'dID': dID})
        request.session[trID] = session_tr_id
        formset = ListJobsFormSet()
        context = {
            'head': head,
            'oattr': oattr,
            'pps': pps,
            'services': services,
            'formset': formset,
            'ticket_spp_id': session_tr_id.get('ticket_spp_id'),
            'dID': dID,
            'ticket_tr': ticket_tr,
            'trID': trID
        }
        return render(request, 'tickets/job_formset.html', context)


def forming_header(request, trID):
    """Данный метод проверяет если клиент подключен через CSW или WDA, то проверяет наличие на этих устройтсвах других
     договоров и если есть такие договоры, то добавляет их ресурсы в список выбранных ресурсов с договора клиента."""
    user = User.objects.get(username=request.user.username)
    username, password = get_user_credential_cordis(user)
    session_tr_id = request.session[str(trID)]
    selected_ono = session_tr_id.get('selected_ono')

    selected_client = selected_ono[0][0]
    selected_device = selected_ono[0][-2]

    if selected_device.startswith('CSW') or selected_device.startswith('WDA'):
        extra_selected_ono = _get_extra_selected_ono(username, password, selected_device, selected_client)
        if extra_selected_ono:
            for i in extra_selected_ono:
                selected_ono.append(i)
    session_tr_id.update({'selected_device': selected_device, 'selected_client': selected_client, 'selected_ono': selected_ono})
    request.session[trID] = session_tr_id
    return redirect('forming_chain_header', trID)


def forming_chain_header(request, trID):
    """Данный метод собирает данные обо всех устройствах через которые подключен клиент и отправляет на страницу
    формирования заголовка из этих данных"""
    user = User.objects.get(username=request.user.username)
    username, password = get_user_credential_cordis(user)
    session_tr_id = request.session[str(trID)]
    chain_device = session_tr_id.get('selected_device')
    selected_ono = session_tr_id.get('selected_ono')
    phone_exist = session_tr_id.get('phone_exist')
    chains = _get_chain_data(username, password, chain_device)
    if chains:
        downlink = _get_downlink(chains, chain_device)
        node_device = _get_node_device(chains, chain_device)
        nodes_vgw = []
        if phone_exist or node_device.endswith(', КК') or node_device.endswith(', WiFi'):
            vgw_on_node = _get_vgw_on_node(chains, chain_device)
            if vgw_on_node:
                nodes_vgw.append(chain_device)
        max_level = 20
        uplink, max_level = _get_uplink(chains, chain_device, max_level)
        all_chain = _get_all_chain(chains, chain_device, uplink, max_level)
        selected_client = 'No client'
        if all_chain[0] == None:
            node_uplink = node_device
            if phone_exist:
                extra_node_device = _get_extra_node_device(chains, chain_device, node_device)
                if extra_node_device:
                    for extra in extra_node_device:
                        extra_chains = _get_chain_data(username, password, extra)
                        extra_vgw = _get_vgw_on_node(extra_chains, extra)
                        if extra_vgw:
                            nodes_vgw.append(extra)
        else:
            node_uplink = _get_node_device(chains, all_chain[-1].split()[0])
            for all_chain_device in all_chain:
                if all_chain_device.startswith('CSW'):
                    extra_chains = _get_chain_data(username, password, all_chain_device)
                    extra_vgw = _get_vgw_on_node(extra_chains, all_chain_device)
                    if extra_vgw:
                        nodes_vgw.append(all_chain_device)
                    extra_selected_ono = _get_extra_selected_ono(username, password, all_chain_device, selected_client)
                    if extra_selected_ono:
                        for i in extra_selected_ono:
                            selected_ono.append(i)
        if downlink:
            for link_device in downlink:
                extra_vgw = _get_vgw_on_node(chains, link_device)
                if extra_vgw:
                    nodes_vgw.append(link_device)
                extra_selected_ono = _get_extra_selected_ono(username, password, link_device, selected_client)
                if extra_selected_ono:
                    for i in extra_selected_ono:
                        selected_ono.append(i)

        all_vgws = []
        if nodes_vgw:
            for i in nodes_vgw:
                parsing_vgws = _parsing_vgws_by_node_name(username, password, Switch=i)
                for vgw in parsing_vgws:
                    all_vgws.append(vgw)
        selected_clients_for_vgw = [client[0] for client in selected_ono]
        contracts_for_vgw = list(set(selected_clients_for_vgw))
        selected_vgw, waste_vgw = check_client_on_vgw(contracts_for_vgw, all_vgws, username, password)
        session_tr_id.update({'node_mon': node_uplink, 'uplink': all_chain, 'downlink': downlink,
                              'vgw_chains': selected_vgw, 'waste_vgw': waste_vgw})
        request.session[trID] = session_tr_id
        return redirect('head', trID)
    else:
        messages.warning(request, 'Не удалось получить логическое подключение')
        return redirect('ortr')


def head(request, trID):
    """Данный метод приводит данные для заголовка в читаемый формат на основе шаблона в КБЗ и отправляет на страницу
    выбора шаблонов для ТР"""
    user = User.objects.get(username=request.user.username)
    username, password = get_user_credential_cordis(user)
    session_tr_id = request.session[str(trID)]
    node_mon = session_tr_id.get('node_mon')
    uplink = session_tr_id.get('uplink')
    downlink = session_tr_id.get('downlink')
    vgw_chains = session_tr_id.get('vgw_chains')
    selected_ono = session_tr_id.get('selected_ono')
    waste_vgw = session_tr_id.get('waste_vgw')
    cameras = session_tr_id.get('cameras')
    templates = ckb_parse(username, password)
    result_services = []
    switch_config = None
    static_vars = {}
    hidden_vars = {}
    stroka = templates.get("Заголовок")
    static_vars['указать номер договора'] = selected_ono[0][0]
    static_vars['указать название клиента'] = selected_ono[0][1]
    static_vars['указать точку подключения'] = selected_ono[0][3]
    node_templates = {', РУА': 'РУА ', ', УА': 'УПА ', ', АВ': 'ППС ', ', КК': 'КК ', ', WiFi': 'WiFi '}
    for key, item in node_templates.items():
        if node_mon.endswith(key):
            finish_node = item + node_mon[:node_mon.index(key)]
            session_tr_id.update({'independent_pps': node_mon})
    static_vars['указать узел связи'] = finish_node
    if uplink == [None]:
        static_vars['указать название коммутатора'] = selected_ono[0][-2]
        session_tr_id.update({'independent_kad': selected_ono[0][-2]})
        static_vars['указать порт'] = selected_ono[0][-1]
        index_of_device = stroka.index('<- порт %указать порт%>') + len('<- порт %указать порт%>') + 1
        stroka = stroka[:index_of_device] + ' \n' + stroka[index_of_device:]
    else:
        static_vars['указать название коммутатора'] = uplink[-1].split()[0]
        session_tr_id.update({'independent_kad': uplink[-1].split()[0]})
        static_vars['указать порт'] = ' '.join(uplink[-1].split()[1:])
        list_stroka_device = []
        if len(uplink) > 1:
            for i in range(len(uplink)-2, -1, -1):
                extra_stroka_device = '- {}\n'.format(uplink[i])
                list_stroka_device.append(extra_stroka_device)
            if selected_ono[0][-2].startswith('WDA'):
                extra_stroka_device = '- {}\n'.format(_replace_wda_wds(selected_ono[0][-2]))
                list_stroka_device.append(extra_stroka_device)
                extra_stroka_device = '- {}\n'.format(selected_ono[0][-2])
                list_stroka_device.append(extra_stroka_device)
            else:
                extra_stroka_device = '- {}\n'.format(selected_ono[0][-2])
                list_stroka_device.append(extra_stroka_device)
        elif len(uplink) == 1:
            if selected_ono[0][-2].startswith('WDA'):
                extra_stroka_device = '- {}\n'.format(_replace_wda_wds(selected_ono[0][-2]))
                list_stroka_device.append(extra_stroka_device)
                extra_stroka_device = '- {}\n'.format(selected_ono[0][-2])
                list_stroka_device.append(extra_stroka_device)
            else:
                extra_stroka_device = '- {}\n'.format(selected_ono[0][-2])
                list_stroka_device.append(extra_stroka_device)
        if downlink:
            for i in range(len(downlink)-1, -1, -1):
                extra_stroka_device = '- {}\n'.format(downlink[i])
                list_stroka_device.append(extra_stroka_device)
        extra_extra_stroka_device = ''.join(list_stroka_device)
        index_of_device = stroka.index('<- порт %указать порт%>') + len('<- порт %указать порт%>') + 1
        stroka = stroka[:index_of_device] + extra_extra_stroka_device + ' \n' + stroka[index_of_device:]
    if selected_ono[0][-2].startswith('CSW'):
        old_model_csw, node_csw = _parsing_model_and_node_client_device_by_device_name(selected_ono[0][-2], username,
                                                                                       password)
        switch_config = get_sw_config(selected_ono[0][-2], old_model_csw, username, password)

        session_tr_id.update({'old_model_csw': old_model_csw, 'node_csw': node_csw})

    service_shpd = ['DA', 'BB', 'ine', 'Ine', '128 -', '53 -', '34 -', '33 -', '32 -', '45 -', '54 -', '55 -', '57 -', '60 -', '62 -',
                    '64 -', '67 -', '68 -', '92 -', '96 -', '101 -', '105 -', '125 -', '131 -', '107 -', '109 -', '483 -', '106 -',
                    '89 -', '138 -']
    service_shpd_bgp = ['BGP', 'bgp']
    service_portvk = ['-vk', 'vk-', '- vk', 'vk -', 'zhkh']
    service_portvm = ['-vrf', 'vrf-', '- vrf', 'vrf -']
    service_hotspot = ['hotspot']
    service_itv = ['itv']
    list_stroka_main_client_service = []
    list_stroka_other_client_service = []
    readable_services = dict()
    counter_exist_line = set()
    stick = False
    counter_stick = 0
    port_stick = set()
    for i in selected_ono:
        if selected_ono[0][0] == i[0]:
            if i[2] == 'IP-адрес или подсеть':
                if any(serv in i[-3] for serv in service_shpd_bgp) or '212.49.97.' in i[-4]:
                    extra_stroka_main_client_service = f'- услугу "Подключение по BGP" c реквизитами "{i[-4]}"({i[-2]} {i[-1]})\n'
                    if list_stroka_main_client_service:
                        for ind, main in enumerate(list_stroka_main_client_service):
                            if i[-1] in main:
                                main = main[
                                       :main.index('"(')] + f', услугу "Подключение по BGP" c реквизитами "{i[-4]}"' + main[
                                                                                                                   main.index(
                                                                                                                       '"('):]
                    list_stroka_main_client_service.append(extra_stroka_main_client_service)
                    curr_value = readable_services.get('"Подключение по BGP"')
                    readable_services = _readable(curr_value, readable_services, '"Подключение по BGP"', i[-4])
                    counter_exist_line.add(f'{i[-2]} {i[-1]}')
                elif any(serv in i[-3] for serv in service_shpd):
                    if switch_config:
                        service_ports = get_extra_service_port_csw(i[-1], switch_config, old_model_csw)
                        extra_stroka_main_client_service = f'- услугу "ШПД в интернет" c реквизитами "{i[-4]}"({i[-2]} {service_ports})\n'
                    else:
                        extra_stroka_main_client_service = f'- услугу "ШПД в интернет" c реквизитами "{i[-4]}"({i[-2]} {i[-1]})\n'
                    list_stroka_main_client_service.append(extra_stroka_main_client_service)
                    curr_value = readable_services.get('"ШПД в интернет"')
                    readable_services = _readable(curr_value, readable_services, '"ШПД в интернет"', i[-4])
                    counter_exist_line.add(f'{i[-2]} {i[-1]}')
                elif any(serv in i[-3].lower() for serv in service_hotspot):
                    if switch_config:
                        service_ports = get_extra_service_port_csw(i[-1], switch_config, old_model_csw)
                        extra_stroka_main_client_service = f'- услугу Хот-спот c реквизитами "{i[-4]}"({i[-2]} {service_ports})\n'
                    else:
                        extra_stroka_main_client_service = f'- услугу Хот-спот c реквизитами "{i[-4]}"({i[-2]} {i[-1]})\n'
                    list_stroka_main_client_service.append(extra_stroka_main_client_service)
                    curr_value = readable_services.get('Хот-спот')
                    readable_services = _readable(curr_value, readable_services, 'Хот-спот', i[-4])
                    counter_exist_line.add(f'{i[-2]} {i[-1]}')
                elif any(serv in i[-3].lower() for serv in service_itv):
                    if switch_config:
                        service_ports = get_extra_service_port_csw(i[-1], switch_config, old_model_csw)
                        extra_stroka_main_client_service = f'- услугу Вебург.ТВ c реквизитами "{i[-4]}"({i[-2]} {service_ports})\n'
                    else:
                        extra_stroka_main_client_service = f'- услугу Вебург.ТВ c реквизитами "{i[-4]}"({i[-2]} {i[-1]})\n'
                    list_stroka_main_client_service.append(extra_stroka_main_client_service)
                    curr_value = readable_services.get('Вебург.ТВ')
                    readable_services = _readable(curr_value, readable_services, 'Вебург.ТВ', i[-4])
                    counter_exist_line.add(f'{i[-2]} {i[-1]}')
            elif i[2] == 'Порт виртуального коммутатора':
                if any(serv in i[-3].lower() for serv in service_portvk):
                    extra_stroka_main_client_service = f'- услугу Порт ВЛС "{i[4]}"({i[-2]} {i[-1]})\n'
                    list_stroka_main_client_service.append(extra_stroka_main_client_service)
                    curr_value = readable_services.get('Порт ВЛС')
                    readable_services = _readable(curr_value, readable_services, 'Порт ВЛС', i[-4])
                    counter_exist_line.add(f'{i[-2]} {i[-1]}')
                elif any(serv in i[-3].lower() or serv in i[-4].lower() for serv in service_portvm):
                    extra_stroka_main_client_service = f'- услугу Порт ВМ "{i[4]}"({i[-2]} {i[-1]})\n'
                    list_stroka_main_client_service.append(extra_stroka_main_client_service)
                    curr_value = readable_services.get('Порт ВМ')
                    readable_services = _readable(curr_value, readable_services, 'Порт ВМ', i[-4])
                    counter_exist_line.add(f'{i[-2]} {i[-1]}')
            elif i[2] == 'Etherline':
                counter_stick += 1
                port_stick.add(i[-1])
                if 'Физический стык' in i[4]:
                    stick = True
                    break
                else:
                    if counter_stick == 5 and len(port_stick) == 1:
                        stick = True
                        break
                extra_stroka_main_client_service = f'- услугу ЦКС "{i[4]}"({i[-2]} {i[-1]})\n'
                list_stroka_main_client_service.append(extra_stroka_main_client_service)
                curr_value = readable_services.get('ЦКС')
                readable_services = _readable(curr_value, readable_services, 'ЦКС', i[-4])
                counter_exist_line.add(f'{i[-2]} {i[-1]}')
        else:
            if i[2] == 'IP-адрес или подсеть':
                if any(serv in i[-3] for serv in service_shpd):
                    extra_stroka_other_client_service = f'- услугу "ШПД в интернет" c реквизитами "{i[-4]}"({i[-2]} {i[-1]}) по договору {i[0]} {i[1]}\n'
                    list_stroka_other_client_service.append(extra_stroka_other_client_service)
                    counter_exist_line.add(f'{i[-2]} {i[-1]}')
                elif any(serv in i[-3].lower() for serv in service_hotspot):
                    extra_stroka_other_client_service = f'- услугу Хот-спот c реквизитами "{i[-4]}"({i[-2]} {i[-1]}) по договору {i[0]} {i[1]}\n'
                    list_stroka_other_client_service.append(extra_stroka_other_client_service)
                    counter_exist_line.add(f'{i[-2]} {i[-1]}')
                elif any(serv in i[-3].lower() for serv in service_itv):
                    extra_stroka_other_client_service = f'- услугу Вебург.ТВ c реквизитами "{i[-4]}"({i[-2]} {i[-1]}) по договору {i[0]} {i[1]}\n'
                    list_stroka_other_client_service.append(extra_stroka_other_client_service)
                    counter_exist_line.add(f'{i[-2]} {i[-1]}')
            elif i[2] == 'Порт виртуального коммутатора':
                if any(serv in i[-3].lower() for serv in service_portvk):
                    extra_stroka_other_client_service = f'- услугу Порт ВЛС "{i[4]}"({i[-2]} {i[-1]}) по договору {i[0]} {i[1]}\n'
                    list_stroka_other_client_service.append(extra_stroka_other_client_service)
                    counter_exist_line.add(f'{i[-2]} {i[-1]}')
                elif any(serv in i[-3].lower() for serv in service_portvm):
                    extra_stroka_other_client_service = f'- услугу Порт ВМ "{i[4]}"({i[-2]} {i[-1]}) по договору {i[0]} {i[1]}\n'
                    list_stroka_other_client_service.append(extra_stroka_other_client_service)
                    counter_exist_line.add(f'{i[-2]} {i[-1]}')
            elif i[2] == 'Etherline':
                extra_stroka_other_client_service = f'- услугу ЦКС "{i[4]}"({i[-2]} {i[-1]}) по договору {i[0]} {i[1]}\n'
                list_stroka_other_client_service.append(extra_stroka_other_client_service)
                counter_exist_line.add(f'{i[-2]} {i[-1]}')
    if not stick:
        if cameras:
            extra_stroka_main_client_service = f'- услугу Видеонаблюдение:\n'
            list_stroka_main_client_service.append(extra_stroka_main_client_service)
            for camera in cameras:
                extra_stroka_main_client_service = f"""-- "{camera.get('title')}" ({camera.get('summary')})\n"""
                list_stroka_main_client_service.append(extra_stroka_main_client_service)
        if vgw_chains:
            old_name_model_vgws = []
            for i in vgw_chains:
                model = i.get('model')
                name = i.get('name')
                vgw_uplink = i.get('uplink').replace('\r\n', '')
                room = i.get('type')
                if model == 'ITM SIP':
                    extra_stroka_main_client_service = f'- услугу "Телефония" через IP-транк {name} ({vgw_uplink})'
                    counter_exist_line.add(f'{vgw_uplink}')
                    readable_services.update({'"Телефония"': 'через IP-транк'})
                else:
                    extra_stroka_main_client_service = f'- услугу "Телефония" через тел. шлюз {model} {name} ({vgw_uplink}). Место установки: {room}\n'
                    old_name_model_vgws.append(f'{model} {name}')
                    readable_services.update({'"Телефония"': None})
                list_stroka_main_client_service.append(extra_stroka_main_client_service)
                readable_services.update({'"Телефония"': None})
            if old_name_model_vgws:
                session_tr_id.update({'old_name_model_vgws': ', '.join(old_name_model_vgws)})
        extra_extra_stroka_main_client_service = ''.join(list_stroka_main_client_service)
        extra_extra_stroka_other_client_service = ''.join(list_stroka_other_client_service)
        index_of_service = stroka.index('В данной точке %клиент потребляет/c клиентом организован L2-стык%') + len('В данной точке %клиент потребляет/c клиентом организован L2-стык%')+1
        stroka = stroka[:index_of_service] + extra_extra_stroka_main_client_service + '\n' + extra_extra_stroka_other_client_service + stroka[index_of_service:]
        if selected_ono[0][-2].startswith('CSW') or selected_ono[0][-2].startswith('WDA'):
            if waste_vgw:
                list_stroka_other_vgw =[]
                for i in waste_vgw:
                    model = i.get('model')
                    name = i.get('name')
                    vgw_uplink = i.get('uplink').replace('\r\n', '')
                    room = i.get('type')
                    contracts = i.get('contracts')
                    if bool(contracts) == False:
                        contracts = 'Нет контрактов'
                    if model == 'ITM SIP':
                        extra_stroka_other_vgw = f'Также есть подключение по IP-транк {name} ({vgw_uplink}). Контракт: {contracts}\n'
                    else:
                        extra_stroka_other_vgw = f'Также есть тел. шлюз {model} {name} ({vgw_uplink}). Контракт: {contracts}\n'
                    list_stroka_other_vgw.append(extra_stroka_other_vgw)
                extra_stroka_other_vgw = ''.join(list_stroka_other_vgw)
                stroka = stroka + '\n' + extra_stroka_other_vgw
        counter_exist_line = len(counter_exist_line)
        static_vars['клиент потребляет/c клиентом организован L2-стык'] = 'клиент потребляет:'
        if (selected_ono[0][-2].startswith('SW') and counter_exist_line > 1) or (selected_ono[0][-2].startswith('IAS') and counter_exist_line > 1) or (selected_ono[0][-2].startswith('AR') and counter_exist_line > 1):
            pass
        else:
            hidden_vars['- порт %указать порт%'] = '- порт %указать порт%'
    else:
        static_vars['клиент потребляет/c клиентом организован L2-стык'] = 'c клиентом организован L2-стык.'
        hidden_vars['- порт %указать порт%'] = '- порт %указать порт%'
        counter_exist_line = 0
        session_tr_id.update({'stick': True})
    result_services.append(analyzer_vars(stroka, static_vars, hidden_vars))
    result_services = ''.join(result_services)
    rev_result_services = result_services[::-1]
    index_of_head = rev_result_services.index('''-----------------------------------------------------------------------------------\n''')
    rev_result_services = rev_result_services[:index_of_head]
    head = rev_result_services[::-1]
    session_tr_id.update({'head': head.strip(), 'readable_services': readable_services,
                          'counter_exist_line': counter_exist_line})
    request.session[trID] = session_tr_id
    if session_tr_id.get('ticket_tr_id'):
        return redirect('job_formset', trID)
    else:
        return redirect('title_tr', trID)


def project_tr_exist_cl(request, trID):
    """Данный метод формирует последовательность url'ов по которым необходимо пройти для получения данных от
     пользователя и перенаправляет на первый из них. Используется для существующей точки подключения."""
    user = User.objects.get(username=request.user.username)
    ticket_tr = TR.objects.filter(ticket_tr=trID).last()
    session_tr_id = request.session[str(trID)]
    oattr = ticket_tr.oattr
    pps = ticket_tr.pps
    pps = pps.strip()
    turnoff = ticket_tr.turnoff
    task_otpm = ticket_tr.ticket_k.task_otpm
    services_plus_desc = ticket_tr.services
    des_tr = ticket_tr.ticket_k.des_tr
    address = None
    for i in range(len(des_tr)):
        if ticket_tr.ticket_tr in next(iter(des_tr[i].keys())):
            while address == None:
                if next(iter(des_tr[i].values())):
                    i -= 1
                else:
                    address = next(iter(des_tr[i].keys()))
                    address = address.replace(', д.', ' ')
    session_tr_id.update({'address': address})
    cks_points = []
    for point in des_tr:
        if next(iter(point.keys())).startswith('г.'):
            cks_points.append(next(iter(point.keys())).split('ул.')[1])
    session_tr_id.update({'cks_points': cks_points, 'services_plus_desc': services_plus_desc,
                          'task_otpm': task_otpm, 'pps': pps})
    if oattr:
        session_tr_id.update({'oattr': oattr})
        sreda = get_oattr_sreda(oattr)
    else:
        sreda = '1'
    new_job_services = session_tr_id.get('new_job_services')
    pass_job_services = session_tr_id.get('pass_job_services')
    change_job_services = session_tr_id.get('change_job_services')
    type_pass = []
    tag_service = session_tr_id.get('tag_service')
    if pass_job_services:
        if [service for service in pass_job_services if service.startswith('Видеонаблюдение')]:
            type_pass.append('Перенос Видеонаблюдение')
            tag_service.append({'pass_video': None})

        spd_services = ['Интернет', 'Порт ВЛС', 'Порт ВМ', 'ЦКС', 'Хот-спот']
        if [service for service in pass_job_services if any(service.startswith(serv) for serv in spd_services)]:
            type_pass.append('Перенос, СПД')
            tag_service.append({'pass_serv': None})


    if new_job_services:
        type_pass.append('Организация/Изменение, СПД')
        counter_line_services = _counter_line_services(new_job_services)
        tags = _tag_service_for_new_serv(new_job_services)
        for tag in tags:
            tag_service.append(tag)
        if change_job_services:
            type_pass.append('Изменение, не СПД')
            tags = _tag_service_for_new_serv(change_job_services)
            for tag in tags:
                tag_service.insert(1, tag)
                tag_service.insert(1, {'change_serv': None})

        spd = session_tr_id.get('spd')
        if counter_line_services == 0:
            tag_service.append({'data': None})
        elif user.groups.filter(name='Менеджеры').exists():
            tag_service.append({'copper': None})
        else:
            if spd == 'РТК':
                if tag_service[-1] in [{'copper': None}, {'vols': None}, {'wireless': None}]:
                    tag_service.pop()
                tag_service.append({'rtk': None})
            elif spd == 'Комтехцентр':
                if tag_service[-1] == {'rtk': None}:
                    tag_service.pop()

                if sreda == '1':
                    tag_service.append({'copper': None})
                elif sreda == '2' or sreda == '4':
                    tag_service.append({'vols': None})
                elif sreda == '3':
                    tag_service.append({'wireless': None})

        session_tr_id.update({'counter_line_services': counter_line_services,
                              'counter_line_services_initial': counter_line_services})

    if change_job_services and not new_job_services and not pass_job_services:
        type_pass.append('Изменение, не СПД')
        tags = _tag_service_for_new_serv(change_job_services)
        for tag in tags:
            tag_service.insert(1, {'change_serv': tag})
        tag_service.append({'data': None})

    session_tr_id.update({'oattr': oattr, 'pps': pps, 'turnoff': turnoff, 'sreda': sreda, 'type_pass': type_pass,
                          'tag_service': tag_service})
    response = get_response_with_prev_get_params(request, tag_service, session_tr_id, trID)
    return response


def change_serv(request, trID):
    """Данный метод отображает форму для выбора изменения услуги ШПД или организации услуг ШПД, ЦКС, порт ВК, порт ВМ
    без монтаж. работ"""
    if request.method == 'POST':
        changeservform = ChangeServForm(request.POST)
        if changeservform.is_valid():
            session_tr_id = request.session[str(trID)]
            type_change_service = changeservform.cleaned_data['type_change_service']
            try:
                types_change_service = session_tr_id['types_change_service']
            except KeyError:
                types_change_service = []
            types_cks_vk_vm_trunk = [
                "Организация порта ВМ trunk'ом",
                "Организация порта ВЛС trunk'ом",
                "Организация ЦКС trunk'ом",
                "Организация ШПД trunk'ом",
                "Организация ШПД trunk'ом с простоем",
                "Организация ЦКС trunk'ом с простоем",
                "Организация порта ВЛС trunk'ом с простоем",
                "Организация порта ВМ trunk'ом с простоем",
                "Изменение сервиса",
            ]
            types_only_mask = ["Организация доп connected",
                               "Организация доп маршрутизируемой",
                               "Замена connected на connected",
                               "Замена IP",
                               "Изменение cхемы организации ШПД",
                               ]
            tag_service = session_tr_id.get('tag_service')
            current_index_local = session_tr_id.get('current_index_local')

            if type_change_service in types_cks_vk_vm_trunk or type_change_service == "Организация доп IPv6":
                tag_service.insert(current_index_local + 1, next(iter(tag_service[current_index_local].values())))
                types_change_service.append(
                    {type_change_service: next(iter(tag_service[current_index_local + 1].values()))}
                )
            elif type_change_service in types_only_mask:
                tag_service.insert(current_index_local + 1, {'change_params_serv': None})
                types_change_service.append(
                    {type_change_service: tag_service[current_index_local]['change_serv']}
                )
            if tag_service[-1] != {'data': None}:
                tag_service.append({'data': None})
            session_tr_id.update({'types_change_service': types_change_service})
            session_tr_id.update({'tag_service': tag_service})
            response = get_response_with_get_params(request, tag_service, session_tr_id, trID)
            return response
    else:
        changeservform = ChangeServForm()
        session_tr_id = request.session[str(trID)]
        tag_service = session_tr_id.get('tag_service')
        service_name = 'change_serv'
        request, service, prev_page, index = backward_page_service(request, trID, service_name)
        current_index_local = index + 1
        if request.GET.get('next_page') and \
                next(iter(tag_service[current_index_local].values())) == tag_service[current_index_local+1]:
            removed_tag = tag_service.pop(current_index_local+1)
            types_change_service = session_tr_id.get('types_change_service')
            for type_change_service in types_change_service:
                if next(iter(type_change_service.values())) == next(iter(removed_tag.values())):
                    types_change_service.remove(type_change_service)
        elif request.GET.get('next_page') and tag_service[current_index_local+1] == {'change_params_serv': None}:
            types_change_service = session_tr_id.get('types_change_service')
            tag_service.pop(current_index_local + 1)
            for type_change_service in types_change_service:
                if next(iter(type_change_service.values())) == tag_service[current_index_local]['change_serv']:
                    types_change_service.remove(type_change_service)
        session_tr_id.update({'current_index_local': current_index_local})
        request.session[trID] = session_tr_id
        service_change = next(iter(service.values()))

        context = {
            'changeservform': changeservform,
            'service': service_change,
            'back_link': reverse(next(iter(tag_service[index])), kwargs={'trID': trID}) + f'?next_page={prev_page}&index={index}',
            'ticket_spp_id': session_tr_id.get('ticket_spp_id'),
            'dID': session_tr_id.get('dID'),
            'trID': trID
        }
        return render(request, 'tickets/change_serv.html', context)


def change_params_serv(request, trID):
    """Данный метод отображает форму с параметрами услуги ШПД(новая подсеть/маршрутизируемая подсеть)"""
    if request.method == 'POST':
        changeparamsform = ChangeParamsForm(request.POST)
        if changeparamsform.is_valid():
            session_tr_id = request.session[str(trID)]
            session_tr_id.update({**changeparamsform.cleaned_data})
            tag_service = session_tr_id.get('tag_service')
            if {'data': None} not in tag_service:
                tag_service.append({'data': None})
            response = get_response_with_get_params(request, tag_service, session_tr_id, trID)
            return response
    else:
        session_tr_id = request.session[str(trID)]
        head = session_tr_id.get('head')
        tag_service = session_tr_id.get('tag_service')
        types_change_service = session_tr_id.get('types_change_service')
        prev_page, index = backward_page(request, trID)
        only_mask = False
        routed = False
        for i in range(len(types_change_service)):
            types_only_mask = ["Организация доп connected",
                               "Замена connected на connected",
                               "Изменение cхемы организации ШПД"
                               ]
            if next(iter(types_change_service[i].keys())) in types_only_mask:
                only_mask = True
            if next(iter(types_change_service[i].keys())) == "Организация доп маршрутизируемой":
                routed = True
            parent_subnet = True if next(iter(types_change_service[i].keys())) == "Замена IP" else False

        changeparamsform = ChangeParamsForm()
        context = {
            'head': head,
            'changeparamsform': changeparamsform,
            'only_mask': only_mask,
            'routed': routed,
            'parent_subnet': parent_subnet,
            'back_link': reverse(next(iter(tag_service[index])), kwargs={'trID': trID}) + f'?next_page={prev_page}&index={index}',
            'ticket_spp_id': session_tr_id.get('ticket_spp_id'),
            'dID': session_tr_id.get('dID'),
            'trID': trID
        }
        return render(request, 'tickets/change_params_serv.html', context)


def change_log_shpd(request, trID):
    """Данный метод отображает форму выбора для услуги ШПД новой адресации или существующей"""
    if request.method == 'POST':
        changelogshpdform = ChangeLogShpdForm(request.POST)
        if changelogshpdform.is_valid():
            session_tr_id = request.session[str(trID)]
            session_tr_id.update({**changelogshpdform.cleaned_data})
            tag_service = session_tr_id.get('tag_service')
            csw_exist = [
                session_tr_id.get('logic_csw'),
                session_tr_id.get('logic_replace_csw'),
                session_tr_id.get('logic_change_gi_csw'),
                session_tr_id.get('logic_change_csw'),
            ]
            csw_change_exist = [
                session_tr_id.get('logic_change_gi_csw'),
                session_tr_id.get('logic_change_csw'),
            ]
            if tag_service[-1] == {'change_log_shpd': None} and any(csw_change_exist):
                type_pass = session_tr_id.get('type_pass')
                if 'Организация/Изменение, СПД' in type_pass and 'Перенос, СПД' not in type_pass:
                    tag_service.append({'pass_serv': None})
            if tag_service[-1] == {'change_log_shpd': None} and any(csw_exist):
                tag_service.append({'csw': None})
            elif tag_service[-1] == {'change_log_shpd': None}:
                tag_service.append({'data': None})
            response = get_response_with_get_params(request, tag_service, session_tr_id, trID)
            return response
    else:
        session_tr_id = request.session[str(trID)]
        head = session_tr_id.get('head')
        kad = session_tr_id.get('kad') if session_tr_id.get('spd') != 'РТК' else 'РТК'
        subnet_for_change_log_shpd = session_tr_id.get('subnet_for_change_log_shpd')
        changelogshpdform = ChangeLogShpdForm()
        if session_tr_id.get('pass_job_services'):
            services = session_tr_id.get('pass_job_services')
        elif session_tr_id.get('new_job_services'):
            services = session_tr_id.get('new_job_services')
        else:
            services = None
        tag_service = session_tr_id.get('tag_service')
        prev_page, index = backward_page(request, trID)
        context = {
            'head': head,
            'kad': kad,
            'subnet_for_change_log_shpd': subnet_for_change_log_shpd,
            'pass_job_services': services,
            'changelogshpdform': changelogshpdform,
            'back_link': reverse(next(iter(tag_service[index])), kwargs={'trID': trID}) + f'?next_page={prev_page}&index={index}',
            'ticket_spp_id': session_tr_id.get('ticket_spp_id'),
            'dID': session_tr_id.get('dID'),
            'trID': trID
        }
        return render(request, 'tickets/change_log_shpd.html', context)


def params_extend_service(request, trID):
    """Данный метод отображает форму с параметрами скорости и ограничения полосы для расширения услуг ЦКС, порт ВК,
    порт ВМ"""
    if request.method == 'POST':
        extendserviceform = ExtendServiceForm(request.POST)
        if extendserviceform.is_valid():
            session_tr_id = request.session[str(trID)]
            session_tr_id.update({**extendserviceform.cleaned_data})
            tag_service = session_tr_id.get('tag_service')
            if tag_service[-1] == {'params_extend_service': None}:
                tag_service.append({'data': None})
            response = get_response_with_get_params(request, tag_service, session_tr_id, trID)
            return response

    else:
        session_tr_id = request.session[str(trID)]
        extendserviceform = ExtendServiceForm()
        tag_service = session_tr_id.get('tag_service')
        prev_page, index = backward_page(request, trID)
        context = {
            'desc_service': session_tr_id.get('desc_service'),
            'type_passage': session_tr_id.get('type_passage'),
            'pass_job_services': session_tr_id.get('pass_job_services'),
            'extendserviceform': extendserviceform,
            'back_link': reverse(next(iter(tag_service[index])), kwargs={'trID': trID}) + f'?next_page={prev_page}&index={index}',
            'ticket_spp_id': session_tr_id.get('ticket_spp_id'),
            'dID': session_tr_id.get('dID'),
            'trID': trID
        }
        return render(request, 'tickets/params_extend_service.html', context)


def pass_serv(request, trID):
    """Данный метод отображает форму с параметрами переноса/расширения услуг"""
    if request.method == 'POST':
        passservform = PassServForm(request.POST)
        if passservform.is_valid():
            session_tr_id = request.session[str(trID)]
            session_tr_id.update({**passservform.cleaned_data})
            type_passage = passservform.cleaned_data['type_passage']
            change_log = passservform.cleaned_data['change_log']
            tag_service = session_tr_id.get('tag_service')
            tag_service_index = session_tr_id.get('tag_service_index')
            index = tag_service_index[-1]
            readable_services = session_tr_id.get('readable_services')
            selected_ono = session_tr_id.get('selected_ono')
            type_pass = session_tr_id.get('type_pass')
            sreda = session_tr_id.get('sreda')
            if 'Перенос, СПД' not in type_pass:
                if tag_service[-1] == {'pass_serv': None}:
                    tag_service.append({'csw': None})
                response = get_response_with_get_params(request, tag_service, session_tr_id, trID)
                return response
            else:
                pass_job_services = session_tr_id.get('pass_job_services')
                if change_log == 'Порт и КАД не меняется':
                    if type_passage == 'Перевод на гигабит':
                        desc_service, _ = get_selected_readable_service(readable_services, selected_ono)
                        if desc_service in ['ЦКС', 'Порт ВЛС', 'Порт ВМ']:
                            session_tr_id.update({'desc_service': desc_service})
                            tag_service.append({'params_extend_service': None})
                            response = get_response_with_get_params(request, tag_service, session_tr_id, trID)
                            return response
                    elif (type_passage == 'Перенос точки подключения' or type_passage == 'Перенос логического подключения') and session_tr_id.get('turnoff'):
                        tag_service.append({'pass_turnoff': None})
                        response = get_response_with_get_params(request, tag_service, session_tr_id, trID)
                        return response
                else:
                    desc_service, _ = get_selected_readable_service(readable_services, selected_ono)
                    if desc_service in ['ЦКС', 'Порт ВЛС', 'Порт ВМ']:
                        session_tr_id.update({'desc_service': desc_service})
                        tag_service.append({'params_extend_service': None})
                    phone_in_pass = [x for x in pass_job_services if x.startswith('Телефон')]
                    if phone_in_pass and 'CSW' not in session_tr_id.get('selected_ono')[0][-2]:
                        tag_service.append({'phone': ''.join(phone_in_pass)})
                        session_tr_id.update({'phone_in_pass': ' '.join(phone_in_pass)})
                    if any(tag in tag_service for tag in [{'copper': None}, {'vols': None}, {'wireless': None}]):
                        pass
                    else:
                        if {'data': None} in tag_service:
                            tag_service.remove({'data': None})

                        spd = session_tr_id.get('spd')
                        if spd == 'РТК':
                            tag_service.append({'rtk': None})
                        elif spd == 'ППМ':

                            tag_service = append_change_log_shpd(session_tr_id)
                        elif spd == 'Комтехцентр':
                            if sreda == '1':
                                tag_service.append({'copper': None})
                            elif sreda == '2' or sreda == '4':
                                tag_service.append({'vols': None})
                            elif sreda == '3':
                                tag_service.append({'wireless': None})

                if tag_service[-1] == {'pass_serv': None}:
                    tag_service.append({'data': None})
                response = get_response_with_get_params(request, tag_service, session_tr_id, trID)
                return response
    else:
        session_tr_id = request.session[str(trID)]
        tag_service = session_tr_id.get('tag_service')
        prev_page, index = backward_page(request, trID)
        if request.GET.get('next_page'):
            clear_session_params(
                session_tr_id,
                'type_passage',
                'change_log',
                'exist_sreda',
            )
        request.session[trID] = session_tr_id
        passservform = PassServForm()
        context = {
            'passservform': passservform,
            'oattr': session_tr_id.get('oattr'),
            'pps': session_tr_id.get('pps'),
            'head': session_tr_id.get('head'),
            'back_link': reverse(next(iter(tag_service[index])), kwargs={'trID': trID}) + f'?next_page={prev_page}&index={index}',
            'ticket_spp_id': session_tr_id.get('ticket_spp_id'),
            'dID': session_tr_id.get('dID'),
            'trID': trID
        }
        return render(request, 'tickets/pass_serv.html', context)


# def pass_video(request, trID):
#     if request.method == 'POST':
#         form = PassVideoForm(request.POST)
#         if form.is_valid():
#             session_tr_id = request.session[str(trID)]
#             session_tr_id.update({**form.cleaned_data})
#     else:
#         session_tr_id = request.session[str(trID)]
#         tag_service = session_tr_id.get('tag_service')
#         prev_page, index = backward_page(request, trID)
#
#         request.session[trID] = session_tr_id
#         form = PassVideoForm()
#         context = {
#             'form': form,
#             'oattr': session_tr_id.get('oattr'),
#             'pps': session_tr_id.get('pps'),
#             'head': session_tr_id.get('head'),
#             'back_link': reverse(next(iter(tag_service[index])), kwargs={'trID': trID}) + f'?next_page={prev_page}&index={index}',
#             'ticket_spp_id': session_tr_id.get('ticket_spp_id'),
#             'dID': session_tr_id.get('dID'),
#             'trID': trID
#         }
#         return render(request, 'tickets/pass_video.html', context)


class PassVideoFormView(FormView):
    template_name = "tickets/pass_video.html"
    form_class = PassVideoForm

    def form_valid(self, form):
        pass_video_form = dict(**form.cleaned_data)
        session_tr_id = self.request.session[str(self.kwargs['trID'])]
        session_tr_id.update({'pass_video_form': pass_video_form})
        self.request.session[str(self.kwargs['trID'])] = session_tr_id
        return super().form_valid(form)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        prev_page, index = backward_page(self.request, self.kwargs['trID'])
        session_tr_id = self.request.session[str(self.kwargs['trID'])]
        tag_service = session_tr_id.get('tag_service')
        ticket_tr_id = session_tr_id.get('ticket_tr_id')
        back_link = reverse(next(iter(tag_service[index])), kwargs={'trID': self.kwargs["trID"]}) + f'?next_page={prev_page}&index={index}'
        context['back_link'] = back_link
        context['pps'] = session_tr_id.get('pps')
        context['oattr'] = session_tr_id.get('oattr')
        context['head'] = session_tr_id.get('head')
        context['ticket_spp_id'] = session_tr_id.get('ticket_spp_id')
        context['dID'] = session_tr_id.get('dID')
        context['trID'] = self.kwargs['trID']
        return context

    def get_success_url(self, **kwargs):
        session_tr_id = self.request.session[str(self.kwargs['trID'])]
        tag_service = session_tr_id.get('tag_service')
        self.request.session[str(self.kwargs['trID'])] = session_tr_id
        tag_service.append({'data': None})
        tag_service_index = session_tr_id.get('tag_service_index')
        index = tag_service_index[-1] + 1
        tag_service_index.append(index)
        session_tr_id.update({'tag_service': tag_service, 'tag_service_index': tag_service_index})
        self.request.session[str(self.kwargs['trID'])] = session_tr_id
        url = f"{reverse(next(iter(tag_service[index + 1])), kwargs={'trID': self.kwargs['trID']})}?prev_page={next(iter(tag_service[index]))}&index={index}"
        return url



def pass_turnoff(request, trID):
    """Данный метод отображает форму для ввода ППР на случае если в ТР осуществляется перенос услуг без изменения
    логического подключения, но при этом в ТР заказано отключение других клиентов"""
    if request.method == 'POST':
        passturnoffform = PassTurnoffForm(request.POST)
        if passturnoffform.is_valid():
            session_tr_id = request.session[str(trID)]
            session_tr_id.update({**passturnoffform.cleaned_data})
            tag_service = session_tr_id.get('tag_service')
            if tag_service[-1] == {'pass_turnoff': None}:
                tag_service.append({'data': None})
            response = get_response_with_get_params(request, tag_service, session_tr_id, trID)
            return response
    else:
        session_tr_id = request.session[str(trID)]
        tag_service = session_tr_id.get('tag_service')
        prev_page, index = backward_page(request, trID)
        ticket_tr_id = session_tr_id.get('ticket_tr_id')
        ticket_tr = TR.objects.get(id=ticket_tr_id)
        passturnoffform = PassTurnoffForm()
        context = {
            'passturnoffform': passturnoffform,
            'oattr': session_tr_id.get('oattr'),
            'pps': session_tr_id.get('pps'),
            'head': session_tr_id.get('head'),
            'ticket_tr': ticket_tr,
            'trID': trID,
            'back_link': reverse(next(iter(tag_service[index])), kwargs={'trID': trID}) + f'?next_page={prev_page}&index={index}',
            'ticket_spp_id': session_tr_id.get('ticket_spp_id'),
            'dID': session_tr_id.get('dID')
        }
        return render(request, 'tickets/pass_turnoff.html', context)


def search(request):
    """Данный метод отображает html-страницу с поиском заявок"""
    searchticketsform = SearchTicketsForm(request.GET)
    if searchticketsform.is_valid():
        spp = searchticketsform.cleaned_data['spp']
        tr = searchticketsform.cleaned_data['tr']
        pps = searchticketsform.cleaned_data['pps']
        connection_point = searchticketsform.cleaned_data['connection_point']
        ortr = searchticketsform.cleaned_data['ortr']
        client = searchticketsform.cleaned_data['client']
        start = searchticketsform.cleaned_data['start']
        stop = searchticketsform.cleaned_data['stop']
        titles = searchticketsform.cleaned_data['titles']
        initial_params = {}
        if spp:
            initial_params.update({'spp': spp})
        if tr:
            initial_params.update({'tr': tr})
        if pps:
            initial_params.update({'pps': pps})
        if pps:
            initial_params.update({'connection_point': connection_point})
        if client:
            initial_params.update({'client': client})
        if ortr:
            initial_params.update({'ortr': ortr})
        if start:
            initial_params.update({'start': start})
        if stop:
            initial_params.update({'stop': stop})
        if titles:
            initial_params.update({'titles': titles})

        searchticketsform = SearchTicketsForm(initial=initial_params)
        context = {
            'searchticketsform': searchticketsform,
        }
        if request.GET:
            query = None
            if request.GET.get('spp'):
                query_spp = Q(ticket_k__ticket_k__icontains=spp)
                query = query_spp if query is None else query & query_spp
            if request.GET.get('tr'):
                query_tr = Q(ticket_tr__icontains=tr)
                query = query_tr if query is None else query & query_tr
            if request.GET.get('pps'):
                query_pps = Q(pps__icontains=pps)
                query = query_pps if query is None else query & query_pps
            if request.GET.get('connection_point'):
                query_connection_point = Q(connection_point__icontains=connection_point)
                query = query_connection_point if query is None else query & query_connection_point
            if request.GET.get('client'):
                query_client = Q(ticket_k__client__icontains=client)
                query = query_client if query is None else query & query_client
            if request.GET.get('ortr'):
                query_ortr = Q(ortrtr__ortr__icontains=ortr) | Q(ortrtr__ots__icontains=ortr)
                query = query_ortr if query is None else query & query_ortr
            if request.GET.get('start'):
                query_start = Q(ticket_k__created__gte=start)
                query = query_start if query is None else query & query_start
            if request.GET.get('stop'):
                query_stop = Q(ticket_k__complited__lt=stop)
                query = query_stop if query is None else query & query_stop
            if request.GET.get('titles'):
                query_titles = Q(ortrtr__titles__icontains=titles)
                query = query_titles if query is None else query & query_titles
            if query is not None:
                results = TR.objects.filter(query).order_by('-ticket_k__created')
                paginator = Paginator(results, 50)
                page_number = request.GET.get('page')
                page_obj = paginator.get_page(page_number)
                context.update({'page_obj': page_obj})

    else:
        context = {
            'searchticketsform': searchticketsform
        }
    return render(request, 'tickets/search.html', context)

def free_ppr(request):
    """Данный метод для выполнения ppr создает в сессии индекс не связанный не с одним ТР"""
    not_exists_trid = 1
    request.session[not_exists_trid] = {}
    return redirect('ppr', not_exists_trid)


def ppr(request, trID):
    """Данный метод отображает html-страничку c формой для выбора новой или сущ. ППР"""
    user = User.objects.get(username=request.user.username)
    username, password = get_user_credential_cordis(user)
    if request.method == 'POST':
        pprform = PprForm(request.POST)
        if pprform.is_valid():
            new_ppr = pprform.cleaned_data['new_ppr']
            title_ppr = pprform.cleaned_data['title_ppr']
            exist_ppr = pprform.cleaned_data['exist_ppr']
            session_tr_id = request.session[str(trID)]
            if new_ppr and exist_ppr:
                messages.warning(request, 'Не может быть одновременно новой и существующей ППР')
                return redirect('ppr', trID)
            elif new_ppr is False and exist_ppr == '':
                messages.warning(request, 'Должна быть выбрана либо новая либо существующая ППР')
                return redirect('ppr', trID)
            elif exist_ppr:
                session_tr_id.update({'exist_ppr': exist_ppr.strip('#')})
                request.session[trID] = session_tr_id
                return redirect('add_resources_to_ppr', trID)
            if title_ppr == '':
                messages.warning(request, 'Для новой ППР должно быть заполнено поле Кратко')
                return redirect('ppr', trID)
            session_tr_id.update({'title_ppr': title_ppr})
            name_id_user_cis = get_name_id_user_cis(username, password, 'Салмин Н') #user.last_name
            if isinstance(name_id_user_cis, list):
                session_tr_id.update({'name_id_user_cis': name_id_user_cis})
                request.session[trID] = session_tr_id
                return redirect('author_id_formset', trID)
            elif isinstance(name_id_user_cis, dict):
                session_tr_id.update({'AuthorId': name_id_user_cis.get('id')})
                session_tr_id.update({'AuthorName': name_id_user_cis.get('value')})
                request.session[trID] = session_tr_id
                return redirect('create_ppr', trID)
            else:
                if name_id_user_cis == 'Фамилия, указанная в АРМ, в Cordis не найдена':
                    messages.warning(request, 'Фамилия, указанная в АРМ, в Cordis не найдена')
                    return redirect('private_page')
    else:
        pprform = PprForm()
        context = {'pprform': pprform, 'trID': trID
                   }
        return render(request, 'tickets/ppr.html', context)


def author_id_formset(request, trID):
    """Данный метод отображает форму, в которой пользователь выбирает свои ФИО в Cordis"""
    session_tr_id = request.session[str(trID)]
    name_id_user_cis = session_tr_id.get('name_id_user_cis')
    ListUserCisFormSet = formset_factory(ListContractIdForm, extra=len(name_id_user_cis))
    if request.method == 'POST':
        formset = ListUserCisFormSet(request.POST)
        if formset.is_valid():
            data = formset.cleaned_data
            selected_user_cis_id = []
            selected = zip(name_id_user_cis, data)
            for name_id_user_cis, data in selected:
                if bool(data):
                    selected_user_cis_id.append(name_id_user_cis)
            if selected_user_cis_id:
                if len(selected_user_cis_id) > 1:
                    messages.warning(request, 'Было выбрано более 1 ФИО')
                    return redirect('author_id_formset', trID)
                else:
                    session_tr_id.update({'AuthorId': selected_user_cis_id[0].get('id')})
                    session_tr_id.update({'AuthorName': selected_user_cis_id[0].get('value')})
                    request.session[trID] = session_tr_id
                    return redirect('create_ppr', trID)
            else:
                messages.warning(request, 'ФИО не выбраны')
                return redirect('author_id_formset', trID)
    else:
        formset = ListUserCisFormSet()
        context = {
            'contract_id': name_id_user_cis,
            'formset': formset,
            'trID': trID
        }
        return render(request, 'tickets/author_id_formset.html', context)


def create_ppr(request, trID):
    user = User.objects.get(username=request.user.username)
    username, password = get_user_credential_cordis(user)
    now = datetime.datetime.now()
    deadline = now + datetime.timedelta(days=5)
    deadline = deadline.strftime("%d.%m.%Y %H:%M:%S")
    session_tr_id = request.session[str(trID)]
    authorid = session_tr_id.get('AuthorId')
    title_ppr = session_tr_id.get('title_ppr')
    authorname = session_tr_id.get('AuthorName')
    url = 'https://cis.corp.itmh.ru/mvc/demand/CreateMaintenance'
    data = {'ExecutorName': f'{authorname}',
            'ExecutorID': f'{authorid}',
            'ScheduledIdlePeriod.FromDate': '01.01.2010 0:00',
            'ScheduledIdlePeriod.TrimDate': '01.01.2010 0:01',
            'ScheduledIdleSpan': '1м',
            'Main': f'{title_ppr}',
            'DemandID': '0',
            'WorkflowID': '306',
            'ReturnJSON': '0',
            'Deadline': deadline,
            'Priority': '3',
            'CreateMaintenance': 'Создать'
            }
    req = requests.post(url, verify=False, auth=HTTPBasicAuth(username, password), data=data)
    if req.status_code == 200 and title_ppr.replace('"', '&quot;') in req.content.decode('utf-8'):
        last_ppr = search_last_created_ppr(username, password, authorname, authorid)
        session_tr_id.update({'exist_ppr': last_ppr})
        request.session[trID] = session_tr_id
        if session_tr_id.get('technical_solution'):
            tr = session_tr_id.get('technical_solution')
            add_tr_to_last_created_ppr(username, password, authorname, authorid, title_ppr, deadline, last_ppr, tr)
        return redirect('add_resources_to_ppr', trID)
    else:
        messages.warning(request, 'Не удалось создать ППР либо не удалось определить созданную ППР')
        return redirect('ppr', trID)


def add_resources_to_ppr(request, trID):
    """Данный метод отображает html-страничку c формой для заполнения ППР"""
    user = User.objects.get(username=request.user.username)
    username, password = get_user_credential_cordis(user)
    if request.method == 'POST':
        addresourcespprform = AddResourcesPprForm(request.POST)
        if addresourcespprform.is_valid():
            ppr_resources = addresourcespprform.cleaned_data['ppr_resources']
            session_tr_id = request.session[str(trID)]
            services = get_services(ppr_resources)
            links = get_links(ppr_resources)
            ppr = int(session_tr_id.get('exist_ppr'))
            results = []
            for service in services:
                result = add_res_to_ppr(ppr, service, username, password)
                results.append(result)
            for link in links:
                result = add_links_to_ppr(ppr, link, username, password)
                results.append(result)
            session_tr_id.update({'added_resources_to_ppr': results})
            request.session[str(trID)] = session_tr_id
            return redirect('ppr_result', trID)

    else:
        session_tr_id = request.session[str(trID)]
        exist_ppr = session_tr_id.get('exist_ppr')
        addresourcespprform = AddResourcesPprForm()
        context = {'addresourcespprform': addresourcespprform,
                   'exist_ppr': exist_ppr,
                   'trID': trID
                   }
        return render(request, 'tickets/ppr_resources.html', context)


def ppr_result(request, trID):
    """Данный метод отображает html-страничку с данными о ТР для новой точки подключения"""
    session_tr_id = request.session[str(trID)]
    exist_ppr = session_tr_id.get('exist_ppr')
    resources = session_tr_id.get('added_resources_to_ppr')
    next_link = f'https://cis.corp.itmh.ru/index.aspx?demand={exist_ppr}'
    if trID == 1:
        del request.session[str(trID)]
    context = {
        'next_link': next_link,
        'exist_ppr': exist_ppr,
        'resources': resources,
        'trID': trID
    }
    return render(request, 'tickets/ppr_result.html', context)


def report_time_tracking(request):
    """Данный метод отображает html-страницу с формированием отчета"""
    if request.method == 'POST':
        timetrackingform = TimeTrackingForm(request.POST)
        if timetrackingform.is_valid():
            start = timetrackingform.cleaned_data['start']
            stop = timetrackingform.cleaned_data['stop']
            technolog = timetrackingform.cleaned_data['technolog']
            if start:
                start = start.strftime('%d.%m.%Y')
            if stop:
                stop = stop.strftime('%d.%m.%Y')
            request.session['report_time_tracking_start'] = start
            request.session['report_time_tracking_stop'] = stop
            request.session['technolog'] = technolog
            return redirect('export_xls')
    else:
        timetrackingform = TimeTrackingForm()
        context = {
            'timetrackingform': timetrackingform
        }
    return render(request, 'tickets/report_time_tracking.html', context)


def add_comment_to_return_ticket(request, dID):
    """Данный метод отображает html-страничку c формой для заполнения комментария к возвращаемой ТР"""
    user = User.objects.get(username=request.user.username)
    username, password = get_user_credential_cordis(user)
    ticket_spp = SPP.objects.filter(dID=dID).last()
    ticket_spp_id = ticket_spp.id
    if request.method == 'POST':
        addcommentform = AddCommentForm(request.POST)
        if addcommentform.is_valid():
            comment = addcommentform.cleaned_data['comment']
            comment = comment + f' (Комментарий добавил {user.last_name}.)'
            return_to = addcommentform.cleaned_data['return_to']
            uid = ticket_spp.uID
            trdifperiod = ticket_spp.trdifperiod
            trcuratorphone = ticket_spp.trcuratorphone
            ticket_k = ticket_spp.ticket_k
            if return_to == 'Вернуть в ОТПМ':
                status_save_to_otpm = save_to_otpm(username, password, dID, comment, uid, trdifperiod, trcuratorphone)
                if status_save_to_otpm == 200:
                    status_send_to_otpm = send_to_otpm(username, password, dID, uid, trdifperiod, trcuratorphone)
                if status_save_to_otpm != 200:
                    messages.warning(request, f'Заявку {ticket_k} не удалось вернуть в ОТПМ. Комментарий не сохранен.')
                    return redirect('spp_view_save', dID, ticket_spp_id)
                elif status_save_to_otpm == 200 and status_send_to_otpm!= 200:
                    messages.warning(request, f'Заявку {ticket_k} не удалось вернуть в ОТПМ. Комментарий сохранен.')
                    return redirect('spp_view_save', dID, ticket_spp_id)
                elif status_save_to_otpm == 200 and status_send_to_otpm == 200:
                    ticket_spp.projected = False
                    ticket_spp.process = False
                    ticket_spp.return_otpm = True
                    ticket_spp.save()
                    tickets_tr = ticket_spp.children.all()
                    for ticket_tr in tickets_tr:
                        if request.session.get(ticket_tr.ticket_tr):
                            del request.session[ticket_tr.ticket_tr]
                    messages.success(request, f'Заявка {ticket_k} возвращена в ОТПМ')
                    return redirect('ortr')
            elif return_to == 'Вернуть менеджеру':
                status_send_to_mko = send_to_mko(username, password, dID, comment)
                if status_send_to_mko != 200:
                    messages.warning(request, f'Заявку {ticket_k} не удалось вернуть менеджеру.')
                    return redirect('spp_view_save', dID, ticket_spp_id)
                ticket_spp.projected = False
                ticket_spp.process = False
                ticket_spp.return_mko = True
                ticket_spp.save()
                tickets_tr = ticket_spp.children.all()
                for ticket_tr in tickets_tr:
                    if request.session.get(ticket_tr.ticket_tr):
                        del request.session[ticket_tr.ticket_tr]
                messages.success(request, f'Заявка {ticket_k} возвращена менеджеру')
                return redirect('ortr')
    else:
        addcommentform = AddCommentForm()
        if user.groups.filter(name='Менеджеры').exists():
            addcommentform.fields['return_to'].widget.choices = [('Вернуть менеджеру', 'Вернуть менеджеру')]
        context = {'addcommentform': addcommentform,
                   'ticket_spp_id': ticket_spp_id,
                   'dID': dID,
                   }
        return render(request, 'tickets/return_comment.html', context)


def send_ticket_to_otpm_control(request, dID):
    """Данный метод завершает работу над заявкой отправленной в ОТПМ Контроль и выпуск"""
    user = User.objects.get(username=request.user.username)
    username, password = get_user_credential_cordis(user)
    ticket_spp = SPP.objects.filter(dID=dID).last()
    ticket_spp_id = ticket_spp.id
    uid = ticket_spp.uID
    trdifperiod = ticket_spp.trdifperiod
    trcuratorphone = ticket_spp.trcuratorphone
    ticket_k = ticket_spp.ticket_k
    if ticket_spp.simplified_tr is True:
        status_send_to_accept = send_to_accept(username, password, dID, uid, trdifperiod, trcuratorphone)
        if status_send_to_accept != 200:
            messages.warning(request, f'Заявку {ticket_k} не удалось отправить на Принятие ТР.')
            return redirect('spp_view_save', dID, ticket_spp_id)
    elif ticket_spp.type_ticket == 'ПТО':
        status_send_to_pto = send_to_pto(username, password, dID, uid, trdifperiod, trcuratorphone)
        if status_send_to_pto != 200:
            messages.warning(request, f'Заявку {ticket_k} не удалось отправить на ПТО.')
            return redirect('spp_view_save', dID, ticket_spp_id)
    else:
        status_send_to_otpm_control = send_to_otpm_control(username, password, dID, uid, trdifperiod, trcuratorphone)
        if status_send_to_otpm_control != 200:
            messages.warning(request, f'Заявку {ticket_k} не удалось отправить на ОТПМ Контроль и выпуск.')
            return redirect('spp_view_save', dID, ticket_spp_id)
    ticket_spp.process = False
    ticket_spp.save()
    tickets_tr = ticket_spp.children.all()
    for ticket_tr in tickets_tr:
        if request.session.get(ticket_tr.ticket_tr):
            del request.session[ticket_tr.ticket_tr]
    messages.success(request, f'Заявка {ticket_k} выполнена и отправлена.')
    if user.groups.filter(name='Менеджеры').exists():
        return redirect('mko')
    return redirect('ortr')


def export_xls(request):
    """Данный метод формирует эксел файл"""
    wb = xlwt.Workbook(encoding='utf-8')
    ws = wb.add_sheet('tickets')
    row_num = 0
    font_style = xlwt.XFStyle()
    font_style.font.bold = True
    columns = ['Дата', '№ Заявки', 'Клиент', 'Точка подключения', 'Время начала', 'Время окончания',
               'Продолжительность', 'Описание']
    for col_num in range(len(columns)):
        ws.write(row_num, col_num, columns[col_num], font_style)
    font_style = xlwt.XFStyle()
    technolog = request.session['technolog']
    start = request.session.get('report_time_tracking_start')
    start_datetime = datetime.datetime.strptime(start, "%d.%m.%Y")
    stop = request.session.get('report_time_tracking_stop')
    stop_datetime = datetime.datetime.strptime(stop, "%d.%m.%Y")
    query_start = Q(complited__gte=start_datetime)
    query_stop = Q(complited__lte=stop_datetime)
    query_wait = Q(wait=False)
    query = query_start & query_stop & query_wait
    rows = SPP.objects.filter(user__username=technolog).filter(query).order_by('created')
    rows = rows.annotate(formatted_date=F('created'))
    rows = rows.values_list('formatted_date',
                            'ticket_k',
                            'client',
                            'des_tr',
                            'created',
                            'complited',
                            'wait',
                            'projected',
                            'was_waiting'
                            )
    for row in rows:
        points_list = []
        row = list(row)
        row[0] = row[0].astimezone(timezone.get_current_timezone()).strftime('%d.%m.%Y')
        row[6] = row[5] - row[4]
        days = row[6].days
        hours, remainder = divmod(row[6].seconds, 3600)
        minutes, seconds = divmod(remainder, 60)
        row[6] = f'{hours+days*24:02}:{minutes:02}:{seconds:02}'

        row[4] = row[4].astimezone(timezone.get_current_timezone()).strftime('%H:%M:%S')
        row[5] = row[5].astimezone(timezone.get_current_timezone()).strftime('%H:%M:%S')

        if row[8] is True:
            row[7] = 'Ожидание'
        else:
            row[7] = 'ТР спроектировано' if row[7] is True else 'ТР не спроектировано'
        row.pop()
        for des in row[3]:
            points_list += [k for k, v in des.items() if 'г.' in k]
        points = '\r\n'.join(points_list)
        row[3] = points
        row_num += 1
        for col_num in range(len(row)):
            ws.write(row_num, col_num, row[col_num], font_style)

    response = HttpResponse(content_type='application/ms-excel')
    technolog = formatted(technolog)
    start = formatted(start)
    stop = formatted(stop)
    response['Content-Disposition'] = f'attachment; filename="{technolog}-{start}-{stop}.xls"'
    wb.save(response)
    return response


class CredentialMixin:
    def get_credential(self, *args, **kwargs):
        user = User.objects.get(username=self.request.user.username)
        username, password = get_user_credential_cordis(user)
        return username, password



class RtkFormView(FormView, CredentialMixin):
    template_name = "tickets/rtk.html"
    form_class = RtkForm

    def form_valid(self, form):
        rtk_form = dict(**form.cleaned_data)
        session_tr_id = self.request.session[str(self.kwargs['trID'])]
        session_tr_id.update({'rtk_form': rtk_form})
        self.request.session[str(self.kwargs['trID'])] = session_tr_id
        return super().form_valid(form)

    def get_initial(self, *args, **kwargs):
        initial = super().get_initial()
        username, password = super().get_credential(self)
        session_tr_id = self.request.session[str(self.kwargs['trID'])]
        rtk_initial = get_rtk_initial(username, password, session_tr_id.get('oattr'))
        initial['switch_ip'] = rtk_initial.get('rtk_ip')
        initial['switch_port'] = rtk_initial.get('rtk_port')
        initial['ploam'] = rtk_initial.get('rtk_ploam')
        return initial

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        prev_page, index = backward_page(self.request, self.kwargs['trID'])
        session_tr_id = self.request.session[str(self.kwargs['trID'])]
        tag_service = session_tr_id.get('tag_service')
        ticket_tr_id = session_tr_id.get('ticket_tr_id')
        ticket_tr = TR.objects.get(id=ticket_tr_id)
        ticket_k = ticket_tr.ticket_k
        oattr = session_tr_id.get('oattr')
        # Временно не используется т.к. креденшалы пока не валидны
        # if oattr and "_Кабинет" in oattr:
        #     form = context['form']
        #     rtk_models = get_gottlieb(form['switch_ip'].initial)
        #     context['rtk_models'] = rtk_models
        back_link = reverse(next(iter(tag_service[index])), kwargs={'trID': self.kwargs["trID"]}) + f'?next_page={prev_page}&index={index}'
        context['back_link'] = back_link
        context['oattr'] = oattr
        context['ticket_k'] = ticket_k
        context['ticket_spp_id'] = session_tr_id.get('ticket_spp_id')
        context['dID'] = session_tr_id.get('dID')
        context['trID'] = self.kwargs['trID']
        return context

    def get_success_url(self, **kwargs):
        session_tr_id = self.request.session[str(self.kwargs['trID'])]
        if session_tr_id.get('type_pass'):
            tag_service = append_change_log_shpd(session_tr_id)
        else:
            tag_service = session_tr_id.get('tag_service')
        self.request.session[str(self.kwargs['trID'])] = session_tr_id
        tag_service.append({'data': None})
        tag_service_index = session_tr_id.get('tag_service_index')
        index = tag_service_index[-1] + 1
        tag_service_index.append(index)
        session_tr_id.update({'tag_service': tag_service, 'tag_service_index': tag_service_index})
        self.request.session[str(self.kwargs['trID'])] = session_tr_id
        url = f"{reverse(next(iter(tag_service[index + 1])), kwargs={'trID': self.kwargs['trID']})}?prev_page={next(iter(tag_service[index]))}&index={index}"
        return url


def spec_objects(request, trID):
    """Получение объектов спецификации"""
    user = User.objects.get(username=request.user.username)
    username, password = get_user_credential_cordis(user)
    id_otu = get_or_create_otu(username, password, trID, only_get=True)
    if not id_otu:
        response = {'error': 'Не удалось получить Проект ОТУ', 'result': id_otu}
        return JsonResponse(response)
    specification = Specification(username, password, id_otu)
    cookie = specification.authenticate()
    entities = specification.get_entity_info_list(cookie)
    pattern = '2.2.2.АВ \(#\d+\) '
    nodes = [re.sub(pattern, '', entity.get('Name')) for entity in entities if entity.get('Name').startswith('2.2.2.АВ')]
    response = {'result': nodes}
    return JsonResponse(response)


class PpsFormView(FormView, CredentialMixin):
    template_name = "tickets/pps.html"
    form_class = PpsForm

    def form_valid(self, form):
        session_tr_id = self.request.session[str(self.kwargs['trID'])]
        session_tr_id.update(**form.cleaned_data)
        if form.cleaned_data['type_change_node'] in ('Установка дополнительного КАД', 'Замена КАД'):
            kad_name = form.cleaned_data['kad_name']
            username, password = super().get_credential(self)
            uplink_data = get_uplink_data(kad_name, username, password)
            stu_data = parsing_stu_switch(kad_name, username, password)
            if stu_data and uplink_data:
                switch_data = get_switch_data(kad_name, stu_data, uplink_data)
                session_tr_id.update({'uplink_data': uplink_data, 'switch_data': switch_data})
            if form.cleaned_data['deleted_kad']:
                stu_data = parsing_stu_switch(form.cleaned_data['deleted_kad'], username, password)
                if stu_data:
                    deleted_switch_data = get_switch_data(form.cleaned_data['deleted_kad'], stu_data, ('', kad_name, ''))
                    session_tr_id.update({'deleted_switch_data': deleted_switch_data})
        self.request.session[str(self.kwargs['trID'])] = session_tr_id
        return super().form_valid(form)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        username, password = super().get_credential(self)
        session_tr_id = self.request.session[str(self.kwargs['trID'])]
        ticket_tr_id = session_tr_id.get('ticket_tr_id')
        ticket_tr = TR.objects.get(id=ticket_tr_id)
        context['ticket_tr'] = ticket_tr
        context['ticket_spp_id'] = session_tr_id.get('ticket_spp_id')
        context['dID'] = session_tr_id.get('dID')
        context['trID'] = self.kwargs['trID']
        if session_tr_id.get('list_switches'):
            list_switches = session_tr_id.get('list_switches')
        else:
            list_switches = parsingByNodename(ticket_tr.pps.strip(), username, password)
            list_switches, switches_name = add_portconfig_to_list_swiches(list_switches, username, password)
            if isinstance(list_switches[0], str):
                list_switches = None
            session_tr_id.update({'list_switches': list_switches, 'pps': ticket_tr.pps.strip()})
            self.request.session[str(self.kwargs['trID'])] = session_tr_id
        context['list_switches'] = list_switches
        return context

    def get_success_url(self, **kwargs):
        session_tr_id = self.request.session[str(self.kwargs['trID'])]
        tag_service = [{'pps': None}, {'data': None}]
        tag_service_index = session_tr_id.get('tag_service_index')
        index = tag_service_index[-1] + 1
        tag_service_index.append(index)
        session_tr_id.update({'tag_service': tag_service, 'tag_service_index': tag_service_index})
        self.request.session[str(self.kwargs['trID'])] = session_tr_id
        return reverse('data', kwargs={'trID': self.kwargs['trID']})


class MkoView(UserPassesTestMixin, LoginRequiredMixin, CredentialMixin, View):
    login_url = '/login/'
    def test_func(self):
        return self.request.user.groups.filter(name='Менеджеры').exists()

    def get(self, request):
        username, password = super().get_credential(self)
        user = User.objects.get(username=request.user.username)
        search = in_work_ortr(username, password)
        spp_proc = SPP.objects.filter(process=True)
        list_spp_proc = list(spp_proc.values_list('ticket_k', flat=True))
        if not isinstance(search[0], str):
            unhandled_managers_ticket = [i for i in search if i[0] not in list_spp_proc and i[5]==user.last_name]
            handled_managers_ticket = [i for i in search if i[0] in list_spp_proc and i[5] == user.last_name]
            handled_by_all = []
            if handled_managers_ticket:
                for i in handled_managers_ticket:
                    entity = SPP.objects.get(process=True, ticket_k=i[0])
                    handled_by_all.append(entity)
            handled_by_manager = SPP.objects.filter(process=True, user=user)
            spp_process = set(handled_by_all + list(handled_by_manager))
        else:
            unhandled_managers_ticket = None
            spp_process = SPP.objects.filter(process=True, user=user)
        return render(request, 'tickets/mko.html', {'search': unhandled_managers_ticket, 'spp_process': spp_process})


class CreateSpecificationView(CredentialMixin, View):
    """Создание и заполнение спецификации"""
    def get(self, request, trID):
        username, password = super().get_credential(self)

        ticket_tr = TR.objects.filter(ticket_tr=trID).last()
        id_otu = get_or_create_otu(username, password, trID)
        specification = Specification(username, password, id_otu)
        cookie = specification.authenticate()
        inventory_objects = ('Цифровая сеть потребителя',)
        csp_exist = specification.check_exist_inventory_object(cookie, inventory_objects, resources=True)
        inventory_objects = (', АВ',)
        pps_exist = specification.check_exist_inventory_object(cookie, inventory_objects, resources=True)
        if csp_exist or pps_exist:
            messages.warning(request, f'Новая стоимость в ТР №{trID} не добавлена. Cпецификация заполнялась ранее.')
            return redirect(f'https://arm.itmh.ru/v3/spec/{id_otu}')
        tentura = Tentura(username, password, id_otu)
        status_project = tentura.check_active_project_for_user()
        session_tr_id = request.session[str(trID)]
        pps_resources = session_tr_id.get('pps_resources')
        csp_resources = session_tr_id.get('csp_resources')
        if pps_resources:
            result = tentura.get_id_node_by_name({'Name': ticket_tr.pps})
            if result.get('result'):
                id_node_tentura = int(result.get('result'))

            project_context = tentura.get_project_context()
            gis_object = tentura.get_gis_object_by_id_node(id_node_tentura, project_context)
            tentura.add_node(gis_object)
            specification.set_resources(cookie, id_node_tentura, pps_resources, update=False)

        if csp_resources:
            result = tentura.get_id_address_connection_point(ticket_tr.aid)
            id_address = result.get('result')
            id_csp_tentura = tentura.add_csp(id_address, ticket_tr.connection_point)
            specification.set_resources(cookie, id_csp_tentura, csp_resources, update=False)
        return redirect(f'https://arm.itmh.ru/v3/spec/{id_otu}')


def sppdata(request, trID):
    """Данный метод отображает html-страничку с данными о типе ТР, Точке подключения, СПД"""
    if request.method == 'POST':
        form = SppDataForm(request.POST)
        if form.is_valid():
            tag_service_index = []
            index = 0
            tag_service_index.append(index)
            spd = form.cleaned_data['spd']
            type_tr = form.cleaned_data['type_tr']
            con_point = form.cleaned_data['con_point']
            session_tr_id = request.session[str(trID)]
            session_tr_id.update({'tag_service_index': tag_service_index})

            ticket_tr_id = session_tr_id.get('ticket_tr_id')
            ticket_tr = TR.objects.get(id=ticket_tr_id)
            if [service for service in ticket_tr.services if 'Интернет, DHCP' in service] and spd == 'РТК':
                messages.warning(request, 'Интернет, DHCP через РТК не предоставляется.')
                return redirect('spp_view_save', ticket_tr.ticket_k.dID, ticket_tr.ticket_k.id)
            session_tr_id.update({'spd': spd, 'type_tr': type_tr, 'con_point': con_point})
            if type_tr == 'Не требуется':
                session_tr_id.update({
                    'services_plus_desc': ticket_tr.services, 'oattr': ticket_tr.oattr,
                    'not_required': True, 'dID': ticket_tr.ticket_k.dID
                })
                request.session[trID] = session_tr_id
                return redirect('data', trID)
            request.session[trID] = session_tr_id
            if type_tr == 'Коммерческое' and con_point == 'Нов. точка':
                return redirect('project_tr', ticket_tr.ticket_k.dID, ticket_tr.ticket_cp, trID)
            if type_tr == 'Коммерческое' and con_point == 'Сущ. точка':
                return redirect('get_resources', trID)
            if type_tr == 'ПТО':
                return redirect('pps', trID)

    else:
        user = User.objects.get(username=request.user.username)
        form = SppDataForm()
        if user.groups.filter(name='Менеджеры').exists():
            form.fields['spd'].widget.choices = [('Комтехцентр', 'Комтехцентр'),]
            form.fields['con_point'].widget.choices = [('Нов. точка', 'Новая точка'),]
            form.fields['type_tr'].widget.choices = [('Коммерческое', 'Коммерческое'), ]
        ticket_tr = TR.objects.filter(ticket_tr=trID).last()
        request.session[trID] = {'ticket_spp_id': ticket_tr.ticket_k.id, 'ticket_tr_id': ticket_tr.id,
                                 'technical_solution': trID, 'dID': ticket_tr.ticket_k.dID}
        context = {
            'ticket_spp_id': ticket_tr.ticket_k.id,
            'dID': ticket_tr.ticket_k.dID,
            'ticket_tr': ticket_tr,
            'form': form,
        }
        return render(request, 'tickets/sppdata.html', context)

def add_tr(request, dID, tID, trID):
    user = User.objects.get(username=request.user.username)
    username, password = get_user_credential_cordis(user)
    tr_params = for_tr_view(username, password, dID, tID, trID)
    if tr_params.get('Access denied') == 'Access denied':
        return render(request, 'base.html', {'my_message': 'Нет доступа в СПП'})
    ticket_spp = SPP.objects.filter(dID=dID).last()
    ticket_spp_id = ticket_spp.id
    ticket_tr_id = add_tr_to_db(dID, tID, trID, tr_params, ticket_spp_id)
    return redirect('sppdata', trID)

import time

def ppr_check(request):
    context = {}
    return render(request, 'tickets/ppr_check.html', context)


import time

def perform_ppr_check(request, id_ppr):
    user = User.objects.get(username=request.user.username)
    username, password = get_user_credential_cordis(user)
    cordis = Cordis(username, password)
    ppr_page = cordis.get_ppr_page(id_ppr)
    ppr_page_victims = cordis.get_ppr_victims_page(id_ppr)
    pages = ppr_page + ppr_page_victims

    ppr = PprParse(pages)
    ppr.parse()

    ppr_check = PprCheck(ppr)
    result = ppr_check.check()

    response = {'result': result}
    return JsonResponse(response)



def static_formset(request):
    """Не используется, задел на будущее"""
    template_static = """Присоединение к СПД по медной линии связи.
-----------------------------------------------------------------------------------

%ОИПМ/ОИПД% проведение работ.
- Организовать медную линию связи от %указать узел связи% до клиентcкого оборудования.
- Подключить организованную линию для клиента в коммутатор %указать название коммутатора%, порт задействовать %указать порт коммутатора%."""

    TemplatesStaticFormSet = formset_factory(TemplatesStaticForm, extra=4)
    if request.method == 'POST':
        formset = TemplatesStaticFormSet(request.POST)
        if formset.is_valid():

            data = formset.cleaned_data
            print('!!!!!!!!dataresources_formset')
            print(data)
            static_vav = ['ОИПМ/ОИПД', 'указать узел связи', 'указать название коммутатора', 'указать порт коммутатора']
            selected_ono = []
            unselected_ono = []
            static_vars = {}
            selected = zip(static_vav, data)
            for static_vav, data in selected:
                static_vars[static_vav] = next(iter(data.values()))
            print('!!!!static_vars')
            print(static_vars)
            return redirect('no_data')
    else:
        template_static = """Присоединение к СПД по медной линии связи.
        -----------------------------------------------------------------------------------

        %ОИПМ/ОИПД% проведение работ.
        - Организовать медную линию связи от %указать узел связи% до клиентcкого оборудования.
        - Подключить организованную линию для клиента в коммутатор %указать название коммутатора%, порт задействовать %указать порт коммутатора%."""
        static_vav = ['ОИПМ/ОИПД', 'указать узел связи', 'указать название коммутатора', 'указать порт коммутатора']
        formset = TemplatesStaticFormSet()
        context = {
            'ono_for_formset': static_vav,
            'formset': formset
        }

        return render(request, 'tickets/template_static_formset.html', context)

