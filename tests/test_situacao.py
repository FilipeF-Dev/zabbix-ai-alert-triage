import sys
sys.path.insert(0, sys.argv[1] if len(sys.argv) > 1 else str(__import__('pathlib').Path(__file__).resolve().parents[1]))
import triage

def fazer(r_eventid):
    z = triage.Zabbix("http://x", "t")
    def chamar(metodo, p):
        if metodo == "event.get" and p.get("eventids") == ["10"]:
            return [{"eventid": "10", "clock": "1794000000", "name": "WinDefend parado",
                     "severity": "3", "objectid": "5", "r_eventid": r_eventid,
                     "hosts": [{"hostid": "1", "host": "SRV-BRANCH01", "name": "SRV-BRANCH01"}], "tags": []}]
        if metodo == "event.get" and p.get("eventids") == ["11"]:
            return [{"eventid": "11", "clock": "1794000600"}]
        if metodo == "event.get":
            return []
        if metodo == "trigger.get":
            return [{"expression": "x", "comments": "", "items": []}]
        return []
    z.chamar = chamar
    return z.contexto("10")

a = fazer("0")
assert a["situacao_deste_alerta"] == "AINDA ABERTO na hora da consulta", a
b = fazer("11")
assert b["situacao_deste_alerta"].startswith("resolvido em ") and "(10 min depois)" in b["situacao_deste_alerta"], b
print(a["situacao_deste_alerta"], "|", b["situacao_deste_alerta"])
print("TUDO OK")
