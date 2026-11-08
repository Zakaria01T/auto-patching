# Pin the resulting image ID in the run configuration after building.
FROM python:3.12.3-slim-bookworm@sha256:afc139a0a640942491ec481ad8dda10f2c5b753f5c969393b12480155fe15a63
RUN apt-get update && apt-get install -y --no-install-recommends gcc libc6-dev cppcheck iputils-ping git tar grep coreutils && rm -rf /var/lib/apt/lists/*
COPY requirements-scanners.txt /tmp/requirements-scanners.txt
RUN pip install --no-cache-dir -r /tmp/requirements-scanners.txt
# Remove ping file capabilities so it can use unprivileged datagram sockets.
RUN setcap -r /usr/bin/ping
ENV SEMGREP_ENABLE_VERSION_CHECK=0 HOME=/tmp PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=/repo SEMGREP_SEND_METRICS=off
USER 65534:65534
WORKDIR /work
ENTRYPOINT ["python3", "/repo/model-compare/worker.py"]
