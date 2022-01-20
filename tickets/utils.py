import re
import pymorphy2

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