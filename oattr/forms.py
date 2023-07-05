from django import forms
from django.contrib.auth.models import User


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
    from_0 = forms.CharField(widget=forms.TextInput(attrs={'class': 'form-control'}))
    to_0 = forms.CharField(widget=forms.TextInput(attrs={'class': 'form-control'}))
    cable_0 = forms.CharField(widget=forms.Select(choices=types_cable, attrs={'class': 'form-control'}))
    mounting_0 = forms.CharField(widget=forms.TextInput(attrs={'class': 'form-control mounting'}))
    fastening_0 = forms.CharField(widget=forms.TextInput(attrs={'class': 'form-control fastening'}))
    no_exit = forms.BooleanField(label='ТР написано без выезда',
                                 required=False,
                                 widget=forms.CheckboxInput(attrs={'class': 'form-check'}))
    tech_reserve = forms.BooleanField(label='Тех. запас',
                                 required=False,
                                 widget=forms.CheckboxInput(attrs={'class': 'form-check'}))
    line_test = forms.BooleanField(label='Теcт линии связи',
                                 required=False,
                                 widget=forms.CheckboxInput(attrs={'class': 'form-check'}))
    access = forms.CharField(label='Доступ', widget=forms.Textarea(attrs={'class': 'form-control',
                                                                          'rows':3}))
    agreement = forms.CharField(label='Согласование', widget=forms.Textarea(attrs={'class': 'form-control',
                                                                                   'rows':3}))

    def __init__(self, *args, **kwargs):
        super(CopperForm, self).__init__(*args, **kwargs)
        if args:
            new_fields = set(args[0].keys()) - set(self.fields.keys())
            new_fields.remove('csrfmiddlewaretoken')

            for field in new_fields:
                self.fields[f'{field}'] = forms.CharField()
