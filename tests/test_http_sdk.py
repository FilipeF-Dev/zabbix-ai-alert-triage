import json, sys, anthropic
import httpx2 as httpx
sys.path.insert(0, sys.argv[1] if len(sys.argv) > 1 else str(__import__('pathlib').Path(__file__).resolve().parents[1])); import triage
cap = {}
def h(req):
    cap["body"] = json.loads(req.content); cap["hdr"] = dict(req.headers)
    stop = cap.get("stop", "end_turn")
    return httpx.Response(200, headers={"request-id": "req_x"}, json={
      "id":"msg_1","type":"message","role":"assistant","model":"claude-opus-5-5",
      "content":[{"type":"thinking","thinking":"","signature":"s"},{"type":"text","text":"O QUE PROVAVELMENTE E: teste"}],
      "stop_reason":stop,"stop_sequence":None,
      "stop_details":({"type":"refusal","category":"cyber","explanation":"x"} if stop=="refusal" else None),
      "usage":{"input_tokens":12000,"output_tokens":800,"cache_read_input_tokens":0,"cache_creation_input_tokens":0}})
c = anthropic.Anthropic(api_key="sk-teste", http_client=httpx.Client(transport=httpx.MockTransport(h)))
t,u = triage.analisar(c, "BASE", {"evento":"x","_triggerid":"1"})
b=cap["body"]
assert b["model"]=="claude-sonnet-5-5" and "fallbacks" not in b and not cap["hdr"].get("anthropic-beta"), b
print("padrao sonnet ok, sem fallback/beta")
t,u = triage.analisar(c, "BASE", {"evento":"x","_triggerid":"1"}, "claude-opus-5-5")
b=cap["body"]
print("beta header:", cap["hdr"].get("anthropic-beta"))
print("campos:", sorted(b)); print("fallbacks:", b["fallbacks"], "| effort:", b["output_config"])
print("cache:", b["system"][0]["cache_control"]); print("texto:", t); print("uso:", u, "custo:", round(triage.custo_usd(u),4))
cap["stop"]="refusal"
try: triage.analisar(c,"BASE",{"evento":"x"},"claude-opus-5-5"); print("ERRO: recusa passou")
except RuntimeError as e: print("recusa ok:", e)
def h400(req): return httpx.Response(400, json={"type":"error","error":{"type":"invalid_request_error","message":"Your credit balance is too low"}})
c2 = anthropic.Anthropic(api_key="sk", max_retries=0, http_client=httpx.Client(transport=httpx.MockTransport(h400)))
try: triage.analisar(c2,"B",{"e":1})
except anthropic.BadRequestError as e: print("sem credito ->", type(e).__name__)
