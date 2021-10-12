from django import forms
from .models import TR, SPP, ServicesTR
from django.contrib.auth.forms import UserCreationForm, AuthenticationForm
from django.contrib.auth.models import User


class UserLoginForm(AuthenticationForm):
    username = forms.CharField(label='Логин', widget=forms.TextInput(attrs={'class': 'form-control'}))
    password = forms.CharField(label='Пароль', widget=forms.PasswordInput(attrs={'class': 'form-control'}))


class UserRegistrationForm(UserCreationForm):
    username = forms.CharField(label='Логин', widget=forms.TextInput(attrs={'class': 'form-control'}))
    last_name = forms.CharField(label='Фамилия', widget=forms.TextInput(attrs={'class': 'form-control'}))
    password1 = forms.CharField(label='Пароль', widget=forms.PasswordInput(attrs={'class': 'form-control'}))
    password2 = forms.CharField(label='Подтверждение пароля', widget=forms.PasswordInput(attrs={'class': 'form-control'}))

    class Meta:
        model = User
        fields = ('username', 'last_name', 'password1', 'password2')


class AuthForServiceForm(forms.Form):
    username = forms.CharField(label='Имя пользователя', widget=forms.TextInput(attrs={'class': 'form-control'}))
    password = forms.CharField(label='Пароль', widget=forms.PasswordInput(attrs={'class': 'form-control'}))


class SPPForm(forms.ModelForm):
    class Meta:
        model = SPP
        fields = '__all__'


class TrForm(forms.ModelForm):
    class Meta:
        model = TR
        fields = ('ticket_k', 'ticket_tr')



class ServiceForm(forms.ModelForm):
    class Meta:
        model = ServicesTR
        fields = '__all__'



class PortForm(forms.Form):
    kad = forms.CharField(max_length=100, label='Коммутатор')
    model = forms.CharField(max_length=100, label='Модель')


class OrtrForm(forms.Form):
    ortr_field = forms.CharField(label='Решение ОРТР', widget=forms.Textarea(attrs={'class': 'form-control'}))
    pps = forms.CharField(label='ППС', required=False, widget=forms.TextInput(attrs={'class': 'form-control'}))
    kad = forms.CharField(label='КАД', required=False, widget=forms.TextInput(attrs={'class': 'form-control'}))
    ots_field = forms.CharField(label='Решение ОТС', required=False, widget=forms.Textarea(attrs={'class': 'form-control'}))

class LinkForm(forms.Form):
    spplink =forms.CharField(max_length=150, label='Ссылка на ТР', widget=forms.TextInput(attrs={'class': 'form-control'}))

class LocalForm(forms.Form):
    types = [('СКС', 'СКС'), ('ЛВС', 'ЛВС')]
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
    hotspot_points = forms.IntegerField(max_value=10, required=False, label='Количество точек', widget=forms.NumberInput(attrs={'class': 'form-control'}))
    hotspot_users = forms.IntegerField(max_value=1000, label='Количество пользователей', widget=forms.NumberInput(attrs={'class': 'form-control'}))

class PhoneForm(forms.Form):
    types = [('ak', 'Аналог, установка шлюза у клиента'), ('ap', 'Аналог, установка шлюза на ППС'), ('ab', 'Аналог, установка шлюза не требуется'), ('s', 'SIP, по логину/паролю'),]
    type_phone = forms.CharField(label='Тип телефонии', widget=forms.Select(choices=types, attrs={'class': 'form-control'}))
    types_vgw = [('Eltex TAU-2M.IP', 'Eltex TAU-2M.IP'), ('Eltex RG-1404G или Eltex TAU-4M.IP', 'Eltex TAU-4M.IP'),
                 ('Eltex TAU-8.IP', 'Eltex TAU-8.IP'), ('Eltex TAU-16.IP', 'Eltex TAU-16.IP'), ('Eltex TAU-24.IP', 'Eltex TAU-24.IP'),
                 ('Eltex TAU-36.IP', 'Eltex TAU-36.IP'), ('Eltex TAU-72.IP', 'Eltex TAU-72.IP'), ('Не требуется', 'Не требуется')]
    vgw = forms.CharField(label='Шлюз', widget=forms.Select(choices=types_vgw, attrs={'class': 'form-control'}))
    channel_vgw = forms.CharField(max_length=11, label='Количество каналов', widget=forms.TextInput(attrs={'class': 'form-control'}))
    ports_vgw = forms.CharField(max_length=11, required=False, label='Количество портов', widget=forms.TextInput(attrs={'class': 'form-control'}))

class ItvForm(forms.Form):
    types = [('vl', 'В отдельном vlan'), ('novl', 'В vlan услуги ШПД'),]
    type_itv = forms.CharField(label='Тип ITV', widget=forms.Select(choices=types, attrs={'class': 'form-control'}))
    cnt_itv = forms.IntegerField(max_value=20, label='Количество приставок',
                                        widget=forms.NumberInput(attrs={'class': 'form-control'}))


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
    device_pps = forms.CharField(label='На стороне ППС', widget=forms.Select(choices=types, attrs={'class': 'form-control'}))
    device_client = forms.CharField(label='На стороне клиента', widget=forms.Select(choices=types, attrs={'class': 'form-control'}))
    kad = forms.CharField(label='Коммутатор', widget=forms.TextInput(attrs={'class': 'form-control'}))
    speed_port = forms.CharField(label='Скорость порта', widget=forms.Select(choices=speed, attrs={'class': 'form-control'}))
    port = forms.CharField(label='Порт', widget=forms.TextInput(attrs={'class': 'form-control'}))
    ppr = forms.CharField(label='ППР', required=False, widget=forms.TextInput(attrs={'class': 'form-control'}))
    logic_csw = forms.BooleanField(label='Установка КК', required=False, widget=forms.CheckboxInput(attrs={'class': 'form-check'}))
    logic_replace_csw = forms.BooleanField(label='Замена КК', required=False,
                                           widget=forms.CheckboxInput(attrs={'class': 'form-check'}))
    logic_change_gi_csw = forms.BooleanField(label='Перевод КК на 1G', required=False,
                                              widget=forms.CheckboxInput(attrs={'class': 'form-check'}))


class CopperForm(forms.Form):
    kad = forms.CharField(label='Коммутатор', widget=forms.TextInput(attrs={'class': 'form-control'}))
    port = forms.CharField(label='Порт', widget=forms.TextInput(attrs={'class': 'form-control'}))
    logic_csw = forms.BooleanField(label='Установка КК', required=False, widget=forms.CheckboxInput(attrs={'class': 'form-check'}))
    logic_replace_csw = forms.BooleanField(label='Замена КК', required=False,
                                   widget=forms.CheckboxInput(attrs={'class': 'form-check'}))
    logic_change_gi_csw = forms.BooleanField(label='Перевод КК на 1G', required=False,
                                   widget=forms.CheckboxInput(attrs={'class': 'form-check'}))

class WirelessForm(forms.Form):
    ap_types = [('AirGrid 23 M5 или LiteBeam LBE-M5-23', 'LiteBeam LBE-M5-23'),
             ('AirGrid 27 M5', 'AirGrid 27 M5'),
             ('Nanostation M5', 'Nanostation M5'),
             ('Infinet H11', 'Infinet H11')]
    access_point = forms.CharField(label='Точки доступа', widget=forms.Select(choices=ap_types, attrs={'class': 'form-control'}))
    kad = forms.CharField(label='Коммутатор', widget=forms.TextInput(attrs={'class': 'form-control'}))
    port = forms.CharField(label='Порт', widget=forms.TextInput(attrs={'class': 'form-control'}))
    ppr = forms.CharField(label='ППР', required=False, widget=forms.TextInput(attrs={'class': 'form-control'}))
    logic_csw = forms.BooleanField(label='Установка КК', required=False, widget=forms.CheckboxInput(attrs={'class': 'form-check'}))
    logic_replace_csw = forms.BooleanField(label='Замена КК', required=False,
                                           widget=forms.CheckboxInput(attrs={'class': 'form-check'}))
    logic_change_gi_csw = forms.BooleanField(label='Перевод КК на 1G', required=False,
                                              widget=forms.CheckboxInput(attrs={'class': 'form-check'}))


class CswForm(forms.Form):
    types_csw = [('D-Link DGS-1100-06/ME', 'D-Link DGS-1100-06/ME'), ('24-портовый коммутатор', '24-портовый коммутатор')]
    types_port = [('5', '5'), ('6', '6'), ('указанный ОНИТС СПД', 'указанный ОНИТС СПД')]
    types_speed_csw = [('Нет', 'Нет'), ('100', '100'), ('1000', '1000')]
    logic_csw_1000 = forms.BooleanField(label='Запуск КК на магистрали 1 Гбит/с', required=False, widget=forms.CheckboxInput(attrs={'class': 'form-check'}))
    exist_speed_csw = forms.CharField(label='Существующая магистраль', widget=forms.Select(choices=types_speed_csw, attrs={'class': 'form-control'}))
    model_csw = forms.CharField(label='Модель', widget=forms.Select(choices=types_csw, attrs={'class': 'form-control'}))
    port_csw = forms.CharField(label='Порт', widget=forms.Select(choices=types_port, attrs={'class': 'form-control'}))

class ShpdForm(forms.Form):
    router = forms.BooleanField(label='Маршрутизатор', required=False, widget=forms.CheckboxInput(attrs={'class': 'form-check'}))
    types = [('access', 'access'), ('trunk', 'trunk')]
    type_shpd = forms.CharField(label='Режим порта',
                                 widget=forms.Select(choices=types, attrs={'class': 'form-control'}))

class CksForm(forms.Form):
    pointA = forms.CharField(label='Точка A', widget=forms.TextInput(attrs={'class': 'form-control'}))
    pointB = forms.CharField(label='Точка B', widget=forms.TextInput(attrs={'class': 'form-control'}))
    type_police = [('полисером Subinterface', 'полисером Subinterface'), ('портом подключения', 'портом подключения'), ('не требуется', 'не требуется')]
    policer_cks = forms.CharField(label='Ограничение', widget=forms.Select(choices=type_police, attrs={'class': 'form-control'}))
    types = [('access', 'access'), ('trunk', 'trunk')]
    type_cks = forms.CharField(label='Режим порта',
                           widget=forms.Select(choices=types, attrs={'class': 'form-control'}))

class PortVKForm(forms.Form):
    new_vk = forms.BooleanField(label='Новая ВЛС', required=False, widget=forms.CheckboxInput(attrs={'class': 'form-check'}))
    exist_vk = forms.CharField(label='Cуществующая ВЛС', required=False, widget=forms.TextInput(attrs={'class': 'form-control'}))
    type_police = [('полисером на Subinterface', 'полисером на Subinterface'), ('на порту подключения', 'на порту подключения'), ('не требуется', 'не требуется')]
    policer_vk = forms.CharField(label='Ограничение', widget=forms.Select(choices=type_police, attrs={'class': 'form-control'}))
    types = [('access', 'access'), ('trunk', 'trunk')]
    type_portvk = forms.CharField(label='Режим порта',
                               widget=forms.Select(choices=types, attrs={'class': 'form-control'}))

class PortVMForm(forms.Form):
    new_vm = forms.BooleanField(label='Новый ВМ', required=False, widget=forms.CheckboxInput(attrs={'class': 'form-check'}))
    exist_vm = forms.CharField(label='Cуществующий ВМ', required=False, widget=forms.TextInput(attrs={'class': 'form-control'}))
    type_police = [('полисером на SVI', 'полисером на SVI'), ('на порту подключения', 'на порту подключения'), ('не требуется', 'не требуется')]
    policer_vm = forms.CharField(label='Ограничение', widget=forms.Select(choices=type_police, attrs={'class': 'form-control'}))
    vm_inet = forms.BooleanField(required=False, label='С доступом в Интернет', widget=forms.CheckboxInput(attrs={'class': 'form-check'}))
    types = [('access', 'access'), ('trunk', 'trunk')]
    type_portvm = forms.CharField(label='Режим порта',
                               widget=forms.Select(choices=types, attrs={'class': 'form-control'}))

class VideoForm(forms.Form):
    camera_number = forms.IntegerField(max_value=9, label='Количество камер',
                                       widget=forms.NumberInput(attrs={'class': 'form-control'}))
    camera_model = forms.CharField(label='Модель камеры', widget=forms.TextInput(attrs={'class': 'form-control'}))
    voice = forms.BooleanField(label='Запись звука', required=False, widget=forms.CheckboxInput(attrs={'class': 'form-check'}))
    type_deep_archive = [('0', '0'), ('3', '3'), ('7', '7'), ('15', '15'), ('30', '30')]
    deep_archive = forms.CharField(label='Глубина архива камеры', widget=forms.Select(choices=type_deep_archive, attrs={'class': 'form-control'}))
    camera_place_one = forms.CharField(label='Место установки Камеры №1', required=False, widget=forms.TextInput(attrs={'class': 'form-control'}), help_text='только если 1 или 2 камеры')
    camera_place_two = forms.CharField(label='Место установки Камеры №2', required=False, widget=forms.TextInput(attrs={'class': 'form-control'}), help_text='только если 1 или 2 камеры')


class ContractForm(forms.Form):
    contract =forms.CharField(max_length=150, label='Договор', widget=forms.TextInput(attrs={'class': 'form-control'}))

class ChainForm(forms.Form):
    chain_device =forms.CharField(max_length=150, label='Девайс', widget=forms.TextInput(attrs={'class': 'form-control'}))

class ListResourcesForm(forms.Form):
    resource = forms.BooleanField(label="", required=False, widget=forms.CheckboxInput(attrs={'class': 'form-check'}))

class ListJobsForm(forms.Form):
    types = [
        ('Организация/Изменение, СПД', 'Организация/Изменение, СПД'),
        ('Организация, не СПД', 'Организация, не СПД'),
        ('Изменение, не СПД', 'Изменение, не СПД'),
        ('Перенос, СПД', 'Перенос, СПД'),
        ('Не требуется', 'Не требуется'),
    ]
    jobs = forms.CharField(label='',
                                 widget=forms.Select(choices=types, attrs={'class': 'form-control'}))


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
        ('Перенос логического подключения', 'Перенос логического подключения'),
        ('Перевод на гигабит', 'Перевод на гигабит'),
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
    change_log_shpd = forms.CharField(label='Изменение схемы ШПД',
                                      widget=forms.Select(choices=types_change_log_shpd,
                                                          attrs={'class': 'form-control'}))

class AddServInstCswForm(forms.Form):
    types = [('Медная линия и порт не меняются', 'Медная линия и порт не меняются'),
             ('ВОЛС и порт не меняются', 'ВОЛС и порт не меняются'),
             ('Перевод на гигабит переключение с меди на ВОЛС', 'Перевод на гигабит переключение с меди на ВОЛС'),
             ('Перевод на гигабит по меди на текущем узле', 'Перевод на гигабит по меди на текущем узле'),
             ('Перевод на гигабит по ВОЛС на текущем узле', 'Перевод на гигабит по ВОЛС на текущем узле'),
             ('Перевод на гигабит/перенос на новый узел', 'Перевод на гигабит/перенос на новый узел')]
    type_install_csw = forms.CharField(label='Варианты установки КК', widget=forms.Select(choices=types, attrs={'class': 'form-control'}))


class ChangeServForm(forms.Form):
    types = [("Организация ШПД trunk'ом", "Организация ШПД trunk'ом"),
             ("Организация ШПД trunk'ом с простоем", "Организация ШПД trunk'ом с простоем"),
             ("Изменение cхемы организации ШПД", "Изменение cхемы организации ШПД"),
             ("Замена connected на connected", "Замена connected на connected"),
             ("Организация доп connected.", "Организация доп connected"),
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
    new_mask = forms.IntegerField(max_value=32, required=False, label='Количество камер',
                                       widget=forms.NumberInput(attrs={'class': 'form-control'}))
    types_port = [("access'ом (native vlan)", "access'ом (native vlan)"), ("trunk", "trunk"), ("в неизменном виде", "в неизменном виде")]
    change_type_port_exist_serv = forms.CharField(required=False, label='Режим порта существующей услуги',
                                 widget=forms.Select(choices=types_port, attrs={'class': 'form-control'}))
    change_type_port_new_serv = forms.CharField(required=False, label='Режим порта новой услуги',
                                           widget=forms.Select(choices=types_port, attrs={'class': 'form-control'}))
    routed_ip = forms.CharField(max_length=20, required=False, label='Ip-адрес', widget=forms.TextInput(attrs={'class': 'form-control'}))
    routed_vrf = forms.CharField(max_length=50, required=False, label='VRF', widget=forms.TextInput(attrs={'class': 'form-control'}))