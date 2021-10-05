from django.shortcuts import render, redirect, get_object_or_404
from django.http import HttpResponse
from .models import TR, SPP, OrtrTR
from .forms import TrForm, PortForm, LinkForm, HotspotForm, SPPForm, ServiceForm, PhoneForm, ItvForm, ShpdForm,\
    VolsForm, CopperForm, WirelessForm, CswForm, CksForm, PortVKForm, PortVMForm, VideoForm, LvsForm, LocalForm, SksForm,\
    UserRegistrationForm, UserLoginForm, OrtrForm, AuthForServiceForm, ContractForm, ChainForm, ListResourcesForm, PassForm,\
    PassServForm, AddServInstCswForm, ChangeServForm, ChangeParamsForm, ListJobsForm

from django.contrib import messages
from django.contrib.auth import login, logout
from django.contrib.auth.models import User
from django.contrib.auth.decorators import login_required
from django.db.models import Q
from django.http import Http404


def register(request):
    """Данный метод отвечает за регистрацию пользователей в АРМ"""
    if request.method == 'POST':
        form = UserRegistrationForm(request.POST)
        if form.is_valid():
            user = form.save()
            login(request, user)
            messages.success(request, 'Вы успешно зарегистрировались')
            return redirect('ortr')
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
                return redirect('private_page')

            else:
                return redirect(request.GET['next'])

    else:
        form = UserLoginForm()
    return render(request, 'tickets/login.html', {'form': form})

def user_logout(request):
    """Данный метод отвечает за выход авторизованного пользователя"""
    logout(request)
    return redirect('login')


def index(request):
    """Данный метод нужно будет удалить"""
    list_session_keys = []
    for key in request.session.keys():
        if key.startswith('_'):
            pass
        else:
            list_session_keys.append(key)
    for key in list_session_keys:
        del request.session[key]
    print(request.session.keys())

    tr = SPP.objects.order_by('-created')
    return render(request, 'tickets/index.html', {'tr': tr})

@login_required(login_url='login/')
def private_page(request):
    """Данный метод в Личном пространстве пользователя отображает все задачи этого пользователя"""
    request = flush_session_key(request)
    spp_success = SPP.objects.filter(user=request.user).order_by('-created')
    return render(request, 'tickets/private_page.html', {'spp_success': spp_success})



def get_tr(request, ticket_tr, ticket_id):
    """Данный метод можно будет удалить"""
    services_one_tr = []
    one_tr = TR.objects.get(ticket_tr=ticket_tr, id=ticket_id)
    for item in one_tr.servicestr_set.all():
        services_one_tr.append(item.service)
    data_one_tr = one_tr.datatr_set.get()
    ortr_one_tr = one_tr.ortrtr_set.first() #first вместо get, т.к. если записи нет, то будет исключение DoesNotExist
    context = {
        'one_tr': one_tr,
        'services_one_tr': services_one_tr,
        'data_one_tr': data_one_tr,
        'ortr_one_tr': ortr_one_tr
    }

    return render(request, 'tickets/tr.html', context=context)


import re
from requests.auth import HTTPBasicAuth
import requests
from bs4 import BeautifulSoup
from collections import OrderedDict
import itertools
import pymorphy2
import datetime


def stash(sw, model, login, password):
    """Данный метод принимает в качестве параметров Название КАД и модель КАД. Обращается к stash.itmh.ru и парсит
    конфиг коммутатора по названию. На основе модели КАД подставляет соответствующие regex для формирования данных по портам КАД"""
    url = 'https://stash.itmh.ru/projects/NMS/repos/pantera_extrim/raw/backups/' + sw + '-config?at=refs%2Fheads%2Fmaster'
    req = requests.get(url, verify=False, auth=HTTPBasicAuth(login, password))
    if req.status_code == 404:
        config_ports_device = {}
    else:
        switch = req.content.decode('utf-8')

        if 'SNR' in model or 'Cisco' in model or 'Orion' in model:
            port_list = []
            regex_description = '\wnterface (\S+\/\S+)(.+?)!'
            match_description = re.finditer(regex_description, switch, flags=re.DOTALL)
            # чтобы найти description блок интерфейса разделяется по \r\n, если не получается разделить, разделяется по \n
            config_ports_device = {}
            for i in match_description:
                if 'description' in i.group(2):
                    desc = i.group(2).split('\r\n')
                    if len(desc) == 1:
                        desc = i.group(2).split('\n')
                        if 'description' in desc[1]:
                            desc = i.group(2).split('\n')[1].split()[1]
                        else:
                            desc = i.group(2).split('\n')[2].split()[1]
                    else:
                        if 'description' in desc[1]:
                            desc = i.group(2).split('\r\n')[1].split()[1]
                        else:
                            desc = i.group(2).split('\r\n')[2].split()[1]
                else:
                    desc = '-'

                if 'switchport access vlan 4094' in i.group(2):
                    vlan = 'Заглушка 4094'
                else:
                    vlan = '-'

                config_ports_device[i.group(1)] = [desc, vlan]


        elif 'D-Link' in model and model != 'D-Link DIR-100':
            port_list = None
            config_ports_device = {}
            regex_description = 'config ports (\d+) (?:.+?) description (\".*?\")\n'
            match_description = re.finditer(regex_description, switch, flags=re.DOTALL)
            for i in match_description:
                config_ports_device['Port {}'.format(i.group(1))] = [i.group(2), '-']
            if '1100' in model:
                regex_free = 'config vlan vlanid 4094 add untagged (\S+)'
            else:
                regex_free = 'config vlan stub add untagged (\S+)'
            match_free = re.search(regex_free, switch)
            port_free = []
            for i in match_free.group(1).split(','):
                if '-' in i:
                    start, stop = [int(j) for j in i.split('-')]
                    port_free += list(range(start, stop+1))
                else:
                    port_free.append(int(i))

            for i in port_free:
                if config_ports_device.get('Port {}'.format(i)):
                    config_ports_device['Port {}'.format(i)][1] = 'Заглушка 4094'
                else:
                    config_ports_device['Port {}'.format(i)] = ['-', 'Заглушка 4094']

    return config_ports_device

def match_cks(tochka, login, password):
    """Данный метод получает в параметр tochka(где содержатся dID и tID), по этим данным парсится страница ТР
     Точки подключения и получает из нее список всех точек подключения. С помощью библиотеки itertools формирует
      всевозможные варианты типа Точка А - Точка В"""
    list_cks = []
    list_strok = []
    url = 'https://sss.corp.itmh.ru/dem_tr/dem_point_panel.php?dID={}&amp;tID={}'.format(tochka[0], tochka[1])
    req = requests.get(url, verify=False, auth=HTTPBasicAuth(login, password))
    if req.status_code == 200:
        cks_parsed = req.content.decode('utf-8')
        regex_cks = '\'>&nbsp;(.+?)&nbsp;<'
        match_cks = re.finditer(regex_cks, cks_parsed)
        # print(match_cks)
        for i in match_cks:
            list_cks.append(i.group(1))
        #for i in itertools.combinations(list_cks,
        #                                2):  # берет по очереди по 2 элемента списка не включая дубли и перевертыши
        #    list_strok.append(i[0] + ' - ' + i[1])

        return list_cks
    else:
        list_cks.append('Access denied')
        return list_cks



def trtr(request):
    """Данный метод можно удалять"""
    #context = {'services_plus_desc': services_plus_desc, 'pps': pps, 'turnoff': turnoff, 'oattr': oattr, 'success': success, 'linkform': linkform}
    return render(request, 'tickets/trtr.html')

def login_for_service(request):
    """Данный метод перенаправляет на страницу Авторизация в ИС Холдинга. Метод используется для получения данных от пользователя
     для авторизации в ИС Холдинга. После получения данных, проверяет, что пароль не содержит русских символов и добавляет
      логин с паролем в redis(задает время хранения в параметре timeout) и перенаправляет на страницу, с которой пришел запрос"""
    if request.method == 'POST':
        authform = AuthForServiceForm(request.POST)
        if authform.is_valid():
            username = authform.cleaned_data['username']
            password = authform.cleaned_data['password']
            if re.search(r'[а-яА-Я]', password):
                messages.warning(request, 'Русская клавиатура')
                return redirect('login_for_service')
            else:

                user = User.objects.get(username=request.user.username)
                credent = dict()
                credent.update({'username': username})
                credent.update({'password': password})
                cache.set(user, credent, timeout=3600)
                #prim = request.META.get('HTTP_REFERER')
                #print(prim)
                #cache.set_many({'username': username, 'password': password}, timeout=60)
                print(request.GET)
                if 'next' in request.GET:
                    return redirect(request.GET['next'])
                return redirect('ortr')
    else:
        authform = AuthForServiceForm()

    return render(request, 'tickets/login_is.html', {'form': authform})

from django.core.cache import cache

from django.contrib.auth.decorators import user_passes_test




from django.http import HttpResponseRedirect

def cache_check(func):
    """Данный декоратор осуществляет проверку, что пользователь авторизован в АРМ, и в redis есть его логин/пароль,
     если данных нет, то перенаправляет на страницу Авторизация в ИС Холдинга"""
    def wrapper(request, *args, **kwargs):
        print(request.path)
        if not request.user.is_authenticated:
            return redirect('login/?next=%s' % (request.path))#(request.GET['next']))
        user = User.objects.get(username=request.user.username)
        credent = cache.get(user)
        print(request.GET)
        #?next={}'.format(request.GET['next'])
        if credent == None:
            response = redirect('login_for_service')#, request.GET['next'])
            print(response['Location'])
            #response['Location'] += '?next={}'.format(request.GET['next'])
            response['Location'] += '?next={}'.format(request.path)
            return response
            #return redirect('login_for_service?next={}'.format(request.GET['next']))
        return func(request, *args, **kwargs)
    return wrapper


@cache_check
def commercial(request):
    """Данный метод перенаправляет на страницу Коммерческие заявки, которые находятся в работе ОРТР.
    1. Получает данные от redis о логин/пароле
    2. Получает данные о коммерческих заявках в пуле ОРТР с помощью метода in_work_ortr
    3. Получает данные о коммерческих заявках которые уже находятся в БД(в работе/в ожидании)
    4. Удаляет из списка в пуле заявки, которые есть в работе/в ожидании
    5. Формирует итоговый список задач в пуле и в работе"""
    user = User.objects.get(username=request.user.username)
    credent = cache.get(user)
    username = credent['username']
    password = credent['password']

    search = in_work_ortr(username, password)
    search[:] = [x for x in search if 'ПТО' not in x[0]]
    if search[0] == 'Access denied':
        messages.warning(request, 'Нет доступа в ИС Холдинга')
        response = redirect('login_for_service')
        response['Location'] += '?next={}'.format(request.path)
        return response

    else:
        list_search = []
        for i in search:
            print('!!!')
            print(i[0])
            if 'ПТО' not in i[0]:
                list_search.append(i[0])
        print(list_search)
        spp_process = SPP.objects.filter(Q(process=True) | Q(wait=True)).filter(type_ticket='Коммерческая')
        list_spp_process = []
        for i in spp_process:
            list_spp_process.append(i.ticket_k)
        print(list_spp_process)
        list_search_rem = []
        for i in list_spp_process:
            for index_j in range(len(list_search)):
                if i in list_search[index_j]:
                    list_search_rem.append(index_j)
        print(list_search_rem)

        search[:] = [x for i, x in enumerate(search) if i not in list_search_rem]
        spp_process = SPP.objects.filter(process=True).filter(type_ticket='Коммерческая')
        return render(request, 'tickets/ortr.html', {'search': search, 'com_search': True, 'spp_process': spp_process})

@cache_check
def pto(request):
    """Данный метод перенаправляет на страницу ПТО заявки, которые находятся в работе ОРТР.
        1. Получает данные от redis о логин/пароле
        2. Получает данные о ПТО заявках в пуле ОРТР с помощью метода in_work_ortr
        3. Получает данные о ПТО заявках которые уже находятся в БД(в работе/в ожидании)
        4. Удаляет из списка в пуле заявки, которые есть в работе/в ожидании
        5. Формирует итоговый список задач в пуле и в работе"""
    user = User.objects.get(username=request.user.username)
    credent = cache.get(user)
    username = credent['username']
    password = credent['password']

    search = in_work_ortr(username, password)
    search[:] = [x for x in search if 'ПТО' in x[0]]
    if search[0] == 'Access denied':
        messages.warning(request, 'Нет доступа в ИС Холдинга')
        response = redirect('login_for_service')
        response['Location'] += '?next={}'.format(request.path)
        return response

    else:
        list_search = []
        print(search)
        for i in search:
            if 'ПТО' in i[0]:
                list_search.append(i[0])
        # list_search = [i for i in set_search]
        print(list_search)
        spp_process = SPP.objects.filter(process=True).filter(type_ticket='ПТО')
        list_spp_process = []
        for i in spp_process:
            list_spp_process.append(i.ticket_k)
        print(list_spp_process)
        list_search_rem = []
        for i in list_spp_process:
            for index_j in range(len(list_search)):
                if i in list_search[index_j]:
                    list_search_rem.append(index_j)
        print(list_search_rem)


        search[:] = [x for i, x in enumerate(search) if i not in list_search_rem]
        return render(request, 'tickets/ortr.html', {'search': search, 'pto_search': True, 'spp_process': spp_process})

def wait(request):
    """Данный метод перенаправляет на страницу заявки в ожидании.
            1. Получает данные о всех заявках которые уже находятся в БД(в ожидании)
            2. Формирует итоговый список задач в ожидании"""
    spp_process = SPP.objects.filter(wait=True)
    return render(request, 'tickets/ortr.html', {'wait_search': True, 'spp_process': spp_process})


@cache_check
def all_com_pto_wait(request):
    """Данный метод перенаправляет на страницу Все заявки, которые находятся в пуле ОРТР/в работе/в ожидании.
        1. Получает данные от redis о логин/пароле
        2. Получает данные о всех заявках в пуле ОРТР с помощью метода in_work_ortr
        3. Получает данные о всех заявках которые уже находятся в БД(в работе/в ожидании)
        4. Удаляет из списка в пуле заявки, которые есть в работе/в ожидании
        5. Формирует итоговый список всех заявок в пуле/в работе/в ожидании"""
    user = User.objects.get(username=request.user.username)
    credent = cache.get(user)
    username = credent['username']
    password = credent['password']

    search = in_work_ortr(username, password)
    if search[0] == 'Access denied':
        messages.warning(request, 'Нет доступа в ИС Холдинга')
        response = redirect('login_for_service')
        response['Location'] += '?next={}'.format(request.path)
        return response

    else:
        list_search = []
        for i in search:
            list_search.append(i[0])
        print(list_search)
        spp_proc_wait_all = SPP.objects.filter(Q(process=True) | Q(wait=True))
        list_spp_proc_wait_all = []
        for i in spp_proc_wait_all:
            list_spp_proc_wait_all.append(i.ticket_k)
        print(list_spp_proc_wait_all)
        list_search_rem = []
        for i in list_spp_proc_wait_all:
            for index_j in range(len(list_search)):
                if i in list_search[index_j]:
                    list_search_rem.append(index_j)
        print(list_search_rem)

        search[:] = [x for i, x in enumerate(search) if i not in list_search_rem]

        spp_process = SPP.objects.filter(process=True)
        spp_wait = SPP.objects.filter(wait=True)

        return render(request, 'tickets/ortr.html', {'all_search': True, 'search': search, 'spp_process': spp_process, 'spp_wait': spp_wait})


@cache_check
def get_link_tr(request):
    """Данный метод открывает страницу Проектирование ТР
    1. Получает от пользователя ссылку на ТР
    2. Проверяет правильность ссылки
    3. Получает из ссылки параметры ТР dID, tID, trID
    4. Перенаправляет на метод project_tr"""
    if request.method == 'POST':
        linkform = LinkForm(request.POST)
        if linkform.is_valid():
            print(linkform.cleaned_data)
            spplink = linkform.cleaned_data['spplink']
            manlink = spplink
            regex_link = 'dem_tr\/dem_begin\.php\?dID=(\d+)&tID=(\d+)&trID=(\d+)'
            match_link = re.search(regex_link, spplink)
            if match_link:
                dID = match_link.group(1)
                tID = match_link.group(2)
                trID = match_link.group(3)

                request.session['manlink'] = manlink
                print(request.session.items())
                return redirect('project_tr', dID, tID, trID)
            else:
                messages.warning(request, 'Неверная ссылка')
                return redirect('get_link_tr')
    else:
        list_session_keys = []
        for key in request.session.keys():
            if key.startswith('_'):
                pass
            else:
                list_session_keys.append(key)
        for key in list_session_keys:
            del request.session[key]

        linkform = LinkForm()

    return render(request, 'tickets/inputtr.html', {'linkform': linkform})


def project_tr(request, dID, tID, trID):
    spplink = 'https://sss.corp.itmh.ru/dem_tr/dem_begin.php?dID={}&tID={}&trID={}'.format(dID, tID, trID)
    user = User.objects.get(username=request.user.username)
    credent = cache.get(user)
    username = credent['username']
    password = credent['password']
    data_sss = parse_tr(username, password, spplink)
    if data_sss[0] == 'Access denied':
        messages.warning(request, 'Нет доступа в ИС Холдинга')
        response = redirect('login_for_service')
        response['Location'] += '?next={}'.format(request.path)
        return response
    elif data_sss[2] == 'Не выбран':
        return redirect('tr_view', dID, tID, trID)
    else:
        services_plus_desc = data_sss[0]
        counter_line_services = data_sss[1]
        pps = data_sss[2]
        turnoff = data_sss[3]
        sreda = data_sss[4]
        tochka = data_sss[5]
        hotspot_points = data_sss[6]
        oattr = data_sss[7]
        address = data_sss[8]
        client = data_sss[9]
        manager = data_sss[10]
        technolog = data_sss[11]
        task_otpm = data_sss[12]
        request.session['services_plus_desc'] = services_plus_desc
        request.session['counter_line_services'] = counter_line_services
        request.session['pps'] = pps
        request.session['turnoff'] = turnoff
        request.session['sreda'] = sreda
        request.session['tochka'] = tochka
        request.session['address'] = address
        request.session['oattr'] = oattr
        request.session['spplink'] = spplink
        request.session['client'] = client
        request.session['manager'] = manager
        request.session['technolog'] = technolog
        request.session['task_otpm'] = task_otpm
        request.session['tID'] = tID
        request.session['dID'] = dID
        request.session['trID'] = trID

        tag_service, hotspot_users, premium_plus = _tag_service_for_new_serv(services_plus_desc)
        tag_service.insert(0, {'sppdata': None})

        request.session['hotspot_points'] = hotspot_points
        request.session['hotspot_users'] = hotspot_users
        request.session['premium_plus'] = premium_plus


        if counter_line_services == 0:
            tag_service.append({'data': None})
        else:
            if sreda == '1':
                tag_service.append({'copper': None})
            elif sreda == '2' or sreda == '4':
                tag_service.append({'vols': None})
            elif sreda == '3':
                tag_service.append({'wireless': None})

        type_tr = 'new_cl'
        request.session['type_tr'] = type_tr
        request.session['tag_service'] = tag_service
        print('!!!!!tagsevice')
        print(tag_service)
        return redirect(next(iter(tag_service[0])))





#def inputtr(request):
#    if request.method == 'POST':
#        linkform = LinkForm(request.POST)
#        if linkform.is_valid():
#            print(linkform.cleaned_data)
#            spplink = linkform.cleaned_data['spplink']
#            manlink = spplink
#            request.session['manlink'] = manlink
#            print(request.session.items())
#            services_plus_desc, counter_line_services, pps, turnoff, sreda, tochka, hotspot_points, oattr, address, client, manager, technolog, task_otpm = parse_tr(username, password, spplink)
#            request.session['services_plus_desc'] = services_plus_desc
#            request.session['counter_line_services'] = counter_line_services
#            request.session['pps'] = pps
#            request.session['turnoff'] = turnoff
#            request.session['sreda'] = sreda
#            request.session['tochka'] = tochka
#            request.session['address'] = address
#            request.session['oattr'] = oattr
#            request.session['spplink'] = spplink
#            request.session['client'] = client
#            request.session['manager'] = manager
#            request.session['technolog'] = technolog
#            request.session['task_otpm'] = task_otpm


#            tag_service = []
#            tag_service.append('sppdata')
#            for index_service in range(len(services_plus_desc)):
#                if 'Телефон' in services_plus_desc[index_service]:
#                    tag_service.append('phone')
#                elif 'iTV' in services_plus_desc[index_service]:
#                    tag_service.append('itv')
#                elif 'ЦКС' in services_plus_desc[index_service]:
#                    tag_service.append('cks')
#                elif 'Порт ВЛС' in services_plus_desc[index_service]:
#                    tag_service.append('portvk')
#                elif 'Порт ВМ' in services_plus_desc[index_service]:
#                    tag_service.append('portvm')
#                elif 'ЛВС' in services_plus_desc[index_service]:
#                    tag_service.append('local')
#                elif 'Видеонаблюдение' in services_plus_desc[index_service]:
#                    tag_service.append('video')
#                elif 'HotSpot' in services_plus_desc[index_service]:
#                    if ('премиум +' or 'премиум+') in services_plus_desc[index_service].lower():
#                        premium_plus = True
#                    else:
#                        premium_plus = False
#                    hotspot_users = None
#                    regex_hotspot_users = ['(\d+)посетит', '(\d+) посетит', '(\d+) польз', '(\d+)польз', '(\d+)чел',
#                                           '(\d+) чел']
#                    for regex in regex_hotspot_users:
#                        match_hotspot_users = re.search(regex, services_plus_desc[index_service])
#                        if match_hotspot_users:
#                            hotspot_users = match_hotspot_users.group(1)
#                            break
#
#                    tag_service.append('hotspot')
#                    request.session['hotspot_points'] = hotspot_points
#                    request.session['hotspot_users'] = hotspot_users
#                    request.session['premium_plus'] = premium_plus
#            if counter_line_services == 0:
#                tag_service.append('data')
#            else:
#                if sreda == '1':
#                    tag_service.append('copper')
#                elif sreda == '2' or sreda == '4':
#                    tag_service.append('vols')
#
#            request.session['tag_service'] = tag_service
#            return redirect(next(iter(tag_service[0])))
#            for i in services_plus_desc:
#
#                if 'Телефон' in i:
#                    return redirect('phone')
#                elif 'HotSpot' in i:
#                    if points_hotspot == None:
#                        return redirect('hotspot')
#                    else:
#                        request.session['points_hotspot'] = points_hotspot
#            return redirect('data')

            #context = {'services_plus_desc': services_plus_desc, 'pps': pps, 'turnoff': turnoff, 'oattr': oattr, 'success': success, 'linkform': linkform}
            #return render(request, 'tickets/inputtr.html', context)
#    else:
#        linkform = LinkForm()
        #user = User.objects.get(username=request.user.username)
        #print('user')
        #print(user)
        #user = request.user
        #print(user)
        #passw = user.password
        #lastna = user.last_name
        #print(passw)
        #print(lastna)

#    return render(request, 'tickets/inputtr.html', {'linkform': linkform})

def sppdata(request):
    services_plus_desc = request.session['services_plus_desc']
    client = request.session['client']
    manager = request.session['manager']
    technolog = request.session['technolog']
    task_otpm = request.session['task_otpm']
    address = request.session['address']
    turnoff = request.session['turnoff']
    tag_service = request.session['tag_service']
    tag_service.pop(0)
    next_link = next(iter(tag_service[0]))
    request.session['tag_service'] = tag_service
    context = {
        'services_plus_desc': services_plus_desc,
        'client': client,
        'manager': manager,
        'technolog': technolog,
        'task_otpm': task_otpm,
        'address': address,
        'next_link': next_link,
        'turnoff': turnoff
    }
    return render(request, 'tickets/sppdata.html', context)

@cache_check
def copper(request):
    if request.method == 'POST':
        copperform = CopperForm(request.POST)

        if copperform.is_valid():
            print(copperform.cleaned_data)
            logic_csw = copperform.cleaned_data['logic_csw']
            port = copperform.cleaned_data['port']
            kad = copperform.cleaned_data['kad']
            request.session['logic_csw'] = logic_csw
            request.session['port'] = port
            request.session['kad'] = kad
            type_tr = request.session['type_tr']
            if type_tr == 'new_cl':
                if logic_csw == True:
                    return redirect('csw')
                else:
                    return redirect('data')
            elif type_tr == 'exist_cl':
                tag_service = request.session['tag_service']
                tag_service.pop(0)
                request.session['tag_service'] = tag_service
                return redirect(next(iter(tag_service[0])))

    else:
        user = User.objects.get(username=request.user.username)
        credent = cache.get(user)
        username = credent['username']
        password = credent['password']
        pps = request.session['pps']
        print('!!!!!pps in copper')
        print(pps)
        services_plus_desc = request.session['services_plus_desc']
        #turnoff = request.session['turnoff']
        sreda = request.session['sreda']
        #tochka = request.session['tochka']
        oattr = request.session['oattr']
        #counter_line_services = request.session['counter_line_services']
        #spp_link = request.session['spplink']
        try:
            type_pass = request.session['type_pass']
        except KeyError:
            type_pass = None


        list_switches = parsingByNodename(pps, username, password)
        if list_switches[0] == 'Access denied':
            messages.warning(request, 'Нет доступа в ИС Холдинга')
            response = redirect('login_for_service')
            response['Location'] += '?next={}'.format(request.path)
            return response
        elif 'No records to display' in list_switches[0]:
            messages.warning(request, 'Нет коммутаторов на узле {}'.format(list_switches[0][22:]))
            return redirect('ortr')

        switch_name = []
        for i in range(len(list_switches)):
            if list_switches[i][-1] == '-':
                pass
            else:
                switch_ports_var = stash(list_switches[i][0], list_switches[i][1], username, password)
                if switch_ports_var == None:
                    pass
                else:
                    for port in switch_ports_var.keys():
                        if list_switches[i][10].get(port) == None:
                            switch_ports_var[port].insert(0, '-')
                            switch_ports_var[port].insert(0, '-')
                            list_switches[i][10].update({port: switch_ports_var[port]})
                        else:
                            for from_dev in switch_ports_var[port]:
                                list_switches[i][10][port].append(from_dev)
                    list_switches[i][10] = OrderedDict(sorted(list_switches[i][10].items(), key=lambda t: t[0][-2:]))
            switch_name.append(list_switches[i][0])
        print(('!!!!switch_name'))
        print(switch_name)
        if len(switch_name) == 1:
            switches_name = switch_name[0]
        else:
            switches_name = ' или '.join(switch_name)

        request.session['list_switches'] = list_switches

        if type_pass:
            if 'Организация доп.услуги с установкой КК' in type_pass:
                copperform = CopperForm(initial={'kad': switches_name, 'port': 'свободный', 'logic_csw': True})
            else:
                copperform = CopperForm(initial={'kad': switches_name, 'port': 'свободный'})
        else:
            copperform = CopperForm(initial={'kad': switches_name, 'port': 'свободный'})

        context = {
            'pps': pps,
            'oattr': oattr,
            'list_switches': list_switches,
            'sreda': sreda,
            'copperform': copperform

        }
        return render(request, 'tickets/env.html', context)

@cache_check
def vols(request):
    if request.method == 'POST':
        volsform = VolsForm(request.POST)

        if volsform.is_valid():
            print(volsform.cleaned_data)
            device_client = volsform.cleaned_data['device_client']
            device_pps = volsform.cleaned_data['device_pps']
            logic_csw = volsform.cleaned_data['logic_csw']
            port = volsform.cleaned_data['port']
            kad = volsform.cleaned_data['kad']
            speed_port = volsform.cleaned_data['speed_port']
            request.session['device_pps'] = device_pps
            request.session['logic_csw'] = logic_csw
            request.session['port'] = port
            request.session['speed_port'] = speed_port
            request.session['kad'] = kad
            try:
                ppr = volsform.cleaned_data['ppr']
            except KeyError:
                ppr = None
            request.session['ppr'] = ppr

            type_tr = request.session['type_tr']
            if type_tr == 'new_cl':
                if logic_csw == True:
                    device_client = device_client.replace('клиентское оборудование', 'клиентский коммутатор')
                    request.session['device_client'] = device_client
                    return redirect('csw')
                else:
                    request.session['device_client'] = device_client
                    return redirect('data')
            elif type_tr == 'exist_cl':
                tag_service = request.session['tag_service']
                tag_service.pop(0)
                request.session['tag_service'] = tag_service
                return redirect(next(iter(tag_service[0])))



    else:
        user = User.objects.get(username=request.user.username)
        credent = cache.get(user)
        username = credent['username']
        password = credent['password']
        pps = request.session['pps']
        services_plus_desc = request.session['services_plus_desc']
        turnoff = request.session['turnoff']
        sreda = request.session['sreda']
        #tochka = request.session['tochka']
        oattr = request.session['oattr']
        #counter_line_services = request.session['counter_line_services']
        spplink = request.session['spplink']
        print('!!!SPPLINK')
        print(spplink)
        regex_link = 'dem_tr\/dem_begin\.php\?dID=(\d+)&tID=(\d+)&trID=(\d+)'
        match_link = re.search(regex_link, spplink)
        dID = match_link.group(1)
        tID = match_link.group(2)
        trID = match_link.group(3)
        print(dID)
        print(tID)
        print(trID)
        try:
            type_pass = request.session['type_pass']
        except KeyError:
            type_pass = None

        list_switches = parsingByNodename(pps, username, password)
        if list_switches[0] == 'Access denied':
            messages.warning(request, 'Нет доступа в ИС Холдинга')
            response = redirect('login_for_service')
            response['Location'] += '?next={}'.format(request.path)
            return response
        elif 'No records to display' in list_switches[0]:
            messages.warning(request, 'Нет коммутаторов на узле {}'.format(list_switches[0][22:]))
            return redirect('ortr')

        switch_name = []
        for i in range(len(list_switches)):
            if list_switches[i][-1] == '-':
                pass
            else:
                switch_ports_var = stash(list_switches[i][0], list_switches[i][1], username, password)
                if switch_ports_var == None:
                    pass
                else:
                    for port in switch_ports_var.keys():
                        if list_switches[i][10].get(port) == None:
                            switch_ports_var[port].insert(0, '-')
                            switch_ports_var[port].insert(0, '-')
                            list_switches[i][10].update({port: switch_ports_var[port]})
                        else:
                            for from_dev in switch_ports_var[port]:
                                list_switches[i][10][port].append(from_dev)
                    list_switches[i][10] = OrderedDict(sorted(list_switches[i][10].items(), key=lambda t: t[0][-2:]))
            switch_name.append(list_switches[i][0])
        if len(switch_name) == 1:
            switches_name = switch_name[0]
        else:
            switches_name = ' или '.join(switch_name)

        request.session['list_switches'] = list_switches


        if sreda == '2':
            if type_pass:
                if 'Организация доп.услуги с установкой КК' in type_pass:
                    volsform = VolsForm(
                        initial={'device_pps': 'конвертер 1310 нм, выставить на конвертере режим работы Auto',
                                 'device_client': 'оптический передатчик SFP WDM, до 20 км, 1550 нм в клиентское оборудование',
                                 'speed_port': 'Auto',
                                 'kad': switches_name,
                                 'port': 'свободный',
                                 'logic_csw': True})
                else:
                    volsform = VolsForm(
                        initial={'device_pps': 'конвертер 1310 нм, выставить на конвертере режим работы Auto',
                                 'device_client': 'конвертер 1550 нм, выставить на конвертере режим работы Auto',
                                 'kad': switches_name,
                                 'speed_port': 'Auto',
                                 'port': 'свободный'})
            else:
                volsform = VolsForm(
                    initial={'device_pps': 'конвертер 1310 нм, выставить на конвертере режим работы Auto',
                             'device_client': 'конвертер 1550 нм, выставить на конвертере режим работы Auto',
                             'kad': switches_name,
                             'speed_port': 'Auto',
                             'port': 'свободный'})
        elif sreda == '4':
            if type_pass:
                if 'Организация доп.услуги с установкой КК' in type_pass:
                    volsform = VolsForm(initial={'device_pps': 'оптический передатчик SFP WDM, до 3 км, 1310 нм',
                                     'device_client': 'оптический передатчик SFP WDM, до 3 км, 1550 нм в клиентское оборудование',
                                                 'kad': switches_name,
                                     'speed_port': '100FD',
                                     'logic_csw': True})
                else:
                    volsform = VolsForm(
                        initial={'device_pps': 'оптический передатчик SFP WDM, до 3 км, 1310 нм',
                                 'device_client': 'конвертер 1550 нм, выставить на конвертере режим работы Auto',
                                 'kad': switches_name,
                                 'speed_port': '100FD',
                                 'port': 'свободный'})
            else:
                volsform = VolsForm(
                        initial={'device_pps': 'оптический передатчик SFP WDM, до 3 км, 1310 нм',
                                 'device_client': 'конвертер 1550 нм, выставить на конвертере режим работы Auto',
                                 'kad': switches_name,
                                 'speed_port': '100FD'})
        else:
            if type_pass:
                if 'Организация доп.услуги с установкой КК' in type_pass:
                    volsform = VolsForm(initial={'logic_csw': True})
            else:
                volsform = VolsForm()
        context = {
            'pps': pps,
            'oattr': oattr,
            'list_switches': list_switches,
            'sreda': sreda,
            'turnoff': turnoff,
            'dID': dID,
            'tID': tID,
            'trID': trID,
            'volsform': volsform
        }

        return render(request, 'tickets/env.html', context)

@cache_check
def wireless(request):
    if request.method == 'POST':
        wirelessform = WirelessForm(request.POST)

        if wirelessform.is_valid():
            print(wirelessform.cleaned_data)
            access_point = wirelessform.cleaned_data['access_point']
            port = wirelessform.cleaned_data['port']
            kad = wirelessform.cleaned_data['kad']
            logic_csw = wirelessform.cleaned_data['logic_csw']
            try:
                ppr = wirelessform.cleaned_data['ppr']
            except KeyError:
                ppr = None
            request.session['ppr'] = ppr
            request.session['access_point'] = access_point
            request.session['port'] = port
            request.session['kad'] = kad
            request.session['logic_csw'] = logic_csw



            type_tr = request.session['type_tr']
            if type_tr == 'new_cl':
                if logic_csw == True:
                    return redirect('csw')
                else:
                    return redirect('data')
            elif type_tr == 'exist_cl':
                tag_service = request.session['tag_service']
                tag_service.pop(0)
                request.session['tag_service'] = tag_service
                return redirect(next(iter(tag_service[0])))



    else:
        user = User.objects.get(username=request.user.username)
        credent = cache.get(user)
        username = credent['username']
        password = credent['password']
        pps = request.session['pps']
        #services_plus_desc = request.session['services_plus_desc']
        turnoff = request.session['turnoff']
        sreda = request.session['sreda']
        #tochka = request.session['tochka']
        oattr = request.session['oattr']
        #counter_line_services = request.session['counter_line_services']
        #spp_link = request.session['spplink']

        list_switches = parsingByNodename(pps, username, password)
        if list_switches[0] == 'Access denied':
            messages.warning(request, 'Нет доступа в ИС Холдинга')
            response = redirect('login_for_service')
            response['Location'] += '?next={}'.format(request.path)
            return response
        elif 'No records to display' in list_switches[0]:
            messages.warning(request, 'Нет коммутаторов на узле {}'.format(list_switches[0][22:]))
            return redirect('ortr')

        switch_name = []
        for i in range(len(list_switches)):
            if list_switches[i][-1] == '-':
                pass
            else:
                switch_ports_var = stash(list_switches[i][0], list_switches[i][1], username, password)
                if switch_ports_var == None:
                    pass
                else:
                    for port in switch_ports_var.keys():
                        if list_switches[i][10].get(port) == None:
                            switch_ports_var[port].insert(0, '-')
                            switch_ports_var[port].insert(0, '-')
                            list_switches[i][10].update({port: switch_ports_var[port]})
                        else:
                            for from_dev in switch_ports_var[port]:
                                list_switches[i][10][port].append(from_dev)
                    list_switches[i][10] = OrderedDict(sorted(list_switches[i][10].items(), key=lambda t: t[0][-2:]))
            switch_name.append(list_switches[i][0])
        if len(switch_name) == 1:
            switches_name = switch_name[0]
        else:
            switches_name = ' или '.join(switch_name)

        request.session['list_switches'] = list_switches

        wirelessform = WirelessForm(initial={'kad': switches_name, 'port': 'свободный'})
        context = {
            'pps': pps,
            'oattr': oattr,
            'list_switches': list_switches,
            'sreda': sreda,
            'turnoff': turnoff,
            'wirelessform': wirelessform
        }

        return render(request, 'tickets/env.html', context)

def csw(request):
    if request.method == 'POST':
        cswform = CswForm(request.POST)

        if cswform.is_valid():
            model_csw = cswform.cleaned_data['model_csw']
            port_csw = cswform.cleaned_data['port_csw']
            logic_csw_1000 = cswform.cleaned_data['logic_csw_1000']
            request.session['model_csw'] = model_csw
            request.session['port_csw'] = port_csw
            request.session['logic_csw_1000'] = logic_csw_1000
            request.session['logic_csw'] = True
            return redirect('data')
    else:
        sreda = request.session['sreda']
        if sreda == '2' or sreda == '4':
            cswform = CswForm(initial={'model_csw': 'D-Link DGS-1100-06/ME', 'port_csw': '6'})
        else:
            cswform = CswForm(initial={'model_csw': 'D-Link DGS-1100-06/ME', 'port_csw': '5'})

        context = {
            'cswform': cswform
        }
        return render(request, 'tickets/csw.html', context)



def data(request):
    user = User.objects.get(username=request.user.username)
    credent = cache.get(user)
    username = credent['username']
    password = credent['password']
    #pps = request.session['pps']
    #services_plus_desc = request.session['services_plus_desc']
    #turnoff = request.session['turnoff']
    #sreda = request.session['sreda']
    #tochka = request.session['tochka']
    #address = request.session['address']
    #oattr = request.session['oattr']


    #counter_line_services = request.session['counter_line_services']
    #print('!!!!!counter_line_services')
    #print(counter_line_services)
    spp_link = request.session['spplink']


    templates = ckb_parse(username, password)
    request.session['templates'] = templates
    #request.session['list_switches'] = list_switches



    variables = ['port', 'logic_csw', 'device_pps', 'access_point', 'speed_port', 'device_client', 'list_switches', 'router_shpd',
                 'type_shpd', 'type_cks', 'type_portvk', 'type_portvm', 'policer_vk', 'new_vk', 'exist_vk', 'model_csw', 'port_csw',
                 'logic_csw_1000', 'pointA', 'pointB', 'policer_cks', 'policer_vm', 'new_vm', 'exist_vm', 'vm_inet', 'hotspot_points',
                 'hotspot_users', 'exist_hotspot_client', 'camera_number', 'camera_model', 'voice', 'deep_archive', 'camera_place_one', 'camera_place_two',
                 'vgw', 'channel_vgw', 'ports_vgw', 'local_type', 'local_ports', 'sks_poe', 'sks_router', 'lvs_busy', 'lvs_switch',
                 'ppr', 'type_itv', 'cnt_itv', 'pps', 'services_plus_desc', 'sreda', 'address', 'counter_line_services', 'templates',
                 'readable_services', 'type_pass', 'head', 'type_install_csw', 'selected_ono', 'counter_exist_line', 'from_node', 'log_change',
                 'new_mask', 'change_type_port_exist_serv', 'change_type_port_new_serv', 'routed_ip', 'routed_vrf', 'type_change_service',
                 'all_cks_in_tr', 'kad', 'all_portvk_in_tr', 'new_without_csw_job_services', 'new_with_csw_job_services',
                 'pass_without_csw_job_services', 'new_no_spd_jobs_services']



    value_vars = dict()

    for i in variables:
        try:
            request.session[i]
        except KeyError:
            value_vars.update({i: None})
        else:
            value_vars.update({i: request.session[i]})

    request.session['templates'] = templates

    if value_vars.get('type_pass') and 'Организация доп.услуги с установкой КК' in value_vars.get('type_pass'):
        #counter_exist_line = value_vars.get('counter_exist_line')
        #print('!!!type_counter_exis')
        #print(type(counter_exist_line))
        #print('!!!')
        #print(value_vars.get('readable_services'))
        #print(counter_exist_line)
        counter_line_services = value_vars.get('counter_line_services') + value_vars.get('counter_exist_line')
        print(counter_line_services)
        value_vars.update({'counter_line_services': counter_line_services})
        titles, result_services, result_services_ots, value_vars = extra_services(value_vars)
        value_vars.update({'result_services': result_services})
        value_vars.update({'result_services_ots': result_services_ots})
    if value_vars.get('type_pass') and 'Перенос существующих сервисов' in value_vars.get('type_pass'):
        print('!!!!!!perenossss')
        counter_line_services = value_vars.get('counter_line_services')
        value_vars.update({'counter_line_services': value_vars.get('counter_exist_line')})
        result_services, result_services_ots, value_vars = passage_services(value_vars)
        value_vars.update({'counter_line_services': counter_line_services})
        value_vars.update({'result_services': result_services})
        value_vars.update({'result_services_ots': result_services_ots})
    if value_vars.get('type_pass') and 'Организация доп.услуги без установки КК' in value_vars.get('type_pass'):
        print('!!!!!!extra bez csw')
        value_vars.update({'services_plus_desc': value_vars.get('new_without_csw_job_services')})
        result_services, result_services_ots, value_vars = client_new(value_vars)
    if value_vars.get('type_pass') and 'Изменение/организация сервисов без монтаж. работ' in value_vars.get('type_pass'):
        print('!!!!!!change')
        titles, result_services, result_services_ots, value_vars = change_services(value_vars)
    if value_vars.get('type_pass') and 'Организация сервиса(не СПД)' in value_vars.get('type_pass'):
        print('!!!!!!!!!no spddddd')
        value_vars.update({'counter_line_services': 0})
        value_vars.update({'services_plus_desc': value_vars.get('new_no_spd_jobs_services')})
        result_services, result_services_ots, value_vars = client_new(value_vars)
    if not value_vars.get('type_pass'):
        result_services, result_services_ots, value_vars = client_new(value_vars)

    titles = _titles(result_services, result_services_ots)
    userlastname = None
    if request.user.is_authenticated:
        userlastname = request.user.last_name
    now = datetime.datetime.now()
    now = now.strftime("%d.%m.%Y")
    titles = ''.join(titles)
    result_services = '\n\n\n'.join(result_services)
    if value_vars.get('type_pass') and value_vars.get('type_pass') == 'Организация доп.услуги с установкой КК':
        need = 'Требуется в данной точке организовать доп. услугу.'
        result_services = 'ОУЗП СПД ' + userlastname + ' ' + now + '\n\n' + value_vars.get('head') +'\n\n'+ need + '\n\n' + titles + '\n' + result_services
    elif value_vars.get('type_pass') and value_vars.get('type_pass') == 'Перенос существующих сервисов':
        need = 'Требуется перенести услугу в новую точку подключения.'
        result_services = 'ОУЗП СПД ' + userlastname + ' ' + now + '\n\n' + value_vars.get('head') +'\n\n'+ need + '\n\n' + titles + '\n' + result_services
    elif value_vars.get('type_pass') and value_vars.get('type_pass') == 'Организация доп.услуги без установки КК':
        need = 'Требуется в данной точке организовать доп. услугу.'
        result_services = 'ОУЗП СПД ' + userlastname + ' ' + now + '\n\n' + value_vars.get('head') +'\n\n'+ need + '\n\n' + titles + '\n' + result_services
    else:
        result_services = 'ОУЗП СПД ' + userlastname + ' ' + now + '\n\n' + titles + '\n' + result_services
    counter_str_ortr = result_services.count('\n')




    if result_services_ots == None:
        counter_str_ots = 1
    else:
        result_services_ots = '\n\n\n'.join(result_services_ots)
        result_services_ots = 'ОУЗП СПД ' + userlastname + ' ' + now + '\n\n' + result_services_ots
        #result_services_ots = result_services_ots.replace('\n', '&#13;&#10;')
        counter_str_ots = result_services_ots.count('\n')

    request.session['kad'] = value_vars.get('kad')
    request.session['titles'] = titles
    request.session['result_services'] = result_services
    request.session['counter_str_ortr'] = counter_str_ortr
    request.session['result_services_ots'] = result_services_ots
    request.session['counter_str_ots'] = counter_str_ots


    try:
        manlink = request.session['manlink']
    except KeyError:
        manlink = None

    if manlink:
        return redirect('unsaved_data')
    else:
        return redirect('saved_data')


def unsaved_data(request):

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
    # request.session.flush()
    #list_session_keys = []
    #for key in request.session.keys():
    #    if key.startswith('_'):
    #        pass
    #    else:
    #       list_session_keys.append(key)
    #or key in list_session_keys:
    #   del request.session[key]

    return render(request, 'tickets/data.html', context)




def saved_data(request):
    if request.method == 'POST':
        ortrform = OrtrForm(request.POST)

        if ortrform.is_valid():
            services_plus_desc = request.session['services_plus_desc']
            oattr = request.session['oattr']
            counter_str_ortr = request.session['counter_str_ortr']
            counter_str_ots = request.session['counter_str_ots']
            result_services_ots = request.session['result_services_ots']
            try:
                list_switches = request.session['list_switches']
            except KeyError:
                list_switches = None
            now = datetime.datetime.now()

            ortr_field = ortrform.cleaned_data['ortr_field']
            ots_field = ortrform.cleaned_data['ots_field']
            pps = ortrform.cleaned_data['pps']
            kad = ortrform.cleaned_data['kad']
            ticket_tr_id = request.session['ticket_tr_id']
            ticket_tr = TR.objects.get(id=ticket_tr_id)
            ticket_k = ticket_tr.ticket_k
            ticket_tr.pps = pps
            ticket_tr.kad = kad
            ticket_tr.save()
            ortr_id = request.session['ortr_id']
            ortr = OrtrTR.objects.get(id=ortr_id)
            ortr.ortr = ortr_field
            ortr.ots = ots_field
            ortr.save()
            #print(ortrform.cleaned_data['ots_field'])
            #if ortrform.cleaned_data['ots_field'] == None:
            #    pass
            #else:

            #ots_id = request.session['ots_id']
            #ots = OtsTR.objects.get(id=ots_id)
            #ots.ots = ots_field
            #ots.save()

            context = {
                'ticket_k': ticket_k,
                'services_plus_desc': services_plus_desc,
                'oattr': oattr,
                'result_services_ots': result_services_ots,
                #'now': now,
                'list_switches': list_switches,
                'counter_str_ortr': counter_str_ortr,
                'counter_str_ots': counter_str_ots,
                'ortrform': ortrform

            }

            return render(request, 'tickets/saved_data.html', context)

    else:
        services_plus_desc = request.session['services_plus_desc']
        oattr = request.session['oattr']
        kad = request.session['kad']
        #pps = 'Не требуется' if kad == 'Не требуется' else request.session['pps']
        print('!!!!!kad')
        print(kad)
        if kad == 'Не требуется':
            pps = 'Не требуется'
        else:
            pps = request.session['pps']
        result_services = request.session['result_services']
        counter_str_ortr = request.session['counter_str_ortr']
        counter_str_ots = request.session['counter_str_ots']
        result_services_ots = request.session['result_services_ots']
        try:
            list_switches = request.session['list_switches']
        except KeyError:
            list_switches = None

        #now = datetime.datetime.now()

        ticket_tr_id = request.session['ticket_tr_id']
        ticket_tr = TR.objects.get(id=ticket_tr_id)
        ticket_k = ticket_tr.ticket_k
        ticket_tr.kad = kad
        ticket_tr.pps = pps
        ticket_tr.save()

        if ticket_tr.ortrtr_set.all():
            ortr = ticket_tr.ortrtr_set.all()[0]
        else:
            ortr = OrtrTR()

        #ortr = OrtrTR()
        ortr.ticket_tr = ticket_tr
        #ortr.title_ortr = titles
        ortr.ortr = result_services
        ortr.ots = result_services_ots
        ortr.save()
        request.session['ortr_id'] = ortr.id
        #if result_services_ots:
        #ots = OtsTR()
        #ots.ticket_tr = ticket_tr
        #ots.ots = result_services_ots
        #ots.save()
        #request.session['ots_id'] = ots.id

        ortrform = OrtrForm(initial={'ortr_field': ortr.ortr, 'ots_field': ortr.ots, 'pps': pps, 'kad': kad})

        context = {
            'ticket_k': ticket_k,
            'services_plus_desc': services_plus_desc,
            'oattr': oattr,
            'result_services_ots': result_services_ots,
            #'now': now,
            'list_switches': list_switches,
            'counter_str_ortr': counter_str_ortr,
            'counter_str_ots': counter_str_ots,
            'ortrform': ortrform

        }

        return render(request, 'tickets/saved_data.html', context)


def edit_tr(request, dID, ticket_spp_id, trID):
    if request.method == 'POST':
        ortrform = OrtrForm(request.POST)

        if ortrform.is_valid():

            ortr_field = ortrform.cleaned_data['ortr_field']
            ots_field = ortrform.cleaned_data['ots_field']
            pps = ortrform.cleaned_data['pps']
            kad = ortrform.cleaned_data['kad']
            ticket_tr_id = request.session['ticket_tr_id']
            ticket_tr = TR.objects.get(id=ticket_tr_id)

            ticket_tr.pps = pps
            ticket_tr.kad = kad
            ticket_tr.save()
            ortr_id = request.session['ortr_id']
            ortr = OrtrTR.objects.get(id=ortr_id)
            ortr.ortr = ortr_field
            ortr.ots = ots_field
            ortr.save()

            counter_str_ortr = ortr.ortr.count('\n')
            if ortr.ots:
                #counter_str_ots = 1
                counter_str_ots = ortr.ots.count('\n')
            else:
                #counter_str_ots = ortr.ots.count('\n')
                counter_str_ots = 1
            #print(ortrform.cleaned_data['ots_field'])
            #if ortrform.cleaned_data['ots_field'] == None:
            #    pass
            #else:

            #ots_id = request.session['ots_id']
            #ots = OtsTR.objects.get(id=ots_id)
            #ots.ots = ots_field
            #ots.save()

            context = {
                'services_plus_desc': ticket_tr.services,
                'oattr': ticket_tr.oattr,
                #'result_services_ots': result_services_ots,
                #'now': now,
                #'list_switches': list_switches,
                'counter_str_ortr': counter_str_ortr,
                'counter_str_ots': counter_str_ots,
                'ortrform': ortrform,
                'ticket_spp_id': ticket_spp_id,
                'dID': dID,
                'ticket_tr': ticket_tr

            }
            return render(request, 'tickets/edit_tr.html', context)

    else:
        ticket_spp_id = request.session['ticket_spp_id']
        dID = request.session['dID']
        ticket_spp = SPP.objects.get(dID=dID, id=ticket_spp_id)

        #if ticket_spp.children.filter(ticket_tr=trID):
        ticket_tr = ticket_spp.children.filter(ticket_tr=trID)[0]
        request.session['ticket_tr_id'] = ticket_tr.id

        #if ticket_tr.ortrtr_set.all():
        ortr = ticket_tr.ortrtr_set.all()[0]
        request.session['ortr_id'] = ortr.id

        counter_str_ortr = ortr.ortr.count('\n')
        if ortr.ots:
            counter_str_ots = ortr.ots.count('\n')
        else:
            counter_str_ots = 1


        #try:
        #    list_switches = request.session['list_switches']
        #except KeyError:
        #    list_switches = None




        ortrform = OrtrForm(initial={'ortr_field': ortr.ortr, 'ots_field': ortr.ots, 'pps': ticket_tr.pps, 'kad': ticket_tr.kad})

        context = {
            'services_plus_desc': ticket_tr.services,
            'oattr': ticket_tr.oattr,
            #'result_services_ots': result_services_ots,
            #'now': now,
            #'list_switches': list_switches,
            'counter_str_ortr': counter_str_ortr,
            'counter_str_ots': counter_str_ots,
            'ortrform': ortrform,
            'ticket_spp_id': ticket_spp_id,
            'dID': dID,
            'ticket_tr': ticket_tr

        }
        return render(request, 'tickets/edit_tr.html', context)

@cache_check
def manually_tr(request, dID, tID, trID):
    if request.method == 'POST':
        ortrform = OrtrForm(request.POST)

        if ortrform.is_valid():
            ticket_spp_id = request.session['ticket_spp_id']
            ortr_field = ortrform.cleaned_data['ortr_field']
            ots_field = ortrform.cleaned_data['ots_field']
            pps = ortrform.cleaned_data['pps']
            kad = ortrform.cleaned_data['kad']
            ticket_tr_id = request.session['ticket_tr_id']
            ticket_tr = TR.objects.get(id=ticket_tr_id)

            ticket_tr.pps = pps
            ticket_tr.kad = kad
            ticket_tr.save()
            ortr_id = request.session['ortr_id']
            ortr = OrtrTR.objects.get(id=ortr_id)
            ortr.ortr = ortr_field
            ortr.ots = ots_field
            ortr.save()

            counter_str_ortr = ortr.ortr.count('\n')
            if ortr.ots:
                counter_str_ots = ortr.ots.count('\n')
            else:
                counter_str_ots = 1
            #print(ortrform.cleaned_data['ots_field'])
            #if ortrform.cleaned_data['ots_field'] == None:
            #    pass
            #else:

            #ots_id = request.session['ots_id']
            #ots = OtsTR.objects.get(id=ots_id)
            #ots.ots = ots_field
            #ots.save()

            context = {
                'services_plus_desc': ticket_tr.services,
                'oattr': ticket_tr.oattr,
                #'result_services_ots': result_services_ots,
                #'now': now,
                #'list_switches': list_switches,
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
            spplink = 'https://sss.corp.itmh.ru/dem_tr/dem_begin.php?dID={}&tID={}&trID={}'.format(dID, tID, trID)
            request.session['spplink'] = spplink
            ticket_spp_id = request.session['ticket_spp_id']

            ticket_spp = SPP.objects.get(dID=dID, id=ticket_spp_id)

            if ticket_spp.children.filter(ticket_tr=trID):
                return redirect('edit_tr', dID, ticket_spp_id, trID)

            ticket_tr = TR()
            ticket_tr.ticket_k = ticket_spp
            ticket_tr.ticket_tr = trID
            ticket_tr.pps = tr_params['Узел подключения клиента']
            ticket_tr.turnoff = False if tr_params['Отключение'] == 'Нет' else True
            ticket_tr.info_tr = tr_params['Информация для разработки ТР']
            ticket_tr.services = tr_params['Перечень требуемых услуг']
            ticket_tr.oattr = tr_params['Решение ОТПМ']
            ticket_tr.vID = tr_params['vID']
            ticket_tr.save()
            request.session['ticket_tr_id'] = ticket_tr.id
            print('Сохранили ТР')
            ortr = OrtrTR()
            ortr.ticket_tr = ticket_tr
            ortr.save()
            print('Сохранили ОРТР')
            request.session['ortr_id'] = ortr.id

            for service in ticket_tr.services:
                if 'Телефон' in service:
                    counter_str_ots = 10
                else:
                    counter_str_ots = 1


            ortrform = OrtrForm()

            context = {
                'services_plus_desc': ticket_tr.services,
                'oattr': ticket_tr.oattr,
                #'result_services_ots': result_services_ots,
                #'now': now,
                #'list_switches': list_switches,
                'counter_str_ortr': 10,
                'counter_str_ots': counter_str_ots,
                'ortrform': ortrform,
                'ticket_spp_id': ticket_spp_id,
                'dID': dID,
                'ticket_tr': trID

            }
            return render(request, 'tickets/edit_tr.html', context)

@cache_check
def send_to_spp(request):
    user = User.objects.get(username=request.user.username)
    credent = cache.get(user)
    username = credent['username']
    password = credent['password']
    #Получение страницы с данными о коммутаторе
    spplink = request.session['spplink']
    url = spplink.replace('dem_begin', 'dem_point')
    print(url)
    req_check = requests.get(url, verify=False, auth=HTTPBasicAuth(username, password))
    if req_check.status_code == 200:
        #url = 'https://sss.corp.itmh.ru/dem_tr/dem_point.php?dID={}&tID={}&trID={}'.format(dID, tID, trID)

        ticket_tr_id = request.session['ticket_tr_id']
        ticket_tr = TR.objects.get(id=ticket_tr_id)
        trOTO_AV = ticket_tr.pps
        trOTO_Comm = ticket_tr.kad
        vID = ticket_tr.vID
        print(trOTO_AV)
        print(vID)


        if ticket_tr.ortrtr_set.all():
            ortr = ticket_tr.ortrtr_set.all()[0]

            trOTO_Resolution = ortr.ortr
            trOTS_Resolution = ortr.ots
            print(trOTO_Resolution)

        data = {'trOTO_Resolution': trOTO_Resolution, 'trOTS_Resolution': trOTS_Resolution, 'action': 'saveVariant',
                'trOTO_AV': trOTO_AV, 'trOTO_Comm': trOTO_Comm, 'vID': vID} # {'dID': 111428, 'tID': 130916, 'trID': 54886,
                #'fType': 0, 'vID': 14147, 'noCompress': 1, 'trOTO_Blocked': 1, 'trOTO_AV': 'АВ ЕКБ Учителей 32 П1 Э2',
                #'trOTO_Comm': 'SW037-AR126-31.ekb', 'tr_OTO_Pay': 0, 'tr_OTS_Pay': 0, 'trOTMPK': 0,
                #'loadNewTask': 0}
        #data['NodeName'] = node_name.encode('utf-8')
        req = requests.post(url, verify=False, auth=HTTPBasicAuth(username, password), data=data)
        print('req.status_code send spp')
        print(req.status_code)
        return redirect(spplink)
    else:
        messages.warning(request, 'Нет доступа в ИС Холдинга')
        response = redirect('login_for_service')
        response['Location'] += '?next={}'.format(request.path)
        return response


def flush_session(request):
    list_session_keys = []
    for key in request.session.keys():
        if key.startswith('_'):
            pass
        else:
            list_session_keys.append(key)
    for key in list_session_keys:
        del request.session[key]

    return render(request, 'tickets/flush.html', {'clear': 'clear'})

def flush_session_key(request_request):
    """Данный метод в качестве параметра принимает request, очищает сессию от переменных, полученных при
    проектировании предыдущих ТР, при этом оставляет в сессии переменные относящиеся к пользователю, и возвращает тот же
     request"""
    list_session_keys = []
    for key in request_request.session.keys():
        if key.startswith('_'):
            pass
        else:
            list_session_keys.append(key)
    for key in list_session_keys:
        del request_request.session[key]
    return request_request




def hotspot(request):
    if request.method == 'POST':
        hotspotform = HotspotForm(request.POST)

        if hotspotform.is_valid():
            print(hotspotform.cleaned_data)
            hotspot_points = hotspotform.cleaned_data['hotspot_points']
            hotspot_users = hotspotform.cleaned_data['hotspot_users']
            exist_hotspot_client = hotspotform.cleaned_data['exist_hotspot_client']
            services_plus_desc = request.session['services_plus_desc']
            counter_line_services = request.session['counter_line_services']
            if hotspot_points:
                for index_service in range(len(services_plus_desc)):
                    if 'HotSpot' in services_plus_desc[index_service]:
                        for i in range(int(hotspot_points)):
                            services_plus_desc[index_service] += '|'
                counter_line_services += hotspot_points-1
            request.session['counter_line_services'] = counter_line_services
            request.session['services_plus_desc'] = services_plus_desc
            request.session['hotspot_points'] = str(hotspot_points)
            request.session['hotspot_users'] = str(hotspot_users)
            request.session['exist_hotspot_client'] = exist_hotspot_client
            tag_service = request.session['tag_service']
            tag_service.pop(0)
            request.session['tag_service'] = tag_service
            return redirect(next(iter(tag_service[0])))

    else:
        hotspot_points = request.session['hotspot_points']
        hotspot_users = request.session['hotspot_users']
        premium_plus = request.session['premium_plus']
        services_plus_desc = request.session['services_plus_desc']
        for service in services_plus_desc:
            if 'HotSpot' in service:
                service_hotspot = service
                break
        hotspotform = HotspotForm(initial={'hotspot_points': hotspot_points, 'hotspot_users': hotspot_users})
        context = {
            'premium_plus': premium_plus,
            'hotspotform': hotspotform,
            'service_hotspot': service_hotspot
        }
        return render(request, 'tickets/hotspot.html', context)

def phone(request):
    if request.method == 'POST':
        phoneform = PhoneForm(request.POST)

        if phoneform.is_valid():
            type_phone = phoneform.cleaned_data['type_phone']
            vgw = phoneform.cleaned_data['vgw']
            channel_vgw = phoneform.cleaned_data['channel_vgw']
            ports_vgw = phoneform.cleaned_data['ports_vgw']
            services_plus_desc = request.session['services_plus_desc']
            tag_service = request.session['tag_service']
            for index_service in range(len(services_plus_desc)):
                if 'Телефон' in services_plus_desc[index_service]:
                    if type_phone == 'ak':
                        services_plus_desc[index_service] += '|'
                        counter_line_services = request.session['counter_line_services']
                        counter_line_services += 1
                        request.session['counter_line_services'] = counter_line_services
                        sreda = request.session['sreda']
                        if sreda == '2' or sreda == '4':
                            if 'vols' in tag_service:
                                pass
                            else:
                                tag_service.insert(1, {'vols': None})
                        elif sreda == '3':
                            if 'wireless' in tag_service:
                                pass
                            else:
                                tag_service.insert(1, {'wireless': None})
                        elif sreda == '1':
                            if 'copper' in tag_service:
                                pass
                            else:
                                tag_service.insert(1, {'copper': None})

                    elif type_phone == 'ap':
                        services_plus_desc[index_service] += '/'
                    elif type_phone == 'ab':
                        services_plus_desc[index_service] += '\\'
            request.session['services_plus_desc'] = services_plus_desc
            request.session['vgw'] = vgw
            request.session['channel_vgw'] = channel_vgw
            request.session['ports_vgw'] = ports_vgw
            tag_service = request.session['tag_service']
            tag_service.pop(0)
            request.session['tag_service'] = tag_service
            return redirect(next(iter(tag_service[0])))


    else:
        services_plus_desc = request.session['services_plus_desc']
        for service in services_plus_desc:
            if 'Телефон' in service:
                regex_ports_vgw = ['(\d+)-порт', '(\d+) порт', '(\d+)порт']
                for regex in regex_ports_vgw:
                    match_ports_vgw = re.search(regex, service)
                    if match_ports_vgw:
                        reg_ports_vgw = match_ports_vgw.group(1)
                    else:
                        reg_ports_vgw = 'Нет данных'
                    break

                regex_channel_vgw = ['(\d+)-канал', '(\d+) канал', '(\d+)канал']
                for regex in regex_channel_vgw:
                    match_channel_vgw = re.search(regex, service)
                    if match_channel_vgw:
                        reg_channel_vgw = match_channel_vgw.group(1)
                    else:
                        reg_channel_vgw = 'Нет данных'
                    break
                service_vgw = service
                if 'ватс' in service.lower():
                    vats = True
                else:
                    vats = False
                break

        phoneform = PhoneForm(initial={'type_phone': 's', 'vgw': 'Не требуется', 'channel_vgw': reg_channel_vgw, 'ports_vgw': reg_ports_vgw})
        context = {
            'service_vgw': service_vgw,
            'vats': vats,
            'phoneform': phoneform
        }

        return render(request, 'tickets/phone.html', context)

def local(request):
    if request.method == 'POST':
        localform = LocalForm(request.POST)

        if localform.is_valid():
            local_type = localform.cleaned_data['local_type']
            local_ports = localform.cleaned_data['local_ports']
            request.session['local_type'] = local_type
            request.session['local_ports'] = str(local_ports)
            tag_service = request.session['tag_service']
            tag_service.pop(0)
            request.session['tag_service'] = tag_service
            if local_type == 'СКС':
                return redirect('sks')
            else:
                return redirect('lvs')

    else:
        services_plus_desc = request.session['services_plus_desc']
        for service in services_plus_desc:
            if 'ЛВС' in service:
                service_lvs = service
                request.session['service_lvs'] = service_lvs
                break

        localform = LocalForm()
        context = {
            'service_lvs': service_lvs,
            'localform': localform
        }

        return render(request, 'tickets/local.html', context)


def sks(request):
    if request.method == 'POST':
        sksform = SksForm(request.POST)

        if sksform.is_valid():
            sks_poe = sksform.cleaned_data['sks_poe']
            sks_router = sksform.cleaned_data['sks_router']
            request.session['sks_poe'] = sks_poe
            request.session['sks_router'] = sks_router
            tag_service = request.session['tag_service']
            return redirect(next(iter(tag_service[0])))


    else:
        service_lvs = request.session['service_lvs']
        sksform = SksForm()
        context = {
            'service_lvs': service_lvs,
            'sksform': sksform
        }

        return render(request, 'tickets/sks.html', context)


def lvs(request):
    if request.method == 'POST':
        lvsform = LvsForm(request.POST)

        if lvsform.is_valid():
            lvs_busy = lvsform.cleaned_data['lvs_busy']
            lvs_switch = lvsform.cleaned_data['lvs_switch']
            request.session['lvs_busy'] = lvs_busy
            request.session['lvs_switch'] = lvs_switch
            tag_service = request.session['tag_service']
            return redirect(next(iter(tag_service[0])))


    else:
        service_lvs = request.session['service_lvs']
        lvsform = LvsForm()
        context = {
            'service_lvs': service_lvs,
            'lvsform': lvsform
        }

        return render(request, 'tickets/lvs.html', context)




def itv(request):
    if request.method == 'POST':
        itvform = ItvForm(request.POST)

        if itvform.is_valid():
            type_itv = itvform.cleaned_data['type_itv']
            cnt_itv = itvform.cleaned_data['cnt_itv']
            services_plus_desc = request.session['services_plus_desc']
            tag_service = request.session['tag_service']
            tag_service.pop(0)
            for index_service in range(len(services_plus_desc)):
                if 'iTV' in services_plus_desc[index_service]:
                    if type_itv == 'novl':
                        services_plus_desc[index_service] = services_plus_desc[index_service][:-1]
                        counter_line_services = request.session['counter_line_services']
                        counter_line_services -= 1
                        request.session['counter_line_services'] = counter_line_services
                        if len(services_plus_desc) == 1:
                            tag_service.pop()
                            tag_service.append({'data': None})
            request.session['type_itv'] = type_itv
            request.session['cnt_itv'] = cnt_itv
            request.session['services_plus_desc'] = services_plus_desc

            print('!!!!tagservice')
            print(tag_service)
            request.session['tag_service'] = tag_service
            return redirect(next(iter(tag_service[0])))


    else:
        services_plus_desc = request.session['services_plus_desc']
        for service in services_plus_desc:
            if 'iTV' in service:
                service_itv = service
                break
        itvform = ItvForm(initial={'type_itv': 'novl'})
        return render(request, 'tickets/itv.html', {'itvform': itvform, 'service_itv': service_itv})

def cks(request):
    if request.method == 'POST':
        cksform = CksForm(request.POST)

        if cksform.is_valid():
            pointA = cksform.cleaned_data['pointA']
            pointB = cksform.cleaned_data['pointB']
            policer_cks = cksform.cleaned_data['policer_cks']
            type_cks = cksform.cleaned_data['type_cks']
            if type_cks == 'trunk':
                request.session['counter_line_services'] = 1
            try:
                all_cks_in_tr = request.session['all_cks_in_tr']
            except KeyError:
                all_cks_in_tr = dict()
            #all_cks_in_tr.update({})
            #request.session['pointA'] = pointA
            #request.session['pointB'] = pointB
            #request.session['policer_cks'] = policer_cks
            #request.session['type_cks'] = type_cks
            tag_service = request.session['tag_service']
            service = tag_service[0]['cks']
            all_cks_in_tr.update({service:{'pointA': pointA, 'pointB': pointB, 'policer_cks': policer_cks, 'type_cks': type_cks}})
            tag_service.pop(0)
            request.session['tag_service'] = tag_service
            request.session['all_cks_in_tr'] = all_cks_in_tr
            return redirect(next(iter(tag_service[0])))


    else:
        #services_plus_desc = request.session['services_plus_desc']
        tag_service = request.session['tag_service']
        service = tag_service[0]['cks']
        #services_cks = []
        #for service in services_plus_desc:
        #    if 'ЦКС' in service:
        #        services_cks.append(service)

        user = User.objects.get(username=request.user.username)
        credent = cache.get(user)
        username = credent['username']
        password = credent['password']


        try:
            tochka = request.session['tochka']
            list_cks = match_cks(tochka, username, password)
        except KeyError:
            list_cks = request.session['cks_points']
        if list_cks[0] == 'Access denied':
            messages.warning(request, 'Нет доступа в ИС Холдинга')
            response = redirect('login_for_service')
            response['Location'] += '?next={}'.format(request.path)
            return response
        else:
            if len(list_cks) == 2:
                #pointsCKS = list_strok[0].split('-')
                pointA = list_cks[0]
                pointB = list_cks[1]
                cksform = CksForm(initial={'pointA': pointA, 'pointB': pointB})
                return render(request, 'tickets/cks.html', {'cksform': cksform, 'services_cks': service})
            else:
                cksform = CksForm()
                return render(request, 'tickets/cks.html', {'cksform': cksform, 'list_strok': list_cks, 'services_cks': service})


def shpd(request):
    if request.method == 'POST':
        shpdform = ShpdForm(request.POST)

        if shpdform.is_valid():
            router_shpd = shpdform.cleaned_data['router']
            type_shpd = shpdform.cleaned_data['type_shpd']
            if type_shpd == 'trunk':
                request.session['counter_line_services'] = 1
            request.session['router_shpd'] = router_shpd
            request.session['type_shpd'] = type_shpd
            tag_service = request.session['tag_service']
            tag_service.pop(0)
            request.session['tag_service'] = tag_service
            return redirect(next(iter(tag_service[0])))


    else:
        services_plus_desc = request.session['services_plus_desc']
        services_shpd = []
        for service in services_plus_desc:
            if 'Интернет, DHCP' in service or 'Интернет, блок Адресов Сети Интернет' in service:
                services_shpd.append(service)
        shpdform = ShpdForm(initial={'shpd': 'access'})
        return render(request, 'tickets/shpd.html', {'shpdform': shpdform, 'services_shpd': services_shpd})


def portvk(request):
    if request.method == 'POST':
        portvkform = PortVKForm(request.POST)

        if portvkform.is_valid():
            new_vk = portvkform.cleaned_data['new_vk']
            exist_vk = '"{}"'.format(portvkform.cleaned_data['exist_vk'])
            policer_vk = portvkform.cleaned_data['policer_vk']
            type_portvk = portvkform.cleaned_data['type_portvk']
            if type_portvk == 'trunk':
                request.session['counter_line_services'] = 1

            try:
                all_portvk_in_tr = request.session['all_portvk_in_tr']
            except KeyError:
                all_portvk_in_tr = dict()

            tag_service = request.session['tag_service']
            service = tag_service[0]['portvk']
            all_portvk_in_tr.update({service:{'new_vk': new_vk, 'exist_vk': exist_vk, 'policer_vk': policer_vk, 'type_portvk': type_portvk}})
            tag_service.pop(0)
            request.session['tag_service'] = tag_service
            request.session['all_portvk_in_tr'] = all_portvk_in_tr

            #request.session['policer_vk'] = policer_vk
            #request.session['new_vk'] = new_vk
            #request.session['exist_vk'] = exist_vk
            #request.session['type_portvk'] = type_portvk
            #tag_service = request.session['tag_service']
            #tag_service.pop(0)
            #request.session['tag_service'] = tag_service
            return redirect(next(iter(tag_service[0])))


    else:
        services_plus_desc = request.session['services_plus_desc']
        services_vk = []
        for service in services_plus_desc:
            if 'Порт ВЛС' in service:
                services_vk.append(service)
        portvkform = PortVKForm()
        return render(request, 'tickets/portvk.html', {'portvkform': portvkform, 'services_vk': services_vk})

def portvm(request):
    if request.method == 'POST':
        portvmform = PortVMForm(request.POST)

        if portvmform.is_valid():
            new_vm = portvmform.cleaned_data['new_vm']
            exist_vm = '"{}"'.format(portvmform.cleaned_data['exist_vm'])
            policer_vm = portvmform.cleaned_data['policer_vm']
            vm_inet = portvmform.cleaned_data['vm_inet']
            type_portvm = portvmform.cleaned_data['type_portvm']
            if type_portvm == 'trunk':
                request.session['counter_line_services'] = 1

            request.session['policer_vm'] = policer_vm
            request.session['new_vm'] = new_vm
            request.session['exist_vm'] = exist_vm
            request.session['vm_inet'] = vm_inet
            request.session['type_portvm'] = type_portvm
            tag_service = request.session['tag_service']
            tag_service.pop(0)
            request.session['tag_service'] = tag_service
            return redirect(next(iter(tag_service[0])))


    else:
        services_plus_desc = request.session['services_plus_desc']
        services_vm = []
        for service in services_plus_desc:
            if 'Порт ВМ' in service:
                services_vm.append(service)
        portvmform = PortVMForm()
        return render(request, 'tickets/portvm.html', {'portvmform': portvmform, 'services_vm': services_vm})


def video(request):
    if request.method == 'POST':
        videoform = VideoForm(request.POST)

        if videoform.is_valid():
            print(videoform.cleaned_data)
            camera_number = videoform.cleaned_data['camera_number']
            camera_model = videoform.cleaned_data['camera_model']
            voice = videoform.cleaned_data['voice']
            deep_archive = videoform.cleaned_data['deep_archive']
            camera_place_one = videoform.cleaned_data['camera_place_one']
            camera_place_two = videoform.cleaned_data['camera_place_two']


            request.session['camera_number'] = str(camera_number)
            request.session['camera_model'] = camera_model
            request.session['voice'] = voice
            request.session['deep_archive'] = deep_archive
            request.session['camera_place_one'] = camera_place_one
            request.session['camera_place_two'] = camera_place_two
            tag_service = request.session['tag_service']
            tag_service.pop(0)
            request.session['tag_service'] = tag_service
            return redirect(next(iter(tag_service[0])))

    else:
        services_plus_desc = request.session['services_plus_desc']
        for service in services_plus_desc:
            if 'Видеонаблюдение' in service:
                service_video = service
                request.session['service_video'] = service_video
                break
        task_otpm = request.session['task_otpm']
        videoform = VideoForm() #initial={'hotspot_points': hotspot_points, 'hotspot_users': hotspot_users})
        context = {
            'service_video': service_video,
            'videoform': videoform,
            'task_otpm': task_otpm
        }
        return render(request, 'tickets/video.html', context)

def get_contract_id(login, password, contract):
    url = f'https://cis.corp.itmh.ru/doc/crm/contract_ajax.ashx?term={contract}'
    req = requests.get(url, verify=False, auth=HTTPBasicAuth(login, password))
    contract_list = req.json()
    print(contract_list)
    if len(contract_list) > 1:
        pass
    elif len(contract_list) == 0:
        pass
    else:
        contract_id = contract_list[0].get('id')
        print(contract_id)
    return contract_id

def get_contract_resources(login, password, contract_id):
    url = f'https://cis.corp.itmh.ru/doc/CRM/contract.aspx?contract={contract_id}'
    req = requests.get(url, verify=False, auth=HTTPBasicAuth(login, password))
    soup = BeautifulSoup(req.content.decode('utf-8'), "html.parser")
    table = soup.find('table', id="ctl00_middle_Table_ONO")
    rows_tr = table.find_all('tr')
    ono = []
    for index, element_rows_tr in enumerate(rows_tr):
        ono_inner = []
        for element_rows_td in element_rows_tr.find_all('td'):
            ono_inner.append(element_rows_td.text)
        ono_inner.pop(5)
        ono_inner.pop(2)
        ono.append(ono_inner)
    return ono

@cache_check
def get_resources(request):
    """Данный метод получает от пользователя номер договора. с помощью метода get_contract_id получает ID договора. С
    помощью метода get_contract_resources получает ресурсы с контракта. Отправляет пользователя на страницу, где
    отображаются эти ресурсы"""
    user = User.objects.get(username=request.user.username)
    credent = cache.get(user)
    username = credent['username']
    password = credent['password']
    if request.method == 'POST':
        print('!!!!req_con')
        print(request.POST)
        contractform = ContractForm(request.POST)
        if contractform.is_valid():
            print(contractform.cleaned_data)
            contract = contractform.cleaned_data['contract']
            contract_id = get_contract_id(username, password, contract)
            ono = get_contract_resources(username, password, contract_id)
            phone_address = check_contract_phone_exist(username, password, contract_id)
            if phone_address:
                request.session['phone_address'] = phone_address
            request.session['ono'] = ono
            request.session['contract'] = contract
            if ono:
                #return redirect('show_resources')
                return redirect('test_formset')
            else:
                messages.warning(request, 'Договора не найдено')
                return redirect('get_resources')
    else:
        contractform = ContractForm()

    return render(request, 'tickets/contract.html', {'contractform': contractform})

def show_resources(request):
    ono = request.session['selected_ono']
    contract = request.session['contract']
    context = {
        'ono': ono,
        'contract': contract
    }
    return render(request, 'tickets/show_resources.html', context)


def _replace_wda_wds(device):
    replace_wda_wds = device.split('-')
    replace_wda_wds[0] = replace_wda_wds[0].replace('WDA', 'WDS')
    replace_wda_wds.pop(1)
    device = '-'.join(replace_wda_wds)
    return device

def _get_chain_data(login, password, device):
    url = f'https://mon.itss.mirasystem.net/mp/index.py/chain_update?hostname={device}'
    req = requests.get(url, verify=False, auth=HTTPBasicAuth(login, password))
    chains = req.json()
    return chains


def _get_downlink(chains, device):
    if device.startswith('WDA'):
        device = _replace_wda_wds(device)
        print('!!!dev')
        print(device)


    downlink = []
    downlevel = 20
    temp_chains2 = []
    for chain in chains:
        #print('!!chain')
        #print(chain)

        if device == chain.get('host_name'):
            downlevel = chain.get('level')
        elif downlevel < chain.get('level'):
            if device.startswith('WDS'):
                if device == chain.get('host_name'):
                    pass
                elif chain.get('host_name').startswith(device.split('-')[0].replace('S', 'A')):
                    pass
                else:
                    if 'VGW' not in chain.get('host_name'):
                        downlink.append(chain.get('host_name'))
            elif device.startswith('CSW'):
                if device != chain.get('host_name'):
                    if 'VGW' not in chain.get('host_name'):
                        print('!!!downle')
                        print(downlevel)
                        downlink.append(chain.get('host_name'))
    return downlink

def _get_vgw_on_node(chains, device):
    vgw_on_node = None
    level_device = 0
    for chain in chains:
        if device == chain.get('host_name'):
            level_device = chain.get('level')

        if device.startswith('SW') or device.startswith('CSW') or device.startswith('WDA'):
            if 'VGW' in chain.get('host_name'):
                level_vgw = chain.get('level')
                if level_vgw == level_device + 1:
                    #vgw_on_node.append(chain.get('host_name'))
                    vgw_on_node = 'exist'
                    break

    return vgw_on_node

def _get_node_device(chains, device):
    for chain in chains:
        if device == chain.get('host_name'):
            node_device = chain.get('alias')
    return node_device

def _get_extra_node_device(chains, device, node_device):
    extra_node_device = []
    for chain in chains:
        if node_device == chain.get('alias') and device != chain.get('host_name'):
            extra_node_device.append(chain.get('host_name'))
    return extra_node_device


def _get_uplink(chains, device, max_level):
    if device.startswith('WDA'):
        device = _replace_wda_wds(device)
        print('!!!dev')
        print(device)
    elif device.startswith('WFA'):
        replace_wfa_wfs = device.split('-')
        replace_wfa_wfs[0] = replace_wfa_wfs[0].replace('WFA', 'WFS')
        replace_wfa_wfs.pop(1)
        device = '-'.join(replace_wfa_wfs)

    uplink = None
    for chain in chains:

        #if device.startswith('SW') or device.startswith('CSW') or device.startswith('WDS'):
        #    if 'VGW' in chain.get('host_name'):
        #        vgw_on_node.append(chain.get('host_name'))

        if device in chain.get('title'):
            temp_chains2 = chain.get('title').split('\nLink')

            # print(temp_chains2)
            for i in temp_chains2:
                # print(i)
                if device.startswith('CSW') or device.startswith('WDS') or device.startswith('WFS'):
                    if f'-{device}' in i:  # для всех случаев подключения CSW, WDS, WFS
                        preuplink = i.split(f'-{device}')
                        preuplink = preuplink[0]
                        match_uplink = re.search('_(\S+?)_(\S+)', preuplink)
                        uplink_host = match_uplink.group(1)
                        uplink_port = match_uplink.group(2)
                        if uplink_host == chain.get('host_name') and chain.get('level') < max_level:
                            print('!!up')
                            print(uplink_host)
                            print(uplink_port)
                            max_level = chain.get('level')

                            if 'thernet' in uplink_port:
                                uplink_port = uplink_port.replace('_', '/')
                            else:
                                uplink_port = uplink_port.replace('_', ' ')
                            uplink = uplink_host + ' ' + uplink_port

                        else:
                            pass
                    elif device in i and 'WDA' in i:  # исключение только для случая, когда CSW подключен от WDA
                        link = i.split('-WDA')
                        uplink = 'WDA' + link[1].replace('_', ' ').replace('\n', '')
                        print('!!!wdauplink')
                        print(uplink)


    return uplink, max_level

@cache_check
def get_chain(request):
    user = User.objects.get(username=request.user.username)
    credent = cache.get(user)
    username = credent['username']
    password = credent['password']
    if request.method == 'POST':
        chainform = ChainForm(request.POST)
        if chainform.is_valid():
            print(chainform.cleaned_data)
            chain_device = chainform.cleaned_data['chain_device']
            chains = _get_chain_data(username,password, chain_device)
            downlink = _get_downlink(chains, chain_device)
            vgw_chains = _get_vgw_on_node(chains, chain_device)
            node_mon = _get_node_device(chains, chain_device)
            max_level = 20
            uplink, max_level = _get_uplink(chains, chain_device, max_level)
            #total_downlink = downlink   выносится в отдельную переменную, чтобы в дальнейшем цикле while не перезаписывался
            all_chain = []
            all_chain.append(uplink)
            if uplink:
                while uplink.startswith('CSW') or uplink.startswith('WDA'):
                    next_chain_device = uplink.split()
                    all_chain.pop()
                    if uplink.startswith('CSW') and chain_device.startswith('WDA'):
                        all_chain.append(_replace_wda_wds(chain_device))
                    all_chain.append(next_chain_device[0])
                    if uplink.startswith('WDA'):
                        all_chain.append(_replace_wda_wds(next_chain_device[0]))
                    uplink, max_level = _get_uplink(chains, next_chain_device[0], max_level)
                    all_chain.append(uplink)
            request.session['node_mon'] = node_mon
            request.session['uplink'] = all_chain
            request.session['downlink'] = downlink
            request.session['vgw_chains'] = vgw_chains
            if node_mon:
                return redirect('show_chains')
            else:
                messages.warning(request, 'не найдено')
                return redirect('get_chain')
    else:
        chainform = ChainForm()

    return render(request, 'tickets/get_chain.html', {'chainform': chainform})


def show_chains(request):
    node_mon = request.session['node_mon']
    uplink = request.session['uplink']
    downlink = request.session['downlink']
    vgw_chains = request.session['vgw_chains']
    selected_ono = request.session['selected_ono']
    waste_vgw = request.session['waste_vgw']
    context = {
        'node_mon': node_mon,
        'uplink': uplink,
        'downlink': downlink,
        'vgw_chains': vgw_chains,
        'selected_ono': selected_ono,
        'waste_vgw': waste_vgw
    }
    return render(request, 'tickets/chain.html', context)


def _counter_line_services(services_plus_desc):
    """Данный метод проходит по списку услуг, чтобы определить количество организуемых линий от СПД и в той услуге,
     где требуется линия добавляется спец. символ. Метод возвращает количество требуемых линий"""
    hotspot_points = None
    for index_service in range(len(services_plus_desc)):
        if 'Интернет, блок Адресов Сети Интернет' in services_plus_desc[index_service]:
            services_plus_desc[index_service] += '|'
            replace_index = services_plus_desc[index_service]
            services_plus_desc.remove(replace_index)
            services_plus_desc.insert(0, replace_index)
        elif 'Интернет, DHCP' in services_plus_desc[index_service]:
            services_plus_desc[index_service] += '|'
            replace_index = services_plus_desc[index_service]
            services_plus_desc.remove(replace_index)
            services_plus_desc.insert(0, replace_index)
        elif 'iTV' in services_plus_desc[index_service]:
            services_plus_desc[index_service] += '|'
        elif 'ЦКС' in services_plus_desc[index_service]:
            services_plus_desc[index_service] += '|'
        elif 'Порт ВЛС' in services_plus_desc[index_service]:
            services_plus_desc[index_service] += '|'
        elif 'Порт ВМ' in services_plus_desc[index_service]:
            services_plus_desc[index_service] += '|'
        elif 'HotSpot' in services_plus_desc[index_service]:
            services_plus_desc[index_service] += '|'
            regex_hotspot_point = ['(\d+)станц', '(\d+) станц', '(\d+) точ', '(\d+)точ', '(\d+)антен', '(\d+) антен']
            for regex in regex_hotspot_point:
                match_hotspot_point = re.search(regex, services_plus_desc[index_service])
                if match_hotspot_point:
                    hotspot_points = match_hotspot_point.group(1)
                    break

    counter_line_services = 0
    for i in services_plus_desc:
        while i.endswith('|'):
            counter_line_services += 1
            i = i[:-1]
    return counter_line_services, hotspot_points

def _tag_service_for_new_serv(services_plus_desc):
    tag_service = []
    hotspot_users = None
    premium_plus = None
    for index_service in range(len(services_plus_desc)):
        if 'Телефон' in services_plus_desc[index_service]:
            tag_service.append({'phone': services_plus_desc[index_service]})
        elif 'iTV' in services_plus_desc[index_service]:
            tag_service.append({'itv': services_plus_desc[index_service]})
        elif 'Интернет, DHCP' in services_plus_desc[index_service] or 'Интернет, блок Адресов Сети Интернет' in \
                services_plus_desc[index_service]:
            tag_service.append({'shpd': services_plus_desc[index_service]})
        elif 'ЦКС' in services_plus_desc[index_service]:
            tag_service.append({'cks': services_plus_desc[index_service]})
        elif 'Порт ВЛС' in services_plus_desc[index_service]:
            tag_service.append({'portvk': services_plus_desc[index_service]})
        elif 'Порт ВМ' in services_plus_desc[index_service]:
            tag_service.append({'portvm': services_plus_desc[index_service]})
        elif 'Видеонаблюдение' in services_plus_desc[index_service]:
            tag_service.append({'video': services_plus_desc[index_service]})
        elif 'HotSpot' in services_plus_desc[index_service]:
            if 'премиум +' in services_plus_desc[index_service].lower() or 'премиум+' in services_plus_desc[index_service].lower():
                premium_plus = True
            else:
                premium_plus = False

            regex_hotspot_users = ['(\d+)посетит', '(\d+) посетит', '(\d+) польз', '(\d+)польз', '(\d+)чел',
                                   '(\d+) чел']
            for regex in regex_hotspot_users:
                match_hotspot_users = re.search(regex, services_plus_desc[index_service])
                if match_hotspot_users:
                    hotspot_users = match_hotspot_users.group(1)
                    break
            tag_service.append({'hotspot': services_plus_desc[index_service]})
        elif 'ЛВС' in services_plus_desc[index_service]:
            tag_service.append({'local': services_plus_desc[index_service]})

    return tag_service, hotspot_users, premium_plus


def parse_tr(login, password, url):
    # Получение данных со страницы Тех решения
    #url = input('Ссылка на Тех.решение: ')
    url = url.replace('dem_begin', 'dem_point')
    req = requests.get(url, verify=False, auth=HTTPBasicAuth(login, password))
    if req.status_code == 200:
        parsed = req.content.decode('utf-8')

        # Получение данных среды передачи с блока "ОТПМ"
        sreda = None
        regex_env = 'Время на реализацию, дней</td>\r\n<td colspan="2">\d</td>\r\n</tr>\r\n\r\n\r\n\r\n\r\n\r\n<tr av_req="1">\r\n<td colspan="3" align="left">\r\n(.+)</td>\r\n</tr>\r\n\r\n\r\n\r\n<tr obt_req'
        match_env = re.search(regex_env, parsed, flags=re.DOTALL)
        try:
            oattr = match_env.group(1)
            oattr = oattr.replace('<br />', '').replace('&quot;', '"').replace('&amp;', '&')
            if ((not 'ОК' in oattr) and ('БС ' in oattr)) or (
                    (not 'ОК' in oattr) and ('радио' in oattr)) or (
                    (not 'ОК' in oattr) and ('радиоканал' in oattr)) or ((not 'ОК' in oattr) and ('антенну' in oattr)):
                sreda = '3'
                print('Среда передачи:  Беспроводная среда')
            elif ('Alpha' in oattr) or (('ОК-1' in oattr) and (not 'ОК-16' in oattr)):
                sreda = '4'
                print('Среда передачи: FTTH')
            elif ('ОВ' in oattr) or ('ОК' in oattr) or ('ВОЛС' in oattr) or ('волокно' in oattr) or (
                    'ОР ' in oattr) or ('ОР№' in oattr) or ('сущ.ОМ' in oattr) or ('оптическ' in oattr):
                sreda = '2'
                print('Среда передачи: ВОЛС')
            else:
                sreda = '1'
                print('Среда передачи: UTP')
        except AttributeError:
            sreda = '1'
            oattr = None
            print('Среда передачи: UTP')

        # Получение данных с блока "Перечень требуемых услуг"
        services_plus_desc = []
        services = []
        hotspot_points = None
        regex_serv = "Service_ID_\d+\'\>\r\n(?:\t)+<TD>(.+)</TD>\r\n(?:\t)+<TD>(.+)</TD>"  # "услуга" - group(1) и "описание" - group(2)
        for service in re.finditer(regex_serv, parsed):
            if service.group(1) in ['Сопровождение ИС', 'Другое']:
                pass
            # проверка на наличие в списке услуг нескольких строк с одной услугой
            elif service.group(1) in services and service.group(1) in ['Телефон', 'ЛВС', 'HotSpot', 'Видеонаблюдение']:
                for i in range(len(services_plus_desc)):
                    if service.group(1) in services_plus_desc[i]:
                        services_plus_desc[i] += ' {}'.format(service.group(2))
            else:
                one_service_plus_des = ' '.join(service.groups())
                services.append(service.group(1))
                services_plus_desc.append(one_service_plus_des)

        for i in range(len(services_plus_desc)):
            services_plus_desc[i] = services_plus_desc[i].replace('&quot;', '"')
            print('Услуга:  {}'.format(
                services_plus_desc[i]))



        # проходим по списку услуг чтобы определить количество организуемых линий от СПД и в той услуге, где требуется
        # добавляем спец. символ
        counter_line_services, hotspot_points = _counter_line_services(services_plus_desc)


        pps = None
        turnoff = None

        #if counter_line_services > 0:
        # Получение данных с блока "Узел подключения клиента"
        # Разделение сделано, т.к. для обычного ТР и упрощенки разный regex
        match_AB = None
        regex_AB = 'Изменить</span></div>\r\n</td>\r\n<td colspan="2">\r\n\t(.+) &'
        match_AB = re.search(regex_AB, parsed)
        if match_AB is None:
            regex_AB = 'Изменить</a></div>\r\n</td>\r\n<td colspan="2">\r\n\t(.+) &'
            match_AB = re.search(regex_AB, parsed)
            if match_AB is None:
                pps = 'Не выбран'
            else:
                pps = match_AB.group(1)
                pps = pps.replace('&quot;', '"')
        else:
            pps = match_AB.group(1)
            pps = pps.replace('&quot;', '"')


        # print(pps)

        # Получение данных с блока "Отключение"
        match_turnoff = None
        regex_turnoff = 'INPUT  disabled=\'disabled\' id=\'trTurnOff'
        match_turnoff = re.search(regex_turnoff, parsed)
        if match_turnoff is None:
            turnoff = True
            print('Отключение:  Внимание! Требуется отключение')
        else:
            turnoff = False
            print('Отключение:  Отключение не требуется')



        tochka = []
        regex_tochka = 'dID=(\d+)&tID=(\d+)&trID'
        match_tochka = re.search(regex_tochka, parsed)
        id1 = match_tochka.group(1)
        id2 = match_tochka.group(2)
        tochka.append(id1)
        tochka.append(id2)

        url = 'https://sss.corp.itmh.ru/dem_tr/dem_point_panel.php?dID={}&tID={}'.format(id1, id2)
        req = requests.get(url, verify=False, auth=HTTPBasicAuth(login, password))
        parsed = req.content.decode('utf-8')
        regex_address = "\({},{}\)'>&nbsp;(.+?)&nbsp;</a>".format(id1, id2)
        match_address = re.search(regex_address, parsed)
        address = match_address.group(1)
        address = address.replace(', д.', ' ')


        url = 'https://sss.corp.itmh.ru/dem_tr/dem_adv.php?dID={}'.format(id1)
        req = requests.get(url, verify=False, auth=HTTPBasicAuth(login, password))
        parsed = req.content.decode('utf-8')
        regex_client = 'Клиент\r\n            </td>\r\n            <td colspan="3">\r\n(.+)</td>'
        match_client = re.search(regex_client, parsed)
        client = match_client.group(1)
        client = ' '.join(client.split())
        client = client.replace('&quot;', '"')
        print(client)
        regex_manager = 'Менеджер клиента            </td>\r\n            <td align="left" colspan="3">\r\n(.+)</td>'
        match_manager = re.search(regex_manager, parsed)
        try:
            manager = match_manager.group(1)
            manager = ' '.join(manager.split())
            print(manager)
        except AttributeError:
            manager = None
        regex_technolog = 'Технологи\r\n            </td>\r\n            <td align="left" colspan="3">\r\n(.+)</td>'
        match_technolog = re.search(regex_technolog, parsed)
        technolog = match_technolog.group(1)
        technolog = ' '.join(technolog.split())
        print(technolog)

        regex_task_otpm = 'Задача в ОТПМ\r\n(?:\s+)</td>\r\n(?:\s+)<td colspan="3" valign="top">(.+)</td>'
        match_task_otpm = re.search(regex_task_otpm, parsed, flags=re.DOTALL)
        task_otpm = match_task_otpm.group(1)
        task_otpm = task_otpm[:task_otpm.find('</td>')]
        task_otpm = ' '.join(task_otpm.split())
        print(task_otpm)

        data_sss = []
        data_sss.append(services_plus_desc)
        data_sss.append(counter_line_services)
        data_sss.append(pps)
        data_sss.append(turnoff)
        data_sss.append(sreda)
        data_sss.append(tochka)
        data_sss.append(hotspot_points)
        data_sss.append(oattr)
        data_sss.append(address)
        data_sss.append(client)
        data_sss.append(manager)
        data_sss.append(technolog)
        data_sss.append(task_otpm)

        return data_sss
    else:
        data_sss = []
        data_sss.append('Access denied')
        return data_sss


def parsingByNodename(node_name, login, password):

    #Получение страницы с данными о коммутаторе
    url = 'https://cis.corp.itmh.ru/stu/NetSwitch/SearchNetSwitchProxy'
    data = {'IncludeDeleted': 'false', 'IncludeDisabled': 'true', 'HideFilterPane': 'false'}
    data['NodeName'] = node_name.encode('utf-8')
    req = requests.post(url, verify=False, auth=HTTPBasicAuth(login, password), data=data)
    print('!!!!!')
    print('req.status_code')
    print(req.status_code)
    if req.status_code == 200:
        switch = req.content.decode('utf-8')
        if 'No records to display.' in switch:
            list_switches = []
            list_switches.append('No records to display {}'.format(node_name))
            return list_switches
        else:
            # Получение данных о названии и модели всех устройств на узле связи
            regex_name_model = '\"netswitch-name\\\\\" >\\\\r\\\\n\s+?(\S+?[ekb|ntg|kur])\\\\r\\\\n\s+?</a>\\\\r\\\\n\s+?\\\\r\\\\n</td><td>(.+?)</td><td>\\\\r\\\\n\s+?<a href=\\\\\"/stu/Node'
            match_name_model = re.findall(regex_name_model, switch)


            # Выявление индексов устройств с признаком SW и CSW
            clear_name_model = []
            clear_index = []
            for i in range(len(match_name_model)):
                if match_name_model[i][0][:3] == 'CSW' or match_name_model[i][0][:2] == 'SW':
                    clear_index.append(i)
                    clear_name_model.append(match_name_model[i])


            # в regex добавлены знаки ?, чтобы отключить жадность. в выводе match список кортежей

            # Получение данных об узле КАД
            regex_node = 'netswitch-nodeName\\\\\">\\\\r\\\\n\s+(.+?[АВ|КК|УА|РУА])\\\\r\\\\n '
            match_node = re.findall(regex_node, switch)
            # в regex добавлены знаки ?, чтобы отключить жадность. в выводе match список узлов - строк

            # Получение данных об ip-адресе КАД
            regex_ip = '\"telnet://([0-9.]+)\\\\'
            match_ip = re.findall(regex_ip, switch)
            clear_ip = []
            for i in clear_index:
                clear_ip.append(match_ip[i])

            # в выводе match список ip - строк

            # Получение данных о магистральном порте КАД
            regex_uplink = 'uplinks-count=\\\\\"\d+\\\\\">\\\\r\\\\n(?:\\\\t)+ (.+?)\\\\r\\\\n(?:\\\\t)+ </span>'
            match_uplink = re.findall(regex_uplink, switch)
            clear_uplink = []
            for i in clear_index:
                clear_uplink.append(match_uplink[i])

            regex_status_desc = '(ВКЛ|ВЫКЛ)</td><td>(.+?)</td>'
            match_status_desc = re.findall(regex_status_desc, switch)
            clear_status_desc = []
            for i in clear_index:
                clear_status_desc.append(match_status_desc[i])


            # в выводе match список uplink - строк

            # Получение данных об id КАД для формирования ссылки на страницу портов КАД
            regex_switch_id = 'span class=\\\\\"netSwitchPorts\\\\\" switch-id=\\\\\"(\d+)\\\\'
            match_switch_id = re.findall(regex_switch_id, switch)
            list_ports = []
            clear_switch_id = []

            configport_switches = []

            for i in clear_index:
                clear_switch_id.append(match_switch_id[i])
            print('!!!!clear_switch_id')
            print(clear_switch_id)
            for i in clear_switch_id:
                ports = {}

                url_switch_id = 'https://cis.corp.itmh.ru/stu/Switch/Details/' + i
                req_switch_id = requests.get(url_switch_id, verify=False, auth=HTTPBasicAuth(login, password))
                switch_id = req_switch_id.content.decode('utf-8')

                regex_total_ports = 'for=\"TotalPorts\">(\d+)<'
                match_total_ports = re.search(regex_total_ports, switch_id)
                ports['Всего портов'] = match_total_ports.group(1)

                #regex_broken_ports = 'for=\"BrokenPorts\">(\d+)<'
                #match_broken_ports = re.search(regex_broken_ports, switch_id)
                #ports['Неисправных'] = match_broken_ports.group(1)

                regex_client_ports = 'for=\"ClientCableUsedPorts\">(\d+)<'
                match_client_ports = re.search(regex_client_ports, switch_id)
                ports['Занятых клиентами'] = match_client_ports.group(1)

                regex_link_ports = 'for=\"LinkUsedPorts\">(\d+)<'
                match_link_ports = re.search(regex_link_ports, switch_id)
                ports['Занятых линками'] = match_link_ports.group(1)

                #regex_zombi_ports = 'for=\"ZombieContractPorts\">(\d+)<'
                #match_zombi_ports = re.search(regex_zombi_ports, switch_id)
                #ports['Зомби'] = match_zombi_ports.group(1)

                #regex_free_ports = 'for=\"FreePorts\">(\d+)<'
                #match_free_ports = re.search(regex_free_ports, switch_id)
                #ports['Свободные'] = match_free_ports.group(1)

                regex_avail_ports = 'for=\"AvailablePorts\">(\d+)<'
                match_avail_ports = re.search(regex_avail_ports, switch_id)
                ports['Доступные'] = match_avail_ports.group(1)
                list_ports.append(ports)


                configport_switch = {}
                for page in range(1, 4):
                    url_port_config = 'https://cis.corp.itmh.ru/stu/NetSwitch/PortConfigs?switchId=' + i + '&PortGonfigsGrid-page=' + str(
                        page)
                    req_port_config = requests.get(url_port_config, verify=False, auth=HTTPBasicAuth(login, password))
                    port_config = req_port_config.content.decode('utf-8')
                    regex_port_config = '<td>(.+)</td><td>(.+)</td><td>(.+)</td><td>(?:.*)</td><td style="text-align:left">'
                    match_port_config = re.finditer(regex_port_config, port_config)  # flags=re.DOTALL
                    for port in match_port_config:
                        configport_switch[port.group(2)] = [port.group(1), port.group(3)]
                configport_switches.append(configport_switch)



            list_switches = []
            #for i in range(len(clear_name_model)):
            for i in range(len(match_name_model)):
                print('!!!')
                print(i)
                if match_name_model[i] not in clear_name_model:
                    list_switches.append(
                        [match_name_model[i][0], match_name_model[i][1], match_ip[i], match_uplink[i],
                         match_status_desc[i][0], match_status_desc[i][1], '-', '-', '-', '-', '-'])

            for i in range(len(clear_name_model)):
                print('!!!')
                print(i)

                #list_switches.append([clear_name_model[i][0], clear_name_model[i][1], match_node[i], clear_ip[i], clear_uplink[i], list_ports[i]])
                list_switches.append(
                    [clear_name_model[i][0], clear_name_model[i][1], clear_ip[i], clear_uplink[i], clear_status_desc[i][0], clear_status_desc[i][1],
                     list_ports[i]['Всего портов'], list_ports[i]['Занятых клиентами'], list_ports[i]['Занятых линками'], list_ports[i]['Доступные'], configport_switches[i]])

            print('!!!!')
            print('list_switches')
            print(list_switches)
            return list_switches
    else:
        list_switches = []
        list_switches.append('Access denied')
        return list_switches







def ckb_parse(login, password):
    templates = {}
    url = 'https://ckb.itmh.ru/login.action?os_destination=%2Fpages%2Fviewpage.action%3FpageId%3D323312207&permissionViolation=true'
    req = requests.get(url, verify=False, auth=HTTPBasicAuth(login, password))
    soup = BeautifulSoup(req.content.decode('utf-8'), "html.parser")
    search = soup.find_all('pre', {'class': 'syntaxhighlighter-pre'})
    for item in search:
        regex = '(.+)'
        match = re.search(regex, item.text)
        title = match.group(1)
        templates[title] = item.text
    return templates

#@login_required(login_url='login/', redirect_field_name='next')
@cache_check
def ortr(request):
    """Данный метод перенаправляет на страницу Новые заявки, которые находятся в пуле ОРТР/в работе.
        1. Получает данные от redis о логин/пароле
        2. Получает данные о всех заявках в пуле ОРТР с помощью метода in_work_ortr
        3. Получает данные о всех заявках которые уже находятся в БД(в работе)
        4. Удаляет из списка в пуле заявки, которые есть в работе
        5. Формирует итоговый список всех заявок в пуле/в работе"""
    user = User.objects.get(username=request.user.username)
    credent = cache.get(user)
    username = credent['username']
    password = credent['password']
    request = flush_session_key(request)
    search = in_work_ortr(username, password)
    if search[0] == 'Access denied':
        messages.warning(request, 'Нет доступа в ИС Холдинга')
        response = redirect('login_for_service')
        response['Location'] += '?next={}'.format(request.path)
        return response

    else:
        list_search = []
        for i in search:
            list_search.append(i[0])
        print(list_search)
        spp_proc_wait = SPP.objects.filter(Q(process=True) | Q(wait=True))
        list_spp_proc_wait = []
        for i in spp_proc_wait:
            list_spp_proc_wait.append(i.ticket_k)
        print(list_spp_proc_wait)
        list_search_rem = []
        for i in list_spp_proc_wait:
            for index_j in range(len(list_search)):
                if i in list_search[index_j]:
                    list_search_rem.append(index_j)
        print(list_search_rem)
        search[:] = [x for i, x in enumerate(search) if i not in list_search_rem]
        spp_process = SPP.objects.filter(process=True)

        return render(request, 'tickets/ortr.html', {'search': search, 'spp_process':spp_process})


def primer_get_tr(request, ticket_tr, ticket_id):
    services_one_tr = []
    one_tr = TR.objects.get(ticket_tr=ticket_tr, id=ticket_id)
    for item in one_tr.servicestr_set.all():
        services_one_tr.append(item.service)
    data_one_tr = one_tr.datatr_set.get()
    ortr_one_tr = one_tr.ortrtr_set.first() #first вместо get, т.к. если записи нет, то будет исключение DoesNotExist
    context = {
        'one_tr': one_tr,
        'services_one_tr': services_one_tr,
        'data_one_tr': data_one_tr,
        'ortr_one_tr': ortr_one_tr
    }

    return render(request, 'tickets/tr.html', context=context)

from django.core.exceptions import ObjectDoesNotExist

@cache_check
def add_spp(request, dID):
    '''должна принимать параметром номер заявки, парсить и добавлять в базу заявку. Сможет работать отдельно от заявок
    в пуле ОРТР, просто вводим урл и номер заявки и она добавляется в бд. А кнопка взять в работу будет ссылкой на этот урл,
    но тогда не получится добавлять в базу время, когда заявка попала в пул(надо подумать учитывать это или нет)
    вызывает for_spp_view, for_tr_view'''
    user = User.objects.get(username=request.user.username)
    credent = cache.get(user)
    username = credent['username']
    password = credent['password']
    print('add_spp get username')
    print(username)
    print(password)
    try:
        current_spp = SPP.objects.filter(dID=dID).latest('created')
    except ObjectDoesNotExist:
        spp_params = for_spp_view(username, password, dID)
        print('!!!!spp_params')
        print(spp_params)
        if spp_params.get('Access denied') == 'Access denied':
            messages.warning(request, 'Нет доступа в ИС Холдинга')
            response = redirect('login_for_service')
            response['Location'] += '?next={}'.format(request.path)
            return response
        else:
            #exist_dID = len(SPP.objects.filter(dID=dID))
            #if exist_dID:
            #    version = exist_dID + 1
            #else:
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

            user = User.objects.get(username=request.user.username)
            ticket_spp.user = user
            ticket_spp.save()
            # request.session['ticket_spp_id'] = ticket_spp.id
            return redirect('spp_view_save', dID, ticket_spp.id)

    else:
        if current_spp.process == True:
            messages.warning(request, '{} уже взял в работу'.format(current_spp.user.last_name))
            return redirect('ortr')

        else:
            spp_params = for_spp_view(username, password, dID)
            if spp_params.get('Access denied') == 'Access denied':
                messages.warning(request, 'Нет доступа в ИС Холдинга')
                response = redirect('login_for_service')
                response['Location'] += '?next={}'.format(request.path)
                return response
            else:
                exist_dID = len(SPP.objects.filter(dID=dID))
                #if exist_dID:
                version = exist_dID + 1
                #else:
                #    version = 1

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

                user = User.objects.get(username=request.user.username)
                ticket_spp.user = user
                ticket_spp.save()
                #request.session['ticket_spp_id'] = ticket_spp.id
                return redirect('spp_view_save', dID, ticket_spp.id)

def remove_spp_process(request, ticket_spp_id):
    current_ticket_spp = SPP.objects.get(id=ticket_spp_id)
    current_ticket_spp.process = False
    current_ticket_spp.save()
    messages.success(request, 'Работа по заявке {} завершена'.format(current_ticket_spp.ticket_k))
    return redirect('ortr')


def remove_spp_wait(request, ticket_spp_id):
    current_ticket_spp = SPP.objects.get(id=ticket_spp_id)
    current_ticket_spp.wait = False
    #current_ticket_spp. = False
    current_ticket_spp.save()
    messages.success(request, 'Заявка {} возвращена из ожидания'.format(current_ticket_spp.ticket_k))
    return redirect('ortr')

def add_spp_wait(request, ticket_spp_id):
    current_ticket_spp = SPP.objects.get(id=ticket_spp_id)
    current_ticket_spp.wait = True
    current_ticket_spp.was_waiting = True
    current_ticket_spp.process = False
    current_ticket_spp.save()
    messages.success(request, 'Заявка {} перемещена в ожидание'.format(current_ticket_spp.ticket_k))
    return redirect('wait')


def spp_view_save(request, dID, ticket_spp_id):
    request.session['ticket_spp_id'] = ticket_spp_id
    request.session['dID'] = dID
    current_ticket_spp = get_object_or_404(SPP, dID=dID, id=ticket_spp_id)
    return render(request, 'tickets/spp_view_save.html', {'current_ticket_spp': current_ticket_spp})

@cache_check
def spp_view(request, dID):
    user = User.objects.get(username=request.user.username)
    credent = cache.get(user)
    username = credent['username']
    password = credent['password']
    spp_params = for_spp_view(username, password, dID)
    if spp_params.get('Access denied') == 'Access denied':
        messages.warning(request, 'Нет доступа в ИС Холдинга')
        response = redirect('login_for_service')
        response['Location'] += '?next={}'.format(request.path)
        return response
    else:
        return render(request, 'tickets/spp_view.html', {'spp_params': spp_params})

def for_spp_view(login, password, dID):
    spp_params = {}
    sostav = []
    url = 'https://sss.corp.itmh.ru/dem_tr/dem_adv.php?dID={}'.format(dID)
    req = requests.get(url, verify=False, auth=HTTPBasicAuth(login, password))
    if req.status_code == 200:
        soup = BeautifulSoup(req.content.decode('utf-8'), "html.parser")
        search = soup.find_all('tr')
        for i in search:
            if 'Заказчик' in i.find_all('td')[0].text:
                customer = ''.join(i.find_all('td')[1].text.split())
                print('!!!!customer')
                print(customer)
                if 'Проектно-технологическийотдел' in customer or 'ОТПМ' in customer:
                    spp_params['Тип заявки'] = 'ПТО'
                else:
                    spp_params['Тип заявки'] = 'Коммерческая'
            elif 'Заявка К' in i.find_all('td')[0].text:
                spp_params['Заявка К'] = ''.join(i.find_all('td')[1].text.split())
            elif 'Менеджер клиента' in i.find_all('td')[0].text:
                spp_params['Менеджер'] = i.find_all('td')[1].text.strip()
            elif 'Клиент' in i.find_all('td')[0].text:
                spp_params['Клиент'] = i.find_all('td')[1].text.strip()
            elif 'Разработка схем/карт' in i.find_all('td')[0].text:
                spp_params['Менеджер'] = i.find_all('td')[1].text.strip()
            elif 'Технологи' in i.find_all('td')[0].text:
                spp_params['Технолог'] = i.find_all('td')[1].text.strip()
            elif 'Задача в ОТПМ' in i.find_all('td')[0].text:
                spp_params['Задача в ОТПМ'] = i.find_all('td')[1].text.strip()
            elif 'ТР по упрощенной схеме' in i.find_all('td')[0].text:
                spp_params['ТР по упрощенной схеме'] = i.find_all('td')[1].text
            elif 'Перечень' in i.find_all('td')[0].text:
                services = i.find_all('td')[1].text
                services = services[::-1]
                services = services[:services.index('еинасипО')]
                services = services[::-1]
                services = services.split('\n\n')
                services.pop(0)
                spp_params['Перечень требуемых услуг'] = services
            elif 'Состав Заявки ТР' in i.find_all('td')[0].text:
                for links in i.find_all('td')[1].find_all('a'):
                    all_link = {}
                    if 'trID' in links.get('href'):
                        regex = 'tID=(\d+)&trID=(\d+)'
                        match_href = re.search(regex, links.get('href'))
                        total_link = [match_href.group(1), match_href.group(2)]
                    else:
                        total_link = None
                    all_link[links.text] = total_link
                    sostav.append(all_link)
                spp_params['Состав Заявки ТР'] = sostav
            elif 'Примечание' in i.find_all('td')[0].text:
                spp_params['Примечание'] = i.find_all('td')[1].text.strip()
        return spp_params
    else:
        spp_params['Access denied'] = 'Access denied'
        return spp_params




#@login_required(login_url='tickets/login/')
@cache_check
def add_tr(request, dID, tID, trID):
    user = User.objects.get(username=request.user.username)
    credent = cache.get(user)
    username = credent['username']
    password = credent['password']
    tr_params = for_tr_view(username, password, dID, tID, trID)
    print('!!!!!tr_params')
    print(tr_params)
    if tr_params.get('Access denied') == 'Access denied':
        messages.warning(request, 'Нет доступа в ИС Холдинга')
        response = redirect('login_for_service')
        response['Location'] += '?next={}'.format(request.path)
        return response
    else:
        ticket_spp_id = request.session['ticket_spp_id']

        ticket_spp = SPP.objects.get(dID=dID, id=ticket_spp_id)

        if ticket_spp.children.filter(ticket_tr=trID):
            ticket_tr = ticket_spp.children.filter(ticket_tr=trID)[0]
        else:
            ticket_tr = TR()

        ticket_tr.ticket_k = ticket_spp
        ticket_tr.ticket_tr = trID
        ticket_tr.pps = tr_params['Узел подключения клиента']
        ticket_tr.turnoff = False if tr_params['Отключение'] == 'Нет' else True
        ticket_tr.info_tr = tr_params['Информация для разработки ТР']
        ticket_tr.services = tr_params['Перечень требуемых услуг']
        ticket_tr.oattr = tr_params['Решение ОТПМ']
        #ticket_tr.tr_OTO_Pay = tr_params['tr_OTO_Pay']
        #ticket_tr.tr_OTS_Pay = tr_params['tr_OTS_Pay']
        #ticket_tr.trOTMPType = tr_params['trOTMPType']
        #ticket_tr.trArticle = tr_params['trArticle']
        ticket_tr.vID = tr_params['vID']
        ticket_tr.save()
        request.session['ticket_tr_id'] = ticket_tr.id
        print(request.GET)

        return redirect('project_tr', dID, tID, trID)

def add_tr_to_db(dID, trID, tr_params, ticket_spp_id):
    """Данный метод получает ID заявки СПП, ID ТР, параметры полученные с распарсенной страницы ТР, ID заявки СПП в АРМ.
    создает заявку ТР в АРМ и добавляет в нее данные. Возвращает ID ТР в АРМ"""
    ticket_spp = SPP.objects.get(dID=dID, id=ticket_spp_id)

    if ticket_spp.children.filter(ticket_tr=trID):
        ticket_tr = ticket_spp.children.filter(ticket_tr=trID)[0]
    else:
        ticket_tr = TR()

    ticket_tr.ticket_k = ticket_spp
    ticket_tr.ticket_tr = trID
    ticket_tr.pps = tr_params['Узел подключения клиента']
    ticket_tr.turnoff = False if tr_params['Отключение'] == 'Нет' else True
    ticket_tr.info_tr = tr_params['Информация для разработки ТР']
    ticket_tr.services = tr_params['Перечень требуемых услуг']
    ticket_tr.oattr = tr_params['Решение ОТПМ']
    ticket_tr.vID = tr_params['vID']
    ticket_tr.save()
    ticket_tr_id = ticket_tr.id
    return ticket_tr_id




def tr_view_save(request, dID, ticket_spp_id, trID):
    #request.session['ticket_spp_id'] = ticket_spp_id
    #request.session['dID'] = dID
    #current_ticket_spp = SPP.objects.get(dID=dID, id=ticket_spp_id)

    #current_ticket_tr = TR.objects.get(ticket_tr=ticket_tr, ticket_k__id=ticket_spp_id)

    #ticket_spp_id = request.session['ticket_spp_id']
    #dID = request.session['dID']
    ticket_spp = SPP.objects.get(dID=dID, id=ticket_spp_id)

    # if ticket_spp.children.filter(ticket_tr=trID):


    #get_object_or_404 не используется т.к. 'RelatedManager' object has no attribute 'get_object_or_404'
    try:
        ticket_tr = ticket_spp.children.get(ticket_tr=trID)
    except TR.DoesNotExist:
        raise Http404("ТР не создавалось")

    try:
        ortr = ticket_tr.ortrtr_set.all()[0]
    except IndexError:
        raise Http404("Блока ОРТР нет")

    #request.session['ticket_tr_id'] = ticket_tr.id

    # if ticket_tr.ortrtr_set.all():

    #request.session['ortr_id'] = ortr.id

    #counter_str_ortr = ortr.ortr.count('\n')
    #if ortr.ots:
    #    counter_str_ots = ortr.ots.count('\n')
    #else:
        #counter_str_ots = 1


    return render(request, 'tickets/tr_view_save.html', {'ticket_tr': ticket_tr, 'ortr': ortr})


@cache_check
def tr_view(request, dID, tID, trID):
    user = User.objects.get(username=request.user.username)
    credent = cache.get(user)
    username = credent['username']
    password = credent['password']
    ticket_tr = for_tr_view(username, password, dID, tID, trID)
    if ticket_tr.get('Access denied') == 'Access denied':
        messages.warning(request, 'Нет доступа в ИС Холдинга')
        response = redirect('login_for_service')
        response['Location'] += '?next={}'.format(request.path)
        return response
    else:
        return render(request, 'tickets/tr_view.html', {'ticket_tr': ticket_tr})


def for_tr_view(login, password, dID, tID, trID): #login, password
    spp_params = {}
    all_link = {}
    url = 'https://sss.corp.itmh.ru/dem_tr/dem_point.php?dID={}&tID={}&trID={}'.format(dID, tID, trID)
    req = requests.get(url, verify=False, auth=HTTPBasicAuth(login, password))
    if req.status_code == 200:
        soup = BeautifulSoup(req.content.decode('utf-8'), "html.parser")
        search = soup.find_all('tr')

        for index, i in enumerate(search):
            if 'Перечень' in i.find_all('td')[0].text:
                total_services = []
                leng_services = i.find_all('td')[1].find_all('tr')
                for service_index in range(1, len(i.find_all('td')[1].find_all('tr'))-1):
                    services = i.find_all('td')[1].find_all('tr')[service_index].find_all('td')
                    var_list = []
                    for k in services:
                        var_list.append(k.text)
                    service = ' '.join(var_list)
                    total_services.append(service)

                spp_params['Перечень требуемых услуг'] = total_services
            elif 'Информация для' in i.find_all('td')[0].text:
                spp_params['Информация для разработки ТР'] = i.find_all('td')[1].text
            elif 'Узел подключения клиента' in i.find_all('td')[0].text:
                #print('!!!!!УЗел')

                node = re.search(r'\t(.+)\s+Статус', i.find_all('td')[1].text)

                #print(node.group(1))
                if 'Изменить' in i.find_all('td')[0].text:
                    spp_params['Узел подключения клиента'] = node.group(1)
                else:
                    #node = i.find_all('td')[0].find('a').get('href')
                    #match_node = re.search(r'(\d+), (\d+)', node)
                    #node_href = match_node.groups()
                    #spp_params['Узел подключения клиента'] = 'https://sss.corp.itmh.ru/building/address_begin.php?mode=selectAV&aID={}&parent={}'.format(*node_href)
                    spp_params['Узел подключения клиента'] = url
            elif 'Отключение' in i.find_all('td')[0].text and len(i.find_all('td')) > 1:
                try:
                    checked = i.find_all('td')[1].find('input')['checked']
                except KeyError:
                    spp_params[i.find_all('td')[0].text] = 'Нет'
                else:
                    spp_params[i.find_all('td')[0].text] = 'Требуется отключение'

            elif 'Тип / кат' in i.find_all('td')[0].text:
                file = {}
                files = i.find_all('td')[0].find_all('a')
                print('!!!Отклю')
                for item in range(len(files)):
                    if 'javascript' not in files[item].get('href'):
                        file[files[item].text] = files[item].get('href')
                        print(files[item].get('href'))
                        print(files[item].text)


                #elif 'Состав Заявки ТР' in i.find_all('td')[0].text:
                #for links in i.find_all('td')[1].find_all('a'):
                #    if 'trID' in links.get('href'):
                #        regex = 'tID=(\d+)&trID=(\d+)'
                #        match_href = re.search(regex, links.get('href'))
                #        total_link = [match_href.group(1), match_href.group(2)]
                #    else:
                #        total_link = None
                #    all_link[links.text] = total_link
                #spp_params['Состав Заявки ТР'] = all_link



            elif 'Время на реализацию, дней' in i.find_all('td')[0].text:
                spp_params['Решение ОТПМ'] = search[index+1].find('td').text.strip()
                #spp_params['Решение ОТПМ'] = spp_params['Решение ОТПМ'].replace('\r\n', '<br />').replace('\n', '<br />')
                #spp_params['Решение ОТПМ'] = spp_params['Решение ОТПМ']
            '''elif 'Стоимость доп. Оборудования' in i.find_all('td')[0].text and i.find_all('td')[1].find('input'):
                if i.find_all('td')[1].find('input')['name'] == 'tr_OTO_Pay':
                    spp_params[i.find_all('td')[1].find('input')['name']] = i.find_all('td')[1].find('input')['value']
                if i.find_all('td')[1].find('input')['name'] == 'tr_OTS_Pay':
                    spp_params[i.find_all('td')[1].find('input')['name']] = i.find_all('td')[1].find('input')['value']
            elif 'Тип ТР' in i.find_all('td')[0].text:
                for option in i.find_all('td')[1].find('select').find_all('option'):
                    try:
                        selected_option = option['selected']
                    except KeyError:
                        selected_option = None
                    else:
                        spp_params['trOTMPType'] = option['value']
                spp_params.setdefault('trOTMPType', 0)
            elif 'Статья затрат' in i.find_all('td')[0].text:
                for option in i.find_all('td')[1].find('select').find_all('option'):
                    try:
                        selected_option = option['selected']
                    except KeyError:
                        selected_option = None
                    else:
                        spp_params['trArticle'] = option['value']
                spp_params.setdefault('trArticle', 0)'''
        if spp_params['Отключение'] == 'Требуется отключение':
            spp_params['Отключение'] = file
        search2 = soup.find_all('form')
        form_data = search2[1].find_all('input')
        for i in form_data:
            if i.attrs['type'] == 'hidden':
                if i['name'] == 'vID':
                    spp_params[i['name']] = i['value']
        return spp_params
    else:
        spp_params['Access denied'] = 'Access denied'
        return spp_params


def in_work_ortr(login, password):
    lines = []
    url = 'https://sss.corp.itmh.ru/dem_tr/demands.php?tech_uID=0&trStatus=inWorkORTR&curator=any&vName=&dSearch=&bID=1&searchType=param'
    req = requests.get(url, verify=False, auth=HTTPBasicAuth(login, password))
    if req.status_code == 200:
        soup = BeautifulSoup(req.content.decode('utf-8'), "html.parser")
        search_demand_num2 = soup.find_all('td', class_='demand_num2')
        search_demand_cust = soup.find_all('td', class_='demand_cust')
        search_demand_point = soup.find_all('td', class_='demand_point')
        search_demand_tech = soup.find_all('td', class_='demand_tech')
        search_demand_cur = soup.find_all('td', class_='demand_cur')
        #search_demand_stat = soup.find_all('td', class_='demand_stat')

        for index in range(len(search_demand_num2)-1):
            if search_demand_cur[index].text in ['Бражкин П.В.', 'Короткова И.В.', 'Полейко А.Л.', 'Полейко А. Л.', 'Гумеров Р.Т.']:
                pass
            else:

                lines.append([search_demand_num2[index].text, search_demand_num2[index].find('a').get('href')[(search_demand_num2[index].find('a').get('href').index('=')+1):], search_demand_cust[index].text, search_demand_point[index].text,
                          search_demand_tech[index].text, search_demand_cur[index].text]) #search_demand_stat[index].text
        for index in range(len(lines)):
            if 'ПТО' in lines[index][0]:
                lines[index][0] = lines[index][0][:lines[index][0].index('ПТО')]+' '+lines[index][0][lines[index][0].index('ПТО'):]
            for symbol_index in range(1, len(lines[index][3])):
                if lines[index][3][symbol_index].isupper() and lines[index][3][symbol_index-1].islower():
                    lines[index][3] = lines[index][3][:symbol_index]+' '+lines[index][3][symbol_index:]
                    break
    else:
        lines.append('Access denied')
    return lines


def _new_services(result_services, value_vars):
    result_services_ots = None
    logic_csw = value_vars.get('logic_csw')
    services_plus_desc = value_vars.get('services_plus_desc')
    templates = value_vars.get('templates')
    sreda = value_vars.get('sreda')
    for service in services_plus_desc:
        if 'Интернет, DHCP' in service:
            print('{}'.format(service.replace('|', ' ')) + '-' * 20)
            if logic_csw == True:
                result_services.append(enviroment_csw(value_vars))
            else:
                pass
            static_vars = {}
            hidden_vars = {}
            stroka = templates.get("Организация услуги ШПД в интернет access'ом.")
            static_vars['указать маску'] = '/32'
            result_services.append(analyzer_vars(stroka, static_vars, hidden_vars))

            if value_vars.get('router_shpd') == True:
                stroka = templates.get("Установка маршрутизатора")
                if sreda == '2' or sreda == '4':
                    static_vars['ОИПМ/ОИПД'] = 'ОИПМ'
                else:
                    static_vars['ОИПМ/ОИПД'] = 'ОИПД'
                result_services.append(analyzer_vars(stroka, static_vars, hidden_vars))

        elif 'Интернет, блок Адресов Сети Интернет' in service:
            print('{}'.format(service.replace('|', ' ')) + '-' * 20)
            if logic_csw == True:
                result_services.append(enviroment_csw(value_vars))
            else:
                pass
            static_vars = {}
            hidden_vars = {}
            if ('29' in service) or (' 8' in service):
                static_vars['указать маску'] = '/29'
            elif ('28' in service) or ('16' in service):
                static_vars['указать маску'] = '/28'
            else:
                static_vars['указать маску'] = '/30'
            if value_vars.get('type_shpd') == 'access':
                stroka = templates.get("Организация услуги ШПД в интернет access'ом.")
                result_services.append(analyzer_vars(stroka, static_vars, hidden_vars))
            elif value_vars.get('type_shpd') == 'trunk':
                stroka = templates.get("Организация услуги ШПД в интернет trunk'ом.")
                result_services.append(analyzer_vars(stroka, static_vars, hidden_vars))

            if value_vars.get('router_shpd') == True:
                stroka = templates.get("Установка маршрутизатора")
                if sreda == '2' or sreda == '4':
                    static_vars['ОИПМ/ОИПД'] = 'ОИПМ'
                else:
                    static_vars['ОИПМ/ОИПД'] = 'ОИПД'
                result_services.append(analyzer_vars(stroka, static_vars, hidden_vars))

        elif 'iTV' in service:
            type_itv = value_vars.get('type_itv')
            cnt_itv = value_vars.get('cnt_itv')
            print('{}'.format(service.replace('|', ' ')) + '-' * 20)
            if logic_csw == True and type_itv == 'vl':
                for i in range(int(cnt_itv)):
                    result_services.append(enviroment_csw(value_vars))
            static_vars = {}
            hidden_vars = {}

            if type_itv == 'vl':
                if cnt_itv == 1:
                    static_vars['маска'] = '/30'
                elif 1 < cnt_itv < 6:
                    static_vars['маска'] = '/29'
                stroka = templates.get("Организация услуги Вебург.ТВ в отдельном vlan'е")
                result_services.append(analyzer_vars(stroka, static_vars, hidden_vars))
            elif type_itv == 'novl':
                for serv_inet in services_plus_desc:
                    if 'Интернет, блок Адресов Сети Интернет' in serv_inet:
                        stroka = templates.get("Организация услуги Вебург.ТВ в vlan'е новой услуги ШПД в интернет")
                        result_services.append(analyzer_vars(stroka, static_vars, hidden_vars))


        elif 'ЦКС' in service:
            print('{}'.format(service.replace('|', ' ')) + '-' * 20)
            if logic_csw == True:
                result_services.append(enviroment_csw(value_vars))

            static_vars = {}
            hidden_vars = {}
            all_cks_in_tr = value_vars.get('all_cks_in_tr')
            if all_cks_in_tr.get(service):
                static_vars['указать точку "A"'] = all_cks_in_tr.get(service)['pointA']
                static_vars['указать точку "B"'] = all_cks_in_tr.get(service)['pointB']
                static_vars['полисером Subinterface/портом подключения'] = all_cks_in_tr.get(service)['policer_cks']
                static_vars['указать полосу'] = _get_policer(service)
                #if '1000' in service:
                #    static_vars['указать полосу'] = '1 Гбит/с'
                #elif '100' in service:
                #    static_vars['указать полосу'] = '100 Мбит/с'
                #lif '10' in service:
                #   static_vars['указать полосу'] = '10 Мбит/с'
                #lif '1' in service:
                #   static_vars['указать полосу'] = '1 Гбит/с'
                #lse:
                #    static_vars['указать полосу'] = 'Неизвестная полоса'

                if all_cks_in_tr.get(service)['type_cks'] == 'access':
                    stroka = templates.get("Организация услуги ЦКС Etherline access'ом.")
                    result_services.append(analyzer_vars(stroka, static_vars, hidden_vars))
                elif all_cks_in_tr.get(service)['type_cks'] == 'trunk':
                    stroka = templates.get("Организация услуги ЦКС Etherline trunk'ом.")
                    result_services.append(analyzer_vars(stroka, static_vars, hidden_vars))


        elif 'Порт ВЛС' in service:
            print('{}'.format(service.replace('|', ' ')) + '-' * 20)
            if logic_csw == True:
                result_services.append(enviroment_csw(value_vars))
            else:
                pass
            static_vars = {}
            hidden_vars = {}
            all_portvk_in_tr = value_vars.get('all_portvk_in_tr')
            if all_portvk_in_tr.get(service):
                if all_portvk_in_tr.get(service)['new_vk'] == True:
                    stroka = templates.get("Организация услуги ВЛС")
                    result_services.append(stroka)
                    static_vars['указать ресурс ВЛС на договоре в Cordis'] = 'Для ВЛС, организованной по решению выше,'
                else:
                    static_vars['указать ресурс ВЛС на договоре в Cordis'] = all_portvk_in_tr.get(service)['exist_vk']
                static_vars['указать полосу'] = _get_policer(service)
                static_vars['полисером на Subinterface/на порту подключения'] = all_portvk_in_tr.get(service)['policer_vk']
                if all_portvk_in_tr.get(service)['type_portvk'] == 'access':
                    stroka = templates.get("Организация услуги порт ВЛС access'ом.")
                    result_services.append(analyzer_vars(stroka, static_vars, hidden_vars))
                elif all_portvk_in_tr.get(service)['type_portvk'] == 'trunk':
                    stroka = templates.get("Организация услуги порт ВЛC trunk'ом.")
                    result_services.append(analyzer_vars(stroka, static_vars, hidden_vars))


        elif 'Порт ВМ' in service:
            print('{}'.format(service.replace('|', ' ')) + '-' * 20)
            if logic_csw == True:
                result_services.append(enviroment_csw(value_vars))
            else:
                pass
            static_vars = {}
            hidden_vars = {}
            if value_vars.get('new_vm') == True:
                stroka = templates.get("Организация услуги виртуальный маршрутизатор")
                result_services.append(stroka)
                static_vars['указать название ВМ'] = ', организованного по решению выше,'
            else:
                static_vars['указать название ВМ'] = value_vars.get('exist_vm')
            if '1000' in service:
                static_vars['указать полосу'] = '1 Гбит/с'
            elif '100' in service:
                static_vars['указать полосу'] = '100 Мбит/с'
            elif '10' in service:
                static_vars['указать полосу'] = '10 Мбит/с'
            elif '1' in service:
                static_vars['указать полосу'] = '1 Гбит/с'
            else:
                static_vars['указать полосу'] = 'Неизвестная полоса'

            static_vars['полисером на SVI/на порту подключения'] = value_vars.get('policer_vm')
            if value_vars.get('vm_inet') == True:
                static_vars['без доступа в интернет/с доступом в интернет'] = 'с доступом в интернет'
            else:
                static_vars['без доступа в интернет/с доступом в интернет'] = 'без доступа в интернет'
                hidden_vars[
                    '- Согласовать с клиентом адресацию для порта ВМ без доступа в интернет.'] = '- Согласовать с клиентом адресацию для порта ВМ без доступа в интернет.'

            if value_vars.get('type_portvm') == 'access':
                stroka = templates.get("Организация услуги порт виртуального маршрутизатора access'ом.")
                result_services.append(analyzer_vars(stroka, static_vars, hidden_vars))
            elif value_vars.get('type_portvm') == 'trunk':
                stroka = templates.get("Организация услуги порт виртуального маршрутизатора trunk'ом.")
                result_services.append(analyzer_vars(stroka, static_vars, hidden_vars))


        elif 'HotSpot' in service:
            # hotspot_users = None
            static_vars = {}
            hidden_vars = {}
            print('{}'.format(service.replace('|', ' ')) + '-' * 20)

            if 'премиум +' in service.lower() or 'премиум+' in service.lower():
                if logic_csw == True:
                    result_services.append(enviroment_csw(value_vars))
                static_vars['указать количество клиентов'] = value_vars.get('hotspot_users')
                static_vars["access'ом (native vlan) / trunk"] = "access'ом"
                if value_vars.get('exist_hotspot_client') == True:
                    stroka = templates.get("Организация услуги Хот-спот Премиум + для существующего клиента.")
                else:
                    stroka = templates.get("Организация услуги Хот-спот Премиум + для нового клиента.")
                result_services.append(analyzer_vars(stroka, static_vars, hidden_vars))
            else:
                if logic_csw == True:
                    for i in range(int(value_vars.get('hotspot_points'))):
                        result_services.append(enviroment_csw(value_vars))
                    static_vars['указать название коммутатора'] = 'клиентского коммутатора'
                else:
                    static_vars['указать название коммутатора'] = value_vars.get('kad')
                if value_vars.get('exist_hotspot_client') == True:
                    stroka = templates.get("Организация услуги Хот-спот %Стандарт/Премиум% для существующего клиента.")
                else:
                    stroka = templates.get("Организация услуги Хот-спот %Стандарт/Премиум% для нового клиента.")
                if 'премиум' in service.lower():
                    static_vars['Стандарт/Премиум'] = 'Премиум'
                    static_vars['указать модель станций'] = 'Ubiquiti UniFi'
                else:
                    static_vars['Стандарт/Премиум'] = 'Стандарт'
                    static_vars['указать модель станций'] = 'D-Link DIR-300'
                if sreda == '2' or sreda == '4':
                    static_vars['ОИПМ/ОИПД'] = 'ОИПМ'
                else:
                    static_vars['ОИПМ/ОИПД'] = 'ОИПД'
                static_vars['указать количество станций'] = value_vars.get('hotspot_points')
                static_vars['ОАТТР/ОТИИ'] = 'ОАТТР'
                static_vars['указать количество клиентов'] = value_vars.get('hotspot_users')
                stroka = analyzer_vars(stroka, static_vars, hidden_vars)
                regex_counter = 'беспроводных станций: (\d+)'
                match_counter = re.search(regex_counter, stroka)
                counter_plur = int(match_counter.group(1))
                result_services.append(pluralizer_vars(stroka, counter_plur))


        elif 'Видеонаблюдение' in service:
            # cnt_camera = None
            print('-' * 20 + '\n' + '{}'.format(service.replace('|', ' ')))
            cameras = ['TRASSIR TR-D7111IR1W', 'TRASSIR TR-D7121IR1W', 'QTECH QVC-IPC-202VAE', 'QTECH QVC-IPC-202ASD', \
                       'TRASSIR TR-D3121IR1 v4', 'QTECH QVC-IPC-201E', 'TRASSIR TR-D2121IR3', 'QTECH QVC-IPC-502AS', \
                       'QTECH QVC-IPC-502VA', 'HiWatch DS-I453', 'QTECH QVC-IPC-501', 'TRASSIR TR-D2141IR3',
                       'HiWatch DS-I450']
            static_vars = {}
            hidden_vars = {}
            static_vars['указать модель камеры'] = value_vars.get('camera_model')
            if value_vars.get('voice') == True:
                static_vars['требуется запись звука / запись звука не требуется'] = 'требуется запись звука'
                hidden_vars[' и запись звука'] = ' и запись звука'
            else:
                static_vars['требуется запись звука / запись звука не требуется'] = 'запись звука не требуется'
            # regex_cnt_camera = ['(\d+)камер', '(\d+) камер', '(\d+) видеокамер', '(\d+)видеокамер']
            # for regex in regex_cnt_camera:
            #    match_cnt_camera = re.search(regex, service.lower())
            #    if match_cnt_camera:
            #        cnt_camera = match_cnt_camera.group(1)
            #        break

            camera_number = value_vars.get('camera_number')
            if int(camera_number) < 3:
                stroka = templates.get("Организация услуги Видеонаблюдение с использованием PoE-инжектора")
                if sreda == '2' or sreda == '4':
                    static_vars['ОИПМ/ОИПД'] = 'ОИПМ'
                else:
                    static_vars['ОИПМ/ОИПД'] = 'ОИПД'
                static_vars['указать количество линий'] = camera_number
                static_vars['указать количество камер'] = camera_number
                static_vars['указать количество инжекторов'] = camera_number
                static_vars['номер порта маршрутизатора'] = 'свободный'
                static_vars['0/3/7/15/30'] = value_vars.get('deep_archive')
                static_vars['указать адрес'] = value_vars.get('address')
                static_vars['указать место установки 1'] = value_vars.get('camera_place_one')

                if int(camera_number) == 2:
                    hidden_vars[
                        '-- %номер порта маршрутизатора%: %указать адрес%, Камера %указать место установки 2%, %указать модель камеры%, %требуется запись звука / запись звука не требуется%.'] = '-- %номер порта маршрутизатора%: %указать адрес%, Камера %указать место установки 2%, %указать модель камеры%, %требуется запись звука / запись звука не требуется%.'
                    hidden_vars[
                        '-- камеры %указать место установки 2% глубину хранения архива %0/3/7/15/30%[ и запись звука].'] = '-- камеры %указать место установки 2% глубину хранения архива %0/3/7/15/30%[ и запись звука].'
                    static_vars['указать место установки 2'] = value_vars.get('camera_place_two')
                static_vars[
                    'PoE-инжектор СКАТ PSE-PoE.220AC/15VA / OSNOVO Midspan-1/151A'] = 'PoE-инжектор СКАТ PSE-PoE.220AC/15VA'
                # result_services.append(analyzer_vars(stroka, static_vars, hidden_vars))

                stroka = analyzer_vars(stroka, static_vars, hidden_vars)
                counter_plur = int(camera_number)
                result_services.append(pluralizer_vars(stroka, counter_plur))


            elif int(camera_number) == 5 or int(camera_number) == 9:
                stroka = templates.get(
                    "Организация услуги Видеонаблюдение с использованием POE-коммутатора и PoE-инжектора")
                if sreda == '2' or sreda == '4':
                    static_vars['ОИПМ/ОИПД'] = 'ОИПМ'
                else:
                    static_vars['ОИПМ/ОИПД'] = 'ОИПД'
                static_vars['указать количество линий'] = str(int(camera_number) - 1)
                static_vars['указать количество камер'] = camera_number
                if int(camera_number) == 5:
                    static_vars['POE-коммутатор D-Link DES-1005P / TP-Link TL-SF1005P'] = 'D-Link DES-1005P'
                    static_vars['указать номер порта POE-коммутатора'] = '5'
                    static_vars['номер камеры'] = '5'
                elif int(camera_number) == 9:
                    static_vars['POE-коммутатор D-Link DES-1005P / TP-Link TL-SF1005P'] = 'Atis PoE-1010-8P'
                    static_vars['указать номер порта POE-коммутатора'] = '10'
                    static_vars['номер камеры'] = '9'
                static_vars['номер порта маршрутизатора'] = 'свободный'
                static_vars['0/3/7/15/30'] = value_vars.get('deep_archive')
                static_vars['указать адрес'] = value_vars.get('address')
                list_cameras_one = []
                list_cameras_two = []
                for i in range(int(camera_number) - 1):
                    extra_stroka_one = 'Порт {}: %указать адрес%, Камера №{}, %указать модель камеры%, %требуется запись звука / запись звука не требуется%\n'.format(
                        i + 1, i + 1)
                    list_cameras_one.append(extra_stroka_one)
                for i in range(int(camera_number)):
                    extra_stroka_two = '-- камеры Камера №{} глубину хранения архива %0/3/7/15/30%< и запись звука>;\n'.format(
                        i + 1)
                    list_cameras_two.append(extra_stroka_two)
                extra_extra_stroka_one = ''.join(list_cameras_one)
                extra_extra_stroka_two = ''.join(list_cameras_two)
                stroka = stroka[:stroka.index('- Организовать 1 линию от камеры')] + extra_extra_stroka_one + stroka[
                                                                                                              stroka.index(
                                                                                                                  '- Организовать 1 линию от камеры'):]
                stroka = stroka + '\n' + extra_extra_stroka_two

                static_vars[
                    'PoE-инжектор СКАТ PSE-PoE.220AC/15VA / OSNOVO Midspan-1/151A'] = 'PoE-инжектор СКАТ PSE-PoE.220AC/15VA'
                static_vars['указать количество POE-коммутаторов'] = '1'

                stroka = analyzer_vars(stroka, static_vars, hidden_vars)
                counter_plur = int(camera_number) - 1
                result_services.append(pluralizer_vars(stroka, counter_plur))
            else:
                stroka = templates.get("Организация услуги Видеонаблюдение с использованием POE-коммутатора")
                if sreda == '2' or sreda == '4':
                    static_vars['ОИПМ/ОИПД'] = 'ОИПМ'
                else:
                    static_vars['ОИПМ/ОИПД'] = 'ОИПД'
                static_vars['указать количество линий'] = camera_number
                static_vars['указать количество камер'] = camera_number
                if 5 < int(camera_number) < 9:
                    static_vars['POE-коммутатор D-Link DES-1005P / TP-Link TL-SF1005P'] = 'Atis PoE-1010-8P'
                    static_vars['указать номер порта POE-коммутатора'] = '10'
                elif 2 < int(camera_number) < 5:
                    static_vars['POE-коммутатор D-Link DES-1005P / TP-Link TL-SF1005P'] = 'D-Link DES-1005P'
                    static_vars['указать номер порта POE-коммутатора'] = '5'
                static_vars['номер порта маршрутизатора'] = 'свободный'
                static_vars['0/3/7/15/30'] = value_vars.get('deep_archive')
                static_vars['указать адрес'] = value_vars.get('address')

                list_cameras_one = []
                list_cameras_two = []
                for i in range(int(camera_number)):
                    extra_stroka_one = 'Порт {}: %указать адрес%, Камера №{}, %указать модель камеры%, %требуется запись звука / запись звука не требуется%;\n'.format(
                        i + 1, i + 1)
                    list_cameras_one.append(extra_stroka_one)
                for i in range(int(camera_number)):
                    extra_stroka_two = '-- камеры Камера №{} глубину хранения архива %0/3/7/15/30%< и запись звука>;\n'.format(
                        i + 1)
                    list_cameras_two.append(extra_stroka_two)
                extra_extra_stroka_one = ''.join(list_cameras_one)
                extra_extra_stroka_two = ''.join(list_cameras_two)
                print('!!!!!!!!!!!!!!!!!')
                print(stroka)
                stroka = stroka[:stroka.index(
                    'порты POE-коммутатора:')] + 'порты POE-коммутатора:\n' + extra_extra_stroka_one + '\n \nОВИТС проведение работ:\n' + stroka[
                                                                                                                                          stroka.index(
                                                                                                                                              '- Произвести настройку'):]
                stroka = stroka + '\n' + extra_extra_stroka_two
                static_vars['указать количество POE-коммутаторов'] = '1'

                # result_services.append(analyzer_vars(stroka, static_vars, hidden_vars))

                stroka = analyzer_vars(stroka, static_vars, hidden_vars)
                counter_plur = int(camera_number)
                result_services.append(pluralizer_vars(stroka, counter_plur))

        elif 'Телефон' in service:
            result_services_ots = []
            hidden_vars = {}
            static_vars = {}
            vgw = value_vars.get('vgw')
            ports_vgw = value_vars.get('ports_vgw')
            channel_vgw = value_vars.get('channel_vgw')
            if service.endswith('|'):
                if logic_csw == True:
                    result_services.append(enviroment_csw(value_vars))
                    static_vars[
                        'клиентского коммутатора / КАД (указать маркировку коммутатора)'] = 'клиентского коммутатора'
                elif logic_csw == False:
                    static_vars['клиентского коммутатора / КАД (указать маркировку коммутатора)'] = value_vars.get(
                        'kad')
                stroka = templates.get("Установка тел. шлюза у клиента")
                static_vars['указать модель тел. шлюза'] = vgw
                if vgw in ['Eltex TAU-2M.IP', 'Eltex RG-1404G или Eltex TAU-4M.IP', 'Eltex TAU-8.IP']:
                    static_vars['WAN порт/Ethernet Порт 0'] = 'WAN порт'
                else:
                    static_vars['WAN порт/Ethernet Порт 0'] = 'Ethernet Порт 0'
                    static_vars['указать модель тел. шлюза'] = vgw + ' c кабелем для коммутации в плинт'
                result_services_ots.append(analyzer_vars(stroka, static_vars, hidden_vars))
                if 'ватс' in service.lower():
                    stroka = templates.get("ВАТС (Подключение по аналоговой линии)")
                    static_vars['идентификатор тел. шлюза'] = 'установленный по решению выше'
                    static_vars['указать модель тел. шлюза'] = vgw
                    static_vars['указать количество портов'] = ports_vgw
                    if 'базов' in service.lower():
                        static_vars[
                            'базовым набором сервисов / расширенным набором сервисов'] = 'базовым набором сервисов'
                    elif 'расшир' in service.lower():
                        static_vars[
                            'базовым набором сервисов / расширенным набором сервисов'] = 'расширенным набором сервисов'

                    static_vars['указать количество телефонных линий'] = ports_vgw
                    if ports_vgw == 1:
                        static_vars['указать порты тел. шлюза'] = '1'
                    else:
                        static_vars['указать порты тел. шлюза'] = '1-{}'.format(ports_vgw)
                    static_vars['указать количество каналов'] = channel_vgw
                    stroka = analyzer_vars(stroka, static_vars, hidden_vars)
                    regex_counter = 'Организовать (\d+)'
                    match_counter = re.search(regex_counter, stroka)
                    counter_plur = int(match_counter.group(1))
                    result_services_ots.append(pluralizer_vars(stroka, counter_plur))
                else:
                    stroka = templates.get(
                        "Подключение аналогового телефона с использованием тел.шлюза на стороне клиента")
                    static_vars['указать модель тел. шлюза'] = vgw

                    static_vars['указать количество телефонных линий'] = channel_vgw
                    static_vars['указать количество каналов'] = channel_vgw
                    if ports_vgw == 1:
                        static_vars['указать порты тел. шлюза'] = '1'
                    else:
                        static_vars['указать порты тел. шлюза'] = '1-{}'.format(channel_vgw)
                    stroka = analyzer_vars(stroka, static_vars, hidden_vars)
                    regex_counter = 'Организовать (\d+)'
                    match_counter = re.search(regex_counter, stroka)
                    counter_plur = int(match_counter.group(1))
                    result_services_ots.append(pluralizer_vars(stroka, counter_plur))
            elif service.endswith('/'):
                stroka = templates.get("Установка тел. шлюза на ППС")

                static_vars['указать модель тел. шлюза'] = vgw
                static_vars['указать узел связи'] = value_vars.get('pps')
                result_services_ots.append(analyzer_vars(stroka, static_vars, hidden_vars))
                if 'ватс' in service.lower():
                    stroka = templates.get("ВАТС (Подключение по аналоговой линии)")
                    if 'базов' in service.lower():
                        static_vars[
                            'базовым набором сервисов / расширенным набором сервисов'] = 'базовым набором сервисов'
                    elif 'расшир' in service.lower():
                        static_vars[
                            'базовым набором сервисов / расширенным набором сервисов'] = 'расширенным набором сервисов'
                    static_vars['идентификатор тел. шлюза'] = 'установленный по решению выше'

                    static_vars['указать количество телефонных линий'] = ports_vgw
                    static_vars['указать количество портов'] = ports_vgw
                    if ports_vgw == 1:
                        static_vars['указать порты тел. шлюза'] = '1'
                    else:
                        static_vars['указать порты тел. шлюза'] = '1-{}'.format(ports_vgw)

                    static_vars['указать количество каналов'] = channel_vgw
                    stroka = analyzer_vars(stroka, static_vars, hidden_vars)
                    regex_counter = 'Организовать (\d+)'
                    match_counter = re.search(regex_counter, stroka)
                    counter_plur = int(match_counter.group(1))
                    result_services_ots.append(pluralizer_vars(stroka, counter_plur))
                else:
                    stroka = templates.get("Подключение аналогового телефона с использованием голосового шлюза на ППС")
                    static_vars['идентификатор тел. шлюза'] = 'установленного по решению выше'

                    static_vars['указать количество телефонных линий'] = channel_vgw
                    static_vars['указать количество каналов'] = channel_vgw
                    if ports_vgw == 1:
                        static_vars['указать порты тел. шлюза'] = '1'
                    else:
                        static_vars['указать порты тел. шлюза'] = '1-{}'.format(channel_vgw)
                    stroka = analyzer_vars(stroka, static_vars, hidden_vars)
                    regex_counter = 'Организовать (\d+)'
                    match_counter = re.search(regex_counter, stroka)
                    counter_plur = int(match_counter.group(1))
                    result_services_ots.append(pluralizer_vars(stroka, counter_plur))

            elif service.endswith('\\'):
                if 'ватс' in service.lower():
                    stroka = templates.get("ВАТС (Подключение по аналоговой линии)")
                    if 'базов' in service.lower():
                        static_vars[
                            'базовым набором сервисов / расширенным набором сервисов'] = 'базовым набором сервисов'
                    elif 'расшир' in service.lower():
                        static_vars[
                            'базовым набором сервисов / расширенным набором сервисов'] = 'расширенным набором сервисов'

                    static_vars['указать количество телефонных линий'] = ports_vgw
                    static_vars['указать количество портов'] = ports_vgw
                    if ports_vgw == 1:
                        static_vars['указать порты тел. шлюза'] = '1'
                    else:
                        static_vars['указать порты тел. шлюза'] = '1-{}'.format(ports_vgw)
                    static_vars['указать количество каналов'] = channel_vgw
                    stroka = analyzer_vars(stroka, static_vars, hidden_vars)
                    regex_counter = 'Организовать (\d+)'
                    match_counter = re.search(regex_counter, stroka)
                    counter_plur = int(match_counter.group(1))
                    result_services_ots.append(pluralizer_vars(stroka, counter_plur))
                else:
                    stroka = templates.get("Подключение аналогового телефона с использованием голосового шлюза на ППС")
                    static_vars['указать узел связи'] = value_vars.get('pps')

                    static_vars['указать количество телефонных линий'] = channel_vgw
                    static_vars['указать количество каналов'] = channel_vgw
                    stroka = analyzer_vars(stroka, static_vars, hidden_vars)
                    regex_counter = 'Организовать (\d+)'
                    match_counter = re.search(regex_counter, stroka)
                    counter_plur = int(match_counter.group(1))
                    result_services_ots.append(pluralizer_vars(stroka, counter_plur))
            else:
                if 'ватс' in service.lower():

                    static_vars['указать количество каналов'] = channel_vgw
                    if 'базов' in service.lower():
                        stroka = templates.get("ВАТС Базовая(SIP регистрация через Интернет)")

                    elif 'расшир' in service.lower():
                        stroka = templates.get("ВАТС Расширенная(SIP регистрация через Интернет)")
                        static_vars['указать количество портов'] = ports_vgw
                    result_services_ots.append(analyzer_vars(stroka, static_vars, hidden_vars))
                else:
                    stroka = templates.get(
                        "Подключения по цифровой линии с использованием протокола SIP, тип линии «SIP регистрация через Интернет»")

                    static_vars['указать количество каналов'] = channel_vgw
                    result_services_ots.append(analyzer_vars(stroka, static_vars, hidden_vars))

        elif 'ЛВС' in service:
            print('{}'.format(service.replace('|', ' ')) + '-' * 20)
            static_vars = {}
            hidden_vars = {}
            local_ports = value_vars.get('local_ports')
            static_vars['2-23'] = local_ports
            if value_vars.get('local_type') == 'СКС':
                stroka = templates.get("Организация СКС на %2-23% {порт}")
                if value_vars.get('sks_poe') == True:
                    hidden_vars[
                        'ОИПД подготовиться к работам:\n- Получить на складе территории PoE-инжектор %указать модель PoE-инжектора% - %указать количество% шт.'] = 'ОИПД подготовиться к работам:\n- Получить на складе территории PoE-инжектор %указать модель PoE-инжектора% - %указать количество% шт.'
                if value_vars.get('sks_router') == True:
                    hidden_vars[
                        '- Подключить %2-23% {организованную} {линию} связи в ^свободный^ ^порт^ маршрутизатора клиента.'] = '- Подключить %2-23% {организованную} {линию} связи в ^свободный^ ^порт^ маршрутизатора клиента.'
                static_vars['указать количество'] = local_ports
                stroka = analyzer_vars(stroka, static_vars, hidden_vars)
                counter_plur = int(local_ports)
                result_services.append(pluralizer_vars(stroka, counter_plur))
            else:
                stroka = templates.get("Организация ЛВС на %2-23% {порт}")
                if value_vars.get('lvs_busy') == True:
                    hidden_vars[
                        'МКО:\n- В связи с тем, что у клиента все порты на маршрутизаторе заняты необходимо с клиентом согласовать перерыв связи по одному из подключенных устройств к маршрутизатору.\nВо время проведения работ данная линия будет переключена из маршрутизатора клиента в проектируемый коммутатор.'] = 'МКО:\n- В связи с тем, что у клиента все порты на маршрутизаторе заняты необходимо с клиентом согласовать перерыв связи по одному из подключенных устройств к маршрутизатору.\nВо время проведения работ данная линия будет переключена из маршрутизатора клиента в проектируемый коммутатор.\n'
                    hidden_vars[
                        '- По согласованию с клиентом высвободить LAN-порт на маршрутизаторе клиента переключив сущ. линию для ЛВС клиента из маршрутизатора клиента в свободный порт установленного коммутатора.'] = '- По согласованию с клиентом высвободить LAN-порт на маршрутизаторе клиента переключив сущ. линию для ЛВС клиента из маршрутизатора клиента в свободный порт установленного коммутатора.'
                    hidden_vars[
                        '- Подтвердить восстановление связи для порта ЛВС который был переключен в установленный коммутатор.'] = '- Подтвердить восстановление связи для порта ЛВС который был переключен в установленный коммутатор.'
                lvs_switch = value_vars.get('lvs_switch')
                static_vars['указать модель коммутатора'] = lvs_switch
                if lvs_switch == ('TP-Link TL-SG105 V4' or 'ZYXEL GS1200-5'):
                    static_vars['5/8/16/24'] = '5'
                elif lvs_switch == ('TP-Link TL-SG108 V4' or 'ZYXEL GS1200-8'):
                    static_vars['5/8/16/24'] = '8'
                elif lvs_switch == 'D-link DGS-1100-16/B':
                    static_vars['5/8/16/24'] = '16'
                elif lvs_switch == 'D-link DGS-1100-24/B':
                    static_vars['5/8/16/24'] = '24'
                stroka = analyzer_vars(stroka, static_vars, hidden_vars)
                print('chech lvs stroka')
                print(stroka)
                counter_plur = int(local_ports)
                result_services.append(pluralizer_vars(stroka, counter_plur))
    return result_services, result_services_ots

def _list_kad(value_vars):
    """Данный метод формирует список всех КАД на узле в строку"""
    list_kad = []

    list_switches = value_vars.get('list_switches')
    if len(list_switches) == 1:
        kad = list_switches[0][0]
    else:
        for i in range(len(list_switches)):
            if (list_switches[i][0].startswith('IAS')) or (list_switches[i][0].startswith('AR')):
                pass
            else:
                list_kad.append(list_switches[i][0])
        kad = ' или '.join(list_kad)
    value_vars.update({'kad': kad})
    return kad, value_vars

def _readable_node(node_mon):
    """Данный метод приводит название узла к читаемой форме"""
    node_templates = {', РУА': 'РУА ', ', УА': 'УПА ', ', АВ': 'ППС ', ', КК': 'КК '}
    for key, item in node_templates.items():
        if node_mon.endswith(key):
            finish_node = item + node_mon[:node_mon.index(key)]
    return finish_node

def _new_enviroment(value_vars):
    """Данный метод проверяет необходимость установки КК, если такая необходимость есть формирует и заполняет шаблон
     для установки КК, если нет необходимости отправляет на метод, который формирует шаблон отдельной линии"""
    if value_vars.get('result_services'):
        result_services = value_vars.get('result_services')
    else:
        result_services = []
    kad = 'Не требуется'

    counter_line_services = value_vars.get('counter_line_services')
    if counter_line_services > 0:
        #kad, value_vars = _list_kad(value_vars)
        kad = value_vars.get('kad')
        print("!!!!!value_vars.get('kad')")
        print(kad)
        #value_vars.update({'kad': kad})
        pps = _readable_node(value_vars.get('pps'))

        logic_csw = value_vars.get('logic_csw')
        if counter_line_services == 1 and logic_csw == False:
            enviroment(result_services, value_vars)
        elif counter_line_services > 1:
            if logic_csw == False:
                for i in range(counter_line_services):
                    enviroment(result_services, value_vars)

        if logic_csw == True:
            static_vars = {}
            hidden_vars = {}
            static_vars['указать № порта'] = value_vars.get('port_csw')
            static_vars['указать модель коммутатора'] = value_vars.get('model_csw')
            static_vars['указать узел связи'] = pps
            static_vars['указать название коммутатора'] = kad
            static_vars['указать порт коммутатора'] = value_vars.get('port')
            logic_csw_1000 = value_vars.get('logic_csw_1000')
            if logic_csw_1000 == True:
                static_vars['100/1000'] = '1000'
            else:
                static_vars['100/1000'] = '100'
            templates = value_vars.get('templates')
            if value_vars.get('type_install_csw'):
                pass
            else:
                sreda = value_vars.get('sreda')
                if sreda == '1':
                    print("Присоединение КК к СПД по медной линии связи." + '-' * 20)
                    stroka = templates.get("Установка клиентского коммутатора")
                    static_vars['ОИПМ/ОИПД'] = 'ОИПД'
                    static_vars['медную линию связи/ВОЛС'] = 'медную линию связи'

                    result_services.append(analyzer_vars(stroka, static_vars, hidden_vars))

                elif sreda == '2' or sreda == '4':
                    if value_vars.get('ppr'):
                        print('-' * 20 + '\n' + "Присоединение КК к СПД по оптической линии ")
                        stroka = templates.get("Установка клиентского коммутатора")
                        static_vars['указать № ППР'] = value_vars.get('ppr')
                    else:
                        print('-' * 20 + '\n' + "Установка клиентского коммутатора по оптической линии связи")
                        stroka = templates.get("Установка клиентского коммутатора")

                    static_vars['ОИПМ/ОИПД'] = 'ОИПМ'
                    static_vars['медную линию связи/ВОЛС'] = 'ВОЛС'
                    hidden_vars[
                        '- Установить на стороне %указать узел связи% %указать конвертер/передатчик на стороне узла связи%'] = '- Установить на стороне %указать узел связи% %указать конвертер/передатчик на стороне узла связи%'
                    hidden_vars[
                        'и %указать конвертер/передатчик на стороне клиента%'] = 'и %указать конвертер/передатчик на стороне клиента%'
                    static_vars['указать конвертер/передатчик на стороне узла связи'] = value_vars.get('device_pps')
                    static_vars['указать конвертер/передатчик на стороне клиента'] = value_vars.get('device_client')

                    if logic_csw_1000 == True:
                        hidden_vars[
                            '-ВНИМАНИЕ! Совместно с ОНИТС СПД удаленно настроить клиентский коммутатор.'] = '-ВНИМАНИЕ! Совместно с ОНИТС СПД удаленно настроить клиентский коммутатор.'
                        hidden_vars[
                            '- Совместно с %ОИПМ/ОИПД% удаленно настроить клиентский коммутатор.'] = '- Совместно с %ОИПМ/ОИПД% удаленно настроить клиентский коммутатор.'
                    result_services.append(analyzer_vars(stroka, static_vars, hidden_vars))

                elif sreda == '3':
                    print("Присоединение к СПД по беспроводной среде передачи данных.")
                    stroka = templates.get("Установка клиентского коммутатора")
                    static_vars['медную линию связи/ВОЛС'] = 'медную линию связи'
                    static_vars['ОИПМ/ОИПД'] = 'ОИПД'
                    static_vars['указать модель беспроводных точек'] = value_vars.get('access_point')
                    hidden_vars[
                        '- Создать заявку в Cordis на ОНИТС СПД для выделения реквизитов беспроводных точек доступа WDS/WDA.'] = '- Создать заявку в Cordis на ОНИТС СПД для выделения реквизитов беспроводных точек доступа WDS/WDA.'
                    hidden_vars[
                        '- Установить на стороне %указать узел связи% и на стороне клиента беспроводные точки доступа %указать модель беспроводных точек% по решению ОАТТР.'] = '- Установить на стороне %указать узел связи% и на стороне клиента беспроводные точки доступа %указать модель беспроводных точек% по решению ОАТТР.'
                    hidden_vars[
                        '- По заявке в Cordis выделить реквизиты для управления беспроводными точками.'] = '- По заявке в Cordis выделить реквизиты для управления беспроводными точками.'
                    hidden_vars[
                        '- Совместно с ОИПД подключить к СПД и запустить беспроводные станции (WDS/WDA).'] = '- Совместно с ОИПД подключить к СПД и запустить беспроводные станции (WDS/WDA).'
                    if value_vars.get('access_point') == 'Infinet H11':
                        hidden_vars[
                            '- Доставить в офис ОНИТС СПД беспроводные точки Infinet H11 для их настройки.'] = '- Доставить в офис ОНИТС СПД беспроводные точки Infinet H11 для их настройки.'
                        hidden_vars[
                            'После выполнения подготовительных работ в рамках заявки в Cordis на ОНИТС СПД и настройки точек в офисе ОНИТС СПД:'] = 'После выполнения подготовительных работ в рамках заявки в Cordis на ОНИТС СПД и настройки точек в офисе ОНИТС СПД:'
                    else:
                        hidden_vars[
                            'После выполнения подготовительных работ в рамках заявки в Cordis на ОНИТС СПД:'] = 'После выполнения подготовительных работ в рамках заявки в Cordis на ОНИТС СПД:'
                    result_services.append(analyzer_vars(stroka, static_vars, hidden_vars))

    return result_services, value_vars


def exist_enviroment_install_csw(value_vars):
    if value_vars.get('result_services'):
        result_services = value_vars.get('result_services')
    else:
        result_services = []

    static_vars = {}
    hidden_vars = {}
    pps = _readable_node(value_vars.get('pps'))
    static_vars['указать узел связи'] = pps
    static_vars['указать модель коммутатора'] = value_vars.get('model_csw')
    static_vars['указать № порта'] = value_vars.get('port_csw')
    logic_csw_1000 = value_vars.get('logic_csw_1000')
    if logic_csw_1000 == True:
        static_vars['100/1000'] = '1000'
    else:
        static_vars['100/1000'] = '100'

    templates = value_vars.get('templates')

    stroka = templates.get("Установка клиентского коммутатора")
    hidden_vars['МКО:'] = 'МКО:'
    hidden_vars[
        '- Проинформировать клиента о простое сервиса на время проведения работ.'] = '- Проинформировать клиента о простое сервиса на время проведения работ.'
    hidden_vars['- Согласовать время проведение работ.'] = '- Согласовать время проведение работ.'

    if value_vars.get('type_install_csw') == 'Медная линия и порт не меняются':
        static_vars['ОИПМ/ОИПД'] = 'ОИПД'
        kad = value_vars.get('selected_ono')[0][-2]
        static_vars['указать название коммутатора'] = kad
        result_services.append(analyzer_vars(stroka, static_vars, hidden_vars))
    elif value_vars.get('type_install_csw') == 'ВОЛС и порт не меняются':
        static_vars['ОИПМ/ОИПД'] = 'ОИПМ'
        hidden_vars[
            'и %указать конвертер/передатчик на стороне клиента%'] = 'и %указать конвертер/передатчик на стороне клиента%'
        static_vars['указать конвертер/передатчик на стороне клиента'] = 'оптический передатчик SFP WDM, до 20 км, 1550 нм в клиентский коммутатор'
        if logic_csw_1000 == True:
            hidden_vars[
                '-ВНИМАНИЕ! Совместно с ОНИТС СПД удаленно настроить клиентский коммутатор.'] = '-ВНИМАНИЕ! Совместно с ОНИТС СПД удаленно настроить клиентский коммутатор.'
            hidden_vars[
                '- Совместно с %ОИПМ/ОИПД% удаленно настроить клиентский коммутатор.'] = '- Совместно с %ОИПМ/ОИПД% удаленно настроить клиентский коммутатор.'
        kad = value_vars.get('selected_ono')[0][-2]
        static_vars['указать название коммутатора'] = kad
        result_services.append(analyzer_vars(stroka, static_vars, hidden_vars))
    else:
        kad, value_vars = _list_kad(value_vars)
        static_vars['указать название коммутатора'] = kad
        static_vars['указать порт коммутатора'] = value_vars.get('port')

        if value_vars.get('type_install_csw') == 'Перевод на гигабит по меди на текущем узле':
            static_vars['ОИПМ/ОИПД'] = 'ОИПД'
            hidden_vars[
            '- Использовать существующую %медную линию связи/ВОЛС% от %указать узел связи% до клиента.'] = '- Использовать существующую %медную линию связи/ВОЛС% от %указать узел связи% до клиента.'
            hidden_vars[
            '- Переключить линию для клиента в порт %указать порт коммутатора% коммутатора %указать название коммутатора%.'] = '- Переключить линию для клиента в порт %указать порт коммутатора% коммутатора %указать название коммутатора%.'
            hidden_vars[
            'Старый порт: порт %указать старый порт коммутатора% коммутатора %указать название старого коммутатора%.'] = 'Старый порт: порт %указать старый порт коммутатора% коммутатора %указать название старого коммутатора%.'
            hidden_vars[
            'Новый порт: порт %указать порт коммутатора% коммутатора %указать название коммутатора%.'] = 'Новый порт: порт %указать порт коммутатора% коммутатора %указать название коммутатора%.'
            static_vars['медную линию связи/ВОЛС'] = 'медную линию связи'

            static_vars['указать название старого коммутатора'] = value_vars.get('selected_ono')[0][-2]
            static_vars['указать старый порт коммутатора'] = value_vars.get('selected_ono')[0][-1]
            result_services.append(analyzer_vars(stroka, static_vars, hidden_vars))
        elif value_vars.get('type_install_csw') == 'Перевод на гигабит по ВОЛС на текущем узле':
            static_vars['ОИПМ/ОИПД'] = 'ОИПМ'
            hidden_vars[
            '- Использовать существующую %медную линию связи/ВОЛС% от %указать узел связи% до клиента.'] = '- Использовать существующую %медную линию связи/ВОЛС% от %указать узел связи% до клиента.'
            hidden_vars[
            '- Переключить линию для клиента в порт %указать порт коммутатора% коммутатора %указать название коммутатора%.'] = '- Переключить линию для клиента в порт %указать порт коммутатора% коммутатора %указать название коммутатора%.'
            hidden_vars[
            'Старый порт: порт %указать старый порт коммутатора% коммутатора %указать название старого коммутатора%.'] = 'Старый порт: порт %указать старый порт коммутатора% коммутатора %указать название старого коммутатора%.'
            hidden_vars[
            'Новый порт: порт %указать порт коммутатора% коммутатора %указать название коммутатора%.'] = 'Новый порт: порт %указать порт коммутатора% коммутатора %указать название коммутатора%.'
            hidden_vars[
            '- Установить на стороне %указать узел связи% %указать конвертер/передатчик на стороне узла связи%'] = '- Установить на стороне %указать узел связи% %указать конвертер/передатчик на стороне узла связи%'
            static_vars['указать конвертер/передатчик на стороне узла связи'] = value_vars.get('device_pps')
            hidden_vars[
            'и %указать конвертер/передатчик на стороне клиента%'] = 'и %указать конвертер/передатчик на стороне клиента%'
            static_vars['указать конвертер/передатчик на стороне клиента'] = value_vars.get('device_client')
            static_vars['медную линию связи/ВОЛС'] = 'ВОЛС'

            static_vars['указать название старого коммутатора'] = value_vars.get('selected_ono')[0][-2]
            static_vars['указать старый порт коммутатора'] = value_vars.get('selected_ono')[0][-1]
            hidden_vars[
            '-ВНИМАНИЕ! Совместно с ОНИТС СПД удаленно настроить клиентский коммутатор.'] = '-ВНИМАНИЕ! Совместно с ОНИТС СПД удаленно настроить клиентский коммутатор.'
            hidden_vars[
            '- Совместно с %ОИПМ/ОИПД% удаленно настроить клиентский коммутатор.'] = '- Совместно с %ОИПМ/ОИПД% удаленно настроить клиентский коммутатор.'
            result_services.append(analyzer_vars(stroka, static_vars, hidden_vars))
        elif value_vars.get('type_install_csw') == 'Перевод на гигабит переключение с меди на ВОЛС' or value_vars.get(
            'type_install_csw') == 'Перевод на гигабит/перенос на новый узел':

            static_vars['указать название старого коммутатора'] = value_vars.get('selected_ono')[0][-2]
            static_vars['указать старый порт коммутатора'] = value_vars.get('selected_ono')[0][-1]
            hidden_vars[
            'Старый порт: порт %указать старый порт коммутатора% коммутатора %указать название старого коммутатора%.'] = 'Старый порт: порт %указать старый порт коммутатора% коммутатора %указать название старого коммутатора%.'
            hidden_vars[
            'Новый порт: порт %указать порт коммутатора% коммутатора %указать название коммутатора%.'] = 'Новый порт: порт %указать порт коммутатора% коммутатора %указать название коммутатора%.'
            hidden_vars[
            '- Организовать %медную линию связи/ВОЛС% от %указать узел связи% до клиентcкого коммутатора по решению ОАТТР.'] = '- Организовать %медную линию связи/ВОЛС% от %указать узел связи% до клиентcкого коммутатора по решению ОАТТР.'
            static_vars['медную линию связи/ВОЛС'] = 'ВОЛС'
            static_vars['ОИПМ/ОИПД'] = 'ОИПМ'
            hidden_vars[
            '- Подключить организованную линию для клиента в коммутатор %указать название коммутатора%, порт задействовать %указать порт коммутатора%.'] = '- Подключить организованную линию для клиента в коммутатор %указать название коммутатора%, порт задействовать %указать порт коммутатора%.'
            hidden_vars[
            '- Установить на стороне %указать узел связи% %указать конвертер/передатчик на стороне узла связи%'] = '- Установить на стороне %указать узел связи% %указать конвертер/передатчик на стороне узла связи%'
            static_vars['указать конвертер/передатчик на стороне узла связи'] = value_vars.get('device_pps')
            hidden_vars[
            'и %указать конвертер/передатчик на стороне клиента%'] = 'и %указать конвертер/передатчик на стороне клиента%'
            static_vars['указать конвертер/передатчик на стороне клиента'] = value_vars.get('device_client')
            if logic_csw_1000 == True:
                hidden_vars[
                    '-ВНИМАНИЕ! Совместно с ОНИТС СПД удаленно настроить клиентский коммутатор.'] = '-ВНИМАНИЕ! Совместно с ОНИТС СПД удаленно настроить клиентский коммутатор.'
                hidden_vars[
                    '- Совместно с %ОИПМ/ОИПД% удаленно настроить клиентский коммутатор.'] = '- Совместно с %ОИПМ/ОИПД% удаленно настроить клиентский коммутатор.'
            result_services.append(analyzer_vars(stroka, static_vars, hidden_vars))
    value_vars.update({'kad': kad})
    return result_services, value_vars


def _titles(result_services, result_services_ots):
    """Данный метод формирует список заголовков из шаблонов в блоках ОРТР и ОТС"""
    index_template = 1
    titles = []
    for i in range(len(result_services)):
        result_services[i] = '{}. '.format(index_template) + result_services[i]
        titles.append(result_services[i][:result_services[i].index('---')])
        index_template += 1

    if result_services_ots == None:
        pass
    else:
        for i in range(len(result_services_ots)):
            result_services_ots[i] = '{}. '.format(index_template) + result_services_ots[i]
            titles.append(result_services_ots[i][:result_services_ots[i].index('---')])
            index_template += 1

    return titles

def client_new(value_vars):
    """Данный метод с помощью внутрених методов формирует блоки ОРТР(заголовки и заполненные шаблоны),
     ОТС(заполненые шаблоны) для нового присоединения и новых услуг"""
    result_services, value_vars = _new_enviroment(value_vars)
    result_services, result_services_ots = _new_services(result_services, value_vars)


    return result_services, result_services_ots, value_vars


def analyzer_vars(stroka, static_vars, hidden_vars):
    '''Данная функция принимает строковую переменную, содержащую шаблон услуги со страницы
    Типовые блоки технического решения. Ищет в шаблоне блоки <> и сравнивает с аналогичными переменными из СПП.
    По средством доп. словаря формирует итоговый словарь содержащий блоки из СПП, которые
    есть в блоках шаблона(чтобы не выводить неактуальный блок) и блоки шаблона, которых не было в блоках
    из СПП(чтобы не пропустить неучтенный блок)
    Передаем переменные, т.к. переменные из глобал видятся, а из другой функции нет.
'''
    #    блок для определения необходимости частных строк <>
    list_var_lines = []
    list_var_lines_in = []
    regex_var_lines = '<(.+?)>'
    match_var_lines = re.finditer(regex_var_lines, stroka, flags=re.DOTALL)

    for i in match_var_lines:
        print('совпадения <>')
        print(i)
        list_var_lines.append(i.group(1))

    for i in list_var_lines:
        print(i)
        if hidden_vars.get(i):
            stroka = stroka.replace('<{}>'.format(i), hidden_vars[i])

        else:
            stroka = stroka.replace('<{}>'.format(i), '  ')

    regex_var_lines_in = '\[(.+?)\]'
    match_var_lines_in = re.finditer(regex_var_lines_in, stroka, flags=re.DOTALL)
    print(match_var_lines_in)
    for i in match_var_lines_in:
        print('совпадения []')
        print(i)
        list_var_lines_in.append(i.group(1))

    for i in list_var_lines_in:
        print(i)
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
            stroka = stroka.replace('\n \n \n \n', '\n')

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
        print(dynamic_vars[key])
    for key in dynamic_vars.keys():
        print(key)
        stroka = stroka.replace('%{}%'.format(key), dynamic_vars[key])
        stroka = stroka.replace(' .', '.')
    #for key in dynamic_vars.keys():
    #    if dynamic_vars[key] == None:
    #        stroka = stroka.replace('%{}%'.format(key), input('Указать свое значение "{}": '.format(key)))
    #    else:
    #        logic = sss.state('"{}": {}'.format(key, dynamic_vars[key]))
    #        if logic == 'y':
    #            stroka = stroka.replace('%{}%'.format(key), dynamic_vars[key])
            #elif logic == 'n':
            #    stroka = stroka.replace('%{}%'.format(key), input('Указать свое значение: '))
    return stroka

def pluralizer_vars(stroka, counter_plur):
    '''Данная функция на основе количества устройств в шаблоне меняет ед./множ. число связанных слов'''
    morph = pymorphy2.MorphAnalyzer()
    regex = '{(\w+?)}'
    match = re.finditer(regex, stroka, flags=re.DOTALL)  #
    for i in match:
        replased_word = '{' + i.group(1) + '}'
        pluralize = morph.parse(i.group(1))[0]
        stroka = stroka.replace(replased_word, pluralize.make_agree_with_number(counter_plur).word)
    regex_plur = '\^(\w+?)\^'
    match_plur = re.finditer(regex_plur, stroka, flags=re.DOTALL)
    if counter_plur == 1:
        for i in match_plur:
            replased_word = '^' + i.group(1) + '^'
            pluralize = morph.parse(i.group(1))[0]
            stroka = stroka.replace(replased_word, pluralize.inflect({'sing'}).word)
    elif counter_plur > 1:
        for i in match_plur:
            replased_word = '^' + i.group(1) + '^'
            pluralize = morph.parse(i.group(1))[0]
            if 'ADJF' in pluralize.tag:
                stroka = stroka.replace(replased_word, pluralize.inflect({'nomn', 'plur'}).word)
            elif 'NOUN' in pluralize.tag:
                stroka = stroka.replace(replased_word, pluralize.inflect({'plur'}).word)
    return stroka



def enviroment(result_services, value_vars):
    sreda = value_vars.get('sreda')
    ppr = value_vars.get('ppr')
    templates = value_vars.get('templates')
    pps = _readable_node(value_vars.get('pps'))
    kad = value_vars.get('kad')
    port = value_vars.get('port')
    device_client = value_vars.get('device_client')
    device_pps = value_vars.get('device_pps')
    speed_port = value_vars.get('speed_port')
    access_point = value_vars.get('access_point')
    if sreda == '1':
        print("Присоединение к СПД по медной линии связи."+'-'*20)
        static_vars = {}
        hidden_vars = {}
        stroka = templates.get("Присоединение к СПД по медной линии связи.")
        static_vars['указать узел связи'] = pps
        static_vars['указать название коммутатора'] = kad
        static_vars['указать порт коммутатора'] = port
        static_vars['ОИПМ/ОИПД'] = 'ОИПД'
        result_services.append(analyzer_vars(stroka, static_vars, hidden_vars))
        return result_services

    if sreda == '2' or sreda == '4':
        static_vars = {}
        if ppr:
            print('-' * 20 + '\n' + "Присоединение к СПД по оптической линии связи с простоем связи услуг.")
            stroka = templates.get("Присоединение к СПД по оптической линии связи с простоем связи услуг.")
            static_vars['указать № ППР'] = ppr
        else:
            print('-' * 20 + '\n' + "Присоединение к СПД по оптической линии связи.")
            stroka = templates.get("Присоединение к СПД по оптической линии связи.")
        print("Присоединение к СПД по оптической линии связи."+'-'*20)

        hidden_vars = {}
        static_vars['указать узел связи'] = pps
        static_vars['указать название коммутатора'] = kad
        static_vars['ОИПМ/ОИПД'] = 'ОИПМ'
        static_vars['указать порт коммутатора'] = port
        static_vars['указать режим работы порта'] = speed_port
        static_vars['указать конвертер/передатчик на стороне узла связи'] = device_pps
        static_vars['указать конвертер/передатчик на стороне клиента'] = device_client

        result_services.append(analyzer_vars(stroka, static_vars, hidden_vars))
        return result_services


    elif sreda == '3':
        print("Присоединение к СПД по беспроводной среде передачи данных.")

        static_vars = {}
        if ppr:
            print('-' * 20 + '\n' + "Присоединение к СПД по беспроводной среде передачи данных с простоем связи услуг.")
            stroka = templates.get("Присоединение к СПД по беспроводной среде передачи данных с простоем связи услуг.")
            static_vars['указать № ППР'] = ppr
        else:
            print('-' * 20 + '\n' + "Присоединение к СПД по беспроводной среде передачи данных.")
            stroka = templates.get("Присоединение к СПД по беспроводной среде передачи данных.")
        print("Присоединение к СПД по беспроводной среде передачи данных."+'-'*20)
        hidden_vars = {}
        static_vars['указать узел связи'] = pps
        static_vars['указать название коммутатора'] = kad

        static_vars['указать порт коммутатора'] = port
        static_vars['указать модель беспроводных точек'] = access_point
        if access_point == 'Infinet H11':
            hidden_vars['- Доставить в офис ОНИТС СПД беспроводные точки Infinet H11 для их настройки.'] = '- Доставить в офис ОНИТС СПД беспроводные точки Infinet H11 для их настройки.'
            hidden_vars[' и настройки точек в офисе ОНИТС СПД'] = ' и настройки точек в офисе ОНИТС СПД'

        result_services.append(analyzer_vars(stroka, static_vars, hidden_vars))
        return result_services



def enviroment_csw(value_vars):
    """Добавляет блок организации медной линии от КК"""
    sreda = value_vars.get('sreda')
    templates = value_vars.get('templates')
    static_vars = {}
    hidden_vars = {}
    stroka = templates.get("Присоединение к СПД по медной линии связи.")
    static_vars['указать узел связи'] = 'клиентского коммутатора'
    static_vars['указать название коммутатора'] = 'установленный по решению выше'
    static_vars['указать порт коммутатора'] = 'свободный'
    if sreda == '2' or sreda == '4':
        static_vars['ОИПМ/ОИПД'] = 'ОИПМ'
    else:
        static_vars['ОИПМ/ОИПД'] = 'ОИПД'
    return analyzer_vars(stroka, static_vars, hidden_vars)




from django.http import JsonResponse

def tr_spin(request):
    text = 'This is my statement one.&#13;&#10;This is my statement2'
    return render(request, 'tickets/spinner.html', {'text': text})

def spp_json(request):
    data = list(SPP.objects.values())
    return JsonResponse(data, safe=False)


from django.forms import formset_factory
#ArticleFormSet = formset_factory(ListResourcesForm, extra=2)
#formset = ArticleFormSet()


def test_formset(request):
    """Данный метод получает спискок ресурсов с выбранного договора. Формирует форму, в которой пользователь выбирает
     только 1 ресурс, который будет участвовать в ТР. По коммутатору этого ресурса метод добавляет все ресурсы с данным
      коммутатором в итоговый список. Если выбрано более одного или ни одного ресурса возвращает эту же форму повторно.
      По точке подключения(город, улица) проверяет наличие телефонии на договоре. Отправляет пользователя на страницу
      формирования заголовка."""
    ono = request.session['ono']
    try:
        phone_address = request.session['phone_address']
    except KeyError:
        phone_address = None
    print('!!!!phone_address')
    print(phone_address)
    ListResourcesFormSet = formset_factory(ListResourcesForm, extra=len(ono))
    if request.method == 'POST':
        formset = ListResourcesFormSet(request.POST)
        if formset.is_valid():

            data = formset.cleaned_data
            print('!!!!!!!!datatest_formset')
            print(data)
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
                    return redirect('test_formset')
                else:
                    for i in unselected_ono:
                        if selected_ono[0][-2] == i[-2]: #to do сейчас проверка по КАД. По точке подключения нужна? Хорошо посмотреть 00128733
                            selected_ono.append(i)
                    if phone_address:

                        print('!!!! doshli do any')
                        print(selected_ono[0][3])
                        print(phone_address)
                        if any(phone_addr in selected_ono[0][3] for phone_addr in phone_address):
                            phone_exist = True
                        else:
                            phone_exist = False
                    else:
                        phone_exist = False
                    print('!!!phone_exist')
                    print(phone_exist)
                    request.session['phone_exist'] = phone_exist
                    request.session['selected_ono'] = selected_ono
                    return redirect('forming_header')
            else:
                messages.warning(request, 'Ресурсы не выбраны')
                return redirect('test_formset')

    else:
        ticket_tr_id = request.session['ticket_tr_id']
        ticket_tr = TR.objects.get(id=ticket_tr_id)
        task_otpm = ticket_tr.ticket_k.task_otpm
        formset = ListResourcesFormSet()
        ono_for_formset = []
        for resource_for_formset in ono:
            resource_for_formset.pop(5)
            resource_for_formset.pop(1)
            resource_for_formset.pop(0)
            ono_for_formset.append(resource_for_formset)

        context = {
            'ono_for_formset': ono_for_formset,
            #'contract': contract,
            'formset': formset,
            'task_otpm': task_otpm
        }

        return render(request, 'tickets/test_formset.html', context)


def job_formset(request):
    """Данный метод получает спискок услуг из ТР. Формирует форму, в которой пользователь выбирает, что необходимо
     сделать с услугой(перенос, изменение, организация) и формируется соответствующие списки услуг."""
    head = request.session['head']
    ticket_tr_id = request.session['ticket_tr_id']
    ticket_tr = TR.objects.get(id=ticket_tr_id)
    oattr = ticket_tr.oattr
    pps = ticket_tr.pps
    services = ticket_tr.services
    ListJobsFormSet = formset_factory(ListJobsForm, extra=len(services))
    if request.method == 'POST':
        formset = ListJobsFormSet(request.POST)
        if formset.is_valid():
            pass_with_csw_job_services = []
            pass_without_csw_job_services = []
            pass_no_spd_job_services = []
            change_job_services = []
            new_with_csw_job_services = []
            new_without_csw_job_services = []
            new_no_spd_jobs_services = []
            data = formset.cleaned_data
            print('!!!!!services')
            print(services)
            print('!!!!!datajobservices')
            print(data)
            selected = zip(services, data)
            for services, data in selected:
                if data == {'jobs': 'Организация сервиса(СПД) без уст. КК'}:
                    new_without_csw_job_services.append(services)
                elif data == {'jobs': 'Организация сервиса(СПД) с уст. КК'}:
                    new_with_csw_job_services.append(services)
                elif data == {'jobs': 'Организация сервиса(не СПД)'}:
                    new_no_spd_jobs_services.append(services)
                elif data == {'jobs': 'Перенос сервиса(СПД) без КК'}:
                    pass_without_csw_job_services.append(services)
                elif data == {'jobs': 'Перенос сервиса(СПД) с КК'}:
                    pass_with_csw_job_services.append(services)
                elif data == {'jobs': 'Перенос сервиса(не СПД)'}:
                    pass_no_spd_job_services.append(services)
                elif data == {'jobs': 'Изменение сервиса'}:
                    change_job_services.append(services)
                elif data == {'jobs': 'Не требуется'}:
                    pass
            request.session['new_without_csw_job_services'] = new_without_csw_job_services
            request.session['new_with_csw_job_services'] = new_with_csw_job_services
            request.session['new_no_spd_jobs_services'] = new_no_spd_jobs_services
            request.session['pass_without_csw_job_services'] = pass_without_csw_job_services
            request.session['pass_with_csw_job_services'] = pass_with_csw_job_services
            request.session['pass_no_spd_job_services'] = pass_no_spd_job_services
            request.session['change_job_services'] = change_job_services

            #context = {
            #    'pass_job_services': pass_job_services,
            #    'change_job_services': change_job_services,
            #    'new_job_services': new_job_services,
            #   'data': data
            #

            return redirect('project_tr_exist_cl')
            #return redirect('passage')
            #return render(request, 'tickets/no_data.html', context)

    else:

        formset = ListJobsFormSet()
        context = {
            'head': head,
            'oattr': oattr,
            'pps': pps,
            'services': services,
            #'contract': contract,
            'formset': formset
        }

        return render(request, 'tickets/job_formset.html', context)


def _parsing_id_client_device_by_device_name(name, login, password):
    """Данный метод получает на входе название КАД и по нему парсит страницу с поиском коммутаторв, чтобы определить
    id этого коммутатора"""
    #Получение страницы с данными о коммутаторе
    url = 'https://cis.corp.itmh.ru/stu/NetSwitch/SearchNetSwitchProxy'
    data = {'IncludeDeleted': 'false', 'IncludeDisabled': 'true', 'HideFilterPane': 'false'}
    data['Name'] = name
    req = requests.post(url, verify=False, auth=HTTPBasicAuth(login, password), data=data)
    print('!!!!!')
    print('req.status_code')
    print(req.status_code)
    if req.status_code == 200:
        soup = BeautifulSoup(req.json()['data'], "html.parser")
        table = soup.find('div', {"class": "t-grid-content"})
        row_tr = table.find('tr')
        id_client_device = row_tr.get('id')
        print(table)
        return id_client_device


def _parsing_config_ports_client_device(id_client_device, login, password):
    """Данный метод получает на входе id коммутатора и парсит страницу с конфигом портов, чтобы получить список портконфигов"""
    url_port_config = 'https://cis.corp.itmh.ru/stu/NetSwitch/PortConfigs?switchId=' + id_client_device + '&PortGonfigsGrid-page=1'
    req_port_config = requests.get(url_port_config, verify=False, auth=HTTPBasicAuth(login, password))
    soup = BeautifulSoup(req_port_config.content.decode('utf-8'), "html.parser")
    table = soup.find('table')
    rows_tr = table.find_all('tr')
    config_ports_client_device = []
    for index, element_rows_tr in enumerate(rows_tr):
        inner_list = []
        for element_rows_td in element_rows_tr.find_all('td'):
            inner_list.append(element_rows_td.text)
        if inner_list:
            inner_list.pop(4)
            inner_list.pop(3)
            config_ports_client_device.append(inner_list)
    return config_ports_client_device

def _compare_config_ports_client_device(config_ports_client_device, main_client):
    """Данный метод на входе получает список портконфигов и номер договора, который участвует в ТР. Данный метод определяет
    какие портконфиги следует учитывать для формирования заголовка ТР."""
    extra_clients = []
    extra_name_clients = []
    for config_port in config_ports_client_device:
        print('!!!!extra_name_clients')
        print(extra_name_clients)
        if extra_name_clients:
            if config_port[2] in extra_name_clients or main_client == config_port[2]:
                pass
            else:
                extra_name_clients.append(config_port[2])
                extra_clients.append(config_port)
        else:
            if main_client == config_port[2]:
                pass
            else:
                extra_name_clients.append(config_port[2])
                extra_clients.append(config_port)
    print('!!!!extra_clients')
    print(extra_clients)
    return extra_clients

@cache_check
def forming_header(request):
    """Данный метод проверяет если клиент подключен через CSW или WDA, то проверяет наличие на этих устройтсвах других
     договоров с помощью метода _get_extra_selected_ono и если есть такие договоры, то добавляет их ресурсы в список
      выбранных ресурсов с договора. Отправляет на получение дополнительных данных если клиент подключен через цепочку
       устройств."""
    user = User.objects.get(username=request.user.username)
    credent = cache.get(user)
    username = credent['username']
    password = credent['password']
    selected_ono = request.session['selected_ono']

    selected_client = selected_ono[0][0]
    selected_device = selected_ono[0][-2]
    request.session['selected_device'] = selected_device
    request.session['selected_client'] = selected_client
    if selected_device.startswith('CSW') or selected_device.startswith('WDA'):
        extra_selected_ono = _get_extra_selected_ono(username, password, selected_device, selected_client)
        if extra_selected_ono:
            for i in extra_selected_ono:
                selected_ono.append(i)

    request.session['selected_ono'] = selected_ono
    context = {
        'ono': selected_ono,

    }
    #return render(request, 'tickets/show_resources.html', context)
    return redirect('forming_chain_header')

def _get_extra_selected_ono(username, password, selected_device, selected_client):
    extra_selected_ono = []
    id_client_device = _parsing_id_client_device_by_device_name(selected_device, username, password)
    config_ports_client_device = _parsing_config_ports_client_device(id_client_device, username, password)
    extra_clients = _compare_config_ports_client_device(config_ports_client_device, selected_client)
    if extra_clients:
        for extra_client in extra_clients:
            contract = extra_client[2]
            contract_id = get_contract_id(username, password, contract)
            extra_resources = get_contract_resources(username, password, contract_id)
            for extra_resource in extra_resources:
                if extra_resource[-2] == selected_device:
                    extra_selected_ono.append(extra_resource)
    return extra_selected_ono

def _get_all_chain(chains, chain_device, uplink, max_level):
    all_chain = []
    all_chain.append(uplink)
    if uplink:
        while uplink.startswith('CSW') or uplink.startswith('WDA'):
            next_chain_device = uplink.split()
            all_chain.pop()
            if uplink.startswith('CSW') and chain_device.startswith('WDA'):
                all_chain.append(_replace_wda_wds(chain_device))
            all_chain.append(next_chain_device[0])
            if uplink.startswith('WDA'):
                all_chain.append(_replace_wda_wds(next_chain_device[0]))
            uplink, max_level = _get_uplink(chains, next_chain_device[0], max_level)
            all_chain.append(uplink)
    return all_chain


@cache_check
def forming_chain_header(request):
    """Данный метод собирает данные обо всех устройствах через которые подключен клиент и отправляет на страницу
    формирования заголовка из этих данных"""
    user = User.objects.get(username=request.user.username)
    credent = cache.get(user)
    username = credent['username']
    password = credent['password']
    chain_device = request.session['selected_device']
    selected_ono = request.session['selected_ono']
    phone_exist = request.session['phone_exist']
    print('!!!phone_exist')
    print(phone_exist)
    print('!!chain_device')
    print(chain_device)

    chains = _get_chain_data(username, password, chain_device)
    print('!!!chains')
    print(chains)
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
        print(all_chain)

        selected_client = 'No client'
        if all_chain[0] == None:
            node_uplink = node_device
            if phone_exist:
                extra_node_device = _get_extra_node_device(chains, chain_device, node_device)
                print(extra_node_device)
                if extra_node_device:
                    for extra in extra_node_device:
                        extra_chains = _get_chain_data(username, password, extra)
                        extra_vgw = _get_vgw_on_node(extra_chains, extra)
                        print(extra_vgw)
                        if extra_vgw:
                            nodes_vgw.append(extra)
                            print(nodes_vgw)

        else:
            node_uplink = _get_node_device(chains, all_chain[-1].split()[0])
            for all_chain_device in all_chain:
                if all_chain_device.startswith('CSW'): # or all_chain_device.startswith('WDA'):
                    #extra_vgw = _get_vgw_on_node(chains, all_chain_device)
                    #node_all_chain_device = _get_node_device(chains, all_chain_device)
                    #if node_all_chain_device in nodes_vgw:
                    #    pass
                    #else:
                    extra_chains = _get_chain_data(username, password, all_chain_device)
                    extra_vgw = _get_vgw_on_node(extra_chains, all_chain_device)
                    if extra_vgw:
                        nodes_vgw.append(all_chain_device)
                    #vgws.update({node_all_chain_device: extra_vgw})
                    extra_selected_ono = _get_extra_selected_ono(username, password, all_chain_device, selected_client)
                    if extra_selected_ono:
                        for i in extra_selected_ono:
                            selected_ono.append(i)
        if downlink:
            print('!!!downlink')

            for link_device in downlink:
                #extra_vgw = _get_vgw_on_node(chains, link_device)
                #node_link_device = _get_node_device(chains, link_device)
                #if node_link_device in nodes_vgw:
                #    pass
                #else:
                extra_vgw = _get_vgw_on_node(chains, link_device)
                print('!!!extra_vgw')
                print(extra_vgw)
                if extra_vgw:
                    nodes_vgw.append(link_device)
                #vgws.update({node_link_device: extra_vgw})
                extra_selected_ono = _get_extra_selected_ono(username, password, link_device, selected_client)
                if extra_selected_ono:
                    for i in extra_selected_ono:
                        selected_ono.append(i)

        all_vgws = []
        if nodes_vgw:
            print('!!!!!nodes_vgw')
            print(nodes_vgw)
            #all_vgws = []
            for i in nodes_vgw:
                parsing_vgws = _parsing_vgws_by_node_name(i, username, password)
                print('!!!!parsing_vgws')
                print(parsing_vgws)
                for vgw in parsing_vgws:
                    all_vgws.append(vgw)
        selected_clients_for_vgw = [client[0] for client in selected_ono]
        contracts_for_vgw = list(set(selected_clients_for_vgw))
        print('!!!contracts_for_vgw')
        print(contracts_for_vgw)
        print('!!!!all_vgws')
        print(all_vgws)
        selected_vgw, waste_vgw = check_client_on_vgw(contracts_for_vgw, all_vgws, username, password)


        request.session['node_mon'] = node_uplink
        request.session['uplink'] = all_chain
        request.session['downlink'] = downlink
        request.session['vgw_chains'] = selected_vgw
        request.session['waste_vgw'] = waste_vgw
        return redirect('head')
    else:
        return redirect('no_data')

def no_data(request):
    context = {}
    return render(request, 'tickets/no_data.html', context)

def _parsing_vgws_by_node_name(device, login, password):
    """Данный метод получает на входе узел связи и по нему парсит страницу с поиском тел. шлюзов, чтобы получить
    список тел. шлюзов, подключенных от этого узла"""
    url = 'https://cis.corp.itmh.ru/stu/VoipGateway/SearchVoipGatewayProxy'
    data = {'SearchZip': 'false', 'SearchDeleted': 'false', 'ClientListRequired': 'false', 'BuildingId': '0'}
    data['Switch'] = device
    req = requests.post(url, verify=False, auth=HTTPBasicAuth(login, password), data=data)
    print('!!!!!')
    print('req.status_code')
    print(req.status_code)
    if req.status_code == 200:
        soup = BeautifulSoup(req.json()['data'], "html.parser")
        table = soup.find('table')
        rows_tr = table.find_all('tr')
        vgws = []
        types_model_vgw = ['ITM SIP', 'D-Link', 'Eltex']
        types_node_vgw = ['Узел связи', 'Помещение клиента']
        for row_tr in rows_tr:
            vgw_inner = dict()
            for row_td in row_tr.find_all('td'):
                if row_td.find('a'):
                    if row_td.find('a', {'class': "voipgateway-name"}):
                        vgw_inner.update({'name': row_td.find('a').text})
                    elif 'tab-links' in row_td.find('a').get('href'):
                        vgw_inner.update({'uplink': row_td.find('a').text})
                    elif 'tab-ports' in row_td.find('a').get('href'):
                        vgw_inner.update({'ports': row_td.find('a').get('href')})
                elif any(model in row_td.text for model in types_model_vgw):
                    vgw_inner.update({'model': row_td.text})
                elif any(room in row_td.text for room in types_node_vgw):
                    vgw_inner.update({'type': row_td.text})
            if vgw_inner:
                vgws.append(vgw_inner)

    return vgws

def check_client_on_vgw(contracts, vgws, login, password):
    """Данный метод получает на входе контракт клиента и список тел. шлюзов и проверяет наличие этого контракта
     на тел. шлюзах"""
    selected_vgw = []
    waste_vgws = []
    for vgw in vgws:
        print('!!!vgws')
        print(vgws)
        contracts_on_vgw = _parsing_config_ports_vgw(vgw.get('ports'), login, password)
        print('!!!!contracts_on_vgw')
        print(contracts_on_vgw)
        if any(contract in contracts_on_vgw for contract in contracts):
            selected_vgw.append(vgw)
        else:
            vgw.update({'contracts': contracts_on_vgw})
            waste_vgws.append(vgw)
    return selected_vgw, waste_vgws


def _parsing_config_ports_vgw(href_ports, login, password):
    """Данный метод получает на входе ссылку на портконфиги тел. шлюза и парсит страницу с конфигом портов,
     чтобы получить список договоров на этом тел. шлюзе"""
    url = 'https://cis.corp.itmh.ru' + href_ports
    req = requests.get(url, verify=False, auth=HTTPBasicAuth(login, password))
    if req.status_code == 200:
        contracts = []
        soup = BeautifulSoup(req.content.decode('utf-8'), "html.parser")
        links = soup.find_all('a')
        for i in links:
            if i.get('href') == None:
                pass
            else:
                if 'contract' in i.get('href') and i.text and i.text not in contracts:
                    contracts.append(i.text)
    return contracts

def check_contract_phone_exist(login, password, contract_id):
    """Данный метод получает ID контракта и парсит страницу Ресурсы, проверяет налиличие ресурсов Телефонный номер
    и возвращает список точек подключения, на которых есть такой ресурс"""
    url = f'https://cis.corp.itmh.ru/doc/CRM/contract.aspx?contract={contract_id}&tab=4'
    req = requests.get(url, verify=False, auth=HTTPBasicAuth(login, password))
    soup = BeautifulSoup(req.content.decode('utf-8'), "html.parser")
    table = soup.find('table', id="ctl00_middle_ResourceContent_ContractResources_RadGrid_Resources_ctl00")
    rows_td = table.find_all('td')
    print('!!!!poluch rows_td')
    pre_phone_address = []
    for index, td in enumerate(rows_td):
        try:
            if 'Телефонный номер' == td.text:
                pre_phone_address.append(index)
        except AttributeError:
            pass

    phone_address_index = list(map(lambda x: x+2, pre_phone_address))
    print('!!!poluch phone_address_index')
    phone_address = set()
    for i in phone_address_index:
        addr = ','.join(rows_td[i].text.split(',')[:2])
        print('!!!poluch addr')
        print(addr)
        phone_address.add(addr)
    print('!!!!!!phone_address')
    print(phone_address)
    phone_address = list(phone_address)
    return phone_address


def _readable(curr_value, readable_services, serv, res):
    """Данный метод формирует массив данных из услуг и реквизитов для использования в шаблонах переноса услуг"""
    if curr_value == None:
        readable_services.update({serv: f' c реквизитами "{res}"'})
    elif type(curr_value) == str:
        readable_services.update({serv: [curr_value, f' c реквизитами "{res}"']})
    elif type(curr_value) == list:
        readable_services.update({serv: curr_value.append(f' c реквизитами "{res}"')})
    return readable_services

@cache_check
def head(request):
    """Данный метод приводит данные для заголовка в читаемый формат на основе шаблона в КБЗ и отправляет на страницу
    выбора шаблонов для ТР"""
    user = User.objects.get(username=request.user.username)
    credent = cache.get(user)
    username = credent['username']
    password = credent['password']
    node_mon = request.session['node_mon']
    uplink = request.session['uplink']
    downlink = request.session['downlink']
    vgw_chains = request.session['vgw_chains']
    selected_ono = request.session['selected_ono']
    waste_vgw = request.session['waste_vgw']

    templates = ckb_parse(username, password)
    result_services = []
    static_vars = {}
    hidden_vars = {}
    stroka = templates.get("Заголовок")
    static_vars['указать номер договора'] = selected_ono[0][0]
    static_vars['указать название клиента'] = selected_ono[0][1]
    static_vars['указать точку подключения'] = selected_ono[0][3]
    node_templates = {', РУА': 'РУА ', ', УА': 'УПА ', ', АВ': 'ППС ', ', КК': 'КК '}
    for key, item in node_templates.items():
        if node_mon.endswith(key):
            finish_node = item + node_mon[:node_mon.index(key)]
    static_vars['указать узел связи'] = finish_node
    if uplink == [None]:
        static_vars['указать название коммутатора'] = selected_ono[0][-2]
        static_vars['указать порт'] = selected_ono[0][-1]
        index_of_device = stroka.index('<- порт %указать порт%>') + len('<- порт %указать порт%>') + 1
        stroka = stroka[:index_of_device] + ' \n' + stroka[index_of_device:]
    else:
        static_vars['указать название коммутатора'] = uplink[-1].split()[0]
        static_vars['указать порт'] = uplink[-1].split()[1]
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
    print('!!!!stroka s \n\n')
    print(stroka)

    service_shpd = ['DA', 'BB', 'inet', 'Inet']
    service_portvk = ['-vk', 'vk-', '- vk', 'vk -']
    service_portvm = ['-vrf', 'vrf-', '- vrf', 'vrf -']
    service_hotspot = ['hotspot']
    service_itv = ['itv']
    list_stroka_main_client_service = []
    list_stroka_other_client_service = []
    readable_services = dict()
    counter_exist_line = set()
    for i in selected_ono:
        if selected_ono[0][0] == i[0]:
            print('!!!before any head')
            if i[2] == 'IP-адрес или подсеть':
                if any(serv in i[-3] for serv in service_shpd):
                    print('!!!any head')
                    extra_stroka_main_client_service = f'- услугу "ШПД в интернет" c реквизитами "{i[-4]}"({i[-2]} {i[-1]})\n'
                    print(extra_stroka_main_client_service)
                    if list_stroka_main_client_service:
                        for ind, main in enumerate(list_stroka_main_client_service):
                            if i[-1] in main:
                                main = main[:main.index('"(')] + f', услугу "ШПД в интернет" c реквизитами "{i[-4]}"' + main[main.index('"('):]
                    list_stroka_main_client_service.append(extra_stroka_main_client_service)
                    curr_value = readable_services.get('"ШПД в интернет"')
                    readable_services = _readable(curr_value, readable_services, '"ШПД в интернет"', i[-4])
                    counter_exist_line.add(f'{i[-2]} {i[-1]}')
                    #if curr_value == None:
                    #    readable_services.update({'"ШПД в интернет"': f' c реквизитами "{i[-4]}"'})
                    #elif type(curr_value) == str:
                    #    readable_services.update({'"ШПД в интернет"': [curr_value, f' c реквизитами "{i[-4]}"']})
                    #elif type(curr_value) == list:
                    #    readable_services.update({'"ШПД в интернет"': curr_value.append(f' c реквизитами "{i[-4]}"')})
                    #readable_services.update({'"ШПД в интернет"': f' c реквизитами "{i[-4]}"'})
                elif any(serv in i[-3].lower() for serv in service_hotspot):
                    extra_stroka_main_client_service = f'- услугу "Хот-спот" c реквизитами "{i[-4]}"({i[-2]} {i[-1]})\n'
                    print(extra_stroka_main_client_service)
                    list_stroka_main_client_service.append(extra_stroka_main_client_service)
                    #readable_services.update({'"Хот-спот"': f' c реквизитами "{i[-4]}"'})
                    curr_value = readable_services.get('"Хот-спот"')
                    readable_services = _readable(curr_value, readable_services, '"Хот-спот"', i[-4])
                    counter_exist_line.add(f'{i[-2]} {i[-1]}')
                elif any(serv in i[-3].lower() for serv in service_itv):
                    extra_stroka_main_client_service = f'- услугу "Вебург.ТВ" c реквизитами "{i[-4]}"({i[-2]} {i[-1]})\n'
                    print(extra_stroka_main_client_service)
                    list_stroka_main_client_service.append(extra_stroka_main_client_service)
                    #readable_services.update({'"Вебург.ТВ"': f' c реквизитами "{i[-4]}"'})
                    curr_value = readable_services.get('"Вебург.ТВ"')
                    readable_services = _readable(curr_value, readable_services, '"Вебург.ТВ"', i[-4])
                    counter_exist_line.add(f'{i[-2]} {i[-1]}')
            elif i[2] == 'Порт виртуального коммутатора':
                if any(serv in i[-3].lower() for serv in service_portvk):
                    extra_stroka_main_client_service = f'- услугу "Порт ВЛС" "{i[4]}"({i[-2]} {i[-1]})\n'
                    list_stroka_main_client_service.append(extra_stroka_main_client_service)
                    #readable_services.update({'"Порт ВЛС"': f' "{i[-4]}"'})
                    curr_value = readable_services.get('"Порт ВЛС"')
                    readable_services = _readable(curr_value, readable_services, '"Порт ВЛС"', i[-4])
                    counter_exist_line.add(f'{i[-2]} {i[-1]}')
                elif any(serv in i[-3].lower() for serv in service_portvm):
                    extra_stroka_main_client_service = f'- услугу "Порт ВМ" "{i[4]}"({i[-2]} {i[-1]})\n'
                    list_stroka_main_client_service.append(extra_stroka_main_client_service)
                    #readable_services.update({'"Порт ВМ"': f' "{i[-4]}"'})
                    curr_value = readable_services.get('"Порт ВМ"')
                    readable_services = _readable(curr_value, readable_services, '"Порт ВМ"', i[-4])
                    counter_exist_line.add(f'{i[-2]} {i[-1]}')
            elif i[2] == 'Etherline':
                extra_stroka_main_client_service = f'- услугу "ЦКС" "{i[4]}"({i[-2]} {i[-1]})\n'
                list_stroka_main_client_service.append(extra_stroka_main_client_service)
                #readable_services.update({'"ЦКС"': f' "{i[-4]}"'})
                curr_value = readable_services.get('"ЦКС"')
                readable_services = _readable(curr_value, readable_services, '"ЦКС"', i[-4])
                counter_exist_line.add(f'{i[-2]} {i[-1]}')
        else:
            if i[2] == 'IP-адрес или подсеть':
                if any(serv in i[-3] for serv in service_shpd):
                    print('!!!any head')
                    extra_stroka_other_client_service = f'- услугу "ШПД в интернет" c реквизитами "{i[-4]}"({i[-2]} {i[-1]}) по договору {i[0]} {i[1]}\n'
                    print(extra_stroka_other_client_service)
                    list_stroka_other_client_service.append(extra_stroka_other_client_service)
                    counter_exist_line.add(f'{i[-2]} {i[-1]}')
                elif any(serv in i[-3].lower() for serv in service_hotspot):
                    extra_stroka_other_client_service = f'- услугу "Хот-спот" c реквизитами "{i[-4]}"({i[-2]} {i[-1]}) по договору {i[0]} {i[1]}\n'
                    print(extra_stroka_other_client_service)
                    list_stroka_other_client_service.append(extra_stroka_other_client_service)
                    counter_exist_line.add(f'{i[-2]} {i[-1]}')
                elif any(serv in i[-3].lower() for serv in service_itv):
                    extra_stroka_other_client_service = f'- услугу "Вебург.ТВ" c реквизитами "{i[-4]}"({i[-2]} {i[-1]}) по договору {i[0]} {i[1]}\n'
                    print(extra_stroka_other_client_service)
                    list_stroka_other_client_service.append(extra_stroka_other_client_service)
                    counter_exist_line.add(f'{i[-2]} {i[-1]}')
            elif i[2] == 'Порт виртуального коммутатора':
                if any(serv in i[-3].lower() for serv in service_portvk):
                    extra_stroka_other_client_service = f'- услугу "Порт ВЛС" "{i[4]}"({i[-2]} {i[-1]}) по договору {i[0]} {i[1]}\n'
                    list_stroka_other_client_service.append(extra_stroka_other_client_service)
                    counter_exist_line.add(f'{i[-2]} {i[-1]}')
                elif any(serv in i[-3].lower() for serv in service_portvm):
                    extra_stroka_other_client_service = f'- услугу "Порт ВМ" "{i[4]}"({i[-2]} {i[-1]}) по договору {i[0]} {i[1]}\n'
                    list_stroka_other_client_service.append(extra_stroka_other_client_service)
                    counter_exist_line.add(f'{i[-2]} {i[-1]}')
            elif i[2] == 'Etherline':
                extra_stroka_other_client_service = f'- услугу "ЦКС" "{i[4]}"({i[-2]} {i[-1]}) по договору {i[0]} {i[1]}\n'
                list_stroka_other_client_service.append(extra_stroka_other_client_service)
                counter_exist_line.add(f'{i[-2]} {i[-1]}')


    if vgw_chains:
        for i in vgw_chains:
            model = i.get('model')
            name = i.get('name')
            vgw_uplink = i.get('uplink').replace('\r\n', '')
            room = i.get('type')
            if model == 'ITM SIP':
                extra_stroka_main_client_service = f'- услугу "Телефония" через IP-транк {name} ({vgw_uplink})'
                counter_exist_line.add(f'{vgw_uplink}')
            else:
                extra_stroka_main_client_service = f'- услугу "Телефония" через тел. шлюз {model} {name} ({vgw_uplink}). Место установки: {room}\n'
                counter_exist_line.add(f'{vgw_uplink}')
            list_stroka_main_client_service.append(extra_stroka_main_client_service)
            readable_services.update({'"Телефония"': None})
    extra_extra_stroka_main_client_service = ''.join(list_stroka_main_client_service)
    extra_extra_stroka_other_client_service = ''.join(list_stroka_other_client_service)
    index_of_service = stroka.index('В данной точке клиент потребляет:') + len('В данной точке клиент потребляет:')+1
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
            stroka = stroka[:stroka.index('Требуется')] + extra_stroka_other_vgw + '\n' + stroka[stroka.index('Требуется'):]

    counter_exist_line = len(counter_exist_line)
    if ((not selected_ono[0][-2].startswith('CSW')) or (not selected_ono[0][-2].startswith('WDA'))) and counter_exist_line > 1:
        pass
    else:
        hidden_vars['- порт %указать порт%'] = '- порт %указать порт%'

    result_services.append(analyzer_vars(stroka, static_vars, hidden_vars))

    result_services = ''.join(result_services)
    rev_result_services = result_services[::-1]
    index_of_head = rev_result_services.index('''-----------------------------------------------------------------------------------\n''')
    rev_result_services = rev_result_services[:index_of_head]
    head = rev_result_services[::-1]
    request.session['head'] = head.strip()
    request.session['readable_services'] = readable_services
    print('!!!!readable_services')
    print(readable_services)
    request.session['counter_exist_line'] = counter_exist_line


    context = {
        'result_services': result_services,
        'node_mon': node_mon,
        'uplink': uplink,
        'downlink': downlink,
        'vgw_chains': vgw_chains,
        'selected_ono': selected_ono,
        'waste_vgw': waste_vgw
    }
    #return render(request, 'tickets/head.html', context)
    #return redirect('passage')
    return redirect('job_formset')

def passage(request):
    """Данный метод выводит страницу с выбором шаблонов ТР в КБЗ"""
    if request.method == 'POST':
        passform = PassForm(request.POST)

        if passform.is_valid():
            type_pass = passform.cleaned_data['type_pass']
            print('!!!!! type_pass')
            print(type_pass)
            request.session['type_pass'] = type_pass
            return redirect('project_tr_exist_cl')


    else:
        head = request.session['head']
        ticket_tr_id = request.session['ticket_tr_id']
        ticket_tr = TR.objects.get(id=ticket_tr_id)
        oattr = ticket_tr.oattr
        pps = ticket_tr.pps
        turnoff = ticket_tr.turnoff
        #task_otpm = ticket_tr.ticket_k.task_otpm
        passform = PassForm(initial={'type_pass': 'Перенос сервиса'})
        context = {
            'passform': passform,
            'head': head,
            'oattr': oattr,
            'pps': pps,
            'turnoff': turnoff,
            #'task_otpm': task_otpm
        }
        return render(request, 'tickets/choice_pass.html', context)


@cache_check
def add_tr_exist_cl(request, dID, tID, trID):
    """Данный метод получает параметры ТР в СПП(dID, tID, trID), вызывает методы for_tr_view и add_tr_to_db. В случае
     недоступности данных(for_tr_view) оправляет логиниться. В случае если ТР добавлено в АРМ(add_tr_to_db) отправляет
    на запрос контракта клиента"""
    user = User.objects.get(username=request.user.username)
    credent = cache.get(user)
    username = credent['username']
    password = credent['password']
    tr_params = for_tr_view(username, password, dID, tID, trID)
    print('!!!!!tr_params')
    print(tr_params)
    if tr_params.get('Access denied') == 'Access denied':
        messages.warning(request, 'Нет доступа в ИС Холдинга')
        response = redirect('login_for_service')
        response['Location'] += '?next={}'.format(request.path)
        return response
    else:
        ticket_spp_id = request.session['ticket_spp_id']
        ticket_tr_id = add_tr_to_db(dID, trID, tr_params, ticket_spp_id)
        spplink = 'https://sss.corp.itmh.ru/dem_tr/dem_begin.php?dID={}&tID={}&trID={}'.format(dID, tID, trID)
        request.session['spplink'] = spplink
        request.session['ticket_tr_id'] = ticket_tr_id
        print(request.GET)

        return redirect('get_resources')


def project_tr_exist_cl(request):
    # elif data_sss[2] == 'Не выбран':
    #    return redirect('tr_view', dID, tID, trID)


    #type_pass = request.session['type_pass']
    ticket_tr_id = request.session['ticket_tr_id']
    ticket_tr = TR.objects.get(id=ticket_tr_id)
    oattr = ticket_tr.oattr
    pps = ticket_tr.pps
    pps = pps.strip()
    turnoff = ticket_tr.turnoff
    services_plus_desc = ticket_tr.services
    points_for_cks = ticket_tr.ticket_k.des_tr
    cks_points = []
    for point in points_for_cks:
        if next(iter(point.keys())).startswith('г.'):
            cks_points.append(next(iter(point.keys())).split('ул.')[1])
    print('!!!!points_for_cks')
    print(points_for_cks)
    request.session['cks_points'] = cks_points
    request.session['services_plus_desc'] = services_plus_desc
    request.session['pps'] = pps
    if oattr:
        request.session['oattr'] = oattr
        wireless_temp = ['БС ', 'радио', 'радиоканал', 'антенну']
        ftth_temp = ['Alpha', 'ОК-1']
        vols_temp = ['ОВ', 'ОК', 'ВОЛС', 'волокно', 'ОР ', 'ОР№', 'сущ.ОМ', 'оптическ']
        if any(wl in oattr for wl in wireless_temp) and (not 'ОК' in oattr):
            sreda = '3'
            print('Среда передачи:  Беспроводная среда')
        elif any(ft in oattr for ft in ftth_temp) and (not 'ОК-16' in oattr):
            sreda = '4'
            print('Среда передачи: FTTH')
        elif any(vo in oattr for vo in vols_temp):
            sreda = '2'
            print('Среда передачи: ВОЛС')
        else:
            sreda = '1'
            print('Среда передачи: UTP')
    else:
        request.session['oattr'] = None
    selected_ono = request.session['selected_ono']
    new_without_csw_job_services = request.session['new_without_csw_job_services']
    new_with_csw_job_services = request.session['new_with_csw_job_services']
    pass_without_csw_job_services = request.session['pass_without_csw_job_services']
    pass_with_csw_job_services = request.session['pass_with_csw_job_services']


    new_no_spd_jobs_services = request.session['new_no_spd_jobs_services']
    pass_no_spd_job_services = request.session['pass_no_spd_job_services']
    change_job_services = request.session['change_job_services']

    #перенос одного сервиса
    #if pass_without_csw_job_services
    #all_job_spd.remove(pass_without_csw_job_services)
    #if not all(all_job_spd):
    #    if selected_ono[0][-2].startswith('CSW'):
    #        pass # перенести только этот сервис
    #    else:
    type_tr = 'new_cl'
    type_pass = []
    tag_service = []
    if pass_without_csw_job_services:
        type_pass.append('Перенос существующих сервисов')


        tag_service.append({'pass_serv': None})
        #if sreda == '1':
        #    tag_service.append({'copper': None})
        #elif sreda == '2' or sreda == '4':
        #    tag_service.append({'vols': None})
        #lif sreda == '3':
        #    tag_service.append({'wireless': None})
        #return redirect(next(iter(tag_service[0])))
    #перенос существующих сервисов и организация нов сервисов отдельными линиями

    if new_without_csw_job_services:
        type_pass = 'Организация доп.услуги без установки КК'

        tags, hotspot_users, premium_plus = _tag_service_for_new_serv(new_without_csw_job_services)
        counter_line_services, hotspot_points = _counter_line_services(new_without_csw_job_services)
        for tag in tags:
            tag_service.append(tag)

        request.session['hotspot_points'] = hotspot_points
        request.session['hotspot_users'] = hotspot_users
        request.session['premium_plus'] = premium_plus
        request.session['services_plus_desc'] = services_plus_desc


        request.session['counter_line_services'] = counter_line_services




        #if not pass_without_csw_job_services and not new_with_csw_job_services and :
        if counter_line_services > 0:
            if sreda == '1':
                tag_service.append({'copper': None})
            elif sreda == '2' or sreda == '4':
                tag_service.append({'vols': None})
            elif sreda == '3':
                tag_service.append({'wireless': None})
        print('!!!check new_with_csw_job_services')
        print(type(new_with_csw_job_services))
        print('!!!check pass_without_csw_job_services')
        print(type(pass_without_csw_job_services))



    # перенос существующих сервисов и организация нов сервисов через новый КК
    if new_with_csw_job_services:
        type_pass.append('Организация доп.услуги с установкой КК')
        tags, hotspot_users, premium_plus = _tag_service_for_new_serv(new_with_csw_job_services)
        tag_service.append({'add_serv_with_install_csw': None})
        for tag in tags:
            tag_service.append(tag)
        counter_line_services, hotspot_points = _counter_line_services(new_with_csw_job_services)
        #tag_service.insert(0, {'add_serv_with_install_csw': None})

        request.session['hotspot_points'] = hotspot_points
        request.session['hotspot_users'] = hotspot_users
        request.session['premium_plus'] = premium_plus
        request.session['services_plus_desc'] = services_plus_desc


        request.session['counter_line_services'] = counter_line_services
    if new_no_spd_jobs_services:
        type_pass.append('Организация сервиса(не СПД)')
        tags, hotspot_users, premium_plus = _tag_service_for_new_serv(new_no_spd_jobs_services)
        for tag in tags:
            tag_service.append(tag)



    request.session['type_tr'] = type_tr
    request.session['oattr'] = oattr
    request.session['pps'] = pps
    request.session['turnoff'] = turnoff
    request.session['sreda'] = sreda
    request.session['type_pass'] = type_pass
    request.session['tag_service'] = tag_service
    return redirect(next(iter(tag_service[0])))



    """if type_pass == 'Изменение/организация сервисов без монтаж. работ':
        tag_service, hotspot_users, premium_plus = _tag_service_for_new_serv(services_plus_desc)
        tag_service.insert(0, {'change_serv': None})

        type_tr = 'new_cl'
        request.session['type_tr'] = type_tr
        request.session['tag_service'] = tag_service
        print('!!!!!tagsevice')
        print(tag_service)
        return redirect(next(iter(tag_service[0])))
    elif type_pass == 'Организация доп. услуги с установкой КК':
        #tag_service.append('add_serv_to_cur_csw')
        tag_service, hotspot_users, premium_plus = _tag_service_for_new_serv(services_plus_desc)
        counter_line_services, hotspot_points = _counter_line_services(services_plus_desc)
        tag_service.insert(0, {'add_serv_with_install_csw': None})

        request.session['hotspot_points'] = hotspot_points
        request.session['hotspot_users'] = hotspot_users
        request.session['premium_plus'] = premium_plus
        request.session['services_plus_desc'] = services_plus_desc
        request.session['oattr'] = oattr
        request.session['pps'] = pps
        request.session['turnoff'] = turnoff
        request.session['sreda'] = sreda
        request.session['counter_line_services'] = counter_line_services


        type_tr = 'new_cl'
        request.session['type_tr'] = type_tr
        request.session['tag_service'] = tag_service
        print('!!!!!tagsevice')
        print(tag_service)
        return redirect(next(iter(tag_service[0])))
    elif type_pass == 'Перенос существующих сервисов':
        type_tr = 'new_cl'
        tag_service = []
        tag_service.append({'pass_serv': None})
        if sreda == '1':
            tag_service.append({'copper': None})
        elif sreda == '2' or sreda == '4':
            tag_service.append({'vols': None})
        elif sreda == '3':
            tag_service.append({'wireless': None})
        request.session['oattr'] = oattr
        request.session['pps'] = pps
        request.session['turnoff'] = turnoff
        request.session['type_tr'] = type_tr
        request.session['sreda'] = sreda
        request.session['services_plus_desc'] = services_plus_desc
        request.session['tag_service'] = tag_service

        return redirect(next(iter(tag_service[0])))
    else:
        type_tr = 'exist_cl'
        tag_service = []

        if type_pass == 'Перенос сервиса':
            tag_service.append({'pass_serv': None})
        elif type_pass == 'Организация доп. услуги от существующего КК':
            tag_service.append({'add_serv_to_cur_csw': None})

        if sreda == '1':
            tag_service.append({'copper': None})
        elif sreda == '2' or sreda == '4':
            tag_service.append({'vols': None})
        elif sreda == '3':
            tag_service.append({'wireless': None})

        tag_service.append({'exist_cl_data': None})

        request.session['services_plus_desc'] = services_plus_desc
        request.session['oattr'] = oattr
        request.session['pps'] = pps
        request.session['turnoff'] = turnoff
        request.session['type_tr'] = type_tr
        request.session['sreda'] = sreda
        request.session['tag_service'] = tag_service

        return redirect(next(iter(tag_service[0])))"""


def add_serv(request):
    variables = ['port', 'logic_csw', 'device_pps', 'access_point', 'speed_port', 'device_client', 'list_switches',
                 'router_shpd',
                 'type_shpd', 'type_cks', 'type_portvk', 'type_portvm', 'policer_vk', 'new_vk', 'exist_vk', 'model_csw',
                 'port_csw',
                 'logic_csw_1000', 'pointA', 'pointB', 'policer_cks', 'policer_vm', 'new_vm', 'exist_vm', 'vm_inet',
                 'hotspot_points',
                 'hotspot_users', 'exist_hotspot_client', 'camera_number', 'camera_model', 'voice', 'deep_archive',
                 'camera_place_one', 'camera_place_two',
                 'vgw', 'channel_vgw', 'ports_vgw', 'local_type', 'local_ports', 'sks_poe', 'sks_router', 'lvs_busy',
                 'lvs_switch',
                 'ppr', 'type_itv', 'cnt_itv']
    value_vars = dict()

    for i in variables:
        try:
            request.session[i]
        except KeyError:
            value_vars.update({i: None})
        else:
            value_vars.update({i: request.session[i]})



    return redirect('no_data')



def pass_serv(request):
    if request.method == 'POST':
        passservform = PassServForm(request.POST)

        if passservform.is_valid():
            from_node = passservform.cleaned_data['from_node']
            log_change = passservform.cleaned_data['log_change']
            request.session['from_node'] = from_node
            request.session['log_change'] = log_change
            tag_service = request.session['tag_service']
            sreda = request.session['sreda']
            tag_service.pop(0)
            if log_change == False:
                #if sreda == '1':
                #    tag_service.remove('copper')
                #elif sreda == '2' or sreda == '4':
                #    tag_service.remove('vols')
                #tag_service.pop()
                pass

            else:
                if sreda == '1':
                    tag_service.append({'copper': None})
                elif sreda == '2' or sreda == '4':
                    tag_service.append({'vols': None})
                elif sreda == '3':
                    tag_service.append({'wireless': None})
            if len(tag_service) == 0:
                tag_service.append({'data': None})

            return redirect(next(iter(tag_service[0])))


    else:
        passservform = PassServForm()
        context = {
            'passservform': passservform
        }

        return render(request, 'tickets/pass_serv.html', context)


def _passage_services(result_services, value_vars):
    templates = value_vars.get('templates')
    sreda = value_vars.get('sreda')
    readable_services = value_vars.get('readable_services')
    stroka = templates.get("Перенос сервиса %указать название сервиса%")
    if stroka:
        static_vars = {}
        hidden_vars = {}

        static_vars['указать название сервиса'] = ', '.join(readable_services.keys())
        if sreda == '2' or sreda == '4':
            static_vars['ОИПМ/ОИПД'] = 'ОИПМ'
        else:
            static_vars['ОИПМ/ОИПД'] = 'ОИПД'
        if value_vars.get('log_change'):
            hidden_vars[
                '-- перенести сервис %указать сервис% для клиента в новую точку подключения.'] = '-- перенести сервис %указать сервис% для клиента в новую точку подключения.'
            services = []
            for key, value in readable_services.items():
                if type(value) == str:
                    services.append(key + ' ' + value)
                elif type(value) == list:
                    services.append(key + ''.join(value))
            static_vars['указать сервис'] = ', '.join(services)
            hidden_vars[
                'В заявке Cordis указать время проведения работ по переносу сервиса.'] = 'В заявке Cordis указать время проведения работ по переносу сервиса.'
            hidden_vars[
                '- После переезда клиента актуализировать информацию в Cordis и системах учета.'] = '- После переезда клиента актуализировать информацию в Cordis и системах учета.'
            hidden_vars[
                '- Сообщить в ОЛИ СПД об освободившемся порте на коммутаторе %указать существующий КАД% после переезда клиента.'] = '- Сообщить в ОЛИ СПД об освободившемся порте на коммутаторе %указать существующий КАД% после переезда клиента.'
            static_vars['указать существующий КАД'] = value_vars.get('head').split('\n')[4].split()[2]

        result_services.append(analyzer_vars(stroka, static_vars, hidden_vars))
    return result_services

def _passage_enviroment(value_vars):
    if value_vars.get('result_services'):
        result_services = value_vars.get('result_services')
    else:
        result_services = []
    sreda = value_vars.get('sreda')
    templates = value_vars.get('templates')
    pps = _readable_node(value_vars.get('pps'))
    port = value_vars.get('port')
    if value_vars.get('log_change'):
        kad, value_vars = _list_kad(value_vars)
    else:
        kad = value_vars.get('selected_ono')[0][-2]


    static_vars = {}
    hidden_vars = {}
    if sreda == '1':
        print("Перенос присоединения к СПД по медной линии связи." + '-' * 20)
        stroka = templates.get("Перенос присоединения к СПД по медной линии связи.")
        if value_vars.get('from_node'):
            hidden_vars[' от %указать узел связи%'] = ' от %указать узел связи%'
            static_vars['указать узел связи'] = pps
        if value_vars.get('oattr'):
            hidden_vars[' по решению ОАТТР'] = ' по решению ОАТТР'
        if value_vars.get('log_change'):
            hidden_vars[
                '- Подключить организованную линию для клиента в коммутатор %указать название коммутатора%, порт выбрать %указать порт коммутатора%.'] = '- Подключить организованную линию для клиента в коммутатор %указать название коммутатора%, порт выбрать %указать порт коммутатора%.'
            hidden_vars[' от %указать узел связи%'] = ' от %указать узел связи%'
            static_vars['указать узел связи'] = pps
            static_vars['указать название коммутатора'] = kad
            static_vars['указать порт коммутатора'] = port
            static_vars['изменится/не изменится'] = 'изменится'
        else:
            static_vars['изменится/не изменится'] = 'не изменится'
        result_services.append(analyzer_vars(stroka, static_vars, hidden_vars))
    elif sreda == '2' or sreda == '4':
        if value_vars.get('ppr'):
            print('-' * 20 + '\n' + "Перенос присоединения к СПД по оптической линии связи с простоем связи услуг.")
            stroka = templates.get("Перенос присоединения к СПД по оптической линии связи с простоем связи услуг.")
            static_vars['указать № ППР'] = value_vars.get('ppr')
            hidden_vars[
                '- На порту подключения клиента выставить скоростной режим %указать режим работы порта%.'] = '- На порту подключения клиента выставить скоростной режим %указать режим работы порта%.'
        else:
            print('-' * 20 + '\n' + "Перенос присоединения к СПД по оптической линии связи.")
            stroka = templates.get("Перенос присоединения к СПД по оптической линии связи.")

        if value_vars.get('from_node'):
            hidden_vars[' от %указать узел связи%'] = ' от %указать узел связи%'
            static_vars['указать узел связи'] = pps
        if value_vars.get('log_change'):
            hidden_vars[
                '- Подключить организованную линию для клиента в коммутатор %указать название коммутатора%, порт выбрать %указать порт коммутатора%.'] = '- Подключить организованную линию для клиента в коммутатор %указать название коммутатора%, порт выбрать %указать порт коммутатора%.'
            hidden_vars[' от %указать узел связи%'] = ' от %указать узел связи%'
            hidden_vars['ОНИТС СПД проведение работ:'] = 'ОНИТС СПД проведение работ:'
            hidden_vars[
                '- На порту подключения клиента выставить скоростной режим %указать режим работы порта%.'] = '- На порту подключения клиента выставить скоростной режим %указать режим работы порта%.'
            static_vars['указать узел связи'] = pps
            static_vars['указать название коммутатора'] = kad
            static_vars['указать порт коммутатора'] = port
            static_vars['изменится/не изменится'] = 'изменится'
            static_vars['указать режим работы порта'] = value_vars.get('speed_port')
            static_vars['указать конвертер/передатчик на стороне узла связи'] = value_vars.get('device_pps')
            static_vars['указать конвертер/передатчик на стороне клиента'] = value_vars.get('device_client')
        else:
            static_vars['изменится/не изменится'] = 'не изменится'
        result_services.append(analyzer_vars(stroka, static_vars, hidden_vars))
    elif sreda == '3':
        print("Присоединение к СПД по беспроводной среде передачи данных.")
        static_vars = {}
        if value_vars.get('ppr'):
            print('-' * 20 + '\n' + "Присоединение к СПД по беспроводной среде передачи данных с простоем связи услуг.")
            stroka = templates.get("Присоединение к СПД по беспроводной среде передачи данных с простоем связи услуг.")
            static_vars['указать № ППР'] = value_vars.get('ppr')
        else:
            print('-' * 20 + '\n' + "Присоединение к СПД по беспроводной среде передачи данных.")
            stroka = templates.get("Присоединение к СПД по беспроводной среде передачи данных.")
        hidden_vars = {}
        static_vars['указать узел связи'] = pps
        static_vars['указать название коммутатора'] = kad

        static_vars['указать порт коммутатора'] = port
        static_vars['указать модель беспроводных точек'] = value_vars.get('access_point')
        if value_vars.get('access_point') == 'Infinet H11':
            hidden_vars[
                '- Доставить в офис ОНИТС СПД беспроводные точки Infinet H11 для их настройки.'] = '- Доставить в офис ОНИТС СПД беспроводные точки Infinet H11 для их настройки.'
            hidden_vars[' и настройки точек в офисе ОНИТС СПД'] = ' и настройки точек в офисе ОНИТС СПД'

        result_services.append(analyzer_vars(stroka, static_vars, hidden_vars))
    value_vars.update({'kad': kad})
    return result_services, value_vars


@cache_check
def exist_cl_data(request):
    user = User.objects.get(username=request.user.username)
    credent = cache.get(user)
    username = credent['username']
    password = credent['password']
    pps = request.session['pps']
    #services_plus_desc = request.session['services_plus_desc']
    #turnoff = request.session['turnoff']
    sreda = request.session['sreda']
    readable_services = request.session['readable_services']
    oattr = request.session['oattr']
    selected_ono = request.session['selected_ono']
    head = request.session['head']


    templates = ckb_parse(username, password)


    try:
        port = request.session['port']
    except KeyError:
        port = None
    try:
        logic_csw = request.session['logic_csw']
    except KeyError:
        logic_csw = None
    try:
        from_node = request.session['from_node']
    except KeyError:
        from_node = None
    try:
        log_change = request.session['log_change']
    except KeyError:
        log_change = None
    try:
        list_switches = request.session['list_switches']
    except KeyError:
        list_switches = None
    try:
        speed_port = request.session['speed_port']
    except KeyError:
        speed_port = None
    try:
        device_pps = request.session['device_pps']
    except KeyError:
        device_pps = None
    try:
        device_client = request.session['device_client']
    except KeyError:
        device_client = None
    try:
        ppr = request.session['ppr']
    except KeyError:
        ppr = None
    try:
        access_point = request.session['access_point']
    except KeyError:
        access_point = None

    if list_switches:
        list_kad = []
        if len(list_switches) == 1:
            kad = list_switches[0][0]
        else:
            for i in range(len(list_switches)):
                if (list_switches[i][0].startswith('IAS')) or (list_switches[i][0].startswith('AR')):
                    pass
                else:
                    list_kad.append(list_switches[i][0])
            kad = ' или '.join(list_kad)

    static_vars = {}
    hidden_vars = {}
    result_services = []
    if sreda == '1':
        print("Перенос присоединения к СПД по медной линии связи." + '-' * 20)
        stroka = templates.get("Перенос присоединения к СПД по медной линии связи.")
        if from_node:
            hidden_vars[' от %указать узел связи%'] = ' от %указать узел связи%'
            static_vars['указать узел связи'] = pps
        if oattr:
            hidden_vars[' по решению ОАТТР'] = ' по решению ОАТТР'
        if log_change:
            hidden_vars['- Подключить организованную линию для клиента в коммутатор %указать название коммутатора%, порт выбрать %указать порт коммутатора%.'] = '- Подключить организованную линию для клиента в коммутатор %указать название коммутатора%, порт выбрать %указать порт коммутатора%.'
            hidden_vars[' от %указать узел связи%'] = ' от %указать узел связи%'
            static_vars['указать узел связи'] = pps
            static_vars['указать название коммутатора'] = kad
            static_vars['указать порт коммутатора'] = port
            static_vars['изменится/не изменится'] = 'изменится'
        else:
            static_vars['изменится/не изменится'] = 'не изменится'
        result_services.append(analyzer_vars(stroka, static_vars, hidden_vars))
    elif sreda == '2' or sreda == '4':
        if ppr:
            print('-' * 20 + '\n' + "Перенос присоединения к СПД по оптической линии связи с простоем связи услуг.")
            stroka = templates.get("Перенос присоединения к СПД по оптической линии связи с простоем связи услуг.")
            static_vars['указать № ППР'] = ppr
            hidden_vars['- На порту подключения клиента выставить скоростной режим %указать режим работы порта%.'] = '- На порту подключения клиента выставить скоростной режим %указать режим работы порта%.'
        else:
            print('-' * 20 + '\n' + "Перенос присоединения к СПД по оптической линии связи.")
            stroka = templates.get("Перенос присоединения к СПД по оптической линии связи.")

        if from_node:
            hidden_vars[' от %указать узел связи%'] = ' от %указать узел связи%'
            static_vars['указать узел связи'] = pps
        if log_change:
            hidden_vars[
                '- Подключить организованную линию для клиента в коммутатор %указать название коммутатора%, порт выбрать %указать порт коммутатора%.'] = '- Подключить организованную линию для клиента в коммутатор %указать название коммутатора%, порт выбрать %указать порт коммутатора%.'
            hidden_vars[' от %указать узел связи%'] = ' от %указать узел связи%'
            hidden_vars['ОНИТС СПД проведение работ:'] = 'ОНИТС СПД проведение работ:'
            hidden_vars['- На порту подключения клиента выставить скоростной режим %указать режим работы порта%.'] = '- На порту подключения клиента выставить скоростной режим %указать режим работы порта%.'
            static_vars['указать узел связи'] = pps
            static_vars['указать название коммутатора'] = kad
            static_vars['указать порт коммутатора'] = port
            static_vars['изменится/не изменится'] = 'изменится'
            static_vars['указать режим работы порта'] = speed_port
            static_vars['указать конвертер/передатчик на стороне узла связи'] = device_pps
            static_vars['указать конвертер/передатчик на стороне клиента'] = device_client
        else:
            static_vars['изменится/не изменится'] = 'не изменится'
        result_services.append(analyzer_vars(stroka, static_vars, hidden_vars))
    elif sreda == '3':
        print("Присоединение к СПД по беспроводной среде передачи данных.")
        static_vars = {}
        if ppr:
            print('-' * 20 + '\n' + "Присоединение к СПД по беспроводной среде передачи данных с простоем связи услуг.")
            stroka = templates.get("Присоединение к СПД по беспроводной среде передачи данных с простоем связи услуг.")
            static_vars['указать № ППР'] = ppr
        else:
            print('-' * 20 + '\n' + "Присоединение к СПД по беспроводной среде передачи данных.")
            stroka = templates.get("Присоединение к СПД по беспроводной среде передачи данных.")
        hidden_vars = {}
        static_vars['указать узел связи'] = pps
        static_vars['указать название коммутатора'] = kad

        static_vars['указать порт коммутатора'] = port
        static_vars['указать модель беспроводных точек'] = access_point
        if access_point == 'Infinet H11':
            hidden_vars['- Доставить в офис ОНИТС СПД беспроводные точки Infinet H11 для их настройки.'] = '- Доставить в офис ОНИТС СПД беспроводные точки Infinet H11 для их настройки.'
            hidden_vars[' и настройки точек в офисе ОНИТС СПД'] = ' и настройки точек в офисе ОНИТС СПД'

        result_services.append(analyzer_vars(stroka, static_vars, hidden_vars))
    print("Перенос сервиса %указать название сервиса%" + '-' * 20)
    stroka = templates.get("Перенос сервиса %указать название сервиса%")
    if stroka:
        static_vars = {}
        hidden_vars = {}


        static_vars['указать название сервиса'] = ', '.join(readable_services.keys())
        if sreda == '2' or sreda == '4':
            static_vars['ОИПМ/ОИПД'] = 'ОИПМ'
        else:
            static_vars['ОИПМ/ОИПД'] = 'ОИПД'
        if log_change:
            hidden_vars['-- перенести сервис %указать сервис% для клиента в новую точку подключения.'] = '-- перенести сервис %указать сервис% для клиента в новую точку подключения.'
            services = []
            for key, value in readable_services.items():
                if type(value) == str:
                    services.append(key+' '+value)
                elif type(value) == list:
                    services.append(key+''.join(value))
            static_vars['указать сервис'] = ', '.join(services)
            hidden_vars['В заявке Cordis указать время проведения работ по переносу сервиса.'] = 'В заявке Cordis указать время проведения работ по переносу сервиса.'
            hidden_vars['- После переезда клиента актуализировать информацию в Cordis и системах учета.'] = '- После переезда клиента актуализировать информацию в Cordis и системах учета.'
            hidden_vars['- Сообщить в ОЛИ СПД об освободившемся порте на коммутаторе %указать существующий КАД% после переезда клиента.'] = '- Сообщить в ОЛИ СПД об освободившемся порте на коммутаторе %указать существующий КАД% после переезда клиента.'
            static_vars['указать существующий КАД'] = head.split('\n')[4].split()[2]

        result_services.append(analyzer_vars(stroka, static_vars, hidden_vars))

        userlastname = None
        if request.user.is_authenticated:
            userlastname = request.user.last_name
        now = datetime.datetime.now()
        now = now.strftime("%d.%m.%Y")

        index_template = 1
        titles = []
        for i in range(len(result_services)):
            result_services[i] = '{}. '.format(index_template) + result_services[i]
            titles.append(result_services[i][:result_services[i].index('---')])
            index_template += 1

        titles = ''.join(titles)
        result_services = '\n\n\n'.join(result_services)
        result_services = 'ОУЗП СПД ' + userlastname + ' ' + now + '\n' + head + '\n\n' + titles + '\n' + result_services

        context = {
            'result_services': result_services

        }


        return render(request, 'tickets/exist_cl_data.html', context)
    else:
        error = 'Нет шаблона "Перенос сервиса %указать название сервиса%"'
        request.session['error'] = error
        redirect('no_data')


def _passage_services_on_csw(result_services, value_vars):
    print("Перенос сервиса %указать название сервиса%" + '-' * 20)
    templates = value_vars.get('templates')
    readable_services = value_vars.get('readable_services')
    sreda = value_vars.get('sreda')

    stroka = templates.get("Перенос сервиса %указать название сервиса% на клиентский коммутатор")
    if stroka:
        services = []
        count_exist_serv = 0
        for key, value in readable_services.items():
            if type(value) == str:
                services.append(key + ' ' + value)
                count_exist_serv += 1
            elif type(value) == list:
                services.append(key + ''.join(value))
                count_exist_serv += len(value)
        for i in range(count_exist_serv):
            result_services.append(enviroment_csw(value_vars))
        static_vars = {}
        hidden_vars = {}
        static_vars['указать название сервиса'] = ', '.join(readable_services.keys())
        if sreda == '2' or sreda == '4':
            static_vars['ОИПМ/ОИПД'] = 'ОИПМ'
        else:
            static_vars['ОИПМ/ОИПД'] = 'ОИПД'
        static_vars['указать сервис'] = ', '.join(services)


        result_services.append(analyzer_vars(stroka, static_vars, hidden_vars))
    return result_services

def change_services(value_vars):
    """Данный метод с помощью внутрених методов формирует блоки ОРТР(заголовки и заполненные шаблоны),
     ОТС(заполненые шаблоны) для организации новых услуг или изменения существующих без монтаж. работ"""
    #result_services, result_services_ots = _new_services(result_services, value_vars)
    result_services, value_vars = _change_services(value_vars)
    result_services_ots = None
    titles = _titles(result_services, result_services_ots)

    return titles, result_services, result_services_ots, value_vars


def extra_services(value_vars):
    """Данный метод с помощью внутрених методов формирует блоки ОРТР(заголовки и заполненные шаблоны),
     ОТС(заполненые шаблоны) для организации новых услуг дополнительно к существующему подключению"""
    result_services, value_vars = exist_enviroment_install_csw(value_vars)
    result_services, result_services_ots = _new_services(result_services, value_vars)
    result_services = _passage_services_on_csw(result_services, value_vars)
    titles = _titles(result_services, result_services_ots)

    return titles, result_services, result_services_ots, value_vars

def passage_services(value_vars):
    """Данный метод с помощью внутрених методов формирует блоки ОРТР(заголовки и заполненные шаблоны),
     ОТС(заполненые шаблоны) для переноса услуг"""
    if value_vars.get('counter_exist_line') > 1:
        result_services, value_vars = _new_enviroment(value_vars)
    else:
        result_services, value_vars = _passage_enviroment(value_vars)
    result_services = _passage_services(result_services, value_vars)
    result_services_ots = None
    return result_services, result_services_ots, value_vars


def add_serv_with_install_csw(request):
    if request.method == 'POST':
        add_serv_inst_csw_form = AddServInstCswForm(request.POST)

        if add_serv_inst_csw_form.is_valid():
            type_install_csw = add_serv_inst_csw_form.cleaned_data['type_install_csw']
            request.session['type_install_csw'] = type_install_csw
            tag_service = request.session['tag_service']
            tag_service.pop(0)
            if type_install_csw == 'Медная линия и порт не меняются':
                tag_service.append({'csw': None})
            elif type_install_csw == 'ВОЛС и порт не меняются':
                tag_service.append({'csw': None})
            elif type_install_csw == 'Перевод на гигабит по меди на текущем узле':
                tag_service.append({'copper': None})
            else:
                tag_service.append({'vols': None})
            request.session['tag_service'] = tag_service
            return redirect(next(iter(tag_service[0])))

    else:

        add_serv_inst_csw_form = AddServInstCswForm()
        context = {
            'add_serv_inst_csw_form': add_serv_inst_csw_form
        }

        return render(request, 'tickets/add_serv_inst_csw_form.html', context)


def change_serv(request):
    if request.method == 'POST':
        changeservform = ChangeServForm(request.POST)

        if changeservform.is_valid():
            type_change_service = changeservform.cleaned_data['type_change_service']
            request.session['type_change_service'] = type_change_service
            tag_service = request.session['tag_service']
            tag_service.pop(0)
            if type_change_service == "Организация доп IPv6":
                tag_service.append({'data': None})
            elif any(serv in type_change_service for serv in ['ЦКС', 'ВЛС', 'ВМ']):
                tag_service.append({'data': None})
            else:
                tag_service.insert(0, {'change_params_serv': None})

            request.session['tag_service'] = tag_service
            return redirect(next(iter(tag_service[0])))

    else:

        changeservform = ChangeServForm()
        context = {
            'changeservform': changeservform
        }

        return render(request, 'tickets/change_serv.html', context)

def change_params_serv(request):
    if request.method == 'POST':
        changeparamsform = ChangeParamsForm(request.POST)

        if changeparamsform.is_valid():
            new_mask = changeparamsform.cleaned_data['new_mask']
            change_type_port_exist_serv = changeparamsform.cleaned_data['change_type_port_exist_serv']
            change_type_port_new_serv = changeparamsform.cleaned_data['change_type_port_new_serv']
            routed_ip = changeparamsform.cleaned_data['routed_ip']
            routed_vrf = changeparamsform.cleaned_data['routed_vrf']

            request.session['new_mask'] = new_mask
            request.session['change_type_port_exist_serv'] = change_type_port_exist_serv
            request.session['change_type_port_new_serv'] = change_type_port_new_serv
            request.session['routed_ip'] = routed_ip
            request.session['routed_vrf'] = routed_vrf
            tag_service = request.session['tag_service']
            tag_service.pop(0)
            #if new_mask:
            #    tag_service.remove('shpd')

            tag_service.append({'data': None})
            request.session['tag_service'] = tag_service
            return redirect(next(iter(tag_service[0])))

    else:
        type_change_service = request.session['type_change_service']
        types_turnoff_trunk = ["Организация ШПД trunk'ом с простоем",
                               "Организация ЦКС trunk'ом с простоем",
                               "Организация порта ВЛС trunk'ом с простоем",
                               "Организация порта ВМ trunk'ом с простоем"]
        if type_change_service in types_turnoff_trunk:
            turnoff_trunk = True
        else:
            turnoff_trunk = False
        types_only_mask = ["Организация порта ВМ trunk'ом",
                           "Организация порта ВЛС trunk'ом",
                           "Организация ЦКС trunk'ом",
                           "Организация доп connected",
                           "Замена connected на connected",
                           "Изменение cхемы организации ШПД",
                           "Организация ШПД trunk'ом"]
        if type_change_service in types_only_mask:
            only_mask = True
        else:
            only_mask = False
        if type_change_service == "Организация доп маршрутизируемой":
            routed = True
        else:
            routed = False

        changeparamsform = ChangeParamsForm()
        context = {
            'changeparamsform': changeparamsform,
            'type_change_service': type_change_service,
            'turnoff_trunk': turnoff_trunk,
            'only_mask': only_mask,
            'routed': routed
        }

        return render(request, 'tickets/change_params_serv.html', context)


def _change_services(value_vars):
    result_services = []
    services_plus_desc = value_vars.get('services_plus_desc')
    type_change_service = value_vars.get('type_change_service')
    templates = value_vars.get('templates')
    if type_change_service == "Организация ШПД trunk'ом":
        stroka = templates.get("Организация услуги ШПД в интернет trunk'ом.")
        static_vars = {}
        hidden_vars = {}
        static_vars['указать маску'] = value_vars.get('new_mask')
        result_services.append(analyzer_vars(stroka, static_vars, hidden_vars))
    elif type_change_service == "Организация ШПД trunk'ом с простоем":
        stroka = templates.get("Организация услуги ШПД в интернет trunk'ом с простоем связи.")
        static_vars = {}
        hidden_vars = {}
        static_vars['указать маску'] = value_vars.get('new_mask')
        static_vars["указать ресурс на договоре"] = value_vars.get('selected_ono')[0][4]
        static_vars["в неизменном виде/access'ом (native vlan)/trunk'ом"] = value_vars.get('change_type_port_exist_serv')
        static_vars["access'ом (native vlan)/trunk'ом"] = value_vars.get('change_type_port_new_serv')
        result_services.append(analyzer_vars(stroka, static_vars, hidden_vars))
    elif type_change_service == "Изменение cхемы организации ШПД":
        stroka = templates.get("Изменение существующей cхемы организации ШПД с маской %указать сущ. маску% на подсеть с маской %указать нов. маску%")
        static_vars = {}
        hidden_vars = {}
        static_vars['указать нов. маску'] = value_vars.get('new_mask')
        static_vars["указать сущ. маску"] = value_vars.get('selected_ono')[0][0][-3:]
        static_vars["указать ресурс на договоре"] = value_vars.get('selected_ono')[0][4]
        static_vars['изменится/не изменится'] = 'не изменится'
        result_services.append(analyzer_vars(stroka, static_vars, hidden_vars))
    elif type_change_service == "Замена connected на connected":
        stroka = templates.get("Замена существующей connected подсети на connected подсеть с %большей/меньшей% маской")
        static_vars = {}
        hidden_vars = {}
        static_vars['указать нов. маску'] = value_vars.get('new_mask')
        static_vars["указать сущ. маску"] = value_vars.get('selected_ono')[0][0][-3:]
        static_vars["указать ресурс на договоре"] = value_vars.get('selected_ono')[0][4]
        static_vars['изменится/не изменится'] = 'не изменится'
        if int(static_vars['указать нов. маску'][1:]) > int(static_vars['указать нов. маску'][1:]):
            static_vars['большей/меньшей'] = 'меньшей'
        else:
            static_vars['большей/меньшей'] = 'большей'
        static_vars['маркировка маршрутизатора'] = '-'.join(value_vars.get('selected_ono')[0][-2].split('-')[1:])
        match_svi = re.search('- (\d\d\d\d) -', value_vars.get('selected_ono')[0][-3])
        svi = match_svi.group(1)
        static_vars['указать номер SVI'] = svi
        result_services.append(analyzer_vars(stroka, static_vars, hidden_vars))
    elif type_change_service == "Организация доп connected.":
        stroka = templates.get('Организация дополнительной подсети (connected)')
        static_vars = {}
        hidden_vars = {}
        static_vars['указать нов. маску'] = value_vars.get('new_mask')
        static_vars['маркировка маршрутизатора'] = '-'.join(value_vars.get('selected_ono')[0][-2].split('-')[1:])
        match_svi = re.search('- (\d\d\d\d) -', value_vars.get('selected_ono')[0][-3])
        svi = match_svi.group(1)
        static_vars['указать номер SVI'] = svi
        result_services.append(analyzer_vars(stroka, static_vars, hidden_vars))
    elif type_change_service == "Организация доп маршрутизируемой":
        stroka = templates.get("Организация маршрутизируемого непрерывного блока адресов сети интернет")
        static_vars = {}
        hidden_vars = {}
        static_vars['указать нов. маску'] = value_vars.get('new_mask')
        static_vars['указать ip-адрес'] = value_vars.get('routed_ip')
        static_vars['указать название vrf'] = value_vars.get('routed_vrf')
        result_services.append(analyzer_vars(stroka, static_vars, hidden_vars))
    elif type_change_service == "Организация доп IPv6":
        stroka = templates.get('Предоставление возможности прямой маршрутизации IPv6 дополнительно к существующему IPv4 подключению')
        static_vars = {}
        hidden_vars = {}
        match_svi = re.search('- (\d\d\d\d) -', value_vars.get('selected_ono')[0][-3])
        svi = match_svi.group(1)
        static_vars['указать номер SVI'] = svi
        static_vars["указать ресурс на договоре"] = value_vars.get('selected_ono')[0][4]
    elif type_change_service == "Организация ЦКС trunk'ом":
        stroka = templates.get("Организация услуги ЦКС Etherline trunk'ом.")
        static_vars = {}
        hidden_vars = {}
        all_cks_in_tr = value_vars.get('all_cks_in_tr')
        if all_cks_in_tr:
            service = next(iter(all_cks_in_tr.keys()))
            static_vars['указать точку "A"'] = all_cks_in_tr.get(service)['pointA']
            static_vars['указать точку "B"'] = all_cks_in_tr.get(service)['pointB']
            static_vars['полисером Subinterface/портом подключения'] = all_cks_in_tr.get(service)['policer_cks']
            static_vars['указать полосу'] = _get_policer(service)
            result_services.append(analyzer_vars(stroka, static_vars, hidden_vars))
    elif type_change_service == "Организация ЦКС trunk'ом с простоем":
        stroka = templates.get("Организация услуги ЦКС Etherline trunk'ом с простоем связи.")
        static_vars = {}
        hidden_vars = {}
        all_cks_in_tr = value_vars.get('all_cks_in_tr')
        if all_cks_in_tr:
            service = next(iter(all_cks_in_tr.keys()))
            static_vars['указать точку "A"'] = all_cks_in_tr.get(service)['pointA']
            static_vars['указать точку "B"'] = all_cks_in_tr.get(service)['pointB']
            static_vars['полисером Subinterface/портом подключения'] = all_cks_in_tr.get(service)['policer_cks']
            static_vars['указать полосу'] = _get_policer(service)
            static_vars['указать ресурс на договоре'] = value_vars.get('selected_ono')[0][4]
            result_services.append(analyzer_vars(stroka, static_vars, hidden_vars))
    elif type_change_service == "Организация порта ВЛС trunk'ом":
        static_vars = {}
        hidden_vars = {}
        all_portvk_in_tr = value_vars.get('all_portvk_in_tr')
        service = next(iter(all_portvk_in_tr.keys()))
        if all_portvk_in_tr.get(service)['new_vk'] == True:
            stroka = templates.get("Организация услуги ВЛС")
            result_services.append(stroka)
            static_vars['указать ресурс ВЛС на договоре в Cordis'] = 'Для ВЛС, организованной по решению выше,'
        else:
            static_vars['указать ресурс ВЛС на договоре в Cordis'] = all_portvk_in_tr.get(service)['exist_vk']
        stroka = templates.get("Организация услуги порт ВЛC trunk'ом.")
        static_vars['указать полосу'] = _get_policer(service)
        static_vars['полисером на Subinterface/на порту подключения'] = all_portvk_in_tr.get(service)['policer_vk']
        result_services.append(analyzer_vars(stroka, static_vars, hidden_vars))
    elif type_change_service == "Организация порта ВЛС trunk'ом с простоем":
        pass
    elif type_change_service == "Организация порта ВМ trunk'ом":
        pass
    elif type_change_service == "Организация порта ВМ trunk'ом с простоем":
        pass
    kad = value_vars.get('selected_ono')[0][-2]
    value_vars.update({'kad': kad})
    return result_services, value_vars


def _get_policer(service):
    """Данный метод в строке услуги определяет скорость услуги"""
    if '1000' in service:
        policer = '1 Гбит/с'
    elif '100' in service:
        policer = '100 Мбит/с'
    elif '10' in service:
        policer = '10 Мбит/с'
    elif '1' in service:
        policer = '1 Гбит/с'
    else:
        policer = 'Неизвестная полоса'
    return policer