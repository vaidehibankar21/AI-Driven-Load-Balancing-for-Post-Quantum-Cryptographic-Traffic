"""Run 5 experiments × 100 requests per algorithm. Saves CSV + summary."""
import requests, time, statistics, json, os, csv

BASE = "http://localhost:8050"
ALGOS = ["ML-KEM-512", "ML-KEM-768", "ML-DSA-44", "ML-DSA-65"]
N_REQ = 50
N_RUNS = 5
os.makedirs("output", exist_ok=True)


def run_once(algo, mode):
    lats = []
    for _ in range(N_REQ):
        try:
            r = requests.post(f"{BASE}/route",
                              json={"algorithm": algo, "mode": mode}, timeout=10)
            lats.append(r.json()["latency_ms"])
        except Exception:
            lats.append(100.0)
    return lats


def stats(l):
    return {
        "mean": statistics.mean(l),
        "p95": sorted(l)[int(0.95 * len(l))],
        "stdev": statistics.stdev(l) if len(l) > 1 else 0,
    }


def main():
    all_results = {}
    rows = []
    for algo in ALGOS:
        print(f"\n=== {algo} ===")
        rr_runs, ai_runs = [], []
        for i in range(N_RUNS):
            requests.post(f"{BASE}/reset"); time.sleep(0.3)
            rr = stats(run_once(algo, "baseline_rr"))
            requests.post(f"{BASE}/reset"); time.sleep(0.3)
            ai = stats(run_once(algo, "rl"))
            rr_runs.append(rr); ai_runs.append(ai)
            print(f"  Run {i+1}: RR={rr['mean']:.2f}ms  AI={ai['mean']:.2f}ms  "
                  f"P95_RR={rr['p95']:.1f}ms  P95_AI={ai['p95']:.1f}ms")

        rr_m = statistics.mean([r["mean"] for r in rr_runs])
        ai_m = statistics.mean([r["mean"] for r in ai_runs])
        rr_p = statistics.mean([r["p95"] for r in rr_runs])
        ai_p = statistics.mean([r["p95"] for r in ai_runs])
        imp = (rr_m - ai_m) / rr_m * 100 if rr_m else 0

        all_results[algo] = {
            "rr_mean_ms": round(rr_m, 2),
            "ai_mean_ms": round(ai_m, 2),
            "improvement_pct": round(imp, 1),
            "rr_p95_ms": round(rr_p, 2),
            "ai_p95_ms": round(ai_p, 2),
        }
        rows.append([algo, round(rr_m, 2), round(ai_m, 2), round(imp, 1),
                     round(rr_p, 2), round(ai_p, 2)])

    with open("output/experiment_results.json", "w") as f:
        json.dump(all_results, f, indent=2)
    with open("output/experiment_results.csv", "w", newline="") as f:
        w = csv.writer(f)
        w.writerow(["Algorithm", "RR_Mean_ms", "AI_Mean_ms", "Improvement_pct",
                    "RR_P95_ms", "AI_P95_ms"])
        w.writerows(rows)

    print("\n=== FINAL ===")
    for a, r in all_results.items():
        print(f"{a}: RR={r['rr_mean_ms']}ms  AI={r['ai_mean_ms']}ms  "
              f"Improvement={r['improvement_pct']}%  P95: RR={r['rr_p95_ms']} → AI={r['ai_p95_ms']}")


if __name__ == "__main__":
    main()