import os
from time import perf_counter

from flask import Flask, Response, g, request
from prometheus_client import Counter, Histogram, CONTENT_TYPE_LATEST, generate_latest

app = Flask(__name__)
instance = os.environ["BACKEND_ID"]
requests = Counter("app_http_requests_total", "Solicitudes HTTP", ["route", "status"])
duration = Histogram("app_http_request_duration_seconds", "Latencia HTTP", ["route"])

@app.before_request
def start_timer():
    g.started = perf_counter()

@app.after_request
def record_metrics(response):
    if request.path != "/metrics":
        route = request.url_rule.rule if request.url_rule else "unmatched"
        requests.labels(route, str(response.status_code)).inc()
        duration.labels(route).observe(perf_counter() - g.started)
    return response

@app.get("/")
def index():
    return {"instancia": instance, "mensaje": "Respuesta del backend"}

@app.get("/metrics")
def metrics():
    return Response(generate_latest(), content_type=CONTENT_TYPE_LATEST)
