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
from parameterized import parameterized

from tickets.models import SPP, TR
from oattr.models import HoldPosition, UserHoldPosition
from django.contrib.auth.models import Group

BASE_DIR = Path(__file__).resolve().parent.parent
dotenv_path = os.path.join(BASE_DIR, '.env')
load_dotenv(dotenv_path)
TEST_CORDIS_USER = os.getenv('CORDIS_USER_OUZP_SPD')
TEST_CORDIS_PASSWORD = os.getenv('CORDIS_PASSWORD_OUZP_SPD')


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

        self.spp = SPP.objects.create(user=user, dID='123456', services=['Интернет, DHCP 10'], des_tr={},
                                        created=timezone.now(),
                                        complited=timezone.now(), version=1,
                                        ticket_k='2023_00000', process = True,
                                        )
        self.tr = TR.objects.create(ticket_k=self.spp, ticket_tr=self.TRID, services=['Интернет, DHCP 10'], vID=1,
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

    @parameterized.expand([
        ('Коммерческое', 'Сущ. точка', 'Комтехцентр', reverse('get_resources', kwargs={'trID': '72459'})),
        ('Коммерческое', 'Нов. точка', 'Комтехцентр', reverse('project_tr', kwargs={'dID': '123456', 'tID': '0', 'trID': '72459'})),
        ('Не требуется', 'Нов. точка', 'Комтехцентр', reverse('data', kwargs={'trID': '72459'})),
        ('ПТО', 'Нов. точка', 'Комтехцентр', reverse('pps', kwargs={'trID': '72459'})),
        ('ПТО', 'Нов. точка', 'РТК', reverse('spp_view_save', kwargs={'dID': '123456', 'ticket_spp_id': '1'})),
    ])
    def test_call_view_sppdata_method_post(self, type_tr, connection_point, spd, expected):
        data = {
            'type_tr': type_tr,
            'con_point': connection_point,
            'spd': spd
        }
        if expected == '/db/123456-1/':
            expected = expected.replace('-1', f'-{self.spp.id}') # В parameterized невозможно указать self.spp.id

        response = self.client.post(f'/sppdata/{self.TRID}/', data=data)
        self.assertEqual(response.url, expected)
        # self.assertRedirects(response, reverse('get_resources', kwargs={'trID': self.TRID}))
        # reverse('project_tr', kwargs={'dID': '123456', 'tID': '0', 'trID': self.TRID}) не работает т.к. после редиректа ожидается 200,
        # а в project_tr еще один редирект

    @parameterized.expand([
        ('/hotspot/72459/?prev_page=sppdata&index=0', [0]),
        ('/hotspot/72459/?next_page=hotspot&index=1', [0, 1]),
    ])
    def test_call_view_hotspot_method_get(self, request_url, tag_service_index):
        self.sess.update({'tag_service': [{'sppdata': None}, {'hotspot': 'HotSpot 1 точка хот-спот'}, {'vols': None}],
                          'tag_service_index': tag_service_index})
        session = self.client.session
        session[self.TRID] = self.sess
        session.save()

        response = self.client.get(request_url)
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'tickets/hotspot.html')

    def test_call_view_hotspot_method_post(self):
        data = {'type_hotspot': 'Хот-спот Стандарт', 'exist_hotspot_client': False, 'hotspot_local_wifi': False,
                'hotspot_points': 1, 'hotspot_users': 1}

        self.sess.update({'tag_service': [{'sppdata': None}, {'hotspot': 'HotSpot 1 точка хот-спот'}, {'shpd': 'Интернет, DHCP Next'}],
                          'tag_service_index': [0],
                          })
        session = self.client.session
        session[self.TRID] = self.sess
        session.save()

        response = self.client.post(f'/hotspot/{self.TRID}/', data=data)
        self.assertRedirects(response, '/shpd/72459/?index=1&prev_page=hotspot')

    @parameterized.expand([
        ('/shpd/72459/?prev_page=sppdata&index=0', [0]),
        ('/shpd/72459/?next_page=shpd&index=1', [0, 1]),
    ])
    def test_call_view_shpd_method_get(self, request_url, tag_service_index):
        self.sess.update({'tag_service': [{'sppdata': None}, {'shpd': 'Интернет, блок Адресов Сети Интернет /30'}, {'vols': None}],
                          'tag_service_index': tag_service_index})
        session = self.client.session
        session[self.TRID] = self.sess
        session.save()

        response = self.client.get(request_url)
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'tickets/shpd.html')

    def test_call_view_shpd_method_post(self):
        data = {'router': False, 'type_shpd': 'access', 'exist_service': ''}

        self.sess.update({'tag_service': [{'sppdata': None}, {'shpd': 'Интернет, DHCP 15 мбит/32'}, {'copper': None}],
                          'tag_service_index': [0], 'pps': 'БЗК Березовский тракт 5 П1 Э3 (Лестничная клетка), АВ'
                          })
        session = self.client.session
        session[self.TRID] = self.sess
        session.save()

        response = self.client.post(f'/shpd/{self.TRID}/', data=data)
        self.assertRedirects(response, '/copper/72459/?index=1&prev_page=shpd')


    @parameterized.expand([
        ('/local/72459/?prev_page=sppdata&index=0', [0]),
        ('/local/72459/?next_page=local&index=1', [0, 1]),
    ])
    def test_call_view_local_method_get(self, request_url, tag_service_index):
        self.sess.update({'tag_service': [{'sppdata': None}, {'local': 'ЛВС 1 порт Стандарт '}, {'vols': None}],
                          'tag_service_index': tag_service_index})
        session = self.client.session
        session[self.TRID] = self.sess
        session.save()

        response = self.client.get(request_url)
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'tickets/local.html')

    def test_call_view_local_method_post(self):
        data = {'local_type': 'sks_standart', 'local_ports': 1, 'local_socket_need': False, 'local_socket': '',
                'local_cable_channel': '', 'sks_router': False, 'sks_transceiver': 'Конвертеры 100',
                'lvs_busy': False, 'lvs_switch': 'TP-Link TL-SG105 V4'}

        self.sess.update({'tag_service': [{'sppdata': None}, {'local': 'ЛВС 1 порт Стандарт '}, {'shpd': 'Интернет, DHCP Next'}],
                          'tag_service_index': [0], 'services_plus_desc': ['ЛВС 1 порт Стандарт ']
                          })
        session = self.client.session
        session[self.TRID] = self.sess
        session.save()

        response = self.client.post(f'/local/{self.TRID}/', data=data)
        self.assertRedirects(response, '/shpd/72459/?prev_page=local&index=1')

    @parameterized.expand([
        ('/phone/72459/?prev_page=sppdata&index=0', [0]),
        ('/phone/72459/?next_page=phone&index=1', [0, 1]),
    ])
    def test_call_view_phone_method_get(self, request_url, tag_service_index):
        self.sess.update({'tag_service': [{'sppdata': None}, {'phone': 'Телефон 1 номер'}, {'data': None}],
                          'tag_service_index': tag_service_index})
        session = self.client.session
        session[self.TRID] = self.sess
        session.save()

        response = self.client.get(request_url)
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'tickets/phone.html')

    @parameterized.expand([
        ('s',),
        ('st',),
        ('ak',),
        ('ap',),
        ('ab',),
    ])
    def test_call_view_phone_method_post(self, type):
        data = {'type_phone': type, 'vgw': 'D-Link DVG-5402SP', 'channel_vgw': 1, 'ports_vgw': '',
                'type_ip_trunk': 'access', 'form_exist_vgw_model': '', 'form_exist_vgw_name': '',
                'form_exist_vgw_port': '', 'channel_vgw_1': 2, 'csrfmiddlewaretoken': '12345'}

        self.sess.update({'tag_service': [{'sppdata': None}, {'phone': 'Телефон 1 номер'}, {'shpd': 'Интернет, DHCP Next'}, {'copper': None}],
                          'tag_service_index': [0], 'current_index_local': 1, 'services_plus_desc': ['Телефон 1 номер'],
                          'sreda': 1})
        session = self.client.session
        session[self.TRID] = self.sess
        session.save()

        response = self.client.post(f'/phone/{self.TRID}/', data=data)
        self.assertRedirects(response, '/shpd/72459/?prev_page=phone&index=1')

    @parameterized.expand([
        ('/cks/72459/?prev_page=sppdata&index=0', [0]),
        ('/cks/72459/?next_page=cks&index=1', [0, 1]),
    ])
    def test_call_view_cks_method_get(self, request_url, tag_service_index):
        self.sess.update({'tag_service': [{'sppdata': None}, {'cks': 'ЦКС 100 мбит: Громова 145 - Асбестовский 4/а '}, {'shpd': 'Интернет, DHCP 1'}],
                          'cks_points': ['Асбестовский переулок, д.4/А', 'Громова, д.145'], 'tag_service_index': tag_service_index})
        session = self.client.session
        session[self.TRID] = self.sess
        session.save()

        response = self.client.get(request_url)
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'tickets/cks.html')

    def test_call_view_cks_method_post(self):
        data = {'pointA': 'Гагарина, д.8', 'pointB': 'Титова, д.14', 'policer_cks': 'полисером Subinterface',
         'type_cks': 'access', 'exist_service': ''}

        self.sess.update({'tag_service': [{'sppdata': None}, {'phone': 'Телефон 1 номер'}, {'shpd': 'Интернет, DHCP Next'}],
                          'tag_service_index': [0]})
        session = self.client.session
        session[self.TRID] = self.sess
        session.save()

        response = self.client.post(f'/cks/{self.TRID}/', data=data)
        self.assertRedirects(response, '/shpd/72459/?prev_page=phone&index=1')

    @parameterized.expand([
        ('/portvk/72459/?prev_page=sppdata&index=0', [0]),
        ('/portvk/72459/?next_page=portvk&index=1', [0, 1]),
    ])
    def test_call_view_portvk_method_get(self, request_url, tag_service_index):
        self.sess.update({'tag_service': [{'sppdata': None}, {'portvk': 'Порт ВЛС 100 мбит: Громова 145'}, {'shpd': 'Интернет, DHCP Next'}],
                          'tag_service_index': tag_service_index})
        session = self.client.session
        session[self.TRID] = self.sess
        session.save()

        response = self.client.get(request_url)
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'tickets/portvk.html')

    def test_call_view_portvk_method_post(self):
        data = {'type_vk': 'Новая ВЛС', 'exist_vk': '', 'policer_vk': 'полисером на Subinterface',
                'type_portvk': 'access', 'exist_service': ''}

        self.sess.update({'tag_service': [{'sppdata': None}, {'portvk': 'Порт ВЛС 100 мбит: Громова 145'}, {'shpd': 'Интернет, DHCP Next'}],
                          'tag_service_index': [0]})
        session = self.client.session
        session[self.TRID] = self.sess
        session.save()

        response = self.client.post(f'/portvk/{self.TRID}/', data=data)
        self.assertRedirects(response, '/shpd/72459/?prev_page=portvk&index=1')

    @parameterized.expand([
        ('/portvm/72459/?prev_page=sppdata&index=0', [0]),
        ('/portvm/72459/?next_page=portvm&index=1', [0, 1]),
    ])
    def test_call_view_portvm_method_get(self, request_url, tag_service_index):
        self.sess.update({'tag_service': [{'sppdata': None}, {'portvm': 'Порт ВМ 100 мбит: Громова 145'}, {'copper': None}],
                          'tag_service_index': tag_service_index})
        session = self.client.session
        session[self.TRID] = self.sess
        session.save()

        response = self.client.get(request_url)
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'tickets/portvm.html')

    def test_call_view_portvm_method_post(self):
        data = {'type_vm': 'Cуществующий ВМ', 'exist_vm': 'CC-00340984-VRF', 'policer_vm': 'на порту подключения',
                'vm_inet': False, 'type_portvm': 'access', 'exist_service_vm': ''}

        self.sess.update({'tag_service': [{'sppdata': None}, {'portvm': 'Порт ВМ 100 мбит: Громова 145'}, {'shpd': 'Интернет, DHCP Next'}],
                          'tag_service_index': [0]})
        session = self.client.session
        session[self.TRID] = self.sess
        session.save()

        response = self.client.post(f'/portvm/{self.TRID}/', data=data)
        self.assertRedirects(response, '/shpd/72459/?prev_page=portvm&index=1')

    @parameterized.expand([
        ('/itv/72459/?prev_page=sppdata&index=0', [0]),
        ('/itv/72459/?next_page=itv&index=1', [0, 1]),
    ])
    def test_call_view_itv_method_get(self, request_url, tag_service_index):
        self.sess.update({'tag_service': [{'sppdata': None}, {'itv': 'iTV 1 приставка'}, {'copper': None}],
                          'tag_service_index': tag_service_index})
        session = self.client.session
        session[self.TRID] = self.sess
        session.save()

        response = self.client.get(request_url)
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'tickets/itv.html')

    @parameterized.expand([
        (['iTV 1 приставка'], reverse('spp_view_save', kwargs={'dID': '123456', 'ticket_spp_id': '1'})),
        (['iTV 1 приставка', 'Интернет, DHCP Next'], '/copper/72459/?prev_page=itv&index=1'),
    ])
    def test_call_view_itv_method_post(self, services_plus_desc, expected):
        data = {'type_itv': 'novl', 'cnt_itv': 1, 'need_line_itv': True, 'router_itv': False}

        self.sess.update({'tag_service': [{'sppdata': None}, {'itv': 'iTV 1 приставка'}, {'copper': None}],
                          'tag_service_index': [0], 'services_plus_desc': services_plus_desc,
                          'pps': 'БЗК Березовский тракт 5 П1 Э3 (Лестничная клетка), АВ'})
        session = self.client.session
        session[self.TRID] = self.sess
        session.save()

        if expected == '/db/123456-1/':
            expected = expected.replace('-1', f'-{self.spp.id}')

        response = self.client.post(f'/itv/{self.TRID}/', data=data)
        self.assertRedirects(response, expected)

    @parameterized.expand([
        ('/video/72459/?prev_page=sppdata&index=0', [0]),
        ('/video/72459/?next_page=video&index=1', [0, 1]),
    ])
    def test_call_view_video_method_get(self, request_url, tag_service_index):
        self.sess.update({'tag_service': [{'sppdata': None}, {'video': 'Видеонаблюдение 1 камера'}, {'data': None}],
                          'tag_service_index': tag_service_index})
        session = self.client.session
        session[self.TRID] = self.sess
        session.save()

        response = self.client.get(request_url)
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'tickets/video.html')

    def test_call_view_video_method_post(self):
        data = {'camera_number': '3', 'camera_model': 'QTECH', 'deep_archive': '0',
                'vm_inet': False, 'type_portvm': 'access', 'exist_service_vm': ''}

        self.sess.update({'tag_service': [{'sppdata': None}, {'video': 'Видеонаблюдение 1 камера'}, {'shpd': 'Интернет, DHCP Next'}],
                          'tag_service_index': [0]})
        session = self.client.session
        session[self.TRID] = self.sess
        session.save()

        response = self.client.post(f'/video/{self.TRID}/', data=data)
        self.assertRedirects(response, '/shpd/72459/?prev_page=video&index=1')

    @parameterized.expand([
        ('/copper/72459/?prev_page=sppdata&index=0', [0]),
        ('/copper/72459/?next_page=video&index=1', [0, 1]),
    ])
    def test_call_view_copper_method_get(self, request_url, tag_service_index):
        self.sess.update({'tag_service': [{'sppdata': None}, {'shpd': 'Интернет, DHCP 15 мбит/32'}, {'copper': None}],
                          'pps': 'БЗК Березовский тракт 5 П1 Э3 (Лестничная клетка), АВ',
                          'tag_service_index': tag_service_index})
        session = self.client.session
        session[self.TRID] = self.sess
        session.save()

        response = self.client.get(request_url)
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'tickets/env.html')

    @parameterized.expand([
        ('2', [False, False, False, False], '1.1.1.1/30', '/copper/72459/?prev_page=shpd&index=1'),
        ('1', [False, False, False, False], '1.1.1.1/30', '/data/72459/?prev_page=copper&index=2'),
        ('1', [False, False, False, False], '1.1.1.1/32', '/change_log_shpd/72459/?prev_page=copper&index=2'),
        ('1', [True, False, False, False], '1.1.1.1/30', '/csw/72459/?prev_page=copper&index=2'),
        ('1', [False, True, False, False], '1.1.1.1/30', '/csw/72459/?prev_page=copper&index=2'),
        ('1', [False, False, True, False], '1.1.1.1/30', '/csw/72459/?prev_page=copper&index=2'),
        ('1', [False, False, False, True], '1.1.1.1/30', '/csw/72459/?prev_page=copper&index=2'),
    ])
    def test_call_view_copper_method_post(self, sreda, logic_csw, ip, expected):
        data = {'correct_sreda': '1', 'kad': 'SW', 'port': '1', 'logic_csw': logic_csw[0],
        'logic_replace_csw': logic_csw[1], 'logic_change_gi_csw': logic_csw[2], 'logic_change_csw': logic_csw[3],}

        self.sess.update({'tag_service': [{'sppdata': None}, {'shpd': 'Интернет, DHCP 15 мбит/32'}, {'copper': None}],
                          'sreda': sreda, 'tag_service_index': [0, 1], 'type_pass': ['Перенос, СПД'],
                          'readable_services': {'"ШПД в интернет"': f'c реквизитами "{ip}"'},
                          'pps': 'БЗК Березовский тракт 5 П1 Э3 (Лестничная клетка), АВ'})
        session = self.client.session
        session[self.TRID] = self.sess
        session.save()

        response = self.client.post(f'/copper/{self.TRID}/', data=data)
        self.assertEqual(response.url, expected)

    @parameterized.expand([
        ('/vols/72459/?prev_page=sppdata&index=0', [0]),
        ('/vols/72459/?next_page=video&index=1', [0, 1]),
    ])
    def test_call_view_vols_method_get(self, request_url, tag_service_index):
        self.sess.update({'tag_service': [{'sppdata': None}, {'shpd': 'Интернет, DHCP 15 мбит/32'}, {'vols': None}],
                          'pps': 'БЗК Березовский тракт 5 П1 Э3 (Лестничная клетка), АВ',
                          'tag_service_index': tag_service_index})
        session = self.client.session
        session[self.TRID] = self.sess
        session.save()

        response = self.client.get(request_url)
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'tickets/env.html')

    @parameterized.expand([
        ('1', [False, False, False, False], '1.1.1.1/30', '/vols/72459/?prev_page=shpd&index=1'),
        ('2', [False, False, False, False], '1.1.1.1/30', '/data/72459/?prev_page=vols&index=2'),
        ('2', [False, False, False, False], '1.1.1.1/32', '/change_log_shpd/72459/?prev_page=vols&index=2'),
        ('2', [True, False, False, False], '1.1.1.1/30', '/csw/72459/?prev_page=vols&index=2'),
        ('2', [False, True, False, False], '1.1.1.1/30', '/csw/72459/?prev_page=vols&index=2'),
        ('2', [False, False, True, False], '1.1.1.1/30', '/csw/72459/?prev_page=vols&index=2'),
        ('2', [False, False, False, True], '1.1.1.1/30', '/csw/72459/?prev_page=vols&index=2'),
    ])
    def test_call_view_vols_method_post(self, sreda, logic_csw, ip, expected):
        data = {'correct_sreda': '2', 'kad': 'SW', 'port': '1', 'logic_csw': logic_csw[0],
        'logic_replace_csw': logic_csw[1], 'logic_change_gi_csw': logic_csw[2], 'logic_change_csw': logic_csw[3],
        'device_pps': 'конвертер 1310 нм, выставить на конвертере режим работы Auto',
        'device_client': 'конвертер 1550 нм, выставить на конвертере режим работы Auto',
        'speed_port': 'Auto'}

        self.sess.update({'tag_service': [{'sppdata': None}, {'shpd': 'Интернет, DHCP 15 мбит/32'}, {'vols': None}],
                          'sreda': sreda, 'tag_service_index': [0, 1], 'type_pass': ['Перенос, СПД'],
                          'readable_services': {'"ШПД в интернет"': f'c реквизитами "{ip}"'},
                          'pps': 'БЗК Березовский тракт 5 П1 Э3 (Лестничная клетка), АВ'})
        session = self.client.session
        session[self.TRID] = self.sess
        session.save()

        response = self.client.post(f'/vols/{self.TRID}/', data=data)
        self.assertEqual(response.url, expected)

    def test_call_view_rtk(self):
        self.sess.update({
            'tag_service': [{'sppdata': None}, {'shpd': 'Интернет, DHCP 15 мбит/32'}, {'rtk': None}],
            'oattr': '№ Наряда Лиры: 269828107 № КЗ Гермес : 9273957 Сх.вкл.:FTTb порт, № устр.:143431087870 № брони' +
            ' в СТУ Аргус: 218384939, бронь до 06.07 ЛД: (Д_14057_Кабинет2_Фролова,31[172.20.80.194]-1 (1GE)[1/1]-н/о)'})
        session = self.client.session
        session[self.TRID] = self.sess
        session.save()

        response = self.client.get(f'/rtk/{self.TRID}/?prev_page=shpd&index=1')
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'tickets/rtk.html')

    @parameterized.expand([
        ('/pass_video/72459/?prev_page=job_formset&index=0', [0]),
        ('/pass_video/72459/?next_page=pass_video&index=1', [0, 1]),
    ])
    def test_call_view_pass_video_method_get(self, request_url, tag_service_index):
        self.sess.update({'tag_service': [{'job_formset': None}, {'pass_video': None}],
                          'tag_service_index': tag_service_index})
        session = self.client.session
        session[self.TRID] = self.sess
        session.save()

        response = self.client.get(request_url)
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'tickets/pass_video.html')

    def test_call_view_pass_serv(self):
        self.sess.update({'tag_service': [{'job_formset': None}, {'pass_serv': None}],
                          })
        session = self.client.session
        session[self.TRID] = self.sess
        session.save()

        response = self.client.get(f'/pass_serv/{self.TRID}/?prev_page=job_formset&index=0')
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'tickets/pass_serv.html')

    def test_call_view_pass_turnoff(self):
        self.sess.update({'tag_service': [{'job_formset': None}, {'pass_serv': None}, {'pass_turnoff': None}],
                          })
        session = self.client.session
        session[self.TRID] = self.sess
        session.save()

        response = self.client.get(f'/pass_turnoff/{self.TRID}/?prev_page=pass_serv&index=1')
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'tickets/pass_turnoff.html')

    def test_call_view_change_log_shpd(self):
        self.sess.update({'tag_service': [{'job_formset': None}, {'pass_serv': None}, {'vols': None}, {'change_log_shpd': None}, {'data': None}],
                          })
        session = self.client.session
        session[self.TRID] = self.sess
        session.save()

        response = self.client.get(f'/change_log_shpd/{self.TRID}/?prev_page=vols&index=2')
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'tickets/change_log_shpd.html')

    def test_call_view_change_serv(self):
        self.sess.update({'tag_service': [{'job_formset': None}, {'change_serv': {'shpd': 'Интернет, блок Адресов Сети Интернет 100 мбит/сек, 30 подсеть'}},
                                          {'change_serv': {'shpd': 'Интернет, блок Адресов Сети Интернет 30 подсеть'}}, {'data': None}],})
        session = self.client.session
        session[self.TRID] = self.sess
        session.save()

        response = self.client.get(f'/change_serv/{self.TRID}/?prev_page=job_formset&index=0')
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'tickets/change_serv.html')

    @parameterized.expand([
        "Организация доп connected",
        "Организация доп маршрутизируемой",
        "Замена connected на connected",
        "Замена IP",
        "Изменение cхемы организации ШПД",
    ])
    def test_call_view_change_params_serv(self, type):
        self.sess.update({'tag_service': [{'job_formset': None}, {'change_serv': {'shpd': 'Интернет, блок Адресов Сети Интернет 30 подсеть'}},
                                          {'change_params_serv': None}, {'data': None}],
                             'types_change_service': [{type: {'shpd': 'Интернет, блок Адресов Сети Интернет 30 подсеть'}}],})
        session = self.client.session
        session[self.TRID] = self.sess
        session.save()

        response = self.client.get(f'/change_params_serv/{self.TRID}/?prev_page=change_serv&index=1')
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'tickets/change_params_serv.html')

    def test_call_view_job_formset(self):
        response = self.client.get(f'/job_formset/{self.TRID}/')
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'tickets/job_formset.html')

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


