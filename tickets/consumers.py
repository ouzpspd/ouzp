import json
import logging
from channels.generic.websocket import AsyncWebsocketConsumer
from asgiref.sync import sync_to_async

from tickets.switch import Connect, SwitchException
from tickets.utils import sql_request_cordis

logger = logging.getLogger(__name__)

query = """
SELECT DISTINCT s.name, Nets.IpDigitToCanon(s.ip_address)
FROM nets.switch s
JOIN Nets.switch_model sm ON s.switch_model = sm.switch_model
WHERE sm.vendor = 'cisco'
AND NOT (sm.model = 'ASR 9001' OR sm.model = '7204VXR-DC' OR sm.model = 'Catalyst 6500')
AND s.enabled = 1
AND (s.name LIKE 'AR%' OR s.name LIKE 'SR%')
AND NOT s.name LIKE '%FAKE%' ORDER BY s.name
"""


class ComponentsConsumer(AsyncWebsocketConsumer):

    @sync_to_async
    def get_switches(self, territory):
        switches = sql_request_cordis(query)
        ip_switches = [ip for name, ip in switches if name.endswith(territory)]
        return ip_switches

    @sync_to_async
    def connect_switches(self, ip_switches, table, summary):
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
        return table, summary

    async def receive(self, text_data):
        response = {}
        table = []
        summary = {}
        text_data_json = json.loads(text_data)
        territory = text_data_json['territory']
        ip_switches = await self.get_switches(territory)
        try:
            table, summary = await self.connect_switches(ip_switches, table, summary)
            response.update({'data': table, 'summary': summary, 'territory': territory})
        except SwitchException as er:
            logger.error(er)
            response.update({"error": f"Выполнение прервано. Произошла ошибка. {er}"})
        except Exception as er:
            logger.error(er)
            raise er
        await self.send(text_data=json.dumps(response))
