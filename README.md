# AI-Driven Load Balancing for Post-Quantum Cryptographic Traffic Using Q-Learning

> A reinforcement-learning router for ML-KEM and ML-DSA workloads.

##  Overview

As quantum computers threaten classical encryption (RSA/ECC), the world is migrating to Post-Quantum Cryptography (PQC) algorithms like **ML-KEM** and **ML-DSA** (NIST FIPS 203/204). However, PQC algorithms are computationally heavy, and in a heterogeneous cluster, some nodes are significantly slower than others. 

Traditional load balancers (like Round Robin) are blind to this variance, causing massive latency bottlenecks.

This project implements a **Q-Learning Agent** that learns the fastest node in real-time and routes PQC traffic to it, reducing latency by up to **76%** compared to Round Robin.

##  Key Features

- **Q-Learning Agent**: Uses ε-greedy exploration (ε = 0.30 → 0.05) and optimistic initialization (Q = 500) to quickly find the optimal node.
- **Real liboqs Benchmarks**: Measures actual ML-KEM and ML-DSA latencies using the Open Quantum Safe library.
- **Live Telemetry Dashboard**: A beautiful, interactive frontend with real-time Chart.js visualizations.
- **Interactive "You vs AI" Game**: A built-in simulation to visualize the exploration vs exploitation trade-off.
- **Fully Containerized**: Runs entirely via Docker Compose.

##  Architecture

1. **Client**: Sends HTTP POST requests to the Balancer.
2. **Balancer (FastAPI)**: The Q-Learning agent evaluates the Q-Table and selects the optimal worker node using `argmax Q(s,a)`.
3. **Worker Nodes (FastAPI + liboqs)**: Three nodes with injected delays (0ms, 100ms, 200ms) execute the PQC algorithms.
4. **Frontend**: Live dashboard that visualizes the Q-Table, latency, and execution logs.

##  Getting Started

### Prerequisites
- Docker & Docker Compose installed.

### Installation & Run

1. Clone the repository:

   git clone https://github.com/vaidehibankar21/AI-Driven-Load-Balancing-for-Post-Quantum-Cryptographic-Traffic.git
   cd YOUR_REPO_NAME

2. Build and start the containers:


    docker compose up --build -d

3. Access the applications:

    Frontend Dashboard: http://localhost:3000

    Balancer API: http://localhost:8050

4. To stop the application:

    docker compose down


### Reproducing the Experiments
To generate the benchmark data and charts:

# Run the liboqs crypto benchmarks
docker compose exec balancer python benchmark_real.py

# Run the Q-Learning vs Round Robin experiment (5 runs x 100 requests)
docker compose exec balancer python experiment.py

# Generate the Q-value convergence plot
docker compose exec balancer python plot_convergence.py


### Results
    Average Latency Reduction: ~76%

    P95 Latency Reduction: 10–20% (the 5% exploration floor occasionally hits a slow node, which is a deliberate trade-off for adaptability).

    Convergence: The agent locks onto the fastest node within 15–20 requests.

### Tech Stack
    Backend: Python 3.11, FastAPI, liboqs-python

    AI/ML: Tabular Q-Learning (Custom Implementation)

    Frontend: HTML5, CSS3, Vanilla JavaScript, Chart.js

    Infrastructure: Docker, Docker Compose

### License
    This project is open-source and available under the MIT License.

# Author
    Vaidehi Bankar
    Aavishkar 2026-27 Project