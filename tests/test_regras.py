import sys, os, tempfile, types, json
sys.path.insert(0, sys.argv[1] if len(sys.argv) > 1 else str(__import__('pathlib').Path(__file__).resolve().parents[1]))
import triage

T0 = 1794000000

class Zbx:
    """Eventos: id -> dict. event.get filtra por eventids ou por janela."""
    def __init__(self, evs):
        self.evs = evs
    def chamar(self, metodo, p):
        assert metodo == "event.get", metodo
        if "eventids" in p:
            return [dict(self.evs[i]) for i in p["eventids"] if i in self.evs]
        out = [e for e in self.evs.values() if e.get("value", "1") == "1"
               and p["time_from"] <= int(e["clock"]) <= p.get("time_till", 10**12)]
        if "severities" in p:
            out = [e for e in out if int(e["severity"]) in p["severities"]]
        return sorted(out, key=lambda e: int(e["clock"]))

def ev(i, host, nome, t, sev=3, r=None):
    return {"eventid": i, "objectid": "t" + i, "name": nome, "clock": str(t),
            "severity": str(sev), "r_eventid": r or "0", "hosts": [{"host": host}],
            "value": "1"}

def rec(i, t):
    return {"eventid": i, "clock": str(t), "value": "0", "hosts": []}

evs = {}
def add(e): evs[e["eventid"]] = e
# 1: Bitdefender que voltou em 6 min (Media, espera 10 min) -> ignorado
add(ev("1", "SRV-DC01", 'Windows: "EPIntegrationService" is not running', T0, 3, "1r")); add(rec("1r", T0 + 360))
# 2: servico que ficou parado 3 h -> analisa
add(ev("2", "SRV-ERP01", 'Windows: "X" is not running', T0 + 20000, 3, "2r")); add(rec("2r", T0 + 30800))
# 3: Alta que voltou em 5 min (espera alta 2 min) -> analisa
add(ev("3", "BRANCH-TUNNEL", "ICMP Ping: Unavailable by ICMP ping", T0 + 40000, 4, "3r")); add(rec("3r", T0 + 40300))
# 4: tunel de terceiro -> lista (ignorar_nomes do conf)
add(ev("4", "ROUTER-HQ", "MikroTik: Interface PPTP-VENDOR-A(): Link down", T0 + 50000))
# 5: temperatura -> lista
add(ev("5", "SRV-HV01", "Sala dos servidores: temperatura alta (>= 30 °C)", T0 + 60000, 3))
# 6: Zabbix server -> host
add(ev("6", "Zabbix server", "Linux: Zabbix agent is not available", T0 + 70000))
# 7-9: tres hosts em 2 min -> massa
add(ev("7", "SRV-HV02", "ICMP Ping: Unavailable", T0 + 80000, 4))
add(ev("8", "SRV-ERP01", "ICMP Ping: Unavailable", T0 + 80060, 4))
add(ev("9", "SRV-DC01", "ICMP Ping: Unavailable", T0 + 80120, 4))
# 10: nobreak
add(ev("10", "SRV-FILES01", "Nobreak: em bateria", T0 + 90000, 4))

d = tempfile.mkdtemp()
conf = {"geral": {"log": d, "espera_segundos": "120", "ignorar_nomes": r"(?i)nobreak|energia|^Sala dos servidores|VENDOR-"}, "anthropic": {"chave": "x"}}
z = Zbx(evs)
esperado = {"1": "resolveu", "2": "", "3": "", "4": "ignorar_nomes", "5": "ignorar_nomes",
            "6": "ignorar_hosts", "7": "massa", "8": "massa", "9": "massa", "10": "ignorar_nomes"}
for i, exp in esperado.items():
    m = triage.motivo_para_ignorar(conf, z, evs[i])
    print(i, "->", m or "ANALISA")
    assert (exp in m) if exp else (m == ""), (i, m)
assert triage.espera_de(conf, 3) == 1200, "espera_segundos antigo nao pode valer"
assert triage.espera_de(conf, 4) == 120
# massa desligada
conf2 = {"geral": dict(conf["geral"], massa_hosts="0"), "anthropic": {}}
assert triage.motivo_para_ignorar(conf2, z, evs["7"]) == ""
# ignorado vai ao log e nao conta no teto
triage.registrar_ignorado(conf, evs["1"], "teste")
assert triage.analises_hoje_e_recentes(conf, "t1", 6, "SRV-DC01", 15) == (0, False, False)
# replay so-regras: nao chama a API
class Nada:
    def __getattr__(self, k): raise AssertionError("chamou a API")
saida = os.path.join(d, "r.md")
triage.modo_replay(conf, z, Nada(), "BASE", 99999, 3, saida, so_regras=True)
txt = open(saida, encoding="utf-8").read()
assert "**8 ignorados**" in txt and "**2 seriam analisados**" in txt, txt
assert triage.MODELO == "claude-sonnet-5-5"
print("TUDO OK")
