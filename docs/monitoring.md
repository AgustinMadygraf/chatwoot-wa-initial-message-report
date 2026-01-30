# Monitoring & Observability

## Logging
- The shared logger emits JSON when `LOG_FORMAT=json` and keeps timestamp/logger/level/message fields.
- Set `LOG_FORMAT=json` in `.env` or your systemd/envrc for aggregator ingestion.
- Example output:

```json
{"timestamp":"2026-01-30T04:00:00","logger":"cli","level":"INFO","message":"Sync phase accounts","phase":"accounts"}
```

## Metrics & health
- Health checks report both Chatwoot API and MySQL connectivity via `EnvironmentHealthCheck`.
- Extend `HealthCheckPort` with gauges/counters if you push metrics to Prometheus (expose `/metrics` using `prometheus_client`).
- Logs already include metadata; add `extra` args to logger methods when emitting (e.g., `get_logger("sync").info("phase", phase=phase)`).
