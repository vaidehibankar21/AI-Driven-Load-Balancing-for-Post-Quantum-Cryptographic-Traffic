"""Plot Q-value convergence from output/q_convergence.csv"""
import csv
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import os

os.makedirs("output", exist_ok=True)

reqs, q1, q2, q3, eps = [], [], [], [], []

with open("output/q_convergence.csv", "r") as f:
    reader = csv.DictReader(f)
    for row in reader:
        reqs.append(int(row["req"]))
        q1.append(float(row["q_node1"]))
        q2.append(float(row["q_node2"]))
        q3.append(float(row["q_node3"]))
        eps.append(float(row["epsilon"]))

fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(10, 8), sharex=True)

# Q-value evolution
ax1.plot(reqs, q1, "o-", color="#059669", label="node1 (fastest, 0ms)", markersize=4)
ax1.plot(reqs, q2, "s-", color="#d97706", label="node2 (medium, 100ms)", markersize=4)
ax1.plot(reqs, q3, "^-", color="#dc2626", label="node3 (slowest, 200ms)", markersize=4)
ax1.set_ylabel("Q-value (reward estimate)")
ax1.set_title("Q-Learning Convergence — ML-KEM-768 state (0,1)")
ax1.grid(True, linestyle="--", alpha=0.5)
ax1.legend(loc="center right")

# Epsilon decay
ax2.plot(reqs, eps, "-", color="#2563eb", linewidth=2)
ax2.set_xlabel("Request number")
ax2.set_ylabel("Epsilon (exploration rate)")
ax2.set_title("Epsilon Decay: 0.30 → 0.05")
ax2.grid(True, linestyle="--", alpha=0.5)
ax2.set_ylim(0, 0.35)

plt.tight_layout()
plt.savefig("output/05_convergence_plot.png", dpi=200)
plt.close()
print("Saved: output/05_convergence_plot.png")