import os
import time
import httpx
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from balancer.rl_agent import QLearningBalancerAgent

app = FastAPI(title="PQC AI Load Balancer")
app.add_middleware(
    CORSMiddleware, allow_origins=["*"], allow_credentials=True,
    allow_methods=["*"], allow_headers=["*"],
)

WORKERS = os.getenv("WORKERS", "http://node1:8001,http://node2:8001,http://node3:8001").split(",")
rl_agent = QLearningBalancerAgent(num_nodes=len(WORKERS))
rr_index = 0
http_client = httpx.AsyncClient(timeout=10.0)

node_hits = {w: 0 for w in WORKERS}
request_log = []   # last 200 for export


class RouteReq(BaseModel):
    algorithm: str = "ML-KEM-768"
    mode: str = "rl"


def build_state(algorithm):
    """State = (algo_type, security_level). 4 possible states."""
    algo_type = 0 if "KEM" in algorithm else 1
    sec_level = 0 if ("512" in algorithm or "44" in algorithm) else 1
    return (algo_type, sec_level)


@app.post("/route")
async def route_traffic(req: RouteReq):
    global rr_index
    state = build_state(req.algorithm)

    if req.mode == "baseline_rr":
        idx = rr_index
        rr_index = (rr_index + 1) % len(WORKERS)
        decision = {"mode": "round_robin", "epsilon": 0, "reason": "Sequential cycling"}
    else:
        idx, decision = rl_agent.select_action(state)

    target_worker = WORKERS[idx]
    node_hits[target_worker] = node_hits.get(target_worker, 0) + 1

    start_rtt = time.perf_counter()
    try:
        resp = await http_client.post(f"{target_worker}/execute",
                                       json={"algorithm": req.algorithm},
                                       timeout=10.0)
        rtt_ms = (time.perf_counter() - start_rtt) * 1000.0
        if resp.status_code == 200:
            data = resp.json()
            crypto_ms = data.get("crypto_ms", 0.0)
            delay_ms = data.get("delay_ms", 0.0)
        else:
            crypto_ms = 0.0; delay_ms = 0.0
            data = {"status": "http_error", "code": resp.status_code}
    except Exception as e:
        rtt_ms = (time.perf_counter() - start_rtt) * 1000.0
        crypto_ms = 0.0; delay_ms = 0.0
        data = {"status": "error", "error": str(e)}

    update_info = None
    if req.mode == "rl":
        reward = 1000.0 / (rtt_ms + 1.0)
        update_info = rl_agent.update_q_table(state, idx, reward)
        update_info["formula"] = f"1000 / ({rtt_ms:.2f} + 1) = {reward:.2f}"

    record = {
        "worker": target_worker,
        "mode": req.mode,
        "latency_ms": round(rtt_ms, 2),
        "crypto_ms": round(crypto_ms, 3),
        "delay_ms": round(delay_ms, 2),
        "decision": decision,
        "update": update_info,
    }
    request_log.append(record)
    if len(request_log) > 200:
        request_log.pop(0)

    return {
        "routed_to": target_worker,
        "mode": req.mode,
        "latency_ms": round(rtt_ms, 2),
        "crypto_ms": round(crypto_ms, 3),
        "delay_ms": round(delay_ms, 2),
        "decision": decision,
        "update": update_info,
    }


@app.post("/reset")
def reset_agent():
    global rr_index, node_hits, request_log
    rl_agent.reset()
    rr_index = 0
    node_hits = {w: 0 for w in WORKERS}
    request_log = []
    return {"status": "reset"}


@app.get("/stats")
def get_stats():
    return {
        "node_hits": node_hits,
        "epsilon": rl_agent.epsilon,
        "snapshot": rl_agent.snapshot(),
        "request_log": request_log[-100:],
    }