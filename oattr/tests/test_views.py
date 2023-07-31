from django.contrib.auth import get_user_model
from django.test import TestCase

import os
import datetime
from pathlib import Path

from django.urls import reverse
from django.utils import timezone
from dotenv import load_dotenv
from oattr.models import HoldPosition, UserHoldPosition, OtpmSpp, OtpmTR

BASE_DIR = Path(__file__).resolve().parent.parent
dotenv_path = os.path.join(BASE_DIR, '.env')
load_dotenv(dotenv_path)
CORDIS_USER = os.getenv('CORDIS_USER')
CORDIS_PASSWORD = os.getenv('CORDIS_PASSWORD')


class ViewsTestCase(TestCase):
    DID = '141891'
    TID = '211509'
    TRID = '72459'
    def setUp(self):
        hold_position = HoldPosition.objects.create(name='Техник-технолог ОАТТР, ЕКБ')
        User = get_user_model()
        user = User.objects.create_user('temporary', 'temporary@gmail.com', 'temporary', last_name='Аристов Д.В.')
        UserHoldPosition.objects.create(user=user, hold_position=hold_position)
        self.otpm_spp = OtpmSpp.objects.create(user=user, dID='123456', services={}, des_tr={}, created=timezone.now(),
                                          waited=timezone.now(), duration_process=datetime.timedelta(0),
                                          duration_wait=datetime.timedelta(0), ticket_k='2023_00000', process = True
                                          )
        self.client.login(username='temporary', password='temporary')
        response = self.client.post('/login_for_service/', data={'username': CORDIS_USER, 'password': CORDIS_PASSWORD})
        self.assertRedirects(response, '/')

    def test_call_view_login(self):
        response = self.client.get('/login/')
        self.assertEqual(response.status_code, 200)

    def test_call_view_login_for_service(self):
        response = self.client.get('/login_for_service/')
        self.assertEqual(response.status_code, 200)

    def test_call_view_registration(self):
        response = self.client.get('/registration')
        self.assertEqual(response.status_code, 200)

    def test_call_view_deny_anonymous(self):
        self.client.logout()
        response = self.client.get('/', follow=True)
        self.assertRedirects(response, 'login/?next=/')
        response = self.client.post('/', follow=True)
        self.assertRedirects(response, 'login/?next=/')

    def test_call_view_authenticated_user(self):
        #self.client.login(username='temporary', password='temporary')  # defined in fixture or with factory in setUp()
        response = self.client.get('/')
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'tickets/private_page.html')

    def test_call_view_otpm_without_query_params(self):
        response = self.client.get(reverse('otpm'))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'oattr/pool_oattr.html')

    def test_call_view_otpm_with_query_params(self):
        response = self.client.get('/otpm/?technolog=Аристов+Д.В.&group=Все&status=Все')
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'oattr/pool_oattr.html')

    def test_call_view_copper(self):
        response = self.client.get(reverse('otpm_copper'))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'oattr/copper.html')

    def test_call_view_create_spp(self):
        response = self.client.get(f'/otpm/create_spp/{self.DID}/?stage=В работе ОТПМ')
        created_spp = str(OtpmSpp.objects.last())
        self.assertEqual(created_spp, '2022_00876')
        self.assertRedirects(response, reverse('spp_view_oattr', kwargs={'dID': self.DID}))

    def test_call_view_create_spp_already_process(self):
        response = self.client.get(f'/otpm/create_spp/{self.otpm_spp.dID}/?stage=В работе ОТПМ')
        self.assertRedirects(response, reverse('otpm'))

    def test_call_view_spp_view_oattr(self):
        response = self.client.get(reverse('spp_view_oattr', kwargs={'dID': self.otpm_spp.dID}))#f'/otpm/db/{dID}/')#
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'oattr/spp_view_oattr.html')

    def test_call_view_spp_view_oattr_wait_and_notwait(self):
        self.client.get(f'/otpm/db/{self.otpm_spp.dID}/?action=wait')
        otpm_spp = OtpmSpp.objects.get(dID=self.otpm_spp.dID)
        self.assertEqual(otpm_spp.wait, True)
        self.assertEqual(otpm_spp.process, False)
        self.client.get(f'/otpm/db/{self.otpm_spp.dID}/?action=notwait')
        otpm_spp = OtpmSpp.objects.get(dID=self.otpm_spp.dID)
        self.assertEqual(otpm_spp.wait, False)
        self.assertEqual(otpm_spp.process, True)

    def test_call_view_send_spp(self):
        response = self.client.get(reverse('send_spp', kwargs={'dID': self.otpm_spp.dID}))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'oattr/send_spp.html')

    def test_call_view_create_tr(self):
        self.client.get(f'/otpm/create_spp/{self.DID}/?stage=В работе ОТПМ')
        response = self.client.get(f'/otpm/add_tr/{self.DID}/{self.TID}/{self.TRID}/?action=add')
        created_tr = str(OtpmTR.objects.last())
        self.assertEqual(created_tr, '72459')
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'oattr/sppdata.html')