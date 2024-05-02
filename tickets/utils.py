import re
import os
from pathlib import Path

import pymorphy2
from dotenv import load_dotenv

from .parsing import parsing_config_ports_vgw
from .parsing import _parsing_id_client_device_by_device_name
from .parsing import _parsing_config_ports_client_device
from .parsing import get_contract_id
from .parsing import get_contract_resources
from .parsing import get_sw_config

from collections import OrderedDict
from django.shortcuts import redirect
from django.conf import settings



def add_portconfig_to_list_swiches(list_switches, username, password):
    """Данный метод добавляет портконфиги коммутаторов в массив данных о коммутаторах"""
    switch_name = []
    for i in range(len(list_switches)):
        if list_switches[i][-1] == '-':
            pass
        else:
            switch_config = get_sw_config(list_switches[i][0], list_switches[i][1], username, password)
            if switch_config:
                switch_ports_var = get_vlan_4094_and_description(switch_config, list_switches[i][1])
                if switch_ports_var:
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
    return list_switches, switches_name

from copy import copy
def get_ip_from_subset(subset):
    ip_network = subset.split('/')[0]
    if subset.endswith('/32'):
        return (ip_network)
    mask = subset.split('/')[1]
    octets = ip_network.split('.')
    if mask == '30':
        octets[3] = str(int(octets[3]) + 2)
        return ('.'.join(octets))
    elif mask == '29':
        ip_addresses = []
        for i in range(5):
            copy_octets = copy(octets)
            copy_octets[3] = str(int(copy_octets[3]) + 2 + i)
            ip_addresses.append('.'.join(copy_octets))
        return tuple(ip_addresses)



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


def _readable_node(node_mon):
    """Данный метод приводит название узла к читаемой форме"""
    node_templates = {', РУА': 'РУА ', ', УА': 'УПА ', ', АВ': 'ППС ', ', КК': 'КК '}
    for key, item in node_templates.items():
        if node_mon.endswith(key):
            return item + node_mon[:node_mon.index(key)]
    return ''


def short_readable_node(node_mon):
    """Данный метод приводит название узла форме без окончания после запятой"""
    node_templates = [', РУА', ', УА', ', АВ', ', КК']
    for key in node_templates:
        if node_mon.endswith(key):
            return node_mon[:node_mon.index(key)]
    return ''


def _separate_services_and_subnet_dhcp(readable_services, change_log_shpd):
    """Данный метод принимает услуги(название + значение) и значение изменения адресации. Определяет услуги с DHCP.
     Если адресация меняется, в массив services добавляет название услуги ШПД без подсети. В массив service_shpd_change
      добавляет подсети с DHCP"""
    services = []
    service_shpd_change = []
    for key, value in readable_services.items():
        if type(value) == str:
            if key != '"ШПД в интернет"':
                services.append(key + ' ' + value)
            else:
                if change_log_shpd == 'существующая адресация':
                    services.append(key + ' ' + value)
                else:
                    if '/32' in value:
                        len_index = len('c реквизитами ')
                        subnet_clear = value[len_index:]
                        service_shpd_change.append(subnet_clear)
                        services.append(key)
        elif type(value) == list:
            if key != '"ШПД в интернет"':
                services.append(key + ', '.join(value))
            else:
                if change_log_shpd == 'существующая адресация':
                    services.append(key + ', '.join(value))
                else:
                    for val in value:
                        if '/32' in val:
                            len_index = len('c реквизитами ')
                            subnet_clear = val[len_index:]
                            service_shpd_change.append(subnet_clear)
                            if len(value) == len(service_shpd_change):
                                services.append(key)
                        else:
                            services.append(key + ' ' + val)
    return services, service_shpd_change


def get_selected_readable_service(readable_services, selected_ono):
    """Данный метод получает все сервисы в точке подключения в читаемом виде и выбранный сервис в ресурсах клиента.
    На основе выбранного сервиса возвращает отдельно название выбранного сервиса и название+описание выбранного
    сервиса"""
    for key, value in readable_services.items():
        if type(value) == str and selected_ono[0][-4] in value:
            desc_service = key
            name_passage_service = key + ' ' + value
        elif type(value) == list:
            for val in value:
                if selected_ono[0][-4] in val:
                    desc_service = key
                    name_passage_service = key + ' ' + val
    return desc_service, name_passage_service


def append_change_log_shpd(session):
    tag_service = session.get('tag_service')
    type_pass = session.get('type_pass')
    if 'Перенос, СПД' in type_pass:
        type_passage = session.get('type_passage')
        if type_passage == 'Перенос сервиса в новую точку' or (
                type_passage == 'Перевод на гигабит' and not any([session.get('logic_change_csw'), session.get('logic_change_gi_csw')])):
            selected_ono = session.get('selected_ono')
            selected_service = selected_ono[0][-3]
            service_shpd = ['DA', 'BB', 'ine', 'Ine', '128 -', '53 -', '34 -', '33 -', '32 -', '45 -', '54 -', '55 -',
                            '57 -', '60 -', '62 -', '64 -', '67 -', '68 -', '92 -', '96 -', '101 -', '105 -',
                            '125 -', '131 -', '107 -', '109 -', '483 -']
            if any(serv in selected_service for serv in service_shpd):
                tag_service.append({'change_log_shpd': None})
                session['subnet_for_change_log_shpd'] = selected_ono[0][-4]
        else:
            readable_services = session.get('readable_services')
            _, service_shpd_change = _separate_services_and_subnet_dhcp(readable_services, 'Новая подсеть /32')
            if service_shpd_change:
                session['subnet_for_change_log_shpd'] = ' '.join(service_shpd_change)
                tag_service.append({'change_log_shpd': None})

    elif 'Организация/Изменение, СПД' in type_pass and not 'Перенос, СПД' in type_pass and session.get('logic_csw') == True:
        readable_services = session.get('readable_services')
        _, service_shpd_change = _separate_services_and_subnet_dhcp(readable_services,
                                                                    'Новая подсеть /32')
        if service_shpd_change:
            session['subnet_for_change_log_shpd'] = ' '.join(service_shpd_change)
            tag_service.append({'change_log_shpd': None})
    return tag_service



def analyzer_vars(stroka, static_vars, hidden_vars):
    """Данный метод принимает строковую переменную, содержащую шаблон услуги со страницы
    Типовые блоки технического решения. Ищет в шаблоне блоки <> и сравнивает с аналогичными переменными из СПП.
    По средством доп. словаря формирует итоговый словарь содержащий блоки из СПП, которые
    есть в блоках шаблона(чтобы не выводить неактуальный блок) и блоки шаблона, которых не было в блоках
    из СПП(чтобы не пропустить неучтенный блок)
    Передаем переменные, т.к. переменные из глобал видятся, а из другой функции нет."""
    #    блок для определения необходимости частных строк <>
    list_var_lines = []
    list_var_lines_in = []
    regex_var_lines = '<(.+?)>'
    match_var_lines = re.finditer(regex_var_lines, stroka, flags=re.DOTALL)
    for i in match_var_lines:
        list_var_lines.append(i.group(1))
    for i in list_var_lines:
        if hidden_vars.get(i):
            stroka = stroka.replace('<{}>'.format(i), hidden_vars[i])
        else:
            stroka = stroka.replace('<{}>'.format(i), '  ')
    regex_var_lines_in = '\[(.+?)\]'
    match_var_lines_in = re.finditer(regex_var_lines_in, stroka, flags=re.DOTALL)
    for i in match_var_lines_in:
        list_var_lines_in.append(i.group(1))
    for i in list_var_lines_in:
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
            stroka = stroka.replace('\n \n \n \n', '\n\n')

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
        stroka = stroka.replace('%{}%'.format(key), dynamic_vars[key])
        stroka = stroka.replace(' .', '.')
    stroka = ''.join([stroka[i] for i in range(len(stroka)) if i != len(stroka)-1 and not (stroka[i] == ' ' and stroka[i + 1] == ' ')])
    for i in [';', ',', ':', '.']:
        stroka = stroka.replace(' ' + i, i)
    return stroka


def pluralizer_vars(stroka, counter_plur):
    """Данный метод на основе количества устройств в шаблоне меняет ед./множ. число связанных слов"""
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


def trunk_turnoff_shpd_cks_vk_vm(service, types_change_service):
    """Данный метод в качестве параметров получает обрабатываемый сервис и массив всех сервисов со значением
     выбранных работ(например организовать trunk'ом с простоем/без простоя). По значению выбранных работ определяет для
     данного сервиса использовать блок ТТР с простоем или без"""
    trunk_turnoff_on = False
    trunk_turnoff_off = False
    if types_change_service:
        for type_change_service in types_change_service:
            if next(iter(type_change_service.values())) == service:
                if "Организация ШПД trunk'ом с простоем" == next(iter(type_change_service.keys())):
                    trunk_turnoff_on = True
                elif "Организация ШПД trunk'ом" == next(iter(type_change_service.keys())):
                    trunk_turnoff_off = True
    return trunk_turnoff_on, trunk_turnoff_off


def get_service_name_from_service_plus_desc(services_plus_desc):
    """Получение названия услуги из строки с описанием"""
    service = None
    if services_plus_desc.startswith('Телефон'):
        service = 'Телефон'
    elif services_plus_desc.startswith('iTV'):
        service = 'Вебург.ТВ'
    elif services_plus_desc.startswith('Интернет, DHCP'):
        service = 'ШПД в Интернет'
    elif services_plus_desc.startswith('Интернет, блок Адресов Сети Интернет'):
        service = 'ШПД в Интернет'
    elif services_plus_desc.startswith('ЦКС'):
        service = 'ЦКС'
    elif services_plus_desc.startswith('Порт ВЛС'):
        service = 'Порт ВЛС'
    elif services_plus_desc.startswith('Порт ВМ'):
        service = 'Порт ВМ'
    elif services_plus_desc.startswith('Видеонаблюдение'):
        service = 'Видеонаблюдение'
    elif services_plus_desc.startswith('HotSpot'):
        service = 'Хот-спот'
    elif services_plus_desc.startswith('ЛВС'):
        service = 'ЛВС'
    return service



def _tag_service_for_new_serv(services_plus_desc):
    """Данный метод принимает на входе список новых услуг и формирует последовательность url'ов услуг, по которым
    необходимо пройти пользователю. Также определяет для услиги Хот-спот количество пользователей и принадлежность
    к услуге премиум+"""
    tag_service = []
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
            tag_service.append({'hotspot': services_plus_desc[index_service]})
        elif 'ЛВС' in services_plus_desc[index_service]:
            tag_service.append({'local': services_plus_desc[index_service]})
    return tag_service


def _replace_wda_wds(device):
    """Данный метод из названия WDA получает название WDS"""
    replace_wda_wds = device.split('-')
    replace_wda_wds[0] = replace_wda_wds[0].replace('WDA', 'WDS')
    replace_wda_wds.pop(1)
    device = '-'.join(replace_wda_wds)
    return device


def _get_downlink(chains, device):
    """Данный метод в качестве параметров получает название оборудования, от которого подключен клиент, цепочку
     устройств, в которой состоит это оборудование, и определяет нижестоящее оборудование"""
    if device.startswith('WDA'):
        device = _replace_wda_wds(device)
    downlink = []
    downlevel = 20
    for chain in chains:
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
                        downlink.append(chain.get('host_name'))
    return downlink


def _get_vgw_on_node(chains, device):
    """Данный метод в качестве параметров получает название оборудования, цепочку устройств, в которой состоит
     это оборудование, и определяет существуют тел. шлюзы, подключенные от этого оборудования или нет"""
    vgw_on_node = None
    level_device = 0
    for chain in chains:
        if device == chain.get('host_name'):
            level_device = chain.get('level')

        if device.startswith('SW') or device.startswith('CSW') or device.startswith('WDA'):
            if 'VGW' in chain.get('host_name'):
                level_vgw = chain.get('level')
                if level_vgw == level_device + 1:
                    vgw_on_node = 'exist'
                    break
    return vgw_on_node

def _get_node_device(chains, device):
    """Данный метод в качестве параметров получает название оборудования, цепочку устройств, в которой состоит
    это оборудование, и определяет название узла связи"""
    for chain in chains:
        if device == chain.get('host_name'):
            node_device = chain.get('alias')
    return node_device


def _get_extra_node_device(chains, device, node_device):
    """Данный метод в качестве параметров получает название оборудования, цепочку устройств, в которой состоит
    это оборудование, название узла связи и определяет иные устройства на данном узле связи"""
    extra_node_device = []
    for chain in chains:
        if node_device == chain.get('alias') and device != chain.get('host_name'):
            extra_node_device.append(chain.get('host_name'))
    return extra_node_device


def _get_uplink(chains, device, max_level):
    """Данный метод в качестве параметров получает название оборудования, цепочку устройств, в которой состоит
        это оборудование и определяет название и порт вышестоящего узла. Парамерт max_level изначально задается
        выше возможно максимального и впоследствии используется, чтобы однозначно определить вышестоящий узел"""
    if device.startswith('WDA'):
        device = _replace_wda_wds(device)
    elif device.startswith('WFA'):
        replace_wfa_wfs = device.split('-')
        replace_wfa_wfs[0] = replace_wfa_wfs[0].replace('WFA', 'WFS')
        replace_wfa_wfs.pop(1)
        device = '-'.join(replace_wfa_wfs)
    uplink = None
    for chain in chains:
        if device in chain.get('title'):
            temp_chains2 = chain.get('title').split('\nLink')
            for i in temp_chains2:
                if device.startswith('CSW') or device.startswith('WDS') or device.startswith('WFS'):
                    if f'-{device}' in i:  # для всех случаев подключения CSW, WDS, WFS
                        preuplink = i.split(f'-{device}')
                        preuplink = preuplink[0]
                        match_uplink = re.search('_(\S+?)_(\S+)', preuplink)
                        uplink_host = match_uplink.group(1)
                        uplink_port = match_uplink.group(2)
                        if uplink_host == chain.get('host_name') and chain.get('level') < max_level:
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
    return uplink, max_level


def _compare_config_ports_client_device(config_ports_client_device, main_client):
    """Данный метод на входе получает список портконфигов на клиентском устройстве и номер договора клиента. Проходит
     по списку портконфигов и составляет список других договоров на данном клиентском устройстве"""
    extra_clients = []
    extra_name_clients = []
    for config_port in config_ports_client_device:
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
    return extra_clients


def _get_extra_selected_ono(username, password, selected_device, selected_client):
    """Данные метод на входе получает устройство клиента, по нему получает ID клиентского устройства, по ID получает
    портконфиги устройства, по портконфигам определяет другие договора на клиентском устройстве. По договорам
    определяет ресурсы и добавляет их в заголовок"""
    extra_selected_ono = []
    id_client_device = _parsing_id_client_device_by_device_name(selected_device, username, password)
    config_ports_client_device = _parsing_config_ports_client_device(id_client_device, username, password)
    extra_clients = _compare_config_ports_client_device(config_ports_client_device, selected_client)
    if extra_clients:
        for extra_client in extra_clients:
            contract = extra_client[2]
            contract_id = get_contract_id(username, password, contract)
            if isinstance(contract_id, list):
                for i in contract_id:
                    real_contract_id = i.get('id')
                    extra_resources = get_contract_resources(username, password, real_contract_id)
                    for extra_resource in extra_resources:
                        if extra_resource[-2] == selected_device:
                            extra_selected_ono.append(extra_resource)
            else:
                extra_resources = get_contract_resources(username, password, contract_id)
                for extra_resource in extra_resources:
                    if extra_resource[-2] == selected_device:
                        extra_selected_ono.append(extra_resource)
    return extra_selected_ono


def _get_all_chain(chains, chain_device, uplink, max_level):
    """Данный метод проверяет является ли uplink КАД/УПА/РУА, если нет, то формирует цепочку из промежуточных
     устройств"""
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


def check_client_on_vgw(contracts, vgws, login, password):
    """Данный метод получает на входе контракт клиента и список тел. шлюзов и проверяет наличие этого контракта
     на тел. шлюзах"""
    selected_vgw = []
    waste_vgws = []
    for vgw in vgws:
        contracts_on_vgw = parsing_config_ports_vgw(vgw.get('ports'), login, password)
        if any(contract in contracts_on_vgw for contract in contracts):
            selected_vgw.append(vgw)
        else:
            vgw.update({'contracts': contracts_on_vgw})
            waste_vgws.append(vgw)
    return selected_vgw, waste_vgws


def _readable(curr_value, readable_services, serv, res):
    """Данный метод формирует массив данных из услуг и реквизитов для использования в шаблонах переноса услуг"""
    if serv in ['ЦКС', 'Порт ВЛС', 'Порт ВМ']:
        if curr_value == None:
            readable_services.update({serv: f' "{res}"'})
        elif type(curr_value) == str:
            readable_services.update({serv: [curr_value, f' "{res}"']})
        elif type(curr_value) == list:
            curr_value.append(f' "{res}"')
            readable_services.update({serv: curr_value})
    else:
        if curr_value == None:
            readable_services.update({serv: f'c реквизитами "{res}"'})
        elif type(curr_value) == str:
            readable_services.update({serv: [curr_value, f'c реквизитами "{res}"']})
        elif type(curr_value) == list:
            curr_value.append(f'c реквизитами "{res}"')
            readable_services.update({serv: curr_value})
    return readable_services


def get_extra_service_port_csw(service_port, switch_config, model):
    """Данный метод ищет порты на КК, если услуга выдана в несколько портов"""
    if 'D-Link' in model and model != 'D-Link DIR-100':
        config_ports_device = {}
        regex_description = 'config port_vlan (\d+|\d+-\d+) pvid (\d+)'
        match_description = re.finditer(regex_description, switch_config)
        for i in match_description:
            config_ports_device.update({i.group(1): i.group(2)})
        port = service_port.split()[-1]
        vlan = config_ports_device.get(port)
        for key, value in config_ports_device.items():
            if key != port and value == vlan and value not in ['1', '4094']:
                service_port = service_port + f',{key}'
    elif 'SNR' in model or 'Cisco' in model or 'Orion' in model:
        port = service_port
        vlan = 'no vlan'
        for interface in switch_config.split('!'):

            if port+'\n' in interface or port+'\r\n' in interface:
                regexes = ['switchport access vlan (\d+)', 'switchport trunk native vlan (\d+)']
                for regex_interface in regexes:
                    match = re.search(regex_interface, interface)
                    if match:
                        if match.group(1) not in ['1', '4094']:
                            vlan = match.group(1)
                        else:
                            vlan = '(на оборудовании не настроен)'
        extra_ports = []

        if vlan == '(на оборудовании не настроен)':
            extra_ports.append('(на оборудовании не настроен)')
        elif vlan != 'no vlan':
            for interface in switch_config.split('!'):
                access_command = f'switchport access vlan {vlan}' in interface and port not in interface
                native_command = f'switchport trunk native vlan {vlan}' in interface and port not in interface
                if access_command or native_command:
                    regex_port = "nterface (.+)['\n'|'\r\n']"
                    match = re.search(regex_port, interface)
                    extra_port = match.group(1).split('/')[-1].strip()
                    extra_ports.append(extra_port)
        if extra_ports:
            service_port = service_port + ',' + ','.join(extra_ports)
    return service_port


def get_vlan_4094_and_description(switch_config, model):
    """Данный метод на основе модели КАД подставляет соответствующие regex для формирования данных по портам КАД"""
    if 'SNR' in model or 'Cisco' in model or 'Orion' in model:
        regex_description = '\wnterface (\S+\/\S+)(.+?\n)!'
        match_description = re.finditer(regex_description, switch_config, flags=re.DOTALL)
        # чтобы найти description блок интерфейса разделяется по \r\n, если не получается разделить, разделяется по \n
        config_ports_device = {}
        for i in match_description:
            if 'description' in i.group(2):
                desc = i.group(2).split('\r\n')
                if len(desc) == 1:
                    desc = i.group(2).split('\n')
                    if 'description' in desc[1]:
                        desc = i.group(2).split('\n')[1][12:]  # 12 - длина description с пробелом
                    else:
                        desc = i.group(2).split('\n')[2][12:]
                else:
                    if 'description' in desc[1]:
                        desc = i.group(2).split('\r\n')[1][12:]
                    else:
                        desc = i.group(2).split('\r\n')[2][12:]
            else:
                desc = '-'
            if 'switchport access vlan 4094' in i.group(2):
                vlan = 'Заглушка 4094'
            else:
                vlan = '-'
            config_ports_device[i.group(1)] = [desc, vlan]

    elif 'D-Link' in model and model != 'D-Link DIR-100':
        config_ports_device = {}
        regex_description = 'config ports (\d+|\d+-\d+) (?:.+?) description (\".*?\")\n'
        match_description = re.finditer(regex_description, switch_config)
        for i in match_description:
            if '-' in i.group(1):
                start, stop = [int(j) for j in i.group(1).split('-')]
                for one_desc in list(range(start, stop + 1)):
                    config_ports_device['Port {}'.format(one_desc)] = [i.group(2), '-']
            else:
                config_ports_device['Port {}'.format(i.group(1))] = [i.group(2), '-']
        if '1100' in model:
            regex_free = 'config vlan vlanid 4094 add untagged (\S+)'
        else:
            regex_free = 'config vlan stub add untagged (\S+)'
        match_free = re.search(regex_free, switch_config)
        port_free = []
        if match_free:
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


def backward_page_service(request, trID, service_name):
    """Данный метод аналогичен методу backward_page, но используется для страниц сервисов. Отличие в том, что следующая
    страница в последовательности tag_service не удаляется, т.к. список сервисов формируется только в начале и
    удаленный сервис не попадет в итоговое ТР"""
    index = int(request.GET.get('index'))
    # tag_service = request.session['tag_service']
    # tag_service_index = request.session['tag_service_index']
    session_tr_id = request.session[str(trID)]
    tag_service = session_tr_id.get('tag_service')
    tag_service_index = session_tr_id.get('tag_service_index')
    # if request.GET.get('next_page'):  # вариант без случая обновления страницы
    #     prev_page = next(iter(tag_service[index - 1]))
    #     service = tag_service[index][service_name]
    #     index -= 1
    #     tag_service_index.pop()
    #     session_tr_id.update({'tag_service_index': tag_service_index})
    #     request.session[trID] = session_tr_id
    if request.GET.get('next_page'):
        if tag_service_index[-1] == index:
            prev_page = next(iter(tag_service[index - 1]))
            service = tag_service[index][service_name]
            index -= 1
            tag_service_index.pop()
            session_tr_id.update({'tag_service_index': tag_service_index})
            request.session[trID] = session_tr_id
        else:
            prev_page = next(iter(tag_service[index]))
            service = tag_service[index][service_name]

    else:
        prev_page = request.GET.get('prev_page')
        service = tag_service[index + 1][service_name]
    return request, service, prev_page, index


def backward_page(request, trID):
    """Данный метод возвращает значения для GET параметров(предыдущая страница и ее индекс), которые будут переданы
    в url кнопки Вернуться. Для определения этих параметров, проверяется наличие GET параметра next_page.
    В случае если next_page не существует в кнопку Вернуться передаются соответствующие значения из GET параметров.
    В слугчае ссли next_page существует, это означает, что на данную страницу перешли не с предыдущей, а со следующей
    по кнопке Вернуться. В этом случае в кнопку Вернуться передается уменьшенный индекс и из последовательности страниц
    tag_service удаляется следующая страница"""

    index = int(request.GET.get('index'))
    # tag_service = request.session['tag_service']
    # tag_service_index = request.session['tag_service_index']

    session_tr_id = request.session[str(trID)]
    tag_service = session_tr_id.get('tag_service')
    tag_service_index = session_tr_id.get('tag_service_index')
    # if request.GET.get('next_page'):  # вариант без случая обновления страницы
    #     prev_page = next(iter(tag_service[index - 1]))
    #     index -= 1
    #     tag_service_index.pop()
    #     tag_service.pop()
    #     session_tr_id.update({'tag_service_index': tag_service_index, 'tag_service': tag_service})
    #     request.session[trID] = session_tr_id
    if request.GET.get('next_page'):
        if tag_service_index[-1] == index:
            prev_page = next(iter(tag_service[index - 1]))
            index -= 1
            tag_service_index.pop()
            tag_service.pop()
            # request.session['tag_service_index'] = tag_service_index
            # request.session['tag_service'] = tag_service
            session_tr_id.update({'tag_service_index': tag_service_index, 'tag_service': tag_service})
            request.session[trID] = session_tr_id
        else:
            prev_page = next(iter(tag_service[index - 1]))
    else:
        prev_page = request.GET.get('prev_page')
    return prev_page, index # request,


def get_response_with_get_params(request, tag_service, session_tr_id, trID):  #request
    """Данный метод создает индекс для отображаемой страницы и при редиректе на новую страницу добавляет в url
     GET параметры текущей страницы и ее индекс"""
    #tag_service = session_tr_id.get('tag_service')
    tag_service_index = session_tr_id.get('tag_service_index')
    # tag_service = request.session['tag_service']
    # tag_service_index = request.session['tag_service_index']
    index = tag_service_index[-1] + 1
    tag_service_index.append(index)
    session_tr_id.update({'tag_service': tag_service, 'tag_service_index': tag_service_index})
    response = redirect(next(iter(tag_service[index + 1])), trID)
    response['Location'] += f'?prev_page={next(iter(tag_service[index]))}&index={index}'
    request.session[trID] = session_tr_id
    return response


def get_response_with_prev_get_params(request, tag_service, session_tr_id, trID):
    """Данный метод не создает новый индекс для отображаемой страницы и при редиректе на новую страницу добавляет в url
    GET параметры текущей страницы и предыдущий индекс"""
    #tag_service = session_tr_id.get('tag_service')
    tag_service_index = session_tr_id.get('tag_service_index')
    index = tag_service_index[-1]
    session_tr_id.update({'tag_service': tag_service})
    response = redirect(next(iter(tag_service[index + 1])), trID)
    response['Location'] += f'?prev_page={next(iter(tag_service[index]))}&index={index}'
    request.session[trID] = session_tr_id
    return response

def splice_services(services):
    """Объединение нескольких строк с сервисами Телефон, ЛВС, HotSpot, Видеонаблюдение, iTV в одну"""
    splice = {}
    for service in services:
        for serv in ['Телефон', 'ЛВС', 'HotSpot', 'Видеонаблюдение', 'iTV']:
            if service.startswith(serv):
                if splice.get(serv):
                    splice[serv] = splice[serv] + ' ' + service[len(serv):]
                else:
                    splice[serv] = service
            elif not [i for i in ['Телефон', 'ЛВС', 'HotSpot', 'Видеонаблюдение', 'iTV'] if service.startswith(i)]:
                splice[service] = service
    return list(splice.values())


def clear_session_params(session_tr_id, *args):
    """Данный метод удаляет из сессии полученные ключи"""
    for param in args:
        if session_tr_id.get(param):
            del session_tr_id[param]


def get_services(file):
    """Выборка ресурсов и получение из них пар(договор, реквизиты)"""
    disable_list = file.split('\r\n')
    services = []
    while True:
        if '' in disable_list:
            disable_list.remove('')
        else:
            break
    for disable_resource in disable_list:
        if '-->' in disable_resource:
            disable_resource = disable_resource.split('-->')[0]
        if ', IP-адрес или подсеть;' in disable_resource:
            contract, ppr_resource = disable_resource.strip().strip('"').split(', IP-адрес или подсеть;')
            services.append((contract, ppr_resource, disable_resource.strip('"')))
        elif 'IP-адрес или подсеть' in disable_resource:
            contract, ppr_resource = disable_resource.strip().strip('"').split('IP-адрес или подсеть ')
            services.append((contract, ppr_resource, disable_resource.strip('"')))
        elif ', Etherline;' in disable_resource:
            contract, ppr_resource = disable_resource.strip().strip('"').split(', Etherline;')
            services.append((contract, ppr_resource, disable_resource.strip('"')))
        elif 'Etherline' in disable_resource:
            contract, ppr_resource = disable_resource.strip().strip('"').split('Etherline ')
            services.append((contract, ppr_resource, disable_resource.strip('"')))
        elif ', Порт виртуального коммутатора;' in disable_resource:
            contract, ppr_resource = disable_resource.strip().strip('"').split(', Порт виртуального коммутатора;')
            services.append((contract, ppr_resource, disable_resource.strip('"')))
        elif 'Порт виртуального коммутатора' in disable_resource:
            contract, ppr_resource = disable_resource.strip().strip('"').split('Порт виртуального коммутатора ')
            services.append((contract, ppr_resource, disable_resource.strip('"')))
        elif ', Предоставление в аренду оптического воло;' in disable_resource:
            contract, ppr_resource = disable_resource.strip().strip('"').split(', Предоставление в аренду оптического воло;')
            services.append((contract, ppr_resource, disable_resource.strip('"')))
    return services


def get_links(file):
    """Выборка линков и получение из них данных об одной стороне линка(коммутатор, порт)"""
    disable_list = file.split('\n')
    links = []
    while True:
        if '' in disable_list:
            disable_list.remove('')
        else:
            break
    for disable_resource in disable_list:
        if '-->' in disable_resource:
            link_data = disable_resource.split('-->')[0]
            if link_data and 'AR' in link_data:
                sw = link_data.split(',')[-2].strip()
                port = link_data.split(',')[-1].strip()
                links.append((sw, port, disable_resource))
        elif ' - ' in disable_resource:
            parts_link = disable_resource.split(' - ')
            if 'AR' in parts_link[0] and 'AR' in parts_link[1]:
                sw = parts_link[0].split(',')[-2].strip()
                port = parts_link[0].split(',')[-1].strip()
                links.append((sw, port, disable_resource))
    return links


def formatted(string):
    """Данный метод удаляет из строки пробелы и точки"""
    string = string.replace(' ', '_').replace('.', '_')
    return string


def get_user_credential_cordis(user):
    if user.groups.filter(name='Менеджеры').exists():
        return (settings.CORDIS_USER_MKO, settings.CORDIS_PASSWORD_MKO)
    elif user.groups.filter(name='Сотрудники ОУЗП').exists():
        return (settings.CORDIS_USER_OUZP_SPD, settings.CORDIS_PASSWORD_OUZP_SPD)
    elif user.groups.filter(name='Сотрудники ОАТТР').exists():
        return (settings.CORDIS_USER_OATTR, settings.CORDIS_PASSWORD_OATTR)
    elif user.groups.filter(name='Сотрудники ОУПМ').exists():
        return (settings.CORDIS_USER_OUPM_SPD, settings.CORDIS_PASSWORD_OUPM_SPD)