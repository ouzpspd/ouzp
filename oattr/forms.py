from django import forms
from django.core.validators import RegexValidator

from django.db import transaction

from .models import HoldPosition, UserHoldPosition, OtpmSpp
from django.contrib.auth.forms import UserCreationForm, AuthenticationForm
from django.contrib.auth.models import User, Group

class UserLoginForm(AuthenticationForm):
    username = forms.CharField(label='Логин', widget=forms.TextInput(attrs={'class': 'form-control'}))
    password = forms.CharField(label='Пароль', widget=forms.PasswordInput(attrs={'class': 'form-control'}))


class UserRegistrationForm(UserCreationForm):
    alphanumeric = RegexValidator(r'^[0-9a-zA-Z.]*$', 'Не использовать русские символы.')
    username = forms.CharField(label='Логин',
                               widget=forms.TextInput(attrs={'class': 'form-control'}),
                               validators=[alphanumeric])
    last_name = forms.CharField(label='ФИО',
                                widget=forms.TextInput(attrs={'class': 'form-control'}),
                                help_text='Строго с пробелами как в СПП'
                                )
    hold_position = forms.ModelChoiceField(
        label='Должность',
        queryset=HoldPosition.objects.all(),
        required=True,
        to_field_name='name',
        widget=forms.Select(attrs={'class': 'form-control'})
    )
    password1 = forms.CharField(label='Пароль',
                                widget=forms.PasswordInput(attrs={'class': 'form-control'}),
                                )
    password2 = forms.CharField(label='Подтверждение пароля',
                                widget=forms.PasswordInput(attrs={'class': 'form-control'}),
                                )

    class Meta:
        model = User
        fields = ('username', 'last_name', 'hold_position', 'password1', 'password2')

    @transaction.atomic
    def save(self):
        user = super().save(commit=False)
        user.save()
        UserHoldPosition.objects.create(user=user, hold_position=self.cleaned_data.get('hold_position'))
        if 'Техник-технолог ОАТТР' in str(self.cleaned_data.get('hold_position')):
            oattr_group = Group.objects.get(name='Сотрудники ОАТТР')
            oattr_group.user_set.add(user)
        elif 'Инженер-технолог ОУЗП СПД' in str(self.cleaned_data.get('hold_position')):
            ouzp_group = Group.objects.get(name='Сотрудники ОУЗП')
            ouzp_group.user_set.add(user)
        elif 'Менеджер' in str(self.cleaned_data.get('hold_position')):
            mko_group = Group.objects.get(name='Менеджеры')
            mko_group.user_set.add(user)
        elif 'Инженер-технолог ОУПМ СПД' in str(self.cleaned_data.get('hold_position')):
            oupm_group = Group.objects.get(name='Сотрудники ОУПМ')
            oupm_group.user_set.add(user)
        user.save()
        return user


class AuthForServiceForm(forms.Form):
    username = forms.CharField(label='Имя пользователя', widget=forms.TextInput(attrs={'class': 'form-control'}))
    password = forms.CharField(label='Пароль', widget=forms.PasswordInput(attrs={'class': 'form-control'}))


class TechnologModelChoiceField(forms.ModelChoiceField):
    """По умолчанию в ModelChoiceField используется поле, которое возвращает метод __str__, поэтому меняем
     на нужное поле"""
    def label_from_instance(self, obj):
        return obj.last_name


class OtpmPoolForm(forms.Form):
    groups = [
        ('Все', 'Все'),
        ('Коммерческая', 'Коммерческая'),
        ('ПТО', 'ПТО'),
    ]
    statuses = [
        ('Все', 'Все'),
        ('В работе', 'В работе'),
        ('Не взята в работу', 'Не взята в работу'),
        ('Отслеживается', 'Отслеживается'),
    ]
    # technologs = [
    #     ('Все', 'Все'),
    # ]
    technolog = TechnologModelChoiceField(
        queryset=User.objects.all(),
        empty_label='Все',
        required=False,
        to_field_name='last_name',
        widget=forms.Select(attrs={'class': 'form-control'})
    )
    # technolog = forms.CharField(label='Технолог', required=False,
    #                            widget=forms.Select(choices=technologs, attrs={'class': 'form-control'}))
    group = forms.CharField(label='Группа', required=False,
                            widget=forms.Select(choices=groups, attrs={'class': 'form-control'}),
                            )
    status = forms.CharField(label='Статус', required=False,
                             widget=forms.Select(choices=statuses, attrs={'class': 'form-control'}),
                             )
                               #widget=forms.TextInput(attrs={'class': 'form-control'}))


class CopperForm(forms.Form):
    types_cable = [
        ('UTP-2е пары', 'UTP-2е пары'),
        ('UTP-4е пары', 'UTP-4е пары'),
    ]
    count_0 = forms.CharField(label='Количество линий', widget=forms.TextInput(attrs={'class': 'form-control'}))
    from_0 = forms.CharField(widget=forms.Textarea(attrs={'class': 'form-control',
                                                                          'rows':2}))
    to_0 = forms.CharField(widget=forms.Textarea(attrs={'class': 'form-control',
                                                                          'rows':2}))
    cable_0 = forms.CharField(widget=forms.Select(choices=types_cable, attrs={'class': 'form-control'}))
    mounting_0 = forms.CharField(widget=forms.Textarea(attrs={'class': 'form-control mounting',
                                                                          'rows':2}))
    fastening_0 = forms.CharField(widget=forms.Textarea(attrs={'class': 'form-control fastening',
                                                                          'rows':2}))
    no_exit = forms.BooleanField(label='ТР написано без выезда',
                                 required=False,
                                 widget=forms.CheckboxInput(attrs={'class': 'form-check'}))
    tech_reserve = forms.BooleanField(label='Тех. запас',
                                 required=False,
                                 widget=forms.CheckboxInput(attrs={'class': 'form-check'}))
    line_test = forms.BooleanField(label='Теcт линии связи',
                                 required=False,
                                 widget=forms.CheckboxInput(attrs={'class': 'form-check'}))
    equipment = forms.CharField(label='Монтаж оборудования', required=False,
                                widget=forms.Textarea(attrs={'class': 'form-control', 'rows': 3}))
    access = forms.CharField(label='Доступ', widget=forms.Textarea(attrs={'class': 'form-control',
                                                                          'rows':3}))
    agreement = forms.CharField(label='Согласование', required=False,
                                widget=forms.Textarea(attrs={'class': 'form-control', 'rows':3}))

    def __init__(self, *args, **kwargs):
        super(CopperForm, self).__init__(*args, **kwargs)
        if kwargs.get('data'):
            # for view func-based fields locate in args
            new_fields = set(kwargs['data'].keys()) - set(self.fields.keys())
            new_fields.remove('csrfmiddlewaretoken')

            for field in new_fields:
                self.fields[f'{field}'] = forms.CharField()


class ServiceForm(forms.Form):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if kwargs.get('data'):
            # for view func-based fields locate in args
            new_fields = set(kwargs['data'].keys())
            new_fields.remove('csrfmiddlewaretoken')

            for field in new_fields:
                self.fields[f'{field}'] = forms.CharField()



class OattrForm(forms.Form):
    oattr_field = forms.CharField(label='Решение ОРТР', widget=forms.Textarea(attrs={'class': 'form-control'}))
    # pps = forms.CharField(label='ППС', required=False, widget=forms.TextInput(attrs={'class': 'form-control'}))
    # kad = forms.CharField(label='КАД', required=False, widget=forms.TextInput(attrs={'class': 'form-control'}))
    # ots_field = forms.CharField(label='Решение ОТС', required=False, widget=forms.Textarea(attrs={'class': 'form-control'}))


class SendSPPForm(forms.Form):
    send_to = forms.CharField(widget=forms.Select(attrs={'class': 'form-control'}))
    comment = forms.CharField(label='Добавить комментарий', required=False, widget=forms.Textarea(attrs={'class': 'form-control'}))



class AddressForm(forms.Form):
    cities = [
        ('0', 'Все'),
        ('Екатеринбург', 'Екатеринбург'),
        ('Нижний Тагил', 'Нижний Тагил'),
        ('Каменск-Уральский', 'Каменск-Уральский'),
    ]
    city = forms.CharField(label='Город', widget=forms.Select(choices=cities, attrs={'class': 'form-control'}))
    street = forms.CharField(label='Улица', required=False, widget=forms.TextInput(attrs={'class': 'form-control'}))
    house = forms.CharField(label='Дом', required=False, widget=forms.TextInput(attrs={'class': 'form-control'}))

