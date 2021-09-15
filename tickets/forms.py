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
    exist_client = forms.BooleanField(label='Существующий клиент', required=False, widget=forms.CheckboxInput(attrs={'class': 'form-check'}))
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
    speed_port = forms.CharField(label='Скорость порта', widget=forms.Select(choices=speed, attrs={'class': 'form-control'}))
    port = forms.CharField(label='Порт', widget=forms.TextInput(attrs={'class': 'form-control'}))
    ppr = forms.CharField(label='ППР', required=False, widget=forms.TextInput(attrs={'class': 'form-control'}))
    logic_csw = forms.BooleanField(label='Установка КК', required=False, widget=forms.CheckboxInput(attrs={'class': 'form-check'}))


class CopperForm(forms.Form):
    port = forms.CharField(label='Порт', widget=forms.TextInput(attrs={'class': 'form-control'}))
    logic_csw = forms.BooleanField(label='Установка КК', required=False, widget=forms.CheckboxInput(attrs={'class': 'form-check'}))

class WirelessForm(forms.Form):
    ap_types = [('AirGrid 23 M5 или LiteBeam LBE-M5-23', 'LiteBeam LBE-M5-23'),
             ('AirGrid 27 M5', 'AirGrid 27 M5'),
             ('Nanostation M5', 'Nanostation M5'),
             ('Infinet H11', 'Infinet H11')]
    access_point = forms.CharField(label='Точки доступа', widget=forms.Select(choices=ap_types, attrs={'class': 'form-control'}))
    port = forms.CharField(label='Порт', widget=forms.TextInput(attrs={'class': 'form-control'}))
    ppr = forms.CharField(label='ППР', required=False, widget=forms.TextInput(attrs={'class': 'form-control'}))
    logic_csw = forms.BooleanField(label='Установка КК', required=False, widget=forms.CheckboxInput(attrs={'class': 'form-check'}))


class CswForm(forms.Form):
    types_csw = [('D-Link DGS-1100-06/ME', 'D-Link DGS-1100-06/ME'), ('24-портовый коммутатор', '24-портовый коммутатор')]
    types_port = [('5', '5'), ('6', '6'), ('указанный ОНИТС СПД', 'указанный ОНИТС СПД')]
    logic_csw_1000 = forms.BooleanField(label='Запуск КК на магистрали 1 Гбит/с', required=False, widget=forms.CheckboxInput(attrs={'class': 'form-check'}))
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


class PassForm(forms.Form):
    #router = forms.BooleanField(label='Маршрутизатор', required=False, widget=forms.CheckboxInput(attrs={'class': 'form-check'}))
    types = [
        ('Перенос сервиса', 'Перенос сервиса'),
        ('Перенос сервиса "ШПД в Интернет" с изменением реквизитов', 'Перенос сервиса "ШПД в Интернет" с изменением реквизитов')
    ]
    type_pass = forms.CharField(label='Выбор работ',
                                 widget=forms.Select(choices=types, attrs={'class': 'form-control'}))


class PassServForm(forms.Form):
    log_change = forms.BooleanField(label='Логическое подключение изменится?', required=False,
                                    widget=forms.CheckboxInput(attrs={'class': 'form-check'}))
    from_node = forms.BooleanField(label='Монтажные работы от узла связи?', required=False,
                                      widget=forms.CheckboxInput(attrs={'class': 'form-check'}))
