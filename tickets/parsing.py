import requests
from requests.auth import HTTPBasicAuth
import re
from bs4 import BeautifulSoup
import datetime



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
    return counter_line_services, hotspot_points, services_plus_desc


def parse_tr(login, password, url):
    """Данный метод парсит ТР в СПП и возвращает полученные данные о ТР"""
    url = url.replace('dem_begin', 'dem_point')
    req = requests.get(url, verify=False, auth=HTTPBasicAuth(login, password))
    if req.status_code == 200:
        parsed = req.content.decode('utf-8')
        # Получение данных среды передачи с блока "ОТПМ"
        sreda = None
        wer = []
        wer.append(req.content.decode('utf-8'))
        regex_env = 'Время на реализацию, дней</td>\r\n<td colspan="2">\d+</td>\r\n</tr>\r\n\r\n\r\n\r\n\r\n\r\n<tr av_req="1">\r\n<td colspan="3" align="left">\r\n(.+)</td>\r\n</tr>\r\n\r\n\r\n\r\n<tr obt_req'
        match_env = re.search(regex_env, parsed, flags=re.DOTALL)
        try:
            oattr = match_env.group(1)
            oattr = oattr.replace('<br />', '').replace('&quot;', '"').replace('&amp;', '&')

            if ((not 'ОК' in oattr) and ('БС ' in oattr)) or (
                    (not 'ОК' in oattr) and ('радио' in oattr)) or (
                    (not 'ОК' in oattr) and ('радиоканал' in oattr)) or ((not 'ОК' in oattr) and ('антенну' in oattr)):
                sreda = '3'
            elif ('Alpha' in oattr) or (('ОК-1' in oattr) and (not 'ОК-16' in oattr)):
                sreda = '4'
            elif ('ОВ' in oattr) or ('ОК' in oattr) or ('ВОЛС' in oattr) or ('волокно' in oattr) or (
                    'ОР ' in oattr) or ('ОР№' in oattr) or ('сущ.ОМ' in oattr) or ('оптическ' in oattr):
                sreda = '2'
            else:
                sreda = '1'
        except AttributeError:
            sreda = '1'
            oattr = None

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

        # проходим по списку услуг чтобы определить количество организуемых линий от СПД и в той услуге, где требуется
        # добавляем спец. символ
        counter_line_services, hotspot_points, services_plus_desc = _counter_line_services(services_plus_desc)

        pps = None
        turnoff = None

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

        # Получение данных с блока "Отключение"
        match_turnoff = None
        regex_turnoff = 'INPUT  disabled=\'disabled\' id=\'trTurnOff'
        match_turnoff = re.search(regex_turnoff, parsed)
        if match_turnoff is None:
            turnoff = True
        else:
            turnoff = False

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

        regex_manager = 'Менеджер клиента            </td>\r\n            <td align="left" colspan="3">\r\n(.+)</td>'
        match_manager = re.search(regex_manager, parsed)
        try:
            manager = match_manager.group(1)
            manager = ' '.join(manager.split())
        except AttributeError:
            manager = None
        regex_technolog = 'Технологи\r\n            </td>\r\n            <td align="left" colspan="3">\r\n(.+)</td>'
        match_technolog = re.search(regex_technolog, parsed)
        technolog = match_technolog.group(1)
        technolog = ' '.join(technolog.split())

        regex_task_otpm = 'Задача в ОТПМ\r\n(?:\s+)</td>\r\n(?:\s+)<td colspan="3" valign="top">(.+)</td>'
        match_task_otpm = re.search(regex_task_otpm, parsed, flags=re.DOTALL)
        task_otpm = match_task_otpm.group(1)
        task_otpm = task_otpm[:task_otpm.find('</td>')]
        task_otpm = ' '.join(task_otpm.split())

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


def match_cks(tochka, login, password):
    """Данный метод получает в параметр tochka(где содержатся dID и tID), по этим данным парсит страницу ТР
     (Точки подключения) и получает список всех точек подключения"""
    list_cks = []
    url = 'https://sss.corp.itmh.ru/dem_tr/dem_point_panel.php?dID={}&amp;tID={}'.format(tochka[0], tochka[1])
    req = requests.get(url, verify=False, auth=HTTPBasicAuth(login, password))
    if req.status_code == 200:
        cks_parsed = req.content.decode('utf-8')
        regex_cks = '\'>&nbsp;(.+?)&nbsp;<'
        match_cks = re.finditer(regex_cks, cks_parsed)
        for i in match_cks:
            list_cks.append(i.group(1))
        return list_cks
    else:
        list_cks.append('Access denied')
        return list_cks

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
            for i in clear_switch_id:
                ports = {}
                url_switch_id = 'https://cis.corp.itmh.ru/stu/Switch/Details/' + i
                req_switch_id = requests.get(url_switch_id, verify=False, auth=HTTPBasicAuth(login, password))
                switch_id = req_switch_id.content.decode('utf-8')

                regex_total_ports = 'for=\"TotalPorts\">([-+]?\d+)<'
                match_total_ports = re.search(regex_total_ports, switch_id)
                ports['Всего портов'] = match_total_ports.group(1)

                regex_client_ports = 'for=\"ClientCableUsedPorts\">([-+]?\d+)<'
                match_client_ports = re.search(regex_client_ports, switch_id)
                ports['Занятых клиентами'] = match_client_ports.group(1)

                regex_link_ports = 'for=\"LinkUsedPorts\">([-+]?\d+)<'
                match_link_ports = re.search(regex_link_ports, switch_id)
                ports['Занятых линками'] = match_link_ports.group(1)

                regex_avail_ports = 'for=\"AvailablePorts\">([-+]?\d+)<'
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
    else:
        list_switches = []
        list_switches.append('Access denied')
        return list_switches


def ckb_parse(login, password):
    """Данный метод парсит страницу КБЗ с Типовыми блоками ТР"""
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
            for row_td in row_tr.find_all('td'):
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
        soup = BeautifulSoup(req.json()['data'], "html.parser")
        table = soup.find('div', {"class": "t-grid-content"})
        row_tr = table.find('tr')
        model = row_tr.contents[1].text
        node = row_tr.find('a', {"class": "netswitch-nodeName"}).text
        node = ' '.join(node.split())
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


def check_contract_phone_exist(login, password, contract_id):
    """Данный метод получает ID контракта и парсит вкладку Ресурсы в Cordis, проверяет налиличие ресурсов
    Телефонный номер и возвращает список точек подключения, на которых есть такой ресурс"""
    url = f'https://cis.corp.itmh.ru/doc/CRM/contract.aspx?contract={contract_id}&tab=4'
    req = requests.get(url, verify=False, auth=HTTPBasicAuth(login, password))
    soup = BeautifulSoup(req.content.decode('utf-8'), "html.parser")
    table = soup.find('table', id="ctl00_middle_ResourceContent_ContractResources_RadGrid_Resources_ctl00")
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


def for_tr_view(login, password, dID, tID, trID):
    """Данный метод принимает в качестве параметров параметры ТР в СПП, парсит страницу с данным ТР в СПП и возвращает
        данные о ТР."""
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
                    service = service[:-1]
                    total_services.append(service)
                spp_params['Перечень требуемых услуг'] = total_services
            elif 'Информация для' in i.find_all('td')[0].text:
                spp_params['Информация для разработки ТР'] = i.find_all('td')[1].text
            elif 'Узел подключения клиента' in i.find_all('td')[0].text:
                node = re.search(r'\t(.+)\s+Статус', i.find_all('td')[1].text)
                if 'Изменить' in i.find_all('td')[0].text:
                    spp_params['Узел подключения клиента'] = node.group(1)
                else:
                    spp_params['Узел подключения клиента'] = url
            elif 'Отключение' in i.find_all('td')[0].text and len(i.find_all('td')) > 1:
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
        for index in range(len(search_demand_num2)-1):
            if search_demand_cur[index].text in ['Бражкин П.В.', 'Короткова И.В.', 'Полейко А.Л.', 'Полейко А. Л.']:
                pass
            else:
                if lines and lines[-1][0] == search_demand_num2[index].text:
                    lines[-1][3] = lines[-1][3] + ' ' + search_demand_point[index].text
                else:
                    lines.append([search_demand_num2[index].text, search_demand_num2[index].find('a').get('href')[(search_demand_num2[index].find('a').get('href').index('=')+1):], search_demand_cust[index].text, search_demand_point[index].text,
                          search_demand_tech[index].text, search_demand_cur[index].text])
        for index in range(len(lines)):
            if 'ПТО' in lines[index][0]:
                lines[index][0] = lines[index][0][:lines[index][0].index('ПТО')]+' '+lines[index][0][lines[index][0].index('ПТО'):]
            for symbol_index in range(1, len(lines[index][3])):
                if lines[index][3][symbol_index].isupper() and lines[index][3][symbol_index-1].islower():
                    lines[index][3] = lines[index][3][:symbol_index]+' '+lines[index][3][symbol_index:]
                    break
        if lines == []:
            lines.append('Empty list tickets')
    else:
        lines.append('Access denied')
    return lines


def get_sw_config(sw, login, password):
    """Данный метод парсит конфиг коммутатора со stash"""
    url = 'https://stash.itmh.ru/projects/NMS/repos/pantera_extrim/raw/backups/' + sw + '-config?at=refs%2Fheads%2Fmaster'
    req = requests.get(url, verify=False, auth=HTTPBasicAuth(login, password))

    if req.status_code == 404:
        switch_config = None
    else:
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

    if len(contract_list) == 1:
        id_contract = (contract_list[0]['ID'])

        url_id_contract = f'https://cis.corp.itmh.ru/mvc/Demand/MaintenanceSimList?contract={id_contract}'
        req = requests.get(url_id_contract, verify=False, auth=HTTPBasicAuth(login, password))
        resources = req.json()

        for resource in resources:
            if resource['SimName'] == ppr_resource:
                url = 'https://cis.corp.itmh.ru/mvc/Demand/MaintenanceObjectAddSim'
                data = {'contract_name': contract, 'sim': resource['Sim'], 'demand': ppr}
                req = requests.post(url, verify=False, auth=HTTPBasicAuth(login, password), data=data)
                if req.status_code == 200:
                    return ('added', disable_resource)
                return ('error', disable_resource)
    return ('Более одного контракта', contract_list)


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
                if ppr_port in port['Name']:
                    found_ports.append(port)
            for found_port in found_ports:
                url = 'https://cis.corp.itmh.ru/mvc/Demand/MaintenanceObjectAddLink'
                data = {'device_name': sw, 'device_port': found_port['id'], 'demand': ppr}
                req = requests.post(url, verify=False, auth=HTTPBasicAuth(login, password), data=data)

                if f'{sw} [<span class="port_name">{ppr_port}</span>]' in req.content.decode('utf-8'):
                    return ('added', disable_resource)
            return ('error', disable_resource)
    return ('не оказалось в списке коммутаторов', sw)


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
        pprs = [link.text for link in links if link.text != ' ']
        last_ppr = pprs[0]
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