import re
import pymorphy2

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
            finish_node = item + node_mon[:node_mon.index(key)]
    return finish_node


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


def analyzer_vars(stroka, static_vars, hidden_vars):
    '''Данная функция принимает строковую переменную, содержащую шаблон услуги со страницы
    Типовые блоки технического решения. Ищет в шаблоне блоки <> и сравнивает с аналогичными переменными из СПП.
    По средством доп. словаря формирует итоговый словарь содержащий блоки из СПП, которые
    есть в блоках шаблона(чтобы не выводить неактуальный блок) и блоки шаблона, которых не было в блоках
    из СПП(чтобы не пропустить неучтенный блок)
    Передаем переменные, т.к. переменные из глобал видятся, а из другой функции нет.
'''
    #    блок для определения необходимости частных строк <>
    list_var_lines = []
    list_var_lines_in = []
    regex_var_lines = '<(.+?)>'
    match_var_lines = re.finditer(regex_var_lines, stroka, flags=re.DOTALL)

    for i in match_var_lines:
        print('совпадения <>')
        print(i)
        list_var_lines.append(i.group(1))

    for i in list_var_lines:
        print(i)
        if hidden_vars.get(i):
            stroka = stroka.replace('<{}>'.format(i), hidden_vars[i])

        else:
            stroka = stroka.replace('<{}>'.format(i), '  ')

    regex_var_lines_in = '\[(.+?)\]'
    match_var_lines_in = re.finditer(regex_var_lines_in, stroka, flags=re.DOTALL)
    print(match_var_lines_in)
    for i in match_var_lines_in:
        print('совпадения []')
        print(i)
        list_var_lines_in.append(i.group(1))

    for i in list_var_lines_in:
        print(i)
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
        print(dynamic_vars[key])
    for key in dynamic_vars.keys():
        print(key)
        stroka = stroka.replace('%{}%'.format(key), dynamic_vars[key])
        stroka = stroka.replace(' .', '.')

    print("stroka")
    print(stroka)
    stroka = ''.join([stroka[i] for i in range(len(stroka)) if i != len(stroka)-1 and not (stroka[i] == ' ' and stroka[i + 1] == ' ')])
    for i in [';', ',', ':', '.']:
        stroka = stroka.replace(' ' + i, i)

    return stroka


def pluralizer_vars(stroka, counter_plur):
    '''Данная функция на основе количества устройств в шаблоне меняет ед./множ. число связанных слов'''
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


def _new_services(result_services, value_vars):
    result_services_ots = None
    logic_csw = True if value_vars.get('logic_csw') or value_vars.get('logic_change_csw') or value_vars.get('logic_change_gi_csw') or value_vars.get('logic_replace_csw') else False
    services_plus_desc = value_vars.get('services_plus_desc')
    templates = value_vars.get('templates')
    sreda = value_vars.get('sreda')
    name_new_service = set()
    for service in services_plus_desc:
        if 'Интернет, DHCP' in service:

            name_new_service.add('ШПД в Интернет')
            print('{}'.format(service.replace('|', ' ')) + '-' * 20)
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
            #if value_vars.get('router_shpd') == True:
                stroka = templates.get("Установка маршрутизатора")
                if sreda == '2' or sreda == '4':
                    static_vars['ОИПМ/ОИПД'] = 'ОИПМ'
                else:
                    static_vars['ОИПМ/ОИПД'] = 'ОИПД'
                result_services.append(analyzer_vars(stroka, static_vars, hidden_vars))

        elif 'Интернет, блок Адресов Сети Интернет' in service:
            name_new_service.add('ШПД в Интернет')
            print('{}'.format(service.replace('|', ' ')) + '-' * 20)
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
            #if value_vars.get('type_shpd') == 'access':
                stroka = templates.get("Организация услуги ШПД в интернет access'ом.")
                result_services.append(analyzer_vars(stroka, static_vars, hidden_vars))
            elif all_shpd_in_tr.get(service) and all_shpd_in_tr.get(service)['type_shpd'] == 'trunk':
            #elif value_vars.get('type_shpd') == 'trunk':
                stroka = templates.get("Организация услуги ШПД в интернет trunk'ом.")
                result_services.append(analyzer_vars(stroka, static_vars, hidden_vars))

            if all_shpd_in_tr.get(service) and all_shpd_in_tr.get(service)['router_shpd']:
            #if value_vars.get('router_shpd') == True:
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
                print('{}'.format(service.replace('|', ' ')) + '-' * 20)
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
            print('{}'.format(service.replace('|', ' ')) + '-' * 20)
            if logic_csw == True:
                result_services.append(enviroment_csw(value_vars))

            static_vars = {}
            hidden_vars = {}
            all_cks_in_tr = value_vars.get('all_cks_in_tr')
            print('!!!!!!all_cks_in_tr')
            print(all_cks_in_tr)
            print(service)
            if all_cks_in_tr.get(service):
                static_vars['указать точку "A"'] = all_cks_in_tr.get(service)['pointA']
                static_vars['указать точку "B"'] = all_cks_in_tr.get(service)['pointB']
                static_vars['полисером Subinterface/портом подключения'] = all_cks_in_tr.get(service)['policer_cks']
                static_vars['указать полосу'] = _get_policer(service)
                #if '1000' in service:
                #    static_vars['указать полосу'] = '1 Гбит/с'
                #elif '100' in service:
                #    static_vars['указать полосу'] = '100 Мбит/с'
                #lif '10' in service:
                #   static_vars['указать полосу'] = '10 Мбит/с'
                #lif '1' in service:
                #   static_vars['указать полосу'] = '1 Гбит/с'
                #lse:
                #    static_vars['указать полосу'] = 'Неизвестная полоса'

                if all_cks_in_tr.get(service)['type_cks'] == 'access':
                    print("all_cks_in_tr.get(service)['pointA']")
                    print(all_cks_in_tr.get(service)['pointA'])
                    stroka = templates.get("Организация услуги ЦКС Etherline access'ом.")
                    result_services.append(analyzer_vars(stroka, static_vars, hidden_vars))
                elif all_cks_in_tr.get(service)['type_cks'] == 'trunk':
                    stroka = templates.get("Организация услуги ЦКС Etherline trunk'ом.")
                    result_services.append(analyzer_vars(stroka, static_vars, hidden_vars))


        elif 'Порт ВЛС' in service:
            name_new_service.add('Порт ВЛС')
            print('{}'.format(service.replace('|', ' ')) + '-' * 20)
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
            print('{}'.format(service.replace('|', ' ')) + '-' * 20)
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
            if '1000' in service:
                static_vars['указать полосу'] = '1 Гбит/с'
            elif '100' in service:
                static_vars['указать полосу'] = '100 Мбит/с'
            elif '10' in service:
                static_vars['указать полосу'] = '10 Мбит/с'
            elif '1' in service:
                static_vars['указать полосу'] = '1 Гбит/с'
            else:
                static_vars['указать полосу'] = 'Неизвестная полоса'

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
            # hotspot_users = None
            static_vars = {}
            hidden_vars = {}
            print('{}'.format(service.replace('|', ' ')) + '-' * 20)
            types_premium_plus = ['премиум +', 'премиум+', 'прем+', 'прем +']
            if any(type in service.lower() for type in types_premium_plus):
            #if 'премиум +' in service.lower() or 'премиум+' in service.lower():
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
            # cnt_camera = None
            print('-' * 20 + '\n' + '{}'.format(service.replace('|', ' ')))
            cameras = ['TRASSIR TR-D7111IR1W', 'TRASSIR TR-D7121IR1W', 'QTECH QVC-IPC-202VAE', 'QTECH QVC-IPC-202ASD', \
                       'TRASSIR TR-D3121IR1 v4', 'QTECH QVC-IPC-201E', 'TRASSIR TR-D2121IR3', 'QTECH QVC-IPC-502AS', \
                       'QTECH QVC-IPC-502VA', 'HiWatch DS-I453', 'QTECH QVC-IPC-501', 'TRASSIR TR-D2141IR3',
                       'HiWatch DS-I450']
            static_vars = {}
            hidden_vars = {}
            static_vars['указать модель камеры'] = value_vars.get('camera_model')
            if value_vars.get('voice') == True:
                static_vars['требуется запись звука / запись звука не требуется'] = 'требуется запись звука'
                hidden_vars[' и запись звука'] = ' и запись звука'
            else:
                static_vars['требуется запись звука / запись звука не требуется'] = 'запись звука не требуется'
            # regex_cnt_camera = ['(\d+)камер', '(\d+) камер', '(\d+) видеокамер', '(\d+)видеокамер']
            # for regex in regex_cnt_camera:
            #    match_cnt_camera = re.search(regex, service.lower())
            #    if match_cnt_camera:
            #        cnt_camera = match_cnt_camera.group(1)
            #        break

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
                # result_services.append(analyzer_vars(stroka, static_vars, hidden_vars))

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
                print('!!!!!!!!!!!!!!!!!')
                print(stroka)
                stroka = stroka[:stroka.index(
                    'порты POE-коммутатора:')] + 'порты POE-коммутатора:\n' + extra_extra_stroka_one + '\n \nОВИТС проведение работ:\n' + stroka[
                                                                                                                                          stroka.index(
                                                                                                                                              '- Произвести настройку'):]
                stroka = stroka + '\n' + extra_extra_stroka_two
                static_vars['указать количество POE-коммутаторов'] = '1'

                # result_services.append(analyzer_vars(stroka, static_vars, hidden_vars))

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
            print('!!!! def _new_services')
            print('!!!service')
            print(service)
            if service.endswith('|'):
                print("!!!!value_vars.get('type_phone')")
                print(value_vars.get('type_phone'))
                if value_vars.get('type_phone') == 'st':
                    if logic_csw == True:
                        result_services.append(enviroment_csw(value_vars))
                    print('result_services')
                    print(result_services)
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
                    print('!!!!channel_vgw')
                    print(type(channel_vgw))
                    if channel_vgw == '1':
                        static_vars['указать порты тел. шлюза'] = '1'
                    else:
                        static_vars['указать порты тел. шлюза'] = '1-{}'.format(channel_vgw)
                    print("!!!!!!static_vars['указать порты тел. шлюза']")
                    print(static_vars['указать порты тел. шлюза'])
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
                    # if ports_vgw == '1':
                    #     static_vars['указать порты тел. шлюза'] = '1'
                    # else:
                    #     static_vars['указать порты тел. шлюза'] = '1-{}'.format(ports_vgw)

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
                    # if channel_vgw == '1':
                    #     static_vars['указать порты тел. шлюза'] = '1'
                    # else:
                    #     static_vars['указать порты тел. шлюза'] = '1-{}'.format(channel_vgw)

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
            print('{}'.format(service.replace('|', ' ')) + '-' * 20)
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
                if lvs_switch == ('TP-Link TL-SG105 V4' or 'ZYXEL GS1200-5'):
                    static_vars['5/8/16/24'] = '5'
                elif lvs_switch == ('TP-Link TL-SG108 V4' or 'ZYXEL GS1200-8'):
                    static_vars['5/8/16/24'] = '8'
                elif lvs_switch == 'D-link DGS-1100-16/B':
                    static_vars['5/8/16/24'] = '16'
                elif lvs_switch == 'D-link DGS-1100-24/B':
                    static_vars['5/8/16/24'] = '24'
                stroka = analyzer_vars(stroka, static_vars, hidden_vars)
                print('chech lvs stroka')
                print(stroka)
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
        hidden_vars['- Организовать %медную линию связи/ВОЛС% [от %указать узел связи% ]до клиентcкого коммутатора по решению ОТПМ.'] = '- Организовать %медную линию связи/ВОЛС% [от %указать узел связи% ]до клиентcкого коммутатора по решению ОТПМ.'
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
            hidden_vars['от %указать узел связи% '] = 'от %указать узел связи% '
            static_vars['медную линию связи/ВОЛС'] = 'медную линию связи'
            static_vars['ОИПМ/ОИПД'] = 'ОИПД'
        elif sreda == '2' or sreda == '4':
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
            static_vars['ОИПМ/ОИПД'] = 'ОИПД'
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


def client_new(value_vars):
    """Данный метод формирует готовое ТР для нового присоединения и новых услуг"""
    result_services, value_vars = _new_enviroment(value_vars)
    result_services, result_services_ots, value_vars = _new_services(result_services, value_vars)
    return result_services, result_services_ots, value_vars