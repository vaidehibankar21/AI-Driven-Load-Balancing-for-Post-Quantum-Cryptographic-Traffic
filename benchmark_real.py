"""
REAL liboqs benchmark. No hardcoded constants.
Outputs:
  - output/01_crypto_mean_bar.png       (bar chart, microseconds)
  - output/02_crypto_breakdown.png      (stacked: keygen + encap/sign)
  - output/03_crypto_distribution.png   (box plot of 100 samples)
  - output/04_crypto_cdf.png            (cumulative distribution)
  - output/05_e2e_microservice.png      (end-to-end via HTTP if running)
  - output/benchmark_results.json
"""
import time
import json
import os
import statistics
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import numpy as np
import oqs

ALGOS = [
    ("ML-KEM-512", "ML-KEM-512", "kem"),
    ("ML-KEM-768", "ML-KEM-768", "kem"),
    ("ML-DSA-44",  "ML-DSA-44",  "sig"),
    ("ML-DSA-65",  "ML-DSA-65",  "sig"),
]
N_ITER = 100
WARMUP = 10
os.makedirs("output", exist_ok=True)


def kem_cycle(name):
    t0 = time.perf_counter()
    with oqs.KeyEncapsulation(name) as c:
        pk = c.generate_keypair()
        ct, _ = c.encap_secret(pk)
        c.decap_secret(ct)
    return (time.perf_counter() - t0) * 1e6


def sig_cycle(name):
    t0 = time.perf_counter()
    with oqs.Signature(name) as s:
        pk = s.generate_keypair()
        sig = s.sign(b"payload")
        s.verify(b"payload", sig, pk)
    return (time.perf_counter() - t0) * 1e6


def kem_keygen(name):
    t0 = time.perf_counter()
    with oqs.KeyEncapsulation(name) as c:
        c.generate_keypair()
    return (time.perf_counter() - t0) * 1e6


def sig_keygen(name):
    t0 = time.perf_counter()
    with oqs.Signature(name) as s:
        s.generate_keypair()
    return (time.perf_counter() - t0) * 1e6


def benchmark():
    print("=" * 70)
    print("REAL liboqs benchmark — actual measurements, no constants added")
    print("=" * 70)
    results = {}

    for label, oqs_name, kind in ALGOS:
        print(f"\n[{label}]")
        for _ in range(WARMUP):
            (kem_cycle if kind == "kem" else sig_cycle)(oqs_name)

        cycles, keygens = [], []
        for _ in range(N_ITER):
            cycles.append((kem_cycle if kind == "kem" else sig_cycle)(oqs_name))
            keygens.append((kem_keygen if kind == "kem" else sig_keygen)(oqs_name))

        results[label] = {
            "mean_us": statistics.mean(cycles),
            "median_us": statistics.median(cycles),
            "stdev_us": statistics.stdev(cycles),
            "p95_us": sorted(cycles)[int(0.95 * len(cycles))],
            "min_us": min(cycles),
            "max_us": max(cycles),
            "keygen_us": statistics.mean(keygens),
            "samples": cycles,
        }
        r = results[label]
        print(f"  Full cycle : mean={r['mean_us']:.1f}µs  median={r['median_us']:.1f}µs  "
              f"stdev={r['stdev_us']:.1f}µs  P95={r['p95_us']:.1f}µs")
        print(f"  Keygen     : {r['keygen_us']:.1f}µs")

    # Save JSON (without raw samples)
    with open("output/benchmark_results.json", "w") as f:
        json.dump({k: {kk: vv for kk, vv in v.items() if kk != "samples"}
                   for k, v in results.items()}, f, indent=2)

    labels = list(results.keys())
    colors = ["#3b82f6", "#1d4ed8", "#10b981", "#047857"]

    # ---- Chart 1: Mean + P95 bar ----
    fig, ax = plt.subplots(figsize=(9, 5))
    x = np.arange(len(labels))
    w = 0.38
    means = [results[k]["mean_us"] for k in labels]
    p95s = [results[k]["p95_us"] for k in labels]
    b1 = ax.bar(x - w/2, means, w, label="Mean", color="#3b82f6")
    b2 = ax.bar(x + w/2, p95s, w, label="P95", color="#1d4ed8")
    for bars in (b1, b2):
        for b in bars:
            ax.text(b.get_x() + b.get_width()/2, b.get_height() * 1.02,
                    f"{b.get_height():.1f}", ha='center', fontsize=9)
    ax.set_xticks(x); ax.set_xticklabels(labels)
    ax.set_ylabel("Latency (microseconds)")
    ax.set_title("Real liboqs latency — NIST PQC primitives (100 iterations each)")
    ax.grid(axis='y', linestyle='--', alpha=0.5); ax.legend()
    plt.tight_layout(); plt.savefig("output/01_crypto_mean_bar.png", dpi=200); plt.close()

    # ---- Chart 2: Stacked breakdown ----
    fig, ax = plt.subplots(figsize=(9, 5))
    kg = [results[k]["keygen_us"] for k in labels]
    op2 = [results[k]["mean_us"] - k_ for k, k_ in zip(labels, kg)]
    ax.bar(labels, kg, label="Key generation", color="#10b981")
    ax.bar(labels, op2, bottom=kg, label="Encap/Sign + Decap/Verify", color="#047857")
    for i, k in enumerate(labels):
        ax.text(i, kg[i]/2, f"{kg[i]:.0f}µs", ha='center', color='white', fontsize=9)
        ax.text(i, kg[i] + op2[i]/2, f"{op2[i]:.0f}µs", ha='center', color='white', fontsize=9)
    ax.set_ylabel("Latency (microseconds)")
    ax.set_title("Per-operation breakdown")
    ax.legend()
    plt.tight_layout(); plt.savefig("output/02_crypto_breakdown.png", dpi=200); plt.close()

    # ---- Chart 3: Box plot distribution ----
    fig, ax = plt.subplots(figsize=(9, 5))
    data = [results[k]["samples"] for k in labels]
    bp = ax.boxplot(data, labels=labels, patch_artist=True, showmeans=True)
    for patch, c in zip(bp['boxes'], colors):
        patch.set_facecolor(c); patch.set_alpha(0.6)
    ax.set_ylabel("Latency (microseconds)")
    ax.set_title(f"Latency distribution across {N_ITER} iterations per algorithm")
    ax.grid(axis='y', linestyle='--', alpha=0.5)
    plt.tight_layout(); plt.savefig("output/03_crypto_distribution.png", dpi=200); plt.close()

    # ---- Chart 4: CDF ----
    fig, ax = plt.subplots(figsize=(9, 5))
    for k, c in zip(labels, colors):
        sorted_s = np.sort(results[k]["samples"])
        y = np.arange(1, len(sorted_s)+1) / len(sorted_s)
        ax.plot(sorted_s, y, label=k, color=c, linewidth=2)
    ax.set_xlabel("Latency (microseconds)")
    ax.set_ylabel("Cumulative probability")
    ax.set_title("CDF of measured crypto latencies")
    ax.grid(True, linestyle='--', alpha=0.5); ax.legend()
    plt.tight_layout(); plt.savefig("output/04_crypto_cdf.png", dpi=200); plt.close()

    print("\n4 charts saved to output/")
    print("  01_crypto_mean_bar.png")
    print("  02_crypto_breakdown.png")
    print("  03_crypto_distribution.png")
    print("  04_crypto_cdf.png")
    print("  benchmark_results.json")


if __name__ == "__main__":
    benchmark()