import datetime

import requests
import re
import random
from bs4 import BeautifulSoup
from requests.auth import HTTPBasicAuth


from oattr.request_templates import SpecTemplate
from tickets.parsing import lost_whitespace
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


def get_or_create_otu(login, password, trID):
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

def send_spp(login, password, ticket_tr, department):
    dID = ticket_tr.ticket_k.dID
    tID = ticket_tr.ticket_cp
    trID = ticket_tr.ticket_tr
    url = f'https://sss.corp.itmh.ru/dem_tr/dem_point.php?dID={dID}&tID={tID}&trID={trID}'
    vID = ticket_tr.vID
    if department == 'ortr':
        data = {'action': 'saveVariant', 'vID': vID}
    else:
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

class Tentura:
    URL = 'https://tentura.corp.itmh.ru/ajax2/'
    def __init__(self, username, password, otu_project_id):
        self.client = requests.session()
        self.username = username
        self.password = password
        self.otu_project_id = otu_project_id

    def check_active_project_for_user(self):
        data = {"id": 5555, "method": "set_active_project_for_user", "params": [self.otu_project_id]}
        return self.__connection(data)

    def __connection(self, data):
        req = self.client.post(self.URL, verify=False, auth=HTTPBasicAuth(self.username, self.password), data=json.dumps(data))
        if req.status_code == 401:
            return {'error': 'Нет доступа. Неверный логин/пароль.'}
        return req.json()

    def get_project_context(self):
        data = {"id": 5555, "method":"project_context_get", "params":[f'{self.otu_project_id}']}
        output = self.__connection(data)
        return output.get('result')

    def get_matched_addresses(self, address):
        data = {"id": 5555, "method": "get_matched_addresses", "params": [address, True]}
        output = self.__connection(data)
        result = output.get('result')
        return json.loads(result)

    def get_construction_center(self, id_address):
        data = {"id": 5555, "method": "get_construction_center", "params": [int(id_address)]}
        output = self.__connection(data)
        result = output.get('result')
        return json.loads(result)

    def set_ioc_filter(self, project_context):
        """Применение фильтра только по КК, АВ, УА, РУА"""
        data = {"id": 5555, "method": "set_ioc_filter", "params": [project_context, [258, 281, 330, 331, 332, 333], 79]}
        output = self.__connection(data)
        return output.get('result')

    def get_id_gis_objects(self, project_context, id_address):
        center = self.get_construction_center(id_address)
        lon = center.get('lon')
        lat = center.get('lat')
        offset = 0.001
        data = {"id": 5555,
                    "method": "get_gis_objects",
                    "params": [project_context, {"left": lon - offset, "right": lon + offset,
                                                 "bottom": lat - offset, "top": lat + offset}]}
        output = self.__connection(data)
        result = output.get('result')
        mounting_points = json.loads(result).get('mounting_points')
        id_gis_objects = [point.get('id') for point in mounting_points]
        return id_gis_objects

    def get_params_binded_objects(self, id_gis_objects, project_context):
        gis_objects = {}
        for id_gis_object in id_gis_objects:
            binded_objects = self.__get_binded_objects(id_gis_object, project_context)
            gis_objects.update({id_gis_object:{'name': binded_objects.get('name_with_name_attribute'),
                                                      'id_binded_object': binded_objects.get('id'),
                                                      'project_registers': binded_objects.get('projectRegisters'),
                                                      'plan_registers': binded_objects.get('planRegisters'),
                                                      'status_registers': binded_objects.get('statusRegisters')}})
        return gis_objects

    def __get_binded_objects(self, id_gis_object, project_context):
        data = {"id": 5555, "method": "get_binded_objects", "params": [id_gis_object, project_context]}
        output = self.__connection(data)
        return json.loads(output.get('result'))[0]

    def __get_query_status_registers(self, registers):
        query_status_registers = []
        for status_register in registers:
            if status_register.get('RegisterRecord'):
                record = status_register.get('RegisterRecord')
                query_status_registers.append({
                    "IsActual": True,
                    "RegisterId": record.get('RegisterId'),
                    "RegisterRecord": {"Id": record.get('Id'), "IsActual": True, "ProjectId": record.get('ProjectId')}
                })
            else:
                query_status_registers.append(
                    {"IsActual": False, "RegisterId": status_register.get('RegisterId'), "RegisterRecord": None})
        return query_status_registers


    def __get_query_project_plan_registers(self, registers):
        # query = []
        # for registers in (id_gis_object.get('project_registers'), id_gis_object.get('plan_registers')):
        subquery = []
        for project_register in registers:
            if project_register.get('RegisterRecords'):
                records = project_register.get('RegisterRecords')
                query_record = []
                for record in records:
                    query_record.append(
                        {"Id": record.get('Id'), "IsActual": True, "ProjectId": record.get('ProjectId')}
                    )
                query_record.append({"Id": None, "IsActual": True, "ProjectId": self.otu_project_id})
                subquery.append({"IsActual": True, "RegisterId": project_register.get('RegisterId'),
                                 "RegisterRecords": query_record})
            elif project_register.get('RegisterName') == 'Проектируемые к реконструкции':
                subquery.append({"IsActual": True, "RegisterId": project_register.get('RegisterId'),
                                 "RegisterRecords": [{"Id": None, "IsActual": True, "ProjectId": self.otu_project_id}]})
            else:
                subquery.append(
                    {"IsActual": False, "RegisterId": project_register.get('RegisterId'), "RegisterRecords": None})
            #query.append(subquery)
        return subquery

    def get_gis_object_by_id_node(self, id_node, project_context):
        self.set_ioc_filter(project_context)
        data = {"id": 5555, "method": "get_object_bounding_box", "params": [id_node, project_context]}
        output = self.__connection(data)
        result = output.get('result')
        id_gis_object = json.loads(result).get('ris_id')
        binded_objects = self.__get_binded_objects(id_gis_object, project_context)
        gis_object = {'name': binded_objects.get('name_with_name_attribute'),
                        'id_binded_object': binded_objects.get('id'),
                        'project_registers': binded_objects.get('projectRegisters'),
                        'plan_registers': binded_objects.get('planRegisters'),
                        'status_registers': binded_objects.get('statusRegisters')}

        print(gis_object['name'])
        return gis_object

    def get_id_node_by_name(self, data):
        url = 'https://tas.corp.itmh.ru/Node/Search'
        req = self.client.post(url, verify=False, auth=HTTPBasicAuth(self.username, self.password), data=data)
        if req.status_code == 401:
            return {'error': 'Нет доступа. Неверный логин/пароль.'}
        soup = BeautifulSoup(req.json().get('data'), "html.parser")
        search = soup.find_all('a')
        id_nodes_tentura = [i.text for i in search if i.get('href') and 'https://tentura' in i.get('href')]
        id_node_tentura = id_nodes_tentura[0] if id_nodes_tentura else None
        return {'result': id_node_tentura}

    def get_id_address_connection_point(self, aid):
        url = f'https://sss.corp.itmh.ru/building/address_main.php?aID={aid}'
        req = self.client.get(url, verify=False, auth=HTTPBasicAuth(self.username, self.password))
        if req.status_code == 401:
            return {'error': 'Нет доступа. Неверный логин/пароль.'}
        soup = BeautifulSoup(req.content.decode('utf-8'), "html.parser")
        search = soup.find_all('a')
        address_link = [i.get('href') for i in search if i.text and i.text == 'адрес в Тентуре'][0]
        match = re.search(r'building_id=(\d+)', address_link)
        id_address = match.group(1) if match else None
        return {'result': id_address}

    def add_node(self, gis_object):
        status_registers = gis_object.get('status_registers')
        project_registers = gis_object.get('project_registers')
        plan_registers = gis_object.get('plan_registers')
        query_status_registers = self.__get_query_status_registers(status_registers)
        query_project_registers = self.__get_query_project_plan_registers(project_registers)
        query_plan_registers = self.__get_query_project_plan_registers(plan_registers)

        data = {"id": 5555,
                "method": "update_io_registers",
                "params": [gis_object.get('id_binded_object'),
                           query_status_registers,
                           query_plan_registers,
                           query_project_registers]
                }
        output = self.__connection(data)
        return output.get('result')

    def add_csp(self, id_address, address):
        center = self.get_construction_center(id_address)
        lon = center.get('lon')
        lat = center.get('lat')
        offset = round(random.random() * 0.0001 + 0.0001, 6)
        lon += offset
        lat += offset
        date_today = datetime.date.today().strftime("%d.%m.%Y")

        data = {
            "id": 5555, "method": "create_object", "params": [{
                "inventory_objects_class": 1138,
                "attributes": [
                    {"id": 2448, "name": "Помещение", "value": address, "isDirty": True, "isNullable": False},
                    {"id": 2443, "name": "Адрес", "value": address, "isDirty": True, "isNullable": False},
                    {"id": 59, "name": "Дата постройки", "value": date_today, "isDirty": True, "isNullable": False},
                    {"id": 178, "name": "Основание размещения", "value": "", "isDirty": False, "isNullable": True},
                    {"id": 31, "name": "Наименование", "value": "", "isDirty": False, "isNullable": True},
                    {"id": 34, "name": "Фотографии", "value": "", "isDirty": False, "isNullable": True},
                    {"id": 79, "name": "Владелец", "value": "ООО «Комтехцентр»", "isDirty": True, "isNullable": False},
                    {"id": 80, "name": "Примечание", "value": "", "isDirty": False, "isNullable": True},
                    {"id": 2447, "name": "ГИС: точка привязки", "value": f"POINT({lon} {lat})", "isDirty": True,
                     "isNullable": True}
                ],
                "project": {
                    "id": self.otu_project_id, "_checked": True,
                    "registers": [
                        {"r2pt": 2, "_checked": False},
                        {"r2pt": 3, "_checked": False},
                        {"r2pt": 4, "_checked": False},
                        {"r2pt": 5, "_checked": False},
                        {"r2pt": 6, "_checked": False},
                        {"r2pt": 7, "_checked": False},
                        {"r2pt": 8, "_checked": False},
                        {"r2pt": 12, "_checked": True},
                        {"r2pt": 13, "_checked": False},
                        {"r2pt": 14, "_checked": False}
                    ],
                    "checked_register": 12
                },
                "includes": []
            }]
        }
        output = self.__connection(data)
        result = output.get('result')
        return json.loads(result).get('inventoryObject').get('id')


class Specification:
    """Класс выполняет заполнение объектов спецификации ресурсами в рабочем проекте"""
    def __init__(self, username, password, otu_project_id):
        self.username = username
        self.password = password
        self.otu_project_id = otu_project_id
    def authenticate(self):
        """Данный метод выполняет авторизацию sts"""
        data_sts = {'UserName': f'CORP\\{self.username}', 'Password': f'{self.password}', 'AuthMethod': 'FormsAuthentication'}
        url = """https://arm.itmh.ru/v3/backend/manager/login/"""
        req = requests.get(url)
        sts_url = req.url
        req = requests.post(sts_url, data=data_sts)
        response = req.content.decode('utf-8')
        if 'Enter your user ID' in response:
            return {'error': 'Аутентификация не выполнена. Неверный логин/пароль.'}
        regex_wresult = """name="wresult" value="(.+TokenResponse>)"""
        result = re.search(regex_wresult, response, flags=re.DOTALL)
        wwresult = result.group(1)
        wresult = wwresult.replace('&lt;', '<').replace('&quot;', '"')
        soup = BeautifulSoup(response, "html.parser")
        wa = soup.find('input', {"name": "wa"}).get('value')
        wctx = soup.find('input', {"name": "wctx"}).get('value')
        data_arm = {'wa': wa, 'wresult': wresult, 'wctx': wctx}
        req = requests.post(url, data=data_arm)
        cookie = req.request.headers.get('Cookie')
        x_session_id = cookie.split(';')[0].strip('PHPSESSID=')
        return {'cookie': cookie, 'x_session_id': x_session_id}

    def __connection(self, cookie, data):
        """Внутренний метод, выполняющий запрос к API"""
        url = 'https://arm.itmh.ru/v3/api'
        headers = {
            'Cookie': cookie.get('cookie'),
            'X-Session-Id': cookie.get('x_session_id')
        }
        req = requests.post(url, verify=False, headers=headers, json=data)
        if req.status_code == 401:
            return {'error': 'Нет доступа. Неверный логин/пароль.'}
        return req.json()

    def get_task_id(self, cookie):
        """Метод по номеру проекта получает ID задачи"""
        data = {"app":"ARM","alias":"production","service":"ArmOopm","method":"TaskIdByProjectGet","args":{"project_id":self.otu_project_id}}
        output = self.__connection(cookie, data)
        return output.get('result', {}).get('TaskIdByProjectGet')

    def is_edited(self, task_id, cookie):
        """Метод проверяет возможность редактирования спецификации"""
        data = {"app":"ARM","alias":"production","service":"ArmOopm","method":"TaskCanBeEdited","args":{"task_id":task_id}}
        output = self.__connection(cookie, data)
        return output.get('result', {}).get('TaskCanBeEdited')

    def __extract_prices(self, output, resources):
        resource_prices = output.get('result', {}).get('ResourcePriceInfoList')
        prices = {}
        for resource in resources:
            price = [i.get('UnitPrice') for i in resource_prices if i.get('Name') == resource.get('Name')]
            if price:
                prices.update({resource.get('Name'): price[0]})
        return prices

    def get_resource_price_sku(self, cookie, resources):
        data = {"app":"ARM","alias":"production","service":"ArmOopm","method":"ResourcePriceInfoList",
                "args":{"resource_type":{"Id":1,"Name":"SKU","Code":"sku","Mem":"Образы SKU"}}}
        output = self.__connection(cookie, data)
        prices = self.__extract_prices(output, resources)
        return prices

    def get_resource_price_tao(self, cookie, resources):
        data = {"app":"ARM","alias":"production","service":"ArmOopm","method":"ResourcePriceInfoList",
                "args":{
                    "resource_type":{
                        "Id":10,"Name":"Трудовые ресурсы ТЭО","Code":"labour","Mem":"Трудовые ресурсы ТЭО"
                    }
                }}
        output = self.__connection(cookie, data)
        prices = self.__extract_prices(output, resources)
        return prices


    def extract_resource_detail(self, output, resources):
        """Метод на основе методов get_resource_list_sku и get_resource_list_tao добавляет к ресурсам, которые
         требуется добавить, параметры, полученные из БД(ID и прочее)"""
        resource_detail = output
        detailed_resources = []
        for resource in resources:
            detail = [i for i in resource_detail if i.get('Name') == resource.get('Name')]
            if detail:
                resource.update({'Resource': detail[0]})
                detailed_resources.append(resource)
        return detailed_resources

    def get_resource_list_sku(self, cookie):
        """Метод получает список всех ресурсов СКУ в БД"""
        data = {"app":"ARM","alias":"production","service":"ArmTask","method":"ResourceList",
                "args":{"resource_type":{"Code":"sku","Id":1,"Name":"SKU"},"term":""}}
        output = self.__connection(cookie, data)
        return output.get('result', {}).get('ResourceList')

    def get_resource_list_tao(self, cookie):
        """Метод получает список всех ресурсов ТЭО в БД"""
        data = {"app":"ARM","alias":"production","service":"ArmTask","method":"ResourceList",
                "args":{"resource_type":{
                            "Id":10,"Name":"Трудовые ресурсы ТЭО","Code":"labour","Mem":"Трудовые ресурсы ТЭО"},
                        "term":""}}
        output = self.__connection(cookie, data)
        return output.get('result', {}).get('ResourceList')

    def get_manager_id(self, cookie):
        """Метод получает ID пользователя, для отправления запроса, от его имени"""
        headers = {
            'Cookie': cookie.get('cookie'),
            'X-Session-Id': cookie.get('x_session_id')
        }
        url = 'https://arm.itmh.ru/v3/backend/manager/user-info/'
        req = requests.get(url, verify=False, headers=headers)
        output = req.json()
        return output.get('manager')

    def get_entity_info_list(self, cookie):
        """Метод получает данные о всех объектах спецификации со всеми существующими ресурсами"""
        task_id = self.get_task_id(cookie)
        data = {"app":"ARM","alias":"production","service":"ArmOopm","method":"SpecificationForSppDetailsGet","args":{"task_id":task_id}}
        output = self.__connection(cookie, data)
        return output.get('result', {}).get('SpecificationForSppDetailsGet', {}).get('EntityInfoList')

    # def get_exist_obj(self, cookie, inventory_object_id):
    #     data = {"app":"ARM","alias":"production","service":"ArmOopm","method":"SpecificationForSppDetailsGet","args":{"task_id":8391318}}
    #     output = self.__connection(cookie, data)
    #     entity_info_list = output.get('result', {}).get('SpecificationForSppDetailsGet', {}).get('EntityInfoList')
    #     entity = [i for i in entity_info_list if i.get('InventoryObjectId') == inventory_object_id][0]
    #     exist_resource_type_list = entity.get('ResourceTypeList')
    #     return exist_resource_type_list

    def set_resources(self, cookie, inventory_object_id, resources, update=False):
        """Метод на основе полученной информации во вспомогательных методах вызывает формирование шаблона запроса
         и добавляет ресурсы в объект спецификации"""
        kwargs = {'inventory_object_id': inventory_object_id}
        manager_id = self.get_manager_id(cookie)
        kwargs.update({'manager_id': manager_id})

        resource_list_sku = self.get_resource_list_sku(cookie)
        kwargs.update({'resource_list_sku': resource_list_sku})

        resource_list_tao = self.get_resource_list_tao(cookie)
        kwargs.update({'resource_list_tao': resource_list_tao})

        detailed_resources_sku = self.extract_resource_detail(resource_list_sku, resources)
        detailed_resources_tao = self.extract_resource_detail(resource_list_tao, resources)
        kwargs.update({'detailed_resources_sku': detailed_resources_sku})
        kwargs.update({'detailed_resources_tao': detailed_resources_tao})

        prices_sku = self.get_resource_price_sku(cookie, resources)
        prices_tao = self.get_resource_price_tao(cookie, resources)
        prices = prices_sku | prices_tao
        kwargs.update({'prices': prices})

        task_id = self.get_task_id(cookie)
        kwargs.update({'task_id': task_id})

        entity_info_list = self.get_entity_info_list(cookie)
        kwargs.update({'entity_info_list': entity_info_list})

        spec_template = SpecTemplate(**kwargs)
        data = spec_template.add_resources(update=update)
        spec_j = self.__connection(cookie, data)
        #spec_j =1
        return spec_j


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
    # data_get_construction_center = {"id": 5555, "method": "get_construction_center", "params": [2459]}
    # # {"id":42015,"result":"{\"lon\":60.593568271428573,\"lat\":56.833121157142855}"}
    # req = client.post(url, verify=False, auth=HTTPBasicAuth(login, password), data=json.dumps(data_get_construction_center))
    # print('!!')
    # result = req.json().get('result')
    # result = json.loads(result)
    # lon = result.get('lon')
    # lat = result.get('lat')
    # horizontal_offset = 0.0001
    # vertical_offset = 0.0001
    # lon += horizontal_offset
    # lat += vertical_offset
    # print(lon)
    # print(lat)
    # address = 'Малышева28'
    #
    # data_create_csp = {
    #     "id":5555, "method":"create_object", "params": [{
    #         "inventory_objects_class":1138,
    #         "attributes": [
    #             {"id":2448,"name":"Помещение","value": address,"isDirty":True,"isNullable":False},
    #             {"id":2443,"name":"Адрес","value": address,"isDirty":True,"isNullable":False},
    #             {"id":59,"name":"Дата постройки","value":"30.08.2023","isDirty":True,"isNullable":False},
    #             {"id":178,"name":"Основание размещения","value":"","isDirty":False,"isNullable":True},
    #             {"id":31,"name":"Наименование","value":"","isDirty":False,"isNullable":True},
    #             {"id":34,"name":"Фотографии","value":"","isDirty":False,"isNullable":True},
    #             {"id":79,"name":"Владелец","value":"ООО «Комтехцентр»","isDirty":True,"isNullable":False},
    #             {"id":80,"name":"Примечание","value":"","isDirty":False,"isNullable":True},
    #             {"id":2447,"name":"ГИС: точка привязки","value":f"POINT({lon} {lat})","isDirty":True,"isNullable":True}
    #         ],
    #         "project": {
    #             "id":project,"_checked":True,
    #             "registers": [
    #                 {"r2pt":2,"_checked":False},
    #                 {"r2pt":3,"_checked":False},
    #                 {"r2pt":4,"_checked":False},
    #                 {"r2pt":5,"_checked":False},
    #                 {"r2pt":6,"_checked":False},
    #                 {"r2pt":7,"_checked":False},
    #                 {"r2pt":8,"_checked":False},
    #                 {"r2pt":12,"_checked":True},
    #                 {"r2pt":13,"_checked":False},
    #                 {"r2pt":14,"_checked":False}
    #             ],
    #             "checked_register":12
    #         },
    #         "includes":[]
    #     }]
    # }

    # Проверка является ли пользователь автором проекта
    active_project = {"id": 50814, "method": "set_active_project_for_user", "params": [27605]}

    # если да то возвращается True
    # {'id': 50814, 'result': True}

    # если нет то возвращается error, при этом status_code тоже 200
    """{'id': 50814, 'error': {'name': 'JSONRPCError', 'message': 'При установке активного проекта для контекста пользователя произошла ошибка! = проект id= 27605 не может быть выбран, так как пользователь id= 469 не является его автором',
    'errors': [{'name': 'Exception', 'message': 'set_active_project_for_user error: При установке активного проекта для контекста пользователя произошла ошибка! = проект id= 27605 не может быть выбран, так как пользователь id= 469 не я
    вляется его автором'}, {'name': 'UserContextServiceException', 'message': 'При установке активного проекта для контекста пользователя произошла ошибка! = проект id= 27605 не может быть выбран, так как пользователь id= 469 не являетс
    я его автором'}]}}
    """
    req = client.post(url, verify=False, auth=HTTPBasicAuth(login, password),
                      data=json.dumps(active_project)) # data_create_csp
    print(req.status_code)
    print(req.json())