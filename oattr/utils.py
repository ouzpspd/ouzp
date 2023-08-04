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