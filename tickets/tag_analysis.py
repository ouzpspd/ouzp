import pymssql
from Exscript import Account
from Exscript.protocols import Telnet
import re
from typing import List, Tuple
from django.conf import settings
from itertools import chain


def sql_connection_and_request():
    # Параметры подключения к базе данных
    server = settings.DB_SERVER_CORDIS
    database = settings.DB_CORDIS
    user = settings.DB_USER_CORDIS
    password = settings.DB_PASSWORD_CORDIS

    query = """
    SELECT DISTINCT s.name, Nets.IpDigitToCanon(s.ip_address)
    FROM nets.switch s
    JOIN Nets.switch_model sm ON s.switch_model = sm.switch_model
    WHERE sm.vendor = 'cisco' 
    AND NOT sm.model = 'ASR 9001'
    AND s.enabled = 1 
    AND s.name LIKE 'AR%'
    AND NOT s.name LIKE '%FAKE%' ORDER BY s.name
    """

    try:
        # Подключение к базе данных
        with pymssql.connect(server, user, password, database) as conn:
            cursor = conn.cursor()
            cursor.execute(query)
            result = cursor.fetchall()
        return result
    except pymssql.Error as e:
        return []


def get_free_vlans_for_ar(selected_ar: str) -> Tuple[List[int], List[int]]:
    """
    Получает список свободных VLAN и VLAN с именем 'Rezerv' (независимо от регистра).
    Возвращает кортеж: (свободные VLAN, VLAN с именем 'Rezerv').
    """
    ar = Ar(selected_ar)
    ar.manage_connect()
    # Получаем данные о VLAN и xconnect
    vlans_output = ar.send_cmd('show vlan brief | incl ^[1-3][0-9][0-9][0-9]')
    xconnects_output = ar.send_cmd('show mpls l2transport vc | incl Eth')
    ar.manage_close()
    # Парсим данные
    vlan_tags, rezerv_tags = parse_vlans(vlans_output)
    xconnect_tags = parse_xconnects(xconnects_output)
    # Определяем диапазон VLAN
    vlan_range = range(1201, 2900)
    if selected_ar == '212.49.96.113':
        vlan_range = list(chain(range(1201, 2900), range(3000, 3299)))
    # Вычисляем свободные VLAN
    free_vlans = sorted(set(vlan_range) - set(vlan_tags) - set(xconnect_tags))
    return free_vlans, rezerv_tags


def parse_vlans(output: str) -> Tuple[List[int], List[int]]:
    """
    Парсит вывод команды 'show vlan brief' и возвращает два списка:
    1. Занятые VLAN.
    2. VLAN с именем 'Rezerv' (независимо от регистра).
    """
    if not output:
        return [], []
    vlan_tags = []
    rezerv_tags = []
    matches = re.findall(r'^(\d+)\s+(\S+)', output, re.MULTILINE)
    for tag, name in matches:
        vlan_tags.append(int(tag))
        if "rezerv" in name.lower() :
            rezerv_tags.append(int(tag))
    return vlan_tags, rezerv_tags


def parse_xconnects(output: str) -> List[int]:
    """
    Парсит вывод команды 'show mpls l2transport vc' и возвращает список VLAN из xconnect.
    """
    if not output:
        return []
    matches = re.findall(r'^\S+\s+(?:Ethernet\s+|\D+(\d+)\s+)', output, re.MULTILINE)
    return [int(match) for match in matches if match.isdigit()]


class Ar:
    __ip = ''
    __login = ''
    __password = ''
    __tn = ''
    __procid = ''
    __connected = False
    __logged_in = False
    __model = ''

    def __init__(self, ip, model='Cisco'):
        self.__ip = ip
        self.__model = model
        self.__login = settings.SWITCH_AM_CISCO_USER
        self.__password = settings.SWITCH_AM_CISCO_PASSWORD

    def manage_connect(self, timeout=5):
        if not self.__connected:
            self.__tn = Telnet(debug=0, connect_timeout=timeout, timeout=timeout + 10)
            self.__tn.connect(self.__ip)
            self.__connected = True
            return self.manage_login()
        return self.__connected

    def manage_login(self):
        if not self.__logged_in:
            # Создаем внутренний класс Exscript Account, который хранит логин и пароль, понятный функции login.
            account = Account(self.__login, self.__password, 'qq')
            self.__tn.login(account)
            self.__logged_in = True
            self.send_cmd('terminal length 0')
            return self.__logged_in
        return self.__logged_in

    def manage_close(self):
        if self.__tn:
            self.__tn.set_prompt('')
            self.__tn.execute('exit')
            self.__tn.close(force=True)
        self.__logged_in = self.__connected = False

    def send_cmd(self, command):
        result = self.__tn.execute(command)
        if result:
            if 'is an internal vlan' in self.__tn.response:
                return
            return self.__tn.response