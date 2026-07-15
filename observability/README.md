# Observability on EKS

## Metrics — Prometheus + Grafana (one Helm chart)
```bash
helm repo add prometheus-community https://prometheus-community.github.io/helm-charts
helm repo update
helm install kube-prometheus-stack prometheus-community/kube-prometheus-stack \
  --namespace monitoring --create-namespace
```
- Installs Prometheus, Alertmanager, Grafana, and the CRDs (incl. `ServiceMonitor`).
- Our `servicemonitor.yaml` (label `release: kube-prometheus-stack`) makes Prometheus
  scrape the app's `/metrics` automatically.
- Grafana login: `kubectl -n monitoring get secret kube-prometheus-stack-grafana -o jsonpath="{.data.admin-password}" | base64 -d`
- Port-forward Grafana: `kubectl -n monitoring port-forward svc/kube-prometheus-stack-grafana 3000:80`
- Useful PromQL for this app (exposed by prometheus-fastapi-instrumentator):
  - Request rate:   `sum(rate(http_requests_total[5m])) by (handler)`
  - p95 latency:    `histogram_quantile(0.95, sum(rate(http_request_duration_seconds_bucket[5m])) by (le, handler))`

## Logs — Elasticsearch + Kibana (ECK) + Fluent Bit
```bash
# 1) ECK operator
helm repo add elastic https://helm.elastic.co && helm repo update
helm install elastic-operator elastic/eck-operator -n elastic-system --create-namespace

# 2) Elasticsearch + Kibana (apply an Elasticsearch and a Kibana CR, minimal for dev)
# 3) Fluent Bit DaemonSet ships every pod's stdout to Elasticsearch
helm install fluent-bit fluent/fluent-bit -n logging --create-namespace \
  --set config.outputs="[OUTPUT]\n Name es\n Match *\n Host elasticsearch-es-http\n Port 9200\n ..."
```
- Because the app logs **JSON to stdout**, Fluent Bit ships structured docs and Kibana
  parses `level`, `message`, `path`, `event` as real fields (not one blob).
- In Kibana: create a data view on the Fluent Bit index, then filter e.g. `level: ERROR`.
