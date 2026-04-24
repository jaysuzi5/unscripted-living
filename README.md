# Unscripted Living

A personal retirement blog covering hobbies (woodworking, photography, reading, guitar, IT), daily life, and thoughts on finance, environment, and AI.

**Live site:** https://unscripted.jaycurtis.org

---

## Stack

- Python 3.12 / Django 6.0
- PostgreSQL (shared k8s cluster)
- django-allauth — email login + Google OAuth
- Bootstrap 5 + custom CSS
- WhiteNoise for static files
- OpenTelemetry for observability
- Docker + Kubernetes (namespace: `unscripted-living`)
- Cloudflare Zero Trust tunnel

---

## Local Development


## Run Server
```bash
uv run python manage.py runserver localhost:8000

```

### Build & Push Multi-Architecture Docker Image

```bash
docker buildx build --platform linux/amd64,linux/arm64 -t jaysuzi5/unscripted-living:latest --push .
```

### Redeploy
```bash
kubectl rollout restart deployment unscripted-living -n unscripted-living
```


```bash
# Install dependencies
uv sync

# Copy and fill in environment variables
cp .env.example .env

# Run migrations
uv run python manage.py migrate

# Create superuser
uv run python manage.py createsuperuser

# Start dev server
uv run python manage.py runserver
```

The dev server connects to the k8s PostgreSQL instance at `192.168.86.201:30004`. See `documents/setup/05_postgres_setup.md` for credentials setup.

---


## Project Structure

```
blog/               Main Django app (models, views, templates)
config/             Django project config (settings, urls, middleware, OTEL)
k8s/                Kubernetes manifests (deployment, sealed secrets, backup PVC)
static/css/         Custom CSS
templates/          Base template + allauth overrides
documents/setup/    Setup guides and project roadmap
```

---

## Deployment

```bash
# Build and push multi-arch Docker image
docker buildx build --platform linux/amd64,linux/arm64 \
  -t jaysuzi5/unscripted-living:latest --push .

# Apply k8s manifests
kubectl apply -f k8s/deployment.yaml

# Restart after a new image push
kubectl rollout restart deployment unscripted-living -n unscripted-living
kubectl rollout status deployment/unscripted-living -n unscripted-living
```

Secrets are managed as SealedSecrets (`k8s/secrets.yaml`). Credentials never appear in committed files — see `documents/setup/05_postgres_setup.md` for the sealing workflow.

---

## Features

- Category and tag-based post organization
- Markdown post content with safe HTML rendering
- Comment system (login required, approval workflow)
- Google OAuth + email authentication
- Responsive card-based design with category color accents
- JSON request/response logging via custom middleware
- OpenTelemetry traces, metrics, and logs exported to the cluster OTEL collector

---

## Roadmap

See [`documents/setup/roadmap.md`](documents/setup/roadmap.md) for setup progress and planned enhancements.
