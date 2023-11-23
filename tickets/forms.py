from django.core.exceptions import ValidationError
from django.db import transaction
from django import forms

from .models import TR, SPP, ServicesTR #, HoldPosition, UserHoldPosition
from django.contrib.auth.forms import UserCreationForm, AuthenticationForm
from django.contrib.auth.models import User
from django.forms import ModelChoiceField




class OrtrForm(forms.Form):
    ortr_field = forms.CharField(label='Решение ОРТР', widget=forms.Textarea(attrs={'class': 'form-control'}))
    pps = forms.CharField(label='ППС', required=False, widget=forms.TextInput(attrs={'class': 'form-control'}))
    kad = forms.CharField(label='КАД', required=False, widget=forms.TextInput(attrs={'class': 'form-control'}))
    ots_field = forms.CharField(label='Решение ОТС', required=False, widget=forms.Textarea(attrs={'class': 'form-control'}))


class LinkForm(forms.Form):
    spplink =forms.CharField(max_length=150, label='Ссылка на ТР', widget=forms.TextInput(attrs={'class': 'form-control'}))


class LocalForm(forms.Form):
    types = [('СКС', 'СКС'), ('ЛВС', 'ЛВС'), ('Под видеонаблюдение', 'Под видеонаблюдение')]
    local_type = forms.CharField(label='Тип ЛВС', widget=forms.Select(choices=types, attrs={'class': 'form-control'}))
    local_ports = forms.IntegerField(max_value=24, label='Количество портов',
                                   widget=forms.NumberInput(attrs={'class': 'form-control'}))


class SksForm(forms.Form):
    sks_poe = forms.BooleanField(label='PoE-инжектор', required=False,
                                      widget=forms.CheckboxInput(attrs={'class': 'form-check'}))
    sks_router = forms.BooleanField(label='Подключить в марш.', required=False,
                                 widget=forms.CheckboxInput(attrs={'class': 'form-check'}))


class LvsForm(forms.Form):
    lvs_busy = forms.BooleanField(label='Все порты заняты', required=False,
                                    widget=forms.CheckboxInput(attrs={'class': 'form-check'}))
    types = [('TP-Link TL-SG105 V4', 'TP-Link TL-SG105 V4'), ('TP-Link TL-SG108 V4', 'TP-Link TL-SG108 V4'),
             ('ZYXEL GS1200-5', 'ZYXEL GS1200-5'), ('ZYXEL GS1200-8', 'ZYXEL GS1200-8'),
             ('D-link DGS-1100-16/B', 'D-link DGS-1100-16/B'), ('D-link DGS-1100-24/B', 'D-link DGS-1100-24/B')]
    lvs_switch = forms.CharField(label='Коммутатор', widget=forms.Select(choices=types, attrs={'class': 'form-control'}))



class HotspotForm(forms.Form):
    exist_hotspot_client = forms.BooleanField(label='Существующий клиент', required=False, widget=forms.CheckboxInput(attrs={'class': 'form-check'}))
    hotspot_local_wifi = forms.BooleanField(label='С локальной сетью WiFi', required=False,
                                              widget=forms.CheckboxInput(attrs={'class': 'form-check'}))
    hotspot_points = forms.IntegerField(max_value=10, required=False, label='Количество точек', widget=forms.NumberInput(attrs={'class': 'form-control'}))
    hotspot_users = forms.IntegerField(max_value=1000, label='Количество пользователей', widget=forms.NumberInput(attrs={'class': 'form-control'}))


class PhoneForm(forms.Form):
    types = [('ak', 'Аналог, установка шлюза у клиента'), ('ap', 'Аналог, установка шлюза на ППС'), ('ab', 'Аналог, установка шлюза не требуется'), ('s', 'SIP, по логину/паролю'), ('st', 'SIP, IP-транк')]
    type_phone = forms.CharField(label='Тип телефонии', widget=forms.Select(choices=types, attrs={'class': 'form-control'}))
    types_vgw = [('D-Link DVG-5402SP', 'D-Link DVG-5402SP'), ('Eltex RG-1404G или Eltex TAU-4M.IP', 'Eltex TAU-4M.IP'),
                 ('Eltex TAU-8.IP', 'Eltex TAU-8.IP'), ('Eltex TAU-16.IP', 'Eltex TAU-16.IP'), ('Eltex TAU-24.IP', 'Eltex TAU-24.IP'),
                 ('Eltex TAU-36.IP', 'Eltex TAU-36.IP'), ('Eltex TAU-72.IP', 'Eltex TAU-72.IP'), ('Не требуется', 'Не требуется')]
    vgw = forms.CharField(label='Установка шлюза', widget=forms.Select(choices=types_vgw, attrs={'class': 'form-control'}))
    channel_vgw = forms.CharField(max_length=11, label='Количество каналов', widget=forms.TextInput(attrs={'class': 'form-control'}))
    ports_vgw = forms.CharField(max_length=11, required=False, label='Количество портов ВАТС', widget=forms.TextInput(attrs={'class': 'form-control'}))
    types_ip_trunk = [('Не требуется', 'Не требуется'), ('access', 'access'), ('trunk', 'trunk')]
    type_ip_trunk = forms.CharField(label='Режим порта для IP-транк', required=False,
                                widget=forms.Select(choices=types_ip_trunk, attrs={'class': 'form-control'}))
    form_exist_vgw_model = forms.CharField(max_length=100, label='Модель существующего шлюза', required=False,
                                  widget=forms.TextInput(attrs={'class': 'form-control'}))
    form_exist_vgw_name = forms.CharField(max_length=100, label='Название существующего шлюза', required=False,
                                  widget=forms.TextInput(attrs={'class': 'form-control'}))
    form_exist_vgw_port = forms.CharField(max_length=100, label='Порты существующего шлюза', required=False,
                                  widget=forms.TextInput(attrs={'class': 'form-control'}))

class ItvForm(forms.Form):
    types = [('vl', 'В отдельном vlan'), ('novl', 'В vlan новой услуги ШПД'), ('novlexist', 'В vlan действующей услуги ШПД')]
    type_itv = forms.CharField(label='Тип ITV', widget=forms.Select(choices=types, attrs={'class': 'form-control'}))
    cnt_itv = forms.IntegerField(max_value=20, label='Количество приставок',
                                        widget=forms.NumberInput(attrs={'class': 'form-control'}))
    router_itv = forms.BooleanField(label='Маршрутизатор для иТВ', required=False, widget=forms.CheckboxInput(attrs={'class': 'form-check'}))


class VolsForm(forms.Form):
    #types первое значение выводится в шаблон, второе значение отображается в форме
    types = [('конвертер 1310 нм, выставить на конвертере режим работы Auto', 'конвертер 1310 нм'),
             ('конвертер 1550 нм, выставить на конвертере режим работы Auto', 'конвертер 1550 нм'),
             ('оптический передатчик SFP WDM, до 20 км, 1310 нм', 'SFP WDM, до 20 км, 1310 нм'),
             ('оптический передатчик SFP WDM, до 20 км, 1550 нм в клиентское оборудование', 'SFP WDM, до 20 км, 1550 нм'),
             ('оптический передатчик SFP WDM, до 3 км, 1310 нм', 'SFP WDM, до 3 км, 1310 нм'),
             ('оптический передатчик SFP WDM, до 3 км, 1550 нм в клиентское оборудование', 'SFP WDM, до 3 км, 1550 нм'),
             ('конвертер SNR-CVT-1000SFP-mini с модулем SFP WDM, дальность до 3 км, 1550 нм', 'SNR-CVT-1000SFP-mini с SFP WDM, 3 км, 1550 нм'),
             ('конвертер SNR-CVT-1000SFP-mini с модулем SFP WDM, дальность до 20 км, 1550 нм', 'SNR-CVT-1000SFP-mini с SFP WDM, 20 км, 1550 нм')]
    speed = [('100FD', '100FD'), ('Auto', 'Auto')]
    types_correct_sreda = [
        ('1', 'UTP'),
        ('2', 'ВОЛС'),
        ('4', 'FTTH'),
        ('3', 'WiFi'),
    ]
    correct_sreda = forms.CharField(label='Среда передачи',
                                  widget=forms.Select(choices=types_correct_sreda, attrs={'class': 'form-control'}))
    device_pps = forms.CharField(label='На стороне ППС', widget=forms.Select(choices=types, attrs={'class': 'form-control'}))
    device_client = forms.CharField(label='На стороне клиента', widget=forms.Select(choices=types, attrs={'class': 'form-control'}))
    kad = forms.CharField(label='Коммутатор', widget=forms.TextInput(attrs={'class': 'form-control'}))
    speed_port = forms.CharField(label='Скорость порта', widget=forms.Select(choices=speed, attrs={'class': 'form-control'}))
    port = forms.CharField(label='Порт', widget=forms.TextInput(attrs={'class': 'form-control'}))
    ppr = forms.CharField(label='ППР', required=False, widget=forms.TextInput(attrs={'class': 'form-control'}))
    logic_csw = forms.BooleanField(label='Установка КК', required=False, widget=forms.CheckboxInput(attrs={'class': 'form-check'}))
    logic_replace_csw = forms.BooleanField(label='Замена КК', required=False,
                                           widget=forms.CheckboxInput(attrs={'class': 'form-check'}))
    logic_change_csw = forms.BooleanField(label='Перенос КК', required=False,
                                          widget=forms.CheckboxInput(attrs={'class': 'form-check'}))
    logic_change_gi_csw = forms.BooleanField(label='Перевод КК 1G', required=False,
                                              widget=forms.CheckboxInput(attrs={'class': 'form-check'}))


class CopperForm(forms.Form):
    types_correct_sreda = [
        ('1', 'UTP'),
        ('2', 'ВОЛС'),
        ('4', 'FTTH'),
        ('3', 'WiFi'),
    ]
    correct_sreda = forms.CharField(label='Среда передачи',
                                    widget=forms.Select(choices=types_correct_sreda, attrs={'class': 'form-control'}))
    kad = forms.CharField(label='Коммутатор', widget=forms.TextInput(attrs={'class': 'form-control'}))
    port = forms.CharField(label='Порт', widget=forms.TextInput(attrs={'class': 'form-control'}))
    logic_csw = forms.BooleanField(label='Установка КК', required=False, widget=forms.CheckboxInput(attrs={'class': 'form-check'}))
    logic_replace_csw = forms.BooleanField(label='Замена КК', required=False,
                                   widget=forms.CheckboxInput(attrs={'class': 'form-check'}))
    logic_change_csw = forms.BooleanField(label='Перенос КК', required=False,
                                             widget=forms.CheckboxInput(attrs={'class': 'form-check'}))
    logic_change_gi_csw = forms.BooleanField(label='Перевод КК 1G', required=False,
                                   widget=forms.CheckboxInput(attrs={'class': 'form-check'}))


class WirelessForm(forms.Form):
    ap_types = [('AirGrid 23 M5 или LiteBeam LBE-M5-23', 'LiteBeam LBE-M5-23'),
             ('AirGrid 27 M5', 'AirGrid 27 M5'),
             ('Nanostation M5', 'Nanostation M5'),
             ('Infinet E5', 'Infinet E5')]
    types_correct_sreda = [
        ('1', 'UTP'),
        ('2', 'ВОЛС'),
        ('4', 'FTTH'),
        ('3', 'WiFi'),
    ]
    correct_sreda = forms.CharField(label='Среда передачи',
                                    widget=forms.Select(choices=types_correct_sreda, attrs={'class': 'form-control'}))
    access_point = forms.CharField(label='Точки доступа', widget=forms.Select(choices=ap_types, attrs={'class': 'form-control'}))
    kad = forms.CharField(label='Коммутатор', widget=forms.TextInput(attrs={'class': 'form-control'}))
    port = forms.CharField(label='Порт', widget=forms.TextInput(attrs={'class': 'form-control'}))
    ppr = forms.CharField(label='ППР', required=False, widget=forms.TextInput(attrs={'class': 'form-control'}))
    logic_csw = forms.BooleanField(label='Установка КК', required=False, widget=forms.CheckboxInput(attrs={'class': 'form-check'}))
    logic_replace_csw = forms.BooleanField(label='Замена КК', required=False,
                                           widget=forms.CheckboxInput(attrs={'class': 'form-check'}))
    logic_change_csw = forms.BooleanField(label='Перенос КК', required=False,
                                          widget=forms.CheckboxInput(attrs={'class': 'form-check'}))
    logic_change_gi_csw = forms.BooleanField(label='Перевод КК на 1G', required=False,
                                              widget=forms.CheckboxInput(attrs={'class': 'form-check'}))


class CswForm(forms.Form):
    types_csw = [('D-Link DGS-1100-06/ME', 'D-Link DGS-1100-06/ME'), ('24-портовый коммутатор', '24-портовый коммутатор')]
    types_port = [('5', '5'), ('6', '6'), ('указанный ОНИТС СПД', 'указанный ОНИТС СПД')]
    types_speed_csw = [('Нет', 'Нет'), ('100', '100'), ('1000', '1000')]
    types_install_csw = [('Медная линия и порт не меняются', 'Медная линия и порт не меняются'),
             ('ВОЛС и порт не меняются', 'ВОЛС и порт не меняются'),
             ('Перевод на гигабит переключение с меди на ВОЛС', 'Перевод на гигабит переключение с меди на ВОЛС'),
             ('Перевод на гигабит по меди на текущем узле', 'Перевод на гигабит по меди на текущем узле'),
             ('Перевод на гигабит по ВОЛС на текущем узле', 'Перевод на гигабит по ВОЛС на текущем узле'),
             ('Перенос на новый узел', 'Перенос на новый узел')]
    types_exist_sreda_csw = [
        ('1', 'UTP'),
        ('2', 'ВОЛС'),
        ('4', 'FTTH'),
        ('3', 'WiFi'),
    ]
    logic_csw_1000 = forms.BooleanField(label='Запуск КК на магистрали 1 Гбит/с', required=False, widget=forms.CheckboxInput(attrs={'class': 'form-check'}))
    exist_speed_csw = forms.CharField(label='Существующая магистраль', required=False, widget=forms.Select(choices=types_speed_csw, attrs={'class': 'form-control'}))
    exist_sreda_csw = forms.CharField(label='Существующее подключение КК', required=False,
                                       widget=forms.Select(choices=types_exist_sreda_csw, attrs={'class': 'form-control'}))
    type_install_csw = forms.CharField(label='Варианты установки КК', required=False,
                                       widget=forms.Select(choices=types_install_csw, attrs={'class': 'form-control'}))
    model_csw = forms.CharField(label='Модель', required=False, widget=forms.Select(choices=types_csw, attrs={'class': 'form-control'}))
    port_csw = forms.CharField(label='Порт', required=False, widget=forms.Select(choices=types_port, attrs={'class': 'form-control'}))


class ShpdForm(forms.Form):
    router = forms.BooleanField(label='Маршрутизатор', required=False, widget=forms.CheckboxInput(attrs={'class': 'form-check'}))
    types = [('access', 'access'), ('trunk', 'trunk')]
    type_shpd = forms.CharField(label='Режим порта', required=False,
                                 widget=forms.Select(choices=types, attrs={'class': 'form-control'}))
    exist_service = forms.CharField(label='Режим порта существующей услуги', required=False,
                                    widget=forms.Select(choices=types, attrs={'class': 'form-control'}))


class ExtendServiceForm(forms.Form):
    type_police_cks_vk = [
        ('полисером Subinterface', 'полисером Subinterface'),
        ('портом подключения', 'портом подключения'),
        ('не требуется', 'не требуется')]
    type_police_vm = [
        ('полисером на SVI', 'полисером на SVI'),
        ('портом подключения', 'портом подключения'),
        ('не требуется', 'не требуется')]
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
    type_police = [('полисером Subinterface', 'полисером Subinterface'), ('портом подключения', 'портом подключения'), ('не требуется', 'не требуется')]
    policer_cks = forms.CharField(label='Ограничение', widget=forms.Select(choices=type_police, attrs={'class': 'form-control'}))
    types = [('access', 'access'), ('trunk', 'trunk')]
    type_cks = forms.CharField(label='Режим порта', required=False,
                           widget=forms.Select(choices=types, attrs={'class': 'form-control'}))
    exist_service = forms.CharField(label='Режим порта существующей услуги', required=False,
                           widget=forms.Select(choices=types, attrs={'class': 'form-control'}))


class PortVKForm(forms.Form):
    new_vk = forms.BooleanField(label='Новая ВЛС', required=False, widget=forms.CheckboxInput(attrs={'class': 'form-check'}))
    exist_vk = forms.CharField(label='Cуществующая ВЛС', required=False, widget=forms.TextInput(attrs={'class': 'form-control'}))
    type_police = [('полисером на Subinterface', 'полисером на Subinterface'), ('на порту подключения', 'на порту подключения'), ('не требуется', 'не требуется')]
    policer_vk = forms.CharField(label='Ограничение', widget=forms.Select(choices=type_police, attrs={'class': 'form-control'}))
    types = [('access', 'access'), ('trunk', 'trunk')]
    type_portvk = forms.CharField(label='Режим порта', required=False,
                               widget=forms.Select(choices=types, attrs={'class': 'form-control'}))
    exist_service = forms.CharField(label='Режим порта существующей услуги', required=False,
                                    widget=forms.Select(choices=types, attrs={'class': 'form-control'}))


class PortVMForm(forms.Form):
    new_vm = forms.BooleanField(label='Новый ВМ', required=False, widget=forms.CheckboxInput(attrs={'class': 'form-check'}))
    exist_vm = forms.CharField(label='Cуществующий ВМ', required=False, widget=forms.TextInput(attrs={'class': 'form-control'}))
    type_police = [('полисером на SVI', 'полисером на SVI'), ('на порту подключения', 'на порту подключения'), ('не требуется', 'не требуется')]
    policer_vm = forms.CharField(label='Ограничение', widget=forms.Select(choices=type_police, attrs={'class': 'form-control'}))
    vm_inet = forms.BooleanField(required=False, label='С доступом в Интернет', widget=forms.CheckboxInput(attrs={'class': 'form-check'}))
    types = [('access', 'access'), ('trunk', 'trunk')]
    type_portvm = forms.CharField(label='Режим порта', required=False,
                               widget=forms.Select(choices=types, attrs={'class': 'form-control'}))
    exist_service_vm = forms.CharField(label='Режим порта существующей услуги', required=False,
                                    widget=forms.Select(choices=types, attrs={'class': 'form-control'}))

class VideoForm(forms.Form):
    camera_number = forms.IntegerField(max_value=9, label='Количество камер',
                                       widget=forms.NumberInput(attrs={'class': 'form-control'}))
    camera_model = forms.CharField(label='Модель камеры', widget=forms.TextInput(attrs={'class': 'form-control'}))
    voice = forms.BooleanField(label='Запись звука', required=False,
                               widget=forms.CheckboxInput(attrs={'class': 'form-check'}))
    type_deep_archive = [('0', '0'), ('3', '3'), ('7', '7'), ('15', '15'), ('30', '30')]
    deep_archive = forms.CharField(label='Глубина архива камеры',
                                   widget=forms.Select(choices=type_deep_archive, attrs={'class': 'form-control'}))
    camera_place_one = forms.CharField(label='Место установки Камеры №1', required=False,
                                       widget=forms.TextInput(attrs={'class': 'form-control'}),
                                       help_text='только если 1 или 2 камеры')
    camera_place_two = forms.CharField(label='Место установки Камеры №2', required=False,
                                       widget=forms.TextInput(attrs={'class': 'form-control'}),
                                       help_text='только если 1 или 2 камеры')


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
        ('Перенос, СПД', 'Перенос/расширение'),
        ('Организация/Изменение, СПД', 'Организация'),
        ('Изменение, не СПД', 'Сущ. порт'),
        ('Не требуется', 'Не требуется'),
    ]
    jobs = forms.CharField(label='',
                                 widget=forms.Select(choices=types, attrs={'class': 'form-control'}))


class TemplatesHiddenForm(forms.Form):
    hidden = forms.BooleanField(label="", required=False, widget=forms.CheckboxInput(attrs={'class': 'form-check'}))


class TemplatesStaticForm(forms.Form):
    static = forms.CharField(label='', required=False, widget=forms.TextInput(attrs={'class': 'form-control'}))


class PassTurnoffForm(forms.Form):
    ppr = forms.CharField(label='ППР', required=False, widget=forms.TextInput(attrs={'class': 'form-control'}))


class PassServForm(forms.Form):
    types_exist_sreda = [
        ('1', 'UTP'),
        ('2', 'ВОЛС'),
        ('4', 'FTTH'),
        ('3', 'WiFi'),
    ]
    exist_sreda = forms.CharField(label='Подключен по',
                                   widget=forms.Select(choices=types_exist_sreda, attrs={'class': 'form-control'}))
    types_passage = [
        ('Перенос сервиса в новую точку', 'Перенос сервиса в новую точку'),
        ('Перенос точки подключения', 'Перенос точки подключения'),
        ('Перенос логического подключения', 'Перенос трассы/логического подключения'),
        ('Перевод на гигабит', 'Расширение сервиса'),
    ]
    type_passage = forms.CharField(label='Варианты переноса',
                                widget=forms.Select(choices=types_passage, attrs={'class': 'form-control'}))
    types_change_log = [
        ('Порт и КАД не меняется', 'Порт и КАД не меняется'),
        ('Порт/КАД меняются', 'Порт/КАД меняются'),
    ]
    change_log = forms.CharField(label='Изменение логики при работах',
                                 widget=forms.Select(choices=types_change_log, attrs={'class': 'form-control'}))


class ChangeLogShpdForm(forms.Form):
    types_change_log_shpd = [
        ('существующая адресация', 'существующая адресация'),
        ('Новая подсеть /30', 'Новая подсеть /30'),
        ('Новая подсеть /32', 'Новая подсеть /32'),
    ]
    change_log_shpd = forms.CharField(label='Изменение схемы ШПД для подсетей с маской /32',
                                      widget=forms.Select(choices=types_change_log_shpd,
                                                          attrs={'class': 'form-control'}))


class ChangeServForm(forms.Form):
    types = [("Организация ШПД trunk'ом", "Организация ШПД trunk'ом"),
             ("Организация ШПД trunk'ом с простоем", "Организация ШПД trunk'ом с простоем"),
             ("Изменение cхемы организации ШПД", "Изменение cхемы организации ШПД"),
             ("Замена connected на connected", "Замена connected на connected"),
             ("Организация доп connected", "Организация доп connected"),
             ("Организация доп маршрутизируемой", "Организация доп маршрутизируемой"),
             ("Организация доп IPv6", "Организация доп IPv6"),
             ("Организация ЦКС trunk'ом", "Организация ЦКС trunk'ом"),
             ("Организация ЦКС trunk'ом с простоем", "Организация ЦКС trunk'ом с простоем"),
             ("Организация порта ВЛС trunk'ом", "Организация порта ВЛС trunk'ом"),
             ("Организация порта ВЛС trunk'ом с простоем", "Организация порта ВЛС trunk'ом с простоем"),
             ("Организация порта ВМ trunk'ом", "Организация порта ВМ trunk'ом"),
             ("Организация порта ВМ trunk'ом с простоем", "Организация порта ВМ trunk'ом с простоем")
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
        ('РТК', 'РТК'),
    ]
    types_tr = [
        ('Нов. точка', 'Новая точка'),
        ('Сущ. точка', 'Существующая точка'),
        ('ПТО', 'ПТО'),
        ('Не требуется', 'Не требуется'),
    ]
    type_tr = forms.CharField(widget=forms.Select(choices=types_tr, attrs={'class': 'form-control'}))
    spd = forms.CharField(widget=forms.Select(choices=types_spd, attrs={'class': 'form-control'}))

class PpsForm(forms.Form):
    types_change_node = [
        ('0', '-----'),
        ('Установка нового КАД', 'Установка нового КАД'),
        ('Установка дополнительного КАД', 'Установка дополнительного КАД'),
        ('Замена КАД', 'Замена КАД'),
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
        ('Установка 2-го медного кад в гирлянду', 'Установка 2-го медного кад в гирлянду'),
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

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if kwargs.get('data'):
            # for view func-based fields locate in args
            new_fields = set(kwargs['data'].keys()) - set(self.fields.keys())
            new_fields.remove('csrfmiddlewaretoken')

            for field in new_fields:
                self.fields[f'{field}'] = forms.CharField()


class RtkForm(forms.Form):
    types_pm = [
        ('ПМ', 'ПМ'),
        ('FVNO Медь', 'FVNO Медь'),
        ('FVNO FTTH', 'FVNO FTTH'),
        ('FVNO GPON', 'FVNO GPON'),
    ]
    vlan = forms.CharField(label='Vlan',
                                widget=forms.TextInput(attrs={'class': 'form-control'}))
    type_pm = forms.CharField(widget=forms.Select(choices=types_pm, attrs={'class': 'form-control'}))
    switch_ip = forms.CharField(label='IP коммутатора', required=False,
                                widget=forms.TextInput(attrs={'class': 'form-control'}))
    switch_port = forms.CharField(label='Порт коммутатора', required=False,
                                widget=forms.TextInput(attrs={'class': 'form-control'}))
    optic_socket = forms.CharField(label='Опт. розетка', required=False,
                                widget=forms.TextInput(attrs={'class': 'form-control'}))
    ploam = forms.CharField(label='PLOAM-пароль', required=False,
                                widget=forms.TextInput(attrs={'class': 'form-control'}))

    # def clean(self):
    #     cleaned_data = super().clean()
    #     type_pm = cleaned_data.get("type_pm")
    #     switch_ip = cleaned_data.get("switch_ip")
    #     switch_port = cleaned_data.get("switch_port")
    #     print(type_pm)
    #
    #
    #     if type_pm == 'FVNO Медь' and not all([switch_ip, switch_port]):
    #         # Only do something if both fields are valid so far.
    #         self.add_error(
    #                 "switch_ip", "required"
    #             )



# class TechnologModelChoiceField(ModelChoiceField):
#     """По умолчанию в ModelChoiceField используется поле, которое возвращает метод __str__, поэтому меняем
#      на нужное поле"""
#     def label_from_instance(self, obj):
#         return obj.last_name


# class OtpmPoolForm(forms.Form):
#     groups = [
#         ('Все', 'Все'),
#         ('Коммерческая', 'Коммерческая'),
#         ('ПТО', 'ПТО'),
#     ]
#     statuses = [
#         ('Все', 'Все'),
#         ('В работе', 'В работе'),
#         ('Не взята в работу', 'Не взята в работу'),
#         ('Отслеживается', 'Отслеживается'),
#     ]
#     # technologs = [
#     #     ('Все', 'Все'),
#     # ]
#     technolog = TechnologModelChoiceField(
#         queryset=User.objects.all(),
#         empty_label='Все',
#         required=False,
#         to_field_name='last_name',
#         widget=forms.Select(attrs={'class': 'form-control'})
#     )
#     # technolog = forms.CharField(label='Технолог', required=False,
#     #                            widget=forms.Select(choices=technologs, attrs={'class': 'form-control'}))
#     group = forms.CharField(label='Группа', required=False,
#                             widget=forms.Select(choices=groups, attrs={'class': 'form-control'}),
#                             )
#     status = forms.CharField(label='Статус', required=False,
#                              widget=forms.Select(choices=statuses, attrs={'class': 'form-control'}),
#                              )
#                                #widget=forms.TextInput(attrs={'class': 'form-control'}))
