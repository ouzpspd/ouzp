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
    evaluative_tr = models.BooleanField(default=False, verbose_name='Оценочное ТР')
    uID = models.CharField(max_length=10, verbose_name='ID куратора', null=True, blank=True)
    trdifperiod = models.CharField(max_length=10, verbose_name='Сложность в часах', null=True, blank=True)
    trcuratorphone = models.CharField(max_length=15, verbose_name='Телефон куратора', null=True, blank=True)
    stage = models.CharField(max_length=100, verbose_name='Cтатус заявки СПП')

    def __str__(self):
        return self.ticket_k

    # def evaluate_duration(self):
    #     return self.complited - self.created
