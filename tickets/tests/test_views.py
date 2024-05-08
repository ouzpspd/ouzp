from bs4 import BeautifulSoup
from django.contrib.auth import get_user_model
from django.test import TestCase
from http import HTTPStatus

import os
import datetime
from pathlib import Path

from django.urls import reverse
from django.utils import timezone
from dotenv import load_dotenv
from tickets.models import SPP, TR
from oattr.models import HoldPosition, UserHoldPosition
from django.contrib.auth.models import Group

BASE_DIR = Path(__file__).resolve().parent.parent
dotenv_path = os.path.join(BASE_DIR, '.env')
load_dotenv(dotenv_path)
TEST_CORDIS_USER = os.getenv('TEST_CORDIS_USER')
TEST_CORDIS_PASSWORD = os.getenv('TEST_CORDIS_PASSWORD')


class OuzpViewsTestCase(TestCase):
    DID = '141891'
    TID = '211509'
    TRID = '72459'
    PPS = 'БЗК Березовский тракт 5 П1 Э3 (Лестничная клетка), АВ'
    def setUp(self):
        hold_position = HoldPosition.objects.create(name='Инженер-технолог ОУЗП СПД')
        User = get_user_model()
        user = User.objects.create_user('temporary', 'temporary@gmail.com', 'temporary', last_name='Бискинский Е.В.')
        UserHoldPosition.objects.create(user=user, hold_position=hold_position)
        group = Group.objects.create(name='Сотрудники ОУЗП')
        group.user_set.add(user)

        self.spp = SPP.objects.create(user=user, dID='123456', services={}, des_tr={}, created=timezone.now(),
                                          complited=timezone.now(), version=1,
                                          ticket_k='2023_00000', process = True,
                                          )
        self.tr = TR.objects.create(ticket_k=self.spp, ticket_tr=self.TRID, services={}, vID=1,
                                    pps=self.PPS
                                               )
        self.client.login(username='temporary', password='temporary')
        self.sess = {'ticket_spp_id': self.tr.ticket_k.id, 'ticket_tr_id': self.tr.id, 'dID': '123456',
                'technical_solution': self.TRID,
                     }

        session = self.client.session
        session[self.TRID] = self.sess
        session.save()

    def test_call_view_login(self):
        response = self.client.get('/login/')
        self.assertEqual(response.status_code, 200)

    def test_call_ortr(self):
        response = self.client.get(reverse('ortr'))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'tickets/ortr.html')

    def test_call_view_add_spp(self):
        response = self.client.get(f'/add_spp/{self.DID}/')
        created_spp = SPP.objects.last()
        self.assertEqual(str(created_spp), '2022_00876')
        self.assertRedirects(response, reverse('spp_view_save', kwargs={'dID': self.DID, 'ticket_spp_id': created_spp.id}))

    def test_call_view_added_spp(self):
        self.client.get(f'/add_spp/{self.DID}/')
        created_spp = SPP.objects.last()
        response = self.client.get(reverse('spp_view_save', kwargs={'dID': self.DID, 'ticket_spp_id': created_spp.id}))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'tickets/spp_view_save.html')

    def test_call_view_add_tr(self):
        self.client.get(f'/add_spp/{self.DID}/')
        response = self.client.get(f'/add_tr/{self.DID}/{self.TID}/{self.TRID}/')
        created_tr = str(TR.objects.last())
        self.assertEqual(created_tr, '72459')
        self.assertRedirects(response,
                             reverse('sppdata', kwargs={'trID': self.TRID}))

    def test_call_view_sppdata_method_get(self):
        response = self.client.get(f'/sppdata/{self.TRID}/')
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'tickets/sppdata.html')

    def test_call_view_sppdata_method_post(self):
        data = {
            'type_tr': 'Коммерческое',
            'con_point': 'Сущ. точка',
            'spd': 'Комтехцентр'
        }

        response = self.client.post(f'/sppdata/{self.TRID}/', data=data)
        self.assertRedirects(response, reverse('get_resources', kwargs={'trID': self.TRID}))
        #reverse('project_tr', kwargs={'dID': '123456', 'tID': '0', 'trID': self.TRID})) не работает т.к. после редиректа ожидается 200,
        # а в project_tr еще один редирект

    def test_call_view_hotspot(self):
        self.sess.update({'tag_service': [{'sppdata': None}, {'hotspot': 'HotSpot 1 точка хот-спот'}, {'vols': None}]})
        session = self.client.session
        session[self.TRID] = self.sess
        session.save()

        response = self.client.get(f'/hotspot/{self.TRID}/?prev_page=sppdata&index=0')
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'tickets/hotspot.html')

    def test_call_view_shpd(self):
        self.sess.update({'tag_service': [{'sppdata': None}, {'shpd': 'Интернет, блок Адресов Сети Интернет /30'}, {'vols': None}]})
        session = self.client.session
        session[self.TRID] = self.sess
        session.save()

        response = self.client.get(f'/shpd/{self.TRID}/?prev_page=sppdata&index=0')
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'tickets/shpd.html')

    def test_call_view_local(self):
        self.sess.update({'tag_service': [{'sppdata': None}, {'local': 'ЛВС 1 порт Стандарт '}, {'vols': None}]})
        session = self.client.session
        session[self.TRID] = self.sess
        session.save()

        response = self.client.get(f'/local/{self.TRID}/?prev_page=sppdata&index=0')
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'tickets/local.html')

    def test_call_view_phone(self):
        self.sess.update({'tag_service': [{'sppdata': None}, {'phone': 'Телефон 1 номер 1 ГС канал'}, {'data': None}]})
        session = self.client.session
        session[self.TRID] = self.sess
        session.save()

        response = self.client.get(f'/phone/{self.TRID}/?prev_page=sppdata&index=0')
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'tickets/phone.html')

    def test_call_view_cks(self):
        self.sess.update({'tag_service': [{'sppdata': None}, {'cks': 'ЦКС 100 мбит: Громова 145 - Асбестовский 4/а '}, {'copper': None}],
                          'cks_points': ['Асбестовский переулок, д.4/А', 'Громова, д.145']})
        session = self.client.session
        session[self.TRID] = self.sess
        session.save()

        response = self.client.get(f'/cks/{self.TRID}/?prev_page=sppdata&index=0')
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'tickets/cks.html')

    def test_call_view_portvk(self):
        self.sess.update({'tag_service': [{'sppdata': None}, {'portvk': 'Порт ВЛС 100 мбит: Громова 145'}, {'copper': None}]})
        session = self.client.session
        session[self.TRID] = self.sess
        session.save()

        response = self.client.get(f'/portvk/{self.TRID}/?prev_page=sppdata&index=0')
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'tickets/portvk.html')

    def test_call_view_portvm(self):
        self.sess.update({'tag_service': [{'sppdata': None}, {'portvm': 'Порт ВМ 100 мбит: Громова 145'}, {'copper': None}]})
        session = self.client.session
        session[self.TRID] = self.sess
        session.save()

        response = self.client.get(f'/portvm/{self.TRID}/?prev_page=sppdata&index=0')
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'tickets/portvm.html')

    def test_call_view_itv(self):
        self.sess.update({'tag_service': [{'sppdata': None}, {'itv': 'iTV 1 приставка'}, {'copper': None}]})
        session = self.client.session
        session[self.TRID] = self.sess
        session.save()

        response = self.client.get(f'/itv/{self.TRID}/?prev_page=sppdata&index=0')
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'tickets/itv.html')

    def test_call_view_video(self):
        self.sess.update({'tag_service': [{'sppdata': None}, {'video': 'Видеонаблюдение 1 камера'}, {'data': None}]})
        session = self.client.session
        session[self.TRID] = self.sess
        session.save()

        response = self.client.get(f'/video/{self.TRID}/?prev_page=sppdata&index=0')
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'tickets/video.html')

    def test_call_view_copper(self):
        self.sess.update({'tag_service': [{'sppdata': None}, {'shpd': 'Интернет, DHCP 15 мбит/32'}, {'copper': None}],
                          'pps': 'БЗК Березовский тракт 5 П1 Э3 (Лестничная клетка), АВ'})
        session = self.client.session
        session[self.TRID] = self.sess
        session.save()

        response = self.client.get(f'/copper/{self.TRID}/?prev_page=shpd&index=1')
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'tickets/env.html')

    def test_call_view_vols(self):
        self.sess.update({'tag_service': [{'sppdata': None}, {'shpd': 'Интернет, DHCP 15 мбит/32'}, {'vols': None}],
                          'pps': 'БЗК Березовский тракт 5 П1 Э3 (Лестничная клетка), АВ'})
        session = self.client.session
        session[self.TRID] = self.sess
        session.save()

        response = self.client.get(f'/vols/{self.TRID}/?prev_page=shpd&index=1')
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'tickets/env.html')

    def test_call_view_rtk(self):
        self.sess.update({'tag_service': [{'sppdata': None}, {'shpd': 'Интернет, DHCP 15 мбит/32'}, {'rtk': None}],
                          })
        session = self.client.session
        session[self.TRID] = self.sess
        session.save()

        response = self.client.get(f'/rtk/{self.TRID}/?prev_page=shpd&index=1')
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'tickets/rtk.html')

    def test_call_view_pass_video(self):
        self.sess.update({'tag_service': [{'job_formset': None}, {'pass_video': None}],
                          })
        session = self.client.session
        session[self.TRID] = self.sess
        session.save()

        response = self.client.get(f'/pass_video/{self.TRID}/?prev_page=job_formset&index=0')
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'tickets/pass_video.html')

    def test_call_view_pps(self):
        session = self.client.session
        session[self.TRID] = self.sess
        session.save()

        response = self.client.get(f'/pps/{self.TRID}/')
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'tickets/pps.html')

class MkoViewsTestCase(TestCase):
    DID = '141891'
    TID = '211509'
    TRID = '72459'
    PPS = 'БЗК Березовский тракт 5 П1 Э3 (Лестничная клетка), АВ'

    def setUp(self):
        hold_position = HoldPosition.objects.create(name='Менеджер')
        User = get_user_model()
        user = User.objects.create_user('manager', 'manager@gmail.com', 'manager',
                                        last_name='Бискинский Е.В.')
        UserHoldPosition.objects.create(user=user, hold_position=hold_position)
        group = Group.objects.create(name='Менеджеры')
        group.user_set.add(user)

        self.spp = SPP.objects.create(user=user, dID='123456', services={}, des_tr={}, created=timezone.now(),
                                      complited=timezone.now(), version=1,
                                      ticket_k='2023_00000', process=True,
                                      )
        self.tr = TR.objects.create(ticket_k=self.spp, ticket_tr=self.TRID, services={}, vID=1,
                                    pps=self.PPS
                                    )
        self.client.login(username='manager', password='manager')
        self.sess = {'ticket_spp_id': self.tr.ticket_k.id, 'ticket_tr_id': self.tr.id, 'dID': '123456',
                     'technical_solution': self.TRID}

    def test_call_mko(self):
        response = self.client.get(reverse('mko'))
        self.assertEqual(response.status_code, HTTPStatus.OK)
        self.assertTemplateUsed(response, 'tickets/mko.html')

    def test_call_view_add_spp_not_simplified(self):
        response = self.client.get(f'/add_spp/{self.DID}/')
        self.assertRedirects(response, reverse('mko'))

    def test_call_view_add_spp_simplified(self):
        response = self.client.get(f'/add_spp/174280/')
        created_spp = SPP.objects.last()
        self.assertRedirects(response, reverse('spp_view_save', kwargs={'dID': '174280', 'ticket_spp_id': created_spp.id}))


