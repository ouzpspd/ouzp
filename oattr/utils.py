import re

def add_tag_for_services(ticket_tr):
    services = {}
    tags_services = {'phone': 'Телефон', 'video': 'Видеонаблюдение', 'lvs': 'ЛВС', 'hotspot': 'Хот-спот'}
    for key, value in tags_services.items():
        for service in ticket_tr.services:
            if service.startswith(value):
                if services.get(key):
                    services[key] = services.get(key) + ', ' + service[len(value):].capitalize()
                else:
                    services.update({key: service})
    return services


def analyzer_vars(stroka, static_vars, hidden_vars, multi_vars):
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

    # блок заполнения повторяющихсся &&
    regex_var_lines = '&(.+?)&'
    match_var_lines = re.finditer(regex_var_lines, stroka, flags=re.DOTALL)
    list_var_lines = [i.group(1) for i in match_var_lines]
    for i in list_var_lines:
        if multi_vars.get(i):
            stroka = stroka.replace(f'&{i}&', '\n'.join(multi_vars[i]))
        else:
            if f'&{i}&\n' in stroka:
                stroka = stroka.replace(f'&{i}&\n', '')
            else:
                stroka = stroka.replace(f'&{i}&', '  ')


    # блок для заполнения %%
    ckb_vars = {}
    dynamic_vars = {}
    regex = '%([\s\S]+?)%'
    match = re.finditer(regex, stroka, flags=re.DOTALL)
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


def construct_tr(value_vars, service_vars, templates, ticket_tr):
    template = templates.get('Присоединение к СПД по медной линии связи.')
    result = []
    static_vars = {}
    hidden_vars = {}
    repr_string = {}

    repr_string['mounting_line'] = '- Смонтировать %Количество линий связи% линии %Тип кабеля% от %Точка от% до %Точка до%. ' +\
                                   '%Способ монтажа линии связи%. %Способ крепежа линии связи%.'
    multi_vars = {repr_string['mounting_line']:[]}
    count_lines = [key.strip('from_') for key in value_vars.keys() if key.startswith('from_')]
    for i in count_lines:
        static_vars[f'Количество линий связи {i}'] = value_vars.get(f'count_{i}')
        static_vars[f'Тип кабеля {i}'] = value_vars.get(f'cable_{i}')
        static_vars[f'Точка от {i}'] = value_vars.get(f'from_{i}')
        static_vars[f'Точка до {i}'] = value_vars.get(f'to_{i}')
        static_vars[f'Способ монтажа линии связи {i}'] = value_vars.get(f'mounting_{i}')
        static_vars[f'Способ крепежа линии связи {i}'] = value_vars.get(f'fastening_{i}')
        multi_vars[repr_string['mounting_line']].append(f'- Смонтировать %Количество линий связи {i}% линии %Тип кабеля {i}% от %Точка от {i}%' +
        f' до %Точка до {i}%. %Способ монтажа линии связи {i}%. %Способ крепежа линии связи {i}%.')

    if value_vars.get('no_exit'):
        hidden_vars['Внимание! ТР написано без выезда технолога.'] = 'Внимание! ТР написано без выезда технолога.'
    if value_vars.get('tech_reserve'):
        hidden_vars['- Оставить тех. запас.'] = '- Оставить тех. запас.'
    if value_vars.get('line_test'):
        hidden_vars['- Протестировать линию связи.'] = '- Протестировать линию связи.'
    if value_vars.get('agreement'):
        hidden_vars['Согласование:'] = 'Согласование:'
        hidden_vars['%Согласование%'] = '%Согласование%'
        static_vars['Согласование'] = value_vars.get('agreement')
    if value_vars.get('equipment'):
        hidden_vars['Монтаж оборудования:'] = 'Монтаж оборудования:'
        hidden_vars['%Монтаж оборудования%'] = '%Монтаж оборудования%'
        static_vars['Монтаж оборудования'] = value_vars.get('equipment')
    static_vars['Доступ'] = value_vars.get('access')

    result.append(analyzer_vars(template, static_vars, hidden_vars, multi_vars))

    # services = add_tag_for_services(ticket_tr)
    # repr_string['mounting_line_service'] = '- Смонтировать %Количество линий связи% линии %Тип кабеля% от %Точка от% до %Точка до%. %Способ монтажа линии связи%. %Способ крепежа линии связи%.'
    # for tag_service in services.keys():
    #     line_exist = bool([True for key in service_vars.keys() if key.startswith(f'{tag_service}_from_')])
    #
    #     if tag_service.startswith('lvs') and line_exist:
    #         if service_vars.get('lvs_switch'):
    #             template = templates.get('Организация ЛВС')
    #         else:
    #             template = templates.get('Организация СКС')
    #         static_vars = {}
    #         hidden_vars = {}
    #         #repr_string = {}
    #
    #         multi_vars = {repr_string['mounting_line_service']: []}
    #         count_lines = [key.strip('lvs_from_') for key in service_vars.keys() if key.startswith('lvs_from_')]
    #         for i in count_lines:
    #             static_vars[f'Количество линий связи {i}'] = service_vars.get(f'lvs_count_line_{i}')
    #             static_vars[f'Тип кабеля {i}'] = service_vars.get(f'lvs_cable_{i}')
    #             static_vars[f'Точка от {i}'] = service_vars.get(f'lvs_from_{i}')
    #             static_vars[f'Точка до {i}'] = service_vars.get(f'lvs_to_{i}')
    #             static_vars[f'Способ монтажа линии связи {i}'] = service_vars.get(f'lvs_mounting_{i}')
    #             static_vars[f'Способ крепежа линии связи {i}'] = service_vars.get(f'lvs_fastening_{i}')
    #             multi_vars[repr_string['mounting_line_service']].append(f'- Смонтировать %Количество линий связи {i}% линии %Тип кабеля {i}% от %Точка от {i}%' +
    #                                                             f' до %Точка до {i}%. %Способ монтажа линии связи {i}%. %Способ крепежа линии связи {i}%.')
    #         result.append(analyzer_vars(template, static_vars, hidden_vars, multi_vars))
    #
    #     elif tag_service.startswith('phone'):
    #         template = templates.get('Организация Телефонии')
    #         static_vars = {}
    #         hidden_vars = {}
    #         #repr_string = {}
    #         multi_vars = {repr_string['mounting_line_service']: []}
    #         count_lines = [key.strip('phone_from_') for key in service_vars.keys() if key.startswith('phone_from_')]
    #         for i in count_lines:
    #             static_vars[f'Количество линий связи {i}'] = service_vars.get(f'phone_count_line_{i}')
    #             static_vars[f'Тип кабеля {i}'] = service_vars.get(f'phone_cable_{i}')
    #             static_vars[f'Точка от {i}'] = service_vars.get(f'phone_from_{i}')
    #             static_vars[f'Точка до {i}'] = service_vars.get(f'phone_to_{i}')
    #             static_vars[f'Способ монтажа линии связи {i}'] = service_vars.get(f'phone_mounting_{i}')
    #             static_vars[f'Способ крепежа линии связи {i}'] = service_vars.get(f'phone_fastening_{i}')
    #             multi_vars[repr_string['mounting_line_service']].append(f'- Смонтировать %Количество линий связи {i}% линии %Тип кабеля {i}% от %Точка от {i}%' +
    #                                                             f' до %Точка до {i}%. %Способ монтажа линии связи {i}%. %Способ крепежа линии связи {i}%.')
    #         if service_vars.get('phone_vgw_place') != 'не требуется':
    #             hidden_vars['Установка оборудования:'] = 'Установка оборудования:'
    #             hidden_vars['- Установить тел. шлюз %Место голос. шлюза%.'] = '- Установить тел. шлюз %Место голос. шлюза%.'
    #             static_vars['Место голос. шлюза'] = service_vars.get('phone_vgw_place')
    #         result.append(analyzer_vars(template, static_vars, hidden_vars, multi_vars))
    #
    #     elif tag_service.startswith('video'):
    #         template = templates.get('Организация СВН')
    #         static_vars = {}
    #         hidden_vars = {}
    #         #repr_string = {}
    #         multi_vars = {repr_string['mounting_line_service']: []}
    #         count_lines = [key.strip('video_from_') for key in service_vars.keys() if key.startswith('video_from_')]
    #         for i in count_lines:
    #             static_vars[f'Количество линий связи {i}'] = service_vars.get(f'video_count_line_{i}')
    #             static_vars[f'Тип кабеля {i}'] = service_vars.get(f'video_cable_{i}')
    #             static_vars[f'Точка от {i}'] = service_vars.get(f'video_from_{i}')
    #             static_vars[f'Точка до {i}'] = service_vars.get(f'video_to_{i}')
    #             static_vars[f'Способ монтажа линии связи {i}'] = service_vars.get(f'video_mounting_{i}')
    #             static_vars[f'Способ крепежа линии связи {i}'] = service_vars.get(f'video_fastening_{i}')
    #             multi_vars[repr_string['mounting_line_service']].append(f'- Смонтировать %Количество линий связи {i}% линии %Тип кабеля {i}% от %Точка от {i}%' +
    #                                                             f' до %Точка до {i}%. %Способ монтажа линии связи {i}%. %Способ крепежа линии связи {i}%.')
    #         if service_vars.get('video_switch'):
    #             hidden_vars['- По согласованию с клиентом установить POE-коммутатор в помещении клиента.'] = \
    #                 '- По согласованию с клиентом установить POE-коммутатор в помещении клиента.'
    #         static_vars['Количество камер'] = service_vars.get('video_count_camera')
    #         result.append(analyzer_vars(template, static_vars, hidden_vars, multi_vars))

    return result