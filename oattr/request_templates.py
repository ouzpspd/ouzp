
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

    def __update_changed_entity(self):

        resources_sku = []
        resources_tao = []
        entity = [i for i in self.entity_info_list if i.get('InventoryObjectId') == self.inventory_object_id][0]
        resources_sku_list = [i.get('ItemList') for i in entity.get('ResourceTypeList') if i.get('Code') == "sku"]
        if resources_sku_list:
            resources_sku = resources_sku_list[0]
        resources_tao_list = [i.get('ItemList') for i in entity.get('ResourceTypeList') if i.get('Code') == "labour"]
        if resources_tao_list:
            resources_tao = resources_tao_list[0]
        for resource in resources_sku:
            resource.update({
                "ItemList": [], "searchText": "", "resourceList": [], "ResourceType": {}, "ResourceModel": {"Name": ""},
                "list": [{}, {}, {}, {}], "specObjects":[{"Name":entity.get('Name'),
                                                          "Id":entity.get('Id'),
                                                          "InventoryObjectId":entity.get('InventoryObjectId'),
                                                          "objAmount":resource.get('Amount')}],
            })
        for resource in resources_tao:
            resource.update({
                "ItemList": [], "searchText": "", "resourceList": [], "ResourceType": {}, "ResourceModel": {"Name": ""},
                "list": [{}, {}, {}, {}], "specObjects":[{"Name":entity.get('Name'),
                                                          "Id":entity.get('Id'),
                                                          "InventoryObjectId":entity.get('InventoryObjectId'),
                                                          "objAmount":resource.get('Amount')}],
            })
        if resources_sku:
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

        if resources_tao:
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
            if i.get('ResourceType') == {"Code": "sku", "Id": 1, "Name": "SKU"} and resources_sku:
                for res in resources_sku:
                    if not [new_res for new_res in i.get('ItemList') if
                            new_res.get('Resource').get('Name') == res.get('Resource').get('Name')]:
                        i.get('ItemList').append(res)
            if i.get('ResourceType') == {"Id": 10, "Name": "Трудовые ресурсы ТЭО", "Code": "labour",
                                                    "Mem": "Трудовые ресурсы ТЭО"} and resources_tao:
                for res in resources_tao:
                    if not [new_res for new_res in i.get('ItemList') if
                            new_res.get('Resource').get('Name') == res.get('Resource').get('Name')]:
                        i.get('ItemList').append(res)

    def spec(self, update=False):
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

    # def csp(self):
    #     entity = [i for i in self.entity_info_list if i.get('InventoryObjectId') == self.inventory_object_id][0]
    #     data = {"app": "ARM",
    #             "alias": "production",
    #             "service": "ArmTask",
    #             "method": "SpecificationDetailsSet",
    #             "args": {
    #                 "entity_info_list": [{
    #                     "Id": entity.get('Id'),  # 104563,
    #                     "InventoryObjectId": self.inventory_object_id,  # 128874,
    #                     "Name": entity.get('Name'),  # "2.4.2.Цифровая сеть потребителя (#128874)",
    #                     "ResourceTypeList": [
    #                         { "ItemList": [
    #
    #                             {"ItemList": [],
    #                              "searchText": "",
    #                              "resourceList": [],
    #                              "ResourceType": {},
    #                              "ResourceModel": {"Name": ""},
    #                              "Amount": 1,
    #                              "Unit": "/шт",
    #                              "TotalCost": "0,00",
    #                              "Resource": {
    #                                  "Id": 87355,
    #                                  "Name": "# [СПП] [Коннектор RJ-45 (одножильный)]",
    #                                  "ResourceType": {"Id": 1, "Name": "SKU", "Code": "sku"},
    #                                  "UnitOfMeasurement": {"Id": 22, "Name": "штука", "Symbol": "шт", "IsUsed": None},
    #                                  "FullName": "# [СПП] [Коннектор RJ-45 (одножильный)], [штука]"},
    #                              "Price": self.prices.get('# [СПП] [Коннектор RJ-45 (одножильный)]')}],  # 51.45
    #                             "searchText": "",
    #                             "resourceList": self.resource_list_sku,
    #                             "ResourceType": {"Code": "sku", "Id": 1, "Name": "SKU"},
    #                             "ResourceModel": {"Id": None, "Name": "Коннектор RJ-45"},
    #                             "Amount": "",
    #                             "Unit": "",
    #                             "Id": 1,
    #                             "Name": "SKU",
    #                             "Code": "sku",
    #                             "showItems": True}  #,
    #
    #                     ],
    #                     "showItems": True,
    #                     "Open": False,
    #                     "template": {"model": {"Name": "Создать вручную"}},
    #                     "isSpecInvalid": False,
    #                     "_template": {"Name": "Создать вручную"}
    #                 }
    #                 ],
    #                 "task_id": self.task_id,
    #                 "manager_id": self.manager_id
    #             }
    #             }
    #     return data