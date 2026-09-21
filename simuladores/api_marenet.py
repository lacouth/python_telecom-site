# simulador: API REST da Maré Net — não precisa ler (é o "servidor" das aulas).
# Sobe um servidor HTTP nesta própria sessão, em http://127.0.0.1:8765, que
# responde em JSON como a API de um sistema de inventário de rede.
import json
import threading
import time
import urllib.request
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from urllib.parse import parse_qs, urlparse

PORTA_API = 8765

_EQUIPAMENTOS = [
    {"nome": "OLT-CENTRO-01", "tipo": "OLT", "ip": "10.0.1.10", "localidade": "Centro", "em_servico": True},
    {"nome": "OLT-NORTE-02", "tipo": "OLT", "ip": "10.0.2.10", "localidade": "Zona Norte", "em_servico": True},
    {"nome": "OLT-SUL-03", "tipo": "OLT", "ip": "10.0.3.10", "localidade": "Zona Sul", "em_servico": False},
    {"nome": "SWITCH-CENTRO-01", "tipo": "SWITCH", "ip": "10.0.1.20", "localidade": "Centro", "em_servico": True},
    {"nome": "SWITCH-NORTE-02", "tipo": "SWITCH", "ip": "10.0.2.20", "localidade": "Zona Norte", "em_servico": True},
    {"nome": "RADIO-OESTE-01", "tipo": "RADIO", "ip": "10.0.5.10", "localidade": "Zona Oeste", "em_servico": True},
]
_ALARMES = [
    {"id": 101, "equipamento": "OLT-CENTRO-01", "severidade": "CRITICAL", "mensagem": "perda de sinal na porta GPON0/1/3"},
    {"id": 102, "equipamento": "SWITCH-NORTE-02", "severidade": "ERROR", "mensagem": "Interface Gi0/12, changed state to down"},
    {"id": 103, "equipamento": "RADIO-OESTE-01", "severidade": "WARNING", "mensagem": "enlace degradado"},
    {"id": 104, "equipamento": "OLT-CENTRO-01", "severidade": "WARNING", "mensagem": "temperatura acima do limite"},
    {"id": 105, "equipamento": "RADIO-OESTE-01", "severidade": "CRITICAL", "mensagem": "enlace fora do ar"},
]
_chamadas_instavel = [0]


class _Tratador(BaseHTTPRequestHandler):
    def log_message(self, *args):          # sem log na tela
        pass

    def _responde(self, status, corpo):
        dados = json.dumps(corpo, ensure_ascii=False).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(dados)))
        self.end_headers()
        self.wfile.write(dados)

    def do_GET(self):
        url = urlparse(self.path)
        partes = [p for p in url.path.split("/") if p]
        filtros = {chave: valores[0] for chave, valores in parse_qs(url.query).items()}
        if partes == ["api", "saude"]:
            return self._responde(200, {"status": "ok"})
        if partes == ["api", "equipamentos"]:
            itens = [e for e in _EQUIPAMENTOS
                     if all(str(e.get(k)) == v for k, v in filtros.items())]
            return self._responde(200, {"count": len(itens), "results": itens})
        if len(partes) == 3 and partes[:2] == ["api", "equipamentos"]:
            for e in _EQUIPAMENTOS:
                if e["nome"] == partes[2]:
                    return self._responde(200, e)
            return self._responde(404, {"erro": f"equipamento {partes[2]} não encontrado"})
        if partes == ["api", "alarmes"]:
            itens = [a for a in _ALARMES
                     if all(str(a.get(k)) == v for k, v in filtros.items())]
            return self._responde(200, {"count": len(itens), "results": itens})
        if partes == ["api", "lento"]:
            time.sleep(3)
            return self._responde(200, {"status": "finalmente"})
        if partes == ["api", "instavel"]:
            _chamadas_instavel[0] += 1
            if _chamadas_instavel[0] % 2 == 1:
                return self._responde(503, {"erro": "serviço temporariamente indisponível"})
            return self._responde(200, {"status": "ok"})
        return self._responde(404, {"erro": f"rota {url.path} não existe"})


def inicia_api(porta=PORTA_API):
    """Sobe a API simulada (se ainda não estiver no ar) e devolve o endereço."""
    endereco = f"http://127.0.0.1:{porta}"
    try:
        urllib.request.urlopen(endereco + "/api/saude", timeout=1)
        return endereco                     # já estava no ar
    except OSError:
        pass
    servidor = ThreadingHTTPServer(("127.0.0.1", porta), _Tratador)
    threading.Thread(target=servidor.serve_forever, daemon=True).start()
    return endereco
