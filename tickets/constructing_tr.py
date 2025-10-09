from .utils import *
from .utils import _get_policer
from .utils import _readable_node
from .utils import _separate_services_and_subnet_dhcp


def convert_requisites_to_types(selected_ono):
    """По полученным данным с таблицы Информация для ОНО в Cordis договора формируется соответствие названия ресрурса
    с названием сервиса. Возвращается dict вида {'10.10.10.10/32':'Интернет'}"""
    requisites = {}
    service_portvk = ['-vk', 'vk-', '- vk', 'vk -', 'zhkh', 'vpls']
    service_portvm = ['-vrf', 'vrf-', '- vrf', 'vrf -']
    for i in selected_ono:
        if i[2] == 'IP-адрес или подсеть' and 'hotspot' in i[-3].lower() and i[-4].startswith('10'):
            requisites[i[-4]] = 'HotSpot'
        elif i[2] == 'IP-адрес или подсеть' and 'itv' in i[-3].lower() and i[-4].startswith('10'):
            requisites[i[-4]] = 'iTV'
        elif i[2] == 'IP-адрес или подсеть' and ('bgp' in i[-3].lower() or i[-4].startswith('212.49.97.')):
            requisites[i[-4]] = 'bgp'
        elif i[2] == 'IP-адрес или подсеть' and not i[-4].startswith('10'):
            requisites[i[-4]] = 'Интернет'
        elif i[2] == 'Порт виртуального коммутатора' and any(serv in i[-3].lower() for serv in service_portvk):
            requisites[i[4]] = 'Порт ВЛС'
        elif i[2] == 'Порт виртуального коммутатора' and any(serv in i[-3].lower() for serv in service_portvm):
            requisites[i[4]] = 'Порт ВМ'
        elif i[2] == 'Etherline':
            requisites[i[4]] = 'ЦКС'
    return requisites

def construct_tr(value_vars):
    """Основная функция формирования готового ТР"""
    if value_vars.get('result_services'):
        del value_vars['result_services']
    if value_vars.get('result_services_ots'):
        del value_vars['result_services_ots']

    mounts = {}
    connects = value_vars.get('connects')
    spd = value_vars.get('spd')
    result_services = []
    result_services_ots = []
    unused_connects = []
    ortr = []
    ots = []
    if connects:
        for connect_name, v in connects.items():
            mounts.update({connect_name: mount_objs[spd][v.get('sreda')](value_vars, connect_name, ortr)})
            unused_connects.append(connect_name)

    types_jobs = value_vars.get('types_jobs')
    pass_services = value_vars.get('pass_job_services') if value_vars.get('pass_job_services') else []
    new_services = value_vars.get('new_job_services') if value_vars.get('new_job_services') else []
    all_services = pass_services + new_services

    for spp_service in all_services:
        job_type = types_jobs[spp_service]
        job = jobs[job_type](value_vars, ortr, ots)
        job.define_services(spp_service, s_objs)
        connect_name = job.connect_name
        mount = mounts.get(connect_name)
        job.register_mount(mount, unused_connects)
        job.perform_job()

    result_services += ortr
    if ots:
        result_services_ots += ots
    else:
        result_services_ots = None

    if value_vars.get('type_pass') and 'Изменение, не СПД' in value_vars.get('type_pass'):
        result_services, result_services_ots, value_vars = change_services(value_vars)

    if value_vars.get('type_tr') == 'Не требуется':
        result_services = 'Решение ОУЗП СПД не требуется'
        for service in value_vars.get('services'):
            if 'Телефон' in service:
                result_services_ots = ['Решение ОУЗП СПД не требуется']
            else:
                result_services_ots = None

    if value_vars.get('type_tr') == 'ПТО':
        if value_vars.get('type_change_node') == 'Замена КАД':
            result_services, value_vars = replace_kad(value_vars)
        elif value_vars.get('type_change_node') == 'Установка дополнительного КАД':
            result_services, value_vars = add_kad(value_vars)
        elif value_vars.get('type_change_node') == 'Установка нового КАД':
            result_services, value_vars = new_kad(value_vars)
        elif value_vars.get('type_change_node') == 'Изминение физ. точки ППС':
            result_services, value_vars = passage_pps_without_logic(value_vars)
        elif value_vars.get('type_change_node') == 'Изменение трассы ВОК':
            result_services, value_vars = passage_optic_line(value_vars)
        elif value_vars.get('type_change_node') == 'Изменение трассы клиентских линий':
            result_services, value_vars = passage_client_lines(value_vars)
        result_services_ots = None
    return result_services, result_services_ots, value_vars

from . import text


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


def get_need(value_vars):
    """Данный метод формирует текст для поля Требуется в готовом ТР"""
    need = ['Требуется:']
    if value_vars.get('pass_job_services') and value_vars.get('needs'):
        for needs, services in value_vars.get('needs').items():
            if needs == 'Перенос сервиса':
                if len(services) == 1:
                    need.append(
                        f"- перенести сервис {','.join(services)} в новую точку подключения {value_vars.get('address')};")
                else:
                    need.append(f"- перенести точку подключения на адрес {value_vars.get('address')};")
            elif needs == 'Перенос трассы':
                need.append(
                    "- перенести трассу присоединения клиента;")
            elif needs == 'Восстановление':
                need.append(
                    "- восстановить трассу присоединения клиента;")
            elif needs == 'Перенос логического подключения':
                if value_vars.get('spd') == 'РТК':
                    need.append('перенести логическое подключение на ПМ РТК;')
                else:
                    need.append(
                        f"- перенести логическое подключение на узел {_readable_node(value_vars.get('pps'))};")
            elif needs == 'Расширение':
                need.append(f"- расширить полосу сервиса {','.join(services)};")
            elif needs == 'ПереносВидеонаблюдение':
                need.append("- перенести сервис Видеонаблюдение;")
    if value_vars.get('new_job_services'):
        name_new_service = [_.split()[0] for _ in value_vars.get('new_job_services')]
        if name_new_service and len(name_new_service) > 1:
            need.append(f"- организовать дополнительные услуги {', '.join(name_new_service)};")
        elif name_new_service and len(name_new_service) == 1:
            need.append(f"- организовать дополнительную услугу {''.join(name_new_service)};")
    if value_vars.get('change_job_services'):
        types_trunk = [
            "Организация ШПД trunk'ом",
            "Организация ШПД trunk'ом с простоем",
            "Организация ЦКС trunk'ом",
            "Организация ЦКС trunk'ом с простоем",
            "Организация порта ВЛС trunk'ом",
            "Организация порта ВЛС trunk'ом с простоем",
            "Организация порта ВМ trunk'ом",
            "Организация порта ВМ trunk'ом с простоем"
        ]
        for type_change_service in value_vars.get('types_change_service'):
            if next(iter(type_change_service.keys())) in types_trunk:
                if 'ШПД' in next(iter(type_change_service.keys())):
                    need.append("- организовать дополнительную услугу ШПД в Интернет;")
                elif 'ЦКС' in next(iter(type_change_service.keys())):
                    need.append("- организовать дополнительную услугу ЦКС;")
                elif 'ВЛС' in next(iter(type_change_service.keys())):
                    need.append("- организовать дополнительную услугу порт ВЛС;")
                elif 'ВМ' in next(iter(type_change_service.keys())):
                    need.append("- организовать дополнительную услугу порт ВМ;")
            else:
                if next(iter(type_change_service.keys())) == "Изменение cхемы организации ШПД":
                    need.append("- изменить cхему организации ШПД;")
                elif next(iter(type_change_service.keys())) == "Замена IP":
                    need.append("- изменить IP адрес;")
                elif next(iter(type_change_service.keys())) == "Установка дополнительных камер СВН":
                    need.append("- установить дополнительные камеры СВН;")
                elif next(iter(type_change_service.keys())) == "Изменение сервиса":
                    old_service = next(iter(value_vars.get('readable_services')))
                    change_service = next(iter(type_change_service.values()))
                    new_service = get_service_name_from_service_plus_desc(change_service)
                    need.append(f"- изменить услугу {old_service} на услугу {new_service};")
                elif next(iter(type_change_service.keys())) == "Замена connected на connected":
                    need.append("- заменить существующую connected подсеть на новую;")
                elif next(iter(type_change_service.keys())) == "Замена connected на connected":
                    need.append("- заменить существующую connected подсеть на новую;")
                elif next(iter(type_change_service.keys())) == "Организация доп connected":
                    need.append("- организовать дополнительную connected подсеть;")
                elif next(iter(type_change_service.keys())) == "Организация доп connected":
                    need.append("- организовать дополнительную маршрутизируемую подсеть;")
                elif next(iter(type_change_service.keys())) == "Организация доп IPv6":
                    need.append("- организовать дополнительную IPv6 подсеть;")
    return '\n'.join(need)[:-1]+'.'


def get_passage_optic_line(value_vars):
    """Данный метод формирует блок ТТР для переноса трассы ВОК"""
    result_services = []
    templates = value_vars.get('templates')
    stroka = templates.get("Изменение трассы ВОК присоединения к СПД.")
    static_vars = {}
    hidden_vars = {}
    static_vars['№ заявки ППР'] = value_vars.get('ppr')
    if value_vars.get('pto_dark_optic'):
        hidden_vars[
            'Внимание! Для проверки восстановления связи в "темном ОВ" для клиента %номер контракта в ИС Cordis% необходимо %способ проверки темного ОВ%.'
        ] = 'Внимание! Для проверки восстановления связи в "темном ОВ" для клиента %номер контракта в ИС Cordis% необходимо %способ проверки темного ОВ%.'
        static_vars['номер контракта в ИС Cordis'] = value_vars.get('pto_dark_optic_client')
        pto_dark_optic_after = value_vars.get('pto_dark_optic_after')
        if pto_dark_optic_after:
            pto_dark_optic_after = pto_dark_optic_after[0].lower() + pto_dark_optic_after[1:]
            pto_dark_optic_after = pto_dark_optic_after[:-1] if pto_dark_optic_after[-1] == "." else pto_dark_optic_after
        static_vars['способ проверки темного ОВ'] = pto_dark_optic_after
    result_services.append(analyzer_vars(stroka, static_vars, hidden_vars))
    return result_services, value_vars

def get_passage_client_lines(value_vars):
    """Данный метод формирует блок ТТР для переноса клиентских линий"""
    result_services = []
    templates = value_vars.get('templates')
    stroka = templates.get("Изменение трассы клиентских линий связи присоединения к СПД.")
    static_vars = {}
    hidden_vars = {}
    static_vars['№ заявки ППР'] = value_vars.get('ppr')
    result_services.append(analyzer_vars(stroka, static_vars, hidden_vars))
    return result_services, value_vars

def get_passage_pps_without_logic(value_vars):
    """Данный метод формирует блок ТТР для изменения физ. точки ППС"""
    result_services = []
    templates = value_vars.get('templates')
    stroka = templates.get("Изменение физической точки подключения ППС.")
    static_vars = {}
    hidden_vars = {}
    if value_vars.get('pto_current_node_name'):
        static_vars['узел связи'] = _readable_node(value_vars.get('pto_current_node_name'))
    else:
        static_vars['узел связи'] = _readable_node(value_vars.get('pps'))
    if value_vars.get('pto_change_node'):
        hidden_vars[
            '- Актуализировать информацию в системах учета и на оборудовании c %узел связи% на %узел связи новый%.'
        ] = '- Актуализировать информацию в системах учета и на оборудовании c %узел связи% на %узел связи новый%.'
        hidden_vars[
            '- Передать информацию в ОУИ СПД заявкой в ИС Cordis.'
        ] = '- Передать информацию в ОУИ СПД заявкой в ИС Cordis.'
        static_vars['узел связи новый'] = _readable_node(value_vars.get('pto_change_node_name'))
    if value_vars.get('pto_current_node_name') and 'ИБП' in value_vars.get('pto_current_node_name') or \
        not value_vars.get('pto_current_node_name') and 'ИБП' in value_vars.get('pps'):
        hidden_vars[
            '- Совместно с ОНИТС СПД проверить резервирование по питанию.'
        ] = '- Совместно с ОНИТС СПД проверить резервирование по питанию.'
        hidden_vars[
            '- Совместно с ТЭО проверить резервирование по питанию.'
        ] = '- Совместно с ТЭО проверить резервирование по питанию.'
    static_vars['№ заявки ППР'] = value_vars.get('ppr')
    result_services.append(analyzer_vars(stroka, static_vars, hidden_vars))
    return result_services, value_vars

def get_replace_kad(value_vars):
    """Данный метод формирует блок ТТР для замены КАД"""
    result_services = []
    templates = value_vars.get('templates')
    stroka = templates.get("Замена КАД на ППС %узел связи%.")
    type_new_model_kad = value_vars.get('type_new_model_kad')
    static_vars = {}
    hidden_vars = {}
    rep_string = {}
    model, node, gig_ports = value_vars.get('switch_data')
    uplink_node, uplink, uplink_port = value_vars.get('uplink_data')
    static_vars['старая модель коммутатора'] = model
    static_vars['узел связи'] = short_readable_node(node)
    static_vars['название коммутатора'] = value_vars.get('kad_name')
    static_vars['узел связи вышестоящий'] = _readable_node(uplink_node)
    static_vars['название коммутатора вышестоящего'] = uplink
    static_vars['порт доступа на коммутаторе вышестоящем'] = uplink_port
    static_vars['новая модель коммутатора'] = value_vars.get('type_new_model_kad')
    static_vars['№ заявки ППР'] = value_vars.get('ppr')
    hidden_vars[
        'Для выбора модели коммутатора руководствоваться документом "Типовые варианты организации УАД" (ссылка на' +
        ' документ: https://ckb.itmh.ru/pages/viewpage.action?pageId=40637908 ). Учесть раздел "Приоритеты использования КАД в рамках эксплуатационных задач".'
    ] = 'Для выбора модели коммутатора руководствоваться документом "Типовые варианты организации УАД" (ссылка на' + \
        ' документ: https://ckb.itmh.ru/pages/viewpage.action?pageId=40637908 ). Учесть раздел "Приоритеты использования КАД в рамках эксплуатационных задач".'
    if ('48' in model or '52' in model) and type_new_model_kad != '48-портовый медный коммутатор':
        hidden_vars[
            '- Клиентов переключить по согласованию с ОНИТС СПД "старый порт - новый порт".'
        ] = '- Клиентов переключить по согласованию с ОНИТС СПД "старый порт - новый порт".'
    else:
        hidden_vars['- Линии связи клиентов переключить "порт в порт".'] = '- Линии связи клиентов переключить "порт в порт".'
    if 'ИБП' in node:
        hidden_vars[', адаптированный для работы с РЭКопитоном'] = ', адаптированный для работы с РЭКопитоном'
        hidden_vars[
            '- Совместно с ОНИТС СПД проверить резервирование по питанию.'
        ] = '- Совместно с ОНИТС СПД проверить резервирование по питанию.'
        hidden_vars[
            '- Совместно c ТЭО проверить резервирование по питанию.'
        ] = '- Совместно c ТЭО проверить резервирование по питанию.'
    if 'Cisco' not in model:
        hidden_vars[
            ' (передатчик задействовать из демонтированного коммутатора)'
        ] = ' (передатчик задействовать из демонтированного коммутатора)'
        hidden_vars['Передатчик SFP переключить из существующего КАД.'] = 'Передатчик SFP переключить из существующего КАД.'
    else:
        hidden_vars[' SFP WDM, дальность до 20км (12dB), 1310 нм'] = ' SFP WDM, дальность до 20км (12dB), 1310 нм'
    multi_vars = {}
    if 'оптогигабитный' not in type_new_model_kad:
        rep_string[
            'gig_ports'] = '- Переключить существующий линк %линк/номер контракта в ИС Cordis% из порта %порт линка/договора% существующего коммутатора в свободный гигабитный порт' + \
                           ' установленного коммутатора. Использовать оптический передатчик[ SFP WDM, дальность до 20км (12dB), 1310 нм]. [Передатчик SFP переключить из существующего КАД.]'
        multi_vars.update({rep_string['gig_ports']: []})
        counter = 0
        for k, v in gig_ports.items():
            counter += 1
            static_vars[f'линк/номер контракта в ИС Cordis {counter}'] = v
            static_vars[f'порт линка/договора {counter}'] = k
            if 'Cisco' not in model:
                multi_vars[rep_string['gig_ports']].append(
                    f'- Переключить существующий линк %линк/номер контракта в ИС Cordis {counter}% из порта %порт линка/договора {counter}%' +
                    f' существующего коммутатора в свободный гигабитный порт установленного коммутатора. Использовать' +
                    ' оптический передатчик. Передатчик SFP переключить из существующего КАД.')
            else:
                multi_vars[rep_string['gig_ports']].append(
                    f'- Переключить существующий линк %линк/номер контракта в ИС Cordis {counter}% из порта %порт линка/договора {counter}%' +
                    f' существующего коммутатора в свободный гигабитный порт установленного коммутатора. Использовать' +
                    ' оптический передатчик SFP WDM, дальность до 20км (12dB), 1310 нм.')

    result_services.append(analyzer_vars(stroka, static_vars, hidden_vars, multi_vars))
    value_vars.update({'pps': node, 'kad': value_vars.get('kad_name')})
    return result_services, value_vars


def get_add_kad(value_vars):
    """Данный метод формирует блок ТТР для установки доп. КАД"""
    result_services = []
    templates = value_vars.get('templates')
    stroka = ' ------'
    type_add_kad = value_vars.get('type_add_kad')
    static_vars = {}
    hidden_vars = {}
    multi_vars = {}
    exist_model, node, gig_ports = value_vars.get('switch_data')
    uplink_node, uplink, uplink_port = value_vars.get('uplink_data')
    type_new_model_kad = value_vars.get('type_new_model_kad')
    static_vars['старая модель коммутатора'] = exist_model
    static_vars['узел связи'] = short_readable_node(node)
    static_vars['название коммутатора'] = value_vars.get('kad_name')
    static_vars['узел связи вышестоящий'] = _readable_node(uplink_node)
    static_vars['название коммутатора вышестоящего'] = uplink
    static_vars['порт доступа на коммутаторе вышестоящем'] = uplink_port
    static_vars['новая модель коммутатора'] = value_vars.get('type_new_model_kad')
    static_vars['порт линка/договора'] = value_vars.get('disabled_port')
    hidden_vars[
        'Для выбора модели коммутатора руководствоваться документом "Типовые варианты организации УАД" (ссылка на' +
        ' документ: https://ckb.itmh.ru/pages/viewpage.action?pageId=40637908 ). Учесть раздел "Приоритеты использования КАД в рамках эксплуатационных задач".'
        ] = 'Для выбора модели коммутатора руководствоваться документом "Типовые варианты организации УАД" (ссылка на' + \
            ' документ: https://ckb.itmh.ru/pages/viewpage.action?pageId=40637908 ). Учесть раздел "Приоритеты использования КАД в рамках эксплуатационных задач".'
    if 'ИБП' in node:
        hidden_vars[', адаптированный для работы с РЭКопитоном'] = ', адаптированный для работы с РЭКопитоном'
        hidden_vars[
            '- Совместно с ОНИТС СПД проверить резервирование по питанию.'
        ] = '- Совместно с ОНИТС СПД проверить резервирование по питанию.'
        hidden_vars[
            '- Совместно c ТЭО проверить резервирование по питанию.'
        ] = '- Совместно c ТЭО проверить резервирование по питанию.'
        hidden_vars[' от ИБП,'] = ' от ИБП,'
    if value_vars.get('ppr'):
        hidden_vars[
            '- Требуется отключение согласно списку отключений в ППР %№ заявки ППР% согласовать проведение работ.'
        ] = '- Требуется отключение согласно списку отключений в ППР %№ заявки ППР% согласовать проведение работ.'
        hidden_vars[
            '- Совместно с ОНИТС СПД убедиться в восстановлении связи согласно списку отключений в ППР %№ заявки ППР%.'
        ] = '- Совместно с ОНИТС СПД убедиться в восстановлении связи согласно списку отключений в ППР %№ заявки ППР%.'
        hidden_vars[
            '- После проведения монтажных работ убедиться в восстановлении услуг согласно списку отключений в ППР %№ заявки ППР%.'
        ] = '- После проведения монтажных работ убедиться в восстановлении услуг согласно списку отключений в ППР %№ заявки ППР%.'
        static_vars['№ заявки ППР'] = value_vars.get('ppr')

    if value_vars.get('type_add_kad') == 'Установка 2-го кад в гирлянду':
        stroka = templates.get("Установка дополнительного %тип коммутатора% КАД на ППС %узел связи% вторым в гирлянду.")
        optic_gig_model_examples = [
            'S2990G-24FX', 'S3650G-48S', 'DGS-1210-28XS/ME', 'S2995G-24FX', 'S2995G-48FX'
        ]
        sfp_1_str = '- Установить в порт %порт линка/договора% КАД %название коммутатора% оптический передатчик[ SFP WDM, дальность до 3км (6dB), 1310нм][ SFP+, дальность до 300м (5dB), 850нм].'
        sfp_2_str = '- Установить в указанный ОНИТС СПД порт проектируемого КАД оптический передатчик[ SFP WDM, дальность до 3км (6dB), 1550нм][ SFP+, дальность до 300м (5dB), 850нм].'
        patch_str = ' Использовать оптический патчкорд[ SM SC-SC 1m][ LC/UPC-LC/UPC 3.0мм MM 1m duplex]'

        is_optic_exist_model = any(example in exist_model for example in optic_gig_model_examples)
        if 'оптогигабитный' not in type_new_model_kad and not is_optic_exist_model:
            static_vars['тип коммутатора'] = 'медного'
            hidden_vars[' Использовать медный патчкорд'] = ' Использовать медный патчкорд'
            hidden_vars[' 1'] = ' 1'
        elif 'оптогигабитный' not in type_new_model_kad and is_optic_exist_model:
            static_vars['тип коммутатора'] = 'медного'
            hidden_vars[sfp_1_str] = sfp_1_str
            hidden_vars[sfp_2_str] = sfp_2_str
            hidden_vars[patch_str] = patch_str
            hidden_vars[' 1'] = ' 1'
            hidden_vars[' SFP WDM, дальность до 3км (6dB), 1310нм'] = ' SFP WDM, дальность до 3км (6dB), 1310нм'
            hidden_vars[' SFP WDM, дальность до 3км (6dB), 1550нм'] = ' SFP WDM, дальность до 3км (6dB), 1550нм'
            hidden_vars[' SM SC-SC 1m'] = ' SM SC-SC 1m'
        elif 'оптогигабитный' in type_new_model_kad and is_optic_exist_model:
            static_vars['тип коммутатора'] = 'оптического'
            hidden_vars[sfp_1_str] = sfp_1_str
            hidden_vars[sfp_2_str] = sfp_2_str
            hidden_vars[patch_str] = patch_str
            hidden_vars[' 10'] = ' 10'
            hidden_vars[' SFP+, дальность до 300м (5dB), 850нм'] = ' SFP+, дальность до 300м (5dB), 850нм'
            hidden_vars[' LC/UPC-LC/UPC 3.0мм MM 1m duplex'] = ' LC/UPC-LC/UPC 3.0мм MM 1m duplex'
        else:
            return result_services, value_vars

        if value_vars.get('disabled_link'):
            static_vars['порт линка/договора'] = value_vars.get('disabled_port')
        else:
            static_vars['порт линка/договора'] = 'указанный ОНИТС СПД'
            port_str = '- Запросить в ОНИТС СПД порт для проектируемого КАД на %название коммутатора%.'
            hidden_vars[port_str] = port_str

        if value_vars.get('disabled_link'):
            hidden_vars[
                '- Переключить существующий линк %линк/номер контракта в ИС Cordis% из порта %порт линка/договора% существующего коммутатора' +
                ' в свободный гигабитный порт установленного коммутатора. Использовать оптический ' +
                'передатчик[ SFP WDM, дальность до 20км (12dB), 1310 нм]. [Передатчик SFP переключить из существующего КАД.]'
                ] = '- Переключить существующий линк %линк/номер контракта в ИС Cordis% из порта %порт линка/договора% существующего коммутатора' + \
                    ' в свободный гигабитный порт установленного коммутатора. Использовать оптический ' + \
                    'передатчик[ SFP WDM, дальность до 20км (12dB), 1310 нм]. [Передатчик SFP переключить из существующего КАД.]'
            hidden_vars[
                '- Сменить логическое подключение %линк/номер контракта в ИС Cordis% с КАД %название коммутатора% порт %порт линка/договора% на проектируемый КАД.'
            ] = '- Сменить логическое подключение %линк/номер контракта в ИС Cordis% с КАД %название коммутатора% порт %порт линка/договора% на проектируемый КАД.'
            static_vars['линк/номер контракта в ИС Cordis'] = value_vars.get('disabled_link')
            if 'Cisco' not in exist_model:
                hidden_vars[
                    ' (передатчик задействовать из демонтированного коммутатора)'
                ] = ' (передатчик задействовать из демонтированного коммутатора)'
                hidden_vars[
                    'Передатчик SFP переключить из существующего КАД.'] = 'Передатчик SFP переключить из существующего КАД.'
            else:
                hidden_vars[
                    ' SFP WDM, дальность до 20км (12dB), 1310 нм'] = ' SFP WDM, дальность до 20км (12dB), 1310 нм'


    elif value_vars.get('type_add_kad') == 'Установка 1-го оптического кад в гирлянду':
        stroka = templates.get("Установка дополнительного оптического КАД на УАД %узел связи% центральным в топологии.")
        static_vars['название коммутатора нижестоящего'] = value_vars.get('deleted_kad')
        gig_ports = {k: v for k, v in gig_ports.items() if v != value_vars.get('deleted_kad')}
        deleted_gig_ports = {}
        if value_vars.get('deleted_switch_data'):
            deleted_model, _, deleted_gig_ports = value_vars.get('deleted_switch_data')

        if value_vars.get('delete_kad'):
            hidden_vars[
                '. Второй в гирлянде КАД %название коммутатора нижестоящего% демонтировать'
            ] = '. Второй в гирлянде КАД %название коммутатора нижестоящего% демонтировать'
            hidden_vars[
                '- Демонтировать высвобожденный коммутатор %старая модель коммутатора% %название коммутатора нижестоящего% вместе со «стековым» линком.'
            ] = '- Демонтировать высвобожденный коммутатор %старая модель коммутатора% %название коммутатора нижестоящего% вместе со «стековым» линком.'
            hidden_vars[
                """- Демонтированное оборудование:
-- коммутатор %старая модель коммутатора% - 1 шт,
доставить на склад."""
            ] = """- Демонтированное оборудование:
-- коммутатор %старая модель коммутатора% - 1 шт,
доставить на склад."""
            hidden_vars[
                '- Высвобожденный коммутатор %название коммутатора нижестоящего% вместе со «стековым» линком демонтировать в' +
                ' ИС Cordis и разобрать настройки на оставшемся КАД на порту подключения демонтированного КАД.'
                ] = '- Высвобожденный коммутатор %название коммутатора нижестоящего% вместе со «стековым» линком демонтировать в' + \
                    ' ИС Cordis и разобрать настройки на оставшемся КАД на порту подключения демонтированного КАД.'

        else:
            hidden_vars['и %название коммутатора нижестоящего% '] = 'и %название коммутатора нижестоящего% '
            hidden_vars[
                '- Установить в свободный гигабитный порт КАД %название коммутатора нижестоящего% оптический передатчик SFP WDM, дальность до 3км (6dB), 1550нм.'
            ] = '- Установить в свободный гигабитный порт КАД %название коммутатора нижестоящего% оптический передатчик SFP WDM, дальность до 3км (6dB), 1550нм.'
            hidden_vars[' - 2 шт'] = ' - 2 шт'
            hidden_vars[
                '- Скроссировать порт дополнительного КАД с портом КАД %название коммутатора нижестоящего%. Использовать оптический патчкорд SM SC-SC 1m.'
            ] = '- Скроссировать порт дополнительного КАД с портом КАД %название коммутатора нижестоящего%. Использовать оптический патчкорд SM SC-SC 1m.'
            hidden_vars[
                '- Запустить существующий КАД %название коммутатора нижестоящего% от оптогигабитного коммутатора на магистрали 1 Гбит/с.'
            ] = '- Запустить существующий КАД %название коммутатора нижестоящего% от оптогигабитного коммутатора на магистрали 1 Гбит/с.'
        static_vars['диапазон оптических портов на демонтируемом коммутаторе'] = ', '.join(deleted_gig_ports.keys())
        static_vars['диапазон оптических портов на коммутаторе'] = ', '.join(gig_ports.keys())
        static_vars['старая модель коммутатора'] = deleted_model
    result_services.append(analyzer_vars(stroka, static_vars, hidden_vars, multi_vars))
    value_vars.update({'pps': node, 'kad': value_vars.get('kad_name')})
    return result_services, value_vars


def get_new_kad(value_vars):
    """Данный метод формирует блок ТТР для установки нового КАД"""
    result_services = []
    templates = value_vars.get('templates')
    stroka = ' ------'
    static_vars = {}
    hidden_vars = {}
    multi_vars = {}
    type_new_model_kad = value_vars.get('type_new_model_kad')
    static_vars['новая модель коммутатора'] = type_new_model_kad
    new_pps = {k:v for k, v in value_vars.items() if 'pps_' in k}
    for i in new_pps.keys():
        index = i.strip('pps_')
        if value_vars.get(f'ftth_{index}') and\
                type_new_model_kad not in ('24-портовый оптогигабитный коммутатор', '48-портовый оптогигабитный коммутатор'):
            stroka = templates.get("Установка оптического и медного КАД на УАД %узел связи%< с простоем связи>.")
        else:
            static_vars['тип коммутатора'] = 'медного' if 'оптогигабитный' not in type_new_model_kad else 'оптического'
            stroka = templates.get("Установка %тип коммутатора% КАД на УАД %узел связи%< с простоем связи>.")
        if 'ИБП' in value_vars.get(f'pps_{index}'):
            hidden_vars[', адаптированный для работы с РЭКопитоном'] = ', адаптированный для работы с РЭКопитоном'
            hidden_vars[
                '- Совместно с ОНИТС СПД проверить резервирование по питанию.'
            ] = '- Совместно с ОНИТС СПД проверить резервирование по питанию.'
            hidden_vars[
                '- Совместно c ТЭО проверить резервирование по питанию.'
            ] = '- Совместно c ТЭО проверить резервирование по питанию.'
            hidden_vars[' от ИБП,'] = ' от ИБП,'
            hidden_vars[
                '- По решению ОТПМ организовать резервирование УАД по питанию.'
            ] = '- По решению ОТПМ организовать резервирование УАД по питанию.'
        if value_vars.get('ppr'):
            hidden_vars[
                '- Требуется отключение согласно списку отключений в ППР %№ заявки ППР% согласовать проведение работ.'
            ] = '- Требуется отключение согласно списку отключений в ППР %№ заявки ППР% согласовать проведение работ.'
            hidden_vars[
                '- Совместно с ОНИТС СПД убедиться в восстановлении связи согласно списку отключений в ППР %№ заявки ППР%.'
            ] = '- Совместно с ОНИТС СПД убедиться в восстановлении связи согласно списку отключений в ППР %№ заявки ППР%.'
            hidden_vars[
                '- После проведения монтажных работ убедиться в восстановлении услуг согласно списку отключений в ППР %№ заявки ППР%.'
            ] = '- После проведения монтажных работ убедиться в восстановлении услуг согласно списку отключений в ППР %№ заявки ППР%.'
            hidden_vars[' с простоем связи'] = ' с простоем связи'
            static_vars['№ заявки ППР'] = value_vars.get('ppr')
        static_vars['узел связи'] = short_readable_node(value_vars.get(f'pps_{index}'))
        static_vars['узел связи вышестоящий'] = _readable_node(value_vars.get('pps'))
        static_vars['название коммутатора вышестоящего'] = value_vars.get(f'uplink_{index}')
        static_vars['порт доступа на коммутаторе вышестоящем'] = value_vars.get(f'uplink_port_{index}')
        static_vars['тип модуля'] = value_vars.get(f'transceiver_{index}')
        result_services.append(analyzer_vars(stroka, static_vars, hidden_vars, multi_vars))
        value_vars.update({'kad': value_vars.get(f'uplink_{index}')})
    value_vars.update({'pps': value_vars.get('pps')})
    return result_services, value_vars




def _change_services(value_vars):
    """Данный метод формирует блок ТТР изменения сервиса ШПД и организации сервисов ШПД, ЦКС, порт ВК, порт ВМ транком
    без монтажных работ"""
    if value_vars.get('result_services'):
        result_services = value_vars.get('result_services')
    else:
        result_services = []
    types_change_service = value_vars.get('types_change_service')
    templates = value_vars.get('templates')
    for type_change_service in types_change_service:
        service = next(iter(type_change_service.values()))
        static_vars = {}
        hidden_vars = {}
        if next(iter(type_change_service.keys())) == "Организация ШПД trunk'ом":
            stroka = templates.get("Организация услуги ШПД в интернет trunk'ом.")
            mask_service = next(iter(type_change_service.values()))
            if 'Интернет, блок Адресов Сети Интернет' in mask_service:
                if ('29' in mask_service) or (' 8' in mask_service):
                    static_vars['маска IP-сети'] = '/29'
                elif ('28' in mask_service) or ('16' in mask_service):
                    static_vars['маска IP-сети'] = '/28'
                else:
                    static_vars['маска IP-сети'] = '/30'
            result_services.append(analyzer_vars(stroka, static_vars, hidden_vars))
        elif next(iter(type_change_service.keys())) == "Организация ШПД trunk'ом с простоем":
            stroka = templates.get("Организация услуги ШПД в интернет trunk'ом с простоем связи.")
            mask_service = next(iter(type_change_service.values()))
            if 'Интернет, блок Адресов Сети Интернет' in mask_service:
                if ('29' in mask_service) or (' 8' in mask_service):
                    static_vars['маска IP-сети'] = '/29'
                elif ('28' in mask_service) or ('16' in mask_service):
                    static_vars['маска IP-сети'] = '/28'
                else:
                    static_vars['маска IP-сети'] = '/30'
            static_vars["ресурс на договоре"] = value_vars.get('selected_ono')[0][4]
            all_shpd_in_tr = value_vars.get('service_params')

            if all_shpd_in_tr:
                service = next(iter(type_change_service.values()))

                if all_shpd_in_tr.get(service)['exist_service'] == 'trunk':
                    hidden_vars['Cогласовать с клиентом tag vlan для ресурса "%ресурс на договоре%".'] = 'Cогласовать с клиентом tag vlan для ресурса "%ресурс на договоре%".'
                    static_vars["способ организации действующего сервиса"] = "tag'ом"
                else:
                    static_vars["способ организации действующего сервиса"] = "access'ом (native vlan)"
                static_vars["способ организации проектируемого сервиса"] = "trunk'ом"
                result_services.append(analyzer_vars(stroka, static_vars, hidden_vars))
        elif next(iter(type_change_service.keys())) == "Организация порта ВЛС trunk'ом" or next(iter(type_change_service.keys())) == "Организация порта ВЛС trunk'ом с простоем":
            all_portvk_in_tr = value_vars.get('service_params')
            if all_portvk_in_tr:
                service = next(iter(all_portvk_in_tr.keys()))
                if all_portvk_in_tr.get(service)['type_vk'] == 'Новая ВЛС':
                    stroka = templates.get("Организация услуги ВЛС.")
                    result_services.append(stroka)
                    static_vars['название ВЛС'] = 'Для ВЛС, организованной по решению выше,'
                else:
                    static_vars['название ВЛС'] = all_portvk_in_tr.get(service)['exist_vk']
                static_vars['пропускная способность'] = _get_policer(service)
                static_vars['L2. точка ограничения и маркировки трафика'] = all_portvk_in_tr.get(service)['policer_vk']
                if next(iter(type_change_service.keys())) == "Организация порта ВЛС trunk'ом":
                    stroka = templates.get("Организация услуги порт ВЛC trunk'ом.")
                else:
                    if all_portvk_in_tr.get(service)['exist_service'] == 'trunk':
                        static_vars["способ организации действующего сервиса"] = "tag'ом"
                    else:
                        static_vars["способ организации действующего сервиса"] = "access'ом (native vlan)"
                    static_vars['ресурс на договоре'] = value_vars.get('selected_ono')[0][-4]
                    static_vars["способ организации проектируемого сервиса"] = "trunk'ом"
                    stroka = templates.get("Организация услуги порт ВЛС trunk'ом с простоем связи.")
                result_services.append(analyzer_vars(stroka, static_vars, hidden_vars))
        elif next(iter(type_change_service.keys())) == "Организация порта ВМ trunk'ом" or next(iter(type_change_service.keys())) == "Организация порта ВМ trunk'ом с простоем":
            service = next(iter(type_change_service.values()))
            all_portvm_in_tr = value_vars.get('service_params')
            if all_portvm_in_tr:
                current_portvm = all_portvm_in_tr.get(service)
                if current_portvm.get('type_vm') == 'Новый ВМ':
                    stroka = templates.get("Организация услуги ВМ.")
                    result_services.append(stroka)
                    static_vars['название ВМ'] = ', организованного по решению выше,'
                else:
                    static_vars['название ВМ'] = current_portvm.get('exist_vm')
                static_vars['пропускная способность'] = _get_policer(service)
                static_vars['L3. точка ограничения и маркировки трафика'] = current_portvm.get('policer_vm')
                if current_portvm.get('vm_inet') == True:
                    static_vars['без доступа в интернет/с доступом в интернет'] = 'с доступом в интернет'
                else:
                    static_vars['без доступа в интернет/с доступом в интернет'] = 'без доступа в интернет'
                    hidden_vars[
                        '- Согласовать с клиентом адресацию для порта ВМ без доступа в интернет.'] = '- Согласовать с клиентом адресацию для порта ВМ без доступа в интернет.'

                if next(iter(type_change_service.keys())) == "Организация порта ВМ trunk'ом":
                    stroka = templates.get("Организация услуги порт ВМ trunk'ом.")
                else:
                    if current_portvm.get('exist_service_vm') == 'trunk':
                        static_vars["способ организации действующего сервиса"] = "tag'ом"
                    else:
                        static_vars["способ организации действующего сервиса"] = "access'ом (native vlan)"
                    static_vars["способ организации проектируемого сервиса"] = "trunk'ом"
                    static_vars['ресурс на договоре'] = value_vars.get('selected_ono')[0][-4]
                    stroka = templates.get("Организация услуги порт ВМ trunk'ом с простоем связи.")
                result_services.append(analyzer_vars(stroka, static_vars, hidden_vars))
        elif next(iter(type_change_service.keys())) == "Изменение сервиса":
            stroka = templates.get("Изменение сервиса %название сервиса% на сервис %название нового сервиса% access'ом.")
            readable_services = value_vars.get('readable_services')
            change_service = next(iter(type_change_service.values()))
            new_service_name = get_service_name_from_service_plus_desc(change_service)
            if new_service_name in ('Порт ВЛС', 'Порт ВМ'):
                hidden_vars[
                    '%новый сервис%'
                ] = '%новый сервис%'
                static_vars['пропускная способность'] = _get_policer(change_service)
                hidden_vars[' с полосой %пропускная способность%'] = ' с полосой %пропускная способность%'
                all_portvk_in_tr = value_vars.get('all_portvk_in_tr')
                all_portvm_in_tr = value_vars.get('all_portvm_in_tr')
                if all_portvk_in_tr:
                    service = next(iter(type_change_service.values()))
                    if all_portvk_in_tr.get(change_service)['type_vk'] == 'Новая ВЛС':
                        extra_stroka = templates.get("Организация услуги ВЛС.")
                        result_services.append(extra_stroka)
                        static_vars[
                            'новый сервис'] = f'для ВЛС, организованной по решению выше'
                    else:
                        static_vars['новый сервис'] = all_portvk_in_tr.get(change_service)["exist_vk"]

                    hidden_vars[
                        '- Ограничить скорость и настроить маркировку трафика для %название нового сервиса% %L2. точка ограничения и маркировки трафика%.'
                    ] = '- Ограничить скорость и настроить маркировку трафика для %название нового сервиса% %L2. точка ограничения и маркировки трафика%.'
                    static_vars['L2. точка ограничения и маркировки трафика'] = all_portvk_in_tr.get(change_service)[
                        'policer_vk']
                elif all_portvm_in_tr:
                    current_portvm = all_portvm_in_tr.get(change_service)
                    if current_portvm.get('type_vm') == 'Новый ВМ':
                        extra_stroka = templates.get("Организация услуги ВМ.")
                        result_services.append(extra_stroka)
                        static_vars['новый сервис'] = ', организованного по решению выше,'
                    else:
                        static_vars['новый сервис'] = current_portvm.get('exist_vm')
                    hidden_vars[
                        '- Ограничить скорость и настроить маркировку трафика для %название нового сервиса% %L3. точка ограничения и маркировки трафика%.'
                    ] = '- Ограничить скорость и настроить маркировку трафика для %название нового сервиса% %L3. точка ограничения и маркировки трафика%.'
                    static_vars['L3. точка ограничения и маркировки трафика'] = current_portvm.get('policer_vm')
                    if current_portvm.get('vm_inet') == True:
                        static_vars['без доступа в интернет/с доступом в интернет'] = 'с доступом в интернет '
                    else:
                        static_vars['без доступа в интернет/с доступом в интернет'] = 'без доступа в интернет '
                        hidden_vars[
                            '- Согласовать с клиентом адресацию для порта ВМ без доступа в интернет.'] = '- Согласовать с клиентом адресацию для порта ВМ без доступа в интернет.'


            elif new_service_name == 'ЦКС':
                hidden_vars[
                    '"%адрес точки "A"% - %адрес точки "B"%"'
                ] = '"%адрес точки "A"% - %адрес точки "B"%"'
                hidden_vars[' с полосой %пропускная способность%'] = ' с полосой %пропускная способность%'
                hidden_vars[
                    '- Ограничить скорость и настроить маркировку трафика для %название нового сервиса% %L2. точка ограничения и маркировки трафика%.'
                ] = '- Ограничить скорость и настроить маркировку трафика для %название нового сервиса% %L2. точка ограничения и маркировки трафика%.'
                static_vars['пропускная способность'] = _get_policer(change_service)
                all_cks_in_tr = value_vars.get('service_params')
                if all_cks_in_tr:
                    static_vars['адрес точки "A"'] = all_cks_in_tr.get(change_service)['pointA']
                    static_vars['адрес точки "B"'] = all_cks_in_tr.get(change_service)['pointB']
                    static_vars['L2. точка ограничения и маркировки трафика'] = all_cks_in_tr.get(change_service)['policer_cks']

            elif new_service_name == 'ШПД в Интернет':
                hidden_vars['использовать подсеть с маской %маска IP-сети%'] = 'использовать подсеть с маской %маска IP-сети%'
                if 'Интернет, блок Адресов Сети Интернет' in change_service:
                    mask_service = next(iter(type_change_service.values()))
                    if ('29' in mask_service) or (' 8' in mask_service):
                        static_vars['маска IP-сети'] = '/29'
                    elif ('28' in mask_service) or ('16' in mask_service):
                        static_vars['маска IP-сети'] = '/28'
                    else:
                        static_vars['маска IP-сети'] = '/30'
                elif 'Интернет, DHCP' in change_service:
                    static_vars['маска IP-сети'] = '/32'
            elif new_service_name == 'Хот-Спот':
                all_hotspot_in_tr = value_vars.get('service_params')
                if all_hotspot_in_tr:
                    current_hotspot = all_hotspot_in_tr.get(change_service)
                    if next(iter(readable_services.keys())) == 'Хот-Спот' and current_hotspot.get('type_hotspot') != 'Хот-Спот Премиум +':
                        if current_hotspot.get('type_hotspot') == 'Хот-Спот Премиум' and current_hotspot.get('hotspot_local_wifi') is True:
                            stroka = templates.get("Изменение услуги Хот-Спот Стандарт на услугу Хот-Спот Премиум c локальной сетью WiFi для сотрудников клиента.")
                        elif current_hotspot.get('type_hotspot') == 'Хот-Спот Премиум':
                            stroka = templates.get("Изменение услуги Хот-Спот Стандарт на услугу Хот-Спот Премиум.")
                        elif current_hotspot.get('type_hotspot') == 'Хот-Спот Стандарт':
                            stroka = templates.get("Изменение услуги Хот-Спот Премиум на услугу Хот-Спот Стандарт.")

                        static_vars['количество беспроводных станций доступа'] = current_hotspot.get('hotspot_points')
                        static_vars['количество клиентов Хот-Спот'] = current_hotspot.get('hotspot_users')
                        static_vars['название коммутатора'] = value_vars.get('selected_device')
                        selected_port = value_vars.get('selected_ono')[0][-1]
                        glue_selected_port = ''.join(selected_port.split())
                        head = value_vars.get('head')
                        head = head.replace(f'{selected_port}', f'{glue_selected_port}')
                        ports_text_fragment = [i for i in head.split() if f'{glue_selected_port},' in i]
                        if ports_text_fragment:
                            ports = ports_text_fragment[0].split(')')[0]
                        else:
                            ports = selected_port
                        static_vars['порт доступа на коммутаторе'] = ports
                        stroka = analyzer_vars(stroka, static_vars, hidden_vars)
                        counter_plur = current_hotspot.get('hotspot_points')
                        stroka = pluralizer_vars(stroka, counter_plur)

            static_vars['название сервиса'] = next(iter(readable_services.keys()))
            static_vars['указать сервис'] = f'{next(iter(readable_services.keys()))} {next(iter(readable_services.values()))}'
            static_vars['название нового сервиса'] = new_service_name
            result_services.append(analyzer_vars(stroka, static_vars, hidden_vars))
        elif next(iter(type_change_service.keys())) == "Установка дополнительных камер СВН":
            extra_cameras = ExtraCameras(value_vars)
            stroka = extra_cameras.get_filled_template()
            result_services.append(stroka)
        elif next(iter(type_change_service.keys())) == "Изменение cхемы организации ШПД":
            stroka = templates.get("Изменение существующей cхемы организации ШПД с маской %сущ. маска IP-сети% на подсеть с маской %нов. маска IP-сети%.")
            static_vars['нов. маска IP-сети'] = value_vars.get('new_mask')
            static_vars["сущ. маска IP-сети"] = value_vars.get('selected_ono')[0][4][-3:]
            static_vars["ресурс на договоре"] = value_vars.get('selected_ono')[0][4]
            static_vars['состояние логического подключения клиента'] = 'не изменится'
            result_services.append(analyzer_vars(stroka, static_vars, hidden_vars))
        elif next(iter(type_change_service.keys())) == "Замена IP":
            stroka = templates.get("Замена подсети connected для ШПД.")
            static_vars["сущ. маска IP-сети"] = value_vars.get('selected_ono')[0][4][-3:]
            static_vars["ресурс на договоре"] = value_vars.get('selected_ono')[0][4]
            if value_vars.get('parent_subnet') is True:
                hidden_vars[' из новой родительской сети'] = ' из новой родительской сети'
            if value_vars.get('selected_ono')[0][4][-3:] != '/32':
                hidden_vars[
                    '-- Актуализировать номер договора в КБЗ на странице учета адресации;'
                ] = '-- Актуализировать номер договора в КБЗ на странице учета адресации;'
            if value_vars.get('ip_ban') is True:
                hidden_vars[
                    '-- Перенести ресурс %ресурс на договоре% на договор К-76884 (Договор для ip-адресов ЧК);'
                ] = '-- Перенести ресурс %ресурс на договоре% на договор К-76884 (Договор для ip-адресов ЧК);'
            result_services.append(analyzer_vars(stroka, static_vars, hidden_vars))
        elif next(iter(type_change_service.keys())) == "Замена connected на connected":
            stroka = templates.get("Замена подсети connected.")
            static_vars['нов. маска IP-сети'] = value_vars.get('new_mask')
            static_vars["сущ. маска IP-сети"] = value_vars.get('selected_ono')[0][4][-3:]
            static_vars["ресурс на договоре"] = value_vars.get('selected_ono')[0][4]
            static_vars['состояние логического подключения клиента'] = 'не изменится'
            static_vars['название коммутатора'] = '-'.join(value_vars.get('selected_ono')[0][-2].split('-')[1:])
            match_svi = re.search('- (\d\d\d\d) -', value_vars.get('selected_ono')[0][-3])
            if match_svi:
                svi = match_svi.group(1)
                static_vars['номер SVI'] = svi
            else:
                static_vars['номер SVI'] = '%Неизвестный SVI%'
            result_services.append(analyzer_vars(stroka, static_vars, hidden_vars))
        elif next(iter(type_change_service.keys())) == "Организация доп connected":
            stroka = templates.get('Организация дополнительного блока адресов сети интернет (connected).')
            static_vars['нов. маска IP-сети'] = value_vars.get('new_mask')
            static_vars['название коммутатора'] = '-'.join(value_vars.get('selected_ono')[0][-2].split('-')[1:])
            match_svi = re.search('- (\d\d\d\d) -', value_vars.get('selected_ono')[0][-3])
            if match_svi:
                svi = match_svi.group(1)
                static_vars['номер SVI'] = svi
            else:
                static_vars['номер SVI'] = '%Неизвестный SVI%'
            result_services.append(analyzer_vars(stroka, static_vars, hidden_vars))
        elif next(iter(type_change_service.keys())) == "Организация доп маршрутизируемой":
            stroka = templates.get("Организация маршрутизируемого блока адресов сети интернет.")
            static_vars['нов. маска IP-сети'] = value_vars.get('new_mask')
            static_vars['адрес IP-сети'] = value_vars.get('routed_ip')
            static_vars['название VRF'] = value_vars.get('routed_vrf')
            result_services.append(analyzer_vars(stroka, static_vars, hidden_vars))
        elif next(iter(type_change_service.keys())) == "Организация доп IPv6":
            stroka = templates.get('Предоставление возможности прямой маршрутизации IPv6 дополнительно к существующему IPv4 подключению.')
            match_svi = re.search('- (\d\d\d\d) -', value_vars.get('selected_ono')[0][-3])
            if match_svi:
                svi = match_svi.group(1)
                static_vars['номер SVI'] = svi
            else:
                static_vars['номер SVI'] = '%Неизвестный SVI%'
            static_vars["ресурс на договоре"] = value_vars.get('selected_ono')[0][4]
            result_services.append(analyzer_vars(stroka, static_vars, hidden_vars))
        elif next(iter(type_change_service.keys())) == "Организация ЦКС trunk'ом" or next(iter(type_change_service.keys())) == "Организация ЦКС trunk'ом с простоем":
            all_cks_in_tr = value_vars.get('service_params')
            if all_cks_in_tr:
                service = next(iter(type_change_service.values()))
                static_vars['адрес точки "A"'] = all_cks_in_tr.get(service)['pointA']
                static_vars['адрес точки "B"'] = all_cks_in_tr.get(service)['pointB']
                static_vars['L2. точка ограничения и маркировки трафика'] = all_cks_in_tr.get(service)['policer_cks']
                static_vars['пропускная способность'] = _get_policer(service)
                if next(iter(type_change_service.keys())) == "Организация ЦКС trunk'ом":
                    stroka = templates.get("Организация услуги ЦКС Etherline trunk'ом.")
                else:
                    if all_cks_in_tr.get(service)['exist_service'] == 'trunk':
                        static_vars["способ организации действующего сервиса"] = "tag'ом"
                    else:
                        static_vars["способ организации действующего сервиса"] = "access'ом (native vlan)"
                    static_vars['ресурс на договоре'] = value_vars.get('selected_ono')[0][-4]
                    stroka = templates.get("Организация услуги ЦКС Etherline trunk'ом с простоем связи.")
                result_services.append(analyzer_vars(stroka, static_vars, hidden_vars))

    if value_vars.get('stick'):
        pps = value_vars.get('independent_pps')
        value_vars.update({'pps': pps})
    if value_vars.get('kad') == None:
        kad = value_vars.get('selected_ono')[0][-2]
        value_vars.update({'kad': kad})
    return result_services, value_vars


def change_services(value_vars):
    """Данный метод формирует готовое ТР для организации новых услуг или изменения существующих без монтаж. работ"""
    result_services, value_vars = _change_services(value_vars)
    if value_vars.get('result_services_ots'):
        result_services_ots = value_vars.get('result_services_ots')
    else:
        result_services_ots = None
    return result_services, result_services_ots, value_vars


def replace_kad(value_vars):
    """Данный метод формирует готовое ТР для замены КАД"""
    result_services, value_vars = get_replace_kad(value_vars)
    value_vars.update({'result_services': result_services})
    return result_services, value_vars


def add_kad(value_vars):
    """Данный метод формирует готовое ТР для установки доп. КАД"""
    result_services, value_vars = get_add_kad(value_vars)
    value_vars.update({'result_services': result_services})
    return result_services, value_vars


def new_kad(value_vars):
    """Данный метод формирует готовое ТР для установки нового КАД"""
    result_services, value_vars = get_new_kad(value_vars)
    value_vars.update({'result_services': result_services})
    return result_services, value_vars


def passage_pps_without_logic(value_vars):
    """Данный метод формирует готовое ТР изменения физической точки подключения ППС"""
    result_services, value_vars = get_passage_pps_without_logic(value_vars)
    value_vars.update({'result_services': result_services})
    return result_services, value_vars

def passage_optic_line(value_vars):
    """Данный метод формирует готовое ТР изменения трассы ВОК"""
    result_services, value_vars = get_passage_optic_line(value_vars)
    value_vars.update({'result_services': result_services})
    return result_services, value_vars

def passage_client_lines(value_vars):
    """Данный метод формирует готовое ТР переноса клиентских линий"""
    result_services, value_vars = get_passage_client_lines(value_vars)
    value_vars.update({'result_services': result_services})
    return result_services, value_vars



def construct_phone_channels_string(value_vars, vats):
    """Формирование строки с канальностью тел. номера. Для одного номера формат 1-канальный тел. номер. Для
    нескольких номеров формат 1 2-канальный тел. номер, 2 1-канальных тел. номера"""
    total = []
    for channel, number in value_vars.get('channels').items():
        if vats:
            stroka = f'{number} {channel}-' + '{канального} тел. {номера}'
        else:
            stroka = f'{number} {channel}-' + '{канальный} тел. {номер}'
        counter_plur = number
        total.append(pluralizer_vars(stroka, counter_plur))
    if len(total) == 1 and total[0].startswith('1'):
        single_number = ' '.join(total[0].split()[1:])
        total[0] = single_number
    return total


class TextBlock:
    """Класс переменных. Он хранит переменные, их значения и заполняет шаблон ТР переменными.
    static_vars - хранит переменные, которые в шаблоне ТР заполняются конкретными значениями.
     В шаблоне обозначаются %переменная%.
     hidden_vars - хранит строки шаблона ТР, которые либо добавляются либо не добавляются в шаблон ТР.
     В шаблоне обозначаются <переменная> [переменная].
     multi_vars - хранит строки шаблона ТР, которые требуется дублировать с разными вводными данными.
     В шаблоне обозначаются &переменная&.
     """
    def __init__(self, value_vars):
        self.static_vars = {}
        self.hidden_vars = {}
        self.multi_vars = {}
        self.value_vars = value_vars
        self.plural = None

    def set_plural(self, plural):
        """Метод, задающий число, от которого определяются окончания переменных с множественным числом в шаблоне"""
        self.plural = int(plural)

    def construct(self, template):
        """Метод заполняет переменные в шаблоне и возвращает готовый шаблон."""
        analyzed = analyzer_vars(template, self.static_vars, self.hidden_vars, self.multi_vars)
        if self.plural:
            analyzed = pluralizer_vars(analyzed, self.plural)
        return analyzed


class TextBlockForExtraCameras(TextBlock):
    """Компановка текста для шаблона Установка дополнительных камер."""
    def __init__(self, value_vars):
        super().__init__(value_vars)
        count_inj, ports_sw1, ports_sw2 = [int(_) for _ in value_vars.get('camera_schema').split('-')]
        count_busy_ports_1 = value_vars.get('count_busy_ports_1') if value_vars.get('count_busy_ports_1') else 0
        count_busy_ports_2 = value_vars.get('count_busy_ports_2') if value_vars.get('count_busy_ports_2') else 0
        self.count_inj = count_inj
        self.busy_ports = [(ports_sw1, count_busy_ports_1), (ports_sw2, count_busy_ports_2)]
        cur = count_inj + count_busy_ports_1 + count_busy_ports_2
        self.new_cameras = value_vars.get('camera_new')
        self.all_cameras = cur + self.new_cameras
        self.added_cam = [i + cur for i in range(1, self.new_cameras + 1)]
        self.counter_new_sw = {'4': 0, '8': 0}

    def idle_service(self):
        """Добавление строк с отключением"""
        strs = []
        strs.append('МКО:')
        strs.append('- Проинформировать клиента о простое сервиса видеонаблюдение на время проведения работ.')
        strs.append('- Согласовать время проведение работ.')
        strs.append('- Убедиться в восстановлении сервиса видеонаблюдение у клиента.')
        self.hidden_vars.update({i: i for i in strs})

    def add_inj(self, inj_number):
        """Добавление строк для добавления инжектора"""
        strs = []
        strs.append('-- PoE-инжектор СКАТ PSE-PoE.220AC/15VA - 1 шт.')
        strs.append('- Организовать 1 линию от камеры до маршрутизатора клиента.')
        strs.append('- Подключить организованную линию связи через POE инжектор в свободный lan-порт маршрутизатора:')
        self.hidden_vars.update({i: i for i in strs})
        port_ing_str = '-- свободный: %адрес установки камеры%, Камера №%номер камеры на схеме%, %модель камеры%, %необходимость записи звука%.'
        self.hidden_vars[port_ing_str] = port_ing_str.replace('%номер камеры на схеме%', inj_number)

        cam_str = '-- камеры №%номер камеры на схеме% глубину хранения архива %глубина хранения записей с камеры%< и запись звука>;'
        if not self.multi_vars.get(cam_str):
            self.multi_vars[cam_str] = []
        self.multi_vars[cam_str].append(cam_str.replace('%номер камеры на схеме%', inj_number))
        self.add_camera_params()

    def del_inj(self, start_port, last_port):
        """Добавление строк для удаления инжектора"""
        self.idle_service()
        remove_inj_str = '- Демонтировать POE-^инжектор^ и высвободить ^порт^ на маршрутизаторе.'
        self.hidden_vars[remove_inj_str] = pluralizer_vars(remove_inj_str, self.count_inj)
        from_inj_to_sw_str = '- Переключить {существующую} {линию} для {камеры} из маршрутизатора клиента в %портовая емкость коммутатора%-портовый POE-коммутатор:'
        from_inj_to_sw_str_changed = from_inj_to_sw_str.replace('%портовая емкость коммутатора%', str(last_port))
        self.hidden_vars[from_inj_to_sw_str] = pluralizer_vars(from_inj_to_sw_str_changed, self.count_inj)
        moved_cam_str = 'Порт %порт доступа на POE-коммутаторе%: существующая камера, переключенная с POE-инжектора;'
        self.multi_vars[moved_cam_str] = []
        for i in range(self.count_inj):
            self.multi_vars[moved_cam_str].append(f'Порт {start_port}: существующая камера, переключенная с POE-инжектора;')
            start_port += 1
        return start_port

    def replace_sw4_to_sw8(self):
        """Добавление строк для замены коммутатора"""
        self.idle_service()
        replace_str = '- Заменить 4-^портовый^ POE-^коммутатор^ на 8-^портовый^ POE-^коммутатор^. Переключить линии от существующих камер "порт в порт".'
        count_switch_str = '-- 8-портовый POE-коммутатор - %количество POE-коммутаторов% шт.'
        if replace_str in self.hidden_vars.keys():
            self.hidden_vars[replace_str] = pluralizer_vars(replace_str, 2)
        else:
            self.hidden_vars[replace_str] = pluralizer_vars(replace_str, 1)
        if '-- 8-портовый POE-коммутатор - 1 шт.' in self.hidden_vars.values():
            self.hidden_vars[count_switch_str] = '-- 8-портовый POE-коммутатор - 2 шт.'
        else:
            self.hidden_vars[count_switch_str] = '-- 8-портовый POE-коммутатор - 1 шт.'

    def add_sw8(self):
        """Добавление строк для добавления 8-портового коммутатора"""
        count_ports = 8
        self.new_poe(count_ports)
        self.counter_new_sw['8'] += 1

    def add_sw4(self):
        """Добавление строк для добавления 4-портового коммутатора"""
        count_ports = 4
        self.new_poe(count_ports)
        self.counter_new_sw['4'] += 1

    def new_poe(self, count_ports):
        """Добавление строк для добавления коммутатора"""
        switch_str = f'-- {count_ports}-портовый POE-коммутатор - %количество POE-коммутаторов% шт.'
        if switch_str in self.hidden_vars.keys():
            self.hidden_vars[switch_str] = switch_str.replace('%количество POE-коммутаторов%', '2')
        else:
            self.hidden_vars[switch_str] = switch_str.replace('%количество POE-коммутаторов%', '1')

        strs = []
        strs.append(f'-- В порт {5 if count_ports == 4 else 10} {count_ports}-портового POE-коммутатора.')
        strs.append('- Установить в помещении клиента %схема POE-коммутаторов% POE-^коммутаторы^.')
        strs.append(
            '- Организовать ^линию^ от маршрутизатора клиента до POE-^коммутаторов^. Включить {организованную} ^линию^ связи:')
        strs.append('-- В ^свободный^ ^порты^ маршрутизатора;')
        strs.append(
            'Для выбора модели POE-коммутатора руководствоваться документом "ИТП ВН. Типовые терминалы и PoE оборудование" (ссылка на документ: https://ckb.itmh.ru/x/LgMcDg).')
        self.hidden_vars.update({i: i for i in strs})

    def add_schema_poe(self):
        """Добавление схемы POE в переменные"""
        new_sw = [pluralizer_vars(f'{k}-^портовый^', v) for k, v in self.counter_new_sw.items() if v]
        new_sw_str = ' и '.join(new_sw)
        self.static_vars.update({'схема POE-коммутаторов': new_sw_str})
        self.plural = sum(self.counter_new_sw.values())

    def add_cameras(self):
        """Формирование заполненных строк с камерами"""
        for last_port, count_busy_ports in self.busy_ports:
            start_port = count_busy_ports + 1
            if self.count_inj and start_port <= last_port:
                start_port = self.del_inj(start_port, last_port)
                self.count_inj = None
            if self.added_cam and start_port <= last_port:
                self.install_cameras(start_port, last_port)

    def install_cameras(self, start_port, last_port):
        """Добавление строк с камерами"""
        temp_cam = copy(self.added_cam)
        new_cam_str = """- Организовать %количество линий% {линию} от %портовая емкость коммутатора%-портового POE-коммутатора до видеокамер. Включить линии в свободные порты POE-коммутатора:
Порт %порт доступа на POE-коммутаторе%: %адрес установки камеры%, Камера №%номер камеры на схеме%, %модель камеры%, %необходимость записи звука%;"""
        new_cam_str_2 = '-- камеры №%номер камеры на схеме% глубину хранения архива %глубина хранения записей с камеры%< и запись звука>;'
        if not self.multi_vars.get(new_cam_str):
            self.multi_vars[new_cam_str] = []
        if not self.multi_vars.get(new_cam_str_2):
            self.multi_vars[new_cam_str_2] = []
        cnt_free_ports = last_port - start_port + 1
        cnt_lines = len(self.added_cam) if len(self.added_cam) < cnt_free_ports else cnt_free_ports
        lines_str = pluralizer_vars(
            '- Организовать %количество линий% {линию} от %портовая емкость коммутатора%-портового POE-коммутатора до видеокамер. Включить линии в свободные порты POE-коммутатора:',
            cnt_lines)
        lines_str = lines_str.replace("%количество линий%", str(cnt_lines)).replace("%портовая емкость коммутатора%",
                                                                                    str(last_port))
        self.multi_vars[new_cam_str].append(lines_str)
        for i in temp_cam:
            self.added_cam.remove(i)
            self.multi_vars[new_cam_str].append(
                f'Порт {start_port}: %адрес установки камеры%, Камера №{i}, %модель камеры%, %необходимость записи звука%;')
            self.multi_vars[new_cam_str_2].append(
                f'-- камеры №{i} глубину хранения архива %глубина хранения записей с камеры%< и запись звука>;')
            if start_port == last_port:
                break
            start_port += 1
        self.multi_vars[new_cam_str_2].sort(key=lambda x: int(x[11:13]))
        self.add_camera_params()

    def add_camera_params(self):
        """Добавление параметров камер"""
        self.static_vars.update({
            'количество камер': str(self.new_cameras),
            'количество POE-инжекторов': str(self.new_cameras),
            'модель камеры': self.value_vars.get('camera_model'),
            'глубина хранения записей с камеры': self.value_vars.get('deep_archive'),
            'адрес установки камеры': self.value_vars.get('address'),
        })
        if self.value_vars.get('voice') is True:
            self.static_vars['необходимость записи звука'] = 'требуется запись звука'
            self.hidden_vars[' и запись звука'] = ' и запись звука'
        else:
            self.static_vars['необходимость записи звука'] = 'запись звука не требуется'


class ExtraCameras:
    """Формирование шаблона Установка дополнительных камер"""
    def __init__(self, value_vars):
        self.text_block = TextBlockForExtraCameras(value_vars)
        self.value_vars = value_vars
        self.schema = value_vars.get('camera_schema')
        self.templates = self.value_vars.get('templates')

    def camera_up_to_2(self):
        """Увеличение количества камер до 2"""
        number_inj_camera = '2'
        if self.schema in ('1-0-0',):
            self.text_block.add_inj(number_inj_camera)
    def camera_up_to_4(self):
        """Увеличение количества камер до 4"""
        if self.schema in ('1-0-0', '2-0-0'):
            self.text_block.add_sw4()
            self.text_block.busy_ports[0] = (4, 0)

    def camera_up_to_5(self):
        """Увеличение количества камер до 5"""
        number_inj_camera = '5'
        if self.schema == '0-4-0':
            self.text_block.add_inj(number_inj_camera)
        elif self.schema == '1-4-0':
            not_deleted_inj = 1
            self.text_block.count_inj -= not_deleted_inj
        elif self.schema in ('1-0-0', '2-0-0'):
            not_deleted_inj = 1
            self.text_block.count_inj -= not_deleted_inj
            self.text_block.add_sw4()
            self.text_block.busy_ports[0] = (4, 0)

    def camera_up_to_8(self):
        """Увеличение количества камер до 8"""
        if self.schema in ('1-0-0', '2-0-0', '0-4-0', '1-4-0'):
            if self.schema in ('1-0-0', '2-0-0'):
                self.text_block.add_sw8()
            elif self.schema in ('0-4-0', '1-4-0'):
                self.text_block.replace_sw4_to_sw8()
            self.text_block.busy_ports[0] = (8, self.text_block.busy_ports[0][1])

    def camera_up_to_9(self):
        """Увеличение количества камер до 9"""
        number_inj_camera = '9'
        if self.schema in ('1-0-0', '2-0-0'):
            not_deleted_inj = 1
            self.text_block.count_inj -= not_deleted_inj
            self.text_block.add_sw8()
            self.text_block.busy_ports[0] = (8, 0)
        elif self.schema in ('0-4-0', '1-4-0'):
            if self.schema == '0-4-0':
                self.text_block.add_inj(number_inj_camera)
            self.text_block.replace_sw4_to_sw8()
            self.text_block.busy_ports[0] = (8, self.text_block.busy_ports[0][1])
        elif self.schema in ('0-8-0', '0-4-4'):
            self.text_block.add_inj(number_inj_camera)

    def camera_up_to_12(self):
        """Увеличение количества камер до 12"""
        if self.schema in ('0-8-0', '1-8-0'):
            self.text_block.add_sw4()
            self.text_block.busy_ports[1] = (4, 0)
        elif self.schema in ('0-4-4',):
            self.text_block.replace_sw4_to_sw8()
            self.text_block.busy_ports[0] = (8, self.text_block.busy_ports[0][1])
        elif self.schema in ('1-0-0', '2-0-0'):
            self.text_block.add_sw8()
            self.text_block.add_sw4()
            self.text_block.busy_ports = [(8, 0), (4, 0)]
        elif self.schema in ('0-4-0', '1-4-0'):
            self.text_block.add_sw8()
            self.text_block.busy_ports[1] = (8, 0)

    def camera_up_to_16(self):
        """Увеличение количества камер до 16"""
        if self.schema in ('1-0-0', '2-0-0'):
            self.text_block.add_sw8()
            self.text_block.add_sw8()
            self.text_block.busy_ports = [(8, 0), (8, 0)]
        elif self.schema in ('0-4-0', '1-4-0',):
            self.text_block.replace_sw4_to_sw8()
            self.text_block.add_sw8()
            self.text_block.busy_ports = [(8, self.text_block.busy_ports[0][1]), (8, 0)]
        elif self.schema in ('0-8-0', '1-8-0'):
            self.text_block.add_sw8()
            self.text_block.busy_ports[1] = (8, 0)
        elif self.schema in ('0-4-4', '0-8-4', '0-4-8'):
            if self.schema == '0-4-4':
                self.text_block.replace_sw4_to_sw8()
            self.text_block.replace_sw4_to_sw8()
            self.text_block.busy_ports = [(8, self.text_block.busy_ports[0][1]), (8, self.text_block.busy_ports[1][1])]

    def get_filled_template(self):
        """Заполнение шаблона данными"""
        if self.text_block.all_cameras == 2:
            self.camera_up_to_2()
        elif self.text_block.all_cameras <= 4:
            self.camera_up_to_4()
        elif self.text_block.all_cameras == 5:
            self.camera_up_to_5()
        elif self.text_block.all_cameras <= 8:
            self.camera_up_to_8()
        elif self.text_block.all_cameras == 9:
            self.camera_up_to_9()
        elif self.text_block.all_cameras <= 12:
            self.camera_up_to_12()
        elif self.text_block.all_cameras <= 16:
            self.camera_up_to_16()
        self.text_block.add_cameras()
        self.text_block.add_schema_poe()
        template = self.templates.get("Установка дополнительных камер.")
        return self.text_block.construct(template)


class Connectable:
    """Базовый класс для услуг, требующих присоединение к СПД."""
    def __init__(self, ortr, connect):
        self.mount = None
        self.ortr = ortr
        self.templates = None
        self.value_vars = None
        self.connect = connect

    def set_mount(self, mount):
        """Метод устанавливает класс СПД, используемый для присоединения услуги."""
        self.mount = mount

    def get_mount(self):
        """Метод возвращает класс СПД, используемый для присоедения услуги."""
        if self.mount:
            return self.mount

    def get_cis_resources(self):
        """Метод возвращает список услуг Cordis, организованных на данном присоединении к СПД."""
        return self.mount.bind_resources

    def get_mount_vars(self, service_params, service):
        """Метод возвращает переменные, связанных с данным классом СПД"""
        if not self.mount:
            raise ExistError('Не было выбрано подключение')
        return self.mount.get_params(service_params, service)

    def get_template_line_from_csw(self):
        """Метод формирует шаблон организации линии от клиентского коммутатора и добавляет его в список шаблонов"""
        text_block = TextBlock(self.value_vars)
        template = self.templates.get("Присоединение к СПД по медной линии связи.")
        text_block.static_vars['узел связи'] = 'клиентского коммутатора'
        text_block.static_vars['название коммутатора'] = 'установленный по решению выше'
        text_block.static_vars['порт доступа на коммутаторе'] = 'свободный'
        department_str = 'отдел ОИПМ / ОИПД'
        text_block.static_vars[department_str] = 'ОИПМ' if self.mount.mount_type in ('2', '4') else 'ОИПД'
        self.ortr.append(text_block.construct(template))

class HotSpot(Connectable):
    """Класс организации новой услуги Хот-спот"""
    def __init__(self, value_vars, service, ortr, ots):
        self.service_params = value_vars.get('service_params', {}).get(service)
        if not self.service_params:
            raise ExistError('No data HotSpot')
        connect = self.service_params.get('connect')
        super().__init__(ortr, connect)
        self.text_block = TextBlock(value_vars)
        self.templates = value_vars.get('templates')
        self.value_vars = value_vars
        self.service = service
        self.type_hotspot = self.service_params.get('type_hotspot')
        self.hotspot_users = self.service_params.get('hotspot_users')
        self.hotspot_points = self.service_params.get('hotspot_points')
        self.exist_hotspot_client = self.service_params.get('exist_hotspot_client')
        self.hotspot_local_wifi = self.service_params.get('hotspot_local_wifi')
        self.mount_csw = None
        self.mount_kad = None
        self.mount_type = None

    def fill_vars(self):
        """Метод, заполняющий шаблон ТР переменными."""
        if self.type_hotspot == 'Хот-Спот Премиум +':
            self.text_block.static_vars['количество клиентов Хот-Спот'] = self.hotspot_users
        else:
            if self.mount_csw:
                self.text_block.static_vars['название коммутатора'] = 'клиентского коммутатора'
            else:
                self.text_block.static_vars['название коммутатора'] = self.mount_kad
            if self.service_params.get('exist_hotspot_client') is True:
                self.text_block.hidden_vars[text.onits_creates_hotspot] = text.onits_creates_hotspot
            else:
                self.text_block.hidden_vars[text.mko_creates_hotspot] = text.mko_creates_hotspot
            self.text_block.static_vars['количество беспроводных станций доступа'] = self.hotspot_points
            self.text_block.static_vars['количество клиентов Хот-Спот'] = self.hotspot_users
        static_vars, hidden_vars = self.get_mount_vars(self.service_params, self.service)
        self.text_block.static_vars.update(static_vars)
        self.text_block.hidden_vars.update(hidden_vars)
        department_str = 'отдел ОИПМ / ОИПД'
        self.text_block.static_vars[department_str] = 'ОИПМ' if self.mount_type in ('2', '4', 'FVNO GPON', 'FVNO FTTH') else 'ОИПД'


    def get_filled_template(self):
        """Метод возвращающий заполненный шаблон ТР."""
        if self.mount:
            self.mount_csw = self.mount.csw
            self.mount_kad = self.mount.kad
            self.mount_type = self.mount.mount_type
            if isinstance(self.mount, KtcMount) and self.mount.logic_csw:
                for i in range(self.hotspot_points):
                    self.get_template_line_from_csw()
        self.fill_vars()
        if self.type_hotspot == 'Хот-Спот Премиум +':
            if self.exist_hotspot_client is True:
                template = self.templates.get("Организация услуги Хот-Спот Премиум + для существующего клиента.")
            else:
                template = self.templates.get("Организация услуги Хот-Спот Премиум + для нового клиента.")
        else:
            if self.hotspot_local_wifi is True:
                if self.mount_csw:
                    template = self.templates.get("Организация услуги Хот-Спот Премиум c локальной сетью WiFi для сотрудников клиента.")
                else:
                    raise ExistError('Для Хот-Спот Премиум c локальной сетью WiFi не выбран КК')
            else:
                if self.type_hotspot == 'Хот-Спот Премиум':
                    template = self.templates.get("Организация услуги Хот-Спот Премиум.")
                else:
                    template = self.templates.get("Организация услуги Хот-Спот Стандарт.")

            self.text_block.set_plural(self.hotspot_points)
        hotspot_text = self.text_block.construct(template)
        self.ortr.append(hotspot_text)



class NewServiceShpd(Connectable):
    """Класс организации новой услуги ШПД"""
    def __init__(self, value_vars, service, ortr, ots):
        self.service_params = value_vars.get('service_params', {}).get(service)
        if not self.service_params:
            raise ExistError('No data Shpd')
        connect = self.service_params.get('connect')
        super().__init__(ortr, connect)
        self.value_vars = value_vars
        self.text_block = TextBlock(value_vars)
        self.router = RouterShpd(value_vars, service)
        self.templates = value_vars.get('templates')
        self.service = service
        self.port_type = self.service_params.get('port_type')

    def fill_text(self):
        """Метод, заполняющий шаблон ТР переменными."""
        if 'Интернет, DHCP' in self.service:
            self.text_block.static_vars['маска IP-сети'] = '/32'
        elif ('29' in self.service) or (' 8' in self.service):
            self.text_block.static_vars['маска IP-сети'] = '/29'
        elif ('28' in self.service) or ('16' in self.service):
            self.text_block.static_vars['маска IP-сети'] = '/28'
        else:
            self.text_block.static_vars['маска IP-сети'] = '/30'

        static_vars, hidden_vars = self.get_mount_vars(self.service_params, self.service)
        self.text_block.static_vars.update(static_vars)
        self.text_block.hidden_vars.update(hidden_vars)

    def get_filled_template(self):
        """Метод возвращающий заполненный шаблон ТР."""
        self.fill_text()
        if isinstance(self.mount, KtcMount) and self.mount.logic_csw:
            self.get_template_line_from_csw()
        if self.port_type == 'trunk':
            template = self.templates.get("Организация услуги ШПД в интернет trunk'ом.")
        else:
            template = self.templates.get("Организация услуги ШПД в интернет access'ом.")
        shpd_text = self.text_block.construct(template)
        router_text = self.router.get_filled_template()
        self.ortr.append(shpd_text)
        if router_text:
            self.ortr.append(router_text)


class RouterShpd:
    """Класс установки маршрутизатора для ШПД."""
    def __init__(self, value_vars, service):
        self.text_block = TextBlock(value_vars)
        self.templates = value_vars.get('templates')
        self.service_params = value_vars.get('service_params')
        self.service = service

    def get_filled_template(self):
        """Метод возвращающий заполненный шаблон ТР."""
        template = self.templates.get("Установка маршрутизатора")
        if self.service_params.get(self.service, {}).get('router_shpd'):
            self.text_block.static_vars['отдел ОИПМ / ОИПД'] = 'ОИПД'
            return self.text_block.construct(template)


class RouterItv:
    """Класс установки маршрутизатора для iTV."""
    def __init__(self, value_vars):
        self.text_block = TextBlock(value_vars)
        self.templates = value_vars.get('templates')
        self.router_itv = value_vars.get('router_itv')

    def get_filled_template(self):
        """Метод возвращающий заполненный шаблон ТР."""
        template = self.templates.get("Установка маршрутизатора")
        if self.router_itv:
            self.text_block.static_vars['отдел ОИПМ / ОИПД'] = 'ОИПД'
            return self.text_block.construct(template)


class NewServiceItv(Connectable):
    """Класс организации новой услуги iTV."""
    def __init__(self, value_vars, service, ortr, ots):
        self.service_params = value_vars.get('service_params', {}).get(service)
        if not self.service_params:
            raise ExistError('No data iTV')
        connect = self.service_params.get('connect') if self.service_params.get('connect') != '' else None
        super().__init__(ortr, connect)
        self.value_vars = value_vars
        self.text_block = TextBlock(value_vars)
        self.templates = value_vars.get('templates')
        self.type_itv = self.service_params.get('type_itv')
        self.router = RouterItv(value_vars)
        self.router_itv = self.service_params.get('router_itv')
        self.cnt_itv = self.service_params.get('cnt_itv')
        self.need_line_itv = self.service_params.get('need_line_itv')

        self.sks = NewServiceLvs(value_vars, service, ortr, ots)
        self.services = value_vars.get('services_plus_desc')


    def fill_vars(self):
        """Метод, заполняющий шаблон ТР переменными."""
        if self.type_itv == 'vl':
            self.text_block.static_vars['маска IP-сети'] = '/30' if self.router_itv or self.cnt_itv == 1 else '/29'

    def get_exist_shpd(self):
        """Метод определяет наличие услуги ШПД среди услуг Corsis и возвращает значение подсети."""
        cis_resources = self.get_cis_resources()
        shpd_list = cis_resources.get("ШПД в Интернет")
        return shpd_list[0] if shpd_list else ''


    def get_filled_template(self):
        """Метод возвращающий заполненный шаблон ТР."""
        template = ''
        self.fill_vars()
        if self.need_line_itv is True and self.type_itv != 'vl':
            self.sks.get_filled_template()

        if self.type_itv == 'vl':
            if isinstance(self.mount, KtcMount) and self.mount.logic_csw:
                for i in range(self.cnt_itv):
                    self.get_template_line_from_csw()
            template = self.templates.get("Организация услуги ЦТВ в отдельном vlan'е.")
        elif self.type_itv == 'novl':
            static_subnet = [s for s in self.services if 'Интернет, блок Адресов Сети Интернет' in s]
            if static_subnet:
                template = self.templates.get("Организация услуги ЦТВ в vlan'е новой услуги ШПД в интернет.")
        elif self.type_itv == 'novlexist':
            exist_shpd = self.get_exist_shpd()
            if not exist_shpd.endswith('/32'):
                template = self.templates.get("Организация услуги ЦТВ в vlan'е действующей услуги ШПД в интернет с простоем связи.")
        if template:
            self.ortr.append(self.text_block.construct(template))
        router_text = self.router.get_filled_template()
        if router_text:
            self.ortr.append(router_text)


class NewServiceCks(Connectable):
    """Класс организации новой услуги ЦКС."""
    def __init__(self, value_vars, service, ortr, ots):
        self.service_params = value_vars.get('service_params', {}).get(service)
        if not self.service_params:
            raise ExistError('No data Cks')
        connect = self.service_params.get('connect')
        super().__init__(ortr, connect)
        self.text_block = TextBlock(value_vars)
        self.value_vars = value_vars
        self.templates = value_vars.get('templates')
        self.port_type = self.service_params.get('port_type')
        self.service = service

    def get_filled_template(self):
        """Метод возвращающий заполненный шаблон ТР."""
        self.fill_vars()
        if isinstance(self.mount, KtcMount) and self.mount.logic_csw:
            self.get_template_line_from_csw()

        if self.port_type in ('access', 'xconnect'):
            template = self.templates.get("Организация услуги ЦКС Etherline access'ом.")
        else:
            template = self.templates.get("Организация услуги ЦКС Etherline trunk'ом.")
        cks_text = self.text_block.construct(template)
        self.ortr.append(cks_text)

    def fill_vars(self):
        """Метод, заполняющий шаблон ТР переменными."""
        self.text_block.static_vars.update({
            'адрес точки "A"': self.service_params['pointA'],
            'адрес точки "B"': self.service_params['pointB'],
            'L2. точка ограничения и маркировки трафика': self.service_params['policer_cks'],
            'пропускная способность': _get_policer(self.service)
        })
        static_vars, hidden_vars = self.get_mount_vars(self.service_params, self.service)
        self.text_block.static_vars.update(static_vars)
        self.text_block.hidden_vars.update(hidden_vars)
        if self.port_type == 'xconnect' and isinstance(self.mount, KtcMount):
            self.text_block.hidden_vars[", в порт подключения выдать vlan access"] = ", на портe подключения настроить xconnect"


class NewVk:
    """Класс организации новой услуги Виртуальный коммутатор."""
    def __init__(self, value_vars):
        self.text_block = TextBlock(value_vars)
        self.templates = value_vars.get('templates')

    def get_filled_template(self):
        """Метод возвращающий заполненный шаблон ТР."""
        template = self.templates.get("Организация услуги ВЛС.")
        return self.text_block.construct(template)

class NewServicePortVk(Connectable):
    """Класс организации новой услуги порт ВЛС."""
    def __init__(self, value_vars, service, ortr, ots):
        self.service_params = value_vars.get('service_params', {}).get(service)
        if not self.service_params:
            raise ExistError('No data Port VK')
        connect = self.service_params.get('connect')
        super().__init__(ortr, connect)
        self.text_block = TextBlock(value_vars)
        self.new_vk = NewVk(value_vars)
        self.value_vars = value_vars
        self.templates = value_vars.get('templates')
        self.service = service
        self.type_vk = self.service_params.get('type_vk')
        self.port_type = self.service_params.get('port_type')
        self.exist_vk = self.service_params['exist_vk']
        self.policer_vk = self.service_params['policer_vk']

    def fill_vars(self):
        """Метод, заполняющий шаблон ТР переменными."""
        if self.type_vk == 'Новая ВЛС':
            self.text_block.static_vars['название ВЛС'] = 'Для ВЛС, организованной по решению выше,'
        else:
            self.text_block.static_vars['название ВЛС'] = self.exist_vk
        self.text_block.static_vars.update({
            'пропускная способность': _get_policer(self.service),
            'L2. точка ограничения и маркировки трафика': self.policer_vk
        })
        static_vars, hidden_vars = self.get_mount_vars(self.service_params, self.service)
        self.text_block.static_vars.update(static_vars)
        self.text_block.hidden_vars.update(hidden_vars)
        if self.port_type == 'xconnect' and isinstance(self.mount, KtcMount):
            self.text_block.hidden_vars[
                ", в порт подключения выдать vlan access"] = ", на портe подключения настроить xconnect"

    def get_filled_template(self):
        """Метод возвращающий заполненный шаблон ТР."""
        if self.type_vk == 'Новая ВЛС':
            new_vk = self.new_vk.get_filled_template()
            self.ortr.append(new_vk)
        if isinstance(self.mount, KtcMount) and self.mount.logic_csw:
            self.get_template_line_from_csw()
        self.fill_vars()
        if self.port_type in ('access', 'xconnect'):
            template = self.templates.get("Организация услуги порт ВЛС access'ом.")
        else:
            template = self.templates.get("Организация услуги порт ВЛC trunk'ом.")
        portvk_text = self.text_block.construct(template)
        self.ortr.append(portvk_text)


class NewVm:
    """Класс организации новой услуги Виртуальный маршрутизатор."""
    def __init__(self, value_vars):
        self.text_block = TextBlock(value_vars)
        self.templates = value_vars.get('templates')

    def get_filled_template(self):
        """Метод возвращающий заполненный шаблон ТР."""
        template = self.templates.get("Организация услуги ВМ.")
        return self.text_block.construct(template)


class NewServicePortVm(Connectable):
    """Класс организации новой услуги порт ВМ."""
    def __init__(self, value_vars, service, ortr, ots):
        self.service_params = value_vars.get('service_params', {}).get(service)
        if not self.service_params:
            raise ExistError('No data Port VM')
        connect = self.service_params.get('connect')
        super().__init__(ortr, connect)
        self.text_block = TextBlock(value_vars)
        self.new_vm = NewVm(value_vars)
        self.value_vars = value_vars
        self.templates = value_vars.get('templates')
        self.service = service
        self.type_vm = self.service_params.get('type_vm')
        self.port_type = self.service_params.get('port_type')
        self.exist_vm = self.service_params['exist_vm']
        self.policer_vm = self.service_params['policer_vm']
        self.vm_inet = self.service_params['vm_inet']

    def fill_vars(self):
        """Метод, заполняющий шаблон ТР переменными."""
        if self.type_vm == 'Новый ВМ':
            self.text_block.static_vars['название ВМ'] = ', организованного по решению выше,'
        else:
            self.text_block.static_vars['название ВМ'] = self.exist_vm
        self.text_block.static_vars['пропускная способность'] = _get_policer(self.service)
        self.text_block.static_vars['L3. точка ограничения и маркировки трафика'] = self.policer_vm
        if self.vm_inet is True:
            self.text_block.static_vars['без доступа в интернет/с доступом в интернет'] = 'с доступом в интернет'
        else:
            self.text_block.static_vars['без доступа в интернет/с доступом в интернет'] = 'без доступа в интернет'
            addr_str = '- Согласовать с клиентом адресацию для порта ВМ без доступа в интернет.'
            self.text_block.hidden_vars[addr_str] = addr_str
        static_vars, hidden_vars = self.get_mount_vars(self.service_params, self.service)
        self.text_block.static_vars.update(static_vars)
        self.text_block.hidden_vars.update(hidden_vars)

    def get_filled_template(self):
        """Метод возвращающий заполненный шаблон ТР."""
        if self.type_vm == 'Новый ВМ':
            new_vk = self.new_vm.get_filled_template()
            self.ortr.append(new_vk)
        if isinstance(self.mount, KtcMount) and self.mount.logic_csw:
            self.get_template_line_from_csw()
        self.fill_vars()
        if self.port_type == 'access':
            template = self.templates.get("Организация услуги порт ВМ access'ом.")
        else:
            template = self.templates.get("Организация услуги порт ВМ trunk'ом.")
        portvm_text = self.text_block.construct(template)
        self.ortr.append(portvm_text)


class NewServiceLvs:
    """Класс организации новой услуги ЛВС."""
    def __init__(self, value_vars, service, ortr, ots):
        self.connect = None
        self.service = service
        self.ortr = ortr
        self.text_block = TextBlock(value_vars)
        self.value_vars = value_vars
        self.templates = value_vars.get('templates')

        self.local_type = value_vars.get('local_type')
        self.decision_otpm = value_vars.get('decision_otpm')
        self.sks_router = value_vars.get('sks_router')
        self.local_socket = value_vars.get('local_socket')
        self.sks_transceiver = value_vars.get('sks_transceiver')
        self.lvs_busy = value_vars.get('lvs_busy')
        self.lvs_switch = value_vars.get('lvs_switch')
        self.lvs_for_itv = True if service.startswith('iTV') else False
        if self.lvs_for_itv:
            service_params = value_vars.get('service_params', {}).get(service)
            cnt_itv = service_params.get('cnt_itv')
            self.local_ports = cnt_itv
        else:
            self.local_ports = value_vars.get('local_ports')

    def fill_vars(self):
        """Метод, заполняющий шаблон ТР переменными."""
        org_line_str = '- Организовать %количество портов ЛВС% {медную} {линию} связи от %оборудование клиента% до места установки маршрутизатора.'
        client_dev_str = 'оборудование клиента'
        if self.decision_otpm:
            otmp_str = ' согласно решению ОТПМ'
            self.text_block.hidden_vars[otmp_str] = otmp_str

        if self.lvs_for_itv:
            self.text_block.static_vars['отдел ОИПМ / ОИПД'] = 'ОИПД'
            self.text_block.static_vars['оборудование клиента'] = '^приставок^'
            self.text_block.hidden_vars[' для ЦТВ'] = ' для ЦТВ'
            self.text_block.hidden_vars[org_line_str] = org_line_str

        if self.local_type in ('sks_standart', 'sks_business'):
            self.text_block.static_vars['отдел ОИПМ / ОИПД'] = 'ОИПД'
            if self.sks_router:
                self.text_block.hidden_vars[org_line_str] = org_line_str
                self.text_block.static_vars[client_dev_str] = client_dev_str
            if self.local_socket:
                self.text_block.hidden_vars[' и розеток'] = ' и {розеток}'
        elif self.local_type == 'sks_vols':
            self.text_block.static_vars['отдел ОИПМ / ОИПД'] = 'ОИПМ'
            if self.sks_router:
                self.text_block.hidden_vars[org_line_str] = '- Организовать %количество портов ЛВС% ВОЛС от %оборудование клиента% до места установки маршрутизатора.'
                self.text_block.static_vars[client_dev_str] = client_dev_str
            strs = [
                ' по ВОЛС',
                '%отдел ОИПМ / ОИПД% подготовиться к работам:',
                '- Получить на складе территории:',
                '-- %тип конвертера А% - %количество портов ЛВС% шт.',
                '-- %тип конвертера Б% - %количество портов ЛВС% шт.',
                '- Установить %тип конвертера А% и %тип конвертера Б%.[ Выставить на конвертерах режим работы "auto".]'
            ]
            self.text_block.hidden_vars.update({i: i for i in strs})
            transceivers = {
                'Конвертеры 100': {
                    'тип конвертера А': '100 Мбит/с ^конвертер^ с длиной волны 1310 нм, дальность до 20 км',
                    'тип конвертера Б': '100 Мбит/с ^конвертер^ с длиной волны 1550 нм, дальность до 20 км'
                },
                'Конвертеры 1000': {
                    'тип конвертера А': '1000 Мбит/с ^конвертер^ с модулем SFP WDM с длиной волны 1310 нм, дальность до 20 км',
                    'тип конвертера Б': '1000 Мбит/с ^конвертер^ с модулем SFP WDM с длиной волны 1550 нм, дальность до 20 км'
                },
                'SFP': {
                    'тип конвертера А': '^оптический^ ^модуль^ SFP WDM с длиной волны 1310 нм, дальность до 20 км',
                    'тип конвертера Б': '^оптический^ ^модуль^ SFP WDM с длиной волны 1550 нм, дальность до 20 км'
                }
            }
            self.text_block.static_vars.update({**transceivers[self.sks_transceiver]})
            if not self.sks_transceiver == 'SFP':
                auto_str = ' Выставить на конвертерах режим работы "auto".'
                self.text_block.hidden_vars[auto_str] = auto_str
        elif self.local_type in ('lvs_standart', 'lvs_business'):
            if self.local_socket:
                self.text_block.hidden_vars[' и розеток'] = ' и {розеток}'
            if self.lvs_busy is True:
                strs = [
                    text.mko_lvs,
                    '- По согласованию с клиентом высвободить LAN-порт на маршрутизаторе клиента переключив сущ. линию для ЛВС клиента из маршрутизатора клиента в свободный порт установленного коммутатора.',
                    '- Подтвердить восстановление связи для порта ЛВС который был переключен в установленный коммутатор.'
                ]
                self.text_block.hidden_vars.update({i: i for i in strs})
            self.text_block.static_vars['модель коммутатора'] = self.lvs_switch
            ports_lvs_switch = {
                'TP-Link TL-SG105 V4': '5',
                'ZYXEL GS1200-5': '5',
                'TP-Link TL-SG108 V4': '8',
                'ZYXEL GS1200-8': '8',
                'D-link DGS-1100-16/B': '16',
                'D-link DGS-1100-24/B': '24'
            }
            self.text_block.static_vars['портовая емкость коммутатора'] = ports_lvs_switch.get(self.lvs_switch)

        self.text_block.static_vars['количество портов ЛВС'] = str(self.local_ports)
        self.text_block.set_plural(self.local_ports)

    def get_filled_template(self):
        """Метод возвращающий заполненный шаблон ТР."""
        self.fill_vars()
        if self.local_type in ('lvs_standart', 'lvs_business'):
            template = self.templates.get("Организация ЛВС на %количество портов ЛВС% {порт}")
        else:
            template = self.templates.get("Организация СКС< для ЦТВ>< по ВОЛС> на %количество портов ЛВС% {порт}")
        ortr_text = self.text_block.construct(template)
        self.ortr.append(ortr_text)


class NewServiceVideo:
    """Класс организации новой услуги Видеонаблюдение."""
    def __init__(self, value_vars, service, ortr, ots):
        self.connect = None
        self.service = service
        self.ortr = ortr
        self.text_block = TextBlock(value_vars)
        self.value_vars = value_vars
        self.templates = value_vars.get('templates')

        self.camera_model = value_vars.get('camera_model')
        self.camera_voice = value_vars.get('voice')
        self.camera_number = value_vars.get('camera_number')
        self.deep_archive = value_vars.get('deep_archive')
        self.address = value_vars.get('address')
        self.is_correct_schema_poe = False

    def up_to_2(self):
        """Метод используется при количестве камер от 1 до 2."""
        self.text_block.static_vars.update({
            'количество линий': str(self.camera_number),
            'количество POE-инжекторов': str(self.camera_number),
            'место установки камеры 1': self.value_vars.get('camera_place_one'),
            'место установки камеры 2': self.value_vars.get('camera_place_two'),
        })

        if self.camera_number == 2:
            strs = [
                '-- %порт доступа на маршрутизаторе%: %адрес установки камеры%, Камера %место установки камеры 2%, %модель камеры%, %необходимость записи звука%.',
                '-- камеры %место установки камеры 2% глубину хранения архива %глубина хранения записей с камеры%[ и запись звука].'
            ]
            self.text_block.hidden_vars.update({i:i for i in strs})
            self.text_block.set_plural(self.camera_number)
        self.text_block.set_plural(self.camera_number)
    def only_5_and_9(self):
        """Метод используется при количестве камер только 5 или 9."""
        self.text_block.static_vars.update({
            'количество линий': str(self.camera_number - 1),
            'количество POE-инжекторов': '1',
        })

        self.text_block.static_vars['портовая емкость коммутатора'] = '4' if self.camera_number == 5 else '8'
        self.text_block.static_vars['порт доступа на POE-коммутаторе'] = '5' if self.camera_number == 5 else '10'
        self.text_block.static_vars['номер камеры на схеме'] = '5' if self.camera_number == 5 else '9'

        port_str = 'Порт %номер камеры на схеме%: %адрес установки камеры%, Камера №%номер камеры на схеме%, %модель камеры%, %необходимость записи звука%;'
        port_counter = [
            f'Порт {_}: %адрес установки камеры%, Камера №{_}, %модель камеры%, %необходимость записи звука%;'
            for _ in range(1, self.camera_number)
        ]
        deep_str = '-- камеры №%номер камеры на схеме% глубину хранения архива %глубина хранения записей с камеры%< и запись звука>;'
        deep_counter = [
            f'-- камеры №{_} глубину хранения архива %глубина хранения записей с камеры%< и запись звука>;'
            for _ in range(1, self.camera_number + 1)
        ]
        self.text_block.multi_vars.update({
            port_str: port_counter,
            deep_str: deep_counter
        })
        self.text_block.set_plural(self.camera_number)

    def from_3_to_16_exclude_5_and_9(self):
        """Метод используется при количестве камер от 3 до 16, за исключением 5 и 9."""
        repr_str = text.poe_switch_line
        cam_str = '-- камеры №%номер камеры на схеме% глубину хранения архива %глубина хранения записей с камеры%< и запись звука>;'
        self.text_block.multi_vars[repr_str] = []
        self.text_block.multi_vars[cam_str] = []

        schema_poe = self.value_vars.get('schema_poe')
        set_poes = schema_poe.split('+')
        number_ports_poe_1 = set_poes[0]
        number_ports_poe_2 = set_poes[1] if len(set_poes) == 2 else None
        counter_same_poe = {}
        counter_same_poe.update({number_ports_poe_1: 1})
        if number_ports_poe_2:
            if counter_same_poe.get(number_ports_poe_2):
                counter_same_poe[number_ports_poe_2] += 1
            else:
                counter_same_poe.update({number_ports_poe_2: 1})
        count_poe = 1 if not number_ports_poe_2 else 2
        str_count_poe = "-- %портовая емкость коммутатора%-портовый POE-коммутатор - %количество POE-коммутаторов% шт."
        str_poe_uplink = "-- В порт %порт доступа на POE-коммутаторе% %портовая емкость коммутатора%-портового POE-коммутатора."

        self.text_block.multi_vars[str_count_poe] = []
        self.text_block.multi_vars[str_poe_uplink] = []
        for k, v in counter_same_poe.items():
            self.text_block.multi_vars[str_count_poe].append(f"-- {k}-портовый POE-коммутатор - {v} шт.")
            appended_str = "-- В порт 5 4-портового POE-коммутатора." if k == '4' else "-- В порт 10 8-портового POE-коммутатора."
            self.text_block.multi_vars[str_poe_uplink].append(appended_str)

        text_schema = {
            '4': '4-портовый',
            '4+4': '4-портовые',
            '4+8': '4-портовый и 8-портовый',
            '8': '8-портовый',
            '8+4': '8-портовый и 4-портовый',
            '8+8': '8-портовые',
        }

        self.text_block.static_vars["схема POE-коммутаторов"] = text_schema[schema_poe]
        counter_camera = 1
        counter_port = 1
        poe_1_cameras = self.value_vars.get('poe_1_cameras')
        poe_2_cameras = self.value_vars.get('poe_2_cameras')
        lines_poe = [poe_1_cameras, poe_2_cameras]
        for j in range(count_poe):
            text_block = TextBlock(self.value_vars)
            text_block.set_plural(lines_poe[j])
            plured_str = text_block.construct("- Организовать %количество линий% {линию} от POE-коммутатора до видеокамер. Включить линии в свободные порты POE-коммутатора:")
            appended_str = plured_str.replace("%количество линий%", str(lines_poe[j]))
            self.text_block.multi_vars[repr_str].append(appended_str)

            for i in range(lines_poe[j]):
                self.text_block.multi_vars[repr_str].append(
                    f'Порт {counter_port}: %адрес установки камеры%, Камера №{counter_camera}, %модель камеры%, %необходимость записи звука%;')
                counter_camera += 1
                counter_port += 1
            counter_port = 1

        deep_str = '-- камеры №%номер камеры на схеме% глубину хранения архива %глубина хранения записей с камеры%< и запись звука>;'
        deep_counter = [
            f'-- камеры №{_} глубину хранения архива %глубина хранения записей с камеры%< и запись звука>;'
            for _ in range(1, self.camera_number + 1)
        ]
        self.text_block.multi_vars.update({deep_str: deep_counter})

        if number_ports_poe_2:
            is_correct_poe_1 = poe_1_cameras <= int(number_ports_poe_1)
            is_correct_poe_2 = poe_2_cameras <= int(number_ports_poe_2)
            is_correct_cameras = poe_1_cameras + poe_2_cameras == self.camera_number
            self.is_correct_schema_poe = is_correct_poe_1 and is_correct_poe_2 and is_correct_cameras
        else:
            self.is_correct_schema_poe = self.camera_number <= int(number_ports_poe_1)
        if not self.is_correct_schema_poe:
            raise ExistError('Ошибка в количестве камер или POE-коммутаторов')
        self.text_block.set_plural(count_poe)

    def fill_vars(self):
        """Метод, заполняющий шаблон ТР переменными."""
        self.text_block.static_vars.update({
            'отдел ОИПМ / ОИПД': 'ОИПД',
            'количество камер': str(self.camera_number),
            'модель камеры': self.camera_model,
            'порт доступа на маршрутизаторе': 'свободный',
            'глубина хранения записей с камеры': self.deep_archive,
            'адрес установки камеры': self.address,
            'модель PoE-инжектора': 'PoE-инжектор СКАТ PSE-PoE.220AC/15VA'
        })
        if self.camera_voice is True:
            self.text_block.static_vars['необходимость записи звука'] = 'требуется запись звука'
            self.text_block.hidden_vars[' и запись звука'] = ' и запись звука'
        else:
            self.text_block.static_vars['необходимость записи звука'] = 'запись звука не требуется'

        if self.camera_number < 3:
            self.up_to_2()
        elif self.camera_number in (5, 9):
            self.only_5_and_9()
        elif 2 < self.camera_number < 17 and self.camera_number not in (5, 9):
            self.from_3_to_16_exclude_5_and_9()

    def get_filled_template(self):
        """Метод возвращающий заполненный шаблон ТР."""
        template = None
        self.fill_vars()
        if self.camera_number < 3:
            template = self.templates.get("Организация услуги Видеонаблюдение с использованием PoE-инжектора.")
        elif self.camera_number in (5, 9):
            template = self.templates.get("Организация услуги Видеонаблюдение с использованием POE-коммутатора и PoE-инжектора.")
        elif 2 < self.camera_number < 17 and self.camera_number not in (5, 9) and self.is_correct_schema_poe:
            template = self.templates.get("Организация услуги Видеонаблюдение с использованием POE-коммутатора.")
        self.ortr.append(self.text_block.construct(template))



class ExistError(Exception):
    pass


class VatsSip:
    """Класс организации новой услуги ВАТС по SIP."""
    def __init__(self, value_vars, ots, service):
        self.text_block = TextBlock(value_vars)
        self.templates = value_vars.get('templates')
        self.value_vars = value_vars
        self.ots = ots
        self.ports_vgw = value_vars.get('ports_vgw')
        self.service = service
        self.is_vats = True

    def fill_vars(self):
        """Метод, заполняющий шаблон ТР переменными."""
        phone_channels_string = construct_phone_channels_string(self.value_vars, self.is_vats)
        self.text_block.static_vars['тел. номер'] = ", ".join(phone_channels_string)
        self.text_block.static_vars['количество линий'] = self.ports_vgw
        self.text_block.static_vars['количество внутренних портов ВАТС'] = self.ports_vgw

    def get_filled_template(self):
        """Метод возвращающий заполненный шаблон ТР."""
        self.fill_vars()
        template = None
        if 'базов' in self.service.lower():
            template = self.templates.get('ВАТС Базовая(SIP регистрация через Интернет).')
        elif 'расш' in self.service.lower():
            template = self.templates.get('ВАТС Расширенная(SIP регистрация через Интернет).')
        if not template:
            raise ExistError('Не удалось определить тип ВАТС')
        self.text_block.set_plural(self.ports_vgw)
        ots_text = self.text_block.construct(template)
        self.ots.append(ots_text)


class Analog:
    """Класс организации новой услуги аналогового телефона."""
    def __init__(self, value_vars, ots):
        self.text_block = TextBlock(value_vars)
        self.templates = value_vars.get('templates')
        self.value_vars = value_vars
        self.ots = ots
        self.type_phone = value_vars.get('type_phone')
        self.phone_lines = sum([int(k) * v for k, v in value_vars.get('channels').items()])
        self.is_vats = False

    def fill_vars(self):
        """Метод, заполняющий шаблон ТР переменными."""
        phone_channels_string = construct_phone_channels_string(self.value_vars, self.is_vats)
        self.text_block.static_vars['тел. номер'] = ", ".join(phone_channels_string)
        if self.type_phone == 'ab':
            self.text_block.static_vars['название тел. шлюза'] = self.value_vars.get('form_exist_vgw_name')
            self.text_block.static_vars['модель тел. шлюза'] = self.value_vars.get('form_exist_vgw_model')
            self.text_block.static_vars['порт доступа на тел. шлюзе'] = self.value_vars.get('form_exist_vgw_port')
        else:
            self.text_block.static_vars['название тел. шлюза'] = 'установленный по решению выше'
            self.text_block.static_vars['модель тел. шлюза'] = self.value_vars.get('vgw')
            self.text_block.static_vars['порт доступа на тел. шлюзе'] = '1' if self.phone_lines == 1  else f'1-{self.phone_lines}'
        self.text_block.static_vars['количество линий'] = str(self.phone_lines)
        plur = self.phone_lines
        self.text_block.set_plural(plur)

    def get_filled_template(self):
        """Метод возвращающий заполненный шаблон ТР."""
        self.fill_vars()
        if self.type_phone == 'ak':
            template = self.templates.get("Подключение аналогового телефона с использованием тел. шлюза на стороне клиента.")
        else:
            template = self.templates.get("Подключение аналогового телефона с использованием тел. шлюза на ППС.")

        ots_text = self.text_block.construct(template)
        self.ots.append(ots_text)


class VatsAnalog(Analog):
    """Класс организации новой услуги ВАТС для аналогового телефона."""
    def __init__(self, value_vars, ots, service):
        super().__init__(value_vars, ots)
        self.ports_vgw = value_vars.get('ports_vgw')
        self.service = service
        self.is_vats = True

    def fill_vars(self):
        """Метод, заполняющий шаблон ТР переменными."""
        super().fill_vars()
        if 'базов' in self.service.lower():
            self.text_block.static_vars['набор сервисов ВАТС'] = 'базовым набором сервисов'
        elif 'расш' in self.service.lower():
            self.text_block.static_vars['набор сервисов ВАТС'] = 'расширенным набором сервисов'
        if not self.type_phone == 'ab':
            self.text_block.static_vars[
                'порт доступа на тел. шлюзе'] = '1' if self.ports_vgw == '1' else f'1-{self.ports_vgw}'

        self.text_block.static_vars['количество линий'] = self.ports_vgw
        self.text_block.static_vars['количество внутренних портов ВАТС'] = self.ports_vgw
        plur = int(self.ports_vgw)
        self.text_block.set_plural(plur)

    def get_filled_template(self):
        """Метод возвращающий заполненный шаблон ТР."""
        self.fill_vars()
        template = self.templates.get("ВАТС (аналоговая линия).")
        ots_text = self.text_block.construct(template)
        self.ots.append(ots_text)




class PassAnalog(Analog):
    """Класс переноса услуги аналогового телефона."""
    def fill_vars(self):
        """Метод, заполняющий шаблон ТР переменными."""
        super().fill_vars()
        self.text_block.static_vars['список тел. шлюзов'] = self.value_vars.get('old_name_model_vgws')

    def get_filled_template(self):
        """Метод возвращающий заполненный шаблон ТР."""
        self.fill_vars()
        if self.type_phone == 'ak':
            template = self.templates.get("Перенос сервиса Телефония на тел. шлюз на стороне клиента.")
        else:
            template = self.templates.get("Перенос сервиса Телефония на тел. шлюз на ППС.")
        ots_text = self.text_block.construct(template)
        self.ots.append(ots_text)


class Sip:
    """Класс организации новой услуги SIP телефонии."""
    def __init__(self, value_vars, ots):
        self.ots = ots
        self.text_block = TextBlock(value_vars)
        self.templates = value_vars.get('templates')
        self.value_vars = value_vars
        self.is_vats = False

    def get_filled_template(self):
        """Метод возвращающий заполненный шаблон ТР."""
        phone_channels_string = construct_phone_channels_string(self.value_vars, self.is_vats)
        self.text_block.static_vars['тел. номер'] = ", ".join(phone_channels_string)
        template = self.templates.get("Подключения по цифровой линии с использованием протокола SIP, тип линии «SIP регистрация через Интернет».")
        ots_text = self.text_block.construct(template)
        self.ots.append(ots_text)


class NewVgwClient:
    """Класс установки нового тел. шлюза у клиента."""
    def __init__(self, value_vars, ots, kad):
        self.text_block = TextBlock(value_vars)
        self.templates = value_vars.get('templates')
        self.value_vars = value_vars
        self.ots = ots
        self.vgw = value_vars.get('vgw')
        self.kad = kad

    def fill_vars(self):
        """Метод, заполняющий шаблон ТР переменными."""
        if self.vgw in ['D-Link DVG-5402SP', 'Eltex RG-1404G или Eltex TAU-4M.IP', 'Eltex TAU-8.IP']:
            model = self.vgw
            uplink_port = 'WAN порт'
        else:
            model = self.vgw + ' c кабелем для коммутации в плинт'
            uplink_port = 'Ethernet Порт 0'
        self.text_block.static_vars['модель тел. шлюза'] = model
        self.text_block.static_vars['магистральный порт на тел. шлюзе'] = uplink_port
        self.text_block.static_vars['название коммутатора'] = self.kad

    def get_filled_template(self):
        """Метод возвращающий заполненный шаблон ТР."""
        self.fill_vars()
        template = self.templates.get("Установка тел. шлюза на стороне клиента.")
        ots_text = self.text_block.construct(template)
        self.ots.append(ots_text)


class NewVgwPps:
    """Класс установки нового тел. шлюза на ППС."""
    def __init__(self, value_vars, ots):
        self.text_block = TextBlock(value_vars)
        self.templates = value_vars.get('templates')
        self.value_vars = value_vars
        self.ots = ots

    def get_filled_template(self):
        """Метод возвращающий заполненный шаблон ТР."""
        template = self.templates.get("Установка тел. шлюза на ППС.")
        self.text_block.static_vars['модель тел. шлюза'] = self.value_vars.get('vgw')
        self.text_block.static_vars['узел связи'] = self.value_vars.get('pps')
        ots_text = self.text_block.construct(template)
        self.ots.append(ots_text)


class NewServicePhone(Connectable):
    """Класс организации новой услуги Телефония."""
    def __init__(self, value_vars, service, ortr, ots):
        self.type_phone = value_vars.get('type_phone')
        vgw_connect = value_vars.get('vgw_connect')
        connect = vgw_connect if self.type_phone == 'ak' and vgw_connect != 'Не требуется' else None
        super().__init__(ortr, connect)
        self.ortr = ortr
        self.ots = ots
        self.text_block = TextBlock(value_vars)
        self.templates = value_vars.get('templates')
        self.value_vars = value_vars
        self.service = service

    def get_filled_template(self):
        """Метод возвращающий заполненный шаблон ТР."""
        if isinstance(self.mount, KtcMount) and self.mount.logic_csw:
            self.get_template_line_from_csw()

        vgw = None
        if self.type_phone == 'ap':
            vgw = NewVgwPps(self.value_vars, self.ots)
        elif self.type_phone == 'ak' and self.mount:
            kad = self.mount.kad if not self.mount.csw else 'клиентского коммутатора'
            vgw = NewVgwClient(self.value_vars, self.ots, kad)
        if vgw:
            vgw.get_filled_template()

        if 'ватс' in self.service.lower() and self.type_phone == 's':
            phone = VatsSip(self.value_vars, self.ots, self.service)
        elif 'ватс' in self.service.lower():
            phone = VatsAnalog(self.value_vars, self.ots, self.service)
        elif self.type_phone == 's':
            phone = Sip(self.value_vars, self.ots)
        else:
            phone = Analog(self.value_vars, self.ots)
        phone.get_filled_template()


class PassServicePhone(Connectable):
    """Класс переноса услуги Телефония."""
    def __init__(self, value_vars, service, ortr, ots):
        self.type_phone = value_vars.get('type_phone')
        vgw_connect = value_vars.get('vgw_connect')
        connect = vgw_connect if self.type_phone == 'ak' and vgw_connect != 'Не требуется' else None
        super().__init__(ortr, connect)
        self.ortr = ortr
        self.ots = ots
        self.text_block = TextBlock(value_vars)
        self.templates = value_vars.get('templates')
        self.value_vars = value_vars
        self.service = service

    def get_filled_template(self):
        """Метод возвращающий заполненный шаблон ТР."""
        if isinstance(self.mount, KtcMount) and self.mount.logic_csw:
            self.get_template_line_from_csw()

        vgw = None
        if self.type_phone == 'ap':
            vgw = NewVgwPps(self.value_vars, self.ots)
        elif self.type_phone == 'ak' and self.mount:
            kad = self.mount.kad if not self.mount.csw else 'клиентского коммутатора'
            vgw = NewVgwClient(self.value_vars, self.ots, kad)
        if vgw:
            vgw.get_filled_template()

        if self.type_phone != 's':
            phone = PassAnalog(self.value_vars, self.ots)
            phone.get_filled_template()


class PassServiceVideo:
    """Класс переноса услуги Видеонаблюдение."""
    def __init__(self, value_vars, service, ortr, ots):
        self.connect = None
        self.ortr = ortr
        self.ots = ots
        self.service = service
        self.text_block = TextBlock(value_vars)
        self.templates = value_vars.get('templates')
        self.value_vars = value_vars
        self.params = value_vars.get('pass_video_form')
        if not self.params:
            raise ExistError('Нет параметров переноса видеонаблюдения')
        self.camera_names = [v for k, v in self.params.items() if 'camera_name' in k]
        self.camera_names.sort()
        self.count_cameras = len(self.camera_names)
        self.change_video_ip = self.params.get('change_video_ip')
        self.poe = self.params.get('poe')

    def fill_vars(self):
        """Метод, заполняющий шаблон ТР переменными."""
        cam_str = '%название камеры% - порт: %порт доступа на маршрутизаторе%, новое место установки камеры: %Новое место Камеры%'
        self.text_block.multi_vars = {cam_str: []}
        self.text_block.static_vars['количество камер'] = str(self.count_cameras)

        if self.change_video_ip is True:
            strs = [
                'ОВИТС проведение работ:',
                '- Произвести настройку ^видеокамер^ и маршрутизатора для предоставления сервиса.',
                '- Актуализировать в ИС Cordis адреса видеопотока.'
            ]
            self.text_block.hidden_vars.update({i:i for i in strs})

        strs = []
        if self.poe == 'Сущ. POE-инжектор':
            strs = [
                '- Организовать %количество камер% ^линию^ от ^камер^ до маршрутизатора клиента.',
                '- Подключить {организованную} {линию} связи через POE ^инжектор^ в lan-^порт^ маршрутизатора:'
            ]
        elif self.poe == 'Новый POE-инжектор':
            strs = [
                '- Организовать %количество камер% ^линию^ от ^камер^ до маршрутизатора клиента.',
                '- Подключить {организованную} {линию} связи через POE ^инжектор^ в lan-^порт^ маршрутизатора:',
                'ОИПД подготовиться к работам:',
                '- Получить на складе территории:',
                '-- PoE-инжектор %модель PoE-инжектора% - %количество POE-инжекторов% шт.'
            ]
            self.text_block.static_vars['модель PoE-инжектора'] = 'СКАТ PSE-PoE.220AC/15VA'
            self.text_block.static_vars['количество POE-инжекторов'] = str(self.count_cameras)
        elif self.poe == 'Сущ. POE-коммутатор':
            strs = [
                '- Организовать %количество камер% ^линию^ от ^камер^ до POE-коммутатора.',
                '- Подключить {организованную} {линию} связи в ^порт^ POE-коммутатора:',
                '- Выполнить монтажные работы по переносу и подключению существующего POE-коммутатора.'
            ]
        elif self.poe == 'Новый POE-коммутатор':
            strs = [
                '- Организовать %количество камер% ^линию^ от ^камер^ до POE-коммутатора.',
                '- Подключить {организованную} {линию} связи в ^порт^ POE-коммутатора:',
                'ОИПД подготовиться к работам:',
                '- Получить на складе территории:',
                '-- POE-коммутатор %модель POE-коммутатора% - 1 шт.',
                '- Установить в помещении клиента POE-коммутатор %модель POE-коммутатора%. Организовать линию от маршрутизатора клиента до POE-коммутатора. Включить организованную линию связи:',
                '-- В свободный порт маршрутизатора;',
                '-- В порт %порт доступа на POE-коммутаторе% POE-коммутатора'
            ]
            if self.count_cameras < 5:
                self.text_block.static_vars['модель POE-коммутатора'] = 'D-Link DES-1005P'
                self.text_block.static_vars['порт доступа на POE-коммутаторе'] = '5'
            else:
                self.text_block.static_vars['модель POE-коммутатора'] = 'Atis PoE-1010-8P'
                self.text_block.static_vars['порт доступа на POE-коммутаторе'] = '10'
        self.text_block.hidden_vars.update({i: i for i in strs})

        for i in range(self.count_cameras):
            self.text_block.static_vars[f'название камеры {i}'] = self.params.get(f'camera_name_{i}')
            self.text_block.static_vars[f'порт доступа на маршрутизаторе {i}'] = self.params.get(f'camera_port_{i}')
            self.text_block.static_vars[f'Новое место Камеры {i}'] = self.params.get(f'camera_place_{i}')
            self.text_block.multi_vars[cam_str].append(
                f'"%название камеры {i}%" - порт: %порт доступа на маршрутизаторе {i}%, новое место установки камеры: %Новое место Камеры {i}%'
            )
        self.text_block.static_vars['перечисление камер'] = ', '.join([f'"{i}"' for i in self.camera_names])
        self.text_block.set_plural(self.count_cameras)

    def get_filled_template(self):
        """Метод возвращающий заполненный шаблон ТР."""
        self.fill_vars()
        template = self.templates.get('Перенос сервиса Видеонаблюдение в новую физическую точку подключения.')
        text = self.text_block.construct(template)
        self.ortr.append(text)


class KtcMount:
    """Базовый класс присоединения к СПД КТЦ."""
    def __init__(self, value_vars, connect, ortr):
        self.ortr = ortr
        self.text_block = TextBlock(value_vars)
        self.value_vars = value_vars
        self.templates = value_vars.get('templates')
        self.template_name = None
        self.params = value_vars.get('connects', {}).get(connect)
        if not self.params:
            raise ExistError('No data KTC')
        self.bind_resources = self.params.get('services')
        self.mount_type = self.params.get('sreda')
        self.exist_mount_type = self.params.get('exist_sreda')
        self.ppr = self.params.get('ppr')
        self.change_log = self.params.get('change_log')
        self.change_physic = self.params.get('change_physic')
        self.type_connect = self.params.get('type_connect')
        self.job = None
        self.service_part_tr = True
        self.head = self.value_vars.get('head')
        self.pps = _readable_node(value_vars.get('pps'))
        self.old_pps = ' '.join(self.head.split('\n')[3].split()[1:]) if self.head else None
        self.old_kad = self.type_connect.split('_')[0] if self.type_connect != 'Новое подключение' else None
        self.old_port = self.type_connect.split('_')[1] if self.type_connect != 'Новое подключение' else None
        self.kad = self.params.get('kad')
        self.port = self.params.get('port')
        self.logic_csw = True if any([
            self.params.get('logic_csw'),
            self.params.get('logic_change_gi_csw'),
            self.params.get('logic_replace_csw'),
            self.params.get('logic_change_csw')
        ]) else False
        self.csw = None
        self.on_csw_pass = None
        if self.logic_csw and self.params.get('logic_csw'):
            self.csw = NewCsw(value_vars, connect)
            self.csw.set_text_block(self.text_block)
            if self.type_connect != 'Новое подключение':
                special_spp_service = 'on_csw_pass'
                fake_unused_connects = []
                ots = None
                on_csw_pass = OnCswPassJob(value_vars, ortr, ots)
                on_csw_pass.define_services(special_spp_service, s_objs)
                on_csw_pass.register_mount(self, fake_unused_connects)
                self.on_csw_pass = on_csw_pass
        elif self.params.get('logic_replace_csw'):
            self.csw = ReplaceCsw(value_vars, connect)
            self.csw.set_text_block(self.text_block)
        elif self.params.get('logic_change_csw') or self.params.get('logic_change_gi_csw'):
            self.csw = PassageCsw(value_vars, connect)
            self.csw.set_text_block(self.text_block)

    def fill_vars(self):
        """Метод, заполняющий шаблон ТР переменными."""
        self.text_block.static_vars.update({
            'узел связи': self._readable_node(self.value_vars.get('pps')),
            'название коммутатора': self.kad,
            'порт доступа на коммутаторе': self.port,
            'отдел ОИПМ / ОИПД': 'ОИПД',
        })
        if self.ppr:
            self.fill_ppr()
        if self.type_connect != 'Новое подключение':
            self.passage()
        else:
            self.fill_new_line_from_kad()

    def fill_ppr(self):
        """Метод добавляет переменными о ППР."""
        strs = [
            '%отдел ОИПМ / ОИПД% подготовка к работам.',
            '- Требуется отключение согласно списку отключений в ППР %№ заявки ППР% согласовать проведение работ.',
            '- Совместно с ОНИТС СПД убедиться в восстановлении связи согласно списку отключений в ППР %№ заявки ППР%.',
            '- После проведения монтажных работ убедиться в восстановлении услуг согласно списку отключений в ППР %№ заявки ППР%.'
        ]
        self.text_block.hidden_vars.update({i: i for i in strs})
        self.text_block.static_vars.update({
            '№ заявки ППР': self.ppr,
        })

    @staticmethod
    def _readable_node(node_mon):
        """Данный метод приводит название узла к читаемой форме"""
        node_templates = {', РУА': 'РУА ', ', УА': 'УПА ', ', АВ': 'ППС ', ', КК': 'КК '}
        for key, item in node_templates.items():
            if node_mon.endswith(key):
                return item + node_mon[:node_mon.index(key)]
        return node_mon

    def get_params(self, service_params, service):
        """Метод возвращает переменными, применимые только к данному присоединению к СПД."""
        add_hidden_vars = {}
        add_static_vars = {}
        if service_params.get('port_type'):
            if service_params.get('port_type') == 'access':
                access_str = ", в порт подключения выдать vlan access"
                add_hidden_vars[access_str] = access_str
            elif service_params.get('port_type') == 'trunk':
                trunk_str = ", в порт подключения выдать vlan tag'ом"
                add_hidden_vars[trunk_str] = trunk_str
        add_hidden_vars[' СПД'] = ' СПД'
        add_hidden_vars['от %название коммутатора%'] = 'от %название коммутатора%'
        return add_static_vars, add_hidden_vars

    def is_not_change(self):
        """Метод возвращает информацию о том, меняется присоединие к СПД или нет."""
        if self.change_log == 'не меняется' and not self.params.get('logic_csw'):
            return True

    def fill_new_line_from_kad(self):
        """Метод добавляет переменными об организации новой линии от УС."""
        strs = [
            '- Организовать %тип линии связи% от %узел связи% до клиента [в новой точке подключения ]по решению ОТПМ.',
            '- Подключить организованную линию для клиента в коммутатор %название коммутатора%, порт задействовать %порт доступа на коммутаторе%.',
        ]
        self.text_block.hidden_vars.update({i: i for i in strs})

    def fill_exist_line_from_kad(self):
        """Метод добавляет переменными об использовании существующей линии от УС."""
        strs = ['- Использовать существующую %тип линии связи% от %узел связи% до клиента.', ]
        self.text_block.hidden_vars.update({i: i for i in strs})
        if self.old_port != self.port:
            strs = [
                '- Переключить линию для клиента в порт %порт доступа на коммутаторе% коммутатора %название коммутатора%.', ]
            self.text_block.hidden_vars.update({i: i for i in strs})

    def fill_rebuild_exist_line(self):
        """Метод добавляет переменными об частичном использовании существующей линии от УС."""
        strs = [
            '- Организовать %тип линии связи% [от %узел связи% ]до клиентcкого оборудования [в новой точке подключения ]по решению ОАТТР.',
            '- Логическое подключение клиента не изменится.',
        ]
        self.text_block.hidden_vars.update({i: i for i in strs})

    def fill_old_new_port(self):
        """Метод добавляет переменными о старом и новом портах."""
        strs = [
            'Старый порт: порт %старый порт доступа на коммутаторе% коммутатора %название коммутатора ранее используемого%.',
            'Новый порт: порт %порт доступа на коммутаторе% коммутатора %название коммутатора%.',
        ]
        self.text_block.hidden_vars.update({i: i for i in strs})
        self.text_block.static_vars['старый порт доступа на коммутаторе'] = self.type_connect.split('_')[1]
        self.text_block.static_vars['название коммутатора ранее используемого'] = self.type_connect.split('_')[0]

    def passage(self):
        """Метод добавляет переменными связанные с переносом присоединения к СПД."""
        if self.change_physic == 'меняется':
            self.text_block.hidden_vars['в новой точке подключения '] = 'в новой точке подключения '

        if self.change_log == 'не меняется':
            self.fill_rebuild_exist_line()
        else:
            if self.pps == self.old_pps and self.exist_mount_type == self.mount_type:
                self.fill_exist_line_from_kad()
            else:
                self.fill_new_line_from_kad()
            self.fill_old_new_port()

    def get_filled_template(self):
        """Метод возвращающий заполненный шаблон ТР."""
        self.fill_vars()
        if self.csw:
            self.ortr.append(self.csw.get_filled_template())
            self.service_part_tr = False if self.job == 'Перенос' else True # сделано чтобы не дублировались шаблоны
            # при одновременном переносе на КК и в новую точку. Не сработает случай когда в услугах только перенос и установка КК.
            if self.on_csw_pass:
                self.on_csw_pass.perform_job()
        elif self.type_connect == 'Новое подключение':
            template = self.templates.get(self.template_name)
            self.ortr.append(self.text_block.construct(template))
        elif self.job == 'Восстановление':
            self.text_block.hidden_vars.update({})
            template = self.templates.get("Восстановление трассы присоединения к СПД.")
            self.ortr.append(self.text_block.construct(template))
            self.service_part_tr = False
        elif self.change_physic == self.change_log == 'не меняется' and self.job == 'Перенос':
            template = self.templates.get("Изменение трассы присоединения к СПД.")
            self.ortr.append(self.text_block.construct(template))
            self.service_part_tr = False
        elif self.change_log == self.change_physic == 'не меняется' and self.mount_type == self.exist_mount_type:
            # сейчас когда change_log не меняется автоматически нов. среда становится равной существующей и невозможно
            # обработать случай расширения когда из работ только 100М конвертер надо поменять на 1Г у клиента
            pass
        else:
            template = self.templates.get("Изменение присоединения к СПД.")
            self.ortr.append(self.text_block.construct(template))
        self.value_vars.update({'kad': self.kad})


class UtpKtcMount(KtcMount):
    """Класс присоединения к СПД КТЦ по медной линии."""
    def __init__(self, value_vars, connect, ortr):
        super().__init__(value_vars, connect, ortr)
        self.template_name = "Присоединение к СПД по медной линии связи."

    def fill_vars(self):
        """Метод, заполняющий шаблон ТР переменными."""
        super().fill_vars()
        self.text_block.static_vars['отдел ОИПМ / ОИПД'] = 'ОИПД'
        self.text_block.static_vars['тип линии связи'] = 'медную линию связи'


class OpticKtcMount(KtcMount):
    """Класс присоединения к СПД КТЦ по оптической линии."""
    def __init__(self, value_vars, connect, ortr):
        super().__init__(value_vars, connect, ortr)
        if self.ppr:
            self.template_name = "Присоединение к СПД по оптической линии связи с простоем связи."
        else:
            self.template_name = "Присоединение к СПД по оптической линии связи."

    def fill_vars(self):
        """Метод, заполняющий шаблон ТР переменными."""
        super().fill_vars()
        self.text_block.static_vars['отдел ОИПМ / ОИПД'] = 'ОИПМ'
        self.text_block.static_vars['тип линии связи'] = 'ВОЛС'

        # лучше отказаться от %вид работ%,т.к. сложно отслеживать что было(ftth, медь, оптика) поэтому "заменить" не используется
        if self.change_log == 'меняется':
            strs = [
                '- Установить на стороне %узел связи% %тип конвертера/передатчика на стороне узла доступа%',
                '- На стороне клиента %вид работ% [%установленный тип конвертера/передатчика на стороне клиента% на ]%тип конвертера/передатчика на стороне клиента%',
                'ОНИТС СПД проведение работ:',
                '- На порту подключения клиента выставить скоростной режим %режим работы порта доступа%.'
            ]
            self.text_block.hidden_vars.update({i: i for i in strs})
            self.text_block.static_vars['вид работ'] = 'установить'

        self.text_block.static_vars.update({
            'отдел ОИПМ / ОИПД': 'ОИПМ',
            'тип конвертера/передатчика на стороне узла доступа': self.params.get('device_pps'),
            'тип конвертера/передатчика на стороне клиента': self.params.get('device_client'),
            'режим работы порта доступа': self.params.get('speed_port'),
        })


class WiFiKtcMount(KtcMount):
    """Класс присоединения к СПД КТЦ по радиоканалу."""
    def __init__(self, value_vars, connect, ortr):
        super().__init__(value_vars, connect, ortr)
        if self.ppr:
            self.template_name = "Присоединение к СПД по беспроводной среде передачи данных с простоем связи."
        else:
            self.template_name = "Присоединение к СПД по беспроводной среде передачи данных."

    def fill_vars(self):
        """Метод, заполняющий шаблон ТР переменными."""
        super().fill_vars()
        self.text_block.static_vars['отдел ОИПМ / ОИПД'] = 'ОИПД'
        self.text_block.static_vars['тип линии связи'] = 'медную линию связи'
        self.text_block.static_vars['модель беспроводной базовой станции'] = self.params.get('access_points')
        if self.params.get('access_points') == 'Infinet E5':
            strs = [
                '- Доставить в офис ОНИТС СПД беспроводные точки Infinet E5 для их настройки.'
                ' и настройки точек в офисе ОНИТС СПД'
                'После выполнения подготовительных работ в рамках заявки в ИС Cordis на ОНИТС СПД и настройки точек в офисе ОНИТС СПД:'
            ]
        else:
            strs = ['После выполнения подготовительных работ в рамках заявки в ИС Cordis на ОНИТС СПД:']    # переделать чтобы подставлялось как в обычной беспроводной среде
        self.text_block.hidden_vars.update({i:i for i in strs})
        to_client_str = '- Организовать %тип линии связи% от %узел связи% до клиента по решению ОТПМ.'
        if self.text_block.hidden_vars.get(to_client_str):
            del self.text_block.hidden_vars[to_client_str]

        if self.csw:
            strs = [
                '- Установить на стороне %узел связи% и на стороне клиента беспроводные точки доступа %модель беспроводной базовой станции% по решению ОТПМ.',
                '- Создать заявку в ИС Cordis на ОНИТС СПД для выделения реквизитов беспроводных точек доступа WDS/WDA.',
                '- По заявке в ИС Cordis выделить реквизиты для управления беспроводными точками.',
                '- Совместно с ОИПД подключить к СПД и запустить беспроводные станции (WDS/WDA).',
            ]
            self.text_block.hidden_vars.update({i: i for i in strs})


class RtkMount:
    """Класс присоединения к СПД Ростелеком."""
    def __init__(self, value_vars, connect, ortr):
        self.ortr = ortr
        self.text_block = TextBlock(value_vars)
        self.value_vars = value_vars
        self.templates = value_vars.get('templates')
        self.params = value_vars.get('connects', {}).get(connect)
        self.msan = value_vars.get('msan_exist')
        if not self.params:
            raise ExistError('No data RTK')
        self.mount_type = self.params.get('sreda') if self.params else None
        self.change_log = self.params.get('change_log')
        self.change_physic = self.params.get('change_physic')
        self.type_connect = self.params.get('type_connect')
        self.bind_resources = self.params.get('services')
        self.service_part_tr = True
        self.exist_mount_type = self.params.get('exist_sreda')
        self.old_kad = self.type_connect.split('_')[0] if self.type_connect != 'Новое подключение' else None
        self.old_port = self.type_connect.split('_')[1] if self.type_connect != 'Новое подключение' else None
        self.csw = None
        self.kad = self.params.get('kad')
        self.port = self.params.get('port')

    def fill_vars(self):
        """Метод, заполняющий шаблон ТР переменными."""
        self.text_block.static_vars.update({
            'IP коммутатора': self.kad,
            'порт доступа на коммутаторе': self.port
        })
        if self.mount_type == 'ПМ':
            self.text_block.static_vars.update({
                'название оператора': 'Ростелеком',
                'узел связи': 'РУА ЕКБ Автоматики переулок 1 стр.В3 П1 Э2 (аппаратная)',
                'название коммутатора': 'AR113-37.ekb',
                'порт доступа на коммутаторе': 'Po4'
            })
        elif self.mount_type == 'FVNO GPON':
            self.text_block.static_vars.update({
                'PLOAM-пароль': self.params.get('ploam')
            })
        elif self.mount_type == 'FVNO FTTH':
            cross_str = 'кросса Ростелеком, ОР %номер ОР%'
            switch_str = 'коммутатора Ростелеком %IP коммутатора%, порт %порт доступа на коммутаторе%'
            if self.params.get('optic_socket'):
                self.text_block.hidden_vars[cross_str] = cross_str
                self.text_block.static_vars['номер ОР'] = self.params.get('optic_socket')
            else:
                self.text_block.hidden_vars[switch_str] = switch_str
            if self.msan:
                strs = [
                    'ОИПМ подготовиться к работам:',
                    '- Для проведения работ на стороне клиента подготовить комплект оборудования:',
                    '-- Конвертер SNR-CVT-1000SFP mini с модулем SFP WDM, дальность до 20км (14dB), 1310 нм;',
                    '-- Конвертер "A" 100 Мбит/с, дальность до 20км (14dB), 1310 нм.',
                    '- Установить на стороне клиента конвертер "A" 100 Мбит/с, дальность до 20км (14dB), 1310 нм, выставить на конвертере режим работы Auto.',
                    'Внимание! В случае если линк не поднялся использовать конвертер SNR-CVT-1000SFP mini с модулем SFP WDM, дальность до 20км (14dB), 1310 нм.',
                ]
                self.text_block.hidden_vars.update({i: i for i in strs})
            else:
                convert_str = '- Установить на стороне клиента конвертер SNR-CVT-1000SFP mini с модулем SFP WDM, дальность до 20км (14dB), 1550 нм;'
                self.text_block.hidden_vars[convert_str] = convert_str

    def get_filled_template(self):
        """Метод возвращающий заполненный шаблон ТР."""
        choice = {
            'ПМ': 'Присоединение к СПД через последнюю милю стороннего оператора %название оператора%.',
            'FVNO Медь': 'Присоединение к СПД по медной линии связи по схеме "Ростелеком. Прямой FVNO".',
            'FVNO GPON': 'Присоединение к СПД по оптической линии связи (GPON) по схеме "Ростелеком. Прямой FVNO". ONT в качестве "конвертера".',
            'FVNO FTTH': 'Присоединение к СПД по оптической линии связи (FTTH) по схеме "Ростелеком. Прямой FVNO".',
        }
        self.fill_vars()
        template = self.templates.get(choice.get(self.mount_type))
        self.value_vars.update({'kad': 'AR113-37.ekb', 'pps': 'ЕКБ Автоматики переулок 1 стр.В3 П1 Э2 (аппаратная), РУА'})
        self.ortr.append(self.text_block.construct(template))

    def get_params(self, service_params, service):
        """Метод возвращает переменными, применимые только к данному присоединению к СПД."""
        add_hidden_vars = {}
        add_static_vars = {}
        if self.mount_type == 'ПМ':
            stick_str = self.templates.get("Организация услуги через L2-стык с Ростелеком.")
            add_hidden_vars['от %название коммутатора%'] = 'через последнюю милю стороннего оператора'
        else:
            stick_str = self.templates.get("Организация услуги access'ом через FVNO стык с Ростелеком.")
            add_hidden_vars['от %название коммутатора%'] = 'через FVNO стык стороннего оператора'
        add_static_vars['tag vlan'] = self.params.get('vlan')
        add_static_vars['№ заявки СПП'] = self.value_vars.get('ticket_k')
        add_hidden_vars[' СПД'] = ' СПД Ростелеком'
        if stick_str:
            add_hidden_vars['Организация услуги через стык'] = '\n'.join(stick_str.split('\n')[2:])
        return add_static_vars, add_hidden_vars

    def is_not_change(self):
        """Метод возвращает информацию о том, меняется присоединие к СПД или нет."""
        if self.change_log == 'не меняется':
            return True


class VlanMount:
    """Базовый класс присоединения к СПД сторонних операторов по последней миле."""
    def __init__(self, value_vars, connect, ortr):
        self.params = value_vars.get('connects', {}).get(connect)
        if not self.params:
            raise ExistError('No data Connection')
        self.ortr = ortr
        self.text_block = TextBlock(value_vars)
        self.value_vars = value_vars
        self.templates = value_vars.get('templates')
        self.template = None
        self.extra_hidden_vars = {}
        self.extra_static_vars = {}
        self.csw = None
        self.kad = None
        self.port = None
        self.mount_type = None
        self.service_part_tr = True
        self.change_log = 'меняется'
        self.change_physic = 'меняется'
        self.type_connect = self.params.get('type_connect')
        self.bind_resources = self.params.get('services')
        self.exist_mount_type = ''
        self.old_kad = self.type_connect.split('_')[0] if self.type_connect != 'Новое подключение' else None
        self.old_port = self.type_connect.split('_')[1] if self.type_connect != 'Новое подключение' else None

    def get_filled_template(self):
        """Метод возвращающий заполненный шаблон ТР."""
        template = self.templates.get(self.template)
        match = re.search('Узел связи: (.+);\n- Коммутатор: (.+);', template, flags=re.DOTALL)
        if match:
            pps, kad = match.groups()
            self.value_vars.update({'kad': kad, 'pps': pps})
        self.ortr.append(self.text_block.construct(template))

    def _get_params(self, service_params, service):
        """Метод возвращает переменными, связанные со сторонним оператором по последней миле."""
        stick_str = self.templates.get("Организация услуги access'ом через FVNO стык с %название оператора%.")
        is_dhcp_service = True if service.startswith('Интернет, DHCP') or service_params.get('change_log_shpd') == 'Новая подсеть /32' else False
        if is_dhcp_service:
            self.extra_hidden_vars[text.fvno_dhcp_access] = text.fvno_dhcp_access
        else:
            port_type = service_params.get('port_type')
            if port_type == 'trunk':
                self.extra_hidden_vars[text.fvno_not_dhcp_trunk] = text.fvno_not_dhcp_trunk
                stick_str = self.templates.get("Организация услуги trunk'ом через FVNO стык с %название оператора%.")
            else:
                self.extra_hidden_vars[text.fvno_not_dhcp_access] = text.fvno_not_dhcp_access

        self.extra_static_vars['№ заявки СПП'] = self.value_vars.get('ticket_k')
        self.extra_hidden_vars[' СПД'] = ' СПД %название оператора%'
        self.extra_hidden_vars['от %название коммутатора%'] = 'через FVNO стык стороннего оператора'
        self.extra_hidden_vars['Организация услуги через стык'] = '\n'.join(stick_str.split('\n')[2:])
        return self.extra_static_vars, self.extra_hidden_vars

    def is_not_change(self):
        """Метод возвращает информацию о том, меняется присоединие к СПД или нет."""
        return False


class VectorMount(VlanMount):
    """Класс присоединения к СПД Вектор СБ."""
    def __init__(self, value_vars, connect, ortr):
        super().__init__(value_vars, connect, ortr)
        self.template = 'Присоединение к СПД по медной линии связи по схеме "ООО "Вектор СБ". Прямой FVNO".'

    def get_params(self, service_params, service):
        """Метод возвращает переменными, применимые только к данному присоединению к СПД."""
        self.extra_static_vars['название оператора'] = 'ООО "Вектор СБ"'
        return self._get_params(service_params, service)


class PpmMount(VlanMount):
    """Класс присоединения к СПД Пред-последняя миля."""
    def __init__(self, value_vars, connect, ortr):
        super().__init__(value_vars, connect, ortr)
        self.template = 'Присоединение к СПД по медной линии связи по схеме "ООО "Пред-последняя миля". Прямой FVNO".'

    def get_params(self, service_params, service):
        """Метод возвращает переменными, применимые только к данному присоединению к СПД."""
        self.extra_static_vars['название оператора'] = 'ООО "Пред-последняя миля"'
        return self._get_params(service_params, service)


class PassService(Connectable):
    """Базовый класс для услуг, требующих переноса."""
    def __init__(self, value_vars, service, ortr):
        connect = value_vars.get('service_params', {}).get(service).get('connect')
        super().__init__(ortr, connect)
        self.service = service
        self.text_block = TextBlock(value_vars)
        self.templates = value_vars.get('templates')
        self.value_vars = value_vars
        self.readable_services = None
        self.service_name = None
        self.service_name_desc = None
        self.cordis_sw = value_vars.get('selected_ono')[0][-2]
        self.service_params = value_vars.get('service_params', {}).get(service)
        self.change_log_shpd = self.service_params['change_log_shpd']
        self.job = value_vars.get('types_jobs').get(service)

    def get_text_block(self):
        """Метод возвращает свой класс переменных TextBlock"""
        return self.text_block

    def set_text_block(self, text_block):
        """Метод устанавливает класс переменных TextBlock, взятый из класс работ, вместо собственного, для того чтобы
         в классе работ были переменные разных услуг в случае одновременного переноса."""
        self.text_block = text_block

    def get_service_data(self):
        """Метод на основе услуг Cordis формирует строку содержащую названия и описание услуг. Также определяет наличие
         услуг ШПД с подсеть /32 и оставляет для них только название. Значение подсети добавляется в переменную
          'ресурс на договоре'"""
        desc = self.get_cis_resources()[self.service_name]
        self.readable_services = {self.service_name: desc}
        services, service_shpd_change = _separate_services_and_subnet_dhcp(self.readable_services, self.change_log_shpd)
        if service_shpd_change:
            self.text_block.static_vars['ресурс на договоре'] = ', '.join(service_shpd_change)
        self.service_name_desc = ', '.join(services)

    def fill_vars(self):
        """Метод, заполняющий шаблон ТР переменными."""
        self.text_block.static_vars['название сервиса'] = self.service_name
        self.text_block.static_vars['указать сервис'] = self.service_name_desc
        if not self.mount:
            raise ExistError(f'Для переноса сервиса {self.service_name} требуется подключение.')
        static_vars, hidden_vars = self.get_mount_vars(self.service_params, self.service)
        self.text_block.static_vars.update(static_vars)
        self.text_block.hidden_vars.update(hidden_vars)

        department_str = 'отдел ОИПМ / ОИПД'
        self.text_block.static_vars[department_str] = 'ОИПМ' if self.mount.mount_type in ('2', '4') else 'ОИПД'
        if self.mount.change_log == 'меняется':
            actual_str = '- Актуализировать информацию в ИС Cordis и системах учета.'
            if 'FVNO' in self.mount.exist_mount_type or self.mount.old_kad.startswith('CSW'):
                self.text_block.hidden_vars[actual_str] = actual_str
            else:
                strs = [actual_str, '- Сообщить в ОЛИ СПД об освободившемся порте на коммутаторе %название коммутатора%.']
                self.text_block.hidden_vars.update({i: i for i in strs})
                self.text_block.static_vars['название коммутатора'] = self.mount.old_kad
        # подумать про перенос на ПМ. тогда строка сопроводить ОИПМ не нужна, может ее вообще убрать.


class PassServiceBgp(PassService):
    """Класс переноса услуги подключение по BGP"""
    def __init__(self, value_vars, service, ortr):
        super().__init__(value_vars, service, ortr)
        self.service_name = '"Подключение по BGP"'

    def fill_vars(self):
        """Метод, заполняющий шаблон ТР переменными."""
        self.get_service_data()
        if self.job == 'Расширение':
            strs = [
                '- Расширить полосу ШПД в ИС Cordis.',
                '- Выполнить настройки на оборудовании для расширения полосы сервиса %указать сервис%[ на %пропускная способность%].',
            ]
            self.text_block.hidden_vars.update({i: i for i in strs})
        super().fill_vars()


class PassServiceShpd(PassService):
    """Класс переноса услуги ШПД"""
    def __init__(self, value_vars, service, ortr):
        super().__init__(value_vars, service, ortr)
        self.service_name = '"ШПД в интернет"'

    def fill_vars(self):
        """Метод, заполняющий шаблон ТР переменными."""
        self.get_service_data()
        if self.change_log_shpd != 'существующая адресация':
            strs = [
                'МКО:',
                '- Согласовать необходимость смены реквизитов.',
                'ОНИТС СПД подготовиться к работам:',
                '- По заявке в ИС Cordis выделить подсеть с маской %нов. маска IP-сети%.',
                '-- по согласованию с клиентом сменить реквизиты для услуги "ШПД в Интернет" на новую подсеть с маской %нов. маска IP-сети%.',
                '- После смены реквизитов:',
                '- разобрать ресурс %ресурс на договоре% на договоре.',
            ]
            self.text_block.hidden_vars.update({i: i for i in strs})
            self.text_block.static_vars[
                'нов. маска IP-сети'] = '/30' if self.change_log_shpd == 'Новая подсеть /30' else '/32'
        if self.job == 'Расширение':
            strs = [
                '- Расширить полосу ШПД в ИС Cordis.',
                '- Выполнить настройки на оборудовании для расширения полосы сервиса %указать сервис%[ на %пропускная способность%].',
            ]
            self.text_block.hidden_vars.update({i: i for i in strs})
        super().fill_vars()


class PassageJob:
    """Базовый класс работ, связанных с переносом услуг"""
    def __init__(self, value_vars, ortr):
        self.text_block = TextBlock(value_vars)
        self.templates = value_vars.get('templates')
        self.ortr = ortr
        self.services = []
        self.type_passage = None
        self.needs = None
        self.all_service_name_desc = []
        self.all_service_name = []
        self.value_vars = value_vars
        self.mount = None
        self.unused_connects = None
        self.connect_name = None
        self.job_name = None
        self.template_name = "Перенос ^сервиса^ %название сервиса% %тип переноса%."

    def update_needs(self, need):
        """Метод используется для заполнения строки Требуется в ТР. Принимает описание выполняемых работ
        и ставит им в соответствие перечень участвующих услуг."""
        exist_needs = self.value_vars.get('needs')
        needs = {} if not exist_needs else exist_needs
        total_needs = self.all_service_name
        if needs.get(need):
            total_needs += needs.get(need)
        needs.update({need: total_needs})
        self.value_vars.update({'needs': needs})

    def fill_vars(self):
        """Метод, заполняющий шаблон ТР переменными."""
        for service in self.services:
            service.fill_vars()
            self.all_service_name_desc.append(service.service_name_desc)
            self.all_service_name.append(service.service_name)
        plur = len(self.services)
        if plur:
            self.text_block.set_plural(plur)
        self.text_block.static_vars['название сервиса'] = ', '.join(self.all_service_name)
        self.text_block.static_vars['указать сервис'] = ', '.join(self.all_service_name_desc)
        self.text_block.static_vars['тип переноса'] = self.type_passage
        if not self.mount.csw:
            self.fill_mko()

    def perform_job(self):
        """Метод возвращающий заполненный шаблон ТР."""
        if not self.mount:
            raise ExistError('Для работ не определено подключение')
        if self.mount.change_physic == self.mount.change_log == 'не меняется' and self.job_name == 'Перенос':
            self.update_needs('Перенос трассы')
        elif self.mount.change_physic == 'меняется' and self.job_name == 'Перенос':
            self.update_needs('Перенос сервиса')
        elif self.mount.change_log == 'меняется' and self.job_name == 'Перенос':
            self.update_needs('Перенос логического подключения')
        elif self.job_name == 'Расширение':
            self.update_needs('Расширение')

        self.get_mount_filled_template()
        if self.mount.service_part_tr:
            self.fill_vars()
            for service in self.services:
                if service.mount and service.mount.params.get('logic_csw'):
                    service.get_template_line_from_csw()
            template = self.templates.get(self.template_name)
            self.ortr.append(self.text_block.construct(template))

    def define_services(self, spp_service, service_objects):
        """Метод определяет используемое Присоединение. На основании Присоединения определяет название услуг Cordis,
         участвующих в работах. На основании названий услуг опдеделяет какие именно услуги будут участвовать в работах.
          Регистрирует у себя классы данных услуг."""
        service_params = self.value_vars.get('service_params')
        connects = self.value_vars.get('connects')
        selected_ono = self.value_vars.get('selected_ono')
        self.connect_name = service_params.get(spp_service).get('connect')
        readable_services = connects[self.connect_name]['services']
        choised_ono = [i for i in selected_ono for v in readable_services.values() if i[-4] in ''.join(v)]
        requisites_to_types = convert_requisites_to_types(choised_ono)
        service_names = set([requisites_to_types[i[-4]] for i in choised_ono])
        services = [
            service_objects[name](self.value_vars, spp_service, self.ortr) for name in service_names
        ]
        for service in services:
            service.set_text_block(self.text_block)
            self.services.append(service)

    def register_mount(self, mount, unused_connects):
        """Метод регистрирует список неиспользованных присоединений. Требуется для того, чтобы в случае использования
        одного Присоединия для нескольких работ информация о Присоединении не дублировалась. Также регистрирует
         используемый класс Присоединия. Траснлирует данный класс в классы услуг."""
        self.mount = mount
        self.mount.job = self.job_name
        self.unused_connects = unused_connects
        for service in self.services:
            if service.connect:
                service.set_mount(mount)


    def get_mount_filled_template(self):
        """Метод обращается к методу класса Присоединия, который возвращает заполненный шаблон присоединения.
        Отмечает данное присоединие как использованное."""
        if self.connect_name in self.unused_connects:
            self.mount.get_filled_template()
            self.unused_connects.remove(self.connect_name)

    def fill_mko(self):
        """Метод добавляет в шаблон переменные связанные с МКО"""
        strs = [
            'МКО:',
            '- Проинформировать клиента о простое ^сервиса^ на время проведения работ.',
            '- Согласовать время проведение работ.',
            '- Создать заявку в ИС Cordis на ОНИТС СПД для переноса ^сервиса^ %название сервиса%.',
            'В заявке ИС Cordis указать время проведения работ по переносу ^сервиса^.'
        ]
        self.text_block.hidden_vars.update({i: i for i in strs})


class RecoveryJob:
    """Класс работ, связанных с восстановлением услуг"""
    def __init__(self, value_vars, ortr, ots):
        self.text_block = TextBlock(value_vars)
        self.value_vars = value_vars
        self.mount = None
        self.unused_connects = None
        self.connect_name = None
        self.job_name = 'Восстановление'

    def update_needs(self, need):
        """Метод используется для заполнения строки Требуется в ТР."""
        exist_needs = self.value_vars.get('needs')
        needs = {} if not exist_needs else exist_needs
        needs.update({need: None})
        self.value_vars.update({'needs': needs})

    def perform_job(self):
        """Метод выполняет работы по восстановлению."""
        self.update_needs('Восстановление')
        if self.mount:
            self.get_mount_filled_template()


    def define_services(self, spp_service, service_objects):
        """Метод только определяет используемое Присоединение. Услиги для данных работ не учитываются."""
        service_params = self.value_vars.get('service_params')
        self.connect_name = service_params.get(spp_service).get('connect')

    def register_mount(self, mount, unused_connects):
        """Метод регистрирует список неиспользованных присоединений. Требуется для того, чтобы в случае использования
        одного Присоединия для нескольких работ информация о Присоединении не дублировалась. Также регистрирует
         используемый класс Присоединия."""
        self.mount = mount
        self.mount.job = self.job_name
        self.unused_connects = unused_connects

    def get_mount_filled_template(self):
        """Метод обращается к методу класса Присоединия, который возвращает заполненный шаблон присоединения.
        Отмечает данное присоединие как использованное."""
        if self.connect_name in self.unused_connects:
            self.mount.get_filled_template()
            self.unused_connects.remove(self.connect_name)


class PhysicLogicPassJob(PassageJob):
    """Класс работ, связанных с переносом услуг в новую точку подключения или изменение логического подключения услуг."""
    def __init__(self, value_vars, ortr, ots):
        super().__init__(value_vars, ortr)
        self.job_name = 'Перенос'

    def fill_vars(self):
        """Метод, заполняющий шаблон ТР переменными."""
        if self.mount.change_log == 'меняется':
            self.type_passage = 'в новую логическую точку подключения'
        if self.mount.change_physic == 'меняется':
            self.type_passage = 'в новую физическую точку подключения'
        if not self.value_vars.get('type_ticket') == 'ПТО':
            self.fill_mko()
        super().fill_vars()


class GigabitPassJob(PassageJob):
    """Класс работ, связанных с расширением полосы услуг"""
    def __init__(self, value_vars, ortr, ots):
        super().__init__(value_vars, ortr)
        self.type_passage = 'в гигабитный порт'
        self.job_name = 'Расширение'
        self.template_name = 'Расширение ^сервиса^ %название сервиса%.'

    def fill_vars(self):
        """Метод, заполняющий шаблон ТР переменными."""
        super().fill_vars()
        if self.mount.change_log == 'меняется' and not self.mount.csw:
            strs = [
                '-- сопроводить работы %отдел ОИПМ / ОИПД% по перенесу ^сервиса^ %указать сервис% %тип переноса%.',
                '-- перенести ^сервис^ %указать сервис% %тип переноса%.'
            ]
            self.text_block.hidden_vars.update({i: i for i in strs})

        if self.mount.csw and self.mount.csw.change_gi_csw:
            shpd = [s for s in self.services if isinstance(s, PassServiceShpd)]
            if shpd:
                self.template_name = 'Расширение сервиса "ШПД в Интернет".'
            messge_str = '- Сообщить в ОЛИ СПД об освободившемся порте на коммутаторе %название коммутатора%.'
            if self.text_block.hidden_vars.get(messge_str):
                del self.text_block.hidden_vars[messge_str]


class OnCswPassJob(PassageJob):
    """Класс работ, связанных с переносом услуг на клиентский коммутатор."""
    def __init__(self, value_vars, ortr, ots):
        super().__init__(value_vars, ortr)
        self.type_passage = 'на клиентский коммутатор'


class OrganizationJob:
    """Класс работ, связанных с организацией услуг."""
    def __init__(self, value_vars, ortr, ots):
        self.value_vars = value_vars
        self.service = None
        self.text_block = TextBlock(value_vars)
        self.templates = value_vars.get('templates')
        self.ortr = ortr
        self.ots = ots
        self.services = []
        self.mount = None
        self.connect_name = None
        self.unused_connects = None
        self.job_name = 'Организация'


    def define_services(self, spp_service, new_service_objects):
        """Метод на основании описания услуги в СПП определяет какую именно услугу требуется организовать.
          Регистрирует у себя класс данной услуги."""
        splitted = spp_service.split()
        service_name = splitted[0].strip(',') if splitted[0] != 'Порт' else f'{splitted[0]} {splitted[1]}'
        new_service_object = new_service_objects.get(f'{self.job_name}_{service_name}')
        if new_service_object:
            new_service = new_service_object(self.value_vars, spp_service, self.ortr, self.ots)
            self.connect_name = new_service.connect
            self.services.append(new_service)

    def perform_job(self):
        """Метод выполняет работы по оргназици услуги."""
        if self.mount and not self.mount.is_not_change():
            self.get_mount_filled_template()

        for service in self.services:
            service.get_filled_template()

    def register_mount(self, mount, unused_connects):
        """Метод регистрирует список неиспользованных присоединений. Требуется для того, чтобы в случае использования
        одного Присоединия для нескольких работ информация о Присоединении не дублировалась. Также регистрирует
         используемый класс Присоединия."""
        self.mount = mount
        self.unused_connects = unused_connects
        for service in self.services:
            if service.connect:
                service.set_mount(self.mount)

    def get_mount_filled_template(self):
        """Метод обращается к методу класса Присоединия, который возвращает заполненный шаблон присоединения.
        Отмечает данное присоединие как использованное."""
        if self.connect_name in self.unused_connects:
            self.mount.get_filled_template()
            self.unused_connects.remove(self.connect_name)


class PassPhoneJob:
    """Класс работ, связанных с переносом услуги Телефония."""
    def __init__(self, value_vars, ortr, ots):
        self.value_vars = value_vars
        self.ortr = ortr
        self.ots = ots
        self.services = []
        self.mount = None
        self.connect_name = None
        self.unused_connects = None
        self.job_name = 'ПереносТелефон'

    def define_services(self, spp_service, service_objects):
        """Метод регистрирует класс Услуги Переноса Телефонии"""
        service_name = spp_service.split()[0].strip(',')
        service_object = service_objects.get(service_name)
        if service_object:
            service = service_object(self.value_vars, spp_service, self.ortr, self.ots)
            self.connect_name = service.connect
            self.services.append(service)

    def perform_job(self):
        """Метод выполняет работы по переносу услуги Телефония."""
        if self.mount and not self.mount.is_not_change():
            self.get_mount_filled_template()

        for service in self.services:
            service.get_filled_template()

    def register_mount(self, mount, unused_connects):
        """Метод регистрирует список неиспользованных присоединений. Требуется для того, чтобы в случае использования
        одного Присоединия для нескольких работ информация о Присоединении не дублировалась. Также регистрирует
         используемый класс Присоединия."""
        self.mount = mount
        self.unused_connects = unused_connects
        for service in self.services:
            if service.connect:
                service.set_mount(self.mount)

    def get_mount_filled_template(self):
        """Метод обращается к методу класса Присоединия, который возвращает заполненный шаблон присоединения.
        Отмечает данное присоединие как использованное."""
        if self.connect_name in self.unused_connects:
            self.mount.get_filled_template()
            self.unused_connects.remove(self.connect_name)



class PassVideoJob:
    """Класс работ, связанных с переносом услуги Видеонаблюдение."""
    def __init__(self, value_vars, ortr, ots):
        self.value_vars = value_vars
        self.ortr = ortr
        self.ots = ots
        self.services = []
        self.connect_name = None
        self.job_name = 'ПереносВидеонаблюдение'

    def update_needs(self, need):
        """Метод используется для заполнения строки Требуется в ТР."""
        exist_needs = self.value_vars.get('needs')
        needs = {} if not exist_needs else exist_needs
        needs.update({need: None})
        self.value_vars.update({'needs': needs})

    def define_services(self, spp_service, service_objects):
        """Метод регистрирует класс Услуги Переноса Видеонаблюдения"""
        service_name = spp_service.split()[0].strip(',')
        service_object = service_objects.get(service_name)
        if service_object:
            service = service_object(self.value_vars, spp_service, self.ortr, self.ots)
            self.services.append(service)

    def perform_job(self):
        """Метод выполняет работы по переносу услуги Видеонаблюдение."""
        self.update_needs('ПереносВидеонаблюдение')
        for service in self.services:
            service.get_filled_template()

    def register_mount(self, mount, unused_connects):
        """Заглушка. Нужна для унификации работ. Присоединение для данных работ не требуется"""


class Csw:
    """Базовый класс, используемый в рамках класса Присоединение к СПД КТЦ, для работ с участием клиентского коммутатора."""
    def __init__(self, value_vars, connect):
        self.text_block = TextBlock(value_vars)
        self.value_vars = value_vars
        self.templates = value_vars.get('templates')
        self.params = value_vars.get('connects', {}).get(connect)
        if not self.params:
            raise ExistError('No data KTC')
        self.mount_type = self.params.get('sreda') if self.params else None
        self.exist_mount_type = self.params.get('exist_sreda') if self.params else None
        self.ppr = self.params.get('ppr')
        self.mount_services = self.params.get('services')
        self.csw_1000 = True if self.params.get('logic_change_gi_csw') or self.params.get('logic_run_gi_csw') else False
        self.change_gi_csw = self.params.get('logic_change_gi_csw')
        self.change_csw = self.params.get('logic_change_csw')
        self.install_csw = self.params.get('logic_csw')
        self.replace_csw = self.params.get('logic_replace_csw')
        self.old_model_csw = value_vars.get('old_model_csw')
        self.old_name_csw = value_vars.get('old_name_csw')
        self.model_csw = self.params.get('model_csw')
        self.uplink_port_csw = self.params.get('uplink_port_csw')
        self.head = self.value_vars.get('head')
        self.kad = self.params.get('kad')
        self.port = self.params.get('port')
        self.pps = _readable_node(value_vars.get('pps'))
        self.old_pps = ' '.join(self.head.split('\n')[3].split()[1:]) if self.head else None
        self.type_connect = self.params.get('type_connect')
        # для расширения нужно выбирать конкретный ресурс, поэтому для одновременного перевода на гигабит кк с расширением сервиса
        # нельзя в интерфейсе выбрать магистральный порт
        if self.type_connect.startswith('CSW'):
            self.old_kad = self.head.split('\n')[4].split()[2]
            self.old_port = ''.join(self.head.split('\n')[5].split()[2:]) # чтобы обрабатывались и порты Port 1
        else:
            self.old_kad = self.type_connect.split('_')[0] if self.type_connect != 'Новое подключение' else None
            self.old_port = self.type_connect.split('_')[1] if self.type_connect != 'Новое подключение' else None
        self.service_part_tr = True
        self.change_physic = self.params.get('change_physic')
        self.change_log = self.params.get('change_log')
        self.device_pps = self.params.get('device_pps')
        self.replace_str_device_client = ''
        self.device_client = self.params.get('device_client')

    def set_text_block(self, text_block):
        """Метод устанавливает класс переменных TextBlock, взятый из класс Приесоединение, вместо собственного,
         для того чтобы объединить переменные данного класса с классом Присоединение, т.к. большая часть переменных
          совпадает."""
        self.text_block = text_block

    def fill_vars(self):
        """Метод, заполняющий шаблон ТР переменными."""
        self.text_block.static_vars['пропускная способность'] = '1000 Мбит/с' if self.csw_1000 else '100 Мбит/с'
        self.text_block.static_vars.update({
            'узел связи': self.pps,
            'название коммутатора': self.kad,
            'модель коммутатора': self.model_csw,
            'магистральный порт на клиентском коммутаторе': self.uplink_port_csw,
        })

        if self.csw_1000 is True and self.model_csw == 'D-Link DGS-1100-06/ME' and any([self.install_csw, self.replace_csw]):
            strs = [
                '-ВНИМАНИЕ! Совместно с ОНИТС СПД удаленно настроить клиентский коммутатор.',
                '- Совместно с %отдел ОИПМ / ОИПД% удаленно настроить клиентский коммутатор.'
            ]
            self.text_block.hidden_vars.update({i: i for i in strs})

        if self.old_pps and self.old_pps != self.pps:
            self.fill_change_shpd_subnet_32()

        if self.old_kad and self.old_kad.split('-')[1] not in self.kad:
            self.fill_change_ip_csw_and_vgw()

        if self.old_kad and (self.old_port != self.port or self.old_kad != self.kad):
            self.fill_change_old_port_to_new_port()

        if self.mount_type in ['1', '3']:
            self.text_block.static_vars['отдел ОИПМ / ОИПД'] = 'ОИПД'
        else:
            self.text_block.static_vars['отдел ОИПМ / ОИПД'] = 'ОИПМ'
            strs = [
                'и %тип конвертера/передатчика на стороне клиента%'
            ]
            self.text_block.hidden_vars.update({i:i for i in strs})

        self.text_block.static_vars['название коммутатора'] = self.kad
        self.text_block.static_vars['порт доступа на коммутаторе'] = self.params.get('port')
        self.text_block.static_vars['тип конвертера/передатчика на стороне узла доступа'] = self.device_pps
        self.device_client = self.device_client.replace(' в клиентское оборудование', self.replace_str_device_client)
        self.text_block.static_vars['тип конвертера/передатчика на стороне клиента'] = self.device_client


    def fill_change_old_port_to_new_port(self):
        """Метод добавляет переменные старого и нового портов."""
        free_port_str = '- Сообщить в ОЛИ СПД об освободившемся порте на %название коммутатора ранее используемого%.'
        self.text_block.hidden_vars[free_port_str] = free_port_str
        self.text_block.static_vars['название коммутатора ранее используемого'] = self.old_kad
        self.text_block.static_vars['старый порт доступа на коммутаторе'] = self.old_port
        strs = [
            'Старый порт: порт %старый порт доступа на коммутаторе% коммутатора %название коммутатора ранее используемого%.',
            'Новый порт: порт %порт доступа на коммутаторе% коммутатора %название коммутатора%.',
        ]
        self.text_block.hidden_vars.update({i: i for i in strs})

    def fill_change_ip_csw_and_vgw(self):
        """Метод добавляет переменные при смене агрегации, связанные устройствами."""
        strs = [
            '- Выделить для клиентского коммутатора[ и тел. шлюза %название тел. шлюза%] новые реквизиты управления.',
            '- Сменить реквизиты клиентского коммутатора [и тел. шлюза %название тел. шлюза%].',
            '- Перед проведением работ запросить ОНИТС СПД сменить реквизиты клиентского коммутатора %название коммутатора клиентского% [и тел. шлюза %название тел. шлюза%] на ZIP.',
            '- Перед проведением работ запросить ОНИТС СПД сменить реквизиты тел. шлюза %название тел. шлюза% на ZIP.',
        ]
        self.text_block.hidden_vars.update({i: i for i in strs})

        vgw_chains = self.value_vars.get('vgw_chains') if self.value_vars.get('vgw_chains') else []
        waste_vgw = self.value_vars.get('waste_vgw') if self.value_vars.get('waste_vgw') else []
        vgws = [i.get('name') for i in vgw_chains + waste_vgw if i.get('model') != 'ITM SIP']

        if vgws and len(vgws) == 1:
            strs = [
                ' и тел. шлюза %название тел. шлюза%',
                ' и тел. шлюз %название тел. шлюза%',
                'и тел. шлюза %название тел. шлюза%',
                'и тел. шлюз %название тел. шлюза%'
            ]
            self.text_block.hidden_vars.update({i: i for i in strs})
            self.text_block.static_vars['название тел. шлюза'] = ', '.join(vgws)
        elif vgws and len(vgws) > 1:
            vgw_str_1 = ' и тел. шлюза %название тел. шлюза%'
            vgw_str_2 = ' и тел. шлюз %название тел. шлюза%'
            vgw_str_3 = 'и тел. шлюза %название тел. шлюза%'
            vgw_str_4 = 'и тел. шлюз %название тел. шлюза%'
            self.text_block.hidden_vars.update({
                vgw_str_1: ' и тел. шлюзов %название тел. шлюза%',
                vgw_str_2: ' и тел. шлюзы %название тел. шлюза%',
                vgw_str_3: 'и тел. шлюзов %название тел. шлюза%',
                vgw_str_4: 'и тел. шлюзы %название тел. шлюза%',
            })
            self.text_block.static_vars['название тел. шлюза'] = ', '.join(vgws)

    def fill_change_shpd_subnet_32(self):
        """Метод добавляет переменные при смене агрегации, связанные с ШПД."""
        readable_services = self.params.get('services')
        change_log_shpd = 'Новая подсеть /32'
        services, service_shpd_change = _separate_services_and_subnet_dhcp(readable_services, change_log_shpd)
        dhcp = [s for s in service_shpd_change if '/32' in s]
        if dhcp:
            strs = [
                '- Выделить новую адресацию с маской %нов. маска IP-сети% вместо %ресурс на договоре%.',
                '- После смены реквизитов:',
                '- разобрать ресурс %ресурс на договоре% на договоре.'
            ]
            self.text_block.hidden_vars.update({i: i for i in strs})
            self.text_block.static_vars['нов. маска IP-сети'] = '/32'
            self.text_block.static_vars['ресурс на договоре'] = ' '.join(dhcp)

    def fill_mko(self):
        """Метод добавляет переменные, связанные с МКО."""
        strs = [
            'МКО:',
            '- Проинформировать клиента о простое сервисов на время проведения работ.',
            '- Согласовать время проведение работ.'
        ]
        self.text_block.hidden_vars.update({i: i for i in strs})



class ReplaceCsw(Csw):
    """Класс замены клиентского коммутатора."""
    def __init__(self, value_vars, connect):
        super().__init__(value_vars, connect)
        self.change_log = self.params.get('change_log')
        self.old_model_csw = value_vars.get('old_model_csw')

    def fill_vars(self):
        """Метод, заполняющий шаблон ТР переменными."""
        super().fill_vars()
        replace_str = 'Замена и перевод на гигабит' if self.csw_1000 and self.change_log == 'меняется' else 'Замена'
        if self.csw_1000:
            readable_pps = self.pps
        else:
            readable_pps = self.old_pps
            # для случая чтобы подставилось название ППС, когда в качестве УС выбран сам КК, а не как положено КАД

        self.text_block.static_vars.update({
            'узел связи': readable_pps,
            'Замена/Замена и перевод на гигабит': replace_str,
            'узел связи клиентского коммутатора': _readable_node(self.value_vars.get('node_csw')),
            'старая модель коммутатора': self.value_vars.get('old_model_csw'),
        })
        strs = [
            '- Линии связи клиента переключить "порт в порт".',
            '- Актуализировать информацию в ИС Cordis и системах учета.'
        ]
        self.text_block.hidden_vars.update({i:i for i in strs})

        self.text_block.static_vars.update({
            'название коммутатора': self.kad,
            'порт доступа на коммутаторе': self.port,
        })
        if self.port == self.old_port:
            if self.params.get('exist_sreda') in ['2', '4']:
                outdated_models = ('DIR-100', '3COM', 'Cisco')
                is_outdated = any(name in self.old_model_csw for name in outdated_models)
                if not is_outdated:
                    transmiter_str = '(передатчик задействовать из демонтированного коммутатора)'
                    self.text_block.hidden_vars[transmiter_str] = transmiter_str

    def get_filled_template(self):
        """Метод возвращающий заполненный шаблон ТР."""
        self.fill_vars()
        template = self.templates.get("%Замена/Замена и перевод на гигабит% клиентского коммутатора.")
        return self.text_block.construct(template)

class PassageCsw(Csw):
    """Класс переноса клиентского коммутатора."""
    def __init__(self, value_vars, connect):
        super().__init__(value_vars, connect)
        self.passage_csw = self.params.get('logic_change_csw')

    def fill_csw_connect(self):
        """Метод добавляет присоединение клиенского коммутатора со стороны клиента."""
        strs = [
            '- Включить линию для клиента в порт %магистральный порт на клиентском коммутаторе% коммутатора %название коммутатора клиентского%.',
        ]
        self.text_block.hidden_vars.update({i: i for i in strs})
        if self.mount_type in ['2', '4']:
            if self.mount_type != self.exist_mount_type:
                device_client_str = '- В %название коммутатора клиентского% установить %тип конвертера/передатчика на стороне клиента%.'
                self.text_block.hidden_vars[device_client_str] = device_client_str

    def fill_vars(self):
        """Метод, заполняющий шаблон ТР переменными."""
        super().fill_vars()
        self.fill_csw_connect()
        if not self.value_vars.get('type_ticket') == 'ПТО':
            self.fill_mko()

        pass_gi_str1 = 'Перенос/Перевод на гигабит'
        pass_gi_str2 ='переносу/переводу на гигабит'
        pass_gi_str3 = 'перенесен в новую точку подключения/переведен на гигабит/переключен на узел'

        if self.change_gi_csw:
            strs = [
                '- Сменить %режим работы магистрального порта/магистральный порт% на клиентском коммутаторе %название коммутатора клиентского%.',
            ]
            self.text_block.hidden_vars.update({i: i for i in strs})
            if self.exist_mount_type in ['1', '3']:
                self.text_block.static_vars['режим работы магистрального порта/магистральный порт'] = 'магистральный порт'
            else:
                self.text_block.static_vars[
                    'режим работы магистрального порта/магистральный порт'] = 'режим работы магистрального порта'
                zap_str = '- Запросить ОНИТС СПД перенастроить режим работы магистрального порта на клиентском коммутаторе %название коммутатора клиентского%.'
                self.text_block.hidden_vars[zap_str] = zap_str
                if self.change_physic == 'не меняется' or self.change_log == 'не меняется':
                    put_str = '- Включить линию для клиента в порт %магистральный порт на клиентском коммутаторе% коммутатора %название коммутатора клиентского%.'
                    del self.text_block.hidden_vars[put_str]
            self.text_block.static_vars[pass_gi_str1] = 'Перевод на гигабит'
            self.text_block.static_vars[pass_gi_str3] = 'переведен на гигабит'
            self.text_block.static_vars[pass_gi_str2] = 'переводу на гигабит'

        if self.change_log == 'меняется':
            self.text_block.static_vars[pass_gi_str2] = 'переносу логического подключения'
            if not self.change_gi_csw:
                self.text_block.static_vars[pass_gi_str1] = 'Перенос логического подключения'
                self.text_block.static_vars[pass_gi_str3] = f'переключен на узел {self.pps}'
            else:
                self.text_block.static_vars[pass_gi_str1] = 'Перевод на гигабит'
                if self.pps == self.old_pps:
                    self.text_block.static_vars[pass_gi_str3] = f'переведен на гигабит'
                    self.text_block.static_vars[pass_gi_str2] = 'переводу на гигабит'
                else:
                    self.text_block.static_vars[pass_gi_str3] = f'переключен на узел {self.pps}, переведен на гигабит'

        if self.change_physic == 'меняется':
            strs = [
                '- Перенести в новое помещении клиента коммутатор %название коммутатора клиентского%.',
                '- Линии связи клиента переключить "порт в порт".'
            ]
            self.text_block.hidden_vars.update({i: i for i in strs})
            if self.change_gi_csw:
                self.text_block.static_vars[pass_gi_str3] = 'перенесен в новую точку подключения, переведен на гигабит'
                self.text_block.static_vars[pass_gi_str1] = 'Перенос и перевод на гигабит'
                self.text_block.static_vars[pass_gi_str2] = 'переводу на гигабит'
            else:
                self.text_block.static_vars[pass_gi_str3] = 'перенесен в новую точку подключения'
                self.text_block.static_vars[pass_gi_str1] = 'Перенос'
                self.text_block.static_vars[pass_gi_str2] = 'переносу'

        self.text_block.static_vars['название коммутатора клиентского'] = self.old_name_csw
        actual_str = '- Актуализировать информацию в ИС Cordis и системах учета.'
        self.text_block.hidden_vars[actual_str] = actual_str

    def get_filled_template(self):
        """Метод возвращающий заполненный шаблон ТР."""
        self.fill_vars()
        if self.old_port == self.port and self.change_csw:
            template = self.templates.get("Перенос клиентского коммутатора.")
        else:
            template = self.templates.get("%Перенос/Перевод на гигабит% клиентского коммутатора.")
        return self.text_block.construct(template)


class NewCsw(Csw):
    """Класс установки клиентского коммутатора."""
    def __init__(self, value_vars, connect):
        super().__init__(value_vars, connect)
        self.replace_str_device_client = ' в клиентский коммутатор'

    def fill_vars(self):
        """Метод, заполняющий шаблон ТР переменными."""
        super().fill_vars()
        if self.model_csw == 'D-Link DGS-1100-06/ME':
            dgs_str = '- Внимание! В случае отсутствия на складе модели коммутатор D-Link DGS-1100-06/ME использовать любую из перечисленных моделей: SNR-S2950-24G; ORION Alpha A26.'
            self.text_block.hidden_vars[dgs_str] = dgs_str
        if self.type_connect != 'Новое подключение':
            self.fill_mko()

    def get_filled_template(self):
        """Метод возвращающий заполненный шаблон ТР."""
        self.fill_vars()
        template = self.templates.get("Установка клиентского коммутатора.")
        csw_text = self.text_block.construct(template)
        return csw_text


class PassServiceL2L3(PassService):
    """Базовый класс для услуг ЦКС, порт ВЛС, порт ВМ, требующих переноса."""
    def __init__(self, value_vars, service, ortr):
        super().__init__(value_vars, service, ortr)
        self.service_name = None
        self.policer = None
        self.extend_speed = self.service_params.get('extend_speed')
        self.policer_str = None
        self.point_policer_str = None

    def fill_vars(self):
        """Метод, заполняющий шаблон ТР переменными."""
        self.get_service_data()
        self.text_block.hidden_vars[self.policer_str] = self.policer_str.replace('%название сервиса%', self.service_name)
        self.text_block.static_vars[self.point_policer_str] = self.policer
        if self.job == 'Расширение':
            strs = [
                '- Выполнить настройки на оборудовании для расширения полосы сервиса %указать сервис%[ на %пропускная способность%].',
                ' на %пропускная способность%',
            ]
            self.text_block.hidden_vars.update({i: i for i in strs})
            self.text_block.static_vars['пропускная способность'] = self.extend_speed
        super().fill_vars()


class PassServiceCks(PassServiceL2L3):
    """Класс переноса услуги ЦКС"""
    def __init__(self, value_vars, service, ortr):
        super().__init__(value_vars, service, ortr)
        self.service_name = 'ЦКС'
        self.policer = self.service_params.get('policer_cks')
        self.policer_str = '- Ограничить скорость и настроить маркировку трафика для ^сервиса^ %название сервиса% %L2. точка ограничения и маркировки трафика%.'
        self.point_policer_str = 'L2. точка ограничения и маркировки трафика'


class PassServicePortVk(PassServiceL2L3):
    """Класс переноса услуги порт ВЛС"""
    def __init__(self, value_vars, service, ortr):
        super().__init__(value_vars, service, ortr)
        self.service_name = 'Порт ВЛС'
        self.policer = self.service_params.get('policer_cks')
        self.policer_str = '- Ограничить скорость и настроить маркировку трафика для ^сервиса^ %название сервиса% %L2. точка ограничения и маркировки трафика%.'
        self.point_policer_str = 'L2. точка ограничения и маркировки трафика'


class PassServicePortVm(PassServiceL2L3):
    """Класс переноса услуги порт ВМ"""
    def __init__(self, value_vars, service, ortr):
        super().__init__(value_vars, service, ortr)
        self.service_name = 'Порт ВМ'
        self.policer = self.service_params.get('policer_vm')
        self.policer_str = '- Ограничить скорость и настроить маркировку трафика для ^сервиса^ %название сервиса% %L3. точка ограничения и маркировки трафика%.'
        self.point_policer_str = 'L3. точка ограничения и маркировки трафика'


class PassServiceITV(PassService):
    """Класс переноса услуги iTV"""
    def __init__(self, value_vars, service, ortr):
        super().__init__(value_vars, service, ortr)
        self.service_name = 'ЦТВ'

    def fill_vars(self):
        """Метод, заполняющий шаблон ТР переменными."""
        self.get_service_data()
        super().fill_vars()


class PassServiceHotspot(PassService):
    """Класс переноса услуги Хот-спот"""
    def __init__(self, value_vars, service, ortr):
        super().__init__(value_vars, service, ortr)
        self.service_name = 'Хот-Спот'

    def fill_vars(self):
        """Метод, заполняющий шаблон ТР переменными."""
        self.get_service_data()
        super().fill_vars()


s_objs = {
    'Интернет': PassServiceShpd,
    'bgp': PassServiceBgp,
    'ЦКС': PassServiceCks,
    'iTV': PassServiceITV,
    'Телефон': PassServicePhone,
    'Видеонаблюдение': PassServiceVideo,
    'Порт ВЛС': PassServicePortVk,
    'Порт ВМ': PassServicePortVm,
    'HotSpot': PassServiceHotspot,

    'Организация_Интернет': NewServiceShpd,
    'Организация_ЦКС': NewServiceCks,
    'Организация_Телефон': NewServicePhone,
    'Организация_iTV': NewServiceItv,
    'Организация_ЛВС': NewServiceLvs,
    'Организация_Видеонаблюдение': NewServiceVideo,
    'Организация_Порт ВЛС': NewServicePortVk,
    'Организация_Порт ВМ': NewServicePortVm,
    'Организация_HotSpot': HotSpot
}

mount_objs = {
    'ППМ': {'1': PpmMount},
    'Вектор': {'1': VectorMount},
    'РТК': {'ПМ': RtkMount, 'FVNO GPON': RtkMount, 'FVNO Медь': RtkMount, 'FVNO FTTH': RtkMount},
    'Комтехцентр': {'1': UtpKtcMount, '2': OpticKtcMount, '3': WiFiKtcMount, '4': OpticKtcMount}
}

jobs = {
    'Перенос': PhysicLogicPassJob,
    'Расширение': GigabitPassJob,
    'Восстановление': RecoveryJob,
    'Организация': OrganizationJob,
    'ПереносТелефон': PassPhoneJob,
    'ПереносВидеонаблюдение': PassVideoJob
}