from .utils import *
from .utils import _get_policer
from .utils import _readable_node
from .utils import _separate_services_and_subnet_dhcp

def construct_tr(value_vars):

    if value_vars.get('counter_line_services_initial'):
        counter_line_services = value_vars.get('counter_line_services_initial')
    else:
        counter_line_services = 0
    if value_vars.get('counter_line_phone'):
        counter_line_services += value_vars.get('counter_line_phone')
    if value_vars.get('counter_line_hotspot'):
        counter_line_services += value_vars.get('counter_line_hotspot')
    if value_vars.get('counter_line_itv'):
        counter_line_services += value_vars.get('counter_line_itv')
    value_vars.update({'counter_line_services': counter_line_services})
    if value_vars.get('result_services'):
        del value_vars['result_services']
    if value_vars.get('result_services_ots'):
        del value_vars['result_services_ots']


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
        for service in value_vars.get('services'):
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
        elif value_vars.get('type_change_node') == 'Изминение физ. точки ППС':
            result_services, value_vars = passage_pps_without_logic(value_vars)
        elif value_vars.get('type_change_node') == 'Изменение трассы ВОК':
            result_services, value_vars = passage_optic_line(value_vars)
        elif value_vars.get('type_change_node') == 'Изменение трассы клиентских линий':
            result_services, value_vars = passage_client_lines(value_vars)
        result_services_ots = None
    return result_services, result_services_ots, value_vars

from . import text

def _get_pm_vars(value_vars, service):
    add_hidden_vars = {}
    add_static_vars = {}
    stick_str = ''
    connected_service = None
    connected_services = {
        'Интернет': 'all_shpd_in_tr',
        'ЦКС': 'all_cks_in_tr',
        'Порт ВЛС': 'all_portvk_in_tr',
        'Порт ВМ': 'all_portvm_in_tr',
        'HotSpot': 'all_hotspot_in_tr'
    }
    templates = value_vars.get('templates')
    spp_service = [_ for _ in connected_services.keys() if service.startswith(_)]
    if spp_service:
        name_connected_var = connected_services.get(spp_service[0])
        connected_service = value_vars.get(name_connected_var, {}).get(service)
    if value_vars.get('spd') in ('ППМ', 'Вектор'):
        type_port = 'access'
        stick_str = templates.get("Организация услуги access'ом через FVNO стык с %название оператора%.")
        is_dhcp_service = [_ for  _ in ('Exist dhcp', 'Интернет, DHCP') if service.startswith(_)]
        if is_dhcp_service:
            add_hidden_vars[text.fvno_dhcp_access] = text.fvno_dhcp_access
        else:
            if service == 'Exist not dhcp':
                add_hidden_vars[text.fvno_not_dhcp_access] = text.fvno_not_dhcp_access  # т.к. не знаем, по-умолчанию берем access
            else:
                if connected_service:
                    type_port = connected_service.get('port_type')
                if type_port == 'access':
                    add_hidden_vars[text.fvno_not_dhcp_access] = text.fvno_not_dhcp_access
                elif type_port == 'trunk':
                    add_hidden_vars[text.fvno_not_dhcp_trunk] = text.fvno_not_dhcp_trunk
                    stick_str = templates.get("Организация услуги trunk'ом через FVNO стык с %название оператора%.")
        if value_vars.get('spd') == 'ППМ':
            add_static_vars['название оператора'] = 'ООО "Пред-последняя миля"'
        elif value_vars.get('spd') == 'Вектор':
            add_static_vars['название оператора'] = 'ООО "Вектор СБ"'
        add_static_vars['№ заявки СПП'] = value_vars.get('ticket_k')
        add_hidden_vars[' СПД'] = ' СПД %название оператора%'
        add_hidden_vars['от %название коммутатора%'] = 'через FVNO стык стороннего оператора'

    elif value_vars.get('spd') == 'РТК':
        if value_vars.get('rtk_form').get('type_pm') == 'ПМ':
            stick_str = templates.get("Организация услуги через L2-стык с Ростелеком.")
            add_hidden_vars['от %название коммутатора%'] = 'через последнюю милю стороннего оператора'
        else:
            stick_str = templates.get("Организация услуги access'ом через FVNO стык с Ростелеком.")
            add_hidden_vars['от %название коммутатора%'] = 'через FVNO стык стороннего оператора'
        add_static_vars['tag vlan'] = value_vars.get('rtk_form').get('vlan')
        add_static_vars['№ заявки СПП'] = value_vars.get('ticket_k')
        add_hidden_vars[' СПД'] = ' СПД Ростелеком'
        
    else:
        if connected_service:
            type_port = connected_service.get('port_type')
            if type_port == 'access':
                access_str = ", в порт подключения выдать vlan access"
                add_hidden_vars[access_str] = access_str
            elif type_port == 'trunk':
                trunk_str = ", в порт подключения выдать vlan tag'ом"
                add_hidden_vars[trunk_str] = trunk_str

        add_hidden_vars[' СПД'] = ' СПД'
        add_hidden_vars['от %название коммутатора%'] = 'от %название коммутатора%'

    if stick_str:
        add_hidden_vars['Организация услуги через стык'] = '\n'.join(stick_str.split('\n')[2:])
    return add_hidden_vars, add_static_vars

def _new_services(result_services, value_vars):
    """Данный метод формирует блоки ТТР организации новых сервисов"""
    result_services_ots = value_vars.get('result_services_ots')
    logic_csw = True if value_vars.get('logic_csw') or value_vars.get('logic_change_csw') or value_vars.get('logic_change_gi_csw') or value_vars.get('logic_replace_csw') else False
    services_plus_desc = value_vars.get('services_plus_desc')
    templates = value_vars.get('templates')
    sreda = value_vars.get('sreda')
    name_new_service = set()
    for service in services_plus_desc:
        if 'Интернет, DHCP' in service:
            name_new_service.add('ШПД в Интернет')
            if logic_csw == True:
                result_services.append(enviroment_csw(value_vars))
            else:
                pass
            static_vars = {}
            hidden_vars = {}
            stroka = templates.get("Организация услуги ШПД в интернет access'ом.")
            static_vars['маска IP-сети'] = '/32'
            add_hidden_vars, add_static_vars = _get_pm_vars(value_vars, service)
            static_vars.update(add_static_vars)
            hidden_vars.update(add_hidden_vars)
            result_services.append(analyzer_vars(stroka, static_vars, hidden_vars))
            all_shpd_in_tr = value_vars.get('all_shpd_in_tr')
            if all_shpd_in_tr.get(service) and all_shpd_in_tr.get(service)['router_shpd']:
                stroka = templates.get("Установка маршрутизатора")
                if sreda == '2' or sreda == '4':
                    static_vars['отдел ОИПМ / ОИПД'] = 'ОИПМ'
                else:
                    static_vars['отдел ОИПМ / ОИПД'] = 'ОИПД'
                result_services.append(analyzer_vars(stroka, static_vars, hidden_vars))
        elif 'Интернет, блок Адресов Сети Интернет' in service:
            name_new_service.add('ШПД в Интернет')
            if logic_csw == True:
                result_services.append(enviroment_csw(value_vars))
            static_vars = {}
            hidden_vars = {}
            if ('29' in service) or (' 8' in service):
                static_vars['маска IP-сети'] = '/29'
            elif ('28' in service) or ('16' in service):
                static_vars['маска IP-сети'] = '/28'
            else:
                static_vars['маска IP-сети'] = '/30'
            all_shpd_in_tr = value_vars.get('all_shpd_in_tr')
            add_hidden_vars, add_static_vars = _get_pm_vars(value_vars, service)
            static_vars.update(add_static_vars)
            hidden_vars.update(add_hidden_vars)
            if all_shpd_in_tr.get(service) and all_shpd_in_tr.get(service)['port_type'] == 'access':
                stroka = templates.get("Организация услуги ШПД в интернет access'ом.")
                result_services.append(analyzer_vars(stroka, static_vars, hidden_vars))
            elif all_shpd_in_tr.get(service) and all_shpd_in_tr.get(service)['port_type'] == 'trunk':
                stroka = templates.get("Организация услуги ШПД в интернет trunk'ом.")
                result_services.append(analyzer_vars(stroka, static_vars, hidden_vars))

            if all_shpd_in_tr.get(service) and all_shpd_in_tr.get(service)['router_shpd']:
                stroka = templates.get("Установка маршрутизатора")
                if sreda == '2' or sreda == '4':
                    static_vars['отдел ОИПМ / ОИПД'] = 'ОИПМ'
                else:
                    static_vars['отдел ОИПМ / ОИПД'] = 'ОИПД'
                result_services.append(analyzer_vars(stroka, static_vars, hidden_vars))
        elif 'iTV' in service:
            name_new_service.add('ЦТВ')
            static_vars = {}
            hidden_vars = {}
            type_itv = value_vars.get('type_itv')
            cnt_itv = value_vars.get('cnt_itv')
            if type_itv == 'vl':
                if logic_csw:
                    if value_vars.get('router_itv'):
                        result_services.append(enviroment_csw(value_vars))
                    else:
                        for i in range(int(cnt_itv)):
                            result_services.append(enviroment_csw(value_vars))

                if value_vars.get('router_itv'):
                    sreda = value_vars.get('sreda')
                    if sreda == '2' or sreda == '4':
                        static_vars['отдел ОИПМ / ОИПД'] = 'ОИПМ'
                    else:
                        static_vars['отдел ОИПМ / ОИПД'] = 'ОИПД'
                    stroka = templates.get("Установка маршрутизатора")
                    result_services.append(analyzer_vars(stroka, static_vars, hidden_vars))
                    static_vars['маска IP-сети'] = '/30'
                else:
                    if cnt_itv == 1:
                        static_vars['маска IP-сети'] = '/30'
                    elif 1 < cnt_itv < 6:
                        static_vars['маска IP-сети'] = '/29'
                stroka = templates.get("Организация услуги ЦТВ в отдельном vlan'е.")
                result_services.append(analyzer_vars(stroka, static_vars, hidden_vars))
            elif type_itv == 'novl':
                if value_vars.get('need_line_itv') is True:
                    static_vars['количество портов ЛВС'] = str(cnt_itv)
                    static_vars['отдел ОИПМ / ОИПД'] = 'ОИПД'
                    static_vars['оборудование клиента'] = '^приставок^'
                    hidden_vars[' для ЦТВ'] = ' для ЦТВ'
                    hidden_vars[
                        '- Организовать %количество портов ЛВС% {медную} {линию} связи от %оборудование клиента% до места установки маршрутизатора.'
                    ] = '- Организовать %количество портов ЛВС% {медную} {линию} связи от %оборудование клиента% до места установки маршрутизатора.'
                    stroka = templates.get('Организация СКС< для ЦТВ>< по ВОЛС> на %количество портов ЛВС% {порт}')
                    stroka = analyzer_vars(stroka, static_vars, hidden_vars)
                    counter_plur = cnt_itv
                    result_services.append(pluralizer_vars(stroka, counter_plur))
                for serv_inet in services_plus_desc:
                    if 'Интернет, блок Адресов Сети Интернет' in serv_inet:
                        stroka = templates.get("Организация услуги ЦТВ в vlan'е новой услуги ШПД в интернет.")
                        result_services.append(analyzer_vars(stroka, static_vars, hidden_vars))
            elif type_itv == 'novlexist':
                if value_vars.get('need_line_itv') is True:
                    static_vars['количество портов ЛВС'] = str(cnt_itv)
                    static_vars['отдел ОИПМ / ОИПД'] = 'ОИПД'
                    static_vars['оборудование клиента'] = '^приставок^'
                    hidden_vars[' для ЦТВ'] = ' для ЦТВ'
                    hidden_vars[
                        '- Организовать %количество портов ЛВС% {медную} {линию} связи от %оборудование клиента% до места установки маршрутизатора.'
                    ] = '- Организовать %количество портов ЛВС% {медную} {линию} связи от %оборудование клиента% до места установки маршрутизатора.'
                    stroka = templates.get('Организация СКС< для ЦТВ>< по ВОЛС> на %количество портов ЛВС% {порт}')
                    stroka = analyzer_vars(stroka, static_vars, hidden_vars)
                    counter_plur = cnt_itv
                    result_services.append(pluralizer_vars(stroka, counter_plur))

                if value_vars.get('selected_ono') and not value_vars.get('selected_ono')[0][-4].endswith('/32'):
                    stroka = templates.get("Организация услуги ЦТВ в vlan'е действующей услуги ШПД в интернет с простоем связи.")
                    result_services.append(analyzer_vars(stroka, static_vars, hidden_vars))

        elif 'ЦКС' in service:
            name_new_service.add('ЦКС')
            if logic_csw == True:
                result_services.append(enviroment_csw(value_vars))
            static_vars = {}
            hidden_vars = {}
            all_cks_in_tr = value_vars.get('all_cks_in_tr')
            if all_cks_in_tr.get(service):
                static_vars['адрес точки "A"'] = all_cks_in_tr.get(service)['pointA']
                static_vars['адрес точки "B"'] = all_cks_in_tr.get(service)['pointB']
                static_vars['L2. точка ограничения и маркировки трафика'] = all_cks_in_tr.get(service)['policer_cks']
                static_vars['пропускная способность'] = _get_policer(service)
                add_hidden_vars, add_static_vars = _get_pm_vars(value_vars, service)
                static_vars.update(add_static_vars)
                hidden_vars.update(add_hidden_vars)
                if all_cks_in_tr.get(service)['port_type'] in ('access', 'xconnect'):
                    if all_cks_in_tr.get(service)['port_type'] == 'xconnect':
                        xconnect_str = ", на портe подключения настроить xconnect"
                        hidden_vars[xconnect_str] = xconnect_str
                    stroka = templates.get("Организация услуги ЦКС Etherline access'ом.")
                    result_services.append(analyzer_vars(stroka, static_vars, hidden_vars))
                elif all_cks_in_tr.get(service)['port_type'] == 'trunk':
                    stroka = templates.get("Организация услуги ЦКС Etherline trunk'ом.")
                    result_services.append(analyzer_vars(stroka, static_vars, hidden_vars))
        elif 'Порт ВЛС' in service:
            name_new_service.add('Порт ВЛС')
            if logic_csw == True:
                result_services.append(enviroment_csw(value_vars))
            else:
                pass
            static_vars = {}
            hidden_vars = {}
            all_portvk_in_tr = value_vars.get('all_portvk_in_tr')
            if all_portvk_in_tr.get(service):
                if all_portvk_in_tr.get(service)['type_vk'] == 'Новая ВЛС':
                    stroka = templates.get("Организация услуги ВЛС.")
                    result_services.append(stroka)
                    static_vars['название ВЛС'] = 'Для ВЛС, организованной по решению выше,'
                else:
                    static_vars['название ВЛС'] = all_portvk_in_tr.get(service)['exist_vk']
                static_vars['пропускная способность'] = _get_policer(service)
                static_vars['L2. точка ограничения и маркировки трафика'] = all_portvk_in_tr.get(service)['policer_vk']
                add_hidden_vars, add_static_vars = _get_pm_vars(value_vars, service)
                static_vars.update(add_static_vars)
                hidden_vars.update(add_hidden_vars)
                if all_portvk_in_tr.get(service)['port_type'] in ('access', 'xconnect'):
                    if all_portvk_in_tr.get(service)['port_type'] == 'xconnect':
                        xconnect_str = ", на портe подключения настроить xconnect"
                        hidden_vars[xconnect_str] = xconnect_str
                    stroka = templates.get("Организация услуги порт ВЛС access'ом.")
                    result_services.append(analyzer_vars(stroka, static_vars, hidden_vars))
                elif all_portvk_in_tr.get(service)['port_type'] == 'trunk':
                    stroka = templates.get("Организация услуги порт ВЛC trunk'ом.")
                    result_services.append(analyzer_vars(stroka, static_vars, hidden_vars))
        elif 'Порт ВМ' in service:
            name_new_service.add('Порт ВМ')
            if logic_csw == True:
                result_services.append(enviroment_csw(value_vars))
            else:
                pass
            static_vars = {}
            hidden_vars = {}
            all_portvm_in_tr = value_vars.get('all_portvm_in_tr')
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

                add_hidden_vars, add_static_vars = _get_pm_vars(value_vars, service)
                static_vars.update(add_static_vars)
                hidden_vars.update(add_hidden_vars)
                if current_portvm.get('port_type') == 'access':
                    stroka = templates.get("Организация услуги порт ВМ access'ом.")
                    result_services.append(analyzer_vars(stroka, static_vars, hidden_vars))
                elif current_portvm.get('port_type') == 'trunk':
                    stroka = templates.get("Организация услуги порт ВМ trunk'ом.")
                    result_services.append(analyzer_vars(stroka, static_vars, hidden_vars))
        elif 'HotSpot' in service:
            name_new_service.add('Хот-Спот')
            static_vars = {}
            hidden_vars = {}
            all_hotspot_in_tr = value_vars.get('all_hotspot_in_tr')
            if all_hotspot_in_tr:
                current_hotspot = all_hotspot_in_tr.get(service)
                add_hidden_vars, add_static_vars = _get_pm_vars(value_vars, service)
                static_vars.update(add_static_vars)
                hidden_vars.update(add_hidden_vars)
                if current_hotspot.get('type_hotspot') == 'Хот-Спот Премиум +':
                    if logic_csw is True:
                        result_services.append(enviroment_csw(value_vars))
                    static_vars['количество клиентов Хот-Спот'] = current_hotspot.get('hotspot_users')

                    if current_hotspot.get('exist_hotspot_client') == True:
                        stroka = templates.get("Организация услуги Хот-Спот Премиум + для существующего клиента.")
                    else:
                        stroka = templates.get("Организация услуги Хот-Спот Премиум + для нового клиента.")
                    result_services.append(analyzer_vars(stroka, static_vars, hidden_vars))
                else:
                    if logic_csw is True:
                        for i in range(current_hotspot.get('hotspot_points')):
                            result_services.append(enviroment_csw(value_vars))
                        static_vars['название коммутатора'] = 'клиентского коммутатора'
                    else:
                        static_vars['название коммутатора'] = value_vars.get('kad')
                    if current_hotspot.get('exist_hotspot_client') is True:
                        hidden_vars[text.onits_creates_hotspot] = text.onits_creates_hotspot
                    else:
                        hidden_vars[text.mko_creates_hotspot] = text.mko_creates_hotspot
                    if current_hotspot.get('hotspot_local_wifi') is True and logic_csw:
                        stroka = templates.get("Организация услуги Хот-Спот Премиум c локальной сетью WiFi для сотрудников клиента.")
                    else:
                        if current_hotspot.get('type_hotspot') == 'Хот-Спот Премиум':
                            stroka = templates.get("Организация услуги Хот-Спот Премиум.")
                        else:
                            stroka = templates.get("Организация услуги Хот-Спот Стандарт.")
                    if sreda == '2' or sreda == '4':
                        static_vars['отдел ОИПМ / ОИПД'] = 'ОИПМ'
                    else:
                        static_vars['отдел ОИПМ / ОИПД'] = 'ОИПД'
                    static_vars['количество беспроводных станций доступа'] = current_hotspot.get('hotspot_points')

                    static_vars['количество клиентов Хот-Спот'] = current_hotspot.get('hotspot_users')

                    stroka = analyzer_vars(stroka, static_vars, hidden_vars)
                    regex_counter = 'беспроводных станций: (\d+)'
                    match_counter = re.search(regex_counter, stroka)
                    counter_plur = int(match_counter.group(1))
                    result_services.append(pluralizer_vars(stroka, counter_plur))
        elif 'Видеонаблюдение' in service:
            name_new_service.add('Видеонаблюдение')
            static_vars = {}
            hidden_vars = {}
            static_vars['модель камеры'] = value_vars.get('camera_model')
            if value_vars.get('voice') == True:
                static_vars['необходимость записи звука'] = 'требуется запись звука'
                hidden_vars[' и запись звука'] = ' и запись звука'
            else:
                static_vars['необходимость записи звука'] = 'запись звука не требуется'
            camera_number = value_vars.get('camera_number')
            if camera_number < 3:
                stroka = templates.get("Организация услуги Видеонаблюдение с использованием PoE-инжектора.")
                if sreda == '2' or sreda == '4':
                    static_vars['отдел ОИПМ / ОИПД'] = 'ОИПМ'
                else:
                    static_vars['отдел ОИПМ / ОИПД'] = 'ОИПД'
                static_vars['количество линий'] = str(camera_number)
                static_vars['количество камер'] = str(camera_number)
                static_vars['количество POE-инжекторов'] = str(camera_number)
                static_vars['порт доступа на маршрутизаторе'] = 'свободный'
                static_vars['глубина хранения записей с камеры'] = value_vars.get('deep_archive')
                static_vars['адрес установки камеры'] = value_vars.get('address')
                static_vars['место установки камеры 1'] = value_vars.get('camera_place_one')

                if camera_number == 2:
                    hidden_vars[
                        '-- %порт доступа на маршрутизаторе%: %адрес установки камеры%, Камера %место установки камеры 2%, %модель камеры%, %необходимость записи звука%.'] = '-- %порт доступа на маршрутизаторе%: %адрес установки камеры%, Камера %место установки камеры 2%, %модель камеры%, %необходимость записи звука%.'
                    hidden_vars[
                        '-- камеры %место установки камеры 2% глубину хранения архива %глубина хранения записей с камеры%[ и запись звука].'] = '-- камеры %место установки камеры 2% глубину хранения архива %глубина хранения записей с камеры%[ и запись звука].'
                    static_vars['место установки камеры 2'] = value_vars.get('camera_place_two')
                static_vars[
                    'модель PoE-инжектора'] = 'PoE-инжектор СКАТ PSE-PoE.220AC/15VA'
                stroka = analyzer_vars(stroka, static_vars, hidden_vars)
                counter_plur = camera_number
                result_services.append(pluralizer_vars(stroka, counter_plur))
            elif camera_number == 5 or camera_number == 9:
                stroka = templates.get(
                    "Организация услуги Видеонаблюдение с использованием POE-коммутатора и PoE-инжектора.")
                if sreda == '2' or sreda == '4':
                    static_vars['отдел ОИПМ / ОИПД'] = 'ОИПМ'
                else:
                    static_vars['отдел ОИПМ / ОИПД'] = 'ОИПД'
                static_vars['количество линий'] = str(camera_number - 1)
                static_vars['количество камер'] = str(camera_number)
                if camera_number == 5:
                    static_vars['портовая емкость коммутатора'] = '4'
                    static_vars['порт доступа на POE-коммутаторе'] = '5'
                    static_vars['номер камеры на схеме'] = '5'
                elif camera_number == 9:
                    static_vars['портовая емкость коммутатора'] = '8'
                    static_vars['порт доступа на POE-коммутаторе'] = '10'
                    static_vars['номер камеры на схеме'] = '9'
                static_vars['порт доступа на маршрутизаторе'] = 'свободный'
                static_vars['глубина хранения записей с камеры'] = value_vars.get('deep_archive')
                static_vars['адрес установки камеры'] = value_vars.get('address')
                multi_vars = {}
                multi_vars['Порт %номер камеры на схеме%: %адрес установки камеры%, Камера №%номер камеры на схеме%, %модель камеры%, %необходимость записи звука%;'] = []
                multi_vars['-- камеры №%номер камеры на схеме% глубину хранения архива %глубина хранения записей с камеры%< и запись звука>;'] = []
                counter = 1
                for i in range(camera_number - 1):
                    multi_vars[
                        'Порт %номер камеры на схеме%: %адрес установки камеры%, Камера №%номер камеры на схеме%, %модель камеры%, %необходимость записи звука%;'
                    ].append(f'Порт {counter}: %адрес установки камеры%, Камера №{counter}, %модель камеры%, %необходимость записи звука%;')
                    counter += 1
                counter = 1
                for i in range(camera_number):
                    multi_vars[
                        '-- камеры №%номер камеры на схеме% глубину хранения архива %глубина хранения записей с камеры%< и запись звука>;'
                    ].append(f'-- камеры №{counter} глубину хранения архива %глубина хранения записей с камеры%< и запись звука>;')
                    counter += 1

                static_vars[
                    'модель PoE-инжектора'] = 'PoE-инжектор СКАТ PSE-PoE.220AC/15VA'
                stroka = analyzer_vars(stroka, static_vars, hidden_vars, multi_vars)
                counter_plur = camera_number - 1
                result_services.append(pluralizer_vars(stroka, counter_plur))
            elif camera_number > 2 and camera_number < 17 and camera_number not in (5, 9):
                stroka = templates.get("Организация услуги Видеонаблюдение с использованием POE-коммутатора.")
                repr_str = """- Организовать %количество линий% {линию} от POE-коммутатора до видеокамер. Включить линии в свободные порты POE-коммутатора:
Порт %порт доступа на POE-коммутаторе%: %адрес установки камеры%, Камера №%номер камеры на схеме%, %модель камеры%, %необходимость записи звука%;"""
                multi_vars = {}
                multi_vars[repr_str] = []
                multi_vars['-- камеры №%номер камеры на схеме% глубину хранения архива %глубина хранения записей с камеры%< и запись звука>;'] = []

                schema_poe = value_vars.get('schema_poe')
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

                multi_vars[str_count_poe] = []
                multi_vars[str_poe_uplink] = []
                for k,v in counter_same_poe.items():
                    multi_vars[str_count_poe].append(f"-- {k}-портовый POE-коммутатор - {v} шт.")
                    appended_str = "-- В порт 5 4-портового POE-коммутатора." if k == '4' else "-- В порт 10 8-портового POE-коммутатора."
                    multi_vars[str_poe_uplink].append(appended_str)

                text_schema = {
                    '4': '4-портовый',
                    '4+4': '4-портовые',
                    '4+8': '4-портовый и 8-портовый',
                    '8': '8-портовый',
                    '8+4': '8-портовый и 4-портовый',
                    '8+8': '8-портовые',
                }

                static_vars["схема POE-коммутаторов"] = text_schema[schema_poe]
                static_vars['глубина хранения записей с камеры'] = value_vars.get('deep_archive')
                static_vars['адрес установки камеры'] = value_vars.get('address')
                static_vars['количество камер'] = str(camera_number)
                if sreda == '2' or sreda == '4':
                    static_vars['отдел ОИПМ / ОИПД'] = 'ОИПМ'
                else:
                    static_vars['отдел ОИПМ / ОИПД'] = 'ОИПД'

                counter_camera = 1
                counter_port = 1
                poe_1_cameras = value_vars.get('poe_1_cameras')
                poe_2_cameras = value_vars.get('poe_2_cameras')
                lines_poe = [poe_1_cameras, poe_2_cameras]
                for j in range(count_poe):
                    plured_str = pluralizer_vars("- Организовать %количество линий% {линию} от POE-коммутатора до видеокамер. Включить линии в свободные порты POE-коммутатора:", lines_poe[j])
                    appended_str = plured_str.replace("%количество линий%", str(lines_poe[j]))
                    multi_vars[repr_str].append(appended_str)

                    for i in range(lines_poe[j]):
                        multi_vars[repr_str].append(f'Порт {counter_port}: %адрес установки камеры%, Камера №{counter_camera}, %модель камеры%, %необходимость записи звука%;')
                        counter_camera += 1
                        counter_port += 1
                    counter_port = 1

                counter = 1
                for i in range(camera_number):
                    multi_vars[
                        '-- камеры №%номер камеры на схеме% глубину хранения архива %глубина хранения записей с камеры%< и запись звука>;'
                    ].append(f'-- камеры №{counter} глубину хранения архива %глубина хранения записей с камеры%< и запись звука>;')
                    counter += 1
                stroka = analyzer_vars(stroka, static_vars, hidden_vars, multi_vars)
                counter_plur = count_poe
                if number_ports_poe_2:
                    is_correct_poe_1 = poe_1_cameras <= int(number_ports_poe_1)
                    is_correct_poe_2 = poe_2_cameras <= int(number_ports_poe_2)
                    is_correct_cameras = poe_1_cameras + poe_2_cameras == camera_number
                    is_correct_schema_poe = is_correct_poe_1 and is_correct_poe_2 and is_correct_cameras
                else:
                    is_correct_schema_poe = camera_number <= int(number_ports_poe_1)
                if is_correct_schema_poe:
                    result_services.append(pluralizer_vars(stroka, counter_plur))
        elif 'Телефон' in service:
            name_new_service.add('Телефония')

            result_services_ots = []
            hidden_vars = {}
            static_vars = {}
            vgw = value_vars.get('vgw')
            ports_vgw = value_vars.get('ports_vgw')
            phone_lines = sum([int(k) * v for k, v in value_vars.get('channels').items()])
            vats = True if 'ватс' in service.lower() else False
            phone_channels_string = construct_phone_channels_string(value_vars, vats)
            static_vars['тел. номер'] = ", ".join(phone_channels_string)
            if service.endswith('|'):
                if value_vars.get('type_phone') == 'st':
                    if logic_csw == True:
                        result_services.append(enviroment_csw(value_vars))
                    stroka = templates.get("Подключения по цифровой линии с использованием протокола SIP, тип линии «IP-транк».")
                    static_vars['способ организации проектируемого сервиса'] = "trunk'ом" if value_vars.get('type_ip_trunk') == 'trunk' else "access'ом"
                    result_services.append(analyzer_vars(stroka, static_vars, hidden_vars))
                elif value_vars.get('type_phone') == 'ak':
                    if logic_csw == True:
                        result_services.append(enviroment_csw(value_vars))
                        static_vars[
                            'название коммутатора'] = 'клиентского коммутатора'
                    elif logic_csw == False:
                        static_vars['название коммутатора'] = value_vars.get(
                            'kad')
                    stroka = templates.get("Установка тел. шлюза на стороне клиента.")
                    static_vars['модель тел. шлюза'] = vgw
                    if vgw in ['D-Link DVG-5402SP', 'Eltex RG-1404G или Eltex TAU-4M.IP', 'Eltex TAU-8.IP']:
                        static_vars['магистральный порт на тел. шлюзе'] = 'WAN порт'
                    else:
                        static_vars['магистральный порт на тел. шлюзе'] = 'Ethernet Порт 0'
                        static_vars['модель тел. шлюза'] = vgw + ' c кабелем для коммутации в плинт'
                    result_services_ots.append(analyzer_vars(stroka, static_vars, hidden_vars))
                    if 'ватс' in service.lower():
                        stroka = templates.get("ВАТС (аналоговая линия).")
                        static_vars['название тел. шлюза'] = 'установленный по решению выше'
                        static_vars['модель тел. шлюза'] = vgw
                        static_vars['количество внутренних портов ВАТС'] = ports_vgw
                        if 'базов' in service.lower():
                            static_vars[
                                'набор сервисов ВАТС'] = 'базовым набором сервисов'
                        elif 'расш' in service.lower():
                            static_vars[
                                'набор сервисов ВАТС'] = 'расширенным набором сервисов'

                        static_vars['количество линий'] = ports_vgw
                        if ports_vgw == '1':
                            static_vars['порт доступа на тел. шлюзе'] = '1'
                        else:
                            static_vars['порт доступа на тел. шлюзе'] = '1-{}'.format(ports_vgw)
                        stroka = analyzer_vars(stroka, static_vars, hidden_vars)
                        counter_plur = int(ports_vgw)
                        result_services_ots.append(pluralizer_vars(stroka, counter_plur))
                    else:
                        stroka = templates.get(
                            "Подключение аналогового телефона с использованием тел. шлюза на стороне клиента.")
                        static_vars['модель тел. шлюза'] = vgw
                        static_vars['количество линий'] = str(phone_lines)
                        if phone_lines == 1:
                            static_vars['порт доступа на тел. шлюзе'] = '1'
                        else:
                            static_vars['порт доступа на тел. шлюзе'] = '1-{}'.format(phone_lines)
                        stroka = analyzer_vars(stroka, static_vars, hidden_vars)
                        counter_plur = phone_lines
                        result_services_ots.append(pluralizer_vars(stroka, counter_plur))
            elif service.endswith('/'):
                stroka = templates.get("Установка тел. шлюза на ППС.")
                static_vars['модель тел. шлюза'] = vgw
                static_vars['узел связи'] = value_vars.get('pps')
                result_services_ots.append(analyzer_vars(stroka, static_vars, hidden_vars))
                if 'ватс' in service.lower():
                    stroka = templates.get("ВАТС (аналоговая линия).")
                    if 'базов' in service.lower():
                        static_vars[
                            'набор сервисов ВАТС'] = 'базовым набором сервисов'
                    elif 'расш' in service.lower():
                        static_vars[
                            'набор сервисов ВАТС'] = 'расширенным набором сервисов'
                    static_vars['название тел. шлюза'] = 'установленный по решению выше'

                    static_vars['количество линий'] = ports_vgw
                    static_vars['количество внутренних портов ВАТС'] = ports_vgw
                    if ports_vgw == '1':
                        static_vars['порт доступа на тел. шлюзе'] = '1'
                    else:
                        static_vars['порт доступа на тел. шлюзе'] = '1-{}'.format(ports_vgw)
                    stroka = analyzer_vars(stroka, static_vars, hidden_vars)
                    counter_plur = int(ports_vgw)
                    result_services_ots.append(pluralizer_vars(stroka, counter_plur))
                else:
                    stroka = templates.get("Подключение аналогового телефона с использованием тел. шлюза на ППС.")
                    static_vars['название тел. шлюза'] = 'установленного по решению выше'
                    static_vars['количество линий'] = str(phone_lines)
                    if phone_lines == 1:
                        static_vars['порт доступа на тел. шлюзе'] = '1'
                    else:
                        static_vars['порт доступа на тел. шлюзе'] = '1-{}'.format(phone_lines)
                    stroka = analyzer_vars(stroka, static_vars, hidden_vars)
                    counter_plur = phone_lines
                    result_services_ots.append(pluralizer_vars(stroka, counter_plur))
            elif service.endswith('\\'):
                static_vars['порт доступа на тел. шлюзе'] = value_vars.get('form_exist_vgw_port')
                static_vars['модель тел. шлюза'] = value_vars.get('form_exist_vgw_model')
                static_vars['название тел. шлюза'] = value_vars.get('form_exist_vgw_name')
                if 'ватс' in service.lower():
                    stroka = templates.get("ВАТС (аналоговая линия).")
                    if 'базов' in service.lower():
                        static_vars[
                            'набор сервисов ВАТС'] = 'базовым набором сервисов'
                    elif 'расш' in service.lower():
                        static_vars[
                            'набор сервисов ВАТС'] = 'расширенным набором сервисов'

                    static_vars['количество линий'] = ports_vgw
                    static_vars['количество внутренних портов ВАТС'] = ports_vgw
                    stroka = analyzer_vars(stroka, static_vars, hidden_vars)
                    counter_plur = int(ports_vgw)
                    result_services_ots.append(pluralizer_vars(stroka, counter_plur))
                else:
                    stroka = templates.get("Подключение аналогового телефона с использованием тел. шлюза на ППС.")
                    static_vars['узел связи'] = value_vars.get('pps')
                    static_vars['количество линий'] = str(phone_lines)
                    stroka = analyzer_vars(stroka, static_vars, hidden_vars)
                    counter_plur = int(phone_lines)
                    result_services_ots.append(pluralizer_vars(stroka, counter_plur))
            else:
                if 'ватс' in service.lower():
                    if 'базов' in service.lower():
                        stroka = templates.get("ВАТС Базовая(SIP регистрация через Интернет).")
                        result_services_ots.append(analyzer_vars(stroka, static_vars, hidden_vars))
                    elif 'расш' in service.lower():
                        stroka = templates.get("ВАТС Расширенная(SIP регистрация через Интернет).")
                        static_vars['количество внутренних портов ВАТС'] = ports_vgw
                        stroka = analyzer_vars(stroka, static_vars, hidden_vars)
                        result_services_ots.append(pluralizer_vars(stroka, int(ports_vgw)))
                else:
                    stroka = templates.get(
                        "Подключения по цифровой линии с использованием протокола SIP, тип линии «SIP регистрация через Интернет».")
                    result_services_ots.append(analyzer_vars(stroka, static_vars, hidden_vars))
        elif 'ЛВС' in service:
            name_new_service.add('ЛВС')
            static_vars = {}
            hidden_vars = {}
            local_ports = value_vars.get('local_ports')
            static_vars['количество портов ЛВС'] = str(local_ports)
            if value_vars.get('local_type') in ('sks_standart', 'sks_business'):
                stroka = templates.get("Организация СКС< для ЦТВ>< по ВОЛС> на %количество портов ЛВС% {порт}")
                static_vars['отдел ОИПМ / ОИПД'] = 'ОИПД'
                if value_vars.get('decision_otpm'):
                    hidden_vars[' согласно решению ОТПМ'] = ' согласно решению ОТПМ'
                if value_vars.get('sks_router'):
                    hidden_vars[
                        '- Организовать %количество портов ЛВС% {медную} {линию} связи от %оборудование клиента% до места установки маршрутизатора.'
                    ] = '- Организовать %количество портов ЛВС% {медную} {линию} связи от %оборудование клиента% до места установки маршрутизатора.'
                    static_vars['оборудование клиента'] = 'оборудование клиента'
                if value_vars.get('local_socket'):
                    hidden_vars[' и розеток'] = ' и {розеток}'
                static_vars['указать количество'] = str(local_ports)
                stroka = analyzer_vars(stroka, static_vars, hidden_vars)
                counter_plur = local_ports
                result_services.append(pluralizer_vars(stroka, counter_plur))
            elif value_vars.get('local_type') == 'sks_vols':
                stroka = templates.get("Организация СКС< для ЦТВ>< по ВОЛС> на %количество портов ЛВС% {порт}")
                if value_vars.get('decision_otpm'):
                    hidden_vars[' согласно решению ОТПМ'] = ' согласно решению ОТПМ'
                if value_vars.get('sks_router'):
                    hidden_vars[
                        '- Организовать %количество портов ЛВС% {медную} {линию} связи от %оборудование клиента% до места установки маршрутизатора.'
                    ] = '- Организовать %количество портов ЛВС% ВОЛС от %оборудование клиента% до места установки маршрутизатора.'
                    static_vars['оборудование клиента'] = 'оборудование клиента'
                hidden_vars[' по ВОЛС'] = ' по ВОЛС'
                hidden_vars['%отдел ОИПМ / ОИПД% подготовиться к работам:'] = '%отдел ОИПМ / ОИПД% подготовиться к работам:'
                hidden_vars['- Получить на складе территории:'] = '- Получить на складе территории:'
                hidden_vars['-- %тип конвертера А% - %количество портов ЛВС% шт.'] = '-- %тип конвертера А% - %количество портов ЛВС% шт.'
                hidden_vars['-- %тип конвертера Б% - %количество портов ЛВС% шт.'] = '-- %тип конвертера Б% - %количество портов ЛВС% шт.'
                hidden_vars[
                    '- Установить %тип конвертера А% и %тип конвертера Б%.[ Выставить на конвертерах режим работы "auto".]'
                ] = '- Установить %тип конвертера А% и %тип конвертера Б%.[ Выставить на конвертерах режим работы "auto".]'
                static_vars['отдел ОИПМ / ОИПД'] = 'ОИПМ'
                if value_vars.get('sks_transceiver') == 'Конвертеры 100':
                    static_vars['тип конвертера А'] = '100 Мбит/с ^конвертер^ с длиной волны 1310 нм, дальность до 20 км'
                    static_vars['тип конвертера Б'] = '100 Мбит/с ^конвертер^ с длиной волны 1550 нм, дальность до 20 км'
                    hidden_vars[' Выставить на конвертерах режим работы "auto".'] = ' Выставить на конвертерах режим работы "auto".'
                elif value_vars.get('sks_transceiver') == 'Конвертеры 1000':
                    static_vars['тип конвертера А'] = '1000 Мбит/с ^конвертер^ с модулем SFP WDM с длиной волны 1310 нм, дальность до 20 км'
                    static_vars['тип конвертера Б'] = '1000 Мбит/с ^конвертер^ с модулем SFP WDM с длиной волны 1550 нм, дальность до 20 км'
                    hidden_vars[' Выставить на конвертерах режим работы "auto".'] = ' Выставить на конвертерах режим работы "auto".'
                elif value_vars.get('sks_transceiver') == 'SFP':
                    static_vars['тип конвертера А'] = '^оптический^ ^модуль^ SFP WDM с длиной волны 1310 нм, дальность до 20 км'
                    static_vars['тип конвертера Б'] = '^оптический^ ^модуль^ SFP WDM с длиной волны 1550 нм, дальность до 20 км'
                static_vars['указать количество'] = str(local_ports)
                stroka = analyzer_vars(stroka, static_vars, hidden_vars)
                counter_plur = local_ports
                result_services.append(pluralizer_vars(stroka, counter_plur))
            elif value_vars.get('local_type') in ('lvs_standart', 'lvs_business'):
                stroka = templates.get("Организация ЛВС на %количество портов ЛВС% {порт}")
                if value_vars.get('local_socket'):
                    hidden_vars[' и розеток'] = ' и {розеток}'
                if value_vars.get('lvs_busy') is True:
                    hidden_vars[
                        'МКО:\n- В связи с тем, что у клиента все порты на маршрутизаторе заняты необходимо с клиентом согласовать перерыв связи по одному из подключенных устройств к маршрутизатору.\nВо время проведения работ данная линия будет переключена из маршрутизатора клиента в проектируемый коммутатор.'] = 'МКО:\n- В связи с тем, что у клиента все порты на маршрутизаторе заняты необходимо с клиентом согласовать перерыв связи по одному из подключенных устройств к маршрутизатору.\nВо время проведения работ данная линия будет переключена из маршрутизатора клиента в проектируемый коммутатор.\n'
                    hidden_vars[
                        '- По согласованию с клиентом высвободить LAN-порт на маршрутизаторе клиента переключив сущ. линию для ЛВС клиента из маршрутизатора клиента в свободный порт установленного коммутатора.'] = '- По согласованию с клиентом высвободить LAN-порт на маршрутизаторе клиента переключив сущ. линию для ЛВС клиента из маршрутизатора клиента в свободный порт установленного коммутатора.'
                    hidden_vars[
                        '- Подтвердить восстановление связи для порта ЛВС который был переключен в установленный коммутатор.'] = '- Подтвердить восстановление связи для порта ЛВС который был переключен в установленный коммутатор.'
                lvs_switch = value_vars.get('lvs_switch')
                static_vars['модель коммутатора'] = lvs_switch
                if lvs_switch in ['TP-Link TL-SG105 V4', 'ZYXEL GS1200-5', 'Origo OS2205/А2A']:
                    static_vars['портовая емкость коммутатора'] = '5'
                elif lvs_switch in ['TP-Link TL-SG108 V4', 'ZYXEL GS1200-8', 'Cudy GS108']:
                    static_vars['портовая емкость коммутатора'] = '8'
                elif lvs_switch == 'D-link DGS-1100-16/B':
                    static_vars['портовая емкость коммутатора'] = '16'
                elif lvs_switch == 'D-link DGS-1100-24/B':
                    static_vars['портовая емкость коммутатора'] = '24'
                stroka = analyzer_vars(stroka, static_vars, hidden_vars)
                counter_plur = int(local_ports)
                result_services.append(pluralizer_vars(stroka, counter_plur))
    value_vars.update({'name_new_service': name_new_service})
    return result_services, result_services_ots, value_vars


def enviroment_csw(value_vars):
    """Данный метод формирует блок ТТР организации медной линии от КК"""
    sreda = value_vars.get('sreda')
    templates = value_vars.get('templates')
    static_vars = {}
    hidden_vars = {}
    stroka = templates.get("Присоединение к СПД по медной линии связи.")
    static_vars['узел связи'] = 'клиентского коммутатора'
    if value_vars.get('logic_csw'):
        static_vars['название коммутатора'] = 'установленный по решению выше'
    else:
        static_vars['название коммутатора'] = value_vars.get('selected_ono')[0][-2]
    static_vars['порт доступа на коммутаторе'] = 'свободный'
    if sreda == '2' or sreda == '4':
        static_vars['отдел ОИПМ / ОИПД'] = 'ОИПМ'
    else:
        static_vars['отдел ОИПМ / ОИПД'] = 'ОИПД'
    return analyzer_vars(stroka, static_vars, hidden_vars)


def vector_enviroment(value_vars):
    if value_vars.get('result_services'):
        result_services = value_vars.get('result_services')
    else:
        result_services = []
    templates = value_vars.get('templates')
    static_vars = {}
    hidden_vars = {}
    stroka = templates.get('Присоединение к СПД по медной линии связи по схеме "ООО "Вектор СБ". Прямой FVNO".')
    result_services.append(analyzer_vars(stroka, static_vars, hidden_vars))
    value_vars.update({'kad': 'AR137-02.ekb', 'pps': 'ЕКБ Луганская 4 П1 Э-1 (паркинг(бокс 114-117)), РУА'})
    return result_services, value_vars


def ppm_enviroment(value_vars):
    if value_vars.get('result_services'):
        result_services = value_vars.get('result_services')
    else:
        result_services = []
    templates = value_vars.get('templates')
    static_vars = {}
    hidden_vars = {}
    stroka = templates.get('Присоединение к СПД по медной линии связи по схеме "ООО "Пред-последняя миля". Прямой FVNO".')
    result_services.append(analyzer_vars(stroka, static_vars, hidden_vars))
    value_vars.update({'kad': 'AR03-25.ekb', 'pps': 'ЕКБ Чкалова 135/а П1 Э1 (пристрой), РУА'})
    return result_services, value_vars

def rtk_enviroment(value_vars):
    if value_vars.get('result_services'):
        result_services = value_vars.get('result_services')
    else:
        result_services = []
    templates = value_vars.get('templates')
    static_vars = {}
    hidden_vars = {}
    if value_vars.get('rtk_form').get('type_pm') == 'ПМ':
        static_vars['название оператора'] = 'Ростелеком'
        static_vars['узел связи'] = 'РУА ЕКБ Автоматики переулок 1 стр.В3 П1 Э2 (аппаратная)'
        static_vars['название коммутатора'] = 'AR113-37.ekb'
        static_vars['порт доступа на коммутаторе'] = 'Po4'
        stroka = templates.get("Присоединение к СПД через последнюю милю стороннего оператора %название оператора%.")
    elif value_vars.get('rtk_form').get('type_pm') == 'FVNO Медь':
        static_vars['IP коммутатора'] = value_vars.get('rtk_form').get('switch_ip')
        static_vars['порт доступа на коммутаторе'] = value_vars.get('rtk_form').get('switch_port')
        stroka = templates.get('Присоединение к СПД по медной линии связи по схеме "Ростелеком. Прямой FVNO".')
    elif value_vars.get('rtk_form').get('type_pm') == 'FVNO GPON':
        static_vars['IP коммутатора'] = value_vars.get('rtk_form').get('switch_ip')
        static_vars['порт доступа на коммутаторе'] = value_vars.get('rtk_form').get('switch_port')
        static_vars['PLOAM-пароль'] = value_vars.get('rtk_form').get('ploam')
        stroka = templates.get('Присоединение к СПД по оптической линии связи (GPON) по схеме "Ростелеком. Прямой FVNO". ONT в качестве "конвертера".')
    elif value_vars.get('rtk_form').get('type_pm') == 'FVNO FTTH':
        static_vars['IP коммутатора'] = value_vars.get('rtk_form').get('switch_ip')
        static_vars['порт доступа на коммутаторе'] = value_vars.get('rtk_form').get('switch_port')
        if value_vars.get('rtk_form').get('optic_socket'):
            hidden_vars['кросса Ростелеком, ОР %номер ОР%'] = 'кросса Ростелеком, ОР %номер ОР%'
            static_vars['номер ОР'] = value_vars.get('rtk_form').get('optic_socket')
        else:
            hidden_vars['коммутатора Ростелеком %IP коммутатора%, порт %порт доступа на коммутаторе%'] = \
                'коммутатора Ростелеком %IP коммутатора%, порт %порт доступа на коммутаторе%'
        if value_vars.get('msan_exist'):
            hidden_vars['ОИПМ подготовиться к работам:'] = 'ОИПМ подготовиться к работам:'
            hidden_vars['- Для проведения работ на стороне клиента подготовить комплект оборудования:'] = \
                '- Для проведения работ на стороне клиента подготовить комплект оборудования:'
            hidden_vars['-- Конвертер SNR-CVT-1000SFP mini с модулем SFP WDM, дальность до 20км (14dB), 1310 нм;'] = \
                '-- Конвертер SNR-CVT-1000SFP mini с модулем SFP WDM, дальность до 20км (14dB), 1310 нм;'
            hidden_vars['-- Конвертер "A" 100 Мбит/с, дальность до 20км (14dB), 1310 нм.'] = \
                '-- Конвертер "A" 100 Мбит/с, дальность до 20км (14dB), 1310 нм.'
            hidden_vars['- Установить на стороне клиента конвертер "A" 100 Мбит/с, дальность до 20км (14dB), 1310 нм, выставить на конвертере режим работы Auto.'] = \
            '- Установить на стороне клиента конвертер "A" 100 Мбит/с, дальность до 20км (14dB), 1310 нм, выставить на конвертере режим работы Auto.'
            hidden_vars['Внимание! В случае если линк не поднялся использовать конвертер SNR-CVT-1000SFP mini с модулем SFP WDM, дальность до 20км (14dB), 1310 нм.'] = \
            'Внимание! В случае если линк не поднялся использовать конвертер SNR-CVT-1000SFP mini с модулем SFP WDM, дальность до 20км (14dB), 1310 нм.'
        else:
            hidden_vars['- Установить на стороне клиента конвертер SNR-CVT-1000SFP mini с модулем SFP WDM, дальность до 20км (14dB), 1550 нм;'] = \
            '- Установить на стороне клиента конвертер SNR-CVT-1000SFP mini с модулем SFP WDM, дальность до 20км (14dB), 1550 нм;'
        stroka = templates.get('Присоединение к СПД по оптической линии связи (FTTH) по схеме "Ростелеком. Прямой FVNO".')
    result_services.append(analyzer_vars(stroka, static_vars, hidden_vars))
    value_vars.update({'kad': 'AR113-37.ekb', 'pps': 'ЕКБ Автоматики переулок 1 стр.В3 П1 Э2 (аппаратная), РУА'})
    return result_services, value_vars

def _new_enviroment(value_vars):
    """Данный метод проверяет необходимость установки КК для новой точки подключения, если такая необходимость есть,
     формирует блок ТТР установки КК, если нет - перенаправляет на метод, который формирует блок ТТР отдельной линии"""
    if value_vars.get('result_services'):
        result_services = value_vars.get('result_services')
    else:
        result_services = []
    counter_line_services = value_vars.get('counter_line_services')
    if counter_line_services > 0:
        kad = value_vars.get('kad')
        readable_pps = _readable_node(value_vars.get('pps'))
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
            static_vars['магистральный порт на клиентском коммутаторе'] = value_vars.get('port_csw')
            static_vars['модель коммутатора'] = value_vars.get('model_csw')
            if value_vars.get('model_csw') == 'D-Link DGS-1100-06/ME':
                hidden_vars['- Внимание! В случае отсутствия на складе модели коммутатор D-Link DGS-1100-06/ME использовать любую из перечисленных моделей: SNR-S2950-24G; ORION Alpha A26.'] = '- Внимание! В случае отсутствия на складе модели коммутатор D-Link DGS-1100-06/ME использовать любую из перечисленных моделей: SNR-S2950-24G; ORION Alpha A26.'
            static_vars['узел связи'] = readable_pps
            static_vars['название коммутатора'] = kad
            static_vars['порт доступа на коммутаторе'] = value_vars.get('port')
            hidden_vars[
                '- Организовать %тип линии связи% от %узел связи% до клиентcкого коммутатора по решению ОАТТР.'] = '- Организовать %тип линии связи% от %узел связи% до клиентcкого коммутатора по решению ОАТТР.'
            hidden_vars['- Подключить организованную линию для клиента в коммутатор %название коммутатора%, порт задействовать %порт доступа на коммутаторе%.'] = '- Подключить организованную линию для клиента в коммутатор %название коммутатора%, порт задействовать %порт доступа на коммутаторе%.'
            logic_csw_1000 = value_vars.get('logic_csw_1000')
            if logic_csw_1000 == True:
                static_vars['пропускная способность'] = '1000 Мбит/с'
            else:
                static_vars['пропускная способность'] = '100 Мбит/с'
            templates = value_vars.get('templates')
            if value_vars.get('type_install_csw'):
                pass
            else:
                sreda = value_vars.get('sreda')
                stroka = templates.get("Установка клиентского коммутатора.")
                if sreda == '1':
                    static_vars['отдел ОИПМ / ОИПД'] = 'ОИПД'
                    static_vars['тип линии связи'] = 'медную линию связи'
                    result_services.append(analyzer_vars(stroka, static_vars, hidden_vars))
                elif sreda == '2' or sreda == '4':
                    if value_vars.get('ppr'):
                        hidden_vars[
                            '- Требуется отключение согласно списку отключений в ППР %№ заявки ППР% согласовать проведение работ.'] = '- Требуется отключение согласно списку отключений в ППР %№ заявки ППР% согласовать проведение работ.'
                        hidden_vars[
                            '- Совместно с ОНИТС СПД убедиться в восстановлении связи согласно списку отключений в ППР %№ заявки ППР%.'] = '- Совместно с ОНИТС СПД убедиться в восстановлении связи согласно списку отключений в ППР %№ заявки ППР%.'
                        hidden_vars[
                            '- После проведения монтажных работ убедиться в восстановлении услуг согласно списку отключений в ППР %№ заявки ППР%.'] = '- После проведения монтажных работ убедиться в восстановлении услуг согласно списку отключений в ППР %№ заявки ППР%.'
                        static_vars['№ заявки ППР'] = value_vars.get('ppr')
                    static_vars['отдел ОИПМ / ОИПД'] = 'ОИПМ'
                    static_vars['тип линии связи'] = 'ВОЛС'
                    hidden_vars[
                        '- Установить на стороне %узел связи% %тип конвертера/передатчика на стороне узла доступа%'] = '- Установить на стороне %узел связи% %тип конвертера/передатчика на стороне узла доступа%'
                    hidden_vars[
                        'и %тип конвертера/передатчика на стороне клиента%'] = 'и %тип конвертера/передатчика на стороне клиента%'
                    static_vars['тип конвертера/передатчика на стороне узла доступа'] = value_vars.get('device_pps')
                    static_vars['тип конвертера/передатчика на стороне клиента'] = value_vars.get('device_client')

                    if logic_csw_1000 == True and value_vars.get('model_csw') == 'D-Link DGS-1100-06/ME':
                        hidden_vars[
                            '-ВНИМАНИЕ! Совместно с ОНИТС СПД удаленно настроить клиентский коммутатор.'] = '-ВНИМАНИЕ! Совместно с ОНИТС СПД удаленно настроить клиентский коммутатор.'
                        hidden_vars[
                            '- Совместно с %отдел ОИПМ / ОИПД% удаленно настроить клиентский коммутатор.'] = '- Совместно с %отдел ОИПМ / ОИПД% удаленно настроить клиентский коммутатор.'
                    result_services.append(analyzer_vars(stroka, static_vars, hidden_vars))
                elif sreda == '3':
                    if value_vars.get('ppr'):
                        hidden_vars[
                            '- Требуется отключение согласно списку отключений в ППР %№ заявки ППР% согласовать проведение работ.'] = '- Требуется отключение согласно списку отключений в ППР %№ заявки ППР% согласовать проведение работ.'
                        hidden_vars[
                            '- Совместно с ОНИТС СПД убедиться в восстановлении связи согласно списку отключений в ППР %№ заявки ППР%.'] = '- Совместно с ОНИТС СПД убедиться в восстановлении связи согласно списку отключений в ППР %№ заявки ППР%.'
                        hidden_vars[
                            '- После проведения монтажных работ убедиться в восстановлении услуг согласно списку отключений в ППР %№ заявки ППР%.'] = '- После проведения монтажных работ убедиться в восстановлении услуг согласно списку отключений в ППР %№ заявки ППР%.'
                        static_vars['№ заявки ППР'] = value_vars.get('ppr')
                    static_vars['тип линии связи'] = 'медную линию связи'
                    static_vars['отдел ОИПМ / ОИПД'] = 'ОИПД'
                    static_vars['модель беспроводной базовой станции'] = value_vars.get('access_point')
                    hidden_vars[
                        '- Создать заявку в ИС Cordis на ОНИТС СПД для выделения реквизитов беспроводных точек доступа WDS/WDA.'] = '- Создать заявку в ИС Cordis на ОНИТС СПД для выделения реквизитов беспроводных точек доступа WDS/WDA.'
                    hidden_vars[
                        '- Установить на стороне %узел связи% и на стороне клиента беспроводные точки доступа %модель беспроводной базовой станции% по решению ОАТТР.'] = '- Установить на стороне %узел связи% и на стороне клиента беспроводные точки доступа %модель беспроводной базовой станции% по решению ОАТТР.'
                    hidden_vars[
                        '- По заявке в ИС Cordis выделить реквизиты для управления беспроводными точками.'] = '- По заявке в ИС Cordis выделить реквизиты для управления беспроводными точками.'
                    hidden_vars[
                        '- Совместно с ОИПД подключить к СПД и запустить беспроводные станции (WDS/WDA).'] = '- Совместно с ОИПД подключить к СПД и запустить беспроводные станции (WDS/WDA).'
                    if value_vars.get('access_point') == 'Infinet E5':
                        hidden_vars[
                            '- Доставить в офис ОНИТС СПД беспроводные точки Infinet E5 для их настройки.'] = '- Доставить в офис ОНИТС СПД беспроводные точки Infinet E5 для их настройки.'
                        hidden_vars[
                            'После выполнения подготовительных работ в рамках заявки в ИС Cordis на ОНИТС СПД и настройки точек в офисе ОНИТС СПД:'] = 'После выполнения подготовительных работ в рамках заявки в ИС Cordis на ОНИТС СПД и настройки точек в офисе ОНИТС СПД:'
                    else:
                        hidden_vars[
                            'После выполнения подготовительных работ в рамках заявки в ИС Cordis на ОНИТС СПД:'] = 'После выполнения подготовительных работ в рамках заявки в ИС Cordis на ОНИТС СПД:'
                    result_services.append(analyzer_vars(stroka, static_vars, hidden_vars))
    if not bool(value_vars.get('kad')):
        kad = 'Не требуется'
        value_vars.update({'kad': kad})
    return result_services, value_vars


def exist_enviroment_install_csw(value_vars):
    """Данный метод формирует блок ТТР установки КК для существующей точки подключения"""
    if value_vars.get('result_services'):
        result_services = value_vars.get('result_services')
    else:
        result_services = []
    static_vars = {}
    hidden_vars = {}
    readable_pps = _readable_node(value_vars.get('pps'))
    static_vars['узел связи'] = readable_pps
    static_vars['модель коммутатора'] = value_vars.get('model_csw')
    if value_vars.get('model_csw') == 'D-Link DGS-1100-06/ME':
        hidden_vars[
            '- Внимание! В случае отсутствия на складе модели коммутатор D-Link DGS-1100-06/ME использовать любую из перечисленных моделей: SNR-S2950-24G; ORION Alpha A26.'] = '- Внимание! В случае отсутствия на складе модели коммутатор D-Link DGS-1100-06/ME использовать любую из перечисленных моделей: SNR-S2950-24G; ORION Alpha A26.'
    static_vars['магистральный порт на клиентском коммутаторе'] = value_vars.get('port_csw')
    logic_csw_1000 = value_vars.get('logic_csw_1000')
    if logic_csw_1000 or value_vars.get('logic_change_gi_csw'):
        static_vars['пропускная способность'] = '1000 Мбит/с'
    else:
        static_vars['пропускная способность'] = '100 Мбит/с'
    templates = value_vars.get('templates')
    stroka = templates.get("Установка клиентского коммутатора.")
    if value_vars.get('ppr'):
        hidden_vars['- Требуется отключение согласно списку отключений в ППР %№ заявки ППР% согласовать проведение работ.'] = '- Требуется отключение согласно списку отключений в ППР %№ заявки ППР% согласовать проведение работ.'
        hidden_vars['- Совместно с ОНИТС СПД убедиться в восстановлении связи согласно списку отключений в ППР %№ заявки ППР%.'] = '- Совместно с ОНИТС СПД убедиться в восстановлении связи согласно списку отключений в ППР %№ заявки ППР%.'
        hidden_vars['- После проведения монтажных работ убедиться в восстановлении услуг согласно списку отключений в ППР %№ заявки ППР%.'] = '- После проведения монтажных работ убедиться в восстановлении услуг согласно списку отключений в ППР %№ заявки ППР%.'
        static_vars['№ заявки ППР'] = value_vars.get('ppr')
    if 'Перенос, СПД' not in value_vars.get('type_pass'):
        hidden_vars['МКО:'] = 'МКО:'
        hidden_vars[
        '- Проинформировать клиента о простое сервиса на время проведения работ.'] = '- Проинформировать клиента о простое сервиса на время проведения работ.'
        hidden_vars['- Согласовать время проведение работ.'] = '- Согласовать время проведение работ.'

    if value_vars.get('type_install_csw') == 'Медная линия и порт не меняются':
        static_vars['отдел ОИПМ / ОИПД'] = 'ОИПД'
        kad = value_vars.get('selected_ono')[0][-2]
        static_vars['название коммутатора'] = kad
        result_services.append(analyzer_vars(stroka, static_vars, hidden_vars))
    elif value_vars.get('type_install_csw') == 'ВОЛС и порт не меняются':
        static_vars['отдел ОИПМ / ОИПД'] = 'ОИПМ'
        hidden_vars[
            'и %тип конвертера/передатчика на стороне клиента%'] = 'и %тип конвертера/передатчика на стороне клиента%'
        static_vars['тип конвертера/передатчика на стороне клиента'] = value_vars.get('device_client')
        if logic_csw_1000 == True and value_vars.get('model_csw') == 'D-Link DGS-1100-06/ME':
            hidden_vars[
                '-ВНИМАНИЕ! Совместно с ОНИТС СПД удаленно настроить клиентский коммутатор.'] = '-ВНИМАНИЕ! Совместно с ОНИТС СПД удаленно настроить клиентский коммутатор.'
            hidden_vars[
                '- Совместно с %отдел ОИПМ / ОИПД% удаленно настроить клиентский коммутатор.'] = '- Совместно с %отдел ОИПМ / ОИПД% удаленно настроить клиентский коммутатор.'
        kad = value_vars.get('selected_ono')[0][-2]
        static_vars['название коммутатора'] = kad
        result_services.append(analyzer_vars(stroka, static_vars, hidden_vars))
    else:
        kad = value_vars.get('kad')
        static_vars['название коммутатора'] = kad
        static_vars['порт доступа на коммутаторе'] = value_vars.get('port')
        if value_vars.get('type_install_csw') == 'Перевод на гигабит по меди на текущем узле':
            static_vars['отдел ОИПМ / ОИПД'] = 'ОИПД'
            hidden_vars[
            '- Использовать существующую %тип линии связи% от %узел связи% до клиента.'] = '- Использовать существующую %тип линии связи% от %узел связи% до клиента.'
            hidden_vars[
            '- Переключить линию для клиента в порт %порт доступа на коммутаторе% коммутатора %название коммутатора%.'] = '- Переключить линию для клиента в порт %порт доступа на коммутаторе% коммутатора %название коммутатора%.'
            hidden_vars[
            'Старый порт: порт %старый порт доступа на коммутаторе% коммутатора %название коммутатора ранее используемого%.'] = 'Старый порт: порт %старый порт доступа на коммутаторе% коммутатора %название коммутатора ранее используемого%.'
            hidden_vars[
            'Новый порт: порт %порт доступа на коммутаторе% коммутатора %название коммутатора%.'] = 'Новый порт: порт %порт доступа на коммутаторе% коммутатора %название коммутатора%.'
            static_vars['тип линии связи'] = 'медную линию связи'
            static_vars['название коммутатора ранее используемого'] = value_vars.get('selected_ono')[0][-2]
            static_vars['старый порт доступа на коммутаторе'] = value_vars.get('selected_ono')[0][-1]
            result_services.append(analyzer_vars(stroka, static_vars, hidden_vars))
        elif value_vars.get('type_install_csw') == 'Перевод на гигабит по ВОЛС на текущем узле':
            static_vars['отдел ОИПМ / ОИПД'] = 'ОИПМ'
            hidden_vars[
            '- Использовать существующую %тип линии связи% от %узел связи% до клиента.'] = '- Использовать существующую %тип линии связи% от %узел связи% до клиента.'
            hidden_vars[
            '- Переключить линию для клиента в порт %порт доступа на коммутаторе% коммутатора %название коммутатора%.'] = '- Переключить линию для клиента в порт %порт доступа на коммутаторе% коммутатора %название коммутатора%.'
            hidden_vars[
            'Старый порт: порт %старый порт доступа на коммутаторе% коммутатора %название коммутатора ранее используемого%.'] = 'Старый порт: порт %старый порт доступа на коммутаторе% коммутатора %название коммутатора ранее используемого%.'
            hidden_vars[
            'Новый порт: порт %порт доступа на коммутаторе% коммутатора %название коммутатора%.'] = 'Новый порт: порт %порт доступа на коммутаторе% коммутатора %название коммутатора%.'
            hidden_vars[
            '- Установить на стороне %узел связи% %тип конвертера/передатчика на стороне узла доступа%'] = '- Установить на стороне %узел связи% %тип конвертера/передатчика на стороне узла доступа%'
            static_vars['тип конвертера/передатчика на стороне узла доступа'] = value_vars.get('device_pps')
            hidden_vars[
            'и %тип конвертера/передатчика на стороне клиента%'] = 'и %тип конвертера/передатчика на стороне клиента%'
            static_vars['тип конвертера/передатчика на стороне клиента'] = value_vars.get('device_client')
            static_vars['тип линии связи'] = 'ВОЛС'

            static_vars['название коммутатора ранее используемого'] = value_vars.get('selected_ono')[0][-2]
            static_vars['старый порт доступа на коммутаторе'] = value_vars.get('selected_ono')[0][-1]
            if value_vars.get('model_csw') == 'D-Link DGS-1100-06/ME':
                hidden_vars[
                '-ВНИМАНИЕ! Совместно с ОНИТС СПД удаленно настроить клиентский коммутатор.'] = '-ВНИМАНИЕ! Совместно с ОНИТС СПД удаленно настроить клиентский коммутатор.'
                hidden_vars[
                '- Совместно с %отдел ОИПМ / ОИПД% удаленно настроить клиентский коммутатор.'] = '- Совместно с %отдел ОИПМ / ОИПД% удаленно настроить клиентский коммутатор.'
            result_services.append(analyzer_vars(stroka, static_vars, hidden_vars))
        elif value_vars.get('type_install_csw') == 'Перевод на гигабит переключение с меди на ВОЛС' or value_vars.get(
            'type_install_csw') == 'Перенос на новый узел':
            hidden_vars[
            '- Организовать %тип линии связи% от %узел связи% до клиентcкого коммутатора по решению ОАТТР.'] = '- Организовать %тип линии связи% от %узел связи% до клиентcкого коммутатора по решению ОАТТР.'
            hidden_vars[
                '- Подключить организованную линию для клиента в коммутатор %название коммутатора%, порт задействовать %порт доступа на коммутаторе%.'] = '- Подключить организованную линию для клиента в коммутатор %название коммутатора%, порт задействовать %порт доступа на коммутаторе%.'
            if value_vars.get('sreda') == '2' or value_vars.get('sreda') == '4':
                static_vars['тип линии связи'] = 'ВОЛС'
                static_vars['отдел ОИПМ / ОИПД'] = 'ОИПМ'
                hidden_vars[
                '- Установить на стороне %узел связи% %тип конвертера/передатчика на стороне узла доступа%'] = '- Установить на стороне %узел связи% %тип конвертера/передатчика на стороне узла доступа%'
                static_vars['тип конвертера/передатчика на стороне узла доступа'] = value_vars.get('device_pps')
                hidden_vars[
                'и %тип конвертера/передатчика на стороне клиента%'] = 'и %тип конвертера/передатчика на стороне клиента%'
                static_vars['тип конвертера/передатчика на стороне клиента'] = value_vars.get('device_client')
                if logic_csw_1000 == True and value_vars.get('model_csw') == 'D-Link DGS-1100-06/ME':
                    hidden_vars[
                        '-ВНИМАНИЕ! Совместно с ОНИТС СПД удаленно настроить клиентский коммутатор.'] = '-ВНИМАНИЕ! Совместно с ОНИТС СПД удаленно настроить клиентский коммутатор.'
                    hidden_vars[
                        '- Совместно с %отдел ОИПМ / ОИПД% удаленно настроить клиентский коммутатор.'] = '- Совместно с %отдел ОИПМ / ОИПД% удаленно настроить клиентский коммутатор.'
            else:
                static_vars['тип линии связи'] = 'медную линию связи'
                static_vars['отдел ОИПМ / ОИПД'] = 'ОИПД'
            result_services.append(analyzer_vars(stroka, static_vars, hidden_vars))
    value_vars.update({'kad': kad})
    return result_services, value_vars


def exist_enviroment_replace_csw(value_vars):
    """Данный метод формирует блок ТТР замены КК"""
    if value_vars.get('result_services'):
        result_services = value_vars.get('result_services')
    else:
        result_services = []
    static_vars = {}
    hidden_vars = {}
    old_kad = value_vars.get('head').split('\n')[4].split()[2]
    old_port = value_vars.get('head').split('\n')[5].split()[2]
    static_vars['название коммутатора'] = old_kad
    logic_csw_1000 = value_vars.get('logic_csw_1000')
    if logic_csw_1000 or value_vars.get('logic_change_gi_csw'):
        static_vars['пропускная способность'] = '1000 Мбит/с'
        readable_pps = _readable_node(value_vars.get('pps'))
    else:
        static_vars['пропускная способность'] = '100 Мбит/с'
        readable_pps = ' '.join(value_vars.get('head').split('\n')[3].split()[1:])
    static_vars['узел связи'] = readable_pps
    static_vars['модель коммутатора'] = value_vars.get('model_csw')
    static_vars['магистральный порт на клиентском коммутаторе'] = value_vars.get('port_csw')
    static_vars['узел связи клиентского коммутатора'] = _readable_node(value_vars.get('node_csw'))
    static_vars['старая модель коммутатора'] = value_vars.get('old_model_csw')
    hidden_vars['- Линии связи клиента переключить "порт в порт".'] = '- Линии связи клиента переключить "порт в порт".'
    hidden_vars['- Актуализировать информацию в ИС Cordis и системах учета.'] = '- Актуализировать информацию в ИС Cordis и системах учета.'
    types_old_models = ('DIR-100', '3COM', 'Cisco')

    templates = value_vars.get('templates')
    stroka = templates.get("%Замена/Замена и перевод на гигабит% клиентского коммутатора.")
    if value_vars.get('type_install_csw') == 'Медная линия и порт не меняются':
        static_vars['отдел ОИПМ / ОИПД'] = 'ОИПД'
        static_vars['Замена/Замена и перевод на гигабит'] = 'Замена'
        result_services.append(analyzer_vars(stroka, static_vars, hidden_vars))
    elif value_vars.get('type_install_csw') == 'ВОЛС и порт не меняются':
        static_vars['отдел ОИПМ / ОИПД'] = 'ОИПМ'
        static_vars['Замена/Замена и перевод на гигабит'] = 'Замена'
        if any(type in value_vars.get('old_model_csw') for type in types_old_models):
            hidden_vars[
            'и %тип конвертера/передатчика на стороне клиента%'] = 'и %тип конвертера/передатчика на стороне клиента%'
            static_vars['тип конвертера/передатчика на стороне клиента'] = value_vars.get('device_client')
        else:
            hidden_vars['(передатчик задействовать из демонтированного коммутатора)'] = '(передатчик задействовать из демонтированного коммутатора)'
        if logic_csw_1000 == True and value_vars.get('model_csw') == 'D-Link DGS-1100-06/ME':
            hidden_vars[
                '-ВНИМАНИЕ! Совместно с ОНИТС СПД удаленно настроить клиентский коммутатор.'] = '-ВНИМАНИЕ! Совместно с ОНИТС СПД удаленно настроить клиентский коммутатор.'
            hidden_vars[
                '- Совместно с %отдел ОИПМ / ОИПД% удаленно настроить клиентский коммутатор.'] = '- Совместно с %отдел ОИПМ / ОИПД% удаленно настроить клиентский коммутатор.'
        result_services.append(analyzer_vars(stroka, static_vars, hidden_vars))
    else:
        hidden_vars[
            '- Сообщить в ОЛИ СПД об освободившемся порте на %название коммутатора ранее используемого%.'] = '- Сообщить в ОЛИ СПД об освободившемся порте на %название коммутатора ранее используемого%.'
        static_vars['название коммутатора ранее используемого'] = old_kad
        if value_vars.get('logic_change_gi_csw') or logic_csw_1000:
            static_vars['Замена/Замена и перевод на гигабит'] = 'Замена и перевод на гигабит'
        else:
            static_vars['Замена/Замена и перевод на гигабит'] = 'Замена'
        if value_vars.get('ppr'):
            hidden_vars[
                '- Требуется отключение согласно списку отключений в ППР %№ заявки ППР% согласовать проведение работ.'] = '- Требуется отключение согласно списку отключений в ППР %№ заявки ППР% согласовать проведение работ.'
            hidden_vars[
                '- Совместно с ОНИТС СПД убедиться в восстановлении связи согласно списку отключений в ППР %№ заявки ППР%.'] = '- Совместно с ОНИТС СПД убедиться в восстановлении связи согласно списку отключений в ППР %№ заявки ППР%.'
            hidden_vars[
                '- После проведения монтажных работ убедиться в восстановлении услуг согласно списку отключений в ППР %№ заявки ППР%.'] = '- После проведения монтажных работ убедиться в восстановлении услуг согласно списку отключений в ППР %№ заявки ППР%.'
            static_vars['№ заявки ППР'] = value_vars.get('ppr')
        kad = value_vars.get('kad')
        static_vars['название коммутатора'] = kad
        static_vars['порт доступа на коммутаторе'] = value_vars.get('port')
        if value_vars.get('type_install_csw') == 'Перевод на гигабит по меди на текущем узле':
            static_vars['отдел ОИПМ / ОИПД'] = 'ОИПД'
            hidden_vars[
            '- Использовать существующую %тип линии связи% от %узел связи% до клиента.'] = '- Использовать существующую %тип линии связи% от %узел связи% до клиента.'
            hidden_vars[
            '- Переключить линию для клиента в порт %порт доступа на коммутаторе% коммутатора %название коммутатора%.'] = '- Переключить линию для клиента в порт %порт доступа на коммутаторе% коммутатора %название коммутатора%.'
            hidden_vars[
            'Старый порт: порт %старый порт доступа на коммутаторе% коммутатора %название коммутатора ранее используемого%.'] = 'Старый порт: порт %старый порт доступа на коммутаторе% коммутатора %название коммутатора ранее используемого%.'
            hidden_vars[
            'Новый порт: порт %порт доступа на коммутаторе% коммутатора %название коммутатора%.'] = 'Новый порт: порт %порт доступа на коммутаторе% коммутатора %название коммутатора%.'
            static_vars['тип линии связи'] = 'медную линию связи'
            static_vars['название коммутатора ранее используемого'] = old_kad
            static_vars['старый порт доступа на коммутаторе'] = old_port
            result_services.append(analyzer_vars(stroka, static_vars, hidden_vars))
        elif value_vars.get('type_install_csw') == 'Перевод на гигабит по ВОЛС на текущем узле':
            static_vars['отдел ОИПМ / ОИПД'] = 'ОИПМ'
            hidden_vars[
            '- Использовать существующую ВОЛС от %узел связи% до клиентского коммутатора.'] = '- Использовать существующую ВОЛС от %узел связи% до клиентского коммутатора.'
            hidden_vars[
            '- Переключить линию до клиентского коммутатора в порт %порт доступа на коммутаторе% коммутатора %название коммутатора%.'] = '- Переключить линию до клиентского коммутатора в порт %порт доступа на коммутаторе% коммутатора %название коммутатора%.'
            hidden_vars[
            'Старый порт: порт %старый порт доступа на коммутаторе% коммутатора %название коммутатора ранее используемого%.'] = 'Старый порт: порт %старый порт доступа на коммутаторе% коммутатора %название коммутатора ранее используемого%.'
            hidden_vars[
            'Новый порт: порт %порт доступа на коммутаторе% коммутатора %название коммутатора%.'] = 'Новый порт: порт %порт доступа на коммутаторе% коммутатора %название коммутатора%.'
            hidden_vars[
            '- Установить на стороне %узел связи% %тип конвертера/передатчика на стороне узла доступа%'] = '- Установить на стороне %узел связи% %тип конвертера/передатчика на стороне узла доступа%'
            static_vars['тип конвертера/передатчика на стороне узла доступа'] = value_vars.get('device_pps')
            hidden_vars[
            'и %тип конвертера/передатчика на стороне клиента%'] = 'и %тип конвертера/передатчика на стороне клиента%'
            static_vars['тип конвертера/передатчика на стороне клиента'] = value_vars.get('device_client')
            static_vars['тип линии связи'] = 'ВОЛС'
            static_vars['название коммутатора ранее используемого'] = old_kad
            static_vars['старый порт доступа на коммутаторе'] = old_port
            if value_vars.get('model_csw') == 'D-Link DGS-1100-06/ME':
                hidden_vars[
                '-ВНИМАНИЕ! Совместно с ОНИТС СПД удаленно настроить клиентский коммутатор.'] = '-ВНИМАНИЕ! Совместно с ОНИТС СПД удаленно настроить клиентский коммутатор.'
                hidden_vars[
                '- Совместно с %отдел ОИПМ / ОИПД% удаленно настроить клиентский коммутатор.'] = '- Совместно с %отдел ОИПМ / ОИПД% удаленно настроить клиентский коммутатор.'
            result_services.append(analyzer_vars(stroka, static_vars, hidden_vars))
        elif value_vars.get('type_install_csw') == 'Перевод на гигабит переключение с меди на ВОЛС' or value_vars.get(
            'type_install_csw') == 'Перенос на новый узел':
            hidden_vars[
            '- Организовать ВОЛС от %узел связи% до клиентcкого коммутатора по решению ОТПМ.'] = '- Организовать ВОЛС от %узел связи% до клиентcкого коммутатора по решению ОТПМ.'
            static_vars['тип линии связи'] = 'ВОЛС'
            static_vars['отдел ОИПМ / ОИПД'] = 'ОИПМ'
            hidden_vars[
            '- Подключить организованную линию для клиента в коммутатор %название коммутатора%, порт задействовать %порт доступа на коммутаторе%.'] = '- Подключить организованную линию для клиента в коммутатор %название коммутатора%, порт задействовать %порт доступа на коммутаторе%.'
            hidden_vars[
            '- Установить на стороне %узел связи% %тип конвертера/передатчика на стороне узла доступа%'] = '- Установить на стороне %узел связи% %тип конвертера/передатчика на стороне узла доступа%'
            static_vars['тип конвертера/передатчика на стороне узла доступа'] = value_vars.get('device_pps')
            hidden_vars[
                'Старый порт: порт %старый порт доступа на коммутаторе% коммутатора %название коммутатора ранее используемого%.'] = 'Старый порт: порт %старый порт доступа на коммутаторе% коммутатора %название коммутатора ранее используемого%.'
            hidden_vars[
                'Новый порт: порт %порт доступа на коммутаторе% коммутатора %название коммутатора%.'] = 'Новый порт: порт %порт доступа на коммутаторе% коммутатора %название коммутатора%.'
            hidden_vars[
                '- Установить на стороне %узел связи% %тип конвертера/передатчика на стороне узла доступа%'] = '- Установить на стороне %узел связи% %тип конвертера/передатчика на стороне узла доступа%'
            static_vars['тип конвертера/передатчика на стороне узла доступа'] = value_vars.get('device_pps')
            hidden_vars[
                'и %тип конвертера/передатчика на стороне клиента%'] = 'и %тип конвертера/передатчика на стороне клиента%'
            static_vars['тип конвертера/передатчика на стороне клиента'] = value_vars.get('device_client')
            static_vars['тип линии связи'] = 'ВОЛС'
            static_vars['название коммутатора ранее используемого'] = old_kad
            static_vars['старый порт доступа на коммутаторе'] = old_port

            if logic_csw_1000 or value_vars.get('logic_change_gi_csw'):
                if value_vars.get('model_csw') == 'D-Link DGS-1100-06/ME':
                    hidden_vars[
                        '-ВНИМАНИЕ! Совместно с ОНИТС СПД удаленно настроить клиентский коммутатор.'] = '-ВНИМАНИЕ! Совместно с ОНИТС СПД удаленно настроить клиентский коммутатор.'
                    hidden_vars[
                        '- Совместно с %отдел ОИПМ / ОИПД% удаленно настроить клиентский коммутатор.'] = '- Совместно с %отдел ОИПМ / ОИПД% удаленно настроить клиентский коммутатор.'
                if old_kad.split('-')[1] != kad.split('-')[1]:
                    readable_services = value_vars.get('readable_services')
                    change_log_shpd = value_vars.get('change_log_shpd')
                    services, service_shpd_change = _separate_services_and_subnet_dhcp(readable_services, change_log_shpd)
                    if service_shpd_change:
                        hidden_vars[
                            '- Выделить новую адресацию с маской %нов. маска IP-сети% вместо %ресурс на договоре%.'] = '- Выделить новую адресацию с маской %нов. маска IP-сети% вместо %ресурс на договоре%.'
                        static_vars['нов. маска IP-сети'] = '/32'
                        static_vars['ресурс на договоре'] = ' '.join(service_shpd_change)
                        hidden_vars['- После смены реквизитов:'] = '- После смены реквизитов:'
                        hidden_vars[
                            '- разобрать ресурс %ресурс на договоре% на договоре.'] = '- разобрать ресурс %ресурс на договоре% на договоре.'

                    hidden_vars[
                        '- Выделить для клиентского коммутатора[ и тел. шлюза %название тел. шлюза%] новые реквизиты управления.'] = '- Выделить для клиентского коммутатора[ и тел. шлюза %название тел. шлюза%] новые реквизиты управления.'
                    hidden_vars['- Сменить реквизиты клиентского коммутатора [и тел. шлюза %название тел. шлюза%].'] = '- Сменить реквизиты клиентского коммутатора [и тел. шлюза %название тел. шлюза%].'
                    vgws = []
                    if value_vars.get('vgw_chains'):
                        for i in value_vars.get('vgw_chains'):
                            if i.get('model') != 'ITM SIP':
                                vgws.append(i.get('name'))
                    if value_vars.get('waste_vgw'):
                        for i in value_vars.get('waste_vgw'):
                            if i.get('model') != 'ITM SIP':
                                vgws.append(i.get('name'))
                    if vgws and len(vgws) == 1:
                        hidden_vars[
                            '- Перед проведением работ запросить ОНИТС СПД сменить реквизиты тел. шлюза %название тел. шлюза% на ZIP.'] = '- Перед проведением работ запросить ОНИТС СПД сменить реквизиты тел. шлюза %название тел. шлюза% на ZIP.'
                        hidden_vars[
                            ' и тел. шлюза %название тел. шлюза%'] = ' и тел. шлюза %название тел. шлюза%'
                        hidden_vars[
                            ' и тел. шлюз %название тел. шлюза%'] = ' и тел. шлюз %название тел. шлюза%'
                        hidden_vars['и тел. шлюза %название тел. шлюза%'] = 'и тел. шлюза %название тел. шлюза%'
                        hidden_vars['и тел. шлюз %название тел. шлюза%'] = 'и тел. шлюз %название тел. шлюза%'
                        static_vars['название тел. шлюза'] = ', '.join(vgws)
                    elif vgws and len(vgws) > 1:
                        hidden_vars[
                            '- Перед проведением работ запросить ОНИТС СПД сменить реквизиты тел. шлюза %название тел. шлюза% на ZIP.'] = '- Перед проведением работ запросить ОНИТС СПД сменить реквизиты тел. шлюза %название тел. шлюза% на ZIP.'
                        hidden_vars[
                            ' и тел. шлюза %название тел. шлюза%'] = ' и тел. шлюзов %название тел. шлюза%'
                        hidden_vars[
                            ' и тел. шлюз %название тел. шлюза%'] = ' и тел. шлюзы %название тел. шлюза%'
                        hidden_vars['и тел. шлюза %название тел. шлюза%'] = 'и тел. шлюзов %название тел. шлюза%'
                        hidden_vars['и тел. шлюз %название тел. шлюза%'] = 'и тел. шлюзы %название тел. шлюза%'
                        static_vars['название тел. шлюза'] = ', '.join(vgws)
            result_services.append(analyzer_vars(stroka, static_vars, hidden_vars))
    return result_services, value_vars


def exist_enviroment_passage_csw(value_vars):
    """Данный метод формирует блок ТТР переноса/перевода на гигабит КК"""
    if value_vars.get('result_services'):
        result_services = value_vars.get('result_services')
    else:
        result_services = []
    static_vars = {}
    hidden_vars = {}
    kad = value_vars.get('kad')
    port = value_vars.get('port')
    sreda = value_vars.get('sreda')
    readable_pps = _readable_node(value_vars.get('pps'))
    templates = value_vars.get('templates')
    readable_services = value_vars.get('readable_services')
    change_log_shpd = value_vars.get('change_log_shpd')
    static_vars['узел связи'] = readable_pps
    static_vars['название коммутатора'] = kad
    static_vars['модель коммутатора'] = value_vars.get('model_csw')
    static_vars['магистральный порт на клиентском коммутаторе'] = value_vars.get('port_csw')
    name_exist_csw = value_vars.get('selected_ono')[0][-2]
    static_vars['название коммутатора клиентского'] = name_exist_csw
    services, service_shpd_change = _separate_services_and_subnet_dhcp(readable_services, change_log_shpd)
    if service_shpd_change:
        hidden_vars['- Выделить новую адресацию с маской %нов. маска IP-сети% вместо %ресурс на договоре%.'] = '- Выделить новую адресацию с маской %нов. маска IP-сети% вместо %ресурс на договоре%.'
        static_vars['нов. маска IP-сети'] = '/32'
        static_vars['ресурс на договоре'] = ' '.join(service_shpd_change)
        hidden_vars['- После смены реквизитов:'] = '- После смены реквизитов:'
        hidden_vars['- разобрать ресурс %ресурс на договоре% на договоре.'] = '- разобрать ресурс %ресурс на договоре% на договоре.'

    if value_vars.get('ppr'):
        hidden_vars[
            '- Требуется отключение согласно списку отключений в ППР %№ заявки ППР% согласовать проведение работ.'] = '- Требуется отключение согласно списку отключений в ППР %№ заявки ППР% согласовать проведение работ.'
        hidden_vars[
            '- Совместно с ОНИТС СПД убедиться в восстановлении связи согласно списку отключений в ППР %№ заявки ППР%.'] = '- Совместно с ОНИТС СПД убедиться в восстановлении связи согласно списку отключений в ППР %№ заявки ППР%.'
        hidden_vars[
            '- После проведения монтажных работ убедиться в восстановлении услуг согласно списку отключений в ППР %№ заявки ППР%.'] = '- После проведения монтажных работ убедиться в восстановлении услуг согласно списку отключений в ППР %№ заявки ППР%.'
        static_vars['№ заявки ППР'] = value_vars.get('ppr')

    if sreda == '2' or sreda == '4':
        static_vars['отдел ОИПМ / ОИПД'] = 'ОИПМ'
        static_vars['тип конвертера/передатчика на стороне узла доступа'] = value_vars.get('device_pps')
        static_vars['тип конвертера/передатчика на стороне клиента'] = value_vars.get('device_client')
    else:
        static_vars['отдел ОИПМ / ОИПД'] = 'ОИПД'

    if value_vars.get('type_passage') == 'Перенос точки подключения':
        if value_vars.get('logic_change_gi_csw'):
            static_vars[
                'перенесен в новую точку подключения/переведен на гигабит/переключен на узел'] = 'перенесен в новую точку подключения, переведен на гигабит'
            static_vars['Перенос/Перевод на гигабит'] = 'Перенос и перевод на гигабит'
        else:
            static_vars['перенесен в новую точку подключения/переведен на гигабит/переключен на узел'] = 'перенесен в новую точку подключения'
            static_vars['Перенос/Перевод на гигабит'] = 'Перенос'
    elif value_vars.get('type_passage') == 'Перенос логического подключения':
        static_vars['Перенос/Перевод на гигабит'] = 'Перенос логического подключения'
        static_vars['перенесен в новую точку подключения/переведен на гигабит/переключен на узел'] = 'переключен на узел {}'.format(readable_pps)
    elif value_vars.get('type_passage') == 'Перевод на гигабит' or value_vars.get('logic_change_gi_csw'):
        static_vars['Перенос/Перевод на гигабит'] = 'Перевод на гигабит'
        static_vars['перенесен в новую точку подключения/переведен на гигабит/переключен на узел'] = 'переведен на гигабит'

    if value_vars.get('logic_change_gi_csw'):
        static_vars['пропускная способность'] = '1000 Мбит/с'
    else:
        static_vars['пропускная способность'] = '100 Мбит/с'
    if not value_vars.get('type_ticket') == 'ПТО':
        hidden_vars['МКО:'] = 'МКО:'
        hidden_vars['- Проинформировать клиента о простое сервисов на время проведения работ.'] = '- Проинформировать клиента о простое сервисов на время проведения работ.'
        hidden_vars['- Согласовать время проведение работ.'] = '- Согласовать время проведение работ.'
    if value_vars.get('ppr'):
        hidden_vars['- Согласовать проведение работ - ППР %№ заявки ППР%.'] = '- Согласовать проведение работ - ППР %№ заявки ППР%.'
        static_vars['№ заявки ППР'] = value_vars.get('ppr')
    if name_exist_csw.split('-')[1] != kad.split('-')[1]:
        hidden_vars['- Перед проведением работ запросить ОНИТС СПД сменить реквизиты клиентского коммутатора %название коммутатора клиентского% [и тел. шлюза %название тел. шлюза%] на ZIP.'] = '- Перед проведением работ запросить ОНИТС СПД сменить реквизиты клиентского коммутатора %название коммутатора клиентского% [и тел. шлюза %название тел. шлюза%] на ZIP.'
        hidden_vars[
            '- Выделить для клиентского коммутатора[ и тел. шлюза %название тел. шлюза%] новые реквизиты управления.'] = '- Выделить для клиентского коммутатора[ и тел. шлюза %название тел. шлюза%] новые реквизиты управления.'
        hidden_vars['- Сменить реквизиты клиентского коммутатора [и тел. шлюза %название тел. шлюза%].'] = '- Сменить реквизиты клиентского коммутатора [и тел. шлюза %название тел. шлюза%].'
        vgws = []
        if value_vars.get('vgw_chains'):
            for i in value_vars.get('vgw_chains'):
                if i.get('model') != 'ITM SIP':
                    vgws.append(i.get('name'))
        if value_vars.get('waste_vgw'):
            for i in value_vars.get('waste_vgw'):
                if i.get('model') != 'ITM SIP':
                    vgws.append(i.get('name'))
        if vgws and len(vgws) == 1:
            hidden_vars[' и тел. шлюза %название тел. шлюза%'] = ' и тел. шлюза %название тел. шлюза%'
            hidden_vars[' и тел. шлюз %название тел. шлюза%'] = ' и тел. шлюз %название тел. шлюза%'
            hidden_vars['и тел. шлюза %название тел. шлюза%'] = 'и тел. шлюза %название тел. шлюза%'
            hidden_vars['и тел. шлюз %название тел. шлюза%'] = 'и тел. шлюз %название тел. шлюза%'
            static_vars['название тел. шлюза'] = ', '.join(vgws)
        elif vgws and len(vgws) > 1:
            hidden_vars[' и тел. шлюза %название тел. шлюза%'] = ' и тел. шлюзов %название тел. шлюза%'
            hidden_vars[' и тел. шлюз %название тел. шлюза%'] = ' и тел. шлюзы %название тел. шлюза%'
            hidden_vars['и тел. шлюза %название тел. шлюза%'] = 'и тел. шлюзов %название тел. шлюза%'
            hidden_vars['и тел. шлюз %название тел. шлюза%'] = 'и тел. шлюзы %название тел. шлюза%'
            static_vars['название тел. шлюза'] = ', '.join(vgws)
    if value_vars.get('type_passage') == 'Перенос точки подключения':
        if value_vars.get('type_install_csw') not in ['Медная линия и порт не меняются', 'ВОЛС и порт не меняются']:
            old_kad = value_vars.get('head').split('\n')[4].split()[2]
            hidden_vars[
                '- Сообщить в ОЛИ СПД об освободившемся порте на %название коммутатора ранее используемого%.'] = '- Сообщить в ОЛИ СПД об освободившемся порте на %название коммутатора ранее используемого%.'
            static_vars['название коммутатора ранее используемого'] = old_kad
        static_vars['переносу/переводу на гигабит'] = 'переносу'
        hidden_vars['- Актуализировать информацию в ИС Cordis и системах учета.'] = '- Актуализировать информацию в ИС Cordis и системах учета.'

        hidden_vars['от %узел связи% '] = 'от %узел связи% '
        hidden_vars[
            '- Подключить организованную линию для клиента в коммутатор %название коммутатора%, порт задействовать %порт доступа на коммутаторе%.'] = '- Подключить организованную линию для клиента в коммутатор %название коммутатора%, порт задействовать %порт доступа на коммутаторе%.'
        hidden_vars['Старый порт: порт %старый порт доступа на коммутаторе% коммутатора %название коммутатора ранее используемого%.'] = 'Старый порт: порт %старый порт доступа на коммутаторе% коммутатора %название коммутатора ранее используемого%.'
        static_vars['старый порт доступа на коммутаторе'] = value_vars.get('head').split('\n')[5].split()[2]
        static_vars['название коммутатора ранее используемого'] = value_vars.get('head').split('\n')[4].split()[2]
        hidden_vars['Новый порт: порт %порт доступа на коммутаторе% коммутатора %название коммутатора%.'] = 'Новый порт: порт %порт доступа на коммутаторе% коммутатора %название коммутатора%.'
        static_vars['порт доступа на коммутаторе'] = port
        hidden_vars['- Перенести в новое помещении клиента коммутатор %название коммутатора клиентского%.'] = '- Перенести в новое помещении клиента коммутатор %название коммутатора клиентского%.'
        hidden_vars['- Включить линию для клиента в порт %магистральный порт на клиентском коммутаторе% коммутатора %название коммутатора клиентского%.'] = '- Включить линию для клиента в порт %магистральный порт на клиентском коммутаторе% коммутатора %название коммутатора клиентского%.'
        hidden_vars['- Линии связи клиента переключить "порт в порт".'] = '- Линии связи клиента переключить "порт в порт".'
        if sreda == '1':
            hidden_vars[
                '- Организовать %тип линии связи% [от %узел связи% ]до клиентcкого коммутатора по решению ОТПМ.'] = '- Организовать %тип линии связи% [от %узел связи% ]до клиентcкого коммутатора по решению ОТПМ.'
            hidden_vars['от %узел связи% '] = 'от %узел связи% '
            static_vars['тип линии связи'] = 'медную линию связи'
            static_vars['отдел ОИПМ / ОИПД'] = 'ОИПД'
        elif sreda == '2' or sreda == '4':
            hidden_vars[
                '- Организовать %тип линии связи% [от %узел связи% ]до клиентcкого коммутатора по решению ОТПМ.'] = '- Организовать %тип линии связи% [от %узел связи% ]до клиентcкого коммутатора по решению ОТПМ.'
            hidden_vars['от %узел связи% '] = 'от %узел связи% '
            static_vars['тип линии связи'] = 'ВОЛС'
            hidden_vars['- Установить на стороне %узел связи% %тип конвертера/передатчика на стороне узла доступа%'] = '- Установить на стороне %узел связи% %тип конвертера/передатчика на стороне узла доступа%'
            if sreda != value_vars.get('exist_sreda'):
                hidden_vars['- В %название коммутатора клиентского% установить %тип конвертера/передатчика на стороне клиента%.'] = '- В %название коммутатора клиентского% установить %тип конвертера/передатчика на стороне клиента%.'
        elif sreda == '3':
            hidden_vars[
                '- Создать заявку в ИС Cordis на ОНИТС СПД для выделения реквизитов беспроводных точек доступа WDS/WDA.'] = '- Создать заявку в ИС Cordis на ОНИТС СПД для выделения реквизитов беспроводных точек доступа WDS/WDA.'
            if value_vars.get('access_point') == 'Infinet E5':
                hidden_vars[
                    '- Доставить в офис ОНИТС СПД беспроводные точки Infinet E5 для их настройки.'] = '- Доставить в офис ОНИТС СПД беспроводные точки Infinet E5 для их настройки.'
                hidden_vars[
                    'После выполнения подготовительных работ в рамках заявки в ИС Cordis на ОНИТС СПД и настройки точек в офисе ОНИТС СПД:'] = 'После выполнения подготовительных работ в рамках заявки в ИС Cordis на ОНИТС СПД и настройки точек в офисе ОНИТС СПД:'
            else:
                hidden_vars[
                    'После выполнения подготовительных работ в рамках заявки в ИС Cordis на ОНИТС СПД:'] = 'После выполнения подготовительных работ в рамках заявки в ИС Cordis на ОНИТС СПД:'
            hidden_vars[
                '- Установить на стороне %узел связи% и на стороне клиента беспроводные точки доступа %модель беспроводной базовой станции% по решению ОТПМ.'] = '- Установить на стороне %узел связи% и на стороне клиента беспроводные точки доступа %модель беспроводной базовой станции% по решению ОТПМ.'
            static_vars['модель беспроводной базовой станции'] = value_vars.get('access_point')
            hidden_vars[
                '- По заявке в ИС Cordis выделить реквизиты для управления беспроводными точками.'] = '- По заявке в ИС Cordis выделить реквизиты для управления беспроводными точками.'
            hidden_vars[
                '- Совместно с ОИПД подключить к СПД и запустить беспроводные станции (WDS/WDA).'] = '- Совместно с ОИПД подключить к СПД и запустить беспроводные станции (WDS/WDA).'
            hidden_vars['от %узел связи% '] = 'от беспроводной точки '
            hidden_vars[
                '- Организовать %тип линии связи% от %узел связи% до беспроводной точки по решению ОТПМ.'] = '- Организовать %тип линии связи% от %узел связи% до беспроводной точки по решению ОТПМ.'
            hidden_vars['- На стороне клиента организовать медный патч-корд от WDA до клиентского коммутатора.'] = '- На стороне клиента организовать медный патч-корд от WDA до клиентского коммутатора.'
            static_vars['отдел ОИПМ / ОИПД'] = 'ОИПД'
            static_vars['тип линии связи'] = 'медную линию связи'
    elif value_vars.get('type_passage') == 'Перенос логического подключения':
        old_kad = value_vars.get('head').split('\n')[4].split()[2]
        hidden_vars[
            '- Сообщить в ОЛИ СПД об освободившемся порте на %название коммутатора ранее используемого%.'] = '- Сообщить в ОЛИ СПД об освободившемся порте на %название коммутатора ранее используемого%.'
        static_vars['название коммутатора ранее используемого'] = old_kad
        static_vars['переносу/переводу на гигабит'] = 'переносу логического подключения'
        hidden_vars['- Актуализировать информацию в ИС Cordis и системах учета.'] = '- Актуализировать информацию в ИС Cordis и системах учета.'
        hidden_vars[
            '- Подключить организованную линию для клиента в коммутатор %название коммутатора%, порт задействовать %порт доступа на коммутаторе%.'] = '- Подключить организованную линию для клиента в коммутатор %название коммутатора%, порт задействовать %порт доступа на коммутаторе%.'
        hidden_vars['Старый порт: порт %старый порт доступа на коммутаторе% коммутатора %название коммутатора ранее используемого%.'] = 'Старый порт: порт %старый порт доступа на коммутаторе% коммутатора %название коммутатора ранее используемого%.'
        static_vars['старый порт доступа на коммутаторе'] = value_vars.get('head').split('\n')[5].split()[2]
        static_vars['название коммутатора ранее используемого'] = value_vars.get('head').split('\n')[4].split()[2]
        hidden_vars['Новый порт: порт %порт доступа на коммутаторе% коммутатора %название коммутатора%.'] = 'Новый порт: порт %порт доступа на коммутаторе% коммутатора %название коммутатора%.'
        static_vars['порт доступа на коммутаторе'] = port
        if sreda == '1':
            hidden_vars[
                '- Организовать %тип линии связи% [от %узел связи% ]до клиентcкого коммутатора по решению ОТПМ.'] = '- Организовать %тип линии связи% [от %узел связи% ]до клиентcкого коммутатора по решению ОТПМ.'
            hidden_vars['от %узел связи% '] = 'от %узел связи% '
            static_vars['тип линии связи'] = 'медную линию связи'
            static_vars['отдел ОИПМ / ОИПД'] = 'ОИПД'
        elif sreda == '2' or sreda == '4':
            hidden_vars[
                '- Организовать %тип линии связи% [от %узел связи% ]до клиентcкого коммутатора по решению ОТПМ.'] = '- Организовать %тип линии связи% [от %узел связи% ]до клиентcкого коммутатора по решению ОТПМ.'
            hidden_vars['от %узел связи% '] = 'от %узел связи% '
            static_vars['тип линии связи'] = 'ВОЛС'
            hidden_vars['- Установить на стороне %узел связи% %тип конвертера/передатчика на стороне узла доступа%'] = '- Установить на стороне %узел связи% %тип конвертера/передатчика на стороне узла доступа%'
            if value_vars.get('exist_sreda') == '1' or value_vars.get('exist_sreda') == '3':
                hidden_vars['- В %название коммутатора клиентского% установить %тип конвертера/передатчика на стороне клиента%.'] = '- В %название коммутатора клиентского% установить %тип конвертера/передатчика на стороне клиента%.'
                hidden_vars['- Включить линию для клиента в порт %магистральный порт на клиентском коммутаторе% коммутатора %название коммутатора клиентского%.'] = '- Включить линию для клиента в порт %магистральный порт на клиентском коммутаторе% коммутатора %название коммутатора клиентского%.'
        elif sreda == '3':
            hidden_vars[
                '- Создать заявку в ИС Cordis на ОНИТС СПД для выделения реквизитов беспроводных точек доступа WDS/WDA.'] = '- Создать заявку в ИС Cordis на ОНИТС СПД для выделения реквизитов беспроводных точек доступа WDS/WDA.'
            if value_vars.get('access_point') == 'Infinet E5':
                hidden_vars[
                    '- Доставить в офис ОНИТС СПД беспроводные точки Infinet E5 для их настройки.'] = '- Доставить в офис ОНИТС СПД беспроводные точки Infinet E5 для их настройки.'
                hidden_vars[
                    'После выполнения подготовительных работ в рамках заявки в ИС Cordis на ОНИТС СПД и настройки точек в офисе ОНИТС СПД:'] = 'После выполнения подготовительных работ в рамках заявки в ИС Cordis на ОНИТС СПД и настройки точек в офисе ОНИТС СПД:'
            else:
                hidden_vars[
                    'После выполнения подготовительных работ в рамках заявки в ИС Cordis на ОНИТС СПД:'] = 'После выполнения подготовительных работ в рамках заявки в ИС Cordis на ОНИТС СПД:'
            hidden_vars[
                '- Установить на стороне %узел связи% и на стороне клиента беспроводные точки доступа %модель беспроводной базовой станции% по решению ОТПМ.'] = '- Установить на стороне %узел связи% и на стороне клиента беспроводные точки доступа %модель беспроводной базовой станции% по решению ОТПМ.'
            static_vars['модель беспроводной базовой станции'] = value_vars.get('access_point')
            hidden_vars['- Организовать %тип линии связи% от %узел связи% до беспроводной точки по решению ОТПМ.'] = '- Организовать %тип линии связи% от %узел связи% до беспроводной точки по решению ОТПМ.'
            hidden_vars['- На стороне клиента организовать медный патч-корд от WDA до клиентского коммутатора.'] = '- На стороне клиента организовать медный патч-корд от WDA до клиентского коммутатора.'
            hidden_vars[
                '- По заявке в ИС Cordis выделить реквизиты для управления беспроводными точками.'] = '- По заявке в ИС Cordis выделить реквизиты для управления беспроводными точками.'
            hidden_vars[
                '- Совместно с ОИПД подключить к СПД и запустить беспроводные станции (WDS/WDA).'] = '- Совместно с ОИПД подключить к СПД и запустить беспроводные станции (WDS/WDA).'
            static_vars['отдел ОИПМ / ОИПД'] = 'ОИПД'
            static_vars['тип линии связи'] = 'медную линию связи'
    elif value_vars.get('type_passage') == 'Перевод на гигабит' or value_vars.get('logic_change_gi_csw'):
        if value_vars.get('type_install_csw') not in ['Медная линия и порт не меняются', 'ВОЛС и порт не меняются']:
            old_kad = value_vars.get('head').split('\n')[4].split()[2]
            hidden_vars[
                '- Сообщить в ОЛИ СПД об освободившемся порте на %название коммутатора ранее используемого%.'] = '- Сообщить в ОЛИ СПД об освободившемся порте на %название коммутатора ранее используемого%.'
            static_vars['название коммутатора ранее используемого'] = old_kad
        static_vars['переносу/переводу на гигабит'] = 'переводу на гигабит'
        hidden_vars['- Актуализировать информацию в ИС Cordis и системах учета.'] = '- Актуализировать информацию в ИС Cordis и системах учета.'
        hidden_vars['Старый порт: порт %старый порт доступа на коммутаторе% коммутатора %название коммутатора ранее используемого%.'] = 'Старый порт: порт %старый порт доступа на коммутаторе% коммутатора %название коммутатора ранее используемого%.'
        static_vars['старый порт доступа на коммутаторе'] = value_vars.get('head').split('\n')[5].split()[2]
        static_vars['название коммутатора ранее используемого'] = value_vars.get('head').split('\n')[4].split()[2]
        hidden_vars['Новый порт: порт %порт доступа на коммутаторе% коммутатора %название коммутатора%.'] = 'Новый порт: порт %порт доступа на коммутаторе% коммутатора %название коммутатора%.'
        static_vars['порт доступа на коммутаторе'] = port
        hidden_vars[
            '- Сменить %режим работы магистрального порта/магистральный порт% на клиентском коммутаторе %название коммутатора клиентского%.'] = '- Сменить %режим работы магистрального порта/магистральный порт% на клиентском коммутаторе %название коммутатора клиентского%.'
        if value_vars.get('exist_sreda') == '1' or value_vars.get('exist_sreda') == '3':
            static_vars['режим работы магистрального порта/магистральный порт'] = 'магистральный порт'
        else:
            static_vars['режим работы магистрального порта/магистральный порт'] = 'режим работы магистрального порта'

        if value_vars.get('logic_change_csw') == True:
            hidden_vars['- Перенести в новое помещении клиента коммутатор %название коммутатора клиентского%.'] = '- Перенести в новое помещении клиента коммутатор %название коммутатора клиентского%.'
            hidden_vars['- Линии связи клиента переключить "порт в порт".'] = '- Линии связи клиента переключить "порт в порт".'

        if value_vars.get('head').split('\n')[3] == '- {}'.format(readable_pps) and (value_vars.get('exist_sreda_csw') == '2' or value_vars.get('exist_sreda_csw') == '4'):
            hidden_vars[
                '- Использовать существующую %тип линии связи% от %узел связи% до клиентcкого коммутатора.'] = '- Использовать существующую %тип линии связи% от %узел связи% до клиентcкого коммутатора.'
            hidden_vars[
                '- Переключить линию для клиента в порт %порт доступа на коммутаторе% коммутатора %название коммутатора%.'] = '- Переключить линию для клиента в порт %порт доступа на коммутаторе% коммутатора %название коммутатора%.'
            if value_vars.get('exist_sreda_csw') == '2':
                hidden_vars['- Установить на стороне %узел связи% %тип конвертера/передатчика на стороне узла доступа%'] = '- Установить на стороне %узел связи% %тип конвертера/передатчика на стороне узла доступа%'

        else:
            if value_vars.get('exist_sreda_csw') == '1' or value_vars.get('exist_sreda_csw') != value_vars.get('sreda'):
                hidden_vars['- В %название коммутатора клиентского% установить %тип конвертера/передатчика на стороне клиента%.'] = '- В %название коммутатора клиентского% установить %тип конвертера/передатчика на стороне клиента%.'
                hidden_vars['- Включить линию для клиента в порт %магистральный порт на клиентском коммутаторе% коммутатора %название коммутатора клиентского%.'] = '- Включить линию для клиента в порт %магистральный порт на клиентском коммутаторе% коммутатора %название коммутатора клиентского%.'

            if value_vars.get('exist_sreda_csw') == '2' or value_vars.get('exist_sreda_csw') == '4':
                hidden_vars[
                    '- Запросить ОНИТС СПД перенастроить режим работы магистрального порта на клиентском коммутаторе %название коммутатора клиентского%.'] = '- Запросить ОНИТС СПД перенастроить режим работы магистрального порта на клиентском коммутаторе %название коммутатора клиентского%.'
            hidden_vars[
                '- Организовать %тип линии связи% [от %узел связи% ]до клиентcкого коммутатора по решению ОТПМ.'] = '- Организовать %тип линии связи% [от %узел связи% ]до клиентcкого коммутатора по решению ОТПМ.'
            hidden_vars['от %узел связи% '] = 'от %узел связи% '
            hidden_vars[
                '- Подключить организованную линию для клиента в коммутатор %название коммутатора%, порт задействовать %порт доступа на коммутаторе%.'] = '- Подключить организованную линию для клиента в коммутатор %название коммутатора%, порт задействовать %порт доступа на коммутаторе%.'
            hidden_vars['- Установить на стороне %узел связи% %тип конвертера/передатчика на стороне узла доступа%'] = '- Установить на стороне %узел связи% %тип конвертера/передатчика на стороне узла доступа%'

        if sreda == '1':
            hidden_vars['от %узел связи% '] = 'от %узел связи% '
            static_vars['тип линии связи'] = 'медную линию связи'
        elif sreda == '2' or sreda == '4':
            hidden_vars['от %узел связи% '] = 'от %узел связи% '
            static_vars['тип линии связи'] = 'ВОЛС'

    stroka = templates.get("%Перенос/Перевод на гигабит% клиентского коммутатора.")
    result_services.append(analyzer_vars(stroka, static_vars, hidden_vars))
    return result_services, value_vars


def enviroment(result_services, value_vars):
    """Данный метод формирует блок ТТР отдельной линии(медь, волс, wifi)"""
    sreda = value_vars.get('sreda')
    ppr = value_vars.get('ppr')
    templates = value_vars.get('templates')
    readable_pps = _readable_node(value_vars.get('pps'))
    kad = value_vars.get('kad')
    port = value_vars.get('port')
    device_client = value_vars.get('device_client')
    device_pps = value_vars.get('device_pps')
    speed_port = value_vars.get('speed_port')
    access_point = value_vars.get('access_point')
    if sreda == '1':
        static_vars = {}
        hidden_vars = {}
        stroka = templates.get("Присоединение к СПД по медной линии связи.")
        static_vars['узел связи'] = readable_pps
        static_vars['название коммутатора'] = kad
        static_vars['порт доступа на коммутаторе'] = port
        static_vars['отдел ОИПМ / ОИПД'] = 'ОИПД'
        result_services.append(analyzer_vars(stroka, static_vars, hidden_vars))
        return result_services
    if sreda == '2' or sreda == '4':
        static_vars = {}
        if ppr:
            stroka = templates.get("Присоединение к СПД по оптической линии связи с простоем связи.")
            static_vars['№ заявки ППР'] = ppr
        else:
            stroka = templates.get("Присоединение к СПД по оптической линии связи.")
        hidden_vars = {}
        static_vars['узел связи'] = readable_pps
        static_vars['название коммутатора'] = kad
        static_vars['отдел ОИПМ / ОИПД'] = 'ОИПМ'
        static_vars['порт доступа на коммутаторе'] = port
        static_vars['режим работы порта доступа'] = speed_port
        static_vars['тип конвертера/передатчика на стороне узла доступа'] = device_pps
        static_vars['тип конвертера/передатчика на стороне клиента'] = device_client
        result_services.append(analyzer_vars(stroka, static_vars, hidden_vars))
        return result_services
    elif sreda == '3':
        static_vars = {}
        if ppr:
            stroka = templates.get("Присоединение к СПД по беспроводной среде передачи данных с простоем связи.")
            static_vars['№ заявки ППР'] = ppr
        else:
            stroka = templates.get("Присоединение к СПД по беспроводной среде передачи данных.")
        hidden_vars = {}
        static_vars['узел связи'] = readable_pps
        static_vars['название коммутатора'] = kad
        static_vars['порт доступа на коммутаторе'] = port
        static_vars['модель беспроводной базовой станции'] = access_point
        if access_point == 'Infinet E5':
            hidden_vars['- Доставить в офис ОНИТС СПД беспроводные точки Infinet E5 для их настройки.'] = '- Доставить в офис ОНИТС СПД беспроводные точки Infinet E5 для их настройки.'
            hidden_vars[' и настройки точек в офисе ОНИТС СПД'] = ' и настройки точек в офисе ОНИТС СПД'
        result_services.append(analyzer_vars(stroka, static_vars, hidden_vars))
        return result_services


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
    if value_vars.get('pass_job_services'):
        if value_vars.get('type_passage') == 'Перенос сервиса в новую точку':
            need.append(
                f"- перенести сервис {value_vars.get('name_passage_service')} в новую точку подключения {value_vars.get('address')};")
        elif value_vars.get('type_passage') == 'Перенос точки подключения':
            need.append(
                f"- перенести точку подключения на адрес {value_vars.get('address')};")
        elif value_vars.get('type_passage') == 'Перенос логического подключения' and value_vars.get(
                'change_log') == 'Порт и КАД не меняется':
            need.append(
                "- перенести трассу присоединения клиента;")
        elif value_vars.get('type_passage') == 'Восстановление трассы' and value_vars.get(
                'change_log') == 'Порт и КАД не меняется':
            need.append(
                "- восстановить трассу присоединения клиента;")
        elif value_vars.get('type_passage') == 'Перенос логического подключения' and value_vars.get(
                'change_log') == 'Порт/КАД меняются':
            if value_vars.get('spd') == 'РТК':
                need.append('перенести логическое подключение на ПМ РТК;')
            else:
                need.append(
                    f"- перенести логическое подключение на узел {_readable_node(value_vars.get('pps'))};")
        elif value_vars.get('type_passage') == 'Перевод на гигабит':
            need.append(
                f"- расширить полосу сервиса {value_vars.get('name_passage_service')};")
        elif not value_vars.get('type_passage') and 'Перенос Видеонаблюдение' in value_vars.get('type_pass'):
            need.append("- перенести сервис Видеонаблюдение;")
    if value_vars.get('new_job_services'):

        if len(value_vars.get('name_new_service')) > 1:
            need.append(f"- организовать дополнительные услуги {', '.join(value_vars.get('name_new_service'))};")
        else:
            need.append(f"- организовать дополнительную услугу {''.join(value_vars.get('name_new_service'))};")
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


def _passage_services(result_services, value_vars):
    """Данный метод формирует блок ТТР переноса сервиса"""
    templates = value_vars.get('templates')
    sreda = value_vars.get('sreda')
    readable_services = value_vars.get('readable_services')
    change_log_shpd = value_vars.get('change_log_shpd')
    static_vars = {}
    hidden_vars = {}
    if sreda == '2' or sreda == '4':
        static_vars['отдел ОИПМ / ОИПД'] = 'ОИПМ'
    else:
        static_vars['отдел ОИПМ / ОИПД'] = 'ОИПД'
    if value_vars.get('type_passage') == 'Перенос сервиса в новую точку' or value_vars.get('type_passage') == 'Перенос точки подключения':
        stroka = templates.get("Перенос ^сервиса^ %название сервиса% в новую физическую точку подключения.")
        if value_vars.get('type_passage') == 'Перенос точки подключения':
            if value_vars.get('change_log') != 'Порт и КАД не меняется':
                hidden_vars[
                    '-- перенести ^сервис^ %указать сервис% для клиента в новую точку подключения.'] = '-- перенести ^сервис^ %указать сервис% для клиента в новую точку подключения.'

                hidden_vars[
                    'В заявке ИС Cordis указать время проведения работ по переносу ^сервиса^.'] = 'В заявке ИС Cordis указать время проведения работ по переносу ^сервиса^.'
                hidden_vars[
                    '- После переезда клиента актуализировать информацию в ИС Cordis и системах учета.'] = '- После переезда клиента актуализировать информацию в ИС Cordis и системах учета.'
                hidden_vars[
                    '- Сообщить в ОЛИ СПД об освободившемся порте на коммутаторе %название коммутатора% после переезда клиента.'] = '- Сообщить в ОЛИ СПД об освободившемся порте на коммутаторе %название коммутатора% после переезда клиента.'
                static_vars['название коммутатора'] = value_vars.get('head').split('\n')[4].split()[2]
                if change_log_shpd == None:
                    change_log_shpd = 'существующая адресация'
                services, service_shpd_change = _separate_services_and_subnet_dhcp(readable_services, change_log_shpd)
                if service_shpd_change:
                    hidden_vars[', необходимость смены реквизитов'] = ', необходимость смены реквизитов'
                    hidden_vars['ОНИТС СПД подготовиться к работам:'] = 'ОНИТС СПД подготовиться к работам:'
                    hidden_vars['- По заявке в ИС Cordis выделить подсеть с маской %нов. маска IP-сети%.'] = '- По заявке в ИС Cordis выделить подсеть с маской %нов. маска IP-сети%.'
                    static_vars['нов. маска IP-сети'] = '/30' if value_vars.get('change_log_shpd') == 'Новая подсеть /30' else '/32'
                    hidden_vars['-- по согласованию с клиентом сменить реквизиты для услуги "ШПД в Интернет" на новую подсеть с маской %нов. маска IP-сети%.'] = '-- по согласованию с клиентом сменить реквизиты для услуги "ШПД в Интернет" на новую подсеть с маской %нов. маска IP-сети%.'
                    hidden_vars['- После смены реквизитов:'] = '- После смены реквизитов:'
                    hidden_vars['- разобрать ресурс %ресурс на договоре% на договоре.'] = '- разобрать ресурс %ресурс на договоре% на договоре.'
                    static_vars['ресурс на договоре'] = ', '.join(service_shpd_change)
                if 'ЦКС' in ', '.join(services):
                    hidden_vars[
                        '- Ограничить скорость и настроить маркировку трафика для ^сервиса^ %название сервиса% %L2. точка ограничения и маркировки трафика%.'] = '- Ограничить скорость и настроить маркировку трафика для ^сервиса^ ЦКС %L2. точка ограничения и маркировки трафика%.'
                    static_vars['L2. точка ограничения и маркировки трафика'] = value_vars.get('extend_policer_cks_vk')
                if 'ВЛС' in ', '.join(services):
                    hidden_vars[
                        '- Ограничить скорость и настроить маркировку трафика для ^сервиса^ %название сервиса% %L2. точка ограничения и маркировки трафика%.'] = '- Ограничить скорость и настроить маркировку трафика для ^сервиса^ порт ВЛС %L2. точка ограничения и маркировки трафика%.'
                    static_vars['L2. точка ограничения и маркировки трафика'] = value_vars.get('extend_policer_cks_vk')
                if 'ВМ' in ', '.join(services):
                    hidden_vars[
                        '- Ограничить скорость и настроить маркировку трафика для ^сервиса^ %название сервиса% %L3. точка ограничения и маркировки трафика%.'] = '- Ограничить скорость и настроить маркировку трафика для ^сервиса^ порт ВМ %L3. точка ограничения и маркировки трафика%.'
                    static_vars['L3. точка ограничения и маркировки трафика'] = value_vars.get('extend_policer_vm')
                service = 'Exist dhcp' if static_vars.get('нов. маска IP-сети') == '/32' else 'Exist not dhcp'
                add_hidden_vars, add_static_vars = _get_pm_vars(value_vars, service)
                static_vars.update(add_static_vars)
                hidden_vars.update(add_hidden_vars)
            else:
                services = []
                for key, value in readable_services.items():
                    if key != '"Телефония"':
                        if type(value) == str:
                            services.append(key + ' ' + value)
                        elif type(value) == list:
                            services.append(key + ''.join(value))
            static_vars['указать сервис'] = ', '.join(services)
            static_vars['название сервиса'] = ', '.join([x for x in readable_services.keys() if x != '"Телефония"'])
            stroka = analyzer_vars(stroka, static_vars, hidden_vars)
            counter_plur = len(services)
            result_services.append(pluralizer_vars(stroka, counter_plur))
        elif value_vars.get('type_passage') == 'Перенос сервиса в новую точку':
            services = []
            other_services = []
            for key, value in readable_services.items():
                if type(value) == str:
                    if value_vars.get('selected_ono')[0][-4] in value:
                        services.append(key + ' ' + value)
                        static_vars['название сервиса'] = key
                        value_vars.update({'name_passage_service': key +' '+ value })
                    else:
                        other_services.append(key + ' ' + value)

                elif type(value) == list:
                    for val in value:
                        if value_vars.get('selected_ono')[0][-4] in val:
                            services.append(key + ' ' + val)
                            static_vars['название сервиса'] = key
                            value_vars.update({'name_passage_service': key +' '+ val})
                        else:
                            other_services.append(key + ' ' + val)

            if value_vars.get('change_log') != 'Порт и КАД не меняется':
                hidden_vars[
                    '-- перенести ^сервис^ %указать сервис% для клиента в новую точку подключения.'] = '-- перенести ^сервис^ %указать сервис% для клиента в новую точку подключения.'

                hidden_vars[
                    'В заявке ИС Cordis указать время проведения работ по переносу ^сервиса^.'] = 'В заявке ИС Cordis указать время проведения работ по переносу ^сервиса^.'
                hidden_vars[
                    '- После переезда клиента актуализировать информацию в ИС Cordis и системах учета.'] = '- После переезда клиента актуализировать информацию в ИС Cordis и системах учета.'
                if value_vars.get('head').split('\n')[4].split()[2] == value_vars.get('selected_ono')[0][-2] or other_services == False:
                    hidden_vars[
                    '- Сообщить в ОЛИ СПД об освободившемся порте на коммутаторе %название коммутатора% после переезда клиента.'] = '- Сообщить в ОЛИ СПД об освободившемся порте на коммутаторе %название коммутатора% после переезда клиента.'
                static_vars['название коммутатора'] = value_vars.get('head').split('\n')[4].split()[2]

                if 'ЦКС' in static_vars['название сервиса'] or 'ВЛС' in static_vars['название сервиса']:
                    hidden_vars[
                        '- Ограничить скорость и настроить маркировку трафика для ^сервиса^ %название сервиса% %L2. точка ограничения и маркировки трафика%.'] = '- Ограничить скорость и настроить маркировку трафика для ^сервиса^ %название сервиса% %L2. точка ограничения и маркировки трафика%.'
                    static_vars['L2. точка ограничения и маркировки трафика'] = value_vars.get('extend_policer_cks_vk')
                if 'ВМ' in static_vars['название сервиса']:
                    hidden_vars[
                        '- Ограничить скорость и настроить маркировку трафика для ^сервиса^ %название сервиса% %L3. точка ограничения и маркировки трафика%.'] = '- Ограничить скорость и настроить маркировку трафика для ^сервиса^ %название сервиса% %L3. точка ограничения и маркировки трафика%.'
                    static_vars['L3. точка ограничения и маркировки трафика'] = value_vars.get('extend_policer_vm')
                if services[0].startswith('"ШПД в интернет"'):
                    if value_vars.get('change_log_shpd') != 'существующая адресация':
                        hidden_vars[', необходимость смены реквизитов'] = ', необходимость смены реквизитов'
                        hidden_vars['ОНИТС СПД подготовиться к работам:'] = 'ОНИТС СПД подготовиться к работам:'
                        hidden_vars['- По заявке в ИС Cordis выделить подсеть с маской %нов. маска IP-сети%.'] = '- По заявке в ИС Cordis выделить подсеть с маской %нов. маска IP-сети%.'
                        static_vars['нов. маска IP-сети'] = '/30' if value_vars.get('change_log_shpd') == 'Новая подсеть /30' else '/32'
                        static_vars['указать сервис'] = static_vars['название сервиса']
                        hidden_vars['-- по согласованию с клиентом сменить реквизиты для услуги "ШПД в Интернет" на новую подсеть с маской %нов. маска IP-сети%.'] = '-- по согласованию с клиентом сменить реквизиты для услуги "ШПД в Интернет" на новую подсеть с маской %нов. маска IP-сети%.'
                        hidden_vars['- После смены реквизитов:'] = '- После смены реквизитов:'
                        hidden_vars['- разобрать ресурс %ресурс на договоре% на договоре.'] = '- разобрать ресурс %ресурс на договоре% на договоре.'
                        static_vars['ресурс на договоре'] = value_vars.get('selected_ono')[0][-4]
                    else:
                        static_vars['указать сервис'] = ', '.join(services)
                else:
                    static_vars['указать сервис'] = ', '.join(services)


                service = 'Exist dhcp' if static_vars.get('нов. маска IP-сети') == '/32' else 'Exist not dhcp'
                add_hidden_vars, add_static_vars = _get_pm_vars(value_vars, service)
                static_vars.update(add_static_vars)
                hidden_vars.update(add_hidden_vars)
            else:
                static_vars['указать сервис'] = ', '.join(services)
            stroka = analyzer_vars(stroka, static_vars, hidden_vars)
            counter_plur = len(services)
            result_services.append(pluralizer_vars(stroka, counter_plur))
    elif value_vars.get('type_passage') == 'Перенос логического подключения':
        stroka = templates.get("Перенос ^сервиса^ %название сервиса% в новую логическую точку подключения.")
        if value_vars.get('type_ticket') == 'ПТО':
            pass
        else:
            hidden_vars['МКО:'] = 'МКО:'
            hidden_vars['- Проинформировать клиента о простое сервиса на время проведения работ.'] = '- Проинформировать клиента о простое сервиса на время проведения работ.'
            hidden_vars['- Согласовать время проведение работ.'] = '- Согласовать время проведение работ.'
            hidden_vars['- Создать заявку в ИС Cordis на ОНИТС СПД для изменения логического подключения ^сервиса^ %указать сервис% клиента.'] = '- Создать заявку в ИС Cordis на ОНИТС СПД для изменения логического подключения ^сервиса^ %указать сервис% клиента.'
        services = []
        service_shpd_change = []
        for key, value in readable_services.items():
            if type(value) == str:
                if 'ШПД' in key and '/32' in value:
                    service_shpd_change.append(value)
                    services.append(key)
                else:
                    services.append(key + ' ' + value)
            elif type(value) == list:
                if 'ШПД' in key:
                    for val in value:
                        if '/32' in val:
                            len_index = len(' c реквизитами ')
                            subnet_clear = value[len_index:]
                            service_shpd_change.append(subnet_clear)
                            if len(value) == len(service_shpd_change):
                                services.append(key)
                        else:
                            services.append(key + ''.join(value))
                else:
                    services.append(key + ''.join(value))
        if 'ЦКС' in ', '.join(services):
            hidden_vars[
                '- Ограничить скорость и настроить маркировку трафика для ^сервиса^ %название сервиса% %L2. точка ограничения и маркировки трафика%.'] = '- Ограничить скорость и настроить маркировку трафика для ^сервиса^ ЦКС %L2. точка ограничения и маркировки трафика%.'
            static_vars['L2. точка ограничения и маркировки трафика'] = value_vars.get('extend_policer_cks_vk')
        if 'ВЛС' in ', '.join(services):
            hidden_vars[
                '- Ограничить скорость и настроить маркировку трафика для ^сервиса^ %название сервиса% %L2. точка ограничения и маркировки трафика%.'] = '- Ограничить скорость и настроить маркировку трафика для ^сервиса^ порт ВЛС %L2. точка ограничения и маркировки трафика%.'
            static_vars['L2. точка ограничения и маркировки трафика'] = value_vars.get('extend_policer_cks_vk')
        if 'ВМ' in ', '.join(services):
            hidden_vars[
                '- Ограничить скорость и настроить маркировку трафика для ^сервиса^ %название сервиса% %L3. точка ограничения и маркировки трафика%.'] = '- Ограничить скорость и настроить маркировку трафика для ^сервиса^ порт ВМ %L3. точка ограничения и маркировки трафика%.'
            static_vars['L3. точка ограничения и маркировки трафика'] = value_vars.get('extend_policer_vm')
        if service_shpd_change and value_vars.get('change_log_shpd') != 'существующая адресация':
            if value_vars.get('type_ticket') != 'ПТО':
                hidden_vars['- Согласовать необходимость смены реквизитов.'] = '- Согласовать необходимость смены реквизитов.'
            hidden_vars[
                '- По заявке в ИС Cordis выделить подсеть с маской %нов. маска IP-сети%.'] = '- По заявке в ИС Cordis выделить подсеть с маской %нов. маска IP-сети%.'
            static_vars['нов. маска IP-сети'] = '/30' if value_vars.get(
                'change_log_shpd') == 'Новая подсеть /30' else '/32'
            hidden_vars[
                '- По согласованию с клиентом сменить реквизиты для услуги "ШПД в Интернет" на новую подсеть с маской %нов. маска IP-сети%.'] = '- По согласованию с клиентом сменить реквизиты для услуги "ШПД в Интернет" на новую подсеть с маской %нов. маска IP-сети%.'
            hidden_vars['- После смены реквизитов:'] = '- После смены реквизитов:'
            hidden_vars['- разобрать ресурс %ресурс на договоре% на договоре.'] = '- разобрать ресурс %ресурс на договоре% на договоре.'
            static_vars['ресурс на договоре'] = ', '.join(service_shpd_change)
        static_vars['указать сервис'] = ', '.join(services)
        static_vars['название сервиса'] = ', '.join(readable_services.keys())
        

        service = 'Exist dhcp' if static_vars.get('нов. маска IP-сети') == '/32' else 'Exist not dhcp'
        add_hidden_vars, add_static_vars = _get_pm_vars(value_vars, service)
        static_vars.update(add_static_vars)
        hidden_vars.update(add_hidden_vars)
        if value_vars.get('spd') == 'РТК':
            static_vars['узел связи'] = 'ПМ РТК'
        else:
            static_vars['узел связи'] = _readable_node(value_vars.get('pps'))
        static_vars['название коммутатора'] = value_vars.get('head').split('\n')[4].split()[2]
        stroka = analyzer_vars(stroka, static_vars, hidden_vars)
        counter_plur = len(services)
        result_services.append(pluralizer_vars(stroka, counter_plur))
    elif value_vars.get('type_passage') == 'Перевод на гигабит':
        stroka = templates.get("Расширение полосы сервиса %название сервиса%.")
        desc_service, name_passage_service = get_selected_readable_service(readable_services, value_vars.get('selected_ono'))
        static_vars['название сервиса'] = desc_service
        if desc_service == '"ШПД в интернет"':
            hidden_vars['- Расширить полосу ШПД в ИС Cordis.'] = '- Расширить полосу ШПД в ИС Cordis.'
            if value_vars.get('change_log_shpd') != 'существующая адресация':
                hidden_vars[', необходимость смены реквизитов'] = ', необходимость смены реквизитов'
                hidden_vars[
                    '- Выделить подсеть с маской %нов. маска IP-сети%.'] = '- Выделить подсеть с маской %нов. маска IP-сети%.'
                static_vars['нов. маска IP-сети'] = '/30' if value_vars.get(
                    'change_log_shpd') == 'Новая подсеть /30' else '/32'
                static_vars['указать сервис'] = static_vars['название сервиса']
                hidden_vars[
                    '-- по согласованию с клиентом сменить реквизиты для услуги "ШПД в Интернет" на новую подсеть с маской %нов. маска IP-сети%.'] = '-- по согласованию с клиентом сменить реквизиты для услуги "ШПД в Интернет" на новую подсеть с маской %нов. маска IP-сети%.'
                hidden_vars['- После смены реквизитов:'] = '- После смены реквизитов:'
                hidden_vars[
                    '- разобрать ресурс %ресурс на договоре% на договоре.'] = '- разобрать ресурс %ресурс на договоре% на договоре.'
                static_vars['ресурс на договоре'] = value_vars.get('selected_ono')[0][-4]
            else:
                static_vars['указать сервис'] = name_passage_service
        else:
            hidden_vars['на %пропускная способность%'] = 'на %пропускная способность%'
            static_vars['пропускная способность'] = value_vars.get('extend_speed')
            hidden_vars[
                '- Ограничить скорость и настроить маркировку трафика для %указать сервис% %L2. точка ограничения и маркировки трафика%.'] = '- Ограничить скорость и настроить маркировку трафика для %указать сервис% %L2. точка ограничения и маркировки трафика%.'
            if value_vars.get('extend_policer_cks_vk'):
                static_vars['L2. точка ограничения и маркировки трафика'] = value_vars.get('extend_policer_cks_vk')
            if value_vars.get('extend_policer_vm'):
                static_vars['L2. точка ограничения и маркировки трафика'] = value_vars.get('extend_policer_vm')
            static_vars['указать сервис'] = name_passage_service
        hidden_vars['ОНИТС СПД подготовка к работам:'] = 'ОНИТС СПД подготовка к работам:'
        hidden_vars['- По заявке в ИС Cordis подготовить настройки на оборудовании для расширения сервиса %указать сервис% [на %пропускная способность%].'] = '- По заявке в ИС Cordis подготовить настройки на оборудовании для расширения сервиса %указать сервис% [на %пропускная способность%].'

        hidden_vars['- Проинформировать клиента о простое сервиса на время проведения работ.'] = '- Проинформировать клиента о простое сервиса на время проведения работ.'
        hidden_vars['- Согласовать время проведение работ[, необходимость смены реквизитов].'] = '- Согласовать время проведение работ[, необходимость смены реквизитов].'
        hidden_vars['-- сопроводить работы %отдел ОИПМ / ОИПД% по перенесу сервиса %указать сервис% в гигабитный порт %название коммутатора%.'] = '-- сопроводить работы %отдел ОИПМ / ОИПД% по перенесу сервиса %указать сервис% в гигабитный порт %название коммутатора%.'
        value_vars.update({'name_passage_service': name_passage_service})
        static_vars['название коммутатора'] = value_vars.get('kad')
        if value_vars.get('selected_ono')[0][-2].startswith('CSW') or value_vars.get('selected_ono')[0][-2].startswith('WDA'):
            pass
        else:
            hidden_vars['- Сообщить в ОЛИ СПД об освободившемся порте на %название коммутатора ранее используемого%.'] = '- Сообщить в ОЛИ СПД об освободившемся порте на %название коммутатора ранее используемого%.'
        static_vars['название коммутатора ранее используемого'] = value_vars.get('head').split('\n')[4].split()[2]
        result_services.append(analyzer_vars(stroka, static_vars, hidden_vars))
    return result_services, value_vars


def _passage_phone_service(result_services, value_vars):
    """Данный метод формирует блоки ТТР для переноса аналоговой телефонии"""
    service = value_vars.get('phone_in_pass')
    result_services_ots = []
    hidden_vars = {}
    static_vars = {}
    vgw = value_vars.get('vgw')
    ports_vgw = value_vars.get('ports_vgw')
    phone_lines = sum([int(k) * v for k, v in value_vars.get('channels').items()])
    templates = value_vars.get('templates')
    if service.endswith('|'):
        if value_vars.get('type_phone') == 'ak':
            if value_vars.get('logic_csw'):
                result_services.append(enviroment_csw(value_vars))
                value_vars.update({'result_services': result_services})
                static_vars[
                        'название коммутатора'] = 'клиентского коммутатора'
            else:
                result_services = enviroment(result_services, value_vars)
                value_vars.update({'result_services': result_services})
                static_vars['название коммутатора'] = value_vars.get(
                        'kad')
            stroka = templates.get("Установка тел. шлюза на стороне клиента.")
            static_vars['модель тел. шлюза'] = vgw
            if vgw in ['D-Link DVG-5402SP', 'Eltex RG-1404G или Eltex TAU-4M.IP', 'Eltex TAU-8.IP']:
                static_vars['магистральный порт на тел. шлюзе'] = 'WAN порт'
            else:
                static_vars['магистральный порт на тел. шлюзе'] = 'Ethernet Порт 0'
                static_vars['модель тел. шлюза'] = vgw + ' c кабелем для коммутации в плинт'
            result_services_ots.append(analyzer_vars(stroka, static_vars, hidden_vars))
            stroka = templates.get(
                    "Перенос сервиса Телефония на тел. шлюз на стороне клиента.")
            static_vars['название тел. шлюза'] = 'установленный по решению выше'
            static_vars['модель тел. шлюза'] = vgw
            static_vars['список тел. шлюзов'] = value_vars.get('old_name_model_vgws')
            if 'ватс' in service.lower():
                static_vars['количество линий'] = ports_vgw
                counter_plur = int(ports_vgw)
                if ports_vgw == '1':
                    static_vars['порт доступа на тел. шлюзе'] = '1'
                else:
                    static_vars['порт доступа на тел. шлюзе'] = '1-{}'.format(ports_vgw)
            else:
                static_vars['количество линий'] = str(phone_lines)
                counter_plur = phone_lines
                if phone_lines == 1:
                    static_vars['порт доступа на тел. шлюзе'] = '1'
                else:
                    static_vars['порт доступа на тел. шлюзе'] = '1-{}'.format(phone_lines)
            stroka = analyzer_vars(stroka, static_vars, hidden_vars)
            result_services_ots.append(pluralizer_vars(stroka, counter_plur))
    elif service.endswith('/'):
        stroka = templates.get("Установка тел. шлюза на ППС.")
        static_vars['модель тел. шлюза'] = vgw
        static_vars['узел связи'] = value_vars.get('pps')
        result_services_ots.append(analyzer_vars(stroka, static_vars, hidden_vars))
        stroka = templates.get("Перенос сервиса Телефония на тел. шлюз на ППС.")
        static_vars['название тел. шлюза'] = 'установленный по решению выше'
        static_vars['список тел. шлюзов'] = value_vars.get('old_name_model_vgws')
        if 'ватс' in service.lower():
            static_vars['количество линий'] = ports_vgw
            counter_plur = int(ports_vgw)
            if ports_vgw == '1':
                static_vars['порт доступа на тел. шлюзе'] = '1'
            else:
                static_vars['порт доступа на тел. шлюзе'] = '1-{}'.format(ports_vgw)
        else:
            static_vars['количество линий'] = str(phone_lines)
            counter_plur = phone_lines
            if phone_lines == 1:
                static_vars['порт доступа на тел. шлюзе'] = '1'
            else:
                static_vars['порт доступа на тел. шлюзе'] = '1-{}'.format(phone_lines)
        stroka = analyzer_vars(stroka, static_vars, hidden_vars)
        result_services_ots.append(pluralizer_vars(stroka, counter_plur))
    elif service.endswith('\\'):
        stroka = templates.get("Перенос сервиса Телефония на тел. шлюз на ППС.")
        static_vars['список тел. шлюзов'] = value_vars.get('old_name_model_vgws')
        static_vars['порт доступа на тел. шлюзе'] = value_vars.get('form_exist_vgw_port')
        static_vars['модель тел. шлюза'] = value_vars.get('form_exist_vgw_model')
        static_vars['название тел. шлюза'] = value_vars.get('form_exist_vgw_name')
        if 'ватс' in service.lower():
            static_vars['количество линий'] = ports_vgw
            counter_plur = int(ports_vgw)
        else:
            static_vars['количество линий'] = str(phone_lines)
            counter_plur = phone_lines
        stroka = analyzer_vars(stroka, static_vars, hidden_vars)
        result_services_ots.append(pluralizer_vars(stroka, counter_plur))
    return result_services, result_services_ots, value_vars


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


def _passage_enviroment(value_vars):
    """Данный метод формирует блок ТТР для изменение присоединения к СПД"""
    if value_vars.get('result_services'):
        result_services = value_vars.get('result_services')
    else:
        result_services = []
    sreda = value_vars.get('sreda')
    templates = value_vars.get('templates')
    readable_pps = _readable_node(value_vars.get('pps'))
    port = value_vars.get('port')
    device_pps = value_vars.get('device_pps')
    selected_ono = value_vars.get('selected_ono')
    if 'Порт и КАД не меняется' == value_vars.get('change_log'):
        kad = value_vars.get('selected_ono')[0][-2]
    else:
        kad = value_vars.get('kad')
    stroka = templates.get("Изменение присоединения к СПД.")
    static_vars = {}
    hidden_vars = {}
    if sreda == '2' or sreda == '4':
        static_vars['отдел ОИПМ / ОИПД'] = 'ОИПМ'
    else:
        static_vars['отдел ОИПМ / ОИПД'] = 'ОИПД'
    if value_vars.get('type_passage') == 'Перенос сервиса в новую точку' or value_vars.get('type_passage') == 'Перенос точки подключения':
        if value_vars.get('change_log') == 'Порт и КАД не меняется':
            hidden_vars['- Организовать %тип линии связи% [от %узел связи% ]до клиентcкого оборудования [в новой точке подключения ]по решению ОАТТР.'] = '- Организовать %тип линии связи% [от %узел связи% ]до клиентcкого оборудования [в новой точке подключения ]по решению ОАТТР.'
            if value_vars.get('exist_sreda') == '1':
                static_vars['тип линии связи'] = 'медную линию связи'
            else:
                static_vars['тип линии связи'] = 'ВОЛС'
            hidden_vars['в новой точке подключения '] = 'в новой точке подключения '
            hidden_vars['- Логическое подключение клиента не изменится.'] = '- Логическое подключение клиента не изменится.'
        elif value_vars.get('change_log') == 'Порт/КАД меняются':
            hidden_vars[
                '- Организовать %тип линии связи% [от %узел связи% ]до клиентcкого оборудования [в новой точке подключения ]по решению ОАТТР.'] = '- Организовать %тип линии связи% [от %узел связи% ]до клиентcкого оборудования [в новой точке подключения ]по решению ОАТТР.'
            if sreda == '1':
                static_vars['тип линии связи'] = 'медную линию связи'
            else:
                static_vars['тип линии связи'] = 'ВОЛС'
                hidden_vars['- Установить на стороне %узел связи% %тип конвертера/передатчика на стороне узла доступа%'] = '- Установить на стороне %узел связи% %тип конвертера/передатчика на стороне узла доступа%'
                static_vars['узел связи'] = readable_pps
                static_vars['тип конвертера/передатчика на стороне узла доступа'] = device_pps
                hidden_vars['ОНИТС СПД проведение работ:'] = 'ОНИТС СПД проведение работ:'
                hidden_vars['- На порту подключения клиента выставить скоростной режим %режим работы порта доступа%.'] = '- На порту подключения клиента выставить скоростной режим %режим работы порта доступа%.'
                static_vars['режим работы порта доступа'] = value_vars.get('speed_port')
            hidden_vars['от %узел связи% '] = 'от %узел связи% '
            static_vars['узел связи'] = readable_pps
            hidden_vars['в новой точке подключения '] = 'в новой точке подключения '
            hidden_vars['- Подключить организованную линию для клиента в коммутатор %название коммутатора%, порт задействовать %порт доступа на коммутаторе%.'] = '- Подключить организованную линию для клиента в коммутатор %название коммутатора%, порт задействовать %порт доступа на коммутаторе%.'
            static_vars['название коммутатора'] = kad
            static_vars['порт доступа на коммутаторе'] = port
            hidden_vars['Старый порт: порт %старый порт доступа на коммутаторе% коммутатора %название коммутатора ранее используемого%.'] = 'Старый порт: порт %старый порт доступа на коммутаторе% коммутатора %название коммутатора ранее используемого%.'
            static_vars['старый порт доступа на коммутаторе'] = selected_ono[0][-1]
            static_vars['название коммутатора ранее используемого'] = selected_ono[0][-2]
            hidden_vars['Новый порт: порт %порт доступа на коммутаторе% коммутатора %название коммутатора%.'] = 'Новый порт: порт %порт доступа на коммутаторе% коммутатора %название коммутатора%.'
            static_vars['порт доступа на коммутаторе'] = port
            static_vars['название коммутатора'] = kad
    elif value_vars.get('type_passage') == 'Перенос логического подключения':
        if value_vars.get('type_ticket') == 'ПТО':
            hidden_vars['ОИПМ подготовиться к работам:'] = 'ОИПМ подготовиться к работам:'
            hidden_vars['- Согласовать проведение работ - ППР %№ заявки ППР%.'] = '- Согласовать проведение работ - ППР %№ заявки ППР%.'
            static_vars['№ заявки ППР'] = value_vars.get('ppr')
            hidden_vars['- Создать заявку в ИС Cordis на ОНИТС СПД для изменения присоединения клиента.'] = '- Создать заявку в ИС Cordis на ОНИТС СПД для изменения присоединения клиента.'
        hidden_vars[
            '- Организовать %тип линии связи% [от %узел связи% ]до клиентcкого оборудования [в новой точке подключения ]по решению ОАТТР.'] = '- Организовать %тип линии связи% [от %узел связи% ]до клиентcкого оборудования [в новой точке подключения ]по решению ОАТТР.'
        hidden_vars['от %узел связи% '] = 'от %узел связи% '
        static_vars['узел связи'] = readable_pps
        hidden_vars['- Подключить организованную линию для клиента в коммутатор %название коммутатора%, порт задействовать %порт доступа на коммутаторе%.'] = '- Подключить организованную линию для клиента в коммутатор %название коммутатора%, порт задействовать %порт доступа на коммутаторе%.'
        static_vars['название коммутатора'] = kad
        static_vars['порт доступа на коммутаторе'] = port
        hidden_vars[
            'Старый порт: порт %старый порт доступа на коммутаторе% коммутатора %название коммутатора ранее используемого%.'] = 'Старый порт: порт %старый порт доступа на коммутаторе% коммутатора %название коммутатора ранее используемого%.'
        static_vars['старый порт доступа на коммутаторе'] = selected_ono[0][-1]
        static_vars['название коммутатора ранее используемого'] = selected_ono[0][-2]
        hidden_vars[
            'Новый порт: порт %порт доступа на коммутаторе% коммутатора %название коммутатора%.'] = 'Новый порт: порт %порт доступа на коммутаторе% коммутатора %название коммутатора%.'
        if sreda == '1':
            static_vars['тип линии связи'] = 'медную линию связи'
        elif sreda == '2' or sreda == '4':
            static_vars['тип линии связи'] = 'ВОЛС'
            hidden_vars['- Установить на стороне %узел связи% %тип конвертера/передатчика на стороне узла доступа%'] = '- Установить на стороне %узел связи% %тип конвертера/передатчика на стороне узла доступа%'
            static_vars['тип конвертера/передатчика на стороне узла доступа'] = value_vars.get('device_pps')
            hidden_vars['ОНИТС СПД проведение работ:'] = 'ОНИТС СПД проведение работ:'
            hidden_vars[
                '- На порту подключения клиента выставить скоростной режим %режим работы порта доступа%.'] = '- На порту подключения клиента выставить скоростной режим %режим работы порта доступа%.'
            static_vars['режим работы порта доступа'] = value_vars.get('speed_port')
            if value_vars.get('exist_sreda') != '2':
                hidden_vars['- На стороне клиента %вид работ% [%установленный тип конвертера/передатчика на стороне клиента% на ]%тип конвертера/передатчика на стороне клиента%'] = '- На стороне клиента %вид работ% [%установленный тип конвертера/передатчика на стороне клиента% на ]%тип конвертера/передатчика на стороне клиента%'
                static_vars['вид работ'] = 'установить'
                static_vars['тип конвертера/передатчика на стороне клиента'] = value_vars.get('device_client')
    elif value_vars.get('type_passage') == 'Перевод на гигабит':
        static_vars['тип линии связи'] = 'ВОЛС'
        static_vars['узел связи'] = readable_pps
        static_vars['название коммутатора'] = kad
        static_vars['порт доступа на коммутаторе'] = port
        hidden_vars['ОНИТС СПД проведение работ:'] = 'ОНИТС СПД проведение работ:'
        hidden_vars[
            '- На порту подключения клиента выставить скоростной режим %режим работы порта доступа%.'] = '- На порту подключения клиента выставить скоростной режим %режим работы порта доступа%.'
        static_vars['режим работы порта доступа'] = value_vars.get('speed_port')
        hidden_vars[
            '- На стороне клиента %вид работ% [%установленный тип конвертера/передатчика на стороне клиента% на ]%тип конвертера/передатчика на стороне клиента%'] = '- На стороне клиента %вид работ% [%установленный тип конвертера/передатчика на стороне клиента% на ]%тип конвертера/передатчика на стороне клиента%'
        if value_vars.get('head').split('\n')[3] == '- {}'.format(readable_pps) and value_vars.get('exist_sreda') == '2':
            hidden_vars['- Использовать существующую %тип линии связи% от %узел связи% до клиентского оборудования.'] = '- Использовать существующую %тип линии связи% от %узел связи% до клиентского оборудования.'
            hidden_vars['- Переключить линию для клиента в порт %порт доступа на коммутаторе% коммутатора %название коммутатора%.'] = '- Переключить линию для клиента в порт %порт доступа на коммутаторе% коммутатора %название коммутатора%.'
            static_vars['вид работ'] = 'заменить'
            hidden_vars[
                '%установленный тип конвертера/передатчика на стороне клиента% на '] = '%установленный тип конвертера/передатчика на стороне клиента% на '
            static_vars['установленный тип конвертера/передатчика на стороне клиента'] = '100 Мбит/с конвертер с длиной волны 1550 нм, дальность до 20 км, режим работы "auto"'
            static_vars['тип конвертера/передатчика на стороне узла доступа'] = value_vars.get('device_pps')
            static_vars['тип конвертера/передатчика на стороне клиента'] = value_vars.get('device_client')
            hidden_vars[
                '- Установить на стороне %узел связи% %тип конвертера/передатчика на стороне узла доступа%'] = '- Установить на стороне %узел связи% %тип конвертера/передатчика на стороне узла доступа%'
            hidden_vars[
                'Старый порт: порт %старый порт доступа на коммутаторе% коммутатора %название коммутатора ранее используемого%.'] = 'Старый порт: порт %старый порт доступа на коммутаторе% коммутатора %название коммутатора ранее используемого%.'
            static_vars['старый порт доступа на коммутаторе'] = selected_ono[0][-1]
            static_vars['название коммутатора ранее используемого'] = selected_ono[0][-2]
            hidden_vars[
                'Новый порт: порт %порт доступа на коммутаторе% коммутатора %название коммутатора%.'] = 'Новый порт: порт %порт доступа на коммутаторе% коммутатора %название коммутатора%.'
        elif value_vars.get('head').split('\n')[3] == '- {}'.format(readable_pps) and value_vars.get('exist_sreda') == '4':
            hidden_vars['- Использовать существующую %тип линии связи% от %узел связи% до клиентского оборудования.'] = '- Использовать существующую %тип линии связи% от %узел связи% до клиентского оборудования.'
            static_vars['вид работ'] = 'заменить'
            hidden_vars['%установленный тип конвертера/передатчика на стороне клиента% на '] = '%установленный тип конвертера/передатчика на стороне клиента% на '
            static_vars['установленный тип конвертера/передатчика на стороне клиента'] = '100 Мбит/с конвертер с длиной волны 1550 нм, дальность до 20 км, режим работы "auto"'
            hidden_vars['- Логическое подключение клиента не изменится.'] = '- Логическое подключение клиента не изменится.'
            static_vars['тип конвертера/передатчика на стороне клиента'] = '1000 Мбит/с конвертер с модулем SFP WDM с длиной волны 1550 нм, дальность до 3 км, режим работы "AUTO/CVT"'
        else:
            hidden_vars[
                '- Организовать %тип линии связи% [от %узел связи% ]до клиентcкого оборудования [в новой точке подключения ]по решению ОАТТР.'] = '- Организовать %тип линии связи% [от %узел связи% ]до клиентcкого оборудования [в новой точке подключения ]по решению ОАТТР.'
            hidden_vars['от %узел связи% '] = 'от %узел связи% '
            hidden_vars[
                '- Подключить организованную линию для клиента в коммутатор %название коммутатора%, порт задействовать %порт доступа на коммутаторе%.'] = '- Подключить организованную линию для клиента в коммутатор %название коммутатора%, порт задействовать %порт доступа на коммутаторе%.'
            static_vars['вид работ'] = 'установить'
            static_vars['тип конвертера/передатчика на стороне узла доступа'] = value_vars.get('device_pps')
            hidden_vars[
                '- Установить на стороне %узел связи% %тип конвертера/передатчика на стороне узла доступа%'] = '- Установить на стороне %узел связи% %тип конвертера/передатчика на стороне узла доступа%'
            hidden_vars[
                'Старый порт: порт %старый порт доступа на коммутаторе% коммутатора %название коммутатора ранее используемого%.'] = 'Старый порт: порт %старый порт доступа на коммутаторе% коммутатора %название коммутатора ранее используемого%.'
            static_vars['старый порт доступа на коммутаторе'] = selected_ono[0][-1]
            static_vars['название коммутатора ранее используемого'] = selected_ono[0][-2]
            static_vars['тип конвертера/передатчика на стороне клиента'] = value_vars.get('device_client')
            hidden_vars[
                'Новый порт: порт %порт доступа на коммутаторе% коммутатора %название коммутатора%.'] = 'Новый порт: порт %порт доступа на коммутаторе% коммутатора %название коммутатора%.'
    value_vars.update({'kad': kad})
    result_services.append(analyzer_vars(stroka, static_vars, hidden_vars))
    return result_services, value_vars


def _passage_services_on_csw(result_services, value_vars):
    """Данный метод формирует блоки ТТР перенос сервиса на КК и организации медной линии от КК для данного сервиса"""
    templates = value_vars.get('templates')
    readable_services = value_vars.get('readable_services')
    counter_exist_line = value_vars.get('counter_exist_line')
    sreda = value_vars.get('sreda')
    stroka = templates.get("Перенос ^сервиса^ %название сервиса% на клиентский коммутатор.")
    if stroka:
        static_vars = {}
        hidden_vars = {}
        if 'Перенос, СПД' in value_vars.get('type_pass'):
            hidden_vars['МКО:'] = 'МКО:'
            hidden_vars['- Проинформировать клиента о простое ^сервиса^ на время проведения работ по переносу ^сервиса^ в новую точку подключения.'] = '- Проинформировать клиента о простое ^сервиса^ на время проведения работ по переносу ^сервиса^ в новую точку подключения.'
            hidden_vars['- Согласовать время проведение работ[, необходимость смены реквизитов].'] = '- Согласовать время проведение работ[, необходимость смены реквизитов].'
            hidden_vars['- Создать заявку в ИС Cordis на ОНИТС СПД для переноса ^сервиса^ %название сервиса%.'] = '- Создать заявку в ИС Cordis на ОНИТС СПД для переноса ^сервиса^ %название сервиса%.'
            hidden_vars[' в новую точку подключения'] = ' в новую точку подключения'
        if value_vars.get('logic_csw') and 'Перенос, СПД' not in value_vars.get('type_pass') or value_vars.get('logic_csw') and value_vars.get('type_passage') == 'Перевод на гигабит' or value_vars.get('type_passage') == 'Перенос точки подключения':
            for i in range(counter_exist_line):
                result_services.append(enviroment_csw(value_vars))
            if value_vars.get('type_install_csw') not in ['Медная линия и порт не меняются', 'ВОЛС и порт не меняются']:
                hidden_vars[
                        '- Сообщить в ОЛИ СПД об освободившемся порте на коммутаторе %название коммутатора% после переезда клиента.'] = '- Сообщить в ОЛИ СПД об освободившемся порте на коммутаторе %название коммутатора% после переезда клиента.'
                static_vars['название коммутатора'] = value_vars.get('head').split('\n')[4].split()[2]
            services, service_shpd_change = _separate_services_and_subnet_dhcp(value_vars.get('readable_services'), value_vars.get('change_log_shpd'))
            if service_shpd_change:
                hidden_vars[', необходимость смены реквизитов'] = ', необходимость смены реквизитов'
                hidden_vars['ОНИТС СПД подготовиться к работам:'] = 'ОНИТС СПД подготовиться к работам:'
                hidden_vars['- По заявке в ИС Cordis выделить подсеть с маской %нов. маска IP-сети%.'] = '- По заявке в ИС Cordis выделить подсеть с маской %нов. маска IP-сети%.'
                static_vars['нов. маска IP-сети'] = '/30' if value_vars.get('change_log_shpd') == 'Новая подсеть /30' else '/32'
                hidden_vars['-- по согласованию с клиентом сменить реквизиты для услуги "ШПД в Интернет" на новую подсеть с маской %нов. маска IP-сети%.'] = '-- по согласованию с клиентом сменить реквизиты для услуги "ШПД в Интернет" на новую подсеть с маской %нов. маска IP-сети%.'
                hidden_vars['- После смены реквизитов:'] = '- После смены реквизитов:'
                hidden_vars['- разобрать ресурс %ресурс на договоре% на договоре.'] = '- разобрать ресурс %ресурс на договоре% на договоре.'
                static_vars['ресурс на договоре'] = ', '.join(service_shpd_change)
            else:
                services = []
                for key, value in readable_services.items():
                    if key != '"Телефония"':
                        if type(value) == str:
                            services.append(key + ' ' + value)
                        elif type(value) == list:
                            services.append(key + ''.join(value))
            if 'ЦКС' in ', '.join(services):
                hidden_vars[
                    '- Ограничить скорость и настроить маркировку трафика для ^сервиса^ %название сервиса% %L2. точка ограничения и маркировки трафика%.'] = '- Ограничить скорость и настроить маркировку трафика для ^сервиса^ ЦКС %L2. точка ограничения и маркировки трафика%.'
                static_vars['L2. точка ограничения и маркировки трафика'] = 'как ранее'
            if 'ВЛС' in ', '.join(services):
                hidden_vars[
                    '- Ограничить скорость и настроить маркировку трафика для ^сервиса^ %название сервиса% %L2. точка ограничения и маркировки трафика%.'] = '- Ограничить скорость и настроить маркировку трафика для ^сервиса^ порт ВЛС %L2. точка ограничения и маркировки трафика%.'
                static_vars['L2. точка ограничения и маркировки трафика'] = 'как ранее'
            if 'ВМ' in ', '.join(services):
                hidden_vars[
                    '- Ограничить скорость и настроить маркировку трафика для ^сервиса^ %название сервиса% %L3. точка ограничения и маркировки трафика%.'] = '- Ограничить скорость и настроить маркировку трафика для ^сервиса^ порт ВМ %L3. точка ограничения и маркировки трафика%.'
                static_vars['L3. точка ограничения и маркировки трафика'] = 'как ранее'
            static_vars['указать сервис'] = ', '.join(services)
            static_vars['название сервиса'] = ', '.join([x for x in readable_services.keys() if x != '"Телефония"'])
            stroka = analyzer_vars(stroka, static_vars, hidden_vars)
            counter_plur = len(services)
            result_services.append(pluralizer_vars(stroka, counter_plur))
        elif value_vars.get('type_passage') == 'Перенос сервиса в новую точку':
            result_services.append(enviroment_csw(value_vars))
            services = []
            other_services = []
            for key, value in readable_services.items():
                if key != '"Телефония"':
                    if type(value) == str:
                        if value_vars.get('selected_ono')[0][-4] in value:
                            services.append(key + ' ' + value)
                            static_vars['название сервиса'] = key
                            value_vars.update({'name_passage_service': key +' '+ value })
                        else:
                            other_services.append(key + ' ' + value)
                    elif type(value) == list:
                        for val in value:
                            if value_vars.get('selected_ono')[0][-4] in val:
                                services.append(key + ' ' + val)
                                static_vars['название сервиса'] = key
                                value_vars.update({'name_passage_service': key +' '+ val})
                            else:
                                other_services.append(key + ' ' + val)
            if value_vars.get('type_passage') == 'Перенос сервиса в новую точку':
                if value_vars.get('head').split('\n')[4].split()[2] == value_vars.get('selected_ono')[0][-2] or other_services == False:
                    hidden_vars[
                        '- Сообщить в ОЛИ СПД об освободившемся порте на коммутаторе %название коммутатора% после переезда клиента.'] = '- Сообщить в ОЛИ СПД об освободившемся порте на коммутаторе %название коммутатора% после переезда клиента.'
                    static_vars['название коммутатора'] = value_vars.get('head').split('\n')[4].split()[2]

            if services[0].startswith('"ШПД в интернет"'):
                if value_vars.get('change_log_shpd') != 'существующая адресация':
                    hidden_vars[', необходимость смены реквизитов'] = ', необходимость смены реквизитов'
                    hidden_vars['ОНИТС СПД подготовиться к работам:'] = 'ОНИТС СПД подготовиться к работам:'
                    hidden_vars['- По заявке в ИС Cordis выделить подсеть с маской %нов. маска IP-сети%.'] = '- По заявке в ИС Cordis выделить подсеть с маской %нов. маска IP-сети%.'
                    static_vars['нов. маска IP-сети'] = '/30' if value_vars.get('change_log_shpd') == 'Новая подсеть /30' else '/32'
                    static_vars['указать сервис'] = static_vars['название сервиса']
                    hidden_vars['-- по согласованию с клиентом сменить реквизиты для услуги "ШПД в Интернет" на новую подсеть с маской %нов. маска IP-сети%.'] = '-- по согласованию с клиентом сменить реквизиты для услуги "ШПД в Интернет" на новую подсеть с маской %нов. маска IP-сети%.'
                    hidden_vars['- После смены реквизитов:'] = '- После смены реквизитов:'
                    hidden_vars['- разобрать ресурс %ресурс на договоре% на договоре.'] = '- разобрать ресурс %ресурс на договоре% на договоре.'
                    static_vars['ресурс на договоре'] = value_vars.get('selected_ono')[0][-4]
                else:
                    static_vars['указать сервис'] = ', '.join(services)
            else:
                static_vars['указать сервис'] = ', '.join(services)
            stroka = analyzer_vars(stroka, static_vars, hidden_vars)
            counter_plur = len(services)
            result_services.append(pluralizer_vars(stroka, counter_plur))
    return result_services


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
        add_hidden_vars, add_static_vars = _get_pm_vars(value_vars, service)
        static_vars.update(add_static_vars)
        hidden_vars.update(add_hidden_vars)
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
            all_shpd_in_tr = value_vars.get('all_shpd_in_tr')
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
            all_portvk_in_tr = value_vars.get('all_portvk_in_tr')
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
            all_portvm_in_tr = value_vars.get('all_portvm_in_tr')
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
                all_cks_in_tr = value_vars.get('all_cks_in_tr')
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
                all_hotspot_in_tr = value_vars.get('all_hotspot_in_tr')
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
            all_cks_in_tr = value_vars.get('all_cks_in_tr')
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


def client_new(value_vars):
    """Данный метод формирует готовое ТР для нового присоединения и новых услуг"""
    if value_vars.get('spd') == 'РТК':
        result_services, value_vars = rtk_enviroment(value_vars)
    elif value_vars.get('spd') == 'ППМ':
        result_services, value_vars = ppm_enviroment(value_vars)
    elif value_vars.get('spd') == 'Вектор':
        result_services, value_vars = vector_enviroment(value_vars)
    else:
        result_services, value_vars = _new_enviroment(value_vars)
    result_services, result_services_ots, value_vars = _new_services(result_services, value_vars)
    return result_services, result_services_ots, value_vars


def change_services(value_vars):
    """Данный метод формирует готовое ТР для организации новых услуг или изменения существующих без монтаж. работ"""
    result_services, value_vars = _change_services(value_vars)
    if value_vars.get('result_services_ots'):
        result_services_ots = value_vars.get('result_services_ots')
    else:
        result_services_ots = None
    return result_services, result_services_ots, value_vars


def extra_services_with_install_csw(value_vars):
    """Данный метод формирует готовое ТР для организации новых услуг дополнительно к существующему подключению
    с установкой КК"""
    result_services, value_vars = exist_enviroment_install_csw(value_vars)
    result_services, result_services_ots, value_vars = _new_services(result_services, value_vars)
    result_services = _passage_services_on_csw(result_services, value_vars)
    if value_vars.get('phone_in_pass'):
        result_services, result_services_ots, value_vars = _passage_phone_service(result_services, value_vars)
    return result_services, result_services_ots, value_vars


def extra_services_with_passage_csw(value_vars):
    """Данный метод формирует готовое ТР для переноса КК и организации от него новых услуг"""
    result_services, value_vars = exist_enviroment_passage_csw(value_vars)
    result_services, result_services_ots, value_vars = _new_services(result_services, value_vars)
    result_services_ots = None
    return result_services, result_services_ots, value_vars


def extra_services_with_replace_csw(value_vars):
    """Данный метод формирует готовое ТР для организации новых услуг дополнительно к существующему подключению
    с заменой КК"""
    result_services, value_vars = exist_enviroment_replace_csw(value_vars)
    result_services, result_services_ots, value_vars = _new_services(result_services, value_vars)
    return result_services, result_services_ots, value_vars


def passage_services_with_install_csw(value_vars):
    """Данный метод формирует готовое ТР для переноса сервисов с установкой КК"""
    result_services, value_vars = exist_enviroment_install_csw(value_vars)
    result_services = _passage_services_on_csw(result_services, value_vars)
    if value_vars.get('phone_in_pass'):
        result_services, result_services_ots, value_vars = _passage_phone_service(result_services, value_vars)
    else:
        result_services_ots = None
    return result_services, result_services_ots, value_vars


def passage_services_with_passage_csw(value_vars):
    """Данный метод формирует готовое ТР для переноса КК или расширения сервиса без монтаж. работ"""
    result_services, value_vars = exist_enviroment_passage_csw(value_vars)
    value_vars.update({'result_services': result_services})
    if value_vars.get('result_services_ots'):
        result_services_ots = value_vars.get('result_services_ots')
    else:
        result_services_ots = None
    if value_vars.get('type_passage') == 'Перевод на гигабит' and value_vars.get('change_log') == 'Порт/КАД меняются':
        result_services, result_services_ots, value_vars  = extend_service(value_vars)
    return result_services, result_services_ots, value_vars


def passage_services(value_vars):
    """Данный метод формирует готовое ТР для переноса услуг"""
    if (value_vars.get('type_passage') == 'Перенос сервиса в новую точку' or value_vars.get('type_passage') == 'Перенос точки подключения') and value_vars.get('change_log') != 'Порт и КАД не меняется':
        if value_vars.get('spd') == 'РТК':
            result_services, value_vars = rtk_enviroment(value_vars)
        elif value_vars.get('spd') == 'ППМ':
            result_services, value_vars = ppm_enviroment(value_vars)
        elif value_vars.get('spd') == 'Вектор':
            result_services, value_vars = vector_enviroment(value_vars)
        else:
            result_services, value_vars = _new_enviroment(value_vars)
    elif value_vars.get('type_passage') == 'Перенос логического подключения' and value_vars.get('change_log') != 'Порт и КАД не меняется':
        if value_vars.get('spd') == 'РТК':
            result_services, value_vars = rtk_enviroment(value_vars)
        else:
            result_services, value_vars = _passage_enviroment(value_vars)
    else:
        result_services, value_vars = _passage_enviroment(value_vars)
    result_services, value_vars = _passage_services(result_services, value_vars)
    if value_vars.get('phone_in_pass'):
        result_services, result_services_ots, value_vars = _passage_phone_service(result_services, value_vars)
    else:
        result_services_ots = None
    return result_services, result_services_ots, value_vars


def extend_service(value_vars):
    """Данный метод формирует готовое ТР для расширения сервиса без монтаж. работ"""
    if value_vars.get('result_services'):
        result_services = value_vars.get('result_services')
    else:
        result_services = []
    if value_vars.get('result_services_ots'):
        result_services_ots = value_vars.get('result_services_ots')
    else:
        result_services_ots = None
    templates = value_vars.get('templates')
    selected_ono = value_vars.get('selected_ono')
    readable_services = value_vars.get('readable_services')
    static_vars = {}
    hidden_vars = {}
    desc_service, name_passage_service = get_selected_readable_service(readable_services, selected_ono)
    if value_vars.get('logic_change_gi_csw') == None:
        hidden_vars['- Проинформировать клиента о простое сервиса на время проведения работ.'] = '- Проинформировать клиента о простое сервиса на время проведения работ.'
        hidden_vars['- Согласовать время проведение работ[, необходимость смены реквизитов].'] = '- Согласовать время проведение работ[, необходимость смены реквизитов].'
    if any([desc_service in ['ЦКС', 'Порт ВЛС', 'Порт ВМ']]):
        hidden_vars['на %пропускная способность%'] = 'на %пропускная способность%'
        hidden_vars['- Ограничить скорость и настроить маркировку трафика для %указать сервис% %L2. точка ограничения и маркировки трафика%.'] = '- Ограничить скорость и настроить маркировку трафика для %указать сервис% %L2. точка ограничения и маркировки трафика%.'
        static_vars['указать сервис'] = name_passage_service
        static_vars['название сервиса'] = desc_service
        static_vars['пропускная способность'] = value_vars.get('extend_speed')
        if value_vars.get('extend_policer_cks_vk'):
            static_vars['L2. точка ограничения и маркировки трафика'] = value_vars.get('extend_policer_cks_vk')
        if value_vars.get('extend_policer_vm'):
            static_vars['L2. точка ограничения и маркировки трафика'] = value_vars.get('extend_policer_vm')
        value_vars.update({'name_passage_service': name_passage_service})
        stroka = templates.get('Расширение полосы сервиса %название сервиса%.')
        result_services.append(analyzer_vars(stroka, static_vars, hidden_vars))
    else:
        stroka = templates.get('Изменение полосы сервиса "ШПД в Интернет".')
        value_vars.update({'name_passage_service': name_passage_service})
        result_services.append(analyzer_vars(stroka, static_vars, hidden_vars))
    if value_vars.get('kad') == None:
        kad = value_vars.get('selected_ono')[0][-2]
        value_vars.update({'kad': kad})
        if value_vars.get('selected_ono')[0][-2].startswith('CSW'):
            node_csw = value_vars.get('node_csw')
            value_vars.update({'pps': node_csw})
    return result_services, result_services_ots, value_vars


def passage_video(value_vars):
    if value_vars.get('result_services'):
        result_services = value_vars.get('result_services')
    else:
        result_services = []
    if value_vars.get('result_services_ots'):
        result_services_ots = value_vars.get('result_services_ots')
    else:
        result_services_ots = None
    templates = value_vars.get('templates')
    static_vars = {}
    hidden_vars = {}
    rep_string = {}
    camera_names = [v for k, v in value_vars.get('pass_video_form').items() if 'camera_name' in k]
    camera_names.sort()
    count_cameras = len(camera_names)
    rep_string[
        'camera'] = '%название камеры% - порт: %порт доступа на маршрутизаторе%, новое место установки камеры: %Новое место Камеры%'
    multi_vars = {rep_string['camera']: []}
    static_vars['количество камер'] = str(count_cameras)
    if value_vars.get('pass_video_form').get('change_video_ip') is True:
        hidden_vars['ОВИТС проведение работ:'] = 'ОВИТС проведение работ:'
        hidden_vars[
            '- Произвести настройку ^видеокамер^ и маршрутизатора для предоставления сервиса.'
        ] = '- Произвести настройку ^видеокамер^ и маршрутизатора для предоставления сервиса.'
        hidden_vars['- Актуализировать в ИС Cordis адреса видеопотока.'] = '- Актуализировать в ИС Cordis адреса видеопотока.'

    if value_vars.get('pass_video_form').get('poe') == 'Сущ. POE-инжектор':
        hidden_vars[
            '- Организовать %количество камер% ^линию^ от ^камер^ до маршрутизатора клиента.'
        ] = '- Организовать %количество камер% ^линию^ от ^камер^ до маршрутизатора клиента.'
        hidden_vars[
            '- Подключить {организованную} {линию} связи через POE ^инжектор^ в lan-^порт^ маршрутизатора:'
        ] = '- Подключить {организованную} {линию} связи через POE ^инжектор^ в lan-^порт^ маршрутизатора:'

    elif value_vars.get('pass_video_form').get('poe') == 'Новый POE-инжектор':
        hidden_vars[
            '- Организовать %количество камер% ^линию^ от ^камер^ до маршрутизатора клиента.'
        ] = '- Организовать %количество камер% ^линию^ от ^камер^ до маршрутизатора клиента.'
        hidden_vars[
            '- Подключить {организованную} {линию} связи через POE ^инжектор^ в lan-^порт^ маршрутизатора:'
        ] = '- Подключить {организованную} {линию} связи через POE ^инжектор^ в lan-^порт^ маршрутизатора:'

        hidden_vars['ОИПД подготовиться к работам:'] = 'ОИПД подготовиться к работам:'
        hidden_vars['- Получить на складе территории:'] = '- Получить на складе территории:'
        hidden_vars[
            '-- PoE-инжектор %модель PoE-инжектора% - %количество POE-инжекторов% шт.'
        ] = '-- PoE-инжектор %модель PoE-инжектора% - %количество POE-инжекторов% шт.'
        static_vars['модель PoE-инжектора'] = 'СКАТ PSE-PoE.220AC/15VA'
        static_vars['количество POE-инжекторов'] = str(count_cameras)

    elif value_vars.get('pass_video_form').get('poe') == 'Сущ. POE-коммутатор':
        hidden_vars[
            '- Организовать %количество камер% ^линию^ от ^камер^ до POE-коммутатора.'
        ] = '- Организовать %количество камер% ^линию^ от ^камер^ до POE-коммутатора.'
        hidden_vars[
            '- Подключить {организованную} {линию} связи в ^порт^ POE-коммутатора:'
        ] = '- Подключить {организованную} {линию} связи в ^порт^ POE-коммутатора:'
        hidden_vars[
            '- Выполнить монтажные работы по переносу и подключению существующего POE-коммутатора.'
        ] = '- Выполнить монтажные работы по переносу и подключению существующего POE-коммутатора.'

    elif value_vars.get('pass_video_form').get('poe') == 'Новый POE-коммутатор':
        hidden_vars[
            '- Организовать %количество камер% ^линию^ от ^камер^ до POE-коммутатора.'
        ] = '- Организовать %количество камер% ^линию^ от ^камер^ до POE-коммутатора.'
        hidden_vars[
            '- Подключить {организованную} {линию} связи в ^порт^ POE-коммутатора:'
        ] = '- Подключить {организованную} {линию} связи в ^порт^ POE-коммутатора:'
        hidden_vars['ОИПД подготовиться к работам:'] = 'ОИПД подготовиться к работам:'
        hidden_vars['- Получить на складе территории:'] = '- Получить на складе территории:'
        hidden_vars['-- POE-коммутатор %модель POE-коммутатора% - 1 шт.'] = '-- POE-коммутатор %модель POE-коммутатора% - 1 шт.'
        hidden_vars[
            '- Установить в помещении клиента POE-коммутатор %модель POE-коммутатора%. Организовать линию от маршрутизатора клиента до POE-коммутатора. Включить организованную линию связи:'
        ] = '- Установить в помещении клиента POE-коммутатор %модель POE-коммутатора%. Организовать линию от маршрутизатора клиента до POE-коммутатора. Включить организованную линию связи:'
        hidden_vars['-- В свободный порт маршрутизатора;'] = '-- В свободный порт маршрутизатора;'
        hidden_vars[
            '-- В порт %порт доступа на POE-коммутаторе% POE-коммутатора'
        ] = '-- В порт %порт доступа на POE-коммутаторе% POE-коммутатора'
        if count_cameras < 5:
            static_vars['модель POE-коммутатора'] = 'D-Link DES-1005P'
            static_vars['порт доступа на POE-коммутаторе'] = '5'
        else:
            static_vars['модель POE-коммутатора'] = 'Atis PoE-1010-8P'
            static_vars['порт доступа на POE-коммутаторе'] = '10'
    for i in range(count_cameras):
        static_vars[f'название камеры {i}'] = value_vars.get('pass_video_form').get(f'camera_name_{i}')
        static_vars[f'порт доступа на маршрутизаторе {i}'] = value_vars.get('pass_video_form').get(f'camera_port_{i}')
        static_vars[f'Новое место Камеры {i}'] = value_vars.get('pass_video_form').get(f'camera_place_{i}')
        multi_vars[rep_string['camera']].append(
                f'"%название камеры {i}%" - порт: %порт доступа на маршрутизаторе {i}%, новое место установки камеры: %Новое место Камеры {i}%')

    static_vars['перечисление камер'] = ', '.join([f'"{i}"' for i in camera_names])
    stroka = templates.get('Перенос сервиса Видеонаблюдение в новую физическую точку подключения.')
    stroka = analyzer_vars(stroka, static_vars, hidden_vars, multi_vars)
    counter_plur = count_cameras
    result_services.append(pluralizer_vars(stroka, counter_plur))
    return result_services, result_services_ots, value_vars


def passage_track(value_vars):
    """Данный метод формирует готовое ТР для переноса сервиса с изменением трассы, но без изменения лог. подключения"""
    if value_vars.get('result_services'):
        result_services = value_vars.get('result_services')
    else:
        result_services = []
    if value_vars.get('result_services_ots'):
        result_services_ots = value_vars.get('result_services_ots')
    else:
        result_services_ots = None
    templates = value_vars.get('templates')
    static_vars = {}
    hidden_vars = {}
    if value_vars.get('ppr'):
        hidden_vars['%отдел ОИПМ / ОИПД% подготовка к работам.'] = '%отдел ОИПМ / ОИПД% подготовка к работам.'
        hidden_vars[
            '- Требуется отключение согласно списку отключений в ППР %№ заявки ППР% согласовать проведение работ.'] = '- Требуется отключение согласно списку отключений в ППР %№ заявки ППР% согласовать проведение работ.'
        hidden_vars[
            '- Совместно с ОНИТС СПД убедиться в восстановлении связи согласно списку отключений в ППР %№ заявки ППР%.'] = '- Совместно с ОНИТС СПД убедиться в восстановлении связи согласно списку отключений в ППР %№ заявки ППР%.'
        hidden_vars[
            '- После проведения монтажных работ убедиться в восстановлении услуг согласно списку отключений в ППР %№ заявки ППР%.'] = '- После проведения монтажных работ убедиться в восстановлении услуг согласно списку отключений в ППР %№ заявки ППР%.'
        static_vars['№ заявки ППР'] = value_vars.get('ppr')
    if value_vars.get('exist_sreda') == '2' or value_vars.get('exist_sreda') == '4':
        static_vars['тип линии связи'] = 'ВОЛС'
        static_vars['отдел ОИПМ / ОИПД'] = 'ОИПМ'
    else:
        static_vars['тип линии связи'] = 'медную линию связи'
        static_vars['отдел ОИПМ / ОИПД'] = 'ОИПД'
    stroka = templates.get('Изменение трассы присоединения к СПД.')
    result_services.append(analyzer_vars(stroka, static_vars, hidden_vars))
    if value_vars.get('kad') == None:
        kad = value_vars.get('independent_kad')
        value_vars.update({'kad': kad})
        pps = value_vars.get('independent_pps')
        value_vars.update({'pps': pps})
    return result_services, result_services_ots, value_vars


def restore_track(value_vars):
    """Данный метод формирует готовое ТР для восстановления трассы присоединения"""
    if value_vars.get('result_services'):
        result_services = value_vars.get('result_services')
    else:
        result_services = []
    if value_vars.get('result_services_ots'):
        result_services_ots = value_vars.get('result_services_ots')
    else:
        result_services_ots = None
    templates = value_vars.get('templates')
    static_vars = {}
    hidden_vars = {}
    if value_vars.get('ppr'):
        hidden_vars['%отдел ОИПМ / ОИПД% подготовка к работам.'] = '%отдел ОИПМ / ОИПД% подготовка к работам.'
        hidden_vars[
            '- Требуется отключение согласно списку отключений в ППР %№ заявки ППР% согласовать проведение работ.'] = '- Требуется отключение согласно списку отключений в ППР %№ заявки ППР% согласовать проведение работ.'
        hidden_vars[
            '- Совместно с ОНИТС СПД убедиться в восстановлении связи согласно списку отключений в ППР %№ заявки ППР%.'] = '- Совместно с ОНИТС СПД убедиться в восстановлении связи согласно списку отключений в ППР %№ заявки ППР%.'
        hidden_vars[
            '- После проведения монтажных работ убедиться в восстановлении услуг согласно списку отключений в ППР %№ заявки ППР%.'] = '- После проведения монтажных работ убедиться в восстановлении услуг согласно списку отключений в ППР %№ заявки ППР%.'
        static_vars['№ заявки ППР'] = value_vars.get('ppr')
    if value_vars.get('exist_sreda') == '2' or value_vars.get('exist_sreda') == '4':
        static_vars['тип линии связи'] = 'ВОЛС'
        static_vars['отдел ОИПМ / ОИПД'] = 'ОИПМ'
    elif value_vars.get('exist_sreda') == '3':
        static_vars['тип линии связи'] = 'радиоканал'
        static_vars['отдел ОИПМ / ОИПД'] = 'ОИПД'
    else:
        static_vars['тип линии связи'] = 'медную линию связи'
        static_vars['отдел ОИПМ / ОИПД'] = 'ОИПД'
    stroka = templates.get('Восстановление трассы присоединения к СПД.')
    result_services.append(analyzer_vars(stroka, static_vars, hidden_vars))
    if value_vars.get('kad') == None:
        kad = value_vars.get('independent_kad')
        value_vars.update({'kad': kad})
        pps = value_vars.get('independent_pps')
        value_vars.update({'pps': pps})
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

def passage_csw_no_install(value_vars):
    """Данный метод формирует готовое ТР для переноса КК с изменением трассы, но без изменения лог. подключения"""
    if value_vars.get('result_services'):
        result_services = value_vars.get('result_services')
    else:
        result_services = []
    if value_vars.get('result_services_ots'):
        result_services_ots = value_vars.get('result_services_ots')
    else:
        result_services_ots = None
    static_vars = {}
    hidden_vars = {}
    templates = value_vars.get('templates')
    if value_vars.get('ppr'):
        hidden_vars[
            '- Требуется отключение согласно списку отключений в ППР %№ заявки ППР% согласовать проведение работ.'] = '- Требуется отключение согласно списку отключений в ППР %№ заявки ППР% согласовать проведение работ.'
        hidden_vars[
            '- Совместно с ОНИТС СПД убедиться в восстановлении связи согласно списку отключений в ППР %№ заявки ППР%.'] = '- Совместно с ОНИТС СПД убедиться в восстановлении связи согласно списку отключений в ППР %№ заявки ППР%.'
        hidden_vars[
            '- После проведения монтажных работ убедиться в восстановлении услуг согласно списку отключений в ППР %№ заявки ППР%.'] = '- После проведения монтажных работ убедиться в восстановлении услуг согласно списку отключений в ППР %№ заявки ППР%.'
        static_vars['№ заявки ППР'] = value_vars.get('ppr')
    static_vars['название коммутатора клиентского'] = value_vars.get('selected_ono')[0][-2]
    if value_vars.get('exist_sreda') == '2' or value_vars.get('exist_sreda') == '4':
        static_vars['тип линии связи'] = 'ВОЛС'
        static_vars['отдел ОИПМ / ОИПД'] = 'ОИПМ'
    else:
        static_vars['тип линии связи'] = 'медную линию связи'
        static_vars['отдел ОИПМ / ОИПД'] = 'ОИПД'
    stroka = templates.get('Перенос клиентского коммутатора.')
    result_services.append(analyzer_vars(stroka, static_vars, hidden_vars))
    if value_vars.get('kad') == None:
        kad = value_vars.get('independent_kad')
        value_vars.update({'kad': kad})
        pps = value_vars.get('independent_pps')
        value_vars.update({'pps': pps})
    return result_services, result_services_ots, value_vars

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
    """Компановка текста"""
    def __init__(self, value_vars):
        self.static_vars = {}
        self.hidden_vars = {}
        self.multi_vars = {}
        self.value_vars = value_vars
        self.plural = 1

    def construct(self, template):
        analyzed = analyzer_vars(template, self.static_vars, self.hidden_vars, self.multi_vars)
        return pluralizer_vars(analyzed, self.plural)


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

