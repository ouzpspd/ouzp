import json
import logging
from channels.generic.websocket import AsyncWebsocketConsumer
from asgiref.sync import sync_to_async

from tickets.switch import Connect, SwitchException, InputSwitchException
from tickets.utils import sql_request_cordis

logger = logging.getLogger(__name__)

query_cisco_ar_sr = """
SELECT DISTINCT s.name, Nets.IpDigitToCanon(s.ip_address), sm.vendor, sm.model
FROM nets.switch s
JOIN Nets.switch_model sm ON s.switch_model = sm.switch_model
WHERE sm.vendor = 'cisco'
AND NOT (sm.model = 'ASR 9001' OR sm.model = '7204VXR-DC' OR sm.model = 'Catalyst 6500')
AND s.enabled = 1
AND (s.name LIKE 'AR%' OR s.name LIKE 'SR%')
AND NOT s.name LIKE '%FAKE%' ORDER BY s.name
"""

query_ar_cisco_ias_snr = """
SELECT DISTINCT s.name, Nets.IpDigitToCanon(s.ip_address), sm.vendor, sm.model
FROM nets.switch s
JOIN Nets.switch_model sm ON s.switch_model = sm.switch_model
WHERE (sm.vendor = 'cisco' OR sm.vendor = 'snr')
AND NOT (sm.model = 'ASR 9001' OR sm.model = '7204VXR-DC' OR sm.model = 'Catalyst 6500')
AND s.enabled = 1
AND (s.name LIKE 'AR%' OR s.name LIKE 'IAS%')
AND NOT s.name LIKE '%FAKE%' ORDER BY s.name
"""

class ComponentsConsumer(AsyncWebsocketConsumer):

	@sync_to_async
	def get_switches(self, territory):
		switches = sql_request_cordis(query_cisco_ar_sr)
		territory_switches = [(name, ip, vendor, model) for name, ip, vendor, model in switches if name.endswith(territory)]
		return territory_switches

	@sync_to_async
	def connect_switches(self, switches, table, summary):
		for switch in switches:
			with Connect(*switch) as session:
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


class ReservePortsConsumer(AsyncWebsocketConsumer):
	@sync_to_async
	def get_switches(self):
		switches = sql_request_cordis(query_ar_cisco_ias_snr)
		return switches

	@staticmethod
	def recognise_switches(input_switches, switches):
		if not input_switches:
			raise InputSwitchException("Необходимо ввести название АМ/КПА")
		is_not_ar_ias = [line for line in input_switches if not (line.startswith("AR") or line.startswith("IAS"))]
		if is_not_ar_ias:
			raise InputSwitchException("Поиск выполняется только по АМ/КПА")
		recognised_switches = [(name, ip, vendor, model) for name, ip, vendor, model in switches if name in input_switches]
		recognised_names = [name for name, *other in recognised_switches]
		if not recognised_names or len(input_switches) != len(recognised_names):
			unrecognized_names = input_switches - recognised_names
			raise InputSwitchException(f"Не удалось распознать {', '.join(unrecognized_names)}")
		return recognised_switches

	@sync_to_async
	def connect_switches(self, switches, action):
		response = {'action': action}
		for name, ip, vendor, model in switches:
			try:
				with Connect(name, ip, vendor, model) as session:
					if action == 'add':
						sw, error_ports, changed_ports = session.add_rezerv_1g_planning()
						response.update({sw: {"error_ports": error_ports, "changed_ports": changed_ports}})
					elif action == 'remove':
						sw, error_ports, changed_ports, = session.remove_rezerv_1g_planning()
						response.update({sw: {"error_ports": error_ports, "changed_ports": changed_ports}})
					elif action == 'show':
						sw, params = session.get_interfaces_summary()
						response.update({sw: params})
			except SwitchException as er:
				logger.error(f"{name}, {ip}. {er}")
				response.update({name: {"error_switch": f"{er}"}})
			except Exception as er:
				logger.error(f"{name}, {ip}. {er}")
				response.update({name: {"error_switch": f"{er}"}})
				raise er
		return response

	async def receive(self, text_data):
		text_data_json = json.loads(text_data)
		action = text_data_json['action']
		input_data = text_data_json['switches']
		input_switches = list(set([line for line in input_data.split(";") if line]))
		switches_in_db = await self.get_switches()
		try:
			switches = self.recognise_switches(input_switches, switches_in_db)
		except InputSwitchException as er:
			logger.error(er)
			response = {"error": f"Выполнение прервано. {er}.", 'action': action}
		else:
			response = await self.connect_switches(switches, action)
		await self.send(text_data=json.dumps(response))