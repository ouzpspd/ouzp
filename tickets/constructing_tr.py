from .utils import *
from .utils import _get_policer
from .utils import _readable_node
from .utils import _separate_services_and_subnet_dhcp


def _new_services(result_services, value_vars):
    """Данный метод формирует блоки ТТР организации новых сервисов"""
    result_services_ots = None
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
            static_vars['указать маску'] = '/32'
            result_services.append(analyzer_vars(stroka, static_vars, hidden_vars))
            all_shpd_in_tr = value_vars.get('all_shpd_in_tr')
            if all_shpd_in_tr.get(service) and all_shpd_in_tr.get(service)['router_shpd']:
                stroka = templates.get("Установка маршрутизатора")
                if sreda == '2' or sreda == '4':
                    static_vars['ОИПМ/ОИПД'] = 'ОИПМ'
                else:
                    static_vars['ОИПМ/ОИПД'] = 'ОИПД'
                result_services.append(analyzer_vars(stroka, static_vars, hidden_vars))
        elif 'Интернет, блок Адресов Сети Интернет' in service:
            name_new_service.add('ШПД в Интернет')
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
            all_shpd_in_tr = value_vars.get('all_shpd_in_tr')
            if all_shpd_in_tr.get(service) and all_shpd_in_tr.get(service)['type_shpd'] == 'access':
                stroka = templates.get("Организация услуги ШПД в интернет access'ом.")
                result_services.append(analyzer_vars(stroka, static_vars, hidden_vars))
            elif all_shpd_in_tr.get(service) and all_shpd_in_tr.get(service)['type_shpd'] == 'trunk':
                stroka = templates.get("Организация услуги ШПД в интернет trunk'ом.")
                result_services.append(analyzer_vars(stroka, static_vars, hidden_vars))

            if all_shpd_in_tr.get(service) and all_shpd_in_tr.get(service)['router_shpd']:
                stroka = templates.get("Установка маршрутизатора")
                if sreda == '2' or sreda == '4':
                    static_vars['ОИПМ/ОИПД'] = 'ОИПМ'
                else:
                    static_vars['ОИПМ/ОИПД'] = 'ОИПД'
                result_services.append(analyzer_vars(stroka, static_vars, hidden_vars))
        elif 'iTV' in service:
            name_new_service.add('Вебург.ТВ')
            static_vars = {}
            hidden_vars = {}
            type_itv = value_vars.get('type_itv')
            if type_itv == 'vl':
                cnt_itv = value_vars.get('cnt_itv')
                if logic_csw:
                    if value_vars.get('router_itv'):
                        result_services.append(enviroment_csw(value_vars))
                    else:
                        for i in range(int(cnt_itv)):
                            result_services.append(enviroment_csw(value_vars))

                if value_vars.get('router_itv'):
                    sreda = value_vars.get('sreda')
                    if sreda == '2' or sreda == '4':
                        static_vars['ОИПМ/ОИПД'] = 'ОИПМ'
                    else:
                        static_vars['ОИПМ/ОИПД'] = 'ОИПД'
                    stroka = templates.get("Установка маршрутизатора")
                    result_services.append(analyzer_vars(stroka, static_vars, hidden_vars))
                    static_vars['маска'] = '/30'
                else:
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
            elif type_itv == 'novlexist':
                stroka = templates.get("Организация услуги Вебург.ТВ в vlan'е действующей услуги ШПД в интернет")
                result_services.append(analyzer_vars(stroka, static_vars, hidden_vars))
        elif 'ЦКС' in service:
            name_new_service.add('ЦКС')
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
                if all_cks_in_tr.get(service)['type_cks'] == 'access':
                    stroka = templates.get("Организация услуги ЦКС Etherline access'ом.")
                    result_services.append(analyzer_vars(stroka, static_vars, hidden_vars))
                elif all_cks_in_tr.get(service)['type_cks'] == 'trunk':
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
            name_new_service.add('Порт ВМ')
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
            static_vars['указать полосу'] = _get_policer(service)
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
            name_new_service.add('Хот-спот')
            static_vars = {}
            hidden_vars = {}
            types_premium_plus = ['премиум +', 'премиум+', 'прем+', 'прем +']
            if any(type in service.lower() for type in types_premium_plus):
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
                if 'прем' in service.lower():
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
            name_new_service.add('Видеонаблюдение')
            static_vars = {}
            hidden_vars = {}
            static_vars['указать модель камеры'] = value_vars.get('camera_model')
            if value_vars.get('voice') == True:
                static_vars['требуется запись звука / запись звука не требуется'] = 'требуется запись звука'
                hidden_vars[' и запись звука'] = ' и запись звука'
            else:
                static_vars['требуется запись звука / запись звука не требуется'] = 'запись звука не требуется'
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
                    static_vars['POE-коммутатор D-Link DES-1005P / TP-Link TL-SF1005P'] = 'POE-коммутатор D-Link DES-1005P'
                    static_vars['указать номер порта POE-коммутатора'] = '5'
                    static_vars['номер камеры'] = '5'
                elif int(camera_number) == 9:
                    static_vars['POE-коммутатор D-Link DES-1005P / TP-Link TL-SF1005P'] = 'POE-коммутатор Atis PoE-1010-8P'
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
                    static_vars['POE-коммутатор D-Link DES-1005P / TP-Link TL-SF1005P'] = 'POE-коммутатор Atis PoE-1010-8P'
                    static_vars['указать номер порта POE-коммутатора'] = '10'
                elif 2 < int(camera_number) < 5:
                    static_vars['POE-коммутатор D-Link DES-1005P / TP-Link TL-SF1005P'] = 'POE-коммутатор D-Link DES-1005P'
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
                stroka = stroka[:stroka.index(
                    'порты POE-коммутатора:')] + 'порты POE-коммутатора:\n' + extra_extra_stroka_one + '\n \nОВИТС проведение работ:\n' + stroka[
                                                                                                                                          stroka.index(
                                                                                                                                              '- Произвести настройку'):]
                stroka = stroka + '\n' + extra_extra_stroka_two
                static_vars['указать количество POE-коммутаторов'] = '1'
                stroka = analyzer_vars(stroka, static_vars, hidden_vars)
                counter_plur = int(camera_number)
                result_services.append(pluralizer_vars(stroka, counter_plur))
        elif 'Телефон' in service:
            name_new_service.add('Телефония')
            result_services_ots = []
            hidden_vars = {}
            static_vars = {}
            vgw = value_vars.get('vgw')
            ports_vgw = value_vars.get('ports_vgw')
            channel_vgw = value_vars.get('channel_vgw')
            if service.endswith('|'):
                if value_vars.get('type_phone') == 'st':
                    if logic_csw == True:
                        result_services.append(enviroment_csw(value_vars))
                    stroka = templates.get("Подключения по цифровой линии с использованием протокола SIP, тип линии «IP-транк»")
                    static_vars['trunk/access'] = 'trunk' if value_vars.get('type_ip_trunk') == 'trunk' else 'access'
                    static_vars['указать количество каналов'] = channel_vgw
                    result_services.append(analyzer_vars(stroka, static_vars, hidden_vars))
                elif value_vars.get('type_phone') == 'ak':
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
                        elif 'расш' in service.lower():
                            static_vars[
                                'базовым набором сервисов / расширенным набором сервисов'] = 'расширенным набором сервисов'

                        static_vars['указать количество телефонных линий'] = ports_vgw
                        if ports_vgw == '1':
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
                        if channel_vgw == '1':
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
                    elif 'расш' in service.lower():
                        static_vars[
                            'базовым набором сервисов / расширенным набором сервисов'] = 'расширенным набором сервисов'
                    static_vars['идентификатор тел. шлюза'] = 'установленный по решению выше'

                    static_vars['указать количество телефонных линий'] = ports_vgw
                    static_vars['указать количество портов'] = ports_vgw
                    if ports_vgw == '1':
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
                    if channel_vgw == '1':
                        static_vars['указать порты тел. шлюза'] = '1'
                    else:
                        static_vars['указать порты тел. шлюза'] = '1-{}'.format(channel_vgw)
                    stroka = analyzer_vars(stroka, static_vars, hidden_vars)
                    regex_counter = 'Организовать (\d+)'
                    match_counter = re.search(regex_counter, stroka)
                    counter_plur = int(match_counter.group(1))
                    result_services_ots.append(pluralizer_vars(stroka, counter_plur))
            elif service.endswith('\\'):
                static_vars['указать порты тел. шлюза'] = value_vars.get('form_exist_vgw_port')
                static_vars['указать модель тел. шлюза'] = value_vars.get('form_exist_vgw_model')
                static_vars['идентификатор тел. шлюза'] = value_vars.get('form_exist_vgw_name')
                if 'ватс' in service.lower():
                    stroka = templates.get("ВАТС (Подключение по аналоговой линии)")
                    if 'базов' in service.lower():
                        static_vars[
                            'базовым набором сервисов / расширенным набором сервисов'] = 'базовым набором сервисов'
                    elif 'расш' in service.lower():
                        static_vars[
                            'базовым набором сервисов / расширенным набором сервисов'] = 'расширенным набором сервисов'

                    static_vars['указать количество телефонных линий'] = ports_vgw
                    static_vars['указать количество портов'] = ports_vgw
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
                        result_services_ots.append(analyzer_vars(stroka, static_vars, hidden_vars))
                    elif 'расш' in service.lower():
                        stroka = templates.get("ВАТС Расширенная(SIP регистрация через Интернет)")
                        static_vars['указать количество портов'] = ports_vgw
                        stroka = analyzer_vars(stroka, static_vars, hidden_vars)
                        result_services_ots.append(pluralizer_vars(stroka, int(ports_vgw)))
                else:
                    stroka = templates.get(
                        "Подключения по цифровой линии с использованием протокола SIP, тип линии «SIP регистрация через Интернет»")

                    static_vars['указать количество каналов'] = channel_vgw
                    result_services_ots.append(analyzer_vars(stroka, static_vars, hidden_vars))
        elif 'ЛВС' in service:
            name_new_service.add('ЛВС')
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
                if lvs_switch in ['TP-Link TL-SG105 V4', 'ZYXEL GS1200-5']:
                    static_vars['5/8/16/24'] = '5'
                elif lvs_switch in ['TP-Link TL-SG108 V4', 'ZYXEL GS1200-8']:
                    static_vars['5/8/16/24'] = '8'
                elif lvs_switch == 'D-link DGS-1100-16/B':
                    static_vars['5/8/16/24'] = '16'
                elif lvs_switch == 'D-link DGS-1100-24/B':
                    static_vars['5/8/16/24'] = '24'
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
    static_vars['указать узел связи'] = 'клиентского коммутатора'
    if value_vars.get('logic_csw'):
        static_vars['указать название коммутатора'] = 'установленный по решению выше'
    else:
        static_vars['указать название коммутатора'] = value_vars.get('selected_ono')[0][-2]
    static_vars['указать порт коммутатора'] = 'свободный'
    if sreda == '2' or sreda == '4':
        static_vars['ОИПМ/ОИПД'] = 'ОИПМ'
    else:
        static_vars['ОИПМ/ОИПД'] = 'ОИПД'
    return analyzer_vars(stroka, static_vars, hidden_vars)


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
            hidden_vars[
                '- Организовать %медную линию связи/ВОЛС% от %указать узел связи% до клиентcкого коммутатора по решению ОАТТР.'] = '- Организовать %медную линию связи/ВОЛС% от %указать узел связи% до клиентcкого коммутатора по решению ОАТТР.'
            hidden_vars['- Подключить организованную линию для клиента в коммутатор %указать название коммутатора%, порт задействовать %указать порт коммутатора%.'] = '- Подключить организованную линию для клиента в коммутатор %указать название коммутатора%, порт задействовать %указать порт коммутатора%.'
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
                stroka = templates.get("Установка клиентского коммутатора")
                if sreda == '1':
                    static_vars['ОИПМ/ОИПД'] = 'ОИПД'
                    static_vars['медную линию связи/ВОЛС'] = 'медную линию связи'
                    result_services.append(analyzer_vars(stroka, static_vars, hidden_vars))
                elif sreda == '2' or sreda == '4':
                    if value_vars.get('ppr'):
                        hidden_vars[
                            '- Требуется отключение согласно ППР %указать № ППР% согласовать проведение работ.'] = '- Требуется отключение согласно ППР %указать № ППР% согласовать проведение работ.'
                        hidden_vars[
                            '- Совместно с ОНИТС СПД убедиться в восстановлении связи согласно ППР %указать № ППР%.'] = '- Совместно с ОНИТС СПД убедиться в восстановлении связи согласно ППР %указать № ППР%.'
                        hidden_vars[
                            '- После проведения монтажных работ убедиться в восстановлении услуг согласно ППР %указать № ППР%.'] = '- После проведения монтажных работ убедиться в восстановлении услуг согласно ППР %указать № ППР%.'
                        static_vars['указать № ППР'] = value_vars.get('ppr')
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
                    if value_vars.get('ppr'):
                        hidden_vars[
                            '- Требуется отключение согласно ППР %указать № ППР% согласовать проведение работ.'] = '- Требуется отключение согласно ППР %указать № ППР% согласовать проведение работ.'
                        hidden_vars[
                            '- Совместно с ОНИТС СПД убедиться в восстановлении связи согласно ППР %указать № ППР%.'] = '- Совместно с ОНИТС СПД убедиться в восстановлении связи согласно ППР %указать № ППР%.'
                        hidden_vars[
                            '- После проведения монтажных работ убедиться в восстановлении услуг согласно ППР %указать № ППР%.'] = '- После проведения монтажных работ убедиться в восстановлении услуг согласно ППР %указать № ППР%.'
                        static_vars['указать № ППР'] = value_vars.get('ppr')
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
    pps = _readable_node(value_vars.get('pps'))
    static_vars['указать узел связи'] = pps
    static_vars['указать модель коммутатора'] = value_vars.get('model_csw')
    static_vars['указать № порта'] = value_vars.get('port_csw')
    logic_csw_1000 = value_vars.get('logic_csw_1000')
    if logic_csw_1000 or value_vars.get('logic_change_gi_csw'):
        static_vars['100/1000'] = '1000'
    else:
        static_vars['100/1000'] = '100'
    templates = value_vars.get('templates')
    stroka = templates.get("Установка клиентского коммутатора")
    if value_vars.get('ppr'):
        hidden_vars['- Требуется отключение согласно ППР %указать № ППР% согласовать проведение работ.'] = '- Требуется отключение согласно ППР %указать № ППР% согласовать проведение работ.'
        hidden_vars['- Совместно с ОНИТС СПД убедиться в восстановлении связи согласно ППР %указать № ППР%.'] = '- Совместно с ОНИТС СПД убедиться в восстановлении связи согласно ППР %указать № ППР%.'
        hidden_vars['- После проведения монтажных работ убедиться в восстановлении услуг согласно ППР %указать № ППР%.'] = '- После проведения монтажных работ убедиться в восстановлении услуг согласно ППР %указать № ППР%.'
        static_vars['указать № ППР'] = value_vars.get('ppr')
    if 'Перенос, СПД' not in value_vars.get('type_pass'):
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
        static_vars['указать конвертер/передатчик на стороне клиента'] = value_vars.get('device_client')  #'оптический передатчик SFP WDM, до 20 км, 1550 нм в клиентский коммутатор'
        if logic_csw_1000 == True:
            hidden_vars[
                '-ВНИМАНИЕ! Совместно с ОНИТС СПД удаленно настроить клиентский коммутатор.'] = '-ВНИМАНИЕ! Совместно с ОНИТС СПД удаленно настроить клиентский коммутатор.'
            hidden_vars[
                '- Совместно с %ОИПМ/ОИПД% удаленно настроить клиентский коммутатор.'] = '- Совместно с %ОИПМ/ОИПД% удаленно настроить клиентский коммутатор.'
        kad = value_vars.get('selected_ono')[0][-2]
        static_vars['указать название коммутатора'] = kad
        result_services.append(analyzer_vars(stroka, static_vars, hidden_vars))
    else:
        kad = value_vars.get('kad')
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
            'type_install_csw') == 'Перенос на новый узел':
            hidden_vars[
            '- Организовать %медную линию связи/ВОЛС% от %указать узел связи% до клиентcкого коммутатора по решению ОАТТР.'] = '- Организовать %медную линию связи/ВОЛС% от %указать узел связи% до клиентcкого коммутатора по решению ОАТТР.'
            hidden_vars[
                '- Подключить организованную линию для клиента в коммутатор %указать название коммутатора%, порт задействовать %указать порт коммутатора%.'] = '- Подключить организованную линию для клиента в коммутатор %указать название коммутатора%, порт задействовать %указать порт коммутатора%.'
            if value_vars.get('sreda') == '2' or value_vars.get('sreda') == '4':
                static_vars['медную линию связи/ВОЛС'] = 'ВОЛС'
                static_vars['ОИПМ/ОИПД'] = 'ОИПМ'
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
            else:
                static_vars['медную линию связи/ВОЛС'] = 'медную линию связи'
                static_vars['ОИПМ/ОИПД'] = 'ОИПД'
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
    kad = value_vars.get('head').split('\n')[4].split()[2]
    static_vars['указать название коммутатора'] = kad
    pps = ' '.join(value_vars.get('head').split('\n')[3].split()[1:])
    static_vars['указать узел связи'] = pps
    static_vars['указать модель коммутатора'] = value_vars.get('model_csw')
    static_vars['указать № порта'] = value_vars.get('port_csw')
    static_vars['указать узел связи клиентского коммутатора'] = _readable_node(value_vars.get('node_csw'))
    static_vars['указать модель старого коммутатора'] = value_vars.get('old_model_csw')
    hidden_vars['- Услуги клиента переключить "порт в порт".'] = '- Услуги клиента переключить "порт в порт".'
    types_old_models = ('DIR-100', '3COM', 'Cisco')
    logic_csw_1000 = value_vars.get('logic_csw_1000')
    if logic_csw_1000 or value_vars.get('logic_change_gi_csw'):
        static_vars['100/1000'] = '1000'
    else:
        static_vars['100/1000'] = '100'
    templates = value_vars.get('templates')
    stroka = templates.get("%Замена/Замена и перевод на гигабит% клиентского коммутатора")
    if value_vars.get('type_install_csw') == 'Медная линия и порт не меняются':
        static_vars['ОИПМ/ОИПД'] = 'ОИПД'
        static_vars['Замена/Замена и перевод на гигабит'] = 'Замена'
        result_services.append(analyzer_vars(stroka, static_vars, hidden_vars))
    elif value_vars.get('type_install_csw') == 'ВОЛС и порт не меняются':
        static_vars['ОИПМ/ОИПД'] = 'ОИПМ'
        static_vars['Замена/Замена и перевод на гигабит'] = 'Замена'
        if any(type in value_vars.get('old_model_csw') for type in types_old_models):
            hidden_vars[
            'и %указать конвертер/передатчик на стороне клиента%'] = 'и %указать конвертер/передатчик на стороне клиента%'
            static_vars['указать конвертер/передатчик на стороне клиента'] = value_vars.get('device_client')  #'оптический передатчик SFP WDM, до 20 км, 1550 нм в клиентский коммутатор'
        else:
            hidden_vars['(передатчик задействовать из демонтированного коммутатора)'] = '(передатчик задействовать из демонтированного коммутатора)'
        if logic_csw_1000 == True and value_vars.get('model_csw') == 'D-Link DGS-1100-06/ME':
            hidden_vars[
                '-ВНИМАНИЕ! Совместно с ОНИТС СПД удаленно настроить клиентский коммутатор.'] = '-ВНИМАНИЕ! Совместно с ОНИТС СПД удаленно настроить клиентский коммутатор.'
            hidden_vars[
                '- Совместно с %ОИПМ/ОИПД% удаленно настроить клиентский коммутатор.'] = '- Совместно с %ОИПМ/ОИПД% удаленно настроить клиентский коммутатор.'
        result_services.append(analyzer_vars(stroka, static_vars, hidden_vars))
    else:
        if value_vars.get('logic_change_gi_csw'):
            static_vars['Замена/Замена и перевод на гигабит'] = 'Замена и перевод на гигабит'
        else:
            static_vars['Замена/Замена и перевод на гигабит'] = 'Замена'
        if value_vars.get('ppr'):
            hidden_vars[
                '- Требуется отключение согласно ППР %указать № ППР% согласовать проведение работ.'] = '- Требуется отключение согласно ППР %указать № ППР% согласовать проведение работ.'
            hidden_vars[
                '- Совместно с ОНИТС СПД убедиться в восстановлении связи согласно ППР %указать № ППР%.'] = '- Совместно с ОНИТС СПД убедиться в восстановлении связи согласно ППР %указать № ППР%.'
            hidden_vars[
                '- После проведения монтажных работ убедиться в восстановлении услуг согласно ППР %указать № ППР%.'] = '- После проведения монтажных работ убедиться в восстановлении услуг согласно ППР %указать № ППР%.'
            static_vars['указать № ППР'] = value_vars.get('ppr')
        kad = value_vars.get('kad')
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
            if value_vars.get('model_csw') == 'D-Link DGS-1100-06/ME':
                hidden_vars[
                '-ВНИМАНИЕ! Совместно с ОНИТС СПД удаленно настроить клиентский коммутатор.'] = '-ВНИМАНИЕ! Совместно с ОНИТС СПД удаленно настроить клиентский коммутатор.'
                hidden_vars[
                '- Совместно с %ОИПМ/ОИПД% удаленно настроить клиентский коммутатор.'] = '- Совместно с %ОИПМ/ОИПД% удаленно настроить клиентский коммутатор.'
            result_services.append(analyzer_vars(stroka, static_vars, hidden_vars))
        elif value_vars.get('type_install_csw') == 'Перевод на гигабит переключение с меди на ВОЛС' or value_vars.get(
            'type_install_csw') == 'Перенос на новый узел':
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
            if logic_csw_1000 or value_vars.get('logic_change_gi_csw') and value_vars.get('model_csw') == 'D-Link DGS-1100-06/ME':
                hidden_vars[
                    '-ВНИМАНИЕ! Совместно с ОНИТС СПД удаленно настроить клиентский коммутатор.'] = '-ВНИМАНИЕ! Совместно с ОНИТС СПД удаленно настроить клиентский коммутатор.'
                hidden_vars[
                    '- Совместно с %ОИПМ/ОИПД% удаленно настроить клиентский коммутатор.'] = '- Совместно с %ОИПМ/ОИПД% удаленно настроить клиентский коммутатор.'
            result_services.append(analyzer_vars(stroka, static_vars, hidden_vars))
    value_vars.update({'pps': pps})
    value_vars.update({'kad': kad})
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
    pps = _readable_node(value_vars.get('pps'))
    templates = value_vars.get('templates')
    readable_services = value_vars.get('readable_services')
    change_log_shpd = value_vars.get('change_log_shpd')
    static_vars['указать узел связи'] = pps
    static_vars['указать название коммутатора'] = kad
    static_vars['указать модель коммутатора'] = value_vars.get('model_csw')
    static_vars['указать № порта'] = value_vars.get('port_csw')
    name_exist_csw = value_vars.get('selected_ono')[0][-2]
    static_vars['указать название клиентского коммутатора'] = name_exist_csw
    services, service_shpd_change = _separate_services_and_subnet_dhcp(readable_services, change_log_shpd)
    if service_shpd_change:
        hidden_vars['- Выделить новую адресацию с маской %указать новую маску% вместо %указать существующий ресурс%.'] = '- Выделить новую адресацию с маской %указать новую маску% вместо %указать существующий ресурс%.'
        static_vars['указать новую маску'] = '/32' if change_log_shpd == 'Новая подсеть /32' else '/30'
        static_vars['указать существующий ресурс'] = ' '.join(service_shpd_change)
        hidden_vars['- После смены реквизитов:'] = '- После смены реквизитов:'
        hidden_vars['- разобрать ресурс %указать существующий ресурс% на договоре.'] = '- разобрать ресурс %указать существующий ресурс% на договоре.'

    if value_vars.get('ppr'):
        hidden_vars[
            '- Требуется отключение согласно ППР %указать № ППР% согласовать проведение работ.'] = '- Требуется отключение согласно ППР %указать № ППР% согласовать проведение работ.'
        hidden_vars[
            '- Совместно с ОНИТС СПД убедиться в восстановлении связи согласно ППР %указать № ППР%.'] = '- Совместно с ОНИТС СПД убедиться в восстановлении связи согласно ППР %указать № ППР%.'
        hidden_vars[
            '- После проведения монтажных работ убедиться в восстановлении услуг согласно ППР %указать № ППР%.'] = '- После проведения монтажных работ убедиться в восстановлении услуг согласно ППР %указать № ППР%.'
        static_vars['указать № ППР'] = value_vars.get('ppr')

    if sreda == '2' or sreda == '4':
        static_vars['ОИПМ/ОИПД'] = 'ОИПМ'
        static_vars['указать конвертер/передатчик на стороне узла связи'] = value_vars.get('device_pps')
        static_vars['указать конвертер/передатчик на стороне клиента'] = value_vars.get('device_client')
    else:
        static_vars['ОИПМ/ОИПД'] = 'ОИПД'

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
        static_vars['перенесен в новую точку подключения/переведен на гигабит/переключен на узел'] = 'переключен на узел {}'.format(pps)
    elif value_vars.get('type_passage') == 'Перевод на гигабит' or value_vars.get('logic_change_gi_csw'):
        static_vars['Перенос/Перевод на гигабит'] = 'Перевод на гигабит'
        static_vars['перенесен в новую точку подключения/переведен на гигабит/переключен на узел'] = 'переведен на гигабит'

    if value_vars.get('logic_change_gi_csw'):
        static_vars['100/1000'] = '1000'
    else:
        static_vars['100/1000'] = '100'
    if not value_vars.get('type_ticket') == 'ПТО':
        hidden_vars['МКО:'] = 'МКО:'
        hidden_vars['- Проинформировать клиента о простое сервисов на время проведения работ.'] = '- Проинформировать клиента о простое сервисов на время проведения работ.'
        hidden_vars['- Согласовать время проведение работ.'] = '- Согласовать время проведение работ.'
    if value_vars.get('ppr'):
        hidden_vars['- Согласовать проведение работ - ППР %указать ППР%.'] = '- Согласовать проведение работ - ППР %указать ППР%.'
        static_vars['указать ППР'] = value_vars.get('ppr')
    if name_exist_csw.split('-')[1] != kad.split('-')[1]:
        hidden_vars['- Перед проведением работ запросить ОНИТС СПД сменить реквизиты клиентского коммутатора %указать название клиентского коммутатора% [и тел. шлюза %указать название тел шлюза%] на ZIP.'] = '- Перед проведением работ запросить ОНИТС СПД сменить реквизиты клиентского коммутатора %указать название клиентского коммутатора% [и тел. шлюза %указать название тел шлюза%] на ZIP.'
        hidden_vars[
            '- Выделить для клиентского коммутатора[ и тел. шлюза %указать название тел шлюза%] новые реквизиты управления.'] = '- Выделить для клиентского коммутатора[ и тел. шлюза %указать название тел шлюза%] новые реквизиты управления.'
        hidden_vars['- Сменить реквизиты клиентского коммутатора [и тел. шлюза %указать название тел шлюза%].'] = '- Сменить реквизиты клиентского коммутатора [и тел. шлюза %указать название тел шлюза%].'
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
            hidden_vars['и тел. шлюза %указать название тел шлюза%'] = 'и тел. шлюза %указать название тел шлюза%'
            hidden_vars['и тел. шлюз %указать название тел шлюза%'] = 'и тел. шлюз %указать название тел шлюза%'
            static_vars['указать название тел шлюза'] = ', '.join(vgws)
        elif vgws and len(vgws) > 1:
            hidden_vars['и тел. шлюза %указать название тел шлюза%'] = 'и тел. шлюзов %указать название тел шлюза%'
            hidden_vars['и тел. шлюз %указать название тел шлюза%'] = 'и тел. шлюзы %указать название тел шлюза%'
            static_vars['указать название тел шлюза'] = ', '.join(vgws)
    if value_vars.get('type_passage') == 'Перенос точки подключения':
        static_vars['переносу/переводу на гигабит'] = 'переносу'
        hidden_vars['- Актуализировать информацию в Cordis и системах учета.'] = '- Актуализировать информацию в Cordis и системах учета.'

        hidden_vars['от %указать узел связи% '] = 'от %указать узел связи% '
        hidden_vars[
            '- Подключить организованную линию для клиента в коммутатор %указать название коммутатора%, порт задействовать %указать порт коммутатора%.'] = '- Подключить организованную линию для клиента в коммутатор %указать название коммутатора%, порт задействовать %указать порт коммутатора%.'
        hidden_vars['Старый порт: порт %указать старый порт коммутатора% коммутатора %указать название старого коммутатора%.'] = 'Старый порт: порт %указать старый порт коммутатора% коммутатора %указать название старого коммутатора%.'
        static_vars['указать старый порт коммутатора'] = value_vars.get('head').split('\n')[5].split()[2]
        static_vars['указать название старого коммутатора'] = value_vars.get('head').split('\n')[4].split()[2]
        hidden_vars['Новый порт: порт %указать порт коммутатора% коммутатора %указать название коммутатора%.'] = 'Новый порт: порт %указать порт коммутатора% коммутатора %указать название коммутатора%.'
        static_vars['указать порт коммутатора'] = port
        hidden_vars['- Перенести в новое помещении клиента коммутатор %указать название клиентского коммутатора%.'] = '- Перенести в новое помещении клиента коммутатор %указать название клиентского коммутатора%.'
        hidden_vars['- Включить линию для клиента в порт %указать № порта% коммутатора %указать название клиентского коммутатора%.'] = '- Включить линию для клиента в порт %указать № порта% коммутатора %указать название клиентского коммутатора%.'
        hidden_vars['- Переключить услуги клиента "порт в порт".'] = '- Переключить услуги клиента "порт в порт".'
        if sreda == '1':
            hidden_vars[
                '- Организовать %медную линию связи/ВОЛС% [от %указать узел связи% ]до клиентcкого коммутатора по решению ОТПМ.'] = '- Организовать %медную линию связи/ВОЛС% [от %указать узел связи% ]до клиентcкого коммутатора по решению ОТПМ.'
            hidden_vars['от %указать узел связи% '] = 'от %указать узел связи% '
            static_vars['медную линию связи/ВОЛС'] = 'медную линию связи'
            static_vars['ОИПМ/ОИПД'] = 'ОИПД'
        elif sreda == '2' or sreda == '4':
            hidden_vars[
                '- Организовать %медную линию связи/ВОЛС% [от %указать узел связи% ]до клиентcкого коммутатора по решению ОТПМ.'] = '- Организовать %медную линию связи/ВОЛС% [от %указать узел связи% ]до клиентcкого коммутатора по решению ОТПМ.'
            hidden_vars['от %указать узел связи% '] = 'от %указать узел связи% '
            static_vars['медную линию связи/ВОЛС'] = 'ВОЛС'
            hidden_vars['- Установить на стороне %указать узел связи% %указать конвертер/передатчик на стороне узла связи%'] = '- Установить на стороне %указать узел связи% %указать конвертер/передатчик на стороне узла связи%'
            if sreda != value_vars.get('exist_sreda'):
                hidden_vars['- В %указать название клиентского коммутатора% установить %указать конвертер/передатчик на стороне клиента%.'] = '- В %указать название клиентского коммутатора% установить %указать конвертер/передатчик на стороне клиента%.'
        elif sreda == '3':
            hidden_vars[
                '- Создать заявку в Cordis на ОНИТС СПД для выделения реквизитов беспроводных точек доступа WDS/WDA.'] = '- Создать заявку в Cordis на ОНИТС СПД для выделения реквизитов беспроводных точек доступа WDS/WDA.'
            if value_vars.get('access_point') == 'Infinet H11':
                hidden_vars[
                    '- Доставить в офис ОНИТС СПД беспроводные точки Infinet H11 для их настройки.'] = '- Доставить в офис ОНИТС СПД беспроводные точки Infinet H11 для их настройки.'
                hidden_vars[
                    'После выполнения подготовительных работ в рамках заявки в Cordis на ОНИТС СПД и настройки точек в офисе ОНИТС СПД:'] = 'После выполнения подготовительных работ в рамках заявки в Cordis на ОНИТС СПД и настройки точек в офисе ОНИТС СПД:'
            else:
                hidden_vars[
                    'После выполнения подготовительных работ в рамках заявки в Cordis на ОНИТС СПД:'] = 'После выполнения подготовительных работ в рамках заявки в Cordis на ОНИТС СПД:'
            hidden_vars[
                '- Установить на стороне %указать узел связи% и на стороне клиента беспроводные точки доступа %указать модель беспроводных точек% по решению ОТПМ.'] = '- Установить на стороне %указать узел связи% и на стороне клиента беспроводные точки доступа %указать модель беспроводных точек% по решению ОТПМ.'
            static_vars['указать модель беспроводных точек'] = value_vars.get('access_point')
            hidden_vars[
                '- По заявке в Cordis выделить реквизиты для управления беспроводными точками.'] = '- По заявке в Cordis выделить реквизиты для управления беспроводными точками.'
            hidden_vars[
                '- Совместно с ОИПД подключить к СПД и запустить беспроводные станции (WDS/WDA).'] = '- Совместно с ОИПД подключить к СПД и запустить беспроводные станции (WDS/WDA).'
            hidden_vars['от %указать узел связи% '] = 'от беспроводной точки '
            hidden_vars[
                '- Организовать %медную линию связи/ВОЛС% от %указать узел связи% до беспроводной точки по решению ОТПМ.'] = '- Организовать %медную линию связи/ВОЛС% от %указать узел связи% до беспроводной точки по решению ОТПМ.'
            hidden_vars['- На стороне клиента организовать медный патч-корд от WDA до клиентского коммутатора.'] = '- На стороне клиента организовать медный патч-корд от WDA до клиентского коммутатора.'
            static_vars['ОИПМ/ОИПД'] = 'ОИПД'
            static_vars['медную линию связи/ВОЛС'] = 'медную линию связи'
    elif value_vars.get('type_passage') == 'Перенос логического подключения':
        static_vars['переносу/переводу на гигабит'] = 'переносу логического подключения'
        hidden_vars['- Актуализировать информацию в Cordis и системах учета.'] = '- Актуализировать информацию в Cordis и системах учета.'
        hidden_vars[
            '- Подключить организованную линию для клиента в коммутатор %указать название коммутатора%, порт задействовать %указать порт коммутатора%.'] = '- Подключить организованную линию для клиента в коммутатор %указать название коммутатора%, порт задействовать %указать порт коммутатора%.'
        hidden_vars['Старый порт: порт %указать старый порт коммутатора% коммутатора %указать название старого коммутатора%.'] = 'Старый порт: порт %указать старый порт коммутатора% коммутатора %указать название старого коммутатора%.'
        static_vars['указать старый порт коммутатора'] = value_vars.get('head').split('\n')[5].split()[2]
        static_vars['указать название старого коммутатора'] = value_vars.get('head').split('\n')[4].split()[2]
        hidden_vars['Новый порт: порт %указать порт коммутатора% коммутатора %указать название коммутатора%.'] = 'Новый порт: порт %указать порт коммутатора% коммутатора %указать название коммутатора%.'
        static_vars['указать порт коммутатора'] = port
        if sreda == '1':
            hidden_vars[
                '- Организовать %медную линию связи/ВОЛС% [от %указать узел связи% ]до клиентcкого коммутатора по решению ОТПМ.'] = '- Организовать %медную линию связи/ВОЛС% [от %указать узел связи% ]до клиентcкого коммутатора по решению ОТПМ.'
            hidden_vars['от %указать узел связи% '] = 'от %указать узел связи% '
            static_vars['медную линию связи/ВОЛС'] = 'медную линию связи'
            static_vars['ОИПМ/ОИПД'] = 'ОИПД'
        elif sreda == '2' or sreda == '4':
            hidden_vars[
                '- Организовать %медную линию связи/ВОЛС% [от %указать узел связи% ]до клиентcкого коммутатора по решению ОТПМ.'] = '- Организовать %медную линию связи/ВОЛС% [от %указать узел связи% ]до клиентcкого коммутатора по решению ОТПМ.'
            hidden_vars['от %указать узел связи% '] = 'от %указать узел связи% '
            static_vars['медную линию связи/ВОЛС'] = 'ВОЛС'
            hidden_vars['- Установить на стороне %указать узел связи% %указать конвертер/передатчик на стороне узла связи%'] = '- Установить на стороне %указать узел связи% %указать конвертер/передатчик на стороне узла связи%'
            if value_vars.get('exist_sreda') == '1' or value_vars.get('exist_sreda') == '3':
                hidden_vars['- В %указать название клиентского коммутатора% установить %указать конвертер/передатчик на стороне клиента%.'] = '- В %указать название клиентского коммутатора% установить %указать конвертер/передатчик на стороне клиента%.'
                hidden_vars['- Включить линию для клиента в порт %указать № порта% коммутатора %указать название клиентского коммутатора%.'] = '- Включить линию для клиента в порт %указать № порта% коммутатора %указать название клиентского коммутатора%.'
        elif sreda == '3':
            hidden_vars[
                '- Создать заявку в Cordis на ОНИТС СПД для выделения реквизитов беспроводных точек доступа WDS/WDA.'] = '- Создать заявку в Cordis на ОНИТС СПД для выделения реквизитов беспроводных точек доступа WDS/WDA.'
            if value_vars.get('access_point') == 'Infinet H11':
                hidden_vars[
                    '- Доставить в офис ОНИТС СПД беспроводные точки Infinet H11 для их настройки.'] = '- Доставить в офис ОНИТС СПД беспроводные точки Infinet H11 для их настройки.'
                hidden_vars[
                    'После выполнения подготовительных работ в рамках заявки в Cordis на ОНИТС СПД и настройки точек в офисе ОНИТС СПД:'] = 'После выполнения подготовительных работ в рамках заявки в Cordis на ОНИТС СПД и настройки точек в офисе ОНИТС СПД:'
            else:
                hidden_vars[
                    'После выполнения подготовительных работ в рамках заявки в Cordis на ОНИТС СПД:'] = 'После выполнения подготовительных работ в рамках заявки в Cordis на ОНИТС СПД:'
            hidden_vars[
                '- Установить на стороне %указать узел связи% и на стороне клиента беспроводные точки доступа %указать модель беспроводных точек% по решению ОТПМ.'] = '- Установить на стороне %указать узел связи% и на стороне клиента беспроводные точки доступа %указать модель беспроводных точек% по решению ОТПМ.'
            static_vars['указать модель беспроводных точек'] = value_vars.get('access_point')
            hidden_vars['- Организовать %медную линию связи/ВОЛС% от %указать узел связи% до беспроводной точки по решению ОТПМ.'] = '- Организовать %медную линию связи/ВОЛС% от %указать узел связи% до беспроводной точки по решению ОТПМ.'
            hidden_vars['- На стороне клиента организовать медный патч-корд от WDA до клиентского коммутатора.'] = '- На стороне клиента организовать медный патч-корд от WDA до клиентского коммутатора.'
            hidden_vars[
                '- По заявке в Cordis выделить реквизиты для управления беспроводными точками.'] = '- По заявке в Cordis выделить реквизиты для управления беспроводными точками.'
            hidden_vars[
                '- Совместно с ОИПД подключить к СПД и запустить беспроводные станции (WDS/WDA).'] = '- Совместно с ОИПД подключить к СПД и запустить беспроводные станции (WDS/WDA).'
            static_vars['ОИПМ/ОИПД'] = 'ОИПД'
            static_vars['медную линию связи/ВОЛС'] = 'медную линию связи'
    elif value_vars.get('type_passage') == 'Перевод на гигабит' or value_vars.get('logic_change_gi_csw'):
        static_vars['переносу/переводу на гигабит'] = 'переводу на гигабит'
        hidden_vars['- Актуализировать информацию в Cordis и системах учета.'] = '- Актуализировать информацию в Cordis и системах учета.'
        hidden_vars['Старый порт: порт %указать старый порт коммутатора% коммутатора %указать название старого коммутатора%.'] = 'Старый порт: порт %указать старый порт коммутатора% коммутатора %указать название старого коммутатора%.'
        static_vars['указать старый порт коммутатора'] = value_vars.get('head').split('\n')[5].split()[2]
        static_vars['указать название старого коммутатора'] = value_vars.get('head').split('\n')[4].split()[2]
        hidden_vars['Новый порт: порт %указать порт коммутатора% коммутатора %указать название коммутатора%.'] = 'Новый порт: порт %указать порт коммутатора% коммутатора %указать название коммутатора%.'
        static_vars['указать порт коммутатора'] = port
        hidden_vars[
            '- Сменить %режим работы магистрального порта/магистральный порт% на клиентском коммутаторе %указать название клиентского коммутатора%.'] = '- Сменить %режим работы магистрального порта/магистральный порт% на клиентском коммутаторе %указать название клиентского коммутатора%.'
        if value_vars.get('exist_sreda') == '1' or value_vars.get('exist_sreda') == '3':
            static_vars['режим работы магистрального порта/магистральный порт'] = 'магистральный порт'
        else:
            static_vars['режим работы магистрального порта/магистральный порт'] = 'режим работы магистрального порта'

        if value_vars.get('logic_change_csw') == True:
            hidden_vars['- Перенести в новое помещении клиента коммутатор %указать название клиентского коммутатора%.'] = '- Перенести в новое помещении клиента коммутатор %указать название клиентского коммутатора%.'
            hidden_vars['- Переключить услуги клиента "порт в порт".'] = '- Переключить услуги клиента "порт в порт".'

        if value_vars.get('head').split('\n')[3] == '- {}'.format(pps) and (value_vars.get('exist_sreda_csw') == '2' or value_vars.get('exist_sreda_csw') == '4'):
            hidden_vars[
                '- Использовать существующую %медную линию связи/ВОЛС% от %указать узел связи% до клиентcкого коммутатора.'] = '- Использовать существующую %медную линию связи/ВОЛС% от %указать узел связи% до клиентcкого коммутатора.'
            hidden_vars[
                '- Переключить линию для клиента в порт %указать порт коммутатора% коммутатора %указать название коммутатора%.'] = '- Переключить линию для клиента в порт %указать порт коммутатора% коммутатора %указать название коммутатора%.'
            if value_vars.get('exist_sreda_csw') == '2':
                hidden_vars['- Установить на стороне %указать узел связи% %указать конвертер/передатчик на стороне узла связи%'] = '- Установить на стороне %указать узел связи% %указать конвертер/передатчик на стороне узла связи%'

        else:
            if value_vars.get('exist_sreda_csw') == '1' or value_vars.get('exist_sreda_csw') != value_vars.get('sreda'):
                hidden_vars['- В %указать название клиентского коммутатора% установить %указать конвертер/передатчик на стороне клиента%.'] = '- В %указать название клиентского коммутатора% установить %указать конвертер/передатчик на стороне клиента%.'
                hidden_vars['- Включить линию для клиента в порт %указать № порта% коммутатора %указать название клиентского коммутатора%.'] = '- Включить линию для клиента в порт %указать № порта% коммутатора %указать название клиентского коммутатора%.'

            if value_vars.get('exist_sreda_csw') == '2' or value_vars.get('exist_sreda_csw') == '4':
                hidden_vars[
                    '- Запросить ОНИТС СПД перенастроить режим работы магистрального порта на клиентском коммутаторе %указать название клиентского коммутатора%.'] = '- Запросить ОНИТС СПД перенастроить режим работы магистрального порта на клиентском коммутаторе %указать название клиентского коммутатора%.'
            hidden_vars[
                '- Организовать %медную линию связи/ВОЛС% [от %указать узел связи% ]до клиентcкого коммутатора по решению ОТПМ.'] = '- Организовать %медную линию связи/ВОЛС% [от %указать узел связи% ]до клиентcкого коммутатора по решению ОТПМ.'
            hidden_vars['от %указать узел связи% '] = 'от %указать узел связи% '
            hidden_vars[
                '- Подключить организованную линию для клиента в коммутатор %указать название коммутатора%, порт задействовать %указать порт коммутатора%.'] = '- Подключить организованную линию для клиента в коммутатор %указать название коммутатора%, порт задействовать %указать порт коммутатора%.'
            hidden_vars['- Установить на стороне %указать узел связи% %указать конвертер/передатчик на стороне узла связи%'] = '- Установить на стороне %указать узел связи% %указать конвертер/передатчик на стороне узла связи%'

        if sreda == '1':
            hidden_vars['от %указать узел связи% '] = 'от %указать узел связи% '
            static_vars['медную линию связи/ВОЛС'] = 'медную линию связи'
        elif sreda == '2' or sreda == '4':
            hidden_vars['от %указать узел связи% '] = 'от %указать узел связи% '
            static_vars['медную линию связи/ВОЛС'] = 'ВОЛС'

    stroka = templates.get("%Перенос/Перевод на гигабит% клиентского коммутатора")
    result_services.append(analyzer_vars(stroka, static_vars, hidden_vars))
    return result_services, value_vars


def enviroment(result_services, value_vars):
    """Данный метод формирует блок ТТР отдельной линии(медь, волс, wifi)"""
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
            stroka = templates.get("Присоединение к СПД по оптической линии связи с простоем связи услуг.")
            static_vars['указать № ППР'] = ppr
        else:
            stroka = templates.get("Присоединение к СПД по оптической линии связи.")
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
        static_vars = {}
        if ppr:
            stroka = templates.get("Присоединение к СПД по беспроводной среде передачи данных с простоем связи услуг.")
            static_vars['указать № ППР'] = ppr
        else:
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
        elif value_vars.get('type_passage') == 'Перенос логического подключения' and value_vars.get(
                'change_log') == 'Порт/КАД меняются':
            need.append(
                f"- перенести логическое подключение на узел {_readable_node(value_vars.get('pps'))};")
        elif value_vars.get('type_passage') == 'Перевод на гигабит':
            need.append(
                f"- расширить полосу сервиса {value_vars.get('name_passage_service')};")
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
        static_vars['ОИПМ/ОИПД'] = 'ОИПМ'
    else:
        static_vars['ОИПМ/ОИПД'] = 'ОИПД'
    if value_vars.get('type_passage') == 'Перенос сервиса в новую точку' or value_vars.get('type_passage') == 'Перенос точки подключения':
        stroka = templates.get("Перенос ^сервиса^ %указать название сервиса% в новую точку подключения")
        if value_vars.get('type_passage') == 'Перенос точки подключения':
            if value_vars.get('change_log') != 'Порт и КАД не меняется':
                hidden_vars[
                    '-- перенести ^сервис^ %указать сервис% для клиента в новую точку подключения.'] = '-- перенести ^сервис^ %указать сервис% для клиента в новую точку подключения.'

                hidden_vars[
                    'В заявке Cordis указать время проведения работ по переносу ^сервиса^.'] = 'В заявке Cordis указать время проведения работ по переносу ^сервиса^.'
                hidden_vars[
                    '- После переезда клиента актуализировать информацию в Cordis и системах учета.'] = '- После переезда клиента актуализировать информацию в Cordis и системах учета.'
                hidden_vars[
                    '- Сообщить в ОЛИ СПД об освободившемся порте на коммутаторе %указать существующий КАД% после переезда клиента.'] = '- Сообщить в ОЛИ СПД об освободившемся порте на коммутаторе %указать существующий КАД% после переезда клиента.'
                static_vars['указать существующий КАД'] = value_vars.get('head').split('\n')[4].split()[2]
                if change_log_shpd == None:
                    change_log_shpd = 'существующая адресация'
                services, service_shpd_change = _separate_services_and_subnet_dhcp(readable_services, change_log_shpd)
                if service_shpd_change:
                    hidden_vars[', необходимость смены реквизитов'] = ', необходимость смены реквизитов'
                    hidden_vars['ОНИТС СПД подготовиться к работам:'] = 'ОНИТС СПД подготовиться к работам:'
                    hidden_vars['- По заявке в Cordis выделить подсеть с маской %указать новую маску%.'] = '- По заявке в Cordis выделить подсеть с маской %указать новую маску%.'
                    static_vars['указать новую маску'] = '/30' if value_vars.get('change_log_shpd') == 'Новая подсеть /30' else '/32'
                    hidden_vars['-- по согласованию с клиентом сменить реквизиты для услуги "ШПД в Интернет" на новую подсеть с маской %указать новую маску%.'] = '-- по согласованию с клиентом сменить реквизиты для услуги "ШПД в Интернет" на новую подсеть с маской %указать новую маску%.'
                    hidden_vars['- После смены реквизитов:'] = '- После смены реквизитов:'
                    hidden_vars['- разобрать ресурс %указать существующий ресурс% на договоре.'] = '- разобрать ресурс %указать существующий ресурс% на договоре.'
                    static_vars['указать существующий ресурс'] = ', '.join(service_shpd_change)
            else:
                services = []
                for key, value in readable_services.items():
                    if key != '"Телефония"':
                        if type(value) == str:
                            services.append(key + ' ' + value)
                        elif type(value) == list:
                            services.append(key + ''.join(value))
            static_vars['указать сервис'] = ', '.join(services)
            static_vars['указать название сервиса'] = ', '.join([x for x in readable_services.keys() if x != '"Телефония"'])
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
                        static_vars['указать название сервиса'] = key
                        value_vars.update({'name_passage_service': key +' '+ value })
                    else:
                        other_services.append(key + ' ' + value)

                elif type(value) == list:
                    for val in value:
                        if value_vars.get('selected_ono')[0][-4] in val:
                            services.append(key + ' ' + val)
                            static_vars['указать название сервиса'] = key
                            value_vars.update({'name_passage_service': key +' '+ val})
                        else:
                            other_services.append(key + ' ' + val)

            if value_vars.get('change_log') != 'Порт и КАД не меняется':
                hidden_vars[
                    '-- перенести ^сервис^ %указать сервис% для клиента в новую точку подключения.'] = '-- перенести ^сервис^ %указать сервис% для клиента в новую точку подключения.'

                hidden_vars[
                    'В заявке Cordis указать время проведения работ по переносу ^сервиса^.'] = 'В заявке Cordis указать время проведения работ по переносу ^сервиса^.'
                hidden_vars[
                    '- После переезда клиента актуализировать информацию в Cordis и системах учета.'] = '- После переезда клиента актуализировать информацию в Cordis и системах учета.'
                if value_vars.get('head').split('\n')[4].split()[2] == value_vars.get('selected_ono')[0][-2] or other_services == False:
                    hidden_vars[
                    '- Сообщить в ОЛИ СПД об освободившемся порте на коммутаторе %указать существующий КАД% после переезда клиента.'] = '- Сообщить в ОЛИ СПД об освободившемся порте на коммутаторе %указать существующий КАД% после переезда клиента.'
                static_vars['указать существующий КАД'] = value_vars.get('head').split('\n')[4].split()[2]

                if services[0].startswith('"ШПД в интернет"'):
                    if value_vars.get('change_log_shpd') != 'существующая адресация':
                        hidden_vars[', необходимость смены реквизитов'] = ', необходимость смены реквизитов'
                        hidden_vars['ОНИТС СПД подготовиться к работам:'] = 'ОНИТС СПД подготовиться к работам:'
                        hidden_vars['- По заявке в Cordis выделить подсеть с маской %указать новую маску%.'] = '- По заявке в Cordis выделить подсеть с маской %указать новую маску%.'
                        static_vars['указать новую маску'] = '/30' if value_vars.get('change_log_shpd') == 'Новая подсеть /30' else '/32'
                        static_vars['указать сервис'] = static_vars['указать название сервиса']
                        hidden_vars['-- по согласованию с клиентом сменить реквизиты для услуги "ШПД в Интернет" на новую подсеть с маской %указать новую маску%.'] = '-- по согласованию с клиентом сменить реквизиты для услуги "ШПД в Интернет" на новую подсеть с маской %указать новую маску%.'
                        hidden_vars['- После смены реквизитов:'] = '- После смены реквизитов:'
                        hidden_vars['- разобрать ресурс %указать существующий ресурс% на договоре.'] = '- разобрать ресурс %указать существующий ресурс% на договоре.'
                        static_vars['указать существующий ресурс'] = value_vars.get('selected_ono')[0][-4]
                    else:
                        static_vars['указать сервис'] = ', '.join(services)
            else:
                static_vars['указать сервис'] = ', '.join(services)
            stroka = analyzer_vars(stroka, static_vars, hidden_vars)
            counter_plur = len(services)
            result_services.append(pluralizer_vars(stroka, counter_plur))
    elif value_vars.get('type_passage') == 'Перенос логического подключения':
        stroka = templates.get("Перенос логического подключения клиента на %указать узел связи%")
        if value_vars.get('type_ticket') == 'ПТО':
            pass
        else:
            hidden_vars['МКО:'] = 'МКО:'
            hidden_vars['- Проинформировать клиента о простое сервиса на время проведения работ.'] = '- Проинформировать клиента о простое сервиса на время проведения работ.'
            hidden_vars['- Согласовать время проведение работ.'] = '- Согласовать время проведение работ.'
            hidden_vars['- Создать заявку в Cordis на ОНИТС СПД для изменения логического подключения сервиса %указать сервис% клиента.'] = '- Создать заявку в Cordis на ОНИТС СПД для изменения логического подключения сервиса %указать сервис% клиента.'
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
        if service_shpd_change and value_vars.get('change_log_shpd') == 'Новая подсеть /32':
            hidden_vars['- Выделить подсеть с маской /32.'] = '- Выделить подсеть с маской /32.'
            hidden_vars['- Cменить реквизиты для услуги "ШПД в Интернет" на новую подсеть с маской /32.'] = '- Cменить реквизиты для услуги "ШПД в Интернет" на новую подсеть с маской /32.'
            hidden_vars['- разобрать ресурс %указать существующий ресурс% на договоре.'] = '- разобрать ресурс %указать существующий ресурс% на договоре.'
            static_vars['указать существующий ресурс'] = ', '.join(service_shpd_change)
        static_vars['указать сервис'] = ', '.join(services)
        static_vars['указать название сервиса'] = ', '.join(readable_services.keys())
        static_vars['указать узел связи'] = _readable_node(value_vars.get('pps'))
        static_vars['указать существующий КАД'] = value_vars.get('head').split('\n')[4].split()[2]
        result_services.append(analyzer_vars(stroka, static_vars, hidden_vars))
    elif value_vars.get('type_passage') == 'Перевод на гигабит':
        stroka = templates.get("Расширение полосы сервиса %указать название сервиса%")
        desc_service, name_passage_service = get_selected_readable_service(readable_services, value_vars.get('selected_ono'))
        static_vars['указать название сервиса'] = desc_service
        if desc_service == '"ШПД в интернет"':
            hidden_vars['- Расширить полосу ШПД в Cordis.'] = '- Расширить полосу ШПД в Cordis.'
            if value_vars.get('change_log_shpd') != 'существующая адресация':
                hidden_vars[', необходимость смены реквизитов'] = ', необходимость смены реквизитов'
                hidden_vars[
                    '- Выделить подсеть с маской %указать новую маску%.'] = '- Выделить подсеть с маской %указать новую маску%.'
                static_vars['указать новую маску'] = '/30' if value_vars.get(
                    'change_log_shpd') == 'Новая подсеть /30' else '/32'
                static_vars['указать сервис'] = static_vars['указать название сервиса']
                hidden_vars[
                    '-- по согласованию с клиентом сменить реквизиты для услуги "ШПД в Интернет" на новую подсеть с маской %указать новую маску%.'] = '-- по согласованию с клиентом сменить реквизиты для услуги "ШПД в Интернет" на новую подсеть с маской %указать новую маску%.'
                hidden_vars['- После смены реквизитов:'] = '- После смены реквизитов:'
                hidden_vars[
                    '- разобрать ресурс %указать существующий ресурс% на договоре.'] = '- разобрать ресурс %указать существующий ресурс% на договоре.'
                static_vars['указать существующий ресурс'] = value_vars.get('selected_ono')[0][-4]
            else:
                static_vars['указать сервис'] = name_passage_service
        else:
            hidden_vars['на %указать новую полосу сервиса%'] = 'на %указать новую полосу сервиса%'
            static_vars['указать новую полосу сервиса'] = value_vars.get('extend_speed')
            hidden_vars[
                '- Ограничить скорость и настроить маркировку трафика для %указать сервис% %полисером Subinterface/портом подключения%.'] = '- Ограничить скорость и настроить маркировку трафика для %указать сервис% %полисером Subinterface/портом подключения%.'
            if value_vars.get('extend_policer_cks_vk'):
                static_vars['полисером Subinterface/портом подключения'] = value_vars.get('extend_policer_cks_vk')
            if value_vars.get('extend_policer_vm'):
                static_vars['полисером Subinterface/портом подключения'] = value_vars.get('extend_policer_vm')
            static_vars['указать сервис'] = name_passage_service
        hidden_vars['ОНИТС СПД подготовка к работам:'] = 'ОНИТС СПД подготовка к работам:'
        hidden_vars['- По заявке в Cordis подготовить настройки на оборудовании для расширения сервиса %указать сервис% [на %указать новую полосу сервиса%].'] = '- По заявке в Cordis подготовить настройки на оборудовании для расширения сервиса %указать сервис% [на %указать новую полосу сервиса%].'

        hidden_vars['- Проинформировать клиента о простое сервиса на время проведения работ.'] = '- Проинформировать клиента о простое сервиса на время проведения работ.'
        hidden_vars['- Согласовать время проведение работ[, необходимость смены реквизитов].'] = '- Согласовать время проведение работ[, необходимость смены реквизитов].'
        hidden_vars['-- сопроводить работы %ОИПМ/ОИПД% по перенесу сервиса %указать сервис% в гигабитный порт %указать название коммутатора%.'] = '-- сопроводить работы %ОИПМ/ОИПД% по перенесу сервиса %указать сервис% в гигабитный порт %указать название коммутатора%.'
        value_vars.update({'name_passage_service': name_passage_service})
        static_vars['указать название коммутатора'] = value_vars.get('kad')
        if value_vars.get('selected_ono')[0][-2].startswith('CSW') or value_vars.get('selected_ono')[0][-2].startswith('WDA'):
            pass
        else:
            hidden_vars['- Сообщить в ОЛИ СПД об освободившемся порте на %существующий КАД%.'] = '- Сообщить в ОЛИ СПД об освободившемся порте на %существующий КАД%.'
        static_vars['существующий КАД'] = value_vars.get('head').split('\n')[4].split()[2]
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
    channel_vgw = value_vars.get('channel_vgw')
    templates = value_vars.get('templates')
    if service.endswith('|'):
        if value_vars.get('type_phone') == 'ak':
            if value_vars.get('logic_csw'):
                result_services.append(enviroment_csw(value_vars))
                value_vars.update({'result_services': result_services})
                static_vars[
                        'клиентского коммутатора / КАД (указать маркировку коммутатора)'] = 'клиентского коммутатора'
            else:
                result_services = enviroment(result_services, value_vars)
                value_vars.update({'result_services': result_services})
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
            stroka = templates.get(
                    "Перенос сервиса Телефония с использованием тел.шлюза на стороне клиента")
            static_vars['идентификатор тел. шлюза'] = 'установленный по решению выше'
            static_vars['указать модель тел. шлюза'] = vgw
            static_vars['указать модель идентификатор существующего тел. шлюза'] = value_vars.get('old_name_model_vgws')
            if 'ватс' in service.lower():
                static_vars['указать количество телефонных линий'] = ports_vgw
                if ports_vgw == '1':
                    static_vars['указать порты тел. шлюза'] = '1'
                else:
                    static_vars['указать порты тел. шлюза'] = '1-{}'.format(ports_vgw)
            else:
                static_vars['указать количество телефонных линий'] = channel_vgw
                if channel_vgw == '1':
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
        stroka = templates.get("Перенос сервиса Телефония с использованием голосового шлюза на ППС")
        static_vars['идентификатор тел. шлюза'] = 'установленный по решению выше'
        static_vars['указать модель идентификатор существующего тел. шлюза'] = value_vars.get('old_name_model_vgws')
        if 'ватс' in service.lower():
            static_vars['указать количество телефонных линий'] = ports_vgw
            if ports_vgw == '1':
                static_vars['указать порты тел. шлюза'] = '1'
            else:
                static_vars['указать порты тел. шлюза'] = '1-{}'.format(ports_vgw)
        else:
            static_vars['указать количество телефонных линий'] = channel_vgw
            if channel_vgw == '1':
                static_vars['указать порты тел. шлюза'] = '1'
            else:
                static_vars['указать порты тел. шлюза'] = '1-{}'.format(channel_vgw)
        stroka = analyzer_vars(stroka, static_vars, hidden_vars)
        regex_counter = 'Организовать (\d+)'
        match_counter = re.search(regex_counter, stroka)
        counter_plur = int(match_counter.group(1))
        result_services_ots.append(pluralizer_vars(stroka, counter_plur))
    elif service.endswith('\\'):
        stroka = templates.get("Перенос сервиса Телефония с использованием голосового шлюза на ППС")
        static_vars['указать модель идентификатор существующего тел. шлюза'] = value_vars.get('old_name_model_vgws')
        static_vars['указать порты тел. шлюза'] = value_vars.get('form_exist_vgw_port')
        static_vars['указать модель тел. шлюза'] = value_vars.get('form_exist_vgw_model')
        static_vars['идентификатор тел. шлюза'] = value_vars.get('form_exist_vgw_name')
        if 'ватс' in service.lower():
            static_vars['указать количество телефонных линий'] = ports_vgw
        else:
            static_vars['указать количество телефонных линий'] = channel_vgw
        stroka = analyzer_vars(stroka, static_vars, hidden_vars)
        regex_counter = 'Организовать (\d+)'
        match_counter = re.search(regex_counter, stroka)
        counter_plur = int(match_counter.group(1))
        result_services_ots.append(pluralizer_vars(stroka, counter_plur))
    return result_services, result_services_ots, value_vars


def _passage_enviroment(value_vars):
    """Данный метод формирует блок ТТР для изменение присоединения к СПД"""
    if value_vars.get('result_services'):
        result_services = value_vars.get('result_services')
    else:
        result_services = []
    sreda = value_vars.get('sreda')
    templates = value_vars.get('templates')
    pps = _readable_node(value_vars.get('pps'))
    port = value_vars.get('port')
    device_pps = value_vars.get('device_pps')
    selected_ono = value_vars.get('selected_ono')
    if 'Порт и КАД не меняется' == value_vars.get('change_log'):
        kad = value_vars.get('selected_ono')[0][-2]
    else:
        kad = value_vars.get('kad')
    stroka = templates.get("Изменение присоединения к СПД")
    static_vars = {}
    hidden_vars = {}
    if sreda == '2' or sreda == '4':
        static_vars['ОИПМ/ОИПД'] = 'ОИПМ'
    else:
        static_vars['ОИПМ/ОИПД'] = 'ОИПД'
    if value_vars.get('type_passage') == 'Перенос сервиса в новую точку' or value_vars.get('type_passage') == 'Перенос точки подключения':
        if value_vars.get('change_log') == 'Порт и КАД не меняется':
            hidden_vars['- Организовать %медную линию связи/ВОЛС% [от %указать узел связи% ]до клиентcкого оборудования [в новой точке подключения ]по решению ОАТТР.'] = '- Организовать %медную линию связи/ВОЛС% [от %указать узел связи% ]до клиентcкого оборудования [в новой точке подключения ]по решению ОАТТР.'
            if value_vars.get('exist_sreda') == '1':
                static_vars['медную линию связи/ВОЛС'] = 'медную линию связи'
            else:
                static_vars['медную линию связи/ВОЛС'] = 'ВОЛС'
            hidden_vars['в новой точке подключения '] = 'в новой точке подключения '
            hidden_vars['- Логическое подключение клиента не изменится.'] = '- Логическое подключение клиента не изменится.'
        elif value_vars.get('change_log') == 'Порт/КАД меняются':
            hidden_vars[
                '- Организовать %медную линию связи/ВОЛС% [от %указать узел связи% ]до клиентcкого оборудования [в новой точке подключения ]по решению ОАТТР.'] = '- Организовать %медную линию связи/ВОЛС% [от %указать узел связи% ]до клиентcкого оборудования [в новой точке подключения ]по решению ОАТТР.'
            if sreda == '1':
                static_vars['медную линию связи/ВОЛС'] = 'медную линию связи'
            else:
                static_vars['медную линию связи/ВОЛС'] = 'ВОЛС'
                hidden_vars['- Установить на стороне %указать узел связи% %указать конвертер/передатчик на стороне узла связи%'] = '- Установить на стороне %указать узел связи% %указать конвертер/передатчик на стороне узла связи%'
                static_vars['указать узел связи'] = pps
                static_vars['указать конвертер/передатчик на стороне узла связи'] = device_pps
            hidden_vars['от %указать узел связи% '] = 'от %указать узел связи% '
            static_vars['указать узел связи'] = pps
            hidden_vars['в новой точке подключения '] = 'в новой точке подключения '
            hidden_vars['- Подключить организованную линию для клиента в коммутатор %указать название коммутатора%, порт задействовать %указать порт коммутатора%.'] = '- Подключить организованную линию для клиента в коммутатор %указать название коммутатора%, порт задействовать %указать порт коммутатора%.'
            static_vars['указать название коммутатора'] = kad
            static_vars['указать порт коммутатора'] = port
            hidden_vars['Старый порт: порт %указать старый порт коммутатора% коммутатора %указать название старого коммутатора%.'] = 'Старый порт: порт %указать старый порт коммутатора% коммутатора %указать название старого коммутатора%.'
            static_vars['указать старый порт коммутатора'] = selected_ono[0][-1]
            static_vars['указать название старого коммутатора'] = selected_ono[0][-2]
            hidden_vars['Новый порт: порт %указать порт коммутатора% коммутатора %указать название коммутатора%.'] = 'Новый порт: порт %указать порт коммутатора% коммутатора %указать название коммутатора%.'
            static_vars['указать порт коммутатора'] = port
            static_vars['указать название коммутатора'] = kad
    elif value_vars.get('type_passage') == 'Перенос логического подключения':
        if value_vars.get('type_ticket') == 'ПТО':
            hidden_vars['ОИПМ подготовиться к работам:'] = 'ОИПМ подготовиться к работам:'
            hidden_vars['- Согласовать проведение работ - ППР %указать ППР%.'] = '- Согласовать проведение работ - ППР %указать ППР%.'
            static_vars['указать ППР'] = value_vars.get('ppr')
            hidden_vars['- Создать заявку в Cordis на ОНИТС СПД для изменения присоединения клиента.'] = '- Создать заявку в Cordis на ОНИТС СПД для изменения присоединения клиента.'
        hidden_vars[
            '- Организовать %медную линию связи/ВОЛС% [от %указать узел связи% ]до клиентcкого оборудования [в новой точке подключения ]по решению ОАТТР.'] = '- Организовать %медную линию связи/ВОЛС% [от %указать узел связи% ]до клиентcкого оборудования [в новой точке подключения ]по решению ОАТТР.'
        hidden_vars['от %указать узел связи% '] = 'от %указать узел связи% '
        static_vars['указать узел связи'] = pps
        hidden_vars['- Подключить организованную линию для клиента в коммутатор %указать название коммутатора%, порт задействовать %указать порт коммутатора%.'] = '- Подключить организованную линию для клиента в коммутатор %указать название коммутатора%, порт задействовать %указать порт коммутатора%.'
        static_vars['указать название коммутатора'] = kad
        static_vars['указать порт коммутатора'] = port
        hidden_vars[
            'Старый порт: порт %указать старый порт коммутатора% коммутатора %указать название старого коммутатора%.'] = 'Старый порт: порт %указать старый порт коммутатора% коммутатора %указать название старого коммутатора%.'
        static_vars['указать старый порт коммутатора'] = selected_ono[0][-1]
        static_vars['указать название старого коммутатора'] = selected_ono[0][-2]
        hidden_vars[
            'Новый порт: порт %указать порт коммутатора% коммутатора %указать название коммутатора%.'] = 'Новый порт: порт %указать порт коммутатора% коммутатора %указать название коммутатора%.'
        if sreda == '1':
            static_vars['медную линию связи/ВОЛС'] = 'медную линию связи'
        elif sreda == '2' or sreda == '4':
            static_vars['медную линию связи/ВОЛС'] = 'ВОЛС'
            hidden_vars['- Установить на стороне %указать узел связи% %указать конвертер/передатчик на стороне узла связи%'] = '- Установить на стороне %указать узел связи% %указать конвертер/передатчик на стороне узла связи%'
            static_vars['указать конвертер/передатчик на стороне узла связи'] = value_vars.get('device_pps')
            if value_vars.get('exist_sreda') != '2':
                hidden_vars['- На стороне клиента %установить/заменить% [%указать существующий конвертер/передатчик на стороне клиента% на ]%указать конвертер/передатчик на стороне клиента%'] = '- На стороне клиента %установить/заменить% [%указать существующий конвертер/передатчик на стороне клиента% на ]%указать конвертер/передатчик на стороне клиента%'
                static_vars['установить/заменить'] = 'установить'
                static_vars['указать конвертер/передатчик на стороне клиента'] = value_vars.get('device_client')
    elif value_vars.get('type_passage') == 'Перевод на гигабит':
        static_vars['медную линию связи/ВОЛС'] = 'ВОЛС'
        static_vars['указать узел связи'] = pps
        static_vars['указать название коммутатора'] = kad
        static_vars['указать порт коммутатора'] = port
        hidden_vars[
            '- На стороне клиента %установить/заменить% [%указать существующий конвертер/передатчик на стороне клиента% на ]%указать конвертер/передатчик на стороне клиента%'] = '- На стороне клиента %установить/заменить% [%указать существующий конвертер/передатчик на стороне клиента% на ]%указать конвертер/передатчик на стороне клиента%'
        if value_vars.get('head').split('\n')[3] == '- {}'.format(pps) and value_vars.get('exist_sreda') == '2':
            hidden_vars['- Использовать существующую %медную линию связи/ВОЛС% от %указать узел связи% до клиентского оборудования.'] = '- Использовать существующую %медную линию связи/ВОЛС% от %указать узел связи% до клиентского оборудования.'
            hidden_vars['- Переключить линию для клиента в порт %указать порт коммутатора% коммутатора %указать название коммутатора%.'] = '- Переключить линию для клиента в порт %указать порт коммутатора% коммутатора %указать название коммутатора%.'
            static_vars['установить/заменить'] = 'заменить'
            hidden_vars[
                '%указать существующий конвертер/передатчик на стороне клиента% на '] = '%указать существующий конвертер/передатчик на стороне клиента% на '
            static_vars['указать существующий конвертер/передатчик на стороне клиента'] = 'конвертер 1550 нм'
            static_vars['указать конвертер/передатчик на стороне узла связи'] = value_vars.get('device_pps')
            static_vars['указать конвертер/передатчик на стороне клиента'] = value_vars.get('device_client')
            hidden_vars[
                '- Установить на стороне %указать узел связи% %указать конвертер/передатчик на стороне узла связи%'] = '- Установить на стороне %указать узел связи% %указать конвертер/передатчик на стороне узла связи%'
            hidden_vars[
                'Старый порт: порт %указать старый порт коммутатора% коммутатора %указать название старого коммутатора%.'] = 'Старый порт: порт %указать старый порт коммутатора% коммутатора %указать название старого коммутатора%.'
            static_vars['указать старый порт коммутатора'] = selected_ono[0][-1]
            static_vars['указать название старого коммутатора'] = selected_ono[0][-2]
            hidden_vars[
                'Новый порт: порт %указать порт коммутатора% коммутатора %указать название коммутатора%.'] = 'Новый порт: порт %указать порт коммутатора% коммутатора %указать название коммутатора%.'
        elif value_vars.get('head').split('\n')[3] == '- {}'.format(pps) and value_vars.get('exist_sreda') == '4':
            hidden_vars['- Использовать существующую %медную линию связи/ВОЛС% от %указать узел связи% до клиентского оборудования.'] = '- Использовать существующую %медную линию связи/ВОЛС% от %указать узел связи% до клиентского оборудования.'
            static_vars['установить/заменить'] = 'заменить'
            hidden_vars['%указать существующий конвертер/передатчик на стороне клиента% на '] = '%указать существующий конвертер/передатчик на стороне клиента% на '
            static_vars['указать существующий конвертер/передатчик на стороне клиента'] = 'конвертер 1550 нм'
            hidden_vars['- Логическое подключение клиента не изменится.'] = '- Логическое подключение клиента не изменится.'
            static_vars['указать конвертер/передатчик на стороне клиента'] = 'конвертер SNR-CVT-1000SFP-mini с модулем SFP WDM, дальность до 3 км, 1550 нм'
        else:
            hidden_vars[
                '- Организовать %медную линию связи/ВОЛС% [от %указать узел связи% ]до клиентcкого оборудования [в новой точке подключения ]по решению ОАТТР.'] = '- Организовать %медную линию связи/ВОЛС% [от %указать узел связи% ]до клиентcкого оборудования [в новой точке подключения ]по решению ОАТТР.'
            hidden_vars['от %указать узел связи% '] = 'от %указать узел связи% '
            hidden_vars[
                '- Подключить организованную линию для клиента в коммутатор %указать название коммутатора%, порт задействовать %указать порт коммутатора%.'] = '- Подключить организованную линию для клиента в коммутатор %указать название коммутатора%, порт задействовать %указать порт коммутатора%.'
            static_vars['установить/заменить'] = 'установить'
            static_vars['указать конвертер/передатчик на стороне узла связи'] = value_vars.get('device_pps')
            hidden_vars[
                '- Установить на стороне %указать узел связи% %указать конвертер/передатчик на стороне узла связи%'] = '- Установить на стороне %указать узел связи% %указать конвертер/передатчик на стороне узла связи%'
            hidden_vars[
                'Старый порт: порт %указать старый порт коммутатора% коммутатора %указать название старого коммутатора%.'] = 'Старый порт: порт %указать старый порт коммутатора% коммутатора %указать название старого коммутатора%.'
            static_vars['указать старый порт коммутатора'] = selected_ono[0][-1]
            static_vars['указать название старого коммутатора'] = selected_ono[0][-2]
            static_vars['указать конвертер/передатчик на стороне клиента'] = value_vars.get('device_client')
            hidden_vars[
                'Новый порт: порт %указать порт коммутатора% коммутатора %указать название коммутатора%.'] = 'Новый порт: порт %указать порт коммутатора% коммутатора %указать название коммутатора%.'
    value_vars.update({'kad': kad})
    result_services.append(analyzer_vars(stroka, static_vars, hidden_vars))
    return result_services, value_vars


def _passage_services_on_csw(result_services, value_vars):
    """Данный метод формирует блоки ТТР перенос сервиса на КК и организации медной линии от КК для данного сервиса"""
    templates = value_vars.get('templates')
    readable_services = value_vars.get('readable_services')
    counter_exist_line = value_vars.get('counter_exist_line')
    sreda = value_vars.get('sreda')
    stroka = templates.get("Перенос ^сервиса^ %указать название сервиса% на клиентский коммутатор")
    if stroka:
        static_vars = {}
        hidden_vars = {}
        if 'Перенос, СПД' in value_vars.get('type_pass'):
            hidden_vars['МКО:'] = 'МКО:'
            hidden_vars['- Проинформировать клиента о простое ^сервиса^ на время проведения работ по переносу ^сервиса^ в новую точку подключения.'] = '- Проинформировать клиента о простое ^сервиса^ на время проведения работ по переносу ^сервиса^ в новую точку подключения.'
            hidden_vars['- Согласовать время проведение работ[, необходимость смены реквизитов].'] = '- Согласовать время проведение работ[, необходимость смены реквизитов].'
            hidden_vars['- Создать заявку в Cordis на ОНИТС СПД для переноса ^сервиса^ %указать название сервиса%.'] = '- Создать заявку в Cordis на ОНИТС СПД для переноса ^сервиса^ %указать название сервиса%.'
            hidden_vars['в новую точку подключения'] = 'в новую точку подключения'
        if value_vars.get('logic_csw') and 'Перенос, СПД' not in value_vars.get('type_pass') or value_vars.get('logic_csw') and value_vars.get('type_passage') == 'Перевод на гигабит' or value_vars.get('type_passage') == 'Перенос точки подключения':
            for i in range(counter_exist_line):
                result_services.append(enviroment_csw(value_vars))
            if value_vars.get('type_install_csw') not in ['Медная линия и порт не меняются', 'ВОЛС и порт не меняются']:
                hidden_vars[
                        '- Сообщить в ОЛИ СПД об освободившемся порте на коммутаторе %указать существующий КАД% после переезда клиента.'] = '- Сообщить в ОЛИ СПД об освободившемся порте на коммутаторе %указать существующий КАД% после переезда клиента.'
                static_vars['указать существующий КАД'] = value_vars.get('head').split('\n')[4].split()[2]
            services, service_shpd_change = _separate_services_and_subnet_dhcp(value_vars.get('readable_services'), value_vars.get('change_log_shpd'))
            if service_shpd_change:
                hidden_vars[', необходимость смены реквизитов'] = ', необходимость смены реквизитов'
                hidden_vars['ОНИТС СПД подготовиться к работам:'] = 'ОНИТС СПД подготовиться к работам:'
                hidden_vars['- По заявке в Cordis выделить подсеть с маской %указать новую маску%.'] = '- По заявке в Cordis выделить подсеть с маской %указать новую маску%.'
                static_vars['указать новую маску'] = '/30' if value_vars.get('change_log_shpd') == 'Новая подсеть /30' else '/32'
                hidden_vars['-- по согласованию с клиентом сменить реквизиты для услуги "ШПД в Интернет" на новую подсеть с маской %указать новую маску%.'] = '-- по согласованию с клиентом сменить реквизиты для услуги "ШПД в Интернет" на новую подсеть с маской %указать новую маску%.'
                hidden_vars['- После смены реквизитов:'] = '- После смены реквизитов:'
                hidden_vars['- разобрать ресурс %указать существующий ресурс% на договоре.'] = '- разобрать ресурс %указать существующий ресурс% на договоре.'
                static_vars['указать существующий ресурс'] = ', '.join(service_shpd_change)
            else:
                services = []
                for key, value in readable_services.items():
                    if key != '"Телефония"':
                        if type(value) == str:
                            services.append(key + ' ' + value)
                        elif type(value) == list:
                            services.append(key + ''.join(value))
            static_vars['указать сервис'] = ', '.join(services)
            static_vars['указать название сервиса'] = ', '.join([x for x in readable_services.keys() if x != '"Телефония"'])
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
                            static_vars['указать название сервиса'] = key
                            value_vars.update({'name_passage_service': key +' '+ value })
                        else:
                            other_services.append(key + ' ' + value)
                    elif type(value) == list:
                        for val in value:
                            if value_vars.get('selected_ono')[0][-4] in val:
                                services.append(key + ' ' + val)
                                static_vars['указать название сервиса'] = key
                                value_vars.update({'name_passage_service': key +' '+ val})
                            else:
                                other_services.append(key + ' ' + val)
            if value_vars.get('type_passage') == 'Перенос сервиса в новую точку':
                if value_vars.get('head').split('\n')[4].split()[2] == value_vars.get('selected_ono')[0][-2] or other_services == False:
                    hidden_vars[
                        '- Сообщить в ОЛИ СПД об освободившемся порте на коммутаторе %указать существующий КАД% после переезда клиента.'] = '- Сообщить в ОЛИ СПД об освободившемся порте на коммутаторе %указать существующий КАД% после переезда клиента.'
                    static_vars['указать существующий КАД'] = value_vars.get('head').split('\n')[4].split()[2]

            if services[0].startswith('"ШПД в интернет"'):
                if value_vars.get('change_log_shpd') != 'существующая адресация':
                    hidden_vars[', необходимость смены реквизитов'] = ', необходимость смены реквизитов'
                    hidden_vars['ОНИТС СПД подготовиться к работам:'] = 'ОНИТС СПД подготовиться к работам:'
                    hidden_vars['- По заявке в Cordis выделить подсеть с маской %указать новую маску%.'] = '- По заявке в Cordis выделить подсеть с маской %указать новую маску%.'
                    static_vars['указать новую маску'] = '/30' if value_vars.get('change_log_shpd') == 'Новая подсеть /30' else '/32'
                    static_vars['указать сервис'] = static_vars['указать название сервиса']
                    hidden_vars['-- по согласованию с клиентом сменить реквизиты для услуги "ШПД в Интернет" на новую подсеть с маской %указать новую маску%.'] = '-- по согласованию с клиентом сменить реквизиты для услуги "ШПД в Интернет" на новую подсеть с маской %указать новую маску%.'
                    hidden_vars['- После смены реквизитов:'] = '- После смены реквизитов:'
                    hidden_vars['- разобрать ресурс %указать существующий ресурс% на договоре.'] = '- разобрать ресурс %указать существующий ресурс% на договоре.'
                    static_vars['указать существующий ресурс'] = value_vars.get('selected_ono')[0][-4]
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
        if next(iter(type_change_service.keys())) == "Организация ШПД trunk'ом":
            stroka = templates.get("Организация услуги ШПД в интернет trunk'ом.")
            static_vars = {}
            hidden_vars = {}
            mask_service = next(iter(type_change_service.values()))
            if 'Интернет, блок Адресов Сети Интернет' in mask_service:
                if ('29' in mask_service) or (' 8' in mask_service):
                    static_vars['указать маску'] = '/29'
                elif ('28' in mask_service) or ('16' in mask_service):
                    static_vars['указать маску'] = '/28'
                else:
                    static_vars['указать маску'] = '/30'
            result_services.append(analyzer_vars(stroka, static_vars, hidden_vars))
        elif next(iter(type_change_service.keys())) == "Организация ШПД trunk'ом с простоем":
            stroka = templates.get("Организация услуги ШПД в интернет trunk'ом с простоем связи.")
            static_vars = {}
            hidden_vars = {}
            mask_service = next(iter(type_change_service.values()))
            if 'Интернет, блок Адресов Сети Интернет' in mask_service:
                if ('29' in mask_service) or (' 8' in mask_service):
                    static_vars['указать маску'] = '/29'
                elif ('28' in mask_service) or ('16' in mask_service):
                    static_vars['указать маску'] = '/28'
                else:
                    static_vars['указать маску'] = '/30'
            static_vars["указать ресурс на договоре"] = value_vars.get('selected_ono')[0][4]
            all_shpd_in_tr = value_vars.get('all_shpd_in_tr')
            if all_shpd_in_tr:
                service = next(iter(type_change_service.values()))

                if all_shpd_in_tr.get(service)['exist_service'] == 'trunk':
                    hidden_vars['Cогласовать с клиентом tag vlan для ресурса "%указать ресурс на договоре%".'] = 'Cогласовать с клиентом tag vlan для ресурса "%указать ресурс на договоре%".'
                    static_vars["в неизменном виде/access'ом (native vlan)/trunk'ом"] = "tag'ом"
                else:
                    static_vars["в неизменном виде/access'ом (native vlan)/trunk'ом"] = "access'ом (native vlan)"
                static_vars["access'ом (native vlan)/trunk'ом"] = "tag'ом"
                result_services.append(analyzer_vars(stroka, static_vars, hidden_vars))
        elif next(iter(type_change_service.keys())) == "Организация порта ВЛС trunk'ом" or next(iter(type_change_service.keys())) == "Организация порта ВЛС trunk'ом с простоем":
            static_vars = {}
            hidden_vars = {}
            all_portvk_in_tr = value_vars.get('all_portvk_in_tr')
            if all_portvk_in_tr:
                service = next(iter(all_portvk_in_tr.keys()))
                if all_portvk_in_tr.get(service)['new_vk'] == True:
                    stroka = templates.get("Организация услуги ВЛС")
                    result_services.append(stroka)
                    static_vars['указать ресурс ВЛС на договоре в Cordis'] = 'Для ВЛС, организованной по решению выше,'
                else:
                    static_vars['указать ресурс ВЛС на договоре в Cordis'] = all_portvk_in_tr.get(service)['exist_vk']
                static_vars['указать полосу'] = _get_policer(service)
                static_vars['полисером на Subinterface/на порту подключения'] = all_portvk_in_tr.get(service)['policer_vk']
                if next(iter(type_change_service.keys())) == "Организация порта ВЛС trunk'ом":
                    stroka = templates.get("Организация услуги порт ВЛC trunk'ом.")
                else:
                    if all_portvk_in_tr.get(service)['exist_service'] == 'trunk':
                        static_vars["в неизменном виде/access'ом (native vlan)/trunk'ом"] = "tag'ом"
                    else:
                        static_vars["в неизменном виде/access'ом (native vlan)/trunk'ом"] = "access'ом (native vlan)"
                    static_vars['указать ресурс на договоре'] = value_vars.get('selected_ono')[0][-4]
                    static_vars["access'ом (native vlan)/trunk'ом"] = "tag'ом"
                    stroka = templates.get("Организация услуги порт ВЛС trunk'ом с простоем связи.")
                result_services.append(analyzer_vars(stroka, static_vars, hidden_vars))
        elif next(iter(type_change_service.keys())) == "Организация порта ВМ trunk'ом" or next(iter(type_change_service.keys())) == "Организация порта ВМ trunk'ом с простоем":
            static_vars = {}
            hidden_vars = {}
            service = next(iter(type_change_service.values()))
            if value_vars.get('new_vm') == True:
                stroka = templates.get("Организация услуги виртуальный маршрутизатор")
                result_services.append(stroka)
                static_vars['указать название ВМ'] = ', организованного по решению выше,'
            else:
                static_vars['указать название ВМ'] = value_vars.get('exist_vm')
            static_vars['указать полосу'] = _get_policer(service)
            static_vars['полисером на SVI/на порту подключения'] = value_vars.get('policer_vm')
            if value_vars.get('vm_inet') == True:
                static_vars['без доступа в интернет/с доступом в интернет'] = 'с доступом в интернет'
            else:
                static_vars['без доступа в интернет/с доступом в интернет'] = 'без доступа в интернет'
                hidden_vars[
                    '- Согласовать с клиентом адресацию для порта ВМ без доступа в интернет.'] = '- Согласовать с клиентом адресацию для порта ВМ без доступа в интернет.'

            if next(iter(type_change_service.keys())) == "Организация порта ВМ trunk'ом":
                stroka = templates.get("Организация услуги порт виртуального маршрутизатора trunk'ом.")
            else:
                if value_vars.get('exist_service_vm') == 'trunk':
                    static_vars["в неизменном виде/access'ом (native vlan)/trunk'ом"] = "tag'ом"
                else:
                    static_vars["в неизменном виде/access'ом (native vlan)/trunk'ом"] = "access'ом (native vlan)"
                static_vars["access'ом (native vlan)/trunk'ом"] = "tag'ом"
                static_vars['указать ресурс на договоре'] = value_vars.get('selected_ono')[0][-4]
                stroka = templates.get("Организация услуги порт виртуального маршрутизатора trunk'ом с простоем связи.")
            result_services.append(analyzer_vars(stroka, static_vars, hidden_vars))
        elif next(iter(type_change_service.keys())) == "Изменение cхемы организации ШПД":
            stroka = templates.get("Изменение существующей cхемы организации ШПД с маской %указать сущ. маску% на подсеть с маской %указать нов. маску%")
            static_vars = {}
            hidden_vars = {}
            static_vars['указать нов. маску'] = value_vars.get('new_mask')
            static_vars["указать сущ. маску"] = value_vars.get('selected_ono')[0][4][-3:]
            static_vars["указать ресурс на договоре"] = value_vars.get('selected_ono')[0][4]
            static_vars['изменится/не изменится'] = 'не изменится'
            result_services.append(analyzer_vars(stroka, static_vars, hidden_vars))
        elif next(iter(type_change_service.keys())) == "Замена connected на connected":
            stroka = templates.get("Замена существующей connected подсети на connected подсеть с %большей/меньшей% маской")
            static_vars = {}
            hidden_vars = {}
            static_vars['указать нов. маску'] = value_vars.get('new_mask')
            static_vars["указать сущ. маску"] = value_vars.get('selected_ono')[0][4][-3:]
            static_vars["указать ресурс на договоре"] = value_vars.get('selected_ono')[0][4]
            static_vars['изменится/не изменится'] = 'не изменится'
            if int(static_vars['указать нов. маску'][1:]) > int(value_vars.get('selected_ono')[0][4][-2:]):
                static_vars['большей/меньшей'] = 'меньшей'
            else:
                static_vars['большей/меньшей'] = 'большей'
            static_vars['маркировка маршрутизатора'] = '-'.join(value_vars.get('selected_ono')[0][-2].split('-')[1:])
            match_svi = re.search('- (\d\d\d\d) -', value_vars.get('selected_ono')[0][-3])
            if match_svi:
                svi = match_svi.group(1)
                static_vars['указать номер SVI'] = svi
            else:
                static_vars['указать номер SVI'] = '%Неизвестный SVI%'
            result_services.append(analyzer_vars(stroka, static_vars, hidden_vars))
        elif next(iter(type_change_service.keys())) == "Организация доп connected":
            stroka = templates.get('Организация дополнительной подсети (connected)')
            static_vars = {}
            hidden_vars = {}
            static_vars['указать нов. маску'] = value_vars.get('new_mask')
            static_vars['маркировка маршрутизатора'] = '-'.join(value_vars.get('selected_ono')[0][-2].split('-')[1:])
            match_svi = re.search('- (\d\d\d\d) -', value_vars.get('selected_ono')[0][-3])
            if match_svi:
                svi = match_svi.group(1)
                static_vars['указать номер SVI'] = svi
            else:
                static_vars['указать номер SVI'] = '%Неизвестный SVI%'
            result_services.append(analyzer_vars(stroka, static_vars, hidden_vars))
        elif next(iter(type_change_service.keys())) == "Организация доп маршрутизируемой":
            stroka = templates.get("Организация маршрутизируемого непрерывного блока адресов сети интернет")
            static_vars = {}
            hidden_vars = {}
            static_vars['указать нов. маску'] = value_vars.get('new_mask')
            static_vars['указать ip-адрес'] = value_vars.get('routed_ip')
            static_vars['указать название vrf'] = value_vars.get('routed_vrf')
            result_services.append(analyzer_vars(stroka, static_vars, hidden_vars))
        elif next(iter(type_change_service.keys())) == "Организация доп IPv6":
            stroka = templates.get('Предоставление возможности прямой маршрутизации IPv6 дополнительно к существующему IPv4 подключению')
            static_vars = {}
            hidden_vars = {}
            match_svi = re.search('- (\d\d\d\d) -', value_vars.get('selected_ono')[0][-3])
            if match_svi:
                svi = match_svi.group(1)
                static_vars['указать номер SVI'] = svi
            else:
                static_vars['указать номер SVI'] = '%Неизвестный SVI%'
            static_vars["указать ресурс на договоре"] = value_vars.get('selected_ono')[0][4]
            result_services.append(analyzer_vars(stroka, static_vars, hidden_vars))
        elif next(iter(type_change_service.keys())) == "Организация ЦКС trunk'ом" or next(iter(type_change_service.keys())) == "Организация ЦКС trunk'ом с простоем":
            static_vars = {}
            hidden_vars = {}
            all_cks_in_tr = value_vars.get('all_cks_in_tr')
            if all_cks_in_tr:
                service = next(iter(type_change_service.values()))
                static_vars['указать точку "A"'] = all_cks_in_tr.get(service)['pointA']
                static_vars['указать точку "B"'] = all_cks_in_tr.get(service)['pointB']
                static_vars['полисером Subinterface/портом подключения'] = all_cks_in_tr.get(service)['policer_cks']
                static_vars['указать полосу'] = _get_policer(service)
                if next(iter(type_change_service.keys())) == "Организация ЦКС trunk'ом":
                    stroka = templates.get("Организация услуги ЦКС Etherline trunk'ом.")
                else:
                    if all_cks_in_tr.get(service)['exist_service'] == 'trunk':
                        static_vars["в неизменном виде/access'ом (native vlan)/trunk'ом"] = "trunk'ом"
                    else:
                        static_vars["в неизменном виде/access'ом (native vlan)/trunk'ом"] = "access'ом (native vlan)"
                    static_vars['указать ресурс на договоре'] = value_vars.get('selected_ono')[0][-4]
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
        result_services, value_vars = _new_enviroment(value_vars)
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
        hidden_vars['на %указать новую полосу сервиса%'] = 'на %указать новую полосу сервиса%'
        hidden_vars['- Ограничить скорость и настроить маркировку трафика для %указать сервис% %полисером Subinterface/портом подключения%.'] = '- Ограничить скорость и настроить маркировку трафика для %указать сервис% %полисером Subinterface/портом подключения%.'
        static_vars['указать сервис'] = name_passage_service
        static_vars['указать название сервиса'] = desc_service
        static_vars['указать новую полосу сервиса'] = value_vars.get('extend_speed')
        if value_vars.get('extend_policer_cks_vk'):
            static_vars['полисером Subinterface/портом подключения'] = value_vars.get('extend_policer_cks_vk')
        if value_vars.get('extend_policer_vm'):
            static_vars['полисером Subinterface/портом подключения'] = value_vars.get('extend_policer_vm')
        value_vars.update({'name_passage_service': name_passage_service})
        stroka = templates.get('Расширение полосы сервиса %указать название сервиса%')
        result_services.append(analyzer_vars(stroka, static_vars, hidden_vars))
    else:
        stroka = templates.get('Изменение полосы сервиса "ШПД в Интернет"')
        value_vars.update({'name_passage_service': name_passage_service})
        result_services.append(analyzer_vars(stroka, static_vars, hidden_vars))
    if value_vars.get('kad') == None:
        kad = value_vars.get('selected_ono')[0][-2]
        value_vars.update({'kad': kad})
        if value_vars.get('selected_ono')[0][-2].startswith('CSW'):
            node_csw = value_vars.get('node_csw')
            value_vars.update({'pps': node_csw})
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
        hidden_vars['%ОИПМ/ОИПД% подготовка к работам.'] = '%ОИПМ/ОИПД% подготовка к работам.'
        hidden_vars[
            '- Требуется отключение согласно ППР %указать № ППР% согласовать проведение работ.'] = '- Требуется отключение согласно ППР %указать № ППР% согласовать проведение работ.'
        hidden_vars[
            '- Совместно с ОНИТС СПД убедиться в восстановлении связи согласно ППР %указать № ППР%.'] = '- Совместно с ОНИТС СПД убедиться в восстановлении связи согласно ППР %указать № ППР%.'
        hidden_vars[
            '- После проведения монтажных работ убедиться в восстановлении услуг согласно ППР %указать № ППР%.'] = '- После проведения монтажных работ убедиться в восстановлении услуг согласно ППР %указать № ППР%.'
        static_vars['указать № ППР'] = value_vars.get('ppr')
    if value_vars.get('exist_sreda') == '2' or value_vars.get('exist_sreda') == '4':
        static_vars['медную линию связи/ВОЛС'] = 'ВОЛС'
        static_vars['ОИПМ/ОИПД'] = 'ОИПМ'
    else:
        static_vars['медную линию связи/ВОЛС'] = 'медную линию связи'
        static_vars['ОИПМ/ОИПД'] = 'ОИПД'
    stroka = templates.get('Изменение трассы присоединения к СПД')
    result_services.append(analyzer_vars(stroka, static_vars, hidden_vars))
    if value_vars.get('kad') == None:
        kad = value_vars.get('independent_kad')
        value_vars.update({'kad': kad})
        pps = value_vars.get('independent_pps')
        value_vars.update({'pps': pps})
    return result_services, result_services_ots, value_vars


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
            '- Требуется отключение согласно ППР %указать № ППР% согласовать проведение работ.'] = '- Требуется отключение согласно ППР %указать № ППР% согласовать проведение работ.'
        hidden_vars[
            '- Совместно с ОНИТС СПД убедиться в восстановлении связи согласно ППР %указать № ППР%.'] = '- Совместно с ОНИТС СПД убедиться в восстановлении связи согласно ППР %указать № ППР%.'
        hidden_vars[
            '- После проведения монтажных работ убедиться в восстановлении услуг согласно ППР %указать № ППР%.'] = '- После проведения монтажных работ убедиться в восстановлении услуг согласно ППР %указать № ППР%.'
        static_vars['указать № ППР'] = value_vars.get('ppr')
    static_vars['указать название клиентского коммутатора'] = value_vars.get('selected_ono')[0][-2]
    if value_vars.get('exist_sreda') == '2' or value_vars.get('exist_sreda') == '4':
        static_vars['медную линию связи/ВОЛС'] = 'ВОЛС'
        static_vars['ОИПМ/ОИПД'] = 'ОИПМ'
    else:
        static_vars['медную линию связи/ВОЛС'] = 'медную линию связи'
        static_vars['ОИПМ/ОИПД'] = 'ОИПД'
    stroka = templates.get('Перенос клиентского коммутатора')
    result_services.append(analyzer_vars(stroka, static_vars, hidden_vars))
    if value_vars.get('kad') == None:
        kad = value_vars.get('independent_kad')
        value_vars.update({'kad': kad})
        pps = value_vars.get('independent_pps')
        value_vars.update({'pps': pps})
    return result_services, result_services_ots, value_vars