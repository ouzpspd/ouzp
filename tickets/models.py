from django.db import models
from django.contrib.auth.models import User

# Create your models here.

class SPP(models.Model):
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
    version = models.IntegerField(verbose_name='Версия')
    created = models.DateTimeField(auto_now_add=True)
    complited = models.DateTimeField(auto_now=True)
    process = models.BooleanField(default=False, verbose_name='В работе')
    wait = models.BooleanField(default=False, verbose_name='В ожидании')
    was_waiting = models.BooleanField(default=False, verbose_name='Была в ожидании')
    user = models.ForeignKey(User, on_delete=models.PROTECT)
    return_otpm = models.BooleanField(default=False, verbose_name='Возвращена в ОТПМ')
    return_mko = models.BooleanField(default=False, verbose_name='Возвращена МКО')
    projected = models.BooleanField(default=True, verbose_name='Спроектирована')
    simplified_tr = models.BooleanField(default=False, verbose_name='Упрощенное ТР')
    evaluative_tr = models.BooleanField(default=False, verbose_name='Оценочное ТР')
    uID = models.CharField(max_length=10, verbose_name='ID куратора', null=True, blank=True)
    trdifperiod = models.CharField(max_length=10, verbose_name='Сложность в часах', null=True, blank=True)
    trcuratorphone = models.CharField(max_length=15, verbose_name='Телефон куратора', null=True, blank=True)

    def __str__(self):
        return self.ticket_k


class TR(models.Model):
    ticket_k = models.ForeignKey(SPP, on_delete=models.CASCADE, related_name='children')
    ticket_tr = models.CharField(max_length=100, verbose_name='ТР')
    pps = models.CharField(max_length=200, verbose_name='ППС')
    turnoff = models.BooleanField(default=False, verbose_name='Отключение')
    info_tr = models.TextField(verbose_name='Инфо для разработки', blank=True, null=True)
    oattr = models.TextField(verbose_name='Решение ОТПМ', blank=True, null=True)
    services = models.JSONField(verbose_name='Перечень требуемых услуг')
    connection_point = models.CharField(default='Неизвестно', max_length=400, verbose_name='Точка подключения')
    kad = models.CharField(max_length=400, verbose_name='КАД')
    vID = models.IntegerField()

    def __str__(self):
        return self.ticket_tr


class ServicesTR(models.Model):
    ticket_tr = models.ForeignKey(TR, on_delete=models.CASCADE)
    service = models.CharField(max_length=200, verbose_name='Услуга')

    def __str__(self):
        return self.service

class OrtrTR(models.Model):
    ticket_tr = models.ForeignKey(TR, on_delete=models.CASCADE)
    ortr = models.TextField(verbose_name='Решение ОРТР')
    ots = models.TextField(verbose_name='Решение ОТС',  null=True, blank=True)
    titles = models.TextField(verbose_name='Заголовки ТР', null=True, blank=True)

    def __str__(self):
        return self.ortr
