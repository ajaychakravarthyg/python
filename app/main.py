import logging
import sys

from fastapi import FastAPI
from prometheus_fastapi_instrumentator import Instrumentator
from pythonjsonlogger import jsonlogger

# --- Structured JSON logging so Fluent Bit -> Elasticsearch -> Kibana
# can parse each field (level, message, path) instead of a raw string. ---
handler = logging.StreamHandler(sys.stdout)
handler.setFormatter(
    jsonlogger.JsonFormatter("%(asctime)s %(levelname)s %(name)s %(message)s")
)
logging.basicConfig(level=logging.INFO, handlers=[handler])
log = logging.getLogger("app")

app = FastAPI(title="devops-demo-api", version="0.1.0")

# Auto-exposes /metrics with request count + latency histograms
# that Prometheus scrapes and Grafana graphs. No manual wiring needed.
Instrumentator().instrument(app).expose(app)


@app.get("/")
def root():
    log.info("request", extra={"path": "/", "event": "root_called"})
    return {"message": "hello from devops-demo-api"}


@app.get("/healthz")  # liveness
def healthz():
    return {"status": "ok"}


@app.get("/readyz")  # readiness
def readyz():
    return {"status": "ready"}
