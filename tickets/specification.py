import json
import datetime
import copy
import requests
import re
import random
from bs4 import BeautifulSoup
from requests.auth import HTTPBasicAuth


class Tentura:
    URL = 'https://tentura.corp.itmh.ru/ajax2/'
    def __init__(self, username, password, otu_project_id):
        self.client = requests.session()
        self.username = username
        self.password = password
        self.otu_project_id = otu_project_id

    def check_active_project_for_user(self):
        data = {"id": 5555, "method": "set_active_project_for_user", "params": [self.otu_project_id]}
        return self.__connection(data)

    def __connection(self, data):
        req = self.client.post(self.URL, verify=False, auth=HTTPBasicAuth(self.username, self.password), data=json.dumps(data))
        if req.status_code == 401:
            return {'error': 'Нет доступа. Неверный логин/пароль.'}
        return req.json()

    def get_project_context(self):
        data = {"id": 5555, "method":"project_context_get", "params":[f'{self.otu_project_id}']}
        output = self.__connection(data)
        return output.get('result')

    def get_matched_addresses(self, address):
        data = {"id": 5555, "method": "get_matched_addresses", "params": [address, True]}
        output = self.__connection(data)
        result = output.get('result')
        return json.loads(result)

    def get_construction_center(self, id_address):
        data = {"id": 5555, "method": "get_construction_center", "params": [int(id_address)]}
        output = self.__connection(data)
        result = output.get('result')
        return json.loads(result)

    def set_ioc_filter(self, project_context):
        """Применение фильтра только по КК, АВ, УА, РУА"""
        data = {"id": 5555, "method": "set_ioc_filter", "params": [project_context, [258, 281, 330, 331, 332, 333], 79]}
        output = self.__connection(data)
        return output.get('result')

    def get_id_gis_objects(self, project_context, id_address):
        center = self.get_construction_center(id_address)
        lon = center.get('lon')
        lat = center.get('lat')
        offset = 0.001
        data = {"id": 5555,
                    "method": "get_gis_objects",
                    "params": [project_context, {"left": lon - offset, "right": lon + offset,
                                                 "bottom": lat - offset, "top": lat + offset}]}
        output = self.__connection(data)
        result = output.get('result')
        mounting_points = json.loads(result).get('mounting_points')
        id_gis_objects = [point.get('id') for point in mounting_points]
        return id_gis_objects

    def get_params_binded_objects(self, id_gis_objects, project_context):
        gis_objects = {}
        for id_gis_object in id_gis_objects:
            binded_objects = self.__get_binded_objects(id_gis_object, project_context)
            gis_objects.update({id_gis_object:{'name': binded_objects.get('name_with_name_attribute'),
                                                      'id_binded_object': binded_objects.get('id'),
                                                      'project_registers': binded_objects.get('projectRegisters'),
                                                      'plan_registers': binded_objects.get('planRegisters'),
                                                      'status_registers': binded_objects.get('statusRegisters')}})
        return gis_objects

    def __get_binded_objects(self, id_gis_object, project_context):
        data = {"id": 5555, "method": "get_binded_objects", "params": [id_gis_object, project_context]}
        output = self.__connection(data)
        return json.loads(output.get('result'))[0]

    def __get_query_status_registers(self, registers):
        query_status_registers = []
        for status_register in registers:
            if status_register.get('RegisterRecord'):
                record = status_register.get('RegisterRecord')
                query_status_registers.append({
                    "IsActual": True,
                    "RegisterId": record.get('RegisterId'),
                    "RegisterRecord": {"Id": record.get('Id'), "IsActual": True, "ProjectId": record.get('ProjectId')}
                })
            else:
                query_status_registers.append(
                    {"IsActual": False, "RegisterId": status_register.get('RegisterId'), "RegisterRecord": None})
        return query_status_registers


    def __get_query_project_plan_registers(self, registers):
        subquery = []
        for project_register in registers:
            if project_register.get('RegisterRecords'):
                records = project_register.get('RegisterRecords')
                query_record = []
                for record in records:
                    query_record.append(
                        {"Id": record.get('Id'), "IsActual": True, "ProjectId": record.get('ProjectId')}
                    )
                query_record.append({"Id": None, "IsActual": True, "ProjectId": self.otu_project_id})
                subquery.append({"IsActual": True, "RegisterId": project_register.get('RegisterId'),
                                 "RegisterRecords": query_record})
            elif project_register.get('RegisterName') == 'Проектируемые к реконструкции':
                subquery.append({"IsActual": True, "RegisterId": project_register.get('RegisterId'),
                                 "RegisterRecords": [{"Id": None, "IsActual": True, "ProjectId": self.otu_project_id}]})
            else:
                subquery.append(
                    {"IsActual": False, "RegisterId": project_register.get('RegisterId'), "RegisterRecords": None})
        return subquery

    def get_gis_object_by_id_node(self, id_node, project_context):
        self.set_ioc_filter(project_context)
        data = {"id": 5555, "method": "get_object_bounding_box", "params": [id_node, project_context]}
        output = self.__connection(data)
        result = output.get('result')
        id_gis_object = json.loads(result).get('ris_id')
        binded_objects = self.__get_binded_objects(id_gis_object, project_context)
        gis_object = {'name': binded_objects.get('name_with_name_attribute'),
                        'id_binded_object': binded_objects.get('id'),
                        'project_registers': binded_objects.get('projectRegisters'),
                        'plan_registers': binded_objects.get('planRegisters'),
                        'status_registers': binded_objects.get('statusRegisters')}
        return gis_object

    def get_id_node_by_name(self, data):
        url = 'https://tas.corp.itmh.ru/Node/Search'
        req = self.client.post(url, verify=False, auth=HTTPBasicAuth(self.username, self.password), data=data)
        if req.status_code == 401:
            return {'error': 'Нет доступа. Неверный логин/пароль.'}
        soup = BeautifulSoup(req.json().get('data'), "html.parser")
        search = soup.find_all('a')
        id_node_tentura = None
        for ind, i in enumerate(search[:-1]):
            next_column = ind + 1
            if i.get('href') and 'https://tentura' in i.get('href') and data['Name'] in search[next_column].text:
                id_node_tentura = i.text
        if id_node_tentura:
            return {'result': id_node_tentura}

    def get_id_address_connection_point(self, aid):
        url = f'https://sss.corp.itmh.ru/building/address_main.php?aID={aid}'
        req = self.client.get(url, verify=False, auth=HTTPBasicAuth(self.username, self.password))
        if req.status_code == 401:
            return {'error': 'Нет доступа. Неверный логин/пароль.'}
        soup = BeautifulSoup(req.content.decode('utf-8'), "html.parser")
        search = soup.find_all('a')
        address_link = [i.get('href') for i in search if i.text and i.text == 'адрес в Тентуре'][0]
        match = re.search(r'building_id=(\d+)', address_link)
        id_address = match.group(1) if match else None
        return {'result': id_address}

    def add_node(self, gis_object):
        status_registers = gis_object.get('status_registers')
        project_registers = gis_object.get('project_registers')
        plan_registers = gis_object.get('plan_registers')
        query_status_registers = self.__get_query_status_registers(status_registers)
        query_project_registers = self.__get_query_project_plan_registers(project_registers)
        query_plan_registers = self.__get_query_project_plan_registers(plan_registers)

        data = {"id": 5555,
                "method": "update_io_registers",
                "params": [gis_object.get('id_binded_object'),
                           query_status_registers,
                           query_plan_registers,
                           query_project_registers]
                }
        output = self.__connection(data)
        return output.get('result')

    def add_csp(self, id_address, address):
        center = self.get_construction_center(id_address)
        lon = center.get('lon')
        lat = center.get('lat')
        offset = round(random.random() * 0.0001 + 0.0001, 6)
        lon += offset
        lat += offset
        date_today = datetime.date.today().strftime("%d.%m.%Y")

        data = {
            "id": 5555, "method": "create_object", "params": [{
                "inventory_objects_class": 1138,
                "attributes": [
                    {"id": 2448, "name": "Помещение", "value": address, "isDirty": True, "isNullable": False},
                    {"id": 2443, "name": "Адрес", "value": address, "isDirty": True, "isNullable": False},
                    {"id": 59, "name": "Дата постройки", "value": date_today, "isDirty": True, "isNullable": False},
                    {"id": 178, "name": "Основание размещения", "value": "", "isDirty": False, "isNullable": True},
                    {"id": 31, "name": "Наименование", "value": "", "isDirty": False, "isNullable": True},
                    {"id": 34, "name": "Фотографии", "value": "", "isDirty": False, "isNullable": True},
                    {"id": 79, "name": "Владелец", "value": "ООО «Комтехцентр»", "isDirty": True, "isNullable": False},
                    {"id": 80, "name": "Примечание", "value": "", "isDirty": False, "isNullable": True},
                    {"id": 2447, "name": "ГИС: точка привязки", "value": f"POINT({lon} {lat})", "isDirty": True,
                     "isNullable": True}
                ],
                "project": {
                    "id": self.otu_project_id, "_checked": True,
                    "registers": [
                        {"r2pt": 2, "_checked": False},
                        {"r2pt": 3, "_checked": False},
                        {"r2pt": 4, "_checked": False},
                        {"r2pt": 5, "_checked": False},
                        {"r2pt": 6, "_checked": False},
                        {"r2pt": 7, "_checked": False},
                        {"r2pt": 8, "_checked": False},
                        {"r2pt": 12, "_checked": True},
                        {"r2pt": 13, "_checked": False},
                        {"r2pt": 14, "_checked": False}
                    ],
                    "checked_register": 12
                },
                "includes": []
            }]
        }
        output = self.__connection(data)
        result = output.get('result')
        return json.loads(result).get('inventoryObject').get('id')


class Specification:
    """Класс выполняет заполнение объектов спецификации ресурсами в рабочем проекте"""
    def __init__(self, username, password, otu_project_id):
        self.username = username
        self.password = password
        self.otu_project_id = otu_project_id
    def authenticate(self):
        """Данный метод выполняет авторизацию sts"""
        data_sts = {'UserName': f'CORP\\{self.username}', 'Password': f'{self.password}', 'AuthMethod': 'FormsAuthentication'}
        url = """https://arm.itmh.ru/v3/backend/manager/login/"""
        req = requests.get(url)
        sts_url = req.url
        req = requests.post(sts_url, data=data_sts)
        response = req.content.decode('utf-8')
        if 'Enter your user ID' in response:
            return {'error': 'Аутентификация не выполнена. Неверный логин/пароль.'}
        regex_wresult = """name="wresult" value="(.+TokenResponse>)"""
        result = re.search(regex_wresult, response, flags=re.DOTALL)
        wwresult = result.group(1)
        wresult = wwresult.replace('&lt;', '<').replace('&quot;', '"')
        soup = BeautifulSoup(response, "html.parser")
        wa = soup.find('input', {"name": "wa"}).get('value')
        wctx = soup.find('input', {"name": "wctx"}).get('value')
        data_arm = {'wa': wa, 'wresult': wresult, 'wctx': wctx}
        req = requests.post(url, data=data_arm)
        cookie = req.request.headers.get('Cookie')
        x_session_id = cookie.split(';')[0].strip('PHPSESSID=')
        return {'cookie': cookie, 'x_session_id': x_session_id}

    def __connection(self, cookie, data):
        """Внутренний метод, выполняющий запрос к API"""
        url = 'https://arm.itmh.ru/v3/api'
        headers = {
            'Cookie': cookie.get('cookie'),
            'X-Session-Id': cookie.get('x_session_id')
        }
        req = requests.post(url, verify=False, headers=headers, json=data)
        if req.status_code == 401:
            return {'error': 'Нет доступа. Неверный логин/пароль.'}
        return req.json()

    def get_task_id(self, cookie):
        """Метод по номеру проекта получает ID задачи"""
        data = {"app":"ARM","alias":"production","service":"ArmOopm","method":"TaskIdByProjectGet","args":{"project_id":self.otu_project_id}}
        output = self.__connection(cookie, data)
        return output.get('result', {}).get('TaskIdByProjectGet')

    def is_edited(self, task_id, cookie):
        """Метод проверяет возможность редактирования спецификации"""
        data = {"app":"ARM","alias":"production","service":"ArmOopm","method":"TaskCanBeEdited","args":{"task_id":task_id}}
        output = self.__connection(cookie, data)
        return output.get('result', {}).get('TaskCanBeEdited')

    def __extract_prices(self, output, resources):
        resource_prices = output.get('result', {}).get('ResourcePriceInfoList')
        prices = {}
        for resource in resources:
            price = [i.get('UnitPrice') for i in resource_prices if i.get('Name') == resource.get('Name')]
            if price:
                prices.update({resource.get('Name'): price[0]})
        return prices

    def get_resource_price_sku(self, cookie, resources):
        data = {"app":"ARM","alias":"production","service":"ArmOopm","method":"ResourcePriceInfoList",
                "args":{"resource_type":{"Id":1,"Name":"SKU","Code":"sku","Mem":"Образы SKU"}}}
        output = self.__connection(cookie, data)
        prices = self.__extract_prices(output, resources)
        return prices

    def get_resource_price_tao(self, cookie, resources):
        data = {"app":"ARM","alias":"production","service":"ArmOopm","method":"ResourcePriceInfoList",
                "args":{
                    "resource_type":{
                        "Id":10,"Name":"Трудовые ресурсы ТЭО","Code":"labour","Mem":"Трудовые ресурсы ТЭО"
                    }
                }}
        output = self.__connection(cookie, data)
        prices = self.__extract_prices(output, resources)
        return prices


    def extract_resource_detail(self, output, resources):
        """Метод на основе методов get_resource_list_sku и get_resource_list_tao добавляет к ресурсам, которые
         требуется добавить, параметры, полученные из БД(ID и прочее)"""
        resource_detail = output
        detailed_resources = []
        for resource in resources:
            detail = [i for i in resource_detail if i.get('Name') == resource.get('Name')]
            if detail:
                resource.update({'Resource': detail[0]})
                detailed_resources.append(resource)
        return detailed_resources

    def get_resource_list_sku(self, cookie):
        """Метод получает список всех ресурсов СКУ в БД"""
        data = {"app":"ARM","alias":"production","service":"ArmTask","method":"ResourceList",
                "args":{"resource_type":{"Code":"sku","Id":1,"Name":"SKU"},"term":""}}
        output = self.__connection(cookie, data)
        return output.get('result', {}).get('ResourceList')

    def get_resource_list_tao(self, cookie):
        """Метод получает список всех ресурсов ТЭО в БД"""
        data = {"app":"ARM","alias":"production","service":"ArmTask","method":"ResourceList",
                "args":{"resource_type":{
                            "Id":10,"Name":"Трудовые ресурсы ТЭО","Code":"labour","Mem":"Трудовые ресурсы ТЭО"},
                        "term":""}}
        output = self.__connection(cookie, data)
        return output.get('result', {}).get('ResourceList')

    def get_manager_id(self, cookie):
        """Метод получает ID пользователя, для отправления запроса, от его имени"""
        headers = {
            'Cookie': cookie.get('cookie'),
            'X-Session-Id': cookie.get('x_session_id')
        }
        url = 'https://arm.itmh.ru/v3/backend/manager/user-info/'
        req = requests.get(url, verify=False, headers=headers)
        output = req.json()
        return output.get('manager')

    def get_entity_info_list(self, cookie):
        """Метод получает данные о всех объектах спецификации со всеми существующими ресурсами"""
        task_id = self.get_task_id(cookie)
        data = {"app":"ARM","alias":"production","service":"ArmOopm","method":"SpecificationForSppDetailsGet","args":{"task_id":task_id}}
        output = self.__connection(cookie, data)
        return output.get('result', {}).get('SpecificationForSppDetailsGet', {}).get('EntityInfoList')

    def check_exist_inventory_object(self, cookie, inventory_objects, resources=False):
        """Метод проверяет наличие объектов в спецификации. Ключ resources добавляет проверку у объекта ресурсов"""
        if not inventory_objects:
            return False
        spec = self.get_entity_info_list(cookie)
        if spec is None:
            return False
        for inventory_object in inventory_objects:
            exist = [obj for obj in spec if inventory_object in obj.get('Name')]
            if not exist:
                return False
            if resources:
                exist = [obj for obj in spec if inventory_object in obj.get('Name') and obj.get('ResourceTypeList')]
                if not exist:
                    return False
        return True


    def set_resources(self, cookie, inventory_object_id, resources, update=False):
        """Метод на основе полученной информации во вспомогательных методах вызывает формирование шаблона запроса
         и добавляет ресурсы в объект спецификации"""
        kwargs = {'inventory_object_id': inventory_object_id}
        manager_id = self.get_manager_id(cookie)
        kwargs.update({'manager_id': manager_id})

        resource_list_sku = self.get_resource_list_sku(cookie)
        kwargs.update({'resource_list_sku': resource_list_sku})

        resource_list_tao = self.get_resource_list_tao(cookie)
        kwargs.update({'resource_list_tao': resource_list_tao})

        detailed_resources_sku = self.extract_resource_detail(resource_list_sku, resources)
        detailed_resources_tao = self.extract_resource_detail(resource_list_tao, resources)
        kwargs.update({'detailed_resources_sku': detailed_resources_sku})
        kwargs.update({'detailed_resources_tao': detailed_resources_tao})

        prices_sku = self.get_resource_price_sku(cookie, resources)
        prices_tao = self.get_resource_price_tao(cookie, resources)
        prices = {**prices_sku, **prices_tao}
        kwargs.update({'prices': prices})

        task_id = self.get_task_id(cookie)
        kwargs.update({'task_id': task_id})

        entity_info_list = self.get_entity_info_list(cookie)
        kwargs.update({'entity_info_list': entity_info_list})

        spec_template = SpecTemplate(**kwargs)
        data = spec_template.add_resources(update=update)
        spec_j = self.__connection(cookie, data)
        return spec_j


class TemplateSpecItem:
    """Класс содержащий позиции спецификации и их начальное количество"""
    def __init__(self):
        self.ride = {'Name': 'Выезд автомобиля В2В ВОЛС', 'Amount': 1, 'StartAmount': 1}
        self.connect_to_pps = {'Name': 'Присоединение B2B UTP', 'Amount': 1, 'StartAmount': 1}
        self.pps_rj45 = {'Name': "# [СПП] [Коннектор RJ-45 (одножильный)]", 'Amount': 1, 'StartAmount': 1}
        self.pps_copper_cable = {'Name': '# [СПП] [Кабель UTP кат.5е 2 пары (внутренний)]', 'Amount': 90,
                                 'StartAmount': 90}
        self.lvs_mount = {'Name': 'Монтаж 1 линии ЛВС от оборудования клиента', 'Amount': 1, 'StartAmount': 1}
        self.lvs_rj45 = {'Name': "# [СПП] [Коннектор RJ-45 (одножильный)]", 'Amount': 2, 'StartAmount': 2}
        self.lvs_cabel = {'Name': '# [СПП] [Кабель UTP кат.5е 2 пары (внутренний)]', 'Amount': 30,
             'StartAmount': 30}
        self.lvs_cabel_channel = {'Name': '# [СПП] [Кабель-канал 40х40мм]', 'Amount': 1,
                          'StartAmount': 1}
        self.lvs_mount_cabel_channel = {'Name': 'Монтаж кабель-канала', 'Amount': 1,
                                  'StartAmount': 1}
        self.lvs_socket = {'Name': '# [СПП] [Розетка RJ-45 1 местная]', 'Amount': 1,
                          'StartAmount': 1}
        self.lvs_patch_cord = {'Name': '# [СПП] [Патч-корд UTP кат.5e RJ-45 3.0м]', 'Amount': 1,
                           'StartAmount': 1}
        self.lvs_mount_socket = {'Name': 'Монтаж розетки RJ-45 на территории клиента (1 порт)', 'Amount': 1,
                                 'StartAmount': 1}


class BundleSpecItems:
    """Класс формирующий наборы позиций для объектов спецификации(ППС, ЦСП) на основе заголовков сформированного ТР"""
    def __init__(self, titles, stb_lines, lvs_lines, sockets, cable_channel):
        self.titles = titles
        self.stb_lines = stb_lines
        self.lvs_lines = lvs_lines
        self.sockets = sockets
        self.cable_channel = cable_channel
        self.template = TemplateSpecItem()
        self.pps_resources = {}
        self.csp_resources = {}

    def add_copper_line(self, items):
        """Метод добавляет позиции спецификации на основе заголовка медная линия"""
        for res in items:
            if self.pps_resources.get(res.get('Name')) and res == self.template.pps_rj45:
                amount = self.pps_resources.get(res.get('Name')).get('Amount')
                self.pps_resources[res.get('Name')]['Amount'] = amount + res.get('StartAmount')
                self.csp_resources[res.get('Name')]['Amount'] = amount + res.get('StartAmount')

            elif res == self.template.pps_rj45:
                self.pps_resources.update({res.get('Name'): copy.copy(res)})
                self.csp_resources.update({res.get('Name'): copy.copy(res)})


            elif self.pps_resources.get(res.get('Name')) and res not in [self.template.ride, self.template.connect_to_pps]:
                amount = self.pps_resources.get(res.get('Name')).get('Amount')
                self.pps_resources[res.get('Name')]['Amount'] = amount + res.get('StartAmount')

            else:
                self.pps_resources.update({
                    res.get('Name'): copy.copy(res)
                })

    def add_lvs_line(self, items, lines):
        """Метод добавляет позиции общие для всех линий ЛВС на основе заголовка организация СКС"""
        for res in items:
            if res == self.template.ride and self.pps_resources.get(res.get('Name')):
                continue

            elif res == self.template.ride:
                self.csp_resources.update({res.get('Name'): res})

            elif self.csp_resources.get(res.get('Name')) and res != self.template.ride:
                amount = self.csp_resources.get(res.get('Name')).get('Amount')
                self.csp_resources[res.get('Name')]['Amount'] = res.get('StartAmount') * lines + amount

            else:
                self.csp_resources.update({res.get('Name'): copy.copy(res)})
                self.csp_resources[res.get('Name')]['Amount'] = res.get('StartAmount') * lines

    def add_extra_lvs_items(self, items):
        """Метод добавляет доп. позиции, указанные пользователем на странице ЛВС"""
        for res in items:
            if self.sockets and res in [self.template.lvs_mount_socket, self.template.lvs_patch_cord]:
                self.csp_resources.update({res.get('Name'): copy.copy(res)})
                self.csp_resources[res.get('Name')]['Amount'] = res.get('StartAmount') * self.sockets

            elif self.sockets and res == self.template.lvs_socket:
                self.csp_resources.update({res.get('Name'): copy.copy(res)})
                self.csp_resources[res.get('Name')]['Amount'] = res.get('StartAmount') * self.sockets
                amount = self.csp_resources[self.template.lvs_rj45.get('Name')]['Amount']
                self.csp_resources[self.template.lvs_rj45.get('Name')]['Amount'] = amount - self.sockets

            elif self.cable_channel and res in [self.template.lvs_cabel_channel, self.template.lvs_mount_cabel_channel]:
                self.csp_resources.update({res.get('Name'): copy.copy(res)})
                self.csp_resources[res.get('Name')]['Amount'] = res.get('StartAmount') * self.cable_channel

    def find_resources(self):
        """Метод проходится по всем заголовкам ТР и вызывает соответствующие методы"""
        if self.titles:
            for title in self.titles.split('\n'):
                if "Присоединение к СПД по медной линии связи." in title:
                    items = [self.template.ride, self.template.connect_to_pps, self.template.pps_copper_cable,
                             self.template.pps_rj45]
                    self.add_copper_line(items)
                elif "Организация СКС для ЦТВ" in title:
                    items = [self.template.ride, self.template.lvs_cabel, self.template.lvs_rj45, self.template.lvs_mount]
                    self.add_lvs_line(items, self.stb_lines)
                elif "Организация СКС на" in title or "Организация ЛВС" in title:
                    items = [self.template.ride, self.template.lvs_cabel, self.template.lvs_rj45, self.template.lvs_mount]
                    self.add_lvs_line(items, self.lvs_lines)
                    items = [self.template.lvs_socket, self.template.lvs_mount_socket, self.template.lvs_patch_cord,
                             self.template.lvs_mount_cabel_channel, self.template.lvs_cabel_channel]
                    self.add_extra_lvs_items(items)

    def is_exist_resources(self):
        """Метод проверяет наличие добавляемых позиций в спецификацию"""
        if self.pps_resources or self.csp_resources:
            return True
        return False

    def get_pps_resources(self):
        """Метод возвращает набор позиций спецификации для объекта ППС"""
        return [{k:v for k,v in resource.items() if k != 'StartAmount'} for resource in self.pps_resources.values()]

    def get_csp_resources(self):
        """Метод возвращает набор позиций спецификации для объекта ЦСП"""
        return [{k: v for k, v in resource.items() if k != 'StartAmount'} for resource in self.csp_resources.values()]


class SpecTemplate:
    """Класс, формирующий структуру тела запроса для добавления ресурсов в объект спецификации. Класс позволяет
     формировать запрос как на наполнение объекта спецификации только переданными в него ресурсами, так и добавлять
      переданные ресурсы к уже существующим ресурсам. В случае, если переданный ресурс совпадает с уже существующим,
       то будет сохранен ресурс с новыми данными."""
    def __init__(self, resource_list_sku=None, resource_list_tao=None, task_id=None, manager_id=None,
                 entity_info_list=None, inventory_object_id=None, prices=None, resource_type_list=None,
                 detailed_resources_sku=None, detailed_resources_tao=None):
        self.resource_list_sku = resource_list_sku
        self.resource_list_tao = resource_list_tao
        self.task_id = task_id
        self.manager_id = manager_id
        self.entity_info_list = entity_info_list
        self.inventory_object_id = inventory_object_id
        self.prices = prices
        self.resource_type_list = resource_type_list
        self.detailed_resources_sku = detailed_resources_sku
        self.detailed_resources_tao = detailed_resources_tao


        if self.detailed_resources_sku:
            for index, resource in enumerate(self.detailed_resources_sku):
                price = self.prices.get(resource['Name'])
                del resource['Name']
                resource.update({"ItemList": [],
                                 "searchText": "",
                                 "resourceList": [],
                                 "ResourceType": {},
                                 "ResourceModel": {"Name": ""},
                                 "Price": price,
                                 "TotalCost": "0,00"})

        if self.detailed_resources_tao:
            for index, resource in enumerate(self.detailed_resources_tao):
                price = self.prices.get(resource['Name'])
                del resource['Name']
                resource.update({"ItemList": [],
                                 "searchText": "",
                                 "resourceList": [],
                                 "ResourceType": {},
                                 "ResourceModel": {"Name": ""},
                                 "Price": price,
                                 "TotalCost": "0,00"})

        self.item_list = []
        if self.detailed_resources_sku:
            self.item_list.append({"ItemList":self.detailed_resources_sku,
                                   "searchText": "",
                                   "resourceList": self.resource_list_sku,
                                   "ResourceType": {"Code": "sku", "Id": 1, "Name": "SKU"},
                                   "ResourceModel": {"Id": None, "Name": "Коннектор RJ-45"},
                                   "Amount": "",
                                   "Unit": "",
                                   "Id": 1,
                                   "Name": "SKU",
                                   "Code": "sku",
                                   "showItems": True
                                   })

        if self.detailed_resources_tao:
            self.item_list.append({"ItemList": self.detailed_resources_tao,
                                   "searchText": "",
                                   "resourceList": self.resource_list_tao,
                                   "ResourceType": {"Id": 10, "Name": "Трудовые ресурсы ТЭО", "Code": "labour",
                                                    "Mem": "Трудовые ресурсы ТЭО"},
                                   "ResourceModel": {"Id": None, "Name": "Выезд автомобиля В2В ВОЛС"},
                                   "Amount": "",
                                   "Unit": "",
                                   "Code": "labour",
                                   "Id": 10,
                                   "Name": "Трудовые ресурсы ТЭО"
                                   })

    def __update_changed_entity(self):
        """Метод встраивает в структуру запроса существующие ресурсы в объекте спецификации при выборе обновления
         ресурсов объекта спецификации"""
        exist_resources_sku = []
        exist_resources_tao = []
        entity = [i for i in self.entity_info_list if i.get('InventoryObjectId') == self.inventory_object_id][0]
        resources_sku_list = [i.get('ItemList') for i in entity.get('ResourceTypeList') if i.get('Code') == "sku"]
        if resources_sku_list:
            exist_resources_sku = resources_sku_list[0]
        resources_tao_list = [i.get('ItemList') for i in entity.get('ResourceTypeList') if i.get('Code') == "labour"]
        if resources_tao_list:
            exist_resources_tao = resources_tao_list[0]
        for resource in exist_resources_sku:
            resource.update({
                "ItemList": [], "searchText": "", "resourceList": [], "ResourceType": {}, "ResourceModel": {"Name": ""},
                "list": [{}, {}, {}, {}], "specObjects":[{"Name":entity.get('Name'),
                                                          "Id":entity.get('Id'),
                                                          "InventoryObjectId":entity.get('InventoryObjectId'),
                                                          "objAmount":resource.get('Amount')}],
            })
        for resource in exist_resources_tao:
            resource.update({
                "ItemList": [], "searchText": "", "resourceList": [], "ResourceType": {}, "ResourceModel": {"Name": ""},
                "list": [{}, {}, {}, {}], "specObjects":[{"Name":entity.get('Name'),
                                                          "Id":entity.get('Id'),
                                                          "InventoryObjectId":entity.get('InventoryObjectId'),
                                                          "objAmount":resource.get('Amount')}],
            })
        if exist_resources_sku:
            item = [i for i in self.item_list if i.get("Code") == "sku"]
            if not item:
                self.item_list.append({"ItemList": [],
                                       "searchText": "",
                                       "resourceList": self.resource_list_sku,
                                       "ResourceType": {"Code": "sku", "Id": 1, "Name": "SKU"},
                                       "ResourceModel": {"Id": None, "Name": "Коннектор RJ-45"},
                                       "Amount": "",
                                       "Unit": "",
                                       "Id": 1,
                                       "Name": "SKU",
                                       "Code": "sku",
                                       "showItems": True
                                       })

        if exist_resources_tao:
            item = [i for i in self.item_list if i.get("Code") == "labour"]
            if not item:
                self.item_list.append({"ItemList": [],
                                       "searchText": "",
                                       "resourceList": self.resource_list_tao,
                                       "ResourceType": {"Id": 10, "Name": "Трудовые ресурсы ТЭО", "Code": "labour",
                                                        "Mem": "Трудовые ресурсы ТЭО"},
                                       "ResourceModel": {"Id": None, "Name": "Выезд автомобиля В2В ВОЛС"},
                                       "Amount": "",
                                       "Unit": "",
                                       "Code": "labour",
                                       "Id": 10,
                                       "Name": "Трудовые ресурсы ТЭО"
                                       })

        for i in self.item_list:
            if i.get('ResourceType') == {"Code": "sku", "Id": 1, "Name": "SKU"} and exist_resources_sku:
                for exist_res in exist_resources_sku:
                    if not [new_res for new_res in i.get('ItemList') if
                            new_res.get('Resource').get('Name') == exist_res.get('Resource').get('Name')]:
                        i.get('ItemList').append(exist_res)
            if i.get('ResourceType') == {"Id": 10, "Name": "Трудовые ресурсы ТЭО", "Code": "labour",
                                                    "Mem": "Трудовые ресурсы ТЭО"} and exist_resources_tao:
                for exist_res in exist_resources_tao:
                    if not [new_res for new_res in i.get('ItemList') if
                            new_res.get('Resource').get('Name') == exist_res.get('Resource').get('Name')]:
                        i.get('ItemList').append(exist_res)

    def add_resources(self, update=False):
        entity_new = [i for i in self.entity_info_list if i.get('InventoryObjectId') == self.inventory_object_id][0]
        if update:
            self.__update_changed_entity()
        self.entity_info_list.remove(entity_new)

        data = {"app": "ARM",
                "alias": "production",
                "service": "ArmTask",
                "method": "SpecificationDetailsSet",
                "args": {
                    "entity_info_list":  [{
                        "Id": entity_new.get('Id'),
                        "InventoryObjectId": self.inventory_object_id,
                        "Name": entity_new.get('Name'),
                        "ResourceTypeList": self.item_list,
                        "showItems": True,
                        "Open": False,
                        "template": {"model": {"Name": "Создать вручную"}},
                        "isSpecInvalid": False,
                        "_template": {"Name": "Создать вручную"}
                    },
                     ] + self.entity_info_list, #}
                    "task_id": self.task_id,
                    "manager_id": self.manager_id
                }}
        return data


def get_specication_resources(session_tr_id):
    titles = session_tr_id.get('titles')
    lvs_lines = session_tr_id.get('local_ports')
    stb_lines = session_tr_id.get('cnt_itv') if session_tr_id.get('need_line_itv') is True else None
    sockets = session_tr_id.get('local_socket') if session_tr_id.get('local_socket_need') is True else None
    cable_channel = None
    if session_tr_id.get('local_type') and 'business' in session_tr_id.get('local_type'):
        cable_channel = session_tr_id.get('local_cable_channel')
    bundle = BundleSpecItems(titles, stb_lines, lvs_lines, sockets, cable_channel)
    bundle.find_resources()
    spec_button = bundle.is_exist_resources()
    pps_resources = bundle.get_pps_resources()
    csp_resources = bundle.get_csp_resources()
    return {'spec_button': spec_button, 'pps_resources':pps_resources, 'csp_resources': csp_resources}