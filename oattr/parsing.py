import requests
import re
from bs4 import BeautifulSoup
from requests.auth import HTTPBasicAuth

from tickets.parsing import get_connection_point


def ckb_parse(login, password):
    """Данный метод парсит страницу КБЗ с Типовыми блоками ТР"""
    templates = {}
    #url = 'https://ckb.itmh.ru/login.action?os_destination=%2Fpages%2Fviewpage.action%3FpageId%3D323312207&permissionViolation=true'
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
    # data = {'action': 'CreateOtu', 'trID': '84367'}
    # req = requests.post(url, verify=False, auth=HTTPBasicAuth(login, password), data=data)
    data = {'action': 'GetOtu', 'trID': f'{trID}'}
    req = requests.post(url, verify=False, auth=HTTPBasicAuth(login, password), data=data)
    if not req.json().get('id'):
        data = {'action': 'CreateOtu', 'trID': f'{trID}'}
        requests.post(url, verify=False, auth=HTTPBasicAuth(login, password), data=data)
        data = {'action': 'GetOtu', 'trID': f'{trID}'}
        req = requests.post(url, verify=False, auth=HTTPBasicAuth(login, password), data=data)
    print('req.json()')
    print(req.json())
    id_otu = req.json().get('id')
    return id_otu


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

def send_spp(login, password, dID, tID, trID, ticket_tr):
    url = f'https://sss.corp.itmh.ru/dem_tr/dem_point.php?dID={dID}&tID={tID}&trID={trID}'
    vID = ticket_tr.vID
    trOTO_Resolution = ticket_tr.oattr
    data = {'trOTO_Resolution': trOTO_Resolution, 'action': 'saveVariant',
             'vID': vID}
    requests.post(url, verify=False, auth=HTTPBasicAuth(login, password), data=data)

