import sys, time, json, tempfile, configparser
from pathlib import Path
sys.path.insert(0, sys.argv[1] if len(sys.argv) > 1 else str(__import__('pathlib').Path(__file__).resolve().parents[1])); import triage as m
agora = int(time.time())
# rajada real de 04/11 17:04: 5 servicos do Bitdefender no SRV-ERP01, + 1 evento do SRV-HV02 e 1 recente demais
EV = {str(i): {"objectid": "t"+str(i), "clock": str(agora-300+i), "host": "SRV-ERP01"} for i in range(1,6)}
EV["6"] = {"objectid": "t6", "clock": str(agora-290), "host": "SRV-HV02"}
EV["7"] = {"objectid": "t7", "clock": str(agora-10), "host": "SRV-ERP01"}   # chegou agora
class Z:
    def chamar(self, met, p):
        if met == "event.get" and "eventids" in p:
            e = EV[p["eventids"][0]]
            return [{"eventid": p["eventids"][0], "objectid": e["objectid"], "clock": e["clock"],
                     "name": "servico " + p["eventids"][0], "severity": "3", "r_eventid": "0",
                     "hosts": [{"host": e["host"]}]}]
        if met == "event.get":
            return [{"eventid": k, "objectid": v["objectid"], "clock": v["clock"], "name": k,
                     "hosts": [{"host": v["host"]}]} for k, v in EV.items()]
analisados = []
def processar(conf, zbx, cli, base, eventid, mandar_email=True, **kw):
    e = EV[eventid]; analisados.append(eventid)
    reg = {"quando": m.hora(int(time.time())), "eventid": eventid, "triggerid": e["objectid"],
           "host": e["host"], "custo_usd": 0.05}
    m.auditar(conf, reg)
    return {"host": e["host"], "evento": eventid, "gravidade": "Media", "quando": "x"}, "txt", reg
m.processar = processar
tmp = Path(tempfile.mkdtemp())
conf = configparser.ConfigParser(); conf.read_dict({"geral": {"fila": str(tmp/"fila"), "log": str(tmp/"log"),
    "max_por_dia": "5", "repetido_horas": "6", "espera_media_segundos": "120"}, "anthropic": {}})
(tmp/"fila").mkdir()
for k in EV: (tmp/"fila"/(k+".evento")).write_text(k)
class Pare(Exception): pass
def dorme(_): raise Pare
m.time.sleep = dorme
try: m.modo_worker(conf, Z(), None, "")
except Pare: pass
fila = sorted(p.name for p in (tmp/"fila").glob("*.evento"))
feitos = sorted(p.name for p in (tmp/"fila"/"feitos").glob("*"))
print("analisados:", analisados); print("ficou na fila:", fila); print("feitos:", feitos)
assert analisados == ["1", "6"], analisados
assert fila == ["7.evento"], fila
assert len(feitos) == 6
# replay agrupado
evs = sorted(Z().chamar("event.get", {}), key=lambda e: int(e["clock"]))
g = m.agrupar(evs)
print("agrupar:", [e["eventid"] for e in g])
assert [e["eventid"] for e in g] == ["1", "6"]
print("TUDO OK")
