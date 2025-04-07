import json
import logging
from channels.generic.websocket import WebsocketConsumer
from tickets.switch import Connect, SwitchException
from tickets.parsing import parsing_switches_by_model
from tickets.utils import get_user_credential_cordis

logger = logging.getLogger(__name__)

class ComponentsConsumer(WebsocketConsumer):
    def connect(self):
        self.user = self.scope["user"]
        self.accept()

    def disconnect(self, close_code):
        pass

    def receive(self, text_data):
        response = {}
        table = []
        summary = {}
        text_data_json = json.loads(text_data)
        territory = text_data_json['territory']
        username, password = get_user_credential_cordis(self.user)
        switches = parsing_switches_by_model('Cisco Catalyst 6', username, password)

        ip_switches = [v for k,v in switches.items() if k.endswith(territory)]
        try:
            for ip in ip_switches:
                with Connect(ip) as session:
                    switch_table = session.get_components_table()
                    table += switch_table
                    switch_summary = session.get_components_summary()
                    for i in switch_summary:
                        if summary.get(i):
                            summary[i] += 1
                        else:
                            summary.update({i: 1})
            response.update({'data': table, 'summary': summary, 'territory': territory})
        except SwitchException as er:
            logger.exception(er)
            response.update({"error": f"Выполнение прервано. Произошла ошибка. {er}"})
        except Exception as er:
            logger.exception(er)
            raise er
        self.send(text_data=json.dumps(response))
