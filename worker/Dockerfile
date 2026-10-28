FROM python:3.11-slim-bookworm
WORKDIR /app

RUN apt-get update --fix-missing && \
    apt-get install -y --no-install-recommends \
    git cmake ninja-build build-essential libssl-dev ca-certificates pkg-config \
    && rm -rf /var/lib/apt/lists/*

RUN git clone --depth 1 https://github.com/open-quantum-safe/liboqs.git && \
    cd liboqs && mkdir build && cd build && \
    cmake -GNinja -DCMAKE_INSTALL_PREFIX=/usr -DOQS_BUILD_ONLY_LIB=ON .. && \
    ninja && ninja install && ldconfig && cd / && rm -rf liboqs

ENV LD_LIBRARY_PATH=/usr/lib:/usr/local/lib:$LD_LIBRARY_PATH
ENV OQS_LIBRARY_PATH=/usr/lib
ENV OQS_INSTALL_PATH=/usr

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
RUN python3 -c "import oqs; print('✅ liboqs OK')"

# ... after COPY worker/ .
COPY worker/ .

# ✅ Add benchmark file
COPY benchmark_real.py .

EXPOSE 8001
CMD ["uvicorn", "server_node:app", "--host", "0.0.0.0", "--port", "8001"]