import requests
import re
from bs4 import BeautifulSoup
from requests.auth import HTTPBasicAuth

from tickets.parsing import get_connection_point, lost_whitespace
import urllib3
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)


def ckb_parse(login, password):
    """Данный метод парсит страницу КБЗ с Типовыми блоками ТР"""
    templates = {}
    url = 'https://ckb.itmh.ru/pages/viewpage.action?pageId=729843023'
    req = requests.get(url, verify=False, auth=HTTPBasicAuth(login, password))
    soup = BeautifulSoup(req.content.decode('utf-8'), "html.parser")
    search = soup.find_all('pre', {'class': 'syntaxhighlighter-pre'})
    for item in search:
        regex = '(.+)'
        match = re.search(regex, item.text)
        title = match.group(1)
        templates[title] = item.text
    return templates


def dispatch(login, password, trID):
    url = 'https://sss.corp.itmh.ru/dem_tr/dem_ajax.php'
    data = {'action': 'GetOtu', 'trID': f'{trID}'}
    req = requests.post(url, verify=False, auth=HTTPBasicAuth(login, password), data=data)
    if not req.json().get('id'):
        data = {'action': 'CreateOtu', 'trID': f'{trID}'}
        requests.post(url, verify=False, auth=HTTPBasicAuth(login, password), data=data)
        data = {'action': 'GetOtu', 'trID': f'{trID}'}
        req = requests.post(url, verify=False, auth=HTTPBasicAuth(login, password), data=data)
    id_otu = req.json().get('id')
    return id_otu


def in_work_otpm(login, password):
    """Данный метод парсит страницу с пулом ОТПМ в СПП и отфильтровывает заявки с кураторами DIR 2.4.1"""
    lines = []
    url = 'https://sss.corp.itmh.ru/dem_tr/demands.php?tech_uID=0&trStatus=inWorkOTPM' +\
          '&curator=any&vName=&dSearch=&bID=1&searchType=param'
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
        search_demand_sl = soup.find_all('td', class_='demand_sl')[num:]


        for index in range(len(search_demand_num2)-1):
            wanted_stat = ['В работе ОТПМ', 'Контроль и выпуск ТР', 'В работе ПТО']
            if search_demand_stat[index].text not in wanted_stat:
                continue
            if lines and lines[-1][0] == search_demand_num2[index].text:
                lines[-1][3] = lines[-1][3] + ' ' + search_demand_point[index].text
                continue
            #else:
            if search_demand_sl[index]["style"] == "background-color: #FEC0CB":
                difficulty = 'Сложное'
            elif search_demand_sl[index]["style"] == "background-color: #99FF99":
                difficulty = 'Простое'
            elif search_demand_sl[index]["style"] == "background-color: #FFFFCC":
                difficulty = 'Оценка'
            else:
                difficulty = '???'
            lines.append([search_demand_num2[index].text,
                          search_demand_num2[index].find('a').get('href')[(search_demand_num2[index].find('a').get('href').index('=')+1):],
                          search_demand_cust[index].text,
                          search_demand_point[index].text,
                          lost_whitespace(search_demand_tech[index].text),

                          search_demand_stat[index].text,
                          f'{difficulty}',])
                          #search_demand_cur[index].text]

        for index in range(len(lines)):
            lines[index].append('Не взята в работу')
            if 'ПТО' in lines[index][0]:
                lines[index][0] = lines[index][0][:lines[index][0].index('ПТО')]
                lines[index].append('ПТО')
            else:
                lines[index].append('Коммерческая')
            for symbol_index in range(1, len(lines[index][3])):
                if lines[index][3][symbol_index].isupper() and lines[index][3][symbol_index-1].islower():
                    lines[index][3] = lines[index][3][:symbol_index]+' '+lines[index][3][symbol_index:]
                    break
        if lines == []:
            lines.append(['Empty list tickets'])

    else:
        lines.append('Access denied')
    return lines


def construct_table_nodes(search):
    entries = []
    for tr in search:
        c3 = tr.find_all('td', class_="C3")
        output_city = c3[0].text
        output_street = lost_whitespace(c3[1].text)
        c11 = tr.find('td', class_="C11")
        output_house = '\n'.join(c11.find_all(text=True))  # recursive=False
        c9 = tr.find('td', class_="C9")
        output_spd = ''.join(c9.find_all(text=True))
        aid = tr['aid']
        entries.append([output_city, output_street, output_house, output_spd, aid])
    return entries

def get_spp_addresses(login, password, city, street, house):
    """Данный метод парсит страницу с адресами в СПП"""
    lines = []
    data = {
        'distr_adm': 'any',
        'distr_mark': 'any',
        'distr_pto': 'any',
        'hideWithOutSPD': 0,
        'aCity': city,
        'aStreet': street,
        'aHouse': house,
        'aTP': 'any',
        'vStatus': 'any',
        'showAll': 0,
        'activeSeach': 1,
        'mode': 'selectAV',
        'parent': 0,
    }
    url = 'https://sss.corp.itmh.ru/building/address.php'
    req = requests.post(url, verify=False, auth=HTTPBasicAuth(login, password), data=data)
    if req.status_code == 200:
        soup = BeautifulSoup(req.content.decode('utf-8'), "html.parser")
        search = soup.find_all('tr')
        node_entries = construct_table_nodes(search)
        return node_entries


def get_nodes_by_address(login, password, aid):
    url = f'https://sss.corp.itmh.ru/building/address_spd.php?aID={aid}&mode=selectAV&parent=0'
    req = requests.get(url, verify=False, auth=HTTPBasicAuth(login, password))
    if req.status_code == 200:
        soup = BeautifulSoup(req.content.decode('utf-8'), "html.parser")
        table_nodes = soup.find_all('table', class_="nice")[1]
        trs = table_nodes.find_all('tr')[1:]
        entries = []
        for tr in trs:
            node_vid = tr['vid']
            tds = tr.find_all('td')
            node_type = tds[1].text
            node_name = tds[3].text
            node_parent_id = tds[4].text
            node_id = tds[5].text
            node_status = tds[6].text
            entries.append((node_vid, node_type, node_name, node_parent_id, node_id, node_status))
        return entries


def get_initial_node(login, password, ticket_tr):
    url = f'https://sss.corp.itmh.ru/building/address.php?mode=selectAV&aID={ticket_tr.aid}&parent=0'
    req = requests.get(url, verify=False, auth=HTTPBasicAuth(login, password))
    if req.status_code == 200:
        soup = BeautifulSoup(req.content.decode('utf-8'), "html.parser")
        search = soup.find_all('tr')
        node_entries = construct_table_nodes(search)
        return node_entries



def get_spp_stage(login, password, dID):
    stage = None
    url = f'https://sss.corp.itmh.ru/dem_tr/dem_adv_control.php?dID={dID}'
    req = requests.get(url, verify=False, auth=HTTPBasicAuth(login, password))
    if req.status_code == 200:
        soup = BeautifulSoup(req.content.decode('utf-8'), "html.parser")
        stage = soup.find('input', id='ip_1').get('value')
    return stage


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
                spp_params['Сложность'] = i.find_all('td')[3].text.strip()
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
                spp_params['Примечание'] = lost_whitespace(i.find_all('td')[1].text.strip())
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
        aid_link = soup.find('a', class_='nodec')['href']
        match = re.search(r'php\?aID=(\d+)', aid_link)
        aid = match.group(1) if match else None
        spp_params['aid'] = aid
        tr_without_os = soup.find('input', {"name": "trWithoutOS"}).get('checked')
        spp_params['tr_without_os'] = True if tr_without_os else False

        tr_complex_access = soup.find('input', {"name": "trComplexAccess"}).get('checked')
        spp_params['tr_complex_access'] = True if tr_complex_access else False
        if tr_complex_access:
            tr_complex_access_input = soup.find('textarea', {"name": "trComplexAccessInput"}).text.strip()
            spp_params['tr_complex_access_input'] = tr_complex_access_input

        tr_turn_off = soup.find('input', {"name": "trTurnOff"}).get('checked')
        spp_params['tr_turn_off'] = True if tr_turn_off else False
        if tr_turn_off:
            tr_turn_off_input = soup.find('textarea', {"name": "trTurnOffInput"}).text.strip()
            spp_params['tr_turn_off_input'] = tr_turn_off_input

        tr_complex_equip = soup.find('input', {"name": "trComplexEquip"}).get('checked')
        spp_params['tr_complex_equip'] = True if tr_complex_equip else False
        if tr_complex_equip:
            tr_complex_equip_input = soup.find('textarea', {"name": "trComplexEquipInput"}).text.strip()
            spp_params['tr_complex_equip_input'] = tr_complex_equip_input

        search = soup.find_all('tr')
        for index, i in enumerate(search):
            if 'Перечень' in i.find_all('td')[0].text:
                services_text = [x.text for x in i.find_all('td') if x.text and not x.text.startswith('\n')]
                services = [x for x in services_text if x not in ('Переченьтребуемых услуг', 'Услуга', 'Описание')]
                for x in range(len(services)//2):
                    services[x] = services[x] + ' ' + services[x+1]
                    services.pop(x+1)
                spp_params['services_plus_desc'] = services
            elif 'Информация дляразработки ТР' in i.find_all('td')[0].text:
                #spp_params['Информация для разработки ТР'] = i.find_all('td')[1].text
                spp_params['info_tr'] = i.find_all('td')[1].text.strip()
            elif 'Место размещенияточки подключения' in i.find_all('td')[0].text:
                spp_params['place_connection_point'] = i.find_all('td')[1].text.strip()
            elif 'Узел подключения клиента' in i.find_all('td')[0].text:
                node = re.search(r'\t(.+)\s+Статус', i.find_all('td')[1].text)
                if 'Изменить' in i.find_all('td')[0].text:
                    spp_params['node'] = node.group(1)
                else:
                    spp_params['node'] = 'Узел не выбран'

        search2 = soup.find_all('form')
        form_data = search2[1].find_all('input')
        for i in form_data:
            if i.attrs['type'] == 'hidden':
                if i['name'] == 'vID':
                    spp_params[i['name']] = i['value']

        parts_address = {'tCity':'г. ', 'tStreet':'ул. ', 'tHouse':'д. ', 'tCorp':'корп. ',
                         'tBild':'стр. ', 'tOffice':'оф. ', 'tIndex':'инд. '}
        address = []
        for part_address in parts_address.keys():
            if soup.find('input', {"name": f'{part_address}'}).get('value'):
                value = soup.find('input', {"name": f'{part_address}'}).get('value')
                address.append(parts_address[part_address] + value)
        address = ', '.join(address)
        spp_params['address'] = address
        return spp_params
    else:
        spp_params['Access denied'] = 'Access denied'
        return spp_params



def send_to_mko(login, password, ticket_spp, comment=None):
    """Данный метод выполняет запрос в СПП на отправление заявки менеджеру"""
    url = 'https://sss.corp.itmh.ru/dem_tr/dem_adv.php'
    data = {'FailText': comment,
            'ActionButton': 'Вернуть в ОПП B2B/ОРКБ',
            'dID': ticket_spp.dID,
            'action': 'returnSummary',
            }
    req = requests.post(url, verify=False, auth=HTTPBasicAuth(login, password), data=data)
    return req.status_code


def save_comment(login, password, comment, ticket_spp):
    """Данный метод выполняет запрос в СПП на сохранение комментария"""
    url = 'https://sss.corp.itmh.ru/dem_tr/dem_adv.php'
    data = {'uID': ticket_spp.uID,
            'trCuratorPhone': ticket_spp.trcuratorphone,
            'trDifPeriod': ticket_spp.trdifperiod,
            'action': 'saveSummary',
            'dID': ticket_spp.dID,
            'trAdv': comment,
            }
    req = requests.post(url, verify=False, auth=HTTPBasicAuth(login, password), data=data)
    return req.status_code


def spp_send_to(login, password, ticket_spp, send_to):
    """Данный метод выполняет запрос в СПП на отправление заявки"""
    url = 'https://sss.corp.itmh.ru/dem_tr/dem_adv.php'
    data = {'uID': ticket_spp.uID,
            'trCuratorPhone': ticket_spp.trcuratorphone,
            'trDifPeriod': ticket_spp.trdifperiod,
            'action': 'sendSummary',
            'dID': ticket_spp.dID,
            'trStatus': send_to
            }
    req = requests.post(url, verify=False, auth=HTTPBasicAuth(login, password), data=data)
    return req.status_code


def send_spp_check(login, password, dID, tID, trID):
    url = f'https://sss.corp.itmh.ru/dem_tr/dem_point.php?dID={dID}&tID={tID}&trID={trID}'
    req_check = requests.get(url, verify=False, auth=HTTPBasicAuth(login, password))
    return req_check

def send_spp(login, password, ticket_tr):
    dID = ticket_tr.ticket_k.dID
    tID = ticket_tr.ticket_cp
    trID = ticket_tr.ticket_tr
    url = f'https://sss.corp.itmh.ru/dem_tr/dem_point.php?dID={dID}&tID={tID}&trID={trID}'
    print('dID')
    print(dID)
    print('tID')
    print(tID)
    print('trID')
    print(trID)
    vID = ticket_tr.vID
    print('vID')
    print(vID)
    # trTurnOff = None  # для отключения
    # trTurnOffInput = None
    # data = {'FileLink': 'файл', 'action': 'saveVariant',
    #         'vID': vID, 'trID': trID}
    # headers
    # 'Content-Type': multipart/form-data; boundary
    tr_without_os = 1 if ticket_tr.tr_without_os else 0
    tr_complex_access = 1 if ticket_tr.tr_complex_access else 0
    tr_complex_equip = 1 if ticket_tr.tr_complex_equip else 0
    tr_turn_off = 1 if ticket_tr.tr_turn_off else 0
    tr_complex_access_input = ticket_tr.tr_complex_access_input
    tr_complex_equip_input = ticket_tr.tr_complex_equip_input
    tr_turn_off_input = ticket_tr.tr_turn_off_input
    trOTPM_Resolution = ticket_tr.oattr
    print('tr_complex_access')
    print(tr_complex_access)
    print('tr_complex_access_input')
    print(tr_complex_access_input)
    data = {'trOTPM_Resolution': trOTPM_Resolution,
            'trWithoutOS': tr_without_os,
            'trComplexAccess': tr_complex_access,
            'trComplexEquip': tr_complex_equip,
            'trTurnOff': tr_turn_off,
            'trComplexAccessInput': tr_complex_access_input,
            'trComplexEquipInput': tr_complex_equip_input,
            'trTurnOffInput': tr_turn_off_input,

            'action': 'saveVariant',
            'vID': vID}
    requests.post(url, verify=False, auth=HTTPBasicAuth(login, password), data=data)


import json

def get_tentura(login, password):
    url = 'https://tentura.corp.itmh.ru/?mode=project_objects&project_id=39203&active_project_id=39203'
    client = requests.session()
    req = client.get(url, verify=False, auth=HTTPBasicAuth(login, password))

    url = 'https://tentura.corp.itmh.ru/ajax2/'

    # data = #{"method":"url_sss_get","params":[], "id":'14107'}  # первый пример запроса


    data_project_objects_get = {"id":'32750',"method":"project_objects_get","params":["39203"]}     # Объекты добавленные в проект

    # {"id":11477,"method":"project_context_get","params":["39203"]} возвращает 55284, которое потом может пригодиться

    data_get_matched_addresses = {"id":38722,"method":"get_matched_addresses","params":["Куйбышева, 10", True]} # ищется соответствующий адрес в поиске



    # при выборе одного из id выполняется запрос {"id": 21984, "method": "get_construction_center", "params": [2170]}
    # {"id": 21984, "result": "{\"lon\":60.5925425,\"lat\":56.82529985}"}

    # потом выполняются методы get_buildings и get_gis_objects с координатами вокруг объекта, на основе них открывается нужное место
    # на карте и объекты попадающие в эту область, они будут не нужны, заполняем коорединаты вручную по 0.0015 в каждую сторону
    # 60,5910425     60.5940425     56.82379985     56.82679985

    data_set_ioc_filter = {"id": 32202, "method": "set_ioc_filter", "params": [55284, [258, 281, 330, 331, 332, 333], 79]} # применение фильтра только по КК, АВ, УА, РУА

    data_get_gis_objects = {"id": 59360, "method": "get_gis_objects", "params": [55284,
                                                                 {"left": 60.5910425, "right": 60.5940425,
                                                                  "bottom": 56.82379985,
                                                                  "top": 56.82679985}]}

    # затем проходиться по всем объектам и вызывать

    data_get_binded_objects = {"id": 14081, "method": "get_binded_objects", "params": [70252, 55284]}

    # получение названия узла через data_get_binded_objects
    # result = req.json().get('result')
    # kk = json.loads(result)
    # node = kk[0]['name_with_name_attribute']
    # 2.2.2.АВ (#5075) ЕКБ Куйбышева 10 П2 (тех.этаж), АВ
    # по ключу id можно получить сам айдишник


    # добавление узла в проект
    project = 39203
    # identificator = 70013
    # node = 2273
    # data = {"id": 14081, "method": "get_binded_objects", "params": [identificator, 55284]}
    #
    # req = client.post(url, verify=False, auth=HTTPBasicAuth(login, password), data=json.dumps(data))
    #
    # result = req.json().get('result')
    # binded_objects = json.loads(result)[0]
    # project_registers = binded_objects.get('projectRegisters')
    # plan_registers = binded_objects.get('planRegisters')
    # status_registers = binded_objects.get('statusRegisters')
    #
    # query_status = []
    # for status_register in status_registers:
    #     if status_register.get('RegisterRecord'):
    #         record = status_register.get('RegisterRecord')
    #         query_status.append({
    #             "IsActual": True,
    #             "RegisterId": record.get('RegisterId'),
    #             "RegisterRecord": {"Id": record.get('Id'), "IsActual": True, "ProjectId": record.get('ProjectId')}
    #         })
    #     else:
    #         query_status.append({"IsActual": False, "RegisterId": status_register.get('RegisterId'), "RegisterRecord": None})
    #
    # query = []
    # for registers in (project_registers, plan_registers):
    #     subquery = []
    #     for project_register in registers:
    #         if project_register.get('RegisterRecords'):
    #             records = project_register.get('RegisterRecords')
    #             query_record = []
    #             for record in records:
    #                 query_record.append(
    #                     {"Id": record.get('Id'), "IsActual": True, "ProjectId": record.get('ProjectId')}
    #                 )
    #             query_record.append({"Id": None, "IsActual": True,"ProjectId": project})
    #             subquery.append({"IsActual": True, "RegisterId": project_register.get('RegisterId'), "RegisterRecords": query_record})
    #         elif project_register.get('RegisterName') == 'Проектируемые к реконструкции':
    #             subquery.append({"IsActual": True, "RegisterId": project_register.get('RegisterId'),
    #                              "RegisterRecords": [{"Id": None, "IsActual": True,"ProjectId": project}]})
    #         else:
    #             subquery.append(
    #                 {"IsActual": False, "RegisterId": project_register.get('RegisterId'), "RegisterRecords": None})
    #     query.append(subquery)
    #
    # query_project = query[0]
    # query_plan = query[1]
    # result_query = {"id":5555, "method":"update_io_registers", "params":[node, query_status, query_plan, query_project]}
    #
    # req = client.post(url, verify=False, auth=HTTPBasicAuth(login, password), data=json.dumps(result_query))

    # Добавление ЦСП в проект
    # по адресу ищутся все подходящие объекты
    data_get_matched_addresses = {"id": 5555, "method": "get_matched_addresses", "params": ["Малышева, 28", True]}

    # нужен вывод полученного списка и выбор одного из id, далее выполняется запрос по id
    data_get_construction_center = {"id": 5555, "method": "get_construction_center", "params": [2459]}
    # {"id":42015,"result":"{\"lon\":60.593568271428573,\"lat\":56.833121157142855}"}
    req = client.post(url, verify=False, auth=HTTPBasicAuth(login, password), data=json.dumps(data_get_construction_center))
    print('!!')
    result = req.json().get('result')
    result = json.loads(result)
    lon = result.get('lon')
    lat = result.get('lat')
    horizontal_offset = 0.0001
    vertical_offset = 0.0001
    lon += horizontal_offset
    lat += vertical_offset
    print(lon)
    print(lat)
    address = 'Малышева28'

    data_create_csp = {
        "id":5555, "method":"create_object", "params": [{
            "inventory_objects_class":1138,
            "attributes": [
                {"id":2448,"name":"Помещение","value": address,"isDirty":True,"isNullable":False},
                {"id":2443,"name":"Адрес","value": address,"isDirty":True,"isNullable":False},
                {"id":59,"name":"Дата постройки","value":"30.08.2023","isDirty":True,"isNullable":False},
                {"id":178,"name":"Основание размещения","value":"","isDirty":False,"isNullable":True},
                {"id":31,"name":"Наименование","value":"","isDirty":False,"isNullable":True},
                {"id":34,"name":"Фотографии","value":"","isDirty":False,"isNullable":True},
                {"id":79,"name":"Владелец","value":"ООО «Комтехцентр»","isDirty":True,"isNullable":False},
                {"id":80,"name":"Примечание","value":"","isDirty":False,"isNullable":True},
                {"id":2447,"name":"ГИС: точка привязки","value":f"POINT({lon} {lat})","isDirty":True,"isNullable":True}
            ],
            "project": {
                "id":project,"_checked":True,
                "registers": [
                    {"r2pt":2,"_checked":False},
                    {"r2pt":3,"_checked":False},
                    {"r2pt":4,"_checked":False},
                    {"r2pt":5,"_checked":False},
                    {"r2pt":6,"_checked":False},
                    {"r2pt":7,"_checked":False},
                    {"r2pt":8,"_checked":False},
                    {"r2pt":12,"_checked":True},
                    {"r2pt":13,"_checked":False},
                    {"r2pt":14,"_checked":False}
                ],
                "checked_register":12
            },
            "includes":[]
        }]
    }

    req = client.post(url, verify=False, auth=HTTPBasicAuth(login, password),
                      data=json.dumps(data_create_csp))
    print(req.json())