# devops-demo-api — end-to-end GitOps reference

FastAPI service wired for a full DevOps loop:
**CI → Nexus (artifact) → ECR (image) → Trivy (scan) → Argo CD → EKS → Prometheus/Grafana + Kibana**

## Flow
```
 push to main
      │
      ▼
┌──────────── GitHub Actions ─────────────┐
│ test → package(Nexus) → build+scan+     │
│ push(ECR) → update GitOps repo tag      │
└─────────────────────┬────────────────────┘
                   │ git commit (image tag)
                   ▼
        devops-demo-gitops repo  ◄── Argo CD watches this
                   │
                   ▼ (auto-sync)
        EKS cluster (namespace: demo)
          ├─ Deployment (2 replicas, probes)
          ├─ Service + ServiceMonitor ──► Prometheus ──► Grafana
          └─ stdout JSON logs ──► Fluent Bit ──► Elasticsearch ──► Kibana
```

## Key idea: CI builds, Argo CD deploys
CI never runs `kubectl apply`. It only pushes a scanned image and bumps the tag in the
**GitOps repo**. Argo CD reconciles cluster state to git — that's what makes it GitOps
(auditable, revertable, no cluster creds in CI).

## Repo layout
- `app/` — FastAPI service (`/`, `/healthz`, `/readyz`, `/metrics`)
- `Dockerfile` — multi-stage, non-root
- `.github/workflows/ci.yml` — the pipeline
- `gitops/` — Kustomize base + prod overlay (move to a SEPARATE repo for real GitOps)
- `argocd/application.yaml` — Argo CD Application CR
- `observability/README.md` — Prometheus/Grafana + ECK/Kibana install

## Repository secrets to set (Settings -> Secrets and variables -> Actions)
| Secret | Purpose |
|---|---|
| `AWS_ROLE_ARN` | IAM role that trusts GitHub OIDC, used to push to ECR (keyless) |
| `NEXUS_USER`, `NEXUS_PASS`, `NEXUS_PYPI_URL` | wheel upload to Nexus |
| `GITOPS_REPO` | GitOps repo, e.g. `your-user/devops-demo-gitops` |
| `GITOPS_TOKEN` | PAT (or fine-grained token) with write access to the GitOps repo |

> No `AWS_ACCESS_KEY_ID` needed if you use OIDC (recommended). To use static keys
> instead, swap the `configure-aws-credentials` inputs for `aws-access-key-id` /
> `aws-secret-access-key` and store those as secrets.

Also set `AWS_REGION` and `IMAGE_NAME` at the top of `.github/workflows/ci.yml`.


## Bootstrap order
1. `eksctl create cluster` (or Terraform) + `aws ecr create-repository --repository-name devops-demo-api`
2. Install Argo CD: `kubectl create ns argocd && kubectl apply -n argocd -f https://raw.githubusercontent.com/argoproj/argo-cd/stable/manifests/install.yaml`
3. Install kube-prometheus-stack + ECK/Fluent Bit (see `observability/README.md`)
4. Split `gitops/` into its own repo, edit `argocd/application.yaml` repoURL, `kubectl apply -f argocd/application.yaml`
5. Push to `main` → pipeline runs → Argo CD syncs the new image

> Pins in `requirements*.txt` are known-good starting points — run `pip freeze` for a lockfile and bump as needed.
