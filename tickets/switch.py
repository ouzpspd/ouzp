import pexpect
import re
from copy import deepcopy

from django.conf import settings

from tickets.parsing import get_switch_ip


class SwitchException(Exception):
    pass

class InputSwitchException(Exception):
    pass


class Connect:
    def __init__(self, ip: str):
        self.session = None
        self.city_prompt = "[ekb|ntg|kur]"
        self.enable = "qq"
        self.ip = ip
        ip_pattern = re.search('(192|212)\.\d{1,3}\.\d{1,3}\.\d{1,3}', ip)
        if ip_pattern and ip_pattern.group(1) == '192':
            self.switch = Snr()
        elif ip_pattern and ip_pattern.group(1) == '212':
            self.switch = Cisco()


    def __enter__(self):
        try:
            self.session = pexpect.spawn(f"telnet {self.ip}", timeout=10, encoding="utf-8")
            login = self.session.expect(["Password", "login", "Username"])
            if login:
                self.session.sendline(self.switch.username)
                self.session.expect("Password")
            self.session.sendline(self.switch.password)
            enable_status = self.session.expect([">", "#", "Password"])
            if enable_status == 0:
                self.session.sendline("enable")
                self.session.expect("[Pp]assword")
                self.session.sendline(self.enable)
                self.session.expect(self.city_prompt + "#")
            elif enable_status == 2:
                raise SwitchException(f"Не удалось залогиниться на {self.ip}")
            pre_name = self.session.before + self.session.after
            self.switch.name = pre_name.strip(":\r\n#")
        except pexpect.TIMEOUT:
            raise SwitchException(f"Не удалось подключиться к {self.ip}")
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.session.close()
        self.session = None

    def get_switch_interfaces(self):
        output = {}
        commands = self.switch.show_ports_command()
        for command in commands:
            output[command[0]] = self.send_command(*command)
        self.switch.interfaces = self.switch.show_ports_output(output)
        return self.switch.interfaces

    def get_switch_components(self):
        output = {}
        commands = self.switch.show_components_command()
        for command in commands:
            output[command[0]] = self.send_command(*command)
        self.switch.show_components_output(output)

    def get_components_table(self):
        if not self.switch.components:
            self.get_switch_components()
        return self.switch.construct_components_table()

    def get_components_summary(self):
        if not self.switch.components:
            self.get_switch_components()
        return self.switch.construct_components_summary()

    def get_interfaces_summary(self):
        self.get_switch_interfaces()
        summary = {}
        summary.update({"rezerv_1g": len(self.switch.get_interfaces_1g_rezerv())})
        summary.update({"rezerv_1g_planning": len(self.switch.get_interfaces_1g_rezerv_planning())})
        summary.update({"rezerv_dir2_4_4": len(self.switch.get_interfaces_1g_rezerv_dir2_4_4())})
        summary.update({"no_description_1g": len(self.switch.get_interfaces_1g_no_description())})
        summary.update({"no_description_10g": len(self.switch.get_interfaces_10g_no_description())})
        summary.update({
            "other_rezerv_1g": [f"{k} - {v['Desc']}" for k, v in self.switch.get_interfaces_1g_other_rezerv().items()]
        })
        summary.update({
            "other_rezerv_10g": [f"{k} - {v['Desc']}" for k, v in self.switch.get_interfaces_10g_other_rezerv().items()]
        })
        summary.update({
            "with_desc_no_link_1g": [f"{k} - {v['Desc']}" for k, v in self.switch.get_interfaces_1g_with_desc_no_link().items()]
        })
        summary.update({
            "with_desc_no_link_10g": [f"{k} - {v['Desc']}" for k, v in self.switch.get_interfaces_10g_with_desc_no_link().items()]
        })

        return self.switch.name, summary

    def remove_rezerv_1g_planning(self):
        self.get_switch_interfaces()
        before = deepcopy(self.switch.interfaces)
        changing = self.switch.get_interfaces_1g_rezerv_planning()
        output = {}
        commands = self.switch.remove_rezerv_1g_planning_command()
        for command in commands:
            output[command[0]] = self.send_command(*command)
        after = self.get_switch_interfaces()
        changed = {
            p: v for p in before.keys() for k, v in after[p].items() if k == 'Desc' and before[p][k] != after[p][k]
        }
        error_ports = set(changed.keys()) - set(changing.keys())
        return self.switch.name, ", ".join(list(error_ports)), ", ".join(list(changing.keys()))

    def add_rezerv_1g_planning(self):
        self.get_switch_interfaces()
        before = deepcopy(self.switch.interfaces)
        changing = self.switch.get_interfaces_1g_no_description()
        output = {}
        commands = self.switch.add_rezerv_1g_planning_command()
        for command in commands:
            output[command[0]] = self.send_command(*command)
        after = self.get_switch_interfaces()
        changed = {
            p: v for p in before.keys() for k, v in after[p].items() if k == 'Desc' and before[p][k] != after[p][k]
        }
        error_ports = set(changed.keys()) - set(changing.keys())
        return self.switch.name, ", ".join(list(error_ports)), ", ".join(list(changing.keys()))

    def send_command(self, command, prompt="#"):
        self.session.sendline(command)
        output = ""
        while True:
            match = self.session.expect([self.city_prompt+prompt, "--More--", pexpect.TIMEOUT])
            page = self.session.before.replace("\r\n", "\n").replace("\x08", "")

            output += page
            if match == 0:
                break
            elif match == 1:
                self.session.send(" ")
            else:
                raise SwitchException(f"Не удалось выполнить команду: {command} on {self.switch.name}")
        return output


class Snr:
    def __init__(self):
        self.username = settings.SWITCH_KPA_SNR_USER
        self.password = settings.SWITCH_KPA_SNR_PASSWORD
        self.model = 'snr'
        self.name = None
        self.interfaces = None

    @staticmethod
    def show_ports_command():
        commands = [("sh int e s",)]
        return commands

    @staticmethod
    def show_ports_output(output):
        interfaces = {}
        command_output = output["sh int e s"]
        output = command_output.split("\n")
        clear_output = output[4:-1]
        keys = ["Status", "Type", "Desc"]
        for line in clear_output:
            regex = " *(\S+) +(\S+) +\S+ +\S+ +\S+ +(\S+) +([\S| ]+| )"
            match = re.match(regex, line)
            data = match.groups()
            interfaces.update({data[0]: dict(zip(keys, data[1:]))})
        return interfaces

    @staticmethod
    def _get_range_ports(interfaces):
        regex = "(\d\/\d|\d)\/(\d{1,2})"
        data = []
        prefix_port = None
        for interface in interfaces.keys():
            match = re.match(regex, interface)
            port = match.group(2) if match else None
            prefix_port = match.group(1)
            data.append(int(port))
        starts = [x for x in data if x - 1 not in data and x + 1 in data]
        ends = [x for x in data if x - 1 in data and x + 1 not in data and x not in starts]
        singles = [str(x) for x in data if x - 1 not in data and x + 1 not in data]
        ranges = list(zip(starts, ends))
        str_ranges = [f'{i[0]}-{i[1]}' for i in ranges]
        result_ranges = str_ranges + singles
        res_ranges = f";".join(result_ranges) if result_ranges else ""
        return prefix_port, res_ranges


    def remove_rezerv_1g_planning_command(self):
        interfaces = self.get_interfaces_1g_rezerv_planning()
        prefix_port, range_ports = self._get_range_ports(interfaces)
        if not range_ports:
            raise SwitchException(f"{self.name}: нет портов Rezerv_1G_planning.")
        if any(i in range_ports for i in [";", "-"]):
            prompt_port = f"\(config-if-port-range\)#"
        else:
            prompt_port = f"\(config-if-ethernet{prefix_port}/{range_ports}\)#"
        commands = [
            ("conf t", "\(config\)#"),
            (f"int e{prefix_port}/{range_ports}", prompt_port),
            ("no description", prompt_port),
            ("exit", "\(config\)#"),
            ("exit",),
        ]
        return commands

    def add_rezerv_1g_planning_command(self):
        interfaces = self.get_interfaces_1g_no_description()
        prefix_port, range_ports = self._get_range_ports(interfaces)
        if not range_ports:
            raise SwitchException(f"{self.name}: нет портов 1G без description.")
        if any(i in range_ports for i in [";", "-"]):
            prompt_port = f"\(config-if-port-range\)#"
        else:
            prompt_port = f"\(config-if-ethernet{prefix_port}/{range_ports}\)#"
        commands = [
            ("conf t", "\(config\)#"),
            (f"int e{prefix_port}/{range_ports}", prompt_port),
            ("description Rezerv_1G_planning", prompt_port),
            ("exit", "\(config\)#"),
            ("exit",),
        ]
        return commands

    def _get_interfaces_1g(self):
        sfp = ["G-Combo", "SFP"]
        if self.interfaces:
            return {k: v for k, v in self.interfaces.items() if any(i for i in sfp if i in v["Type"]) and "SFP+" not in v["Type"]}

    def _get_interfaces_10g(self):
        if self.interfaces:
            return {k: v for k, v in self.interfaces.items() if any(i for i in ["SFP+"] if i in v["Type"])}

    def get_interfaces_1g_rezerv(self):
        int_1g = self._get_interfaces_1g()
        return {k: v for k, v in int_1g.items() if v["Desc"] == "Rezerv_1G"}

    def get_interfaces_1g_rezerv_planning(self):
        int_1g = self._get_interfaces_1g()
        return {k: v for k, v in int_1g.items() if v["Desc"] == "Rezerv_1G_planning"}

    def get_interfaces_1g_rezerv_dir2_4_4(self):
        int_1g = self._get_interfaces_1g()
        return {k: v for k, v in int_1g.items() if v["Desc"] == "Rezerv_DIR.I2.4.4"}

    def get_interfaces_1g_other_rezerv(self):
        int_1g = self._get_interfaces_1g()
        reserves = ["Rezerv_1G", "Rezerv_1G_planning", "Rezerv_DIR.I2.4.4"]
        return {k: v for k, v in int_1g.items() if "rezerv" in v["Desc"].lower() and v["Desc"] not in reserves}

    def get_interfaces_1g_with_desc_no_link(self):
        with_desc_no_link = {}
        int_1g = self._get_interfaces_1g()
        for k, v in int_1g.items():
            if "rezerv" not in v["Desc"].lower() and v["Desc"] != " " and v["Status"] == "A-DOWN/DOWN":
                with_desc_no_link.update({k: v})
        return with_desc_no_link

    def get_interfaces_1g_no_description(self):
        int_1g = self._get_interfaces_1g()
        return {k: v for k, v in int_1g.items() if v["Desc"] == ' '}

    def get_interfaces_10g_other_rezerv(self):
        reserves = ["Rezerv_DIR.I2.4.4"]
        int_10g = self._get_interfaces_10g()
        interfaces = {k: v for k, v in int_10g.items() if "Rezerv" in v["Desc"] and v["Desc"] not in reserves}
        return {k: v for k, v in interfaces.items() if v["Status"] == "A-DOWN/DOWN"}

    def get_interfaces_10g_with_desc_no_link(self):
        with_desc_no_link = {}
        int_10g = self._get_interfaces_10g()
        for k, v in int_10g.items():
            if "rezerv" not in v["Desc"].lower() and v["Desc"] != " " and v["Status"] == "admin down":
                with_desc_no_link.update({k: v})
        return with_desc_no_link

    def get_interfaces_10g_no_description(self):
        int_10g = self._get_interfaces_10g()
        return {k: v for k, v in int_10g.items() if v["Desc"] == ' '}


class Cisco:
    def __init__(self):
        self.username = settings.SWITCH_AM_CISCO_USER
        self.password = settings.SWITCH_AM_CISCO_PASSWORD
        self.model = 'cisco'
        self.name = None
        self.interfaces = None
        self.components = None

    @staticmethod
    def show_ports_command():
        commands = [("sh int des | e Vl",), ("sh mod",)]
        return commands

    @staticmethod
    def show_components_command():
        commands = [("sh power",), ("sh mod",), ("sh version",)]
        return commands

    @staticmethod
    def show_ports_output(output):
        interfaces = {}
        int_output = output["sh int des | e Vl"]
        split_output = int_output.split("\n")
        keys = ["Status", "Protocol", "Desc"]
        for line in split_output:
            regex = " *(Fa\S+|Gi\S+|Te\S+) +(\w+ \w+|\w+) +(\w+) +([\S| ]+| )"
            match = re.match(regex, line)
            if match:
                data = match.groups()
                interfaces.update({data[0]: dict(zip(keys, data[1:]))})
        ports = list(filter(lambda x: '.' not in x and '/' in x, interfaces.keys()))
        mod_output = output["sh mod"]
        sup_line = [line.split()[0] for line in mod_output.split("\n") if 'Supervisor' in line]
        sup_slot = sup_line[0] if sup_line else ''
        return {k: v for k, v in interfaces.items() if k in ports and f"Gi{sup_slot}/" not in k and "REMOVED_" not in v["Desc"]}

    def show_components_output(self, output):
        linecards = {}
        mod_output = output["sh mod"]
        split_output = mod_output.split("\n")
        keys = ["slot", "ports", "card_type", "model", "serial", "submodules", "type"]

        for line in split_output:
            regex = "\s*(\d{1,2})\s+(\d{1,2})\s+(.+?)\s+(\S+)\s+(\S+)\s?$"
            match = re.match(regex, line)
            if match:
                data = list(match.groups())
                data.append([])
                data.append("Линейная карта")
                linecards.update({data[0]: dict(zip(keys, data))})

        keys = ["sub_module", "model", "serial"]
        for line in split_output:
            regex = "\s*(\d{1,2})\s+(.+?)\s+(\S+)\s+(\S+)\s+\d\.\d\s+Ok"
            match = re.match(regex, line)
            if match:
                data = match.groups()
                linecards[data[0]]["submodules"].append(dict(zip(keys, data[1:])))
                self.components = [v for v in linecards.values()]

        power_output = output["sh power"]
        split_output = power_output.split("\n")
        for line in split_output:
            regex = "\s*(\d)\s+(WS-CAC\S+)\s.+"
            match = re.match(regex, line)
            if match:
                self.components.append({"slot": match.group(1),"model": match.group(2), "type": "Блок питания"})

        version_output = output["sh version"]
        regex = ".+cisco (WS\S+) .+"
        match = re.match(regex, version_output, flags=re.DOTALL)
        if match:
            self.components.append({"model": match.group(1), "type":"Шасси"})

    def construct_components_table(self):
        table = []
        for v in self.components:
            submodules = v.get("submodules")
            row = [self.name.split(".")[-1], self.name.strip(), v["type"], v.get("slot"), v["model"], v.get("serial")]
            if not submodules:
                row.append(None)
                table.append(row)
            else:
                for submodule in submodules:
                    new_row = deepcopy(row)
                    new_row.append(submodule["model"])
                    table.append(new_row)
        return table

    def construct_components_summary(self):
        if self.components:
            summary = []
            for c in self.components:
                if 'WS-SUP720' in c["model"]:
                    summary.append('WS-SUP720')
                elif 'WS-CAC-4000W' in c["model"]:
                    summary.append('WS-CAC-4000W')
                elif c["model"] in ['WS-X6516-GBIC', 'WS-X6516A-GBIC']:
                    summary.append('WS-X6516(A)-GBIC')
                elif c["model"] in ['WS-X6708-10GE', 'WS-X6708A-10GE']:
                    summary.append('WS-X6708(A)-10GE')
                else:
                    summary.append(c["model"])
            return summary

    @staticmethod
    def _get_range_ports(interfaces):
        ports = {}
        ranges_by_module = []
        regex = "(\w{2}\d{1,2}\/)(\d{1,2})"
        for interface in interfaces.keys():
            match = re.match(regex, interface)
            port = int(match.group(2)) if match else None
            prefix_port = match.group(1) if match else None
            if ports.get(prefix_port):
                ports[prefix_port].append(port)
            else:
                ports[prefix_port] = [port]
        for prefix_port, data in ports.items():
            starts = [x for x in data if x - 1 not in data and x + 1 in data]
            ends = [x for x in data if x - 1 in data and x + 1 not in data and x not in starts]
            singles = [str(x) for x in data if x - 1 not in data and x + 1 not in data]
            ranges = list(zip(starts, ends))
            str_ranges = [f'{i[0]}-{i[1]}' for i in ranges]
            result_ranges = str_ranges + singles
            res_ranges = f"{prefix_port}" + f",{prefix_port}".join(result_ranges) if result_ranges else ""
            ranges_by_module.append(res_ranges)
        if ranges_by_module:
            all_ranges = ",".join(ranges_by_module).split(",")
            chunks = [all_ranges[i:i + 5] for i in range(0, len(all_ranges), 5)]  # Cisco не может обработать более 5 диапазонов портов за раз
            return [",".join(i) for i in chunks]

    def add_rezerv_1g_planning_command(self):
        interfaces = self.get_interfaces_1g_no_description()
        range_ports = self._get_range_ports(interfaces)
        if not range_ports:
            raise SwitchException(f"{self.name}: нет портов 1G без description.")
        commands = []
        commands.append(("conf t", "\(config\)#"))
        for block_range_ports in range_ports:
            commands.append((f"int range {block_range_ports}", f"\(config-if-range\)#"))
            commands.append(("description Rezerv_1G_planning", f"\(config-if-range\)#"))
        commands.append(("exit", "\(config\)#"))
        commands.append(("exit",))
        return commands

    def remove_rezerv_1g_planning_command(self):
        interfaces = self.get_interfaces_1g_rezerv_planning()
        range_ports = self._get_range_ports(interfaces)
        if not range_ports:
            raise SwitchException(f"{self.name}: нет портов Rezerv_1G_planning.")
        commands = []
        commands.append(("conf t", "\(config\)#"))
        for block_range_ports in range_ports:
            commands.append((f"int range {block_range_ports}", f"\(config-if-range\)#"))
            commands.append(("no description", f"\(config-if-range\)#"))
        commands.append(("exit", "\(config\)#"))
        commands.append(("exit",))
        return commands

    def _get_interfaces_1g(self):
        if self.interfaces:
            return {k: v for k, v in self.interfaces.items() if "Gi" in k}

    def _get_interfaces_10g(self):
        if self.interfaces:
            return {k: v for k, v in self.interfaces.items() if "Te" in k}

    def get_interfaces_1g_rezerv(self):
        int_1g = self._get_interfaces_1g()
        return {k: v for k, v in int_1g.items() if v["Desc"] == "Rezerv_1G"}

    def get_interfaces_1g_rezerv_planning(self):
        int_1g = self._get_interfaces_1g()
        return {k: v for k, v in int_1g.items() if v["Desc"] == "Rezerv_1G_planning"}

    def get_interfaces_1g_rezerv_dir2_4_4(self):
        int_1g = self._get_interfaces_1g()
        return {k: v for k, v in int_1g.items() if v["Desc"] == "Rezerv_DIR.I2.4.4"}

    def get_interfaces_1g_other_rezerv(self):
        int_1g = self._get_interfaces_1g()
        reserves = ["Rezerv_1G", "Rezerv_1G_planning", "Rezerv_DIR.I2.4.4"]
        return {k: v for k, v in int_1g.items() if "rezerv" in v["Desc"].lower() and v["Desc"] not in reserves}

    def get_interfaces_1g_with_desc_no_link(self):
        with_desc_no_link = {}
        int_1g = self._get_interfaces_1g()
        for k, v in int_1g.items():
            if "rezerv" not in v["Desc"].lower() and v["Desc"] != " " and v["Status"] == "admin down":
                with_desc_no_link.update({k: v})
        return with_desc_no_link

    def get_interfaces_1g_no_description(self):
        int_1g = self._get_interfaces_1g()
        return {k: v for k, v in int_1g.items() if v["Desc"] == ' '}

    def get_interfaces_10g_other_rezerv(self):
        reserves = ["Rezerv_DIR.I2.4.4"]
        int_10g = self._get_interfaces_10g()
        interfaces = {k: v for k, v in int_10g.items() if "Rezerv" in v["Desc"] and v["Desc"] not in reserves}
        return {k: v for k, v in interfaces.items() if v["Status"] == "admin down"}

    def get_interfaces_10g_with_desc_no_link(self):
        with_desc_no_link = {}
        int_10g = self._get_interfaces_10g()
        for k, v in int_10g.items():
            if "rezerv" not in v["Desc"].lower() and v["Desc"] != " " and v["Status"] == "admin down":
                with_desc_no_link.update({k: v})
        return with_desc_no_link

    def get_interfaces_10g_no_description(self):
        int_10g = self._get_interfaces_10g()
        return {k: v for k, v in int_10g.items() if v["Desc"] == ' '}


def input_checks(search_ip, username, password):
    input = [line for line in search_ip.split(";") if line]
    if len(input) > 10:
        raise InputSwitchException("Введено более 10 устройств")
    is_not_ar_ias = [line for line in input if not (line.startswith("AR") or line.startswith("IAS"))]
    if is_not_ar_ias:
        raise InputSwitchException("Поиск выполняется только по АМ/КПА")
    switches_in_db = {}
    for switch in input:
        switch_ip = get_switch_ip(username, password, switch)
        if switch_ip:
            switches_in_db.update({switch: switch_ip})
    ip_switches = switches_in_db.values()
    if not switches_in_db or len(input) != len(ip_switches):
        unrecognized = set(input) - set(switches_in_db.keys())
        raise InputSwitchException(f"Ошибка в текстовом вводе. Не удалось получить IP для {', '.join(unrecognized)}")
    return ip_switches
