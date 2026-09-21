# simulador: equipamentos SSH da Maré Net — não precisa ler (faz o papel dos switches).
# Imita a interface da biblioteca Netmiko: ConnectHandler(...), send_command(...),
# disconnect() e as mesmas exceções. Com equipamentos de verdade, a única linha que
# muda é o import: from netmiko import ConnectHandler, ...
import time


class NetmikoTimeoutException(Exception):
    """O equipamento não respondeu a tempo."""


class NetmikoAuthenticationException(Exception):
    """Usuário ou senha recusados."""


_VERSAO = """Cisco IOS Software, C2960X Software (C2960X-UNIVERSALK9-M), Version {versao}, RELEASE SOFTWARE (fc3)
{nome} uptime is {uptime}
System image file is "flash:c2960x-universalk9-mz.{versao}.bin"
cisco WS-C2960X-48FPD-L (APM86XXX) processor with 524288K bytes of memory."""

_CABECALHO = "Interface              IP-Address      OK? Method Status                Protocol"

_EQUIPAMENTOS = {
    "10.0.1.20": {"nome": "SWITCH-CENTRO-01", "versao": "15.2(7)E7", "uptime": "3 weeks, 2 days, 4 hours",
                  "interfaces": [("Vlan10", "10.0.1.20", "up", "up"),
                                 ("GigabitEthernet1/0/1", "unassigned", "up", "up"),
                                 ("GigabitEthernet1/0/2", "unassigned", "up", "up"),
                                 ("GigabitEthernet1/0/3", "unassigned", "down", "down")]},
    "10.0.2.20": {"nome": "SWITCH-NORTE-02", "versao": "15.2(7)E7", "uptime": "12 days, 7 hours",
                  "interfaces": [("Vlan20", "10.0.2.20", "up", "up"),
                                 ("GigabitEthernet1/0/1", "unassigned", "up", "up"),
                                 ("GigabitEthernet1/0/2", "unassigned", "administratively down", "down"),
                                 ("GigabitEthernet1/0/3", "unassigned", "down", "down"),
                                 ("GigabitEthernet1/0/4", "unassigned", "down", "down")]},
    "10.0.3.20": {"nome": "SWITCH-SUL-03", "falha": "tempo"},
    "10.0.4.20": {"nome": "SWITCH-LESTE-04", "falha": "senha"},
    "10.0.5.20": {"nome": "SWITCH-OESTE-05", "versao": "15.2(4)E10", "uptime": "1 year, 5 weeks",
                  "interfaces": [("Vlan50", "10.0.5.20", "up", "up"),
                                 ("GigabitEthernet1/0/1", "unassigned", "up", "up"),
                                 ("GigabitEthernet1/0/2", "unassigned", "up", "up")]},
}
_SENHA = "marenet"


class _Conexao:
    def __init__(self, dados):
        self._dados = dados

    def send_command(self, comando):
        comando = " ".join(comando.split())
        if comando == "show version":
            return _VERSAO.format(**self._dados)
        if comando == "show ip interface brief":
            linhas = [_CABECALHO]
            for nome, ip, estado, protocolo in self._dados["interfaces"]:
                linhas.append(f"{nome:<23}{ip:<16}YES manual {estado:<22}{protocolo}")
            return "\n".join(linhas)
        if comando == "show clock":
            return "*14:03:17.123 BRT Mon Mar 2 2026"
        return "% Invalid input detected at '^' marker."

    def disconnect(self):
        pass

    def __enter__(self):
        return self

    def __exit__(self, *args):
        self.disconnect()


def ConnectHandler(device_type, host, username, password, timeout=5, **extras):
    """Abre uma "sessão SSH" com o equipamento simulado."""
    dados = _EQUIPAMENTOS.get(host)
    if dados is None or dados.get("falha") == "tempo":
        time.sleep(0.2)
        raise NetmikoTimeoutException(f"TCP connection to device failed: {host}")
    if dados.get("falha") == "senha" or password != _SENHA:
        raise NetmikoAuthenticationException(f"Authentication to device failed: {host}")
    return _Conexao(dados)
