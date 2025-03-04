from django import forms
from django.contrib.auth.models import User


class OrtrForm(forms.Form):
    ortr_field = forms.CharField(label='Решение ОРТР', widget=forms.Textarea(attrs={'class': 'form-control'}))
    pps = forms.CharField(label='ППС', required=False, widget=forms.TextInput(attrs={'class': 'form-control'}))
    kad = forms.CharField(label='КАД', required=False, widget=forms.TextInput(attrs={'class': 'form-control'}))
    ots_field = forms.CharField(label='Решение ОТС', required=False, widget=forms.Textarea(attrs={'class': 'form-control'}))


class LocalForm(forms.Form):
    types = [('sks_standart', 'СКС Стандарт (без использования кабель-канала)'),
              ('sks_business', 'СКС Бизнес (с использованием кабель-канала)'),
              ('lvs_standart', 'ЛВС Стандарт (без использования кабель-канала)'),
              ('lvs_business', 'ЛВС Бизнес (с использованием кабель-канала)'),
              ('sks_vols', 'СКС Стандарт оптический'),
             ('Под видеонаблюдение', 'СКС для видеонаблюдения',
              )]
    local_type = forms.CharField(label='Тип ЛВС', widget=forms.Select(choices=types, attrs={'class': 'form-control'}))
    local_ports = forms.IntegerField(max_value=24, label='Количество портов', required=False,
                                   widget=forms.NumberInput(attrs={'class': 'form-control'}))

    local_socket_need = forms.BooleanField(label='Требуются розетки RJ-45', required=False,
                                 widget=forms.CheckboxInput(attrs={'class': 'form-check'}))
    local_socket = forms.IntegerField(max_value=24, label='Количество розеток', required=False,
                                     widget=forms.NumberInput(attrs={'class': 'form-control'}))

    local_cable_channel = forms.IntegerField(max_value=10000, label='Длина кабель-канала (метров)', required=False,
                                             widget=forms.NumberInput(attrs={'class': 'form-control'}))

    sks_router = forms.BooleanField(label='Подключить линии в маршрутизатор', required=False,
                                    widget=forms.CheckboxInput(attrs={'class': 'form-check'}))

    types_transceiver = [
        ('Конвертеры 100', 'Конвертеры 100 Мбит/с'),
        ('Конвертеры 1000', 'Конвертеры 1 Гбит/с'),
        ('SFP', 'SFP WDM, до 20 км')
    ]
    sks_transceiver = forms.CharField(
        widget=forms.Select(choices=types_transceiver, attrs={'class': 'form-control transceiver'}))

    lvs_busy = forms.BooleanField(label='Все порты маршрутизатора заняты', required=False,
                                  widget=forms.CheckboxInput(attrs={'class': 'form-check'}))
    types = [('TP-Link TL-SG105 V4', 'TP-Link TL-SG105 (5 портов)'),
             ('TP-Link TL-SG108 V4', 'TP-Link TL-SG108 (8 портов)'),
             ('ZYXEL GS1200-5', 'ZYXEL GS1200-5 (5 портов)'),
             ('ZYXEL GS1200-8', 'ZYXEL GS1200-8 (8 портов)'),
             ('D-link DGS-1100-16/B', 'D-link DGS-1100-16 (16 портов)'),
             ('D-link DGS-1100-24/B', 'D-link DGS-1100-24 (24 порта)')]
    lvs_switch = forms.CharField(label='Коммутатор',
                                 widget=forms.Select(choices=types, attrs={'class': 'form-control'}))


class HotspotForm(forms.Form):
    types = [('Хот-Спот Стандарт', 'Хот-Спот Стандарт'),
             ('Хот-Спот Премиум', 'Хот-Спот Премиум'),
             ('Хот-Спот Премиум +', 'Хот-Спот Премиум +')]
    type_hotspot = forms.CharField(
        widget=forms.Select(choices=types, attrs={'class': 'form-control transceiver'}))
    exist_hotspot_client = forms.BooleanField(label='Существующий клиент', required=False, widget=forms.CheckboxInput(attrs={'class': 'form-check'}))
    hotspot_local_wifi = forms.BooleanField(label='С локальной сетью WiFi', required=False,
                                              widget=forms.CheckboxInput(attrs={'class': 'form-check'}))
    hotspot_points = forms.IntegerField(max_value=10, required=False, label='Количество точек', widget=forms.NumberInput(attrs={'class': 'form-control'}))
    hotspot_users = forms.IntegerField(max_value=1000, label='Количество пользователей', widget=forms.NumberInput(attrs={'class': 'form-control'}))
    types = [('access', 'access'), ('trunk', 'trunk')]
    port_type = forms.CharField(label='Режим порта', required=False,
                                widget=forms.Select(choices=types, attrs={'class': 'form-control'}))
    connect = forms.CharField(label='Подключение', required=False,
                                 widget=forms.Select(attrs={'class': 'form-control'}))


class PhoneForm(forms.Form):
    types = [('ak', 'Аналог, установка шлюза у клиента'), ('ap', 'Аналог, установка шлюза на ППС'), ('ab', 'Аналог, установка шлюза не требуется'), ('s', 'SIP, по логину/паролю'), ('st', 'SIP, IP-транк')]
    type_phone = forms.CharField(label='Тип телефонии', widget=forms.Select(choices=types, attrs={'class': 'form-control'}))
    types_vgw = [('D-Link DVG-5402SP', 'D-Link DVG-5402SP'), ('Eltex RG-1404G или Eltex TAU-4M.IP', 'Eltex TAU-4M.IP'),
                 ('Eltex TAU-8.IP', 'Eltex TAU-8.IP'), ('Eltex TAU-16.IP', 'Eltex TAU-16.IP'), ('Eltex TAU-24.IP', 'Eltex TAU-24.IP'),
                 ('Eltex TAU-36.IP', 'Eltex TAU-36.IP'), ('Eltex TAU-72.IP', 'Eltex TAU-72.IP'),]
    vgw = forms.CharField(label='Модель шлюза', widget=forms.Select(choices=types_vgw, attrs={'class': 'form-control'}))
    channel_vgw = forms.IntegerField(label='Количество каналов', widget=forms.NumberInput(attrs={'class': 'form-control', 'placeholder': 'Канальность'}))
    ports_vgw = forms.CharField(required=False, label='Количество портов ВАТС', widget=forms.NumberInput(attrs={'class': 'form-control'}))
    types_ip_trunk = [('access', 'access'), ('trunk', 'trunk')]
    type_ip_trunk = forms.CharField(label='Режим порта для IP-транк', required=False,
                                widget=forms.Select(choices=types_ip_trunk, attrs={'class': 'form-control'}))
    form_exist_vgw_model = forms.CharField(max_length=100, required=False,
                                  widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Модель сущ. шлюза'}))
    form_exist_vgw_name = forms.CharField(max_length=100, required=False,
                                  widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Название сущ. шлюза'}))
    form_exist_vgw_port = forms.CharField(max_length=100, required=False,
                                  widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Порты сущ. шлюза'}))
    con = [('', 'Не требуется')]
    connect = forms.CharField(label='Подключение', required=False,
                                 widget=forms.Select(choices=con, attrs={'class': 'form-control'}))

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if args:
            # for view func-based fields locate in args
            new_fields = set(args[0]) - set(self.fields.keys())
            new_fields.remove('csrfmiddlewaretoken')
            for field in new_fields:
                self.fields[f'{field}'] = forms.IntegerField()

class ItvForm(forms.Form):
    types = [('novl', 'В vlan организуемой услуги ШПД'),
             ('novlexist', 'В vlan действующей услуги ШПД'),
             ('vl', 'В vlan индивидуальном')]
    type_itv = forms.CharField(label='Тип ITV', widget=forms.Select(choices=types, attrs={'class': 'form-control'}))
    cnt_itv = forms.IntegerField(max_value=4, label='Количество приставок',
                                        widget=forms.NumberInput(attrs={'class': 'form-control'}))
    need_line_itv = forms.BooleanField(label='Монтаж линий', required=False,
                                           widget=forms.CheckboxInput(attrs={'class': 'form-check'}))
    router_itv = forms.BooleanField(label='Маршрутизатор для иТВ', required=False, widget=forms.CheckboxInput(attrs={'class': 'form-check'}))
    con = [('', 'Не требуется')]
    connect = forms.CharField(label='Подключение', required=False,
                                 widget=forms.Select(choices=con, attrs={'class': 'form-control'}))


class ShpdForm(forms.Form):
    router = forms.BooleanField(label='Маршрутизатор', required=False, widget=forms.CheckboxInput(attrs={'class': 'form-check'}))
    types = [('access', 'access'), ('trunk', 'trunk')]
    port_type = forms.CharField(label='Режим порта', required=False,
                                 widget=forms.Select(choices=types, attrs={'class': 'form-control'}))
    exist_service = forms.CharField(label='Режим порта существующей услуги', required=False,
                                    widget=forms.Select(choices=types, attrs={'class': 'form-control'}))
    connect = forms.CharField(label='Подключение', required=False,
                                 widget=forms.Select(attrs={'class': 'form-control'}))


class PassServiceForm(forms.Form):
    connect = forms.CharField(label='Подключение', required=False,
                                 widget=forms.Select(attrs={'class': 'form-control'}))
    types_change_log_shpd = [
        ('существующая адресация', 'существующая адресация'),
        ('Новая подсеть /30', 'Новая подсеть /30'),
        ('Новая подсеть /32', 'Новая подсеть /32'),
    ]
    change_log_shpd = forms.CharField(label='Изменение схемы ШПД для подсетей с маской /32', required=False,
                                      widget=forms.Select(choices=types_change_log_shpd,
                                                          attrs={'class': 'form-control'}))
    type_police = [('полисером на Subinterface', 'Subinterface'), ('портом подключения', 'Порт коммутатора'), ('не требуется', 'Не требуется')]
    policer_cks = forms.CharField(label='Ограничение', required=False, widget=forms.Select(choices=type_police, attrs={'class': 'form-control'}))
    type_police_vm = [('полисером на SVI', 'SVI'), ('портом подключения', 'Порт коммутатора'), ('не требуется', 'Не требуется')]
    policer_vm = forms.CharField(label='Ограничение', required=False,
                                 widget=forms.Select(choices=type_police_vm, attrs={'class': 'form-control'}))
    types = [
        ('10 Мбит/с', '10 Мбит/с'),
        ('100 Мбит/с', '100 Мбит/с'),
        ('1 Гбит/с', '1 Гбит/с'),
    ]
    extend_speed = forms.CharField(label='Новая полоса', required=False,
                                   widget=forms.Select(choices=types, attrs={'class': 'form-control'}))


class ExtendServiceForm(forms.Form):
    type_police_cks_vk = [
        ('полисером на Subinterface', 'Subinterface'),
        ('портом подключения', 'Порт коммутатора'),
        ('не требуется', 'Не требуется')]
    type_police_vm = [
        ('полисером на SVI', 'SVI'),
        ('портом подключения', 'Порт коммутатора'),
        ('не требуется', 'Не требуется')]
    types = [
        ('10 Мбит/с', '10 Мбит/с'),
        ('100 Мбит/с', '100 Мбит/с'),
        ('1 Гбит/с', '1 Гбит/с'),
    ]
    extend_speed = forms.CharField(label='Новая полоса', required=False,
                               widget=forms.Select(choices=types, attrs={'class': 'form-control'}))
    extend_policer_cks_vk = forms.CharField(label='Ограничение', required=False, widget=forms.Select(choices=type_police_cks_vk, attrs={'class': 'form-control'}))
    extend_policer_vm = forms.CharField(label='Ограничение', required=False,
                                  widget=forms.Select(choices=type_police_vm, attrs={'class': 'form-control'}))


class CksForm(forms.Form):
    pointA = forms.CharField(label='Точка A', widget=forms.TextInput(attrs={'class': 'form-control'}))
    pointB = forms.CharField(label='Точка B', widget=forms.TextInput(attrs={'class': 'form-control'}))
    type_police = [('полисером на Subinterface', 'Subinterface'), ('портом подключения', 'Порт коммутатора'), ('не требуется', 'Не требуется')]
    policer_cks = forms.CharField(label='Ограничение', widget=forms.Select(choices=type_police, attrs={'class': 'form-control'}))
    types = [('access', 'access'), ('xconnect', 'xconnect'), ('trunk', 'trunk')]
    port_type = forms.CharField(label='Режим порта', required=False,
                           widget=forms.Select(choices=types, attrs={'class': 'form-control'}))
    exist_service = forms.CharField(label='Режим порта существующей услуги', required=False,
                           widget=forms.Select(choices=types, attrs={'class': 'form-control'}))
    connect = forms.CharField(label='Подключение', required=False,
                              widget=forms.Select(attrs={'class': 'form-control'}))


class PortVKForm(forms.Form):
    connect = forms.CharField(label='Подключение', required=False,
                              widget=forms.Select(attrs={'class': 'form-control'}))
    types = [('Cуществующая ВЛС', 'Cуществующая ВЛС'), ('Новая ВЛС', 'Новая ВЛС'),]
    type_vk = forms.CharField(label='Тип ВЛС',
                                 widget=forms.Select(choices=types, attrs={'class': 'form-control'}))
    exist_vk = forms.CharField(label='Cуществующая ВЛС', required=False, widget=forms.TextInput(attrs={'class': 'form-control'}))
    type_police = [('полисером на Subinterface', 'Subinterface'), ('на порту подключения', 'Порт коммутатора'), ('не требуется', 'Не требуется')]
    policer_vk = forms.CharField(label='Ограничение', widget=forms.Select(choices=type_police, attrs={'class': 'form-control'}))
    types = [('access', 'access'), ('xconnect', 'xconnect'), ('trunk', 'trunk')]
    port_type = forms.CharField(label='Режим порта', required=False,
                               widget=forms.Select(choices=types, attrs={'class': 'form-control'}))
    exist_service = forms.CharField(label='Режим порта существующей услуги', required=False,
                                    widget=forms.Select(choices=types, attrs={'class': 'form-control'}))


class PortVMForm(forms.Form):
    connect = forms.CharField(label='Подключение', required=False,
                              widget=forms.Select(attrs={'class': 'form-control'}))
    types = [('Cуществующий ВМ', 'Cуществующий ВМ'), ('Новый ВМ', 'Новый ВМ'),]
    type_vm = forms.CharField(label='Тип ВМ',
                              widget=forms.Select(choices=types, attrs={'class': 'form-control'}))
    exist_vm = forms.CharField(label='Cуществующий ВМ', required=False, widget=forms.TextInput(attrs={'class': 'form-control'}))
    type_police = [('полисером на SVI', 'SVI'), ('на порту подключения', 'Порт коммутатора'), ('не требуется', 'Не требуется')]
    policer_vm = forms.CharField(label='Ограничение', widget=forms.Select(choices=type_police, attrs={'class': 'form-control'}))
    vm_inet = forms.BooleanField(required=False, label='С доступом в Интернет', widget=forms.CheckboxInput(attrs={'class': 'form-check'}))
    types = [('access', 'access'), ('trunk', 'trunk')]
    port_type = forms.CharField(label='Режим порта', required=False,
                               widget=forms.Select(choices=types, attrs={'class': 'form-control'}))
    exist_service_vm = forms.CharField(label='Режим порта существующей услуги', required=False,
                                    widget=forms.Select(choices=types, attrs={'class': 'form-control'}))

class VideoForm(forms.Form):
    camera_number = forms.IntegerField(min_value=1, max_value=16, label='Количество камер', required=False,
                                       widget=forms.NumberInput(attrs={'class': 'form-control'}))
    camera_model = forms.CharField(label='Модель камеры', widget=forms.TextInput(attrs={'class': 'form-control'}))
    type_schema = [
        ('4', '4'),
        ('4+4', '4+4'),
        ('4+8', '4+8'),
        ('8', '8'),
        ('8+4', '8+4'),
        ('8+8', '8+8'),
    ]
    schema_poe = forms.CharField(label='POE-коммутаторы', required=False,
                                   widget=forms.Select(choices=type_schema, attrs={'class': 'form-control'}))
    poe_1_cameras = forms.IntegerField(max_value=8, label='Количество камер на POE-коммутаторе №1', required=False,
                                       widget=forms.NumberInput(attrs={'class': 'form-control'}))
    poe_2_cameras = forms.IntegerField(max_value=8, label='Количество камер на POE-коммутаторе №2', required=False,
                                       widget=forms.NumberInput(attrs={'class': 'form-control'}))
    voice = forms.BooleanField(label='Запись звука', required=False,
                               widget=forms.CheckboxInput(attrs={'class': 'form-check'}))
    type_deep_archive = [('0', '0'), ('3', '3'), ('7', '7'), ('15', '15'), ('30', '30'), ('90', '90')]
    deep_archive = forms.CharField(label='Глубина архива камеры',
                                   widget=forms.Select(choices=type_deep_archive, attrs={'class': 'form-control'}))
    camera_place_one = forms.CharField(label='Место установки Камеры №1', required=False,
                                       widget=forms.TextInput(attrs={'class': 'form-control'}),
                                       help_text='только если 1 или 2 камеры')
    camera_place_two = forms.CharField(label='Место установки Камеры №2', required=False,
                                       widget=forms.TextInput(attrs={'class': 'form-control'}),
                                       help_text='только если 1 или 2 камеры')
    camera_new = forms.IntegerField(min_value=1, max_value=15, label='Количество новых камер', required=False,
                                    widget=forms.NumberInput(attrs={'class': 'form-control'}))
    type_schema = [
        ('1-0-0', '1-0-0'),
        ('2-0-0', '2-0-0'),
        ('1-4-0', '1-4-0'),
        ('1-8-0', '1-8-0'),
        ('0-4-0', '0-4-0'),
        ('0-8-0', '0-8-0'),
        ('0-4-4', '0-4-4'),
        ('0-8-4', '0-8-4'),
        ('0-4-8', '0-4-8'),
        ('0-8-8', '0-8-8'),
    ]
    camera_schema = forms.CharField(label='Cхема POE оборудования', required=False,
                                   widget=forms.Select(choices=type_schema, attrs={'class': 'form-control'}))
    count_busy_ports_1 = forms.IntegerField(min_value=0, max_value=8, label='Количество камер на POE коммутаторе №1',
                                       widget=forms.NumberInput(attrs={'class': 'form-control'}), required=False)
    count_busy_ports_2 = forms.IntegerField(min_value=0, max_value=8, label='Количество камер на POE коммутаторе №2',
                                       widget=forms.NumberInput(attrs={'class': 'form-control'}), required=False)


class PassVideoForm(forms.Form):
    change_video_ip = forms.BooleanField(label="Изменение IP", required=False, widget=forms.CheckboxInput(attrs={'class': 'form-check'}))
    camera_port_0 = forms.CharField(label='Порт для камеры', widget=forms.TextInput(attrs={'class': 'form-control'}))
    camera_name_0 = forms.CharField(label='Название камеры', widget=forms.TextInput(attrs={'class': 'form-control'}))
    camera_place_0 = forms.CharField(label='Новое место камеры', widget=forms.TextInput(attrs={'class': 'form-control'}))
    types_poe = [
        ('Сущ. POE-инжектор', 'Сущ. POE-инжектор'),
        ('Новый POE-инжектор', 'Новый POE-инжектор'),
        ('Сущ. POE-коммутатор', 'Сущ. POE-коммутатор'),
        ('Новый POE-коммутатор', 'Новый POE-коммутатор'),
    ]
    poe = forms.CharField(label='POE-оборудование',
                                   widget=forms.Select(choices=types_poe, attrs={'class': 'form-control'}))

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if kwargs.get('data'):
            # for view func-based fields locate in args
            new_fields = set(kwargs['data'].keys()) - set(self.fields.keys())
            new_fields.remove('csrfmiddlewaretoken')

            for field in new_fields:
                self.fields[f'{field}'] = forms.CharField()


class ContractForm(forms.Form):
    contract =forms.CharField(max_length=150, label='Договор', widget=forms.TextInput(attrs={'class': 'form-control'}))


class ListResourcesForm(forms.Form):
    resource = forms.BooleanField(label="", required=False, widget=forms.CheckboxInput(attrs={'class': 'form-check'}))


class ListContractIdForm(forms.Form):
    resource = forms.BooleanField(label="", required=False, widget=forms.CheckboxInput(attrs={'class': 'form-check'}))


class ListJobsForm(forms.Form):
    types = [
        ('Перенос', 'Перенос'),
        ('Расширение', 'Расширение'),
        ('Восстановление', 'Восстановление'),
        ('Организация', 'Организация'),
        ('Изменение, не СПД', 'Изменение'),
        ('Не требуется', 'Не требуется'),


    ]
    jobs = forms.CharField(label='',
                                 widget=forms.Select(choices=types, attrs={'class': 'form-control'}))
    requisite = forms.CharField(label='', required=False,
                           widget=forms.Select(attrs={'class': 'form-control'}))


class PassTurnoffForm(forms.Form):
    ppr = forms.CharField(label='ППР', required=False, widget=forms.TextInput(attrs={'class': 'form-control'}))


class ChangeServForm(forms.Form):
    types = [("Организация ШПД trunk'ом", "ШПД. Организация trunk'ом"),
             ("Организация ШПД trunk'ом с простоем", "ШПД. Организация trunk'ом с простоем"),
             ("Изменение cхемы организации ШПД", "ШПД. Изменение cхемы"),
             ("Замена IP", "ШПД. Замена IP"),
             ("Замена connected на connected", "ШПД. Замена connected на connected подсеть"),
             ("Организация доп connected", "ШПД. Организация доп. connected подсети"),
             ("Организация доп маршрутизируемой", "ШПД. Организация доп. маршрутизируемой подсети"),
             ("Организация доп IPv6", "ШПД. Организация доп IPv6"),
             ("Организация ЦКС trunk'ом", "ЦКС. Организация trunk'ом"),
             ("Организация ЦКС trunk'ом с простоем", "ЦКС. Организация trunk'ом с простоем"),
             ("Организация порта ВЛС trunk'ом", "ВЛС. Организация порта trunk'ом"),
             ("Организация порта ВЛС trunk'ом с простоем", "ВЛС. Организация порта trunk'ом с простоем"),
             ("Организация порта ВМ trunk'ом", "ВМ. Организация порта trunk'ом"),
             ("Организация порта ВМ trunk'ом с простоем", "ВМ. Организация порта trunk'ом с простоем"),
             ("Установка дополнительных камер СВН", "СВН. Установка дополнительных камер"),
             ("Изменение сервиса", "Изменение сервиса"),
             ]
    type_change_service = forms.CharField(label='Варианты ТР', widget=forms.Select(choices=types, attrs={'class': 'form-control'}))


class ChangeParamsForm(forms.Form):
    types_mask = [('/32', '/32'),
                  ('/30', '/30'),
                  ('/29', '/29'),
                  ('/28', '/28')]
    new_mask = forms.CharField(label='Новая маска', required=False,
                                       widget=forms.Select(choices=types_mask, attrs={'class': 'form-control'}))
    routed_ip = forms.CharField(max_length=20, required=False,
                                label='Ip-адрес', widget=forms.TextInput(attrs={'class': 'form-control'}))
    routed_vrf = forms.CharField(max_length=50, required=False,
                                 label='VRF', widget=forms.TextInput(attrs={'class': 'form-control'}))
    types_mask = [(True, 'Новая родительская подсеть'),
                  (False, 'Существующая родительская подсеть'),
                  ]
    parent_subnet = forms.CharField(label='Родительская сеть', required=False,
                               widget=forms.Select(choices=types_mask, attrs={'class': 'form-control'}))
    ip_ban = forms.BooleanField(label="Причина блокировка в интернете", required=False,
                                         widget=forms.CheckboxInput(attrs={'class': 'form-check'}))


class SearchTicketsForm(forms.Form):
    spp = forms.CharField(label='Заявка СПП', required=False,
                               widget=forms.TextInput(attrs={'class': 'form-control'}))
    tr = forms.CharField(label='ТР', required=False,
                               widget=forms.TextInput(attrs={'class': 'form-control'}))
    pps = forms.CharField(label='ППС', required=False,
                               widget=forms.TextInput(attrs={'class': 'form-control'}))
    connection_point = forms.CharField(label='Точка подключения', required=False,
                          widget=forms.TextInput(attrs={'class': 'form-control'}))
    client = forms.CharField(label='Клиент', required=False,
                               widget=forms.TextInput(attrs={'class': 'form-control'}))
    ortr = forms.CharField(label='Поле ОРТР', required=False,
                               widget=forms.TextInput(attrs={'class': 'form-control'}))
    start = forms.DateTimeField(label='Дата начала', required=False,
                                # widget=forms.DateTimeInput(attrs={'class': 'form-control'})
                                input_formats = ['%d.%m.%Y'],
                                                widget = forms.DateTimeInput(attrs={
                                    'class': 'form-control datetimepicker-input',
                                    'data-target': '#datetimepicker1'
                                })
                                )
    stop = forms.DateTimeField(label='Дата окончания', required=False,
                                input_formats=['%d.%m.%Y'],
                                widget=forms.DateTimeInput(attrs={
                                    'class': 'form-control datetimepicker-input',
                                    'data-target': '#datetimepicker2'
                                })
                                )
    titles = forms.CharField(label='Заголовки', required=False,
                           widget=forms.TextInput(attrs={'class': 'form-control'}))


class PprForm(forms.Form):
    new_ppr = forms.BooleanField(label='Новая ППР', required=False, widget=forms.CheckboxInput(attrs={'class': 'form-check'}))
    title_ppr = forms.CharField(label='Поле Кратко ППР', required=False,
                                widget=forms.TextInput(attrs={'class': 'form-control'}))
    exist_ppr = forms.CharField(label='Cуществующая ППР', required=False, widget=forms.TextInput(attrs={'class': 'form-control'}))


class AddResourcesPprForm(forms.Form):
    ppr_resources = forms.CharField(label='Массовое добавление ресурсов и линков', required=False, widget=forms.Textarea(attrs={'class': 'form-control'}))


class TimeTrackingForm(forms.Form):

    technologs = [(user, user.last_name) for user in User.objects.filter(groups__name__in=['Сотрудники ОУЗП'])]
    technolog = forms.CharField(label='Технолог',
                                widget=forms.Select(choices=technologs, attrs={'class': 'form-control'}))
    start = forms.DateTimeField(label='Дата начала',
                                # widget=forms.DateTimeInput(attrs={'class': 'form-control'})
                                input_formats=['%d.%m.%Y'],
                                                widget = forms.DateTimeInput(attrs={
                                    'class': 'form-control datetimepicker-input',
                                    'data-target': '#datetimepicker1'
                                })
                                )
    stop = forms.DateTimeField(label='Дата окончания',
                                input_formats=['%d.%m.%Y'],
                                widget=forms.DateTimeInput(attrs={
                                    'class': 'form-control datetimepicker-input',
                                    'data-target': '#datetimepicker2'
                                })
                                )


class AddCommentForm(forms.Form):
    types_return = [
        ('Вернуть менеджеру', 'Вернуть менеджеру'),
        ('Вернуть в ОТПМ', 'Вернуть в ОТПМ'),
    ]
    return_to = forms.CharField(widget=forms.Select(choices=types_return, attrs={'class': 'form-control'}))
    comment = forms.CharField(label='Добавить комментарий', widget=forms.Textarea(attrs={'class': 'form-control'}))


class SppDataForm(forms.Form):
    types_spd = [
        ('Комтехцентр', 'Комтехцентр'),
        ('РТК', 'ПАО "Ростелеком"'),
        ('ППМ', 'ООО "Пред-последняя миля"'),
        ('Вектор', 'ООО "Вектор СБ"'),
    ]
    types_tr = [
        ('Коммерческое', 'Коммерческое'),
        ('ПТО', 'ПТО'),
        ('Не требуется', 'Не требуется'),
    ]
    con_points = [
        ('Нов. точка', 'Новая точка'),
        ('Сущ. точка', 'Существующая точка'),
    ]
    type_tr = forms.CharField(widget=forms.Select(choices=types_tr, attrs={'class': 'form-control'}))
    con_point = forms.CharField(widget=forms.Select(choices=con_points, attrs={'class': 'form-control'}))
    spd = forms.CharField(widget=forms.Select(choices=types_spd, attrs={'class': 'form-control'}))

class PpsForm(forms.Form):
    types_change_node = [
        ('0', '-----'),
        ('Установка нового КАД', 'Установка нового КАД'),
        ('Установка дополнительного КАД', 'Установка дополнительного КАД'),
        ('Замена КАД', 'Замена КАД'),
        ('Изменение трассы ВОК', 'Изменение трассы ВОК'),
        ('Изменение трассы клиентских линий', 'Изменение трассы клиентских линий'),
        ('Изминение физ. точки ППС', 'Изминение физ. точки ППС'),
    ]
    types_new_model = [
        ('24-портовый медный коммутатор (с 4-мя SFP портами)', '24-портовый медный коммутатор (с 4-мя SFP портами)'),
        ('24-портовый медный коммутатор', '24-портовый медный коммутатор'),
        ('48-портовый медный коммутатор', '48-портовый медный коммутатор'),
        ('24-портовый оптогигабитный коммутатор', '24-портовый оптогигабитный коммутатор'),
        ('48-портовый оптогигабитный коммутатор', '48-портовый оптогигабитный коммутатор'),
    ]
    types_add_kad = [
        ('не требуется', 'не требуется'),
        ('Установка 2-го кад в гирлянду', 'Установка 2-го кад в гирлянду'),
        ('Установка 1-го оптического кад в гирлянду', 'Установка 1-го оптического кад в гирлянду'),
    ]
    type_change_node = forms.CharField(label='Тип работ на узле',
                                       widget=forms.Select(choices=types_change_node, attrs={'class': 'form-control'}))
    kad_name = forms.CharField(label='Название КАД', required=False,
                                  widget=forms.TextInput(attrs={'class': 'form-control'}))
    type_new_model_kad = forms.CharField(label='Новая модель КАД',
                                   widget=forms.Select(choices=types_new_model, attrs={'class': 'form-control'}))
    ppr = forms.CharField(label='ППР', required=False,
                                widget=forms.TextInput(attrs={'class': 'form-control'}))
    type_add_kad = forms.CharField(label='Тип установки доп. КАД',
                                       widget=forms.Select(choices=types_add_kad, attrs={'class': 'form-control'}))
    disabled_port = forms.CharField(label='Порт для доп. КАД', required=False,
                          widget=forms.TextInput(attrs={'class': 'form-control'}))
    disabled_link = forms.CharField(label='Линк/договор отключения', required=False,
                          widget=forms.TextInput(attrs={'class': 'form-control'}))
    disable = forms.BooleanField(label='Отключение', required=False,
                                 widget=forms.CheckboxInput(attrs={'class': 'form-check'}))
    deleted_kad = forms.CharField(label='Второй КАД в гирлянде', required=False,
                                    widget=forms.TextInput(attrs={'class': 'form-control'}))
    delete_kad = forms.BooleanField(label='Демонтаж второго КАД', required=False,
                                 widget=forms.CheckboxInput(attrs={'class': 'form-check'}))
    pto_change_node = forms.BooleanField(label='УС меняется', required=False,
                                 widget=forms.CheckboxInput(attrs={'class': 'form-check'}))
    pto_change_node_name = forms.CharField(label='Новое название УС', required=False,
                          widget=forms.TextInput(attrs={'class': 'form-control'}))
    pto_current_node_name = forms.CharField(label='Текущее название УС', required=False,
                                           widget=forms.TextInput(attrs={'class': 'form-control'}))
    pto_dark_optic = forms.BooleanField(label='Наличие "темного" ОВ в ВОК', required=False,
                                         widget=forms.CheckboxInput(attrs={'class': 'form-check'}))
    pto_dark_optic_client = forms.CharField(label='Договор клиента', required=False,
                                           widget=forms.TextInput(attrs={'class': 'form-control'}))
    pto_dark_optic_after = forms.CharField(label='Решение по проверке темного ОВ', required=False,
                                            widget=forms.Textarea(attrs={'class': 'form-control'}))

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if kwargs.get('data'):
            # for view func-based fields locate in args
            new_fields = set(kwargs['data'].keys()) - set(self.fields.keys())
            new_fields.remove('csrfmiddlewaretoken')

            for field in new_fields:
                self.fields[f'{field}'] = forms.CharField()


class KtcEnvForm(forms.Form):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if kwargs.get('data'):
            # for view func-based fields locate in args
            new_fields = set(kwargs['data'].keys()) - set(self.fields.keys())
            new_fields.remove('csrfmiddlewaretoken')
            for field in new_fields:
                if 'logic_csw' in field:
                    self.fields[f'{field}'] = forms.BooleanField(required=False)
                else:
                    self.fields[f'{field}'] = forms.CharField(required=False)


class OtherEnvForm(forms.Form):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if kwargs.get('data'):
            # for view func-based fields locate in args
            new_fields = set(kwargs['data'].keys()) - set(self.fields.keys())
            new_fields.remove('csrfmiddlewaretoken')

            for field in new_fields:
                self.fields[f'{field}'] = forms.CharField(required=False)
