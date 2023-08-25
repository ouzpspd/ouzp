from django.contrib.auth.models import User
from django.db import models

class OtpmSpp(models.Model):
    dID = models.CharField(max_length=10)
    ticket_k = models.CharField(max_length=15, verbose_name='Заявка К')
    client = models.CharField(max_length=200, verbose_name='Клиент')
    type_ticket = models.CharField(max_length=20, verbose_name='Тип заявки')
    manager = models.CharField(max_length=100, verbose_name='Менеджер')
    technolog = models.CharField(max_length=100, verbose_name='Технолог')
    task_otpm = models.TextField(verbose_name='Задача в ОТПМ')
    services = models.JSONField(verbose_name='Перечень требуемых услуг')
    des_tr = models.JSONField(verbose_name='Состав Заявки ТР')
    comment = models.TextField(verbose_name='Примечание')
    created = models.DateTimeField()#auto_now=True) # auto_now_add=True
    waited = models.DateTimeField()
    duration_process = models.DurationField()
    duration_wait = models.DurationField()
    process = models.BooleanField(default=False, verbose_name='В работе')
    wait = models.BooleanField(default=False, verbose_name='В ожидании')
    user = models.ForeignKey(User, on_delete=models.PROTECT)
    projected = models.BooleanField(default=False, verbose_name='Спроектирована')
    difficulty = models.CharField(max_length=10, verbose_name='Сложность')
    uID = models.CharField(max_length=10, verbose_name='ID куратора', null=True, blank=True)
    trdifperiod = models.CharField(max_length=10, verbose_name='Сложность в часах', null=True, blank=True)
    trcuratorphone = models.CharField(max_length=15, verbose_name='Телефон куратора', null=True, blank=True)
    stage = models.CharField(max_length=100, verbose_name='Cтатус заявки СПП')

    def __str__(self):
        return self.ticket_k

    def evaluate_completed(self):
        return self.duration_process + self.created

class OtpmTR(models.Model):
    ticket_k = models.ForeignKey('OtpmSpp', on_delete=models.CASCADE, related_name='children')
    ticket_tr = models.CharField(max_length=100, verbose_name='ТР')
    pps = models.CharField(max_length=200, verbose_name='ППС')
    info_tr = models.TextField(verbose_name='Инфо для разработки', blank=True, null=True)
    services = models.JSONField(verbose_name='Перечень требуемых услуг')
    address_cp = models.CharField(max_length=400, verbose_name='Адрес точки подключения')
    place_cp = models.CharField(max_length=400, verbose_name='Место точки подключения', blank=True, null=True)
    vID = models.IntegerField()
    ticket_cp = models.CharField(max_length=10, verbose_name='Точка подключения')
    oattr = models.TextField(verbose_name='Решение ОТПМ')
    titles = models.TextField(verbose_name='Заголовки ТР', null=True, blank=True)
    aid = models.CharField(max_length=10, verbose_name='ID адреса точки подключения')
    tr_without_os = models.BooleanField(default=False, verbose_name='Участие ОС не требуется')
    tr_complex_access = models.BooleanField(default=False, verbose_name='Сложный доступ')
    tr_complex_equip = models.BooleanField(default=False, verbose_name='Нестандартное оборудование')
    tr_turn_off = models.BooleanField(default=False, verbose_name='Отключение')
    tr_complex_access_input = models.TextField(verbose_name='Сложный доступ текст', blank=True, null=True)
    tr_complex_equip_input = models.TextField(verbose_name='Нестандартное оборудование текст', blank=True, null=True)
    tr_turn_off_input = models.TextField(verbose_name='Отключение текст', blank=True, null=True)

    def __str__(self):
        return self.ticket_tr


class HoldPosition(models.Model):
    """Должность сотрудника"""
    name = models.CharField(max_length=200, verbose_name='Название должности')

    def __str__(self):
        return self.name

class UserHoldPosition(models.Model):
    """Модель добавляющая пользователю поле должность"""
    user = models.OneToOneField(User, on_delete=models.CASCADE, primary_key=True)
    hold_position = models.ForeignKey(HoldPosition, on_delete=models.CASCADE, verbose_name='Должность')

    def __str__(self):
        return self.hold_position.name

