import requests
from requests.auth import HTTPBasicAuth
import re
from bs4 import BeautifulSoup
import datetime
from collections import namedtuple
import os
from pathlib import Path
from dotenv import load_dotenv


BASE_DIR = Path(__file__).resolve().parent.parent
dotenv_path = os.path.join(BASE_DIR, '.env')
load_dotenv(dotenv_path)
GOTTLIEB_USER = os.getenv('GOTTLIEB_USER')
GOTTLIEB_PASSWORD = os.getenv('GOTTLIEB_PASSWORD')


def get_rtk_initial(username, password, line_data):
    rtk_initial = {}
    line_data = '' if not line_data else line_data
    match_rtk_ip_port = re.search("\[(\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3})\]-(\d{1,2})", line_data)
    if match_rtk_ip_port:
        rtk_ip = match_rtk_ip_port.group(1)
        rtk_port = match_rtk_ip_port.group(2)
        rtk_initial.update({'rtk_ip': rtk_ip, 'rtk_port': rtk_port})
    else:
        match_rtk_gpon = re.search("pon-port (\d{1,2}/\d{1,2})\)-(\d{1,2})TS", line_data)
        if match_rtk_gpon:
            rtk_port_1 = match_rtk_gpon.group(1)
            rtk_port_2 = match_rtk_gpon.group(2)
            rtk_port = rtk_port_1 + '/' + rtk_port_2.lstrip('0')
            rtk_initial.update({'rtk_port': rtk_port})
            match_rtk_ip = re.search("\[(\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3})\]", line_data)
            if match_rtk_ip:
                rtk_ip = match_rtk_ip.group(1)
                rtk_initial.update({'rtk_ip': rtk_ip})
            regex_rtk_order = "(?:[Лл][Ии][Рр][ЫыАа]\s*:\s*|[Нн]\s*[Аа]\s*[Рр]\s*[Яя]\s*[Дд]\s*:\s*)(\d{9})"
            match_rtk_order = re.search(regex_rtk_order, line_data)
            if match_rtk_order:
                rtk_order = match_rtk_order.group(1)
                ploam = get_ploam(username, password, rtk_order)
                rtk_initial.update({'rtk_ploam': ploam})
    return rtk_initial


def get_oattr_sreda(oattr):
    wireless_temp = ['БС ', 'радио', 'радиоканал', 'антенну']
    ftth_temp = ['Alpha', 'ОК-1']
    vols_temp = ['ОВ', 'ОК', 'ВОЛС', 'волокно', 'ОР ', 'ОР№', 'сущ.ОМ', 'оптическ']
    if any(wl in oattr for wl in wireless_temp) and (not 'ОК' in oattr):
        sreda = '3'
    elif any(ft in oattr for ft in ftth_temp) and (not 'ОК-16' in oattr):
        sreda = '4'
    elif any(vo in oattr for vo in vols_temp):
        sreda = '2'
    else:
        sreda = '1'
    return sreda


def parsingByNodename(node_name, login, password):
    """Данный метод выполняет поиск коммутаторов по узлу связи и парсит страницу со списком коммутаторов"""
    url = 'https://cis.corp.itmh.ru/stu/NetSwitch/SearchNetSwitchProxy'
    data = {'IncludeDeleted': 'false', 'IncludeDisabled': 'true', 'HideFilterPane': 'false'}
    data['NodeName'] = node_name.encode('utf-8')
    req = requests.post(url, verify=False, auth=HTTPBasicAuth(login, password), data=data)
    if req.status_code == 200:
        switch = req.content.decode('utf-8')
        if 'No records to display.' in switch:
            list_switches = []
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
            for i in clear_switch_id:
                ports = {}
                # Обработка AttributeError для обхода проблемы https://ctms.itmh.ru/browse/DEPIT3-5457
                try:
                    url_switch_id = 'https://cis.corp.itmh.ru/stu/Switch/Details/' + i
                    req_switch_id = requests.get(url_switch_id, verify=False, auth=HTTPBasicAuth(login, password))
                    switch_id = req_switch_id.content.decode('utf-8')
                except AttributeError:
                    switch_id = ''
                regex_total_ports = 'for=\"TotalPorts\">([-+]?\d+)<'
                match_total_ports = re.search(regex_total_ports, switch_id)
                ports['Всего портов'] = match_total_ports.group(1) if match_total_ports else ''

                regex_client_ports = 'for=\"ClientCableUsedPorts\">([-+]?\d+)<'
                match_client_ports = re.search(regex_client_ports, switch_id)
                ports['Занятых клиентами'] = match_client_ports.group(1) if match_client_ports else ''

                regex_link_ports = 'for=\"LinkUsedPorts\">([-+]?\d+)<'
                match_link_ports = re.search(regex_link_ports, switch_id)
                ports['Занятых линками'] = match_link_ports.group(1) if match_link_ports else ''

                regex_avail_ports = 'for=\"AvailablePorts\">([-+]?\d+)<'
                match_avail_ports = re.search(regex_avail_ports, switch_id)
                ports['Доступные'] = match_avail_ports.group(1) if match_avail_ports else ''
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
            for i in range(len(match_name_model)):
                if match_name_model[i] not in clear_name_model:
                    list_switches.append(
                        [match_name_model[i][0], match_name_model[i][1], match_ip[i], match_uplink[i],
                         match_status_desc[i][0], match_status_desc[i][1].replace('&quot;','"'), '-', '-', '-', '-', '-'])

            for i in range(len(clear_name_model)):
                list_switches.append(
                    [clear_name_model[i][0], clear_name_model[i][1], clear_ip[i], clear_uplink[i], clear_status_desc[i][0], clear_status_desc[i][1].replace('&quot;','"'),
                     list_ports[i]['Всего портов'], list_ports[i]['Занятых клиентами'], list_ports[i]['Занятых линками'], list_ports[i]['Доступные'], configport_switches[i]])

            return list_switches


def ckb_parse(login, password):
    """Данный метод парсит страницу КБЗ с Типовыми блоками ТР"""
    templates = {}
    url = 'https://ckb.itmh.ru/pages/viewpage.action?pageId=781026728'
    req = requests.get(url, verify=False, auth=HTTPBasicAuth(login, password))
    soup = BeautifulSoup(req.content.decode('utf-8'), "html.parser")
    search = soup.find_all('pre', {'class': 'syntaxhighlighter-pre'})
    for item in search:
        regex = '(.+)'
        match = re.search(regex, item.text)
        title = match.group(1)
        templates[title] = item.text
    return templates


def ckb_parse_msan_exist(login, password, ip):
    """Данный метод парсит страницу КБЗ с Типовыми блоками ТР"""
    url = 'https://ckb.itmh.ru/pages/viewpage.action?pageId=578595591'
    req = requests.get(url, verify=False, auth=HTTPBasicAuth(login, password))
    if ip in req.content.decode('utf-8'):
        return True
    return False


def _parsing_vgws_by_node_name(login, password, **kwargs):
    """Данный метод получает на входе узел связи или название КАД и по нему парсит страницу с поиском тел. шлюзов"""
    url = 'https://cis.corp.itmh.ru/stu/VoipGateway/SearchVoipGatewayProxy'
    data = {'SearchZip': 'false', 'SearchDeleted': 'false', 'ClientListRequired': 'false', 'BuildingId': '0'}
    if kwargs.get('Switch'):
        data['Switch'] = kwargs['Switch']
    elif kwargs.get('NodeName'):
        data['NodeName'] = kwargs['NodeName']
    req = requests.post(url, verify=False, auth=HTTPBasicAuth(login, password), data=data)
    if req.status_code == 200:
        soup = BeautifulSoup(req.json()['data'], "html.parser")
        table = soup.find('table')
        rows_tr = table.find_all('tr')
        vgws = []
        types_model_vgw = ['ITM SIP', 'D-Link', 'Eltex', 'Nateks', 'AddPac', 'Cisco']
        # модели задаются вручную, т.к. поле модели текстовое и проще его определить по совпадению из списка
        types_node_vgw = ['Узел связи', 'Помещение клиента']
        for row_tr in rows_tr:
            vgw_inner = dict()
            #rows_td = row_tr.find_all('td')
            index_row = 0                           # Поля состояние и описание - текстовые, найти их как остальные
            for row_td in row_tr.find_all('td'):    # не получится и т.к. row_td - элемент класса bs4 нет возможности
                index_row += 1                      # обратится  к полям по позиции, поэтому считаем вручную
                if index_row == 8:                  # 8 - позиция состояния в таблице шлюзов
                    vgw_inner.update({'state': row_td.text})
                if index_row == 12:                 # 12 - позиция описания в таблице шлюзов
                    vgw_inner.update({'description': row_td.text})
                if row_td.find('a'):
                    if row_td.find('a', {'class': "voipgateway-name"}):
                        vgw_inner.update({'name': row_td.find('a').text})
                    elif 'tab-links' in row_td.find('a').get('href'):
                        vgw_inner.update({'uplink': row_td.find('a').text})
                    elif 'tab-ports' in row_td.find('a').get('href'):
                        vgw_inner.update({'ports': row_td.find('a').get('href')})
                    elif row_td.find('a', {'class': "dashed"}):
                        vgw_inner.update({'ip': row_td.find('a').text})
                elif any(model in row_td.text for model in types_model_vgw):
                    vgw_inner.update({'model': row_td.text})
                elif any(room in row_td.text for room in types_node_vgw):
                    vgw_inner.update({'type': row_td.text})
            if vgw_inner:
                vgws.append(vgw_inner)
    return vgws


def get_contract_id(login, password, contract):
    """Данный метод получает на входе номер договора клиента или его часть, выполняет запрос в Cordis на
    соответствующий ID, возвращает либо список ID удовлетворяющих договору, если их несколько, либо один ID,
    если соответствующий договор только один, либо сообщение о отсутствии соответствующего договора"""
    url = f'https://cis.corp.itmh.ru/doc/crm/contract_ajax.ashx?term={contract}'
    req = requests.get(url, verify=False, auth=HTTPBasicAuth(login, password))
    contract_list = req.json()
    if len(contract_list) > 1:
        contract_id = contract_list
    elif len(contract_list) == 0:
        contract_id = 'Такого договора не найдено'
    else:
        contract_id = contract_list[0].get('id')
    return contract_id


def get_contract_resources(login, password, contract_id):
    """Данный метод на входе получает ID договора клиента, парсит вкладку Сводка в Cordis, возвращает список
    услуг на договоре"""
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


def _parsing_model_and_node_client_device_by_device_name(name, login, password):
    """Данный метод получает на входе название КАД и по нему парсит страницу с поиском коммутатров, чтобы определить
    модель коммутатора и название узла этого коммутатора"""
    url = 'https://cis.corp.itmh.ru/stu/NetSwitch/SearchNetSwitchProxy'
    data = {'IncludeDeleted': 'false', 'IncludeDisabled': 'true', 'HideFilterPane': 'false'}
    data['Name'] = name
    req = requests.post(url, verify=False, auth=HTTPBasicAuth(login, password), data=data)
    if req.status_code == 200:
        model = None
        node = None
        soup = BeautifulSoup(req.json()['data'], "html.parser")
        table = soup.find('div', {"class": "t-grid-content"})
        for td in table.find_all('td'):
            if td.text.strip() == name:
                model = td.next_sibling.text.strip()
                node = td.next_sibling.next_sibling.text.strip()
        return model, node


def _parsing_id_client_device_by_device_name(name, login, password):
    """Данный метод получает на входе название КАД и по нему парсит страницу с поиском коммутаторв, чтобы определить
    id этого коммутатора"""
    url = 'https://cis.corp.itmh.ru/stu/NetSwitch/SearchNetSwitchProxy'
    data = {'IncludeDeleted': 'false', 'IncludeDisabled': 'true', 'HideFilterPane': 'false'}
    data['Name'] = name
    req = requests.post(url, verify=False, auth=HTTPBasicAuth(login, password), data=data)
    if req.status_code == 200:
        soup = BeautifulSoup(req.json()['data'], "html.parser")
        table = soup.find('div', {"class": "t-grid-content"})
        row_tr = table.find('tr')
        id_client_device = row_tr.get('id')
        return id_client_device


def _parsing_config_ports_client_device(id_client_device, login, password):
    """Данный метод получает на входе id коммутатора и парсит страницу с конфигом портов, чтобы получить
     список портконфигов"""
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
        if inner_list and inner_list[0] != 'No records to display.':
            inner_list.pop(4)
            inner_list.pop(3)
            config_ports_client_device.append(inner_list)
    return config_ports_client_device


def parsing_config_ports_vgw(href_ports, login, password):
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


def get_cis_resources(login, password, contract_id):
    """Данный метод по id контракта получает данные с вкладки Ресурсы на договоре"""
    url = f'https://cis.corp.itmh.ru/doc/CRM/contract.aspx?contract={contract_id}&tab=4'
    req = requests.get(url, verify=False, auth=HTTPBasicAuth(login, password))
    soup = BeautifulSoup(req.content.decode('utf-8'), "html.parser")
    table = soup.find('table', id="ctl00_middle_ResourceContent_ContractResources_RadGrid_Resources_ctl00")
    return table


def get_cis_vss_camera(login, password, sim, contract_id):
    """Данный метод по id контракта и id ресурса Управление видеокамерой получает данные о ресурсе"""
    url = f'https://cis.corp.itmh.ru/mvc/Resource/CardVssCamera?contract={contract_id}&sim={sim.id}'
    req = requests.get(url, verify=False, auth=HTTPBasicAuth(login, password))
    soup = BeautifulSoup(req.content.decode('utf-8'), "html.parser")
    stream = soup.find('input', id="primary_stream_url").get('value')
    match = re.search(r"(\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3})", stream)
    if match:
        ip = match.group(1)
        summary = soup.find('textarea', id="mem").text.strip()
        return {'title': sim.title, 'ip': ip, 'summary': summary}


def check_contract_video(login, password, table, contract_id):
    all_a = table.find_all('a')
    SimCamera = namedtuple('SimCamera', 'title id')
    sims = [SimCamera(a.get('title'), a.get('href').split(',')[1]) for a in all_a if a.get('href') and 'vss_camera' in a['href']]
    cameras = []
    for sim in sims:
        cis_vss_camera = get_cis_vss_camera(login, password, sim, contract_id)
        if cis_vss_camera:
            cameras.append(cis_vss_camera)
    return cameras

def check_contract_phone_exist(table):
    """Данный метод получает Ресурсы в Cordis, проверяет налиличие ресурсов
    Телефонный номер и возвращает список точек подключения, на которых есть такой ресурс"""
    rows_td = table.find_all('td')
    pre_phone_address = []
    for index, td in enumerate(rows_td):
        try:
            if 'Телефонный номер' == td.text:
                pre_phone_address.append(index)
        except AttributeError:
            pass
    phone_address_index = list(map(lambda x: x+2, pre_phone_address))
    phone_address = set()
    for i in phone_address_index:
        addr = ','.join(rows_td[i].text.split(',')[:2])
        phone_address.add(addr)
    phone_address = list(phone_address)
    return phone_address


def _get_chain_data(login, password, device):
    """Данный метод принимает в качестве параметра Название оборудования, от которого подключен клиент. Обращается к
     https://mon.itss.mirasystem.net/mp/ и парсит цепочку устройств в которой состоит это оборудование."""
    url = f'https://mon.itss.mirasystem.net/mp/index.py/chain_update?hostname={device}'
    req = requests.get(url, verify=False, auth=HTTPBasicAuth(login, password))
    chains = req.json()
    return chains


def get_switch_ip(login, password, switch):
    """Данный метод получает IP коммутатора по названию через mon.itss.mirasystem.net"""
    url = f'https://mon.itss.mirasystem.net/mp/index.py/search'
    data = {"hnames": f"^{switch}$", "haliases": "", "hgroups": "", "hips": ""}
    req = requests.post(url, data=data, verify=False, auth=HTTPBasicAuth(login, password))
    response = req.json()
    if response and response[0].get("host_name") == switch:
        return response[0].get("address")


def for_spp_view(login, password, dID):
    """Данный метод принимает в качестве параметра ID заявки в СПП, парсит страницу с данной заявкой и возвращает
    данные о заявке в СПП."""
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
            elif 'Дата оформления' in i.find_all('td')[0].text:
                spp_params['Оценочное ТР'] = True if i.find_all('td')[3].text.strip() == 'Оценка' else False
            elif 'Куратор' in i.find_all('td')[0].text:
                spp_params['uID'] = i.find_all('td')[1].find('select').find('option').get('value')
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
        simplified_tr = soup.find('input', id='is_simple_solution_required').get('checked')
        spp_params['ТР по упрощенной схеме'] = True if simplified_tr else False
        dif_period = soup.find('input', id='trDifPeriod').get('value')
        spp_params['trDifPeriod'] = dif_period
        cur_phone = soup.find('input', id='inp_1').get('value')
        spp_params['trCuratorPhone'] = cur_phone
        return spp_params
    else:
        spp_params['Access denied'] = 'Access denied'
        return spp_params


def for_tr_view(login, password, dID, tID, trID):
    """Данный метод принимает в качестве параметров параметры ТР в СПП, парсит страницу с данным ТР в СПП и возвращает
        данные о ТР."""
    spp_params = {}
    all_link = {}
    url = 'https://sss.corp.itmh.ru/dem_tr/dem_point.php?dID={}&tID={}&trID={}'.format(dID, tID, trID)
    req = requests.get(url, verify=False, auth=HTTPBasicAuth(login, password))
    if req.status_code == 200:
        soup = BeautifulSoup(req.content.decode('utf-8'), "html.parser")
        aid_link = soup.find('a', class_='nodec')
        if aid_link:
            aid_link = aid_link['href']
        else:
            aid_link = ''
        match = re.search(r'php\?aID=(\d+)', aid_link)
        aid = match.group(1) if match else 0
        spp_params['aid'] = aid
        stu_find = soup.find('a', title="Переход в СТУ")
        stu_link = stu_find.get('href') if stu_find else '0'
        match = re.search(r'Edit/(\d+)', stu_link)
        id_otu_project = match.group(1) if match else 0
        spp_params['id_otu_project'] = id_otu_project
        search = soup.find_all('tr')
        for index, i in enumerate(search):
            if 'Переченьтребуемых услуг' in i.find_all('td')[0].text:
                total_services = []
                for service_index in range(1, len(i.find_all('td')[1].find_all('tr'))-1):
                    services = i.find_all('td')[1].find_all('tr')[service_index].find_all('td')
                    var_list = []
                    for k in services:
                        var_list.append(k.text)
                    service = ' '.join(var_list)
                    service = service[:-1]
                    total_services.append(service)
                spp_params['Перечень требуемых услуг'] = total_services
            elif 'Информация дляразработки ТР' in i.find_all('td')[0].text:
                spp_params['Информация для разработки ТР'] = i.find_all('td')[1].text
            elif 'Узел подключения клиента' in i.find_all('td')[0].text:
                node = re.search(r'\t(.+)\s+Статус', i.find_all('td')[1].text)
                if 'Изменить' in i.find_all('td')[0].text:
                    spp_params['Узел подключения клиента'] = node.group(1)
                else:
                    spp_params['Узел подключения клиента'] = 'Не выбран'
            elif 'Отключение' in i.find_all('td')[0].text and len(i.find_all('td')) > 1 and i.find_all('td')[1].find('input'):
                try:
                    checked = i.find_all('td')[1].find('input')['checked']
                except KeyError:
                    spp_params[i.find_all('td')[0].text] = 'Нет'
                else:
                    spp_params[i.find_all('td')[0].text] = search[index+1].find('td').text.strip()
            elif 'Тип / кат' in i.find_all('td')[0].text:
                file = {}
                files = i.find_all('td')[0].find_all('a')
                for item in range(len(files)):
                    if 'javascript' not in files[item].get('href'):
                        file[files[item].text] = files[item].get('href')
            elif 'Время на реализацию, дней' in i.find_all('td')[0].text:
                spp_params['Решение ОТПМ'] = search[index+1].find('td').text.strip()
            elif 'Стоимость доп. Оборудования' in i.find_all('td')[0].text:
                for textarea in search[index + 1].find_all('textarea'):
                    if textarea:
                        if textarea['name'] == 'trOTO_Resolution':
                            spp_params['Решение ОРТР'] = textarea.text
                        elif textarea['name'] == 'trOTS_Resolution':
                            spp_params['Решение ОТC'] = textarea.text
        if spp_params['Отключение']:
            spp_params['Файлы'] = file
        search2 = soup.find_all('form')
        form_data = search2[1].find_all('input')
        for i in form_data:
            if i.attrs['type'] == 'hidden':
                if i['name'] == 'vID':
                    spp_params[i['name']] = i['value']
        spp_params['Точка подключения'] = get_connection_point(dID, tID, login, password)
        unranged_services = spp_params['Перечень требуемых услуг']
        always_last = ['Видеонаблюдение', 'ЛВС', 'Телефон']
        temp = [service for service in unranged_services for template in always_last if service.startswith(template)]
        for service in temp:
            unranged_services.remove(service)
        ranged_services = unranged_services + temp
        spp_params['Перечень требуемых услуг'] = ranged_services
        return spp_params
    else:
        spp_params['Access denied'] = 'Access denied'
        return spp_params


def in_work_ortr(login, password):
    """Данный метод парсит страницу с пулом ОРТР в СПП и отфильтровывает заявки с кураторами DIR 2.4.1"""
    lines = []
    url = 'https://sss.corp.itmh.ru/dem_tr/demands.php?tech_uID=0&trStatus=inWorkORTR&curator=any&vName=&dSearch=&bID=1&searchType=param'
    req = requests.get(url, verify=False, auth=HTTPBasicAuth(login, password))
    if req.status_code == 200:
        soup = BeautifulSoup(req.content.decode('utf-8'), "html.parser")
        num = 0
        search = soup.find_all('tr')
        for tr in search:
            if 'Заявки, ожидающие Вашей обработки' == tr.find('td').text:
                continue
            elif tr.find('td', id="cur_stat"):
                num = int(tr.find('td', class_='demand_num').text)
            elif not tr.find('td', id="cur_stat"):
                break

        search_demand_num2 = soup.find_all('td', class_='demand_num2')[num:]
        search_demand_cust = soup.find_all('td', class_='demand_cust')[num:]
        search_demand_point = soup.find_all('td', class_='demand_point')[num:]
        search_demand_tech = soup.find_all('td', class_='demand_tech')[num:]
        search_demand_cur = soup.find_all('td', class_='demand_cur')
        search_demand_stat = soup.find_all('td', class_='demand_stat')
        for index in range(len(search_demand_num2)-1):
            unwanted = ['Бражкин П.В.', 'Короткова И.В.', 'Полейко А.Л.', 'Полейко А. Л.', 'Чернов А. С.']
            if search_demand_cur[index].text not in unwanted:
                if lines and lines[-1][0] == search_demand_num2[index].text:
                    lines[-1][3] = lines[-1][3] + ' ' + search_demand_point[index].text
                else:
                    lines.append([search_demand_num2[index].text,
                                  search_demand_num2[index].find('a').get('href')[(search_demand_num2[index].find('a').get('href').index('=')+1):],
                                  search_demand_cust[index].text,
                                  search_demand_point[index].text,
                                  search_demand_tech[index].text,
                                  search_demand_cur[index].text,
                                  search_demand_stat[index].text])
        for index in range(len(lines)):
            if 'ПТО' in lines[index][0]:
                lines[index][0] = lines[index][0][:lines[index][0].index('ПТО')]+' '+lines[index][0][lines[index][0].index('ПТО'):]
            for symbol_index in range(1, len(lines[index][3])):
                if lines[index][3][symbol_index].isupper() and lines[index][3][symbol_index-1].islower():
                    lines[index][3] = lines[index][3][:symbol_index]+' '+lines[index][3][symbol_index:]
                    break
        return lines


def get_sw_config(sw, model, login, password):
    """Данный метод парсит конфиг коммутатора со stash"""
    switch_config = None
    if model.startswith('3COM'):
        return switch_config

    url = 'https://stash.itmh.ru/projects/NMS/repos/pantera_extrim/raw/backups/' + sw + '-config?at=refs%2Fheads%2Fmaster'
    req = requests.get(url, verify=False, auth=HTTPBasicAuth(login, password))

    if req.status_code == 200 and model.startswith('Cisco'):
        blob = None
        url = f'https://stash.itmh.ru/rest/api/latest/projects/NMS/repos/pantera_extrim/commits?followRenames=true&path=backups%2F{sw}-config&until=refs%2Fheads%2Fmaster&start=0&limit=3&avatarSize=32'
        req = requests.get(url, verify=False, auth=HTTPBasicAuth(login, password))
        if req.json().get('values'):
            for i in req.json().get('values'):
                if i.get('author').get('name') == 'net_backup':
                    blob = i.get('id')
                    break
            if blob:
                url = f'https://stash.itmh.ru/projects/NMS/repos/pantera_extrim/raw/backups/{sw}-config?at={blob}'
                req = requests.get(url, verify=False, auth=HTTPBasicAuth(login, password))
                switch_config = req.content.decode('utf-8')
    elif req.status_code == 200:
        switch_config = req.content.decode('utf-8')
    return switch_config


def get_connection_point(dID, tID, username, password):
    """Данный метод парсит страницу Точки подключения в заявке СПП. По параметрам dID, tID определяет точку
    подключения"""
    connection_point = None
    url = f'https://sss.corp.itmh.ru/dem_tr/dem_point_panel.php?dID={dID}&amp;tID={tID}'
    req = requests.get(url, verify=False, auth=HTTPBasicAuth(username, password))
    if req.status_code == 200:
        soup = BeautifulSoup(req.content.decode('utf-8'), "html.parser")
        point = soup.find('a', id=f"Point_{tID}")
        connection_point = point.text.strip()
        return connection_point


def get_name_id_user_cis(login, password, last_name):
    """Данный метод выполняет запрос в Cordis по фамилии указанной в АРМ и получает подходящие имя и id пользователя"""
    url = f'https://cis.corp.itmh.ru/Autocomplete/Manager/?term={last_name}&only_enabled=true'
    req = requests.get(url, verify=False, auth=HTTPBasicAuth(login, password))
    last_name_list = req.json()
    if len(last_name_list) > 1:
        name_id_user_cis = last_name_list
    elif len(last_name_list) == 0:
        name_id_user_cis = 'Фамилия, указанная в АРМ, в Cordis не найдена'
    else:
        name_id_user_cis = {'id': last_name_list[0].get('id'), 'value': last_name_list[0].get('value')}
    return name_id_user_cis


def add_res_to_ppr(ppr, service, login, password):
    """Добавление ресурса в ППР"""
    contract, ppr_resource, disable_resource = service
    url_contract = f'https://cis.corp.itmh.ru/mvc/Autocomplete/ContractByFullName?term={contract}'
    req_contract = requests.get(url_contract, verify=False, auth=HTTPBasicAuth(login, password))
    contract_list = req_contract.json()
    founded = [i for i in contract_list if i['Name'] == contract]

    if len(founded) == 1:
        id_contract = (founded[0]['ID'])
        url_id_contract = f'https://cis.corp.itmh.ru/mvc/Demand/MaintenanceSimList?contract={id_contract}'
        req = requests.get(url_id_contract, verify=False, auth=HTTPBasicAuth(login, password))
        resources = req.json()

        for resource in resources:
            if resource['Name'].strip() == ppr_resource:
                url = 'https://cis.corp.itmh.ru/mvc/Demand/MaintenanceObjectAddSim'
                data = {'demand': ppr, 'sim': resource['SimId']}
                req = requests.post(url, verify=False, auth=HTTPBasicAuth(login, password), data=data)
                if req.status_code == 200:
                    return 'added', disable_resource, 'Добавлен в ППР'
                return 'error', disable_resource, 'Не добавлен в ППР. Ошибка при добавлении'
        return 'not_found', disable_resource, 'Не добавлен в ППР. Не найден на договоре'
    return 'not_found', disable_resource, 'Не добавлен в ППР. Возможные контракты '+', '.join([r.get('Name') for r in contract_list])


def add_links_to_ppr(ppr, link, login, password):
    """Добавление линка в ППР"""
    sw, ppr_port, disable_resource = link
    url_sw = f'https://cis.corp.itmh.ru/mvc/Autocomplete/EnabledSwitchWithNodeName?term={sw}'
    req_contract = requests.get(url_sw, verify=False, auth=HTTPBasicAuth(login, password))
    sw_list = req_contract.json()
    for found_sw in sw_list:
        if found_sw['Name'] == sw:
            id_sw = (found_sw['ID'])
            url_id_ports = f'https://cis.corp.itmh.ru/mvc/Autocomplete/SwitchPort?device={id_sw}&has_links=true'
            req = requests.get(url_id_ports, verify=False, auth=HTTPBasicAuth(login, password))
            ports = req.json()
            found_ports = []
            for port in ports:
                if f'{ppr_port} ' in port['Name']:
                    found_ports.append(port)
            for found_port in found_ports:
                url = 'https://cis.corp.itmh.ru/mvc/Demand/MaintenanceObjectAddLink'
                data = {'device_name': sw, 'device_port': found_port['id'], 'demand': ppr}
                req = requests.post(url, verify=False, auth=HTTPBasicAuth(login, password), data=data)

                if f'{sw} [<span class="port_name">{ppr_port}</span>]' in req.content.decode('utf-8'):
                    return 'added', disable_resource, 'Добавлен в ППР'
            return 'error', disable_resource, 'Не добавлен в ППР'
    return 'не оказалось в списке коммутаторов', sw, 'Не добавлен в ППР, не найден в списке коммутаторов'


def search_last_created_ppr(login, password, authorname, authorid):
    """Данный метод выполняет поиск последней созданной ППР"""
    last_ppr = None
    now = datetime.datetime.now()
    now = now.strftime("%d.%m.%Y")
    url = 'https://cis.corp.itmh.ru/mvc/demand/search'
    data = {'AuthorName': authorname,
            'AuthorId': authorid,
            'TrackingFilter': 'All',
            'FromDate': now,
            'ShowClosed': 'false',
            'OrderBy': 'deadline',
            'OrderAsc': 'False',
            'ContractMode': 'Default',
            'OrangeIsTheNewBlack': 'False',
            'PagerCurrent': '1',
            'PagerPerPage': '50',
            }
    req = requests.post(url, verify=False, auth=HTTPBasicAuth(login, password), data=data)
    if req.status_code == 200:
        soup = BeautifulSoup(req.content.decode('utf-8'), "html.parser")
        links = soup.find_all('a', {"target": "MainFrame"})
        pprs = [int(link.text) for link in links if link.text.isdigit() and 'mvc/demand' in link['href']]
        last_ppr = sorted(pprs)[-1]
    return last_ppr


def add_tr_to_last_created_ppr(login, password, authorname, authorid, title_ppr, deadline, last_ppr, tr):
    """Данный метод выполняет поиск последней созданной ППР"""
    url = 'https://cis.corp.itmh.ru/mvc/demand/SaveMaintenance'
    data = {'ExecutorName': f'{authorname}',
            'ExecutorID': f'{authorid}',
            'ScheduledIdlePeriod.FromDate': '01.01.2010 0:00',
            'ScheduledIdlePeriod.TrimDate': '01.01.2010 0:01',
            'ScheduledIdleSpan': '1м',
            'IsNotPostponement': 'false',
            'Main': title_ppr,
            'TechnicalSolutionNew': f'{tr}',
            'TechnicalSolutionLink': 'Проверить и добавить',
            'IsCarriedOutsideOrganization': 'false',
            'IsNetworkTune': 'false',
            'IsFvnoAffected': 'false',
            'IsPrivateAffected': 'true',
            'IsPrivateAffected': 'false',
            'IsCorporateAffected': 'true',
            'IsCorporateAffected': 'false',
            'IsIpChanged': 'false',
            'ServiceAndQualities.service_and_quality[0].service': '21',
            'ServiceAndQualities.service_and_quality[1].service': '4',
            'ServiceAndQualities.service_and_quality[2].service': '6',
            'ServiceAndQualities.service_and_quality[3].service': '19',
            'ServiceAndQualities.service_and_quality[4].service': '20',
            'ServiceAndQualities.service_and_quality[0].service_quality': '1',
            'DemandID': f'{last_ppr}',
            'WorkflowID': '306',
            'ReturnJSON': '0',
            'Deadline': f'{deadline}',
            'Priority': '3',
            }
    req = requests.post(url, verify=False, auth=HTTPBasicAuth(login, password), data=data)


class Cordis:
    """Класс для обращения к Cordis"""
    def __init__(self, username, password):
        self.username = username
        self.password = password

    def __connection(self, url):
        req = requests.get(url, verify=False, auth=HTTPBasicAuth(self.username, self.password))
        if req.status_code == 200:
            return req.content.decode('utf-8')

    def get_ppr_page(self, id_ppr):
        url = f'https://cis.corp.itmh.ru/mvc/demand?id={id_ppr}'
        return self.__connection(url)

    def get_ppr_victims_page(self, id_ppr):
        url = f'https://cis.corp.itmh.ru/mvc/Demand/MaintenanceVictimClientList?demand={id_ppr}'
        return self.__connection(url)


class PprParse:
    """Класс принимает html-страниы ППР, Список клиентов ппр и парсит значения в таблицах"""
    def __init__(self, html):
        self.soup = BeautifulSoup(html, "html.parser")
        self.resources = []
        self.victims = []
        self.devices = []
        self.links = []
        self.ip_changed = False
        self.b2b_affected = False
        self.b2c_affected = False

    def parse(self):
        self.parse_devices()
        self.parse_links()
        self.parse_resources()
        self.parse_victims()
        self.parse_checkbox_ip_changed()
        self.parse_checkbox_b2b()
        self.parse_checkbox_b2c()

    def get_devices(self):
        return self.devices

    def get_resources(self):
        return self.resources

    def get_links(self):
        return self.links

    def get_victims(self):
        return self.victims

    def get_b2b_affected(self):
        return self.b2b_affected

    def get_b2c_affected(self):
        return self.b2c_affected

    def get_ip_changed(self):
        return self.ip_changed

    def parse_checkbox_b2b(self):
        self.b2b_affected = True if self.soup.find('input', id='IsCorporateAffected').get('checked') else False

    def parse_checkbox_b2c(self):
        self.b2c_affected = True if self.soup.find('input', id='IsPrivateAffected').get('checked') else False

    def parse_checkbox_ip_changed(self):
        self.ip_changed = True if self.soup.find('input', id='IsIpChanged').get('checked') else False

    def parse_devices(self):
        trs = self.soup.find('div', id="CrashDeviceDivContent").find('table').find_all('tr')[1:]
        all_td = []
        for tr in trs:
            all_td.append(tr.find_all('td'))
        for tds in all_td:
            temp = []
            for index, td in enumerate(tds[::-1]):
                if index in (1, 2, 3, 4):
                    temp.append(td.text)
                    if td.find('a'):
                        temp.append(td.find('a').get('href'))
            self.devices.append(temp[::-1])

        fields = ['name_link', 'name', 'az_link', 'az', 'address', 'model']
        Device = namedtuple('Device', fields)
        self.devices = [Device(*device) for device in self.devices]

    def parse_resources(self):
        header = self.soup.find("h3", text="Объекты ППР: ресурсы клиентов")
        trs = header.find_next('table').find_all('tr')[1:]
        for tr in trs:
            self.resources.append(tr.find_all('td')[1:-1])
        self.resources = [[td.text for td in tds] for tds in self.resources if tds]
        fields = ['contract', 'client_name', 'resource_type', 'resource_name', 'bundle', 'device_name', 'port']
        Resource = namedtuple('Resource', fields)
        self.resources = [Resource(*resource) for resource in self.resources]

    def parse_links(self):
        header = self.soup.find_all("h3", string="Объекты ППР: линки")[0]
        trs = header.find_next('table').find_all('tr')[1:]
        for tr in trs:
            self.links.append(tr.find_all('td')[1:-1])
        self.links = [[td.text.strip() for td in tds] for tds in self.links]

    def parse_victims(self):
        header = self.soup.find("h2", string="B2B")
        trs = header.find_next('table').find_all('tr')[1:]
        for tr in trs:
            self.victims.append(tr.find_all('td'))
        self.victims = [[td.text for td in tds] for tds in self.victims]
        fields = ['contract', 'client_name', 'client_class', 'resource_type', 'point', 'resource_name', 'bundle',
                  'device_name', 'port']
        Victim = namedtuple('Victim', fields)
        self.victims = [Victim(*victim) for victim in self.victims]


class PprCheck:
    """Класс принимает распарсенные данные ППР и выполняет необходимые проверки"""
    def __init__(self, ppr):
        self.messages = []
        self.data = {}
        self.devices = ppr.get_devices()
        self.resources = ppr.get_resources()
        self.victims = ppr.get_victims()
        self.b2b_affected = ppr.get_b2b_affected()
        self.b2c_affected = ppr.get_b2c_affected()
        self.ip_changed = ppr.get_ip_changed()
        self.links = ppr.get_links()

    def check_exist_resources_in_victims(self):
        victim_names = [res.resource_name for res in self.victims]
        not_added = [r for r in self.resources if r.resource_name not in victim_names]
        if not_added:
            self.data.update({
                'table_not_resource_in_victims': {
                    'messages': '<font color="red"><b>Внимание! Обнаружен сбой.</b></font> <ul><li>В Список клиентов не попали сервисы добавленные вручную как <b>Объекты ППР: ресурсы клиентов</b>',
                    'set': not_added
                }
            })

    def check_b2b_affected(self):
        if not self.b2b_affected:
            self.data.update({
                'b2b_affected': {
                    'messages': '<font color="red"><b>Внимание!</b></font> Не установлена галочка <b>B2B</b> в поле <b>Тип клиента</b>. <ul><li>Проверьте, что простой для B2B клиентов действительно не планируется.',
                    'set': None
                }
            })

    def check_b2c_affected(self):
        if not self.b2c_affected:
            self.data.update({
                'b2c_affected': {
                    'messages': '<font color="red"><b>Внимание!</b></font> Не установлена галочка <b>B2C</b> в поле <b>Тип клиента</b>. <ul><li>Проверьте, что простой для B2C клиентов действительно не планируется.',
                    'set': None
                }
            })

    def check_ip_changed(self):
        if self.ip_changed:
            self.data.update({
                'ip_changed': {
                    'messages': '<font color="red"><b>Внимание!</b> </font>Установлена галочка в поле <b>Смена IP адресов B2C/B2B c DHCP</b>. Ожидается смена логики.',
                    'set': None
                }
            })
        else:
            self.data.update({
                'ip_not_changed': {
                    'messages': '<font color="red"><b>Внимание!</b> </font>Не установлена галочка в поле <b>Смена IP адресов B2C/B2B c DHCP</b>. <ul><li>Проверьте, что смена логического подключения действительно не потребуется.',
                    'set': None
                }
            })

    def check_vgw_ip_changed(self):
        expected = [
            'SIP', 'AP-GS1002',	'AP200B', 'AP1000',	'AP1100', '1760', '2801', 'DVG-2016S', 'DVG-2032S',	'DVG-5004S',
			'DVG-5004Sc1', 'DVG-5008S',	'DVG-5008SG', 'DVG-5402SP',	'RG-1404G',	'TAU-2M.IP', 'TAU-8.IP','TAU-16.IP',
			'TAU-24.IP', 'VC-115-2', 'VC-110-2', 'VC-220', 'VC-130-2'
        ]
        if self.ip_changed:
            unexpected = [device for device in self.devices if device.model not in expected and device.name.startswith('VGW')]
            if unexpected:
                self.data.update({
                    'table_device_vgw_ip_changed': {
                        'set': unexpected,
                        'messages': '<ul><li>Необходимо добавить в ТР требование привлечь <b>DIR.I8.3.3</b> для сопровождения работ по смене адресации оборудования',
                    }
                })

    def check_wfc_wfh_ip_changed(self):
        if self.ip_changed:
            wfc = [d for d in self.devices if d.name.startswith('WFC') or d.name.startswith('WFH')]
            if wfc:
                self.data.update({
                    'table_device_wfc_wfh_ip_changed': {
                        'set': wfc,
                        'messages': '<ul><li>Необходимо привлечь <b>DIR.I8.5.1</b> для проектирования ТР по смене адресации оборудования',
                    }
                })

    def check_old_scheme(self):
        old_scheme = []
        not_sign = ['DA', 'BB']

        for r in self.victims:
            if r.resource_type == 'IP-адрес или подсеть' and '/32' in r.resource_name:
                if not any(_ in r.bundle for _ in not_sign):
                    old_scheme.append(r)
        if old_scheme:
            self.data.update({
                'table_resource_old_scheme': {
                    'set': old_scheme,
                    'messages': '<ul><li>Обнаружен сервис <b>IP-адрес или подсеть</b> с маской <b>/32</b> Возможно необходимо инициировать смену реквизитов <b>старой схемы ШПД в общем влан</b> для клиентов',
                }
            })

    def check_offices(self):
        office_devices = [d for d in self.devices if 'Офис Планеты' in d.address]
        office_stik = [v for v in self.victims if
                       'Физический стык для организации L2 каналов до офисов' in v.resource_name]
        if office_devices or office_stik:
            self.data.update({
                'office': {
                    'set': None,
                    'messages': 'Необходимо привлечь <b>DIR.I8.5.1</b> для проектирования ТР с учетом простоя связи на оборудовании Офис ITMH.',
                }
            })
        if office_devices:
            self.data.update({
                'table_device_office_devices': {
                    'set': office_devices,
                    'messages': '<ul><li>Обнаружено <b>Оборудование в УС (Офис Планеты)</b>',
                }
            })

        if office_stik:
            self.data.update({
                'table_resource_office_stik': {
                    'set': office_stik,
                    'messages': '<ul><li>Обнаружен <a href="https://ckb.itmh.ru/x/bTFGHg" target="_blank"><b>Физический стык для организации L2 каналов до офисов</b></a>. Адреса офисов смотри в <a href="https://ckb.itmh.ru/x/nW3CHQ" target="_blank">Реестр. Присоединение офисов Холдинга через РТ</a>',
                }
            })

    def check_itr(self):
        itr_devices = [d for d in self.devices if 'ИНД. ТР' in d.address]
        itr_victims = [v for v in self.victims if 'ИНД. ТР' in v.resource_name]

        if itr_devices or itr_victims:
            self.data.update({
                'itr': {
                    'set': None,
                    'messages': 'Необходимо учесть в ТР особенности схемы организации <a href="https://ckb.itmh.ru/pages/viewpage.action?pageId=81494995" target="_blank">Индивидуального технического решения СПД</a> <b>(ИНД. ТР)</b>',
                }
            })

        if itr_devices:
            self.data.update({
                'table_device_itr_devices': {
                    'set': itr_devices,
                    'messages': '<ul><li>Обнаружено <b>ИНД. ТР</b> на УС',
                }
            })
        if itr_victims:
            self.data.update({
                'table_resource_itr_victims': {
                    'set': itr_victims,
                    'messages': '<ul><li>Обнаружено <b>ИНД. ТР</b> у клиентов',
                }
            })

    def check_rent_vols(self):
        service = 'Предоставление в аренду оптического волокна'
        victims = [v for v in self.victims if service in v.resource_type]
        if victims:
            self.data.update({
                'table_resource_rent_vols': {
                    'set': victims,
                    'messages': 'Обнаружен сервис <b>'+service+'</b>.<ul><li>Необходимо согласовать порядок проверки восстановления связи с клиентами',
                }
            })

    def check_stand_dir8(self):
        service = 'Тестовый стенд DIR.I8'
        victims = [v for v in self.victims if service in v.resource_name]
        if victims:
            self.data.update({
                'table_resource_stand_dir8': {
                    'set': victims,
                    'messages': 'Обнаружен сервис <a href="https://ckb.itmh.ru/x/9iavG" target="_blank"><b>'+service+'</b></a>.<ul><li><b>Исполнителю работ</b> необходимо проинформировать <b>DIR.I8.3.2</b> о запланированных работах, отдельного согласования не требуется',
                }
            })

    def check_stik_getting_services_from_parther(self):
        service = 'Физический стык для получения сервисов от'
        victims = [v for v in self.victims if service in v.resource_name]
        if victims:
            self.data.update({
                'table_resource_stik_getting_services_from_parther': {
                    'set': victims,
                    'messages': 'Обнаружен сервис <b>'+service+' партнера</b>.<ul><li>Необходимо привлечь <b>DIR.I8.3.3</b> для проектирования ТР по вводу/выводу из эксплуатации стыков'
                }
            })

    def check_stik_fvno(self):
        service = 'Физический стык. FVNO'
        victims = [v for v in self.victims if service in v.resource_name]
        if victims:
            self.data.update({
                'table_resource_stik_fvno': {
                    'set': victims,
                    'messages': 'Обнаружен сервис <a href="https://ckb.itmh.ru/x/SDYwH" target="_blank"><b>'+service+'</b></a>.<ul><li><b>Исполнителю работ</b> необходимо проинформировать <b>Ростелеком</b> о работах на стыке.</li><li>При простое на стыке (оба порта EtherChannel) для информирования клиентов необходимо добавить в ППР линки от портов АМ, на которых организован данный стык'
                }
            })

    def check_l2_channel_between_am(self):
        service = 'для обратного FVNO'
        victims = [v for v in self.victims if service in v.resource_name]
        if victims:
            self.data.update({
                'table_resource_l2_channel_between_am': {
                    'set': victims,
                    'messages': 'Обнаружен сервис <a href="https://ckb.itmh.ru/x/SDYwH" target="_blank"><b>L2-канал между АМ на РУА для обратного FVNO</b></a>.<ul><li>Необходимо выполнить эскалацию руководству для согласования порядка вывода L2-канала и корректного информирования Ростелеком о простое.</li><li>При простое на L2-канале для информирования клиентов необходимо добавить в ППР линки от портов АМ, на которых организована заколка для обратного FVNO между АМ'
                }
            })

    def check_b2b_etherchannel(self):
        service = 'B2B. EtherChannel'
        victims = [v for v in self.victims if service in v.resource_name]
        if victims:
            self.data.update({
                'table_resource_b2b_etherchannel': {
                    'set': victims,
                    'messages': 'Обнаружен сервис <b>'+service+'</b>.<ul><li>При необходимости учесть в ТР информирование менеджера клиента о <b>простое на одном из портов EtherChannel</b>'
                }
            })

    def check_icc_dpi(self):
        icc = [d for d in self.devices if re.match('ICC\d+-DPI', d.name)]
        if icc:
            self.data.update({
                'table_device_icc_dpi': {
                    'set': icc,
                    'messages': 'Обнаружен <a href="https://ckb.itmh.ru/x/6wS-HQ" target="_blank"><b>Конвертер MOXA для удаленного управления DPI</b></a>.<ul><li><b>Исполнителю работ</b> необходимо проинформировать <b>DIR.I8.3.2</b> о запланированных работах, отдельного согласования не требуется'
                }
            })

    def check_ias(self):
        links_ias = [d[1].split()[0] for d in self.links if d and d[1].startswith('IAS')]
        exist_ias = [d for d in self.devices if d.name.startswith('IAS') and d.name in links_ias]

        devices_ias = [d.name for d in self.devices if d.name.startswith('IAS')]
        not_exist_ias = [d for d in self.links if d and d[1].startswith('IAS') and d[1].split()[0] not in devices_ias]
        if exist_ias or not_exist_ias:
            self.data.update({
                'ias': {
                    'set': None,
                    'messages': 'Обнаружено <b>устройство КПА</b>:',
                }
            })

        if exist_ias:
            self.data.update({
                'table_device_exist_ias': {
                    'set': exist_ias,
                    'messages': '<ul><li>В ППР добавлены КПА вместе с линками. Необходимо проверить, что отсутствует резервный рабочий линк и ожидается отключение КПА'
                }
            })
        if not_exist_ias:
            self.data.update({
                'table_links_not_exist_ias': {
                    'set': not_exist_ias,
                    'messages': '<ul><li>В ППР добавлены линки без КПА. Необходимо проверить, что присутствует резервный рабочий линк и отключение КПА не ожидается'
                }
            })

    def perform_checks(self):
        self.check_exist_resources_in_victims()
        self.check_b2b_affected()
        self.check_b2c_affected()
        self.check_ip_changed()
        self.check_vgw_ip_changed()
        self.check_wfc_wfh_ip_changed()
        self.check_old_scheme()
        self.check_offices()
        self.check_itr()
        self.check_rent_vols()
        self.check_stand_dir8()
        self.check_stik_getting_services_from_parther()
        self.check_stik_fvno()
        self.check_l2_channel_between_am()
        self.check_b2b_etherchannel()
        self.check_icc_dpi()
        self.check_ias()

    def check(self):
        self.perform_checks()
        if not self.data:
            self.data.update({
                'good': {
                    'set': None,
                    'messages': 'Особенностей в ППР не обнаружено.',
                }
            })
        return self.data


def save_to_otpm(login, password, dID, comment, uid, trdifperiod, trcuratorphone):
    """Данный метод выполняет запрос в СПП на сохранение комментария"""
    url = 'https://sss.corp.itmh.ru/dem_tr/dem_adv.php'
    data = {'uID': uid,
            'trCuratorPhone': trcuratorphone,
            'trDifPeriod': trdifperiod,
            'action': 'saveSummary',
            'dID': dID,
            'trAdv': comment,
            }
    req = requests.post(url, verify=False, auth=HTTPBasicAuth(login, password), data=data)
    return req.status_code


def accept_to_ortr(login, password, dID, uid, trdifperiod, trcuratorphone):
    """Данный метод выполняет запрос в СПП на сохранение комментария"""
    url = 'https://sss.corp.itmh.ru/dem_tr/dem_adv.php'
    data = {'uID': uid,
            'trCuratorPhone': trcuratorphone,
            'trDifPeriod': trdifperiod,
            'action': 'reciveSummary',
            'dID': dID
            }
    req = requests.post(url, verify=False, auth=HTTPBasicAuth(login, password), data=data)
    return req.status_code


def send_to_otpm(login, password, dID, uid, trdifperiod, trcuratorphone):
    """Данный метод выполняет запрос в СПП на отправление заявки в ОТПМ"""
    url = 'https://sss.corp.itmh.ru/dem_tr/dem_adv.php'
    data = {'uID': uid,
            'trCuratorPhone': trcuratorphone,
            'trDifPeriod': trdifperiod,
            'action': 'sendSummary',
            'dID': dID,
            'trStatus': '50'
            }
    req = requests.post(url, verify=False, auth=HTTPBasicAuth(login, password), data=data)
    return req.status_code


def send_to_otpm_control(login, password, dID, uid, trdifperiod, trcuratorphone):
    """Данный метод выполняет запрос в СПП на отправление заявки в ОТПМ Контроль"""
    url = 'https://sss.corp.itmh.ru/dem_tr/dem_adv.php'
    data = {'uID': uid,
            'trCuratorPhone': trcuratorphone,
            'trDifPeriod': trdifperiod,
            'action': 'sendSummary',
            'dID': dID,
            'trStatus': '83'
            }
    req = requests.post(url, verify=False, auth=HTTPBasicAuth(login, password), data=data)
    return req.status_code


def send_to_pto(login, password, dID, uid, trdifperiod, trcuratorphone):
    """Данный метод выполняет запрос в СПП на отправление заявки в ПТО"""
    url = 'https://sss.corp.itmh.ru/dem_tr/dem_adv.php'
    data = {'uID': uid,
            'trCuratorPhone': trcuratorphone,
            'trDifPeriod': trdifperiod,
            'action': 'sendSummary',
            'dID': dID,
            'trStatus': '82'
            }
    req = requests.post(url, verify=False, auth=HTTPBasicAuth(login, password), data=data)
    return req.status_code


def send_to_accept(login, password, dID, uid, trdifperiod, trcuratorphone):
    """Данный метод выполняет запрос в СПП на отправление упрощенной заявки на принятие"""
    url = 'https://sss.corp.itmh.ru/dem_tr/dem_adv.php'
    data = {'uID': uid,
            'trCuratorPhone': trcuratorphone,
            'trDifPeriod': trdifperiod,
            'action': 'sendSummary',
            'dID': dID,
            'trStatus': '100'
            }
    req = requests.post(url, verify=False, auth=HTTPBasicAuth(login, password), data=data)
    return req.status_code


def send_to_mko(login, password, dID, comment):
    """Данный метод выполняет запрос в СПП на отправление заявки менеджеру"""
    url = 'https://sss.corp.itmh.ru/dem_tr/dem_adv.php'
    data = {'FailText': comment,
            'ActionButton': 'Вернуть в ОПП B2B/ОРКБ',
            'dID': dID,
            'action': 'returnSummary',
            }
    req = requests.post(url, verify=False, auth=HTTPBasicAuth(login, password), data=data)
    return req.status_code


def lost_whitespace(text):
    """Данный метод добавляет пропущенный переход строки в формате А.А или аА или 1А -> А. А или а А или 1 А"""
    text = re.sub('(.+\w)\.([А-Я]\w.+)', lambda m: m.group(1) + '.\n' + m.group(2), text)
    text = re.sub('(.+[а-я])([А-Я]\w.+)', lambda m: m.group(1) + '\n' + m.group(2), text)
    text = re.sub('(.+\d)([А-Я]\w.+)', lambda m: m.group(1) + '\n' + m.group(2), text)
    return text


def spec(username, password):
    """Данный метод выполняет авторизацию sts"""
    data_sts = {'UserName': f'CORP\\{username}', 'Password': f'{password}', 'AuthMethod': 'FormsAuthentication'}
    url = """https://arm.itmh.ru/v3/backend/manager/login/"""
    req = requests.get(url)
    sts_url = req.url
    req = requests.post(sts_url, data=data_sts)
    response = req.content.decode('utf-8')
    regex_wresult = """name="wresult" value="(.+TokenResponse>)"""
    result = re.search(regex_wresult, response, flags=re.DOTALL)
    wwresult = result.group(1)
    wresult = wwresult.replace('&lt;', '<').replace('&quot;', '"')
    soup = BeautifulSoup(response, "html.parser")
    wa = soup.find('input', {"name": "wa"}).get('value')
    wctx = soup.find('input', {"name":"wctx"}).get('value')
    data_arm = {'wa': wa, 'wresult': wresult, 'wctx': wctx}
    req = requests.post(url, data=data_arm)
    cookie = req.request.headers.get('Cookie')
    x_session_id = cookie.split(';')[0].strip('PHPSESSID=')
    return cookie, x_session_id


def get_ploam(username, password, rtk_order):
    url = 'https://sauron.itmh.ru/portal/report/0.0.%20%D0%AD%D0%BA%D1%81%D0%BF%D0%B5%D1%80%D1%82%D0%B8%D0%B7%D0%B0%20%D0%BE%D1%82%D1%87%D0%B5%D1%82%D0%BE%D0%B2/FVNO/%D0%98%D0%BD%D1%84%D0%BE%D1%80%D0%BC%D0%B0%D1%86%D0%B8%D1%8F%20%D0%BE%20%D0%BD%D0%B0%D1%80%D1%8F%D0%B4%D0%B5'
    client = requests.session()
    req = client.get(url)

    soup = BeautifulSoup(req.content.decode('utf-8'), "html.parser")
    sts_url = soup.find('form', id="options").get('action')
    data_sts = {'UserName': f'CORP\\{username}', 'Password': f'{password}', 'AuthMethod': 'FormsAuthentication'}
    req = client.post(sts_url, data=data_sts)

    edge_access_cookie = req.headers.get('Set-Cookie').split(';')[0]
    headers = {'Cookie': edge_access_cookie,
        'User-Agent':
        'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/115.0.0.0 Safari/537.36'
               }
    url = 'https://sauron.itmh.ru/reports/Pages/ReportViewer.aspx?%2F0.0.%20%D0%AD%D0%BA%D1%81%D0%BF%D0%B5%D1%80%D1%82%D0%B8%D0%B7%D0%B0%20%D0%BE%D1%82%D1%87%D0%B5%D1%82%D0%BE%D0%B2%2FFVNO%2F%D0%98%D0%BD%D1%84%D0%BE%D1%80%D0%BC%D0%B0%D1%86%D0%B8%D1%8F%20%D0%BE%20%D0%BD%D0%B0%D1%80%D1%8F%D0%B4%D0%B5'
    req = client.get(url, headers=headers)

    soup = BeautifulSoup(req.content.decode('utf-8'), "html.parser")
    view_state = soup.find(id="__VIEWSTATE").get('value')
    data = {
        'AjaxScriptManager': 'AjaxScriptManager|ReportViewerControl$ctl04$ctl00',
        'ReportViewerControl$ctl04$ctl03$txtValue': rtk_order,
        '__VIEWSTATEGENERATOR': '32461442',
        '__VIEWSTATE': view_state,
        'ReportViewerControl$ctl04$ctl00': 'Просмотр отчета',
        'ReportViewerControl$ctl11': 'standards',
        'ReportViewerControl$AsyncWait$HiddenCancelField': 'False',
        'ReportViewerControl$ToggleParam$collapse': 'false',
        'ReportViewerControl$ctl07$collapse': 'false',
        'ReportViewerControl$ctl09$VisibilityState$ctl00': 'None',
        'ReportViewerControl$ctl09$ReportControl$ctl04': '100',
        '__ASYNCPOST': 'true'

    }
    req = client.post(url, data=data, headers=headers)

    soup = BeautifulSoup(req.content.decode('utf-8'), "html.parser")
    navigation_corrector_new_view_state = soup.find(id="NavigationCorrector_NewViewState").get('value')
    regex = '__VIEWSTATE\|(/.+)\|8\|hiddenField\|'
    match = re.search(regex, req.content.decode('utf-8'))
    new_view_state = match.group(1)
    data = {
        'AjaxScriptManager': 'AjaxScriptManager|ReportViewerControl$ctl09$Reserved_AsyncLoadTarget',
        'NavigationCorrector$NewViewState': navigation_corrector_new_view_state,
        'ReportViewerControl$ctl10': 'ltr',
        'ReportViewerControl$ctl11': 'standards',
        'ReportViewerControl$AsyncWait$HiddenCancelField': 'False',
        'ReportViewerControl$ctl04$ctl03$txtValue': rtk_order,
        'ReportViewerControl$ToggleParam$collapse': 'false',
        'null': '100',
        'ReportViewerControl$ctl07$collapse': 'false',
        'ReportViewerControl$ctl09$VisibilityState$ctl00': 'None',
        'ReportViewerControl$ctl09$ReportControl$ctl04': '100',
        '__EVENTTARGET': 'ReportViewerControl$ctl09$Reserved_AsyncLoadTarget',
        '__VIEWSTATEGENERATOR': '32461442',
        '__VIEWSTATE': new_view_state,
        '__ASYNCPOST': 'true'
    }
    req = client.post(url, data=data, headers=headers)

    soup = BeautifulSoup(req.content.decode('utf-8'), "html.parser")
    ploam = soup.find_all('div', {"class": "canGrowTextBoxInTablix"})[11].text[2:]
    return ploam


def get_gottlieb(rtk_ip):
    rtk_models = {}
    url = 'https://gl-ural.rt-edge.itss.mirasystem.net/login/?path=%2Fsubs%2F%3F'
    client = requests.session()
    token_resp = client.get(url, verify=False)
    soup = BeautifulSoup(token_resp.content.decode('utf-8'), "html.parser")
    token = soup.find(id="csrf_token").get('value')
    data = {'login': GOTTLIEB_USER, 'password': GOTTLIEB_PASSWORD,
            'csrf_token': token}
    client.post(url, verify=False, data=data)

    ajax_url = 'https://gl-ural.rt-edge.itss.mirasystem.net/equipment/ajax/'
    data = {'address': rtk_ip}
    r = client.post(ajax_url, verify=False, data=data)
    suggestions = r.json().get('suggestions')
    tree = ''.join([sug.get('data') for sug in suggestions if sug.get('value').startswith(f'{rtk_ip},')])
    tree_url = f'https://gl-ural.rt-edge.itss.mirasystem.net/api/equipment/tree/{tree}/'
    r = client.get(tree_url, verify=False)
    data = r.json()
    children = True
    while children == True:
        data = data[0].get('children')
        if data[0].get('children'):
            children = True
            parent = data
        else:
            children = False
    node = data[0].get('html')
    node_soup = BeautifulSoup(node, "html.parser")
    rtk_models.update({'Модель коммутатора': node_soup.text.split(',')[-2]})
    parent_node = parent[0].get('html')
    parent_node_soup = BeautifulSoup(parent_node, "html.parser")
    rtk_models.update({'Модель вышестоящего коммутатора': parent_node_soup.text.split(',')[-2]})
    return rtk_models


def get_uplink_data(chain_device, username, password):
    chains = _get_chain_data(username, password, chain_device)
    if chains:
        for chain in chains:
            if chain.get('host_name') == chain_device:
                level = chain.get('level')
                node = chain.get('alias')

        for chain in chains:
            if chain_device in chain.get('title') and chain.get('level') < level:
                uplink = chain.get('host_name')
                uplink_node = chain.get('alias')
                uplink_port = chain.get('title').split(chain_device)[0].split(uplink)[-1][1:-1]
                uplink_port = uplink_port.replace('_', '/')
        return (uplink_node, uplink, uplink_port)


def parsing_stu_switch(chain_device, username, password):
    details_url = None
    url = 'https://cis.corp.itmh.ru/stu/Switch/Search'
    data = {'Name': chain_device, 'IncludeDeleted': 'false'}
    req = requests.post(url, verify=False, auth=(username, password), data=data)
    if req.status_code == 200:
        soup = BeautifulSoup(req.content.decode('utf-8'), "html.parser")
        details = [a['href'] for a in soup.find_all('a') if '/stu/Switch/Details/' in a['href']]
        if len(details) > 1:
            all_a = soup.find_all('a')
            model, node = _parsing_model_and_node_client_device_by_device_name(chain_device, username, password)
            for index, a in enumerate(all_a):
                if '/stu/Switch/Details/' in a['href'] and all_a[index - 1].text == node:
                    details_url = a['href']
        else:
            details_url = details[0]
        req = requests.get('https://cis.corp.itmh.ru' + details_url, verify=False, auth=(username, password))
        if req.status_code == 200:
            return req.content.decode('utf-8')


def get_switch_data(chain_device, stu_data, uplink_data):
    model = None
    node = None
    soup = BeautifulSoup(stu_data, "html.parser")
    table_switch = soup.find_all('table')[0]
    tds = table_switch.find_all('td')
    for index, td in enumerate(tds):
        if 'Модель' in td.text:
            if tds[index+1].text.startswith('S'):
                model = 'SNR ' + tds[index+1].text
            elif tds[index+1].text.startswith('D'):
                model = 'D-link ' + tds[index+1].text
            elif tds[index+1].text.startswith('A'):
                model = 'Orion ' + tds[index+1].text
            else:
                model = tds[index+1].text
        if 'Узел связи' in td.text:
            node = tds[index + 1].find('a').text

    table_ports_desc = soup.find_all('table')[2]
    tds = table_ports_desc.find_all('td')
    gig_ports = {}
    for index, td in enumerate(tds):
        if 'SFP' in td.text or 'GBIC' in td.text:
            if tds[index+2].find('a').text:
                gig_ports.update({td.text: tds[index+2].find('a').text})
            elif tds[index+2].text:
                gig_ports.update({td.text: tds[index+2].text.strip()})
        elif 'RJ45' in td.text:
            if td.text[:td.text.index('[')]+'[SFP]' in gig_ports.keys():
                if tds[index + 2].find('a').text:
                    gig_ports.update({td.text: tds[index + 2].find('a').text})
                elif tds[index + 2].text:
                    gig_ports.update({td.text: tds[index + 2].text.strip()})
    uplink_node, uplink, uplink_port = uplink_data
    gig_ports = {k:v for k, v in gig_ports.items() if v and not f'{uplink}, {uplink_port}' in v }
    for k, v in gig_ports.items():
        if chain_device in v:
            for i in v.split(' - '):
                if chain_device not in i:
                    gig_ports.update({k: i.split(',')[0]})
    return (model, node, gig_ports)


def parsing_switches_by_model(name, login, password):
    """Данный метод получает на входе модель КАД и по нему парсит страницу с поиском коммутатров, чтобы определить
	название коммутатора и ip-адрес"""
    url = 'https://cis.corp.itmh.ru/stu/NetSwitch/SearchNetSwitchProxy'
    data = {'IncludeDeleted': 'false', 'IncludeDisabled': 'false', 'HideFilterPane': 'false'}
    data['ModelName'] = name
    req = requests.post(url, verify=False, auth=HTTPBasicAuth(login, password), data=data)
    if req.status_code == 200:
        soup = BeautifulSoup(req.json()['data'], "html.parser")
        table = soup.find('div', {"class": "t-grid-content"})
        trs = table.find_all('tr')
        switches = {tr.find_all('td')[0].text.strip(): tr.find_all('td')[3].text.strip() for tr in trs}
        return switches
