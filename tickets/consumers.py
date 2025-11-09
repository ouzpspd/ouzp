import asyncio
import json
import logging
from channels.generic.websocket import AsyncWebsocketConsumer
from asgiref.sync import sync_to_async
from typing import List, Tuple

from tickets.switch import Connect, SwitchException, InputSwitchException, WarningSwitchException
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
	def get_switches(self, territory: str):
		switches = sql_request_cordis(query_cisco_ar_sr)
		territory_switches = [(name, ip, vendor, model) for name, ip, vendor, model in switches if name.endswith(territory)]
		return territory_switches

	@sync_to_async
	def connect_switches(self, switches: List[Tuple[str, str, str, str]]):
		table = []
		summary = {}
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
		text_data_json = json.loads(text_data)
		territory = text_data_json['territory']
		switches = await self.get_switches(territory)
		try:
			table, summary = await self.connect_switches(switches)
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
	def recognise_switches(input_switches: set, switches: List[Tuple[str, str, str, str]]):
		if not input_switches:
			raise InputSwitchException("Необходимо ввести название АМ/КПА")
		is_not_ar_ias = [line for line in input_switches if not (line.startswith("AR") or line.startswith("IAS"))]
		if is_not_ar_ias:
			raise InputSwitchException("Поиск выполняется только по АМ/КПА")
		recognised_switches = [(name, ip, vendor, model) for name, ip, vendor, model in switches if name in input_switches]
		recognised_names = [name for name, *other in recognised_switches]
		if not recognised_names or len(input_switches) != len(recognised_names):
			unrecognized_names = input_switches - set(recognised_names)
			raise InputSwitchException(f"Не удалось распознать {', '.join(unrecognized_names)}")
		return recognised_switches

	async def receive(self, text_data):
		text_data_json = json.loads(text_data)
		action = text_data_json['action']
		input_data = text_data_json['switches']
		input_switches = set([line for line in input_data.split(";") if line])
		switches_in_db = await self.get_switches()
		try:
			switches = self.recognise_switches(input_switches, switches_in_db)
		except InputSwitchException as er:
			logger.error(er)
			await self.send(json.dumps({
				'type': 'error',
				'message': f"Выполнение прервано. {er}."
			}))
		else:
			asyncio.create_task(self.process_and_send_messages(switches, action))

	@sync_to_async
	def connect_switches(self, switch: Tuple[str, str, str, str], action: str, response):
		name, ip, vendor, model = switch
		message = f'{name}:'
		status = 'success'
		try:
			with Connect(name, ip, vendor, model) as session:
				if action == 'add':
					sw, error_ports, changed_ports = session.add_rezerv_1g_planning()
					if changed_ports:
						message += f' Успешно зарезервированы порты {changed_ports}.'
					if error_ports:
						message += f' Внимание! Обратить внимание незапланированно изменились порты {error_ports}.'
						status = 'warning'
					response.update({sw.strip(): {"message": message, "status": status}})
				elif action == 'remove':
					sw, error_ports, changed_ports, = session.remove_rezerv_1g_planning()
					if changed_ports:
						message += f' Успешно снят резерв портов {changed_ports}.'
					if error_ports:
						message += f' Внимание! Обратить внимание незапланированно изменились порты {error_ports}.'
						status = 'warning'
					response.update({sw.strip(): {"message": message, "status": status}})
				elif action == 'show':
					sw, params = session.get_interfaces_summary()
					message += " Данные получены."
					response.update({sw.strip(): {"params": params, "message":message, "status": status}})
		except WarningSwitchException as er:
			status = 'warning'
			message += f" {er}"
			response.update({name: {"message": message, "status": status}})
		except SwitchException as er:
			logger.error(f"{name}, {ip}. {er}")
			status = 'error'
			message += f" {er}"
			response.update({name: {"message": message, "status": status}})
		except Exception as er:
			logger.error(f"{name}, {ip}. {er}")
			status = 'error'
			message += f" {er}"
			response.update({name: {"message": message, "status": status}})
			raise er
		finally:
			return name

	async def process_and_send_messages(self, switches: List[Tuple[str, str, str, str]], action: str):
		response = {}
		try:
			await self.send(json.dumps({
				'type': 'status',
				'message': 'Начинаем обработку...',
				'progress': 0
			}))

			for i, sw in enumerate(switches):
				sw_name = await self.connect_switches(sw, action, response)
				progress = int((i + 1) / len(switches) * 100)
				res = {
					'action': action,
					'type': response[sw_name]['status'],
					'message': response[sw_name]['message'],
					'progress': progress,
				}
				await self.send(json.dumps(res))

			final = {
				'action': action,
				'type': 'complete',
				'message': 'Обработка завершена.',
				'progress': 100,
			}
			if action == 'show':
				data = {k:v.get('params') for k,v in response.items() if v.get('params')}
				final.update({'data': data})
			await self.send(json.dumps(final))

		except Exception as e:
			await self.send(json.dumps({
				'type': 'error',
				'message': f'Произошла ошибка: {str(e)}'
			}))
