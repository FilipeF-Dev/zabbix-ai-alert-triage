import sys, json, os, tempfile, types
sys.path.insert(0, sys.argv[1] if len(sys.argv) > 1 else str(__import__('pathlib').Path(__file__).resolve().parents[1]))
import triage

chamadas = []

class Resp:
    def __init__(self, model):
        self.stop_reason = "end_turn"; self.stop_details = None
        self.content = [types.SimpleNamespace(type="text", text="analise simulada")]
        self.model = model; self._request_id = "req_x"
        self.usage = types.SimpleNamespace(input_tokens=1000, cache_read_input_tokens=5000,
                                           cache_creation_input_tokens=0, output_tokens=1000)

class Msgs:
    def create(self, **kw):
        chamadas.append(kw)
        return Resp(kw["model"])

cliente = types.SimpleNamespace(beta=types.SimpleNamespace(messages=Msgs()))

class Zbx:
    def chamar(self, metodo, p):
        return [{"eventid": str(i), "name": "ev" + str(i), "clock": str(1793800000 + i * 3600),
                 "objectid": str(100 + i), "hosts": [{"host": "H" + str(i)}]} for i in range(3)]
    def contexto(self, eid):
        return {"evento": "ev" + eid, "gravidade": "Media", "quando": "x", "host": "H" + eid,
                "_triggerid": "1"}

d = tempfile.mkdtemp()
conf = {"geral": {"log": d}, "anthropic": {"chave": "x"}}
saida = os.path.join(d, "t.md")
triage.modo_replay(conf, Zbx(), cliente, "BASE", 14, 3, saida, 0, ["opus", "sonnet", "haiku"], regras=False)
txt = open(saida, encoding="utf-8").read()
gab = open(saida[:-3] + "-gabarito.md", encoding="utf-8").read()
assert txt.count("### Resposta") == 9, txt
assert "claude-" not in txt, "modelo vazou no arquivo cego"
assert gab.count(" = claude-") == 9
for kw in chamadas:
    if kw["model"].startswith("claude-opus"):
        assert kw.get("fallbacks") == "default" and kw.get("betas")
    else:
        assert "fallbacks" not in kw and "betas" not in kw, kw["model"]
    assert kw["output_config"] == {"effort": "low"}
# custo: opus 1000*4+5000*0.4+1000*20 = 26000 -> 0.026
assert abs(triage.custo_usd({"modelo": "claude-opus-5-5", "entrada": 1000, "cache_escrito": 0,
                            "cache_lido": 5000, "saida": 1000}) - 0.026) < 1e-9
assert abs(triage.custo_usd({"modelo": "claude-haiku-5-5", "entrada": 1000, "cache_escrito": 0,
                            "cache_lido": 5000, "saida": 1000}) - 0.00065) < 1e-9
# registros de teste nao contam no limite diario
n, rep, raj = triage.analises_hoje_e_recentes(conf, "1", 6, "H0", 15)
assert (n, rep, raj) == (0, False, False), (n, rep, raj)
# replay sem --modelos usa o modelo do conf (padrao opus), sem gabarito
chamadas.clear()
triage.modo_replay(conf, Zbx(), cliente, "BASE", 14, 3, os.path.join(d, "u.md"), 0, [], regras=False)
assert {k["model"] for k in chamadas} == {"claude-sonnet-5-5"}
assert not os.path.exists(os.path.join(d, "u-gabarito.md"))
conf["anthropic"]["modelo"] = "opus"; chamadas.clear()
triage.modo_replay(conf, Zbx(), cliente, "BASE", 14, 3, os.path.join(d, "v.md"), 0, [], regras=False)
assert {k["model"] for k in chamadas} == {"claude-opus-5-5"}
print(gab)
print("TUDO OK")
