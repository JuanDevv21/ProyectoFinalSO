from collections import Counter
from concurrent.futures import ThreadPoolExecutor
import json
from pathlib import Path
import statistics
import time
from urllib.request import urlopen

def request():
    start = time.perf_counter()
    try:
        with urlopen("http://127.0.0.1:8080/", timeout=3) as response:
            instance = json.load(response)["instancia"]
        if instance in {"backend-1", "backend-2", "backend-3"}:
            return instance, (time.perf_counter() - start) * 1000
    except (OSError, ValueError, KeyError):
        pass
    return None, None

balance = Counter(request()[0] for _ in range(30))
print("Balance:", balance, flush=True)
assert None not in balance and len(balance) == 3
scheduled = []
with ThreadPoolExecutor(max_workers=16) as workers:
    start = time.perf_counter()
    for index in range(2400):
        delay = start + index / 40 - time.perf_counter()
        if delay > 0:
            time.sleep(delay)
        scheduled.append(workers.submit(request))
    results = [future.result() for future in scheduled]
counts = Counter(instance for instance, _ in results)
latencies = sorted(latency for _, latency in results if latency is not None)
data = {
    "balance": dict(balance),
    "counts": {instance: value for instance, value in counts.items() if instance is not None},
    "errors": counts[None],
    "p95_ms": round(statistics.quantiles(latencies, n=20, method="inclusive")[-1], 2) if len(latencies) > 1 else next(iter(latencies), None),
    "duration_seconds": round(time.perf_counter() - start, 2),
}
output = Path("resultados/host.json")
output.parent.mkdir(exist_ok=True)
output.write_text(json.dumps(data, indent=2), encoding="utf-8")
print(data, flush=True)

assert data["errors"] < 24 and data["p95_ms"] is not None and data["p95_ms"] < 250 and len(data["counts"]) == 3