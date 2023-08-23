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


def get_spp_addresses(login, password, street, house):
    """Данный метод парсит страницу с адресами в СПП"""
    lines = []
    data = {
        'distr_adm': 'any',
        'distr_mark': 'any',
        'distr_pto': 'any',
        'hideWithOutSPD': 0,
        'aCity': 0,
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
        entries = []
        search = soup.find_all('tr')
        # popo = soup.find_all(attrs={"tag": "str"})
        # print(popo)
        for tr in search:
            #print('!')
            aid = tr.find(attrs='aid')
            #tr.find('td', id="cur_stat")
            с3 = tr.find_all('td', class_="C3")
            output_city = с3[0].text
            output_street = lost_whitespace(с3[1].text)
            с11 = tr.find('td', class_="C11")
            output_house = '\n'.join(с11.find_all(text=True)) # recursive=False
            с9 = tr.find('td', class_="C9")
            output_spd = ''.join(с9.find_all(text=True))
            aid = tr['aid']
            entries.append([output_city, output_street, output_house, output_spd, aid])
        return entries







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
    # trTurnOff = None  # для отключения
    # trTurnOffInput = None
    # data = {'FileLink': 'файл', 'action': 'saveVariant',
    #         'vID': vID, 'trID': trID}
    # headers
    # 'Content-Type': multipart/form-data; boundary
    trOTPM_Resolution = ticket_tr.oattr
    data = {'trOTPM_Resolution': trOTPM_Resolution, 'action': 'saveVariant',
            'vID': vID}
    requests.post(url, verify=False, auth=HTTPBasicAuth(login, password), data=data)

