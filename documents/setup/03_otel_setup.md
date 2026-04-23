## OpenTelemetry Setup

Structured JSON logging and OpenTelemetry tracing/metrics/logs are configured following the same pattern as jautolog.

---

### Local Development

OpenTelemetry exporters are not active in local dev (no OTEL endpoint set). Logs go to console.

To view logs:
```bash
uv run python manage.py runserver
```

All requests log JSON to stdout via `config/middleware.py`.

---

### Production (Kubernetes)

The Docker CMD wraps gunicorn with `opentelemetry-instrument`:

```bash
uv run opentelemetry-instrument \
  --traces_exporter otlp \
  --metrics_exporter otlp \
  --logs_exporter otlp \
  -- gunicorn config.wsgi:application --bind 0.0.0.0:8000 --workers 4
```

The OTEL collector endpoint is set in `k8s/deployment.yaml`:
```
OTEL_EXPORTER_OTLP_ENDPOINT=http://otel-collector-collector.monitoring.svc.cluster.local:4317
OTEL_SERVICE_NAME=unscripted-living
```

---

### Structured Logging

Use `log_event()` from `config/logging_utils.py` for application events:

```python
from config.logging_utils import log_event

log_event(
    request=request,
    event='comment_submitted',
    level='INFO',
    post_slug=post.slug,
)
```

All request/response pairs are automatically logged by `config/middleware.py` including:
- Transaction ID (UUID)
- Method, path, status code, elapsed time
- User context (authenticated user or null)
