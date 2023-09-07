
class SpecTemplate:
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
                del resource['Name']
                resource.update({"ItemList": [],
                                 "searchText": "",
                                 "resourceList": [],
                                 "ResourceType": {},
                                 "ResourceModel": {"Name": ""},
                                 "TotalCost": "0,00"})

        if self.detailed_resources_tao:
            for index, resource in enumerate(self.detailed_resources_tao):
                del resource['Name']
                resource.update({"ItemList": [],
                                 "searchText": "",
                                 "resourceList": [],
                                 "ResourceType": {},
                                 "ResourceModel": {"Name": ""},
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

    def pps(self):
        entity_new = [i for i in self.entity_info_list if i.get('InventoryObjectId') == self.inventory_object_id][0]
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

    def csp(self):
        entity = [i for i in self.entity_info_list if i.get('InventoryObjectId') == self.inventory_object_id][0]
        data = {"app": "ARM",
                "alias": "production",
                "service": "ArmTask",
                "method": "SpecificationDetailsSet",
                "args": {
                    "entity_info_list": [{
                        "Id": entity.get('Id'),  # 104563,
                        "InventoryObjectId": self.inventory_object_id,  # 128874,
                        "Name": entity.get('Name'),  # "2.4.2.Цифровая сеть потребителя (#128874)",
                        "ResourceTypeList": [
                            { "ItemList": [

                                {"ItemList": [],
                                 "searchText": "",
                                 "resourceList": [],
                                 "ResourceType": {},
                                 "ResourceModel": {"Name": ""},
                                 "Amount": 1,
                                 "Unit": "/шт",
                                 "TotalCost": "0,00",
                                 "Resource": {
                                     "Id": 87355,
                                     "Name": "# [СПП] [Коннектор RJ-45 (одножильный)]",
                                     "ResourceType": {"Id": 1, "Name": "SKU", "Code": "sku"},
                                     "UnitOfMeasurement": {"Id": 22, "Name": "штука", "Symbol": "шт", "IsUsed": None},
                                     "FullName": "# [СПП] [Коннектор RJ-45 (одножильный)], [штука]"},
                                 "Price": self.prices.get('# [СПП] [Коннектор RJ-45 (одножильный)]')}],  # 51.45
                                "searchText": "",
                                "resourceList": self.resource_list_sku,
                                "ResourceType": {"Code": "sku", "Id": 1, "Name": "SKU"},
                                "ResourceModel": {"Id": None, "Name": "Коннектор RJ-45"},
                                "Amount": "",
                                "Unit": "",
                                "Id": 1,
                                "Name": "SKU",
                                "Code": "sku",
                                "showItems": True}  #,

                        ],
                        "showItems": True,
                        "Open": False,
                        "template": {"model": {"Name": "Создать вручную"}},
                        "isSpecInvalid": False,
                        "_template": {"Name": "Создать вручную"}
                    }
                    ],
                    "task_id": self.task_id,
                    "manager_id": self.manager_id
                }
                }
        return data