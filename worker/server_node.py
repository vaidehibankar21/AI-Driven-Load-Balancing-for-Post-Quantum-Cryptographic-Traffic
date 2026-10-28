import os
import time
import psutil
from fastapi import FastAPI
from pydantic import BaseModel

os.environ['LD_LIBRARY_PATH'] = '/usr/lib:/usr/local/lib:' + os.environ.get('LD_LIBRARY_PATH', '')

import oqs

app = FastAPI(title=f"PQC Worker - {os.getenv('NODE_ID', 'node')}")

class Task(BaseModel):
    algorithm: str

BASE_DELAY_MS = float(os.getenv("BASE_DELAY_MS", "0"))
NODE_ID = os.getenv("NODE_ID", "node")
print(f"WORKER STARTED | NODE={NODE_ID} | DELAY={BASE_DELAY_MS}ms", flush=True)


@app.get("/metrics")
def get_metrics():
    return {
        "node_id": NODE_ID,
        "cpu_percent": psutil.cpu_percent(interval=0.05),
        "memory_percent": psutil.virtual_memory().percent,
        "delay_ms": BASE_DELAY_MS,
        "available": True,
    }


@app.post("/execute")
def execute_task(task: Task):
    algo = task.algorithm
    status = "unknown"

    # Measure CRYPTO time separately from DELAY time
    crypto_start = time.perf_counter()
    try:
        if "KEM" in algo:
            name = ("ML-KEM-512" if "512" in algo else
                    "ML-KEM-768" if "768" in algo else "ML-KEM-1024")
            with oqs.KeyEncapsulation(name) as c:
                pk = c.generate_keypair()
                ct, _ = c.encap_secret(pk)
                c.decap_secret(ct)
            status = "kem_ok"
        else:
            name = ("ML-DSA-44" if "44" in algo else
                    "ML-DSA-65" if "65" in algo else "ML-DSA-87")
            with oqs.Signature(name) as s:
                pk = s.generate_keypair()
                sig = s.sign(b"payload")
                s.verify(b"payload", sig, pk)
            status = "dsa_ok"
    except Exception as e:
        status = f"error: {e}"

    crypto_ms = (time.perf_counter() - crypto_start) * 1000.0

    # Injected delay (simulates slow hardware) — measured separately
    delay_start = time.perf_counter()
    if BASE_DELAY_MS > 0:
        time.sleep(BASE_DELAY_MS / 1000.0)
    delay_ms = (time.perf_counter() - delay_start) * 1000.0

    total_ms = crypto_ms + delay_ms
    return {
        "node_id": NODE_ID,
        "algorithm": algo,
        "crypto_ms": round(crypto_ms, 3),
        "delay_ms": round(delay_ms, 2),
        "latency_ms": round(total_ms, 3),
        "status": status,
    }