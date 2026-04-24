# New Django Project — Claude Instructions Template

Use this document as the prompt/briefing for Claude Code when starting a new Django project
with the same general infrastructure stack. Customize the bracketed values for each project.

---

## What to Tell Claude

Paste the following into a new Claude Code session (edit anything in `[brackets]`):

---

### Prompt to Claude

```
Create a new Django project called [PROJECT_NAME] in the directory [PROJECT_DIR].

## Project Overview

[One paragraph describing what the app does and who uses it.]

## Stack

- Python 3.12 / Django 6.0
- uv for package management
- PostgreSQL — new database called `[DB_NAME]` on the shared k8s instance:
    - External (local dev): 192.168.86.201:30004
    - Internal (k8s pods): postgresql-rw.postgresql.svc.cluster.local:5432
    - Owner: jcurtis
- django-allauth 65.x — email login + Google OAuth
- Bootstrap 5 + custom CSS
- WhiteNoise for static files
- OpenTelemetry (OTLP exporter, wraps gunicorn in production)
- Docker multi-arch image: jaysuzi5/[IMAGE_NAME]:latest
- Kubernetes namespace: [K8S_NAMESPACE]
- Cloudflare tunnel: [SUBDOMAIN].jaycurtis.org

## Credential Security Rules (CRITICAL)

- NEVER put passwords, secret keys, or tokens in any file that will be committed to git.
- Local dev credentials go only in `.env` (must be gitignored).
- Kubernetes credentials go in `k8s/temp.yaml` (gitignored plain text) → seal with kubeseal
  → output to `k8s/secrets.yaml` (safe to commit sealed) → delete temp.yaml immediately.
- The roadmap, CLAUDE.md, and all documentation must reference credentials by description only —
  never include actual values.

## Claude Code Setup (do this first, before any code)

1. Create `.claudeignore` — copy the standard template; add `.venv/`, `staticfiles/`, `media/`,
   `uv.lock` under the project-specific section.
2. Create `CLAUDE.md` with:
   - Project overview (stack, dev commands)
   - Architecture notes (key entry points, non-obvious conventions)
   - Deployment commands
   - Project-specific routing rules (see below)
3. Create `.vscode/tasks.json` with: Compact Session, View Token Usage, Open ChatGPT, Open Grok tasks.

## Django App Structure

Use the `config/` project layout (not the default `[project_name]/` layout):

```
[PROJECT_DIR]/
├── [APP_NAME]/           # main application
│   ├── migrations/
│   ├── templates/[APP_NAME]/
│   ├── admin.py
│   ├── apps.py
│   ├── context_processors.py
│   ├── forms.py
│   ├── models.py
│   ├── urls.py
│   └── views.py
├── config/
│   ├── asgi.py
│   ├── logging_utils.py
│   ├── middleware.py     # JSON request/response logging
│   ├── otel_config.py
│   ├── settings.py       # all settings, reads from .env via django-environ
│   ├── urls.py
│   └── wsgi.py
├── k8s/
│   ├── deployment.yaml
│   ├── secrets.yaml      # SealedSecret — safe to commit
│   └── backup-pvc.yaml
├── static/css/
├── templates/
│   ├── base.html
│   └── account/          # allauth template overrides
├── documents/setup/
│   └── roadmap.md
├── .env                  # gitignored
├── .env.example          # safe to commit, no real values
├── .gitignore
├── Dockerfile
├── manage.py
└── pyproject.toml
```

## settings.py Key Patterns

### django-environ for credentials (allauth 65.x settings):
```python
import environ
env = environ.Env()
environ.Env.read_env(os.path.join(BASE_DIR, '.env'))

# allauth 65.x — use the NEW API, not the deprecated one
ACCOUNT_LOGIN_METHODS = {'email'}
ACCOUNT_SIGNUP_FIELDS = ['email*', 'password1*', 'password2*']
ACCOUNT_EMAIL_VERIFICATION = 'optional'
SOCIALACCOUNT_LOGIN_ON_GET = True
```

### Production security block (Cloudflare terminates TLS — do NOT redirect HTTP):
```python
if os.getenv('DJANGO_ENV') == 'production':
    SECURE_SSL_REDIRECT = False   # Cloudflare handles TLS, never True
    SESSION_COOKIE_SECURE = True
    CSRF_COOKIE_SECURE = True
    SECURE_HSTS_SECONDS = 31536000
    SECURE_HSTS_INCLUDE_SUBDOMAINS = True
```

### CSRF for Cloudflare domain:
```python
CSRF_TRUSTED_ORIGINS = env.list(
    'CSRF_TRUSTED_ORIGINS',
    default=['http://localhost:8000', 'http://127.0.0.1:8000'],
)
# In .env, add: CSRF_TRUSTED_ORIGINS=https://[SUBDOMAIN].jaycurtis.org
```

## Kubernetes Secrets Pattern

Create `k8s/temp.yaml` (gitignored) in this format — values must be base64 encoded:
```yaml
apiVersion: v1
kind: Secret
metadata:
  name: [K8S_NAMESPACE]
  namespace: [K8S_NAMESPACE]
type: Opaque
data:
  postgres_user: <base64>      # echo -n 'value' | base64
  postgres_password: <base64>
  secret_key: <base64>
  # add other secrets as needed
```

Seal and delete:
```bash
kubeseal -f k8s/temp.yaml -o yaml > k8s/secrets.yaml
kubectl apply -f k8s/secrets.yaml
rm k8s/temp.yaml
```

## Kubernetes Deployment Pattern

`k8s/deployment.yaml` must include:
- Namespace definition
- Init container that runs `uv run python manage.py migrate --no-input` before the app starts
- All env vars from SealedSecret via `secretKeyRef`
- `DJANGO_ENV=production` env var
- OTEL env vars: `OTEL_EXPORTER_OTLP_ENDPOINT=http://otel-collector-collector.monitoring.svc.cluster.local:4317`
- LoadBalancer service, port 80 → 8000

## Dockerfile Pattern

```dockerfile
FROM python:3.12-slim
ADD https://astral.sh/uv/install.sh /install.sh
RUN sh /install.sh && rm /install.sh
ENV PATH="/root/.local/bin:$PATH"
WORKDIR /app
COPY pyproject.toml uv.lock ./
RUN uv sync --frozen --no-dev
COPY . .
RUN uv run python manage.py collectstatic --noinput
CMD ["uv", "run", "opentelemetry-instrument", \
     "--traces_exporter", "otlp", \
     "--metrics_exporter", "otlp", \
     "--logs_exporter", "otlp", \
     "--", "gunicorn", "config.wsgi:application", \
     "--bind", "0.0.0.0:8000", "--workers", "4"]
```

## Roadmap

Create `documents/setup/roadmap.md` with phases:
1. Project Foundation (Claude setup files, pyproject.toml, config/)
2. [APP_NAME] Application (models, views, urls, admin, forms)
3. Templates & Design (base.html, app templates, static/css)
4. Database (create DB, migrate, createsuperuser)
5. Kubernetes Secrets (temp.yaml → seal → apply → delete)
6. Docker & Kubernetes Deployment (build, push, apply, verify)
7. Cloudflare Tunnel (add route, test domain)
8. Authentication Setup (Google OAuth credentials + Django admin Social App)
9. Initial Content ([app-specific content setup])
10. Database Backups (cronjob-backup.yaml)

Check off items as each phase is completed.

## Claude Routing Rules (for CLAUDE.md)

Add this section to the project CLAUDE.md:

```
## Project-Specific Routing Rules
- Schema changes and migrations: stay on Sonnet
- Template/CSS changes: Haiku is fine
- New [APP_NAME] features (models, views): stay on Sonnet
- Setup documentation updates: GPT-4o-mini
```

## What to Build

[Describe the specific models, views, templates, and features for this project.]
```

---

## Infrastructure Reference

### Cluster Details (do not put in committed files)

| Resource | Value |
|---|---|
| PostgreSQL external | 192.168.86.201:30004 |
| PostgreSQL internal (k8s) | postgresql-rw.postgresql.svc.cluster.local:5432 |
| DB owner | jcurtis |
| OTEL collector | otel-collector-collector.monitoring.svc.cluster.local:4317 |
| Docker Hub user | jaysuzi5 |
| Cloudflare domain | jaycurtis.org |
| kubeseal version | 0.29.0 |

### Create the PostgreSQL Database

```bash
PGPASSWORD='...' psql -h 192.168.86.201 -p 30004 -U jcurtis -d postgres \
  -c 'CREATE DATABASE "[DB_NAME]" OWNER jcurtis;'
```

### Build & Deploy

```bash
# Build multi-arch image and push
docker buildx build --platform linux/amd64,linux/arm64 \
  -t jaysuzi5/[IMAGE_NAME]:latest --push .

# First deploy
kubectl apply -f k8s/secrets.yaml
kubectl apply -f k8s/deployment.yaml

# Subsequent deploys
kubectl rollout restart deployment [K8S_NAMESPACE] -n [K8S_NAMESPACE]
kubectl rollout status deployment/[K8S_NAMESPACE] -n [K8S_NAMESPACE]
```

### Cloudflare Tunnel Route

In Cloudflare Zero Trust → Networks → Tunnels → Edit existing tunnel → Add route:
- Subdomain: `[SUBDOMAIN]`
- Domain: `jaycurtis.org`
- Type: HTTP
- URL: `[K8S_NAMESPACE].[K8S_NAMESPACE].svc.cluster.local:80`

### Post-Deploy: Superuser

```bash
kubectl exec -n [K8S_NAMESPACE] -it \
  $(kubectl get pod -n [K8S_NAMESPACE] -l app=[K8S_NAMESPACE] -o name | head -1) \
  -- uv run python manage.py createsuperuser
```

### Post-Deploy: Google OAuth

1. Google Cloud Console → APIs & Credentials → Create OAuth 2.0 Client ID (Web Application)
2. Add authorized redirect URIs:
   - `http://localhost:8000/accounts/google/login/callback/`
   - `https://[SUBDOMAIN].jaycurtis.org/accounts/google/login/callback/`
3. In Django Admin → Social Applications → Add:
   - Provider: Google
   - Client ID + Secret: from Google Cloud Console
   - Sites: assign the production site

---

## Token Efficiency — Claude Code Configuration

These settings reduce token usage across the project lifecycle.

### .claudeignore (critical — create before exploring)

Always create `.claudeignore` before doing any file exploration. At minimum, exclude:
```
.git/
__pycache__/
*.pyc
.venv/
venv/
uv.lock
poetry.lock
staticfiles/
media/
node_modules/
*.min.js
*.min.css
.env
.env.*
```

### CLAUDE.md Structure

Keep the project CLAUDE.md focused on things Claude cannot derive from the code:
- Non-obvious conventions (e.g., "context processor injects X globally, don't pass it from views")
- Deployment commands (not in code)
- Which things are never edited directly (generated files)
- Project-specific routing rules (which tasks use which model)

Do NOT put architecture that's readable from the code, or git history summaries.

### Model Routing Rules

| Task | Model |
|---|---|
| Schema changes, migrations, debugging | Sonnet (stay on current) |
| New feature implementation | Sonnet |
| Template / CSS edits | Haiku |
| Documentation updates | GPT-4o-mini |
| Commit message drafting | Haiku |
| Boilerplate from a clear pattern | Haiku |

### /compact Habit

Run `/compact` before:
- Switching from one major task to another in the same session
- Starting any large implementation task
- The session has been running more than ~30 minutes

This compresses conversation history while preserving intent, significantly reducing tokens on long tasks.

### Sub-agent Usage

When a task requires reading many files to produce a short answer, spawn a sub-agent
(Agent tool with `subagent_type=Explore`). The sub-agent absorbs the file-reading tokens;
the parent session only sees the summary. Use this for:
- "How does X work across the codebase?"
- "Find all places that do Y"
- Any exploration that would require reading 5+ files

### VS Code Tasks

Create `.vscode/tasks.json` with a "Compact Session" task so `/compact` can be triggered
from the command palette without switching to the Claude Code terminal:
```json
{
  "label": "Compact Session",
  "type": "shell",
  "command": "echo '/compact' | pbcopy && echo 'Copied /compact to clipboard'"
}
```

---

## Email Setup (Gmail SMTP)

This project uses Gmail SMTP for transactional email (comment notifications, test emails).

**Key settings** (in `config/settings.py` production block):
```python
EMAIL_BACKEND = 'django.core.mail.backends.smtp.EmailBackend'
EMAIL_HOST = 'smtp.gmail.com'
EMAIL_PORT = 587
EMAIL_USE_TLS = True
EMAIL_HOST_USER = 'jaysuzi5@gmail.com'
EMAIL_HOST_PASSWORD = '<16-char app password>'
DEFAULT_FROM_EMAIL = 'jaysuzi5@gmail.com'
```

**Important:** `DEFAULT_FROM_EMAIL` must match `EMAIL_HOST_USER` exactly — Gmail rejects mismatched from addresses.

**App Password:** Generate at myaccount.google.com → Security → 2-Step Verification → App passwords. Required when 2FA is enabled. Store in k8s SealedSecret as `email_user` and `email_password`.

**k8s env vars:** `EMAIL_HOST`, `EMAIL_PORT`, `EMAIL_HOST_USER`, `EMAIL_HOST_PASSWORD` — set in `k8s/deployment.yaml`. After adding new env vars, always run `kubectl apply -f k8s/deployment.yaml` first, then `kubectl rollout restart`. A plain `kubectl rollout restart` without a prior `apply` will not pick up new env vars.

**Verify email is working:** Visit `/test-email/` while logged in as staff. Remove that view once confirmed.

---

## Database Backups

Backups use 4 k8s CronJobs defined in `k8s/cronjob-backup.yaml`. The PVC (`k8s/backup-pvc.yaml`, 5Gi RWO) is a local staging area; S3 is the durable store.

| Job | Schedule | What it does |
|---|---|---|
| `backup-local` | Every 6h | pg_dump (custom format, compress=9) → PVC, keeps 7 days |
| `backup-cloud-daily` | 2am daily | Reads latest from PVC → S3 daily path |
| `backup-cloud-monthly` | 3am on 1st | Reads latest from PVC → S3 monthly path |
| `backup-cloud-yearly` | 4am on Jan 1st | Reads latest from PVC → S3 yearly path |

**S3 bucket:** `jay-curtis-backup` (same bucket used across all projects, region `us-east-1`, `STANDARD_IA` storage class)
**S3 prefix:** `unscripted-living/backups/{daily,monthly,yearly}/YYYY/[MM/[DD]]/`

**AWS credentials:** Reuses existing `aws_access_key_id` / `aws_secret_access_key` keys from the `unscripted-living` SealedSecret. Ensure that IAM user has `s3:PutObject` and `s3:ListBucket` on `jay-curtis-backup`.

**Apply:**
```bash
kubectl apply -f k8s/backup-pvc.yaml
kubectl apply -f k8s/cronjob-backup.yaml
kubectl get cronjobs -n unscripted-living
```

**Test (triggers local backup immediately):**
```bash
kubectl create job --from=cronjob/unscripted-living-backup-local test-local -n unscripted-living
kubectl logs -n unscripted-living job/test-local -f
```

**Restore:**
```bash
# Download from S3
aws s3 cp s3://jay-curtis-backup/unscripted-living/backups/daily/YYYY/MM/DD/<file>.dump ./restore.dump
# Restore into running pod
kubectl exec -n unscripted-living -it <pod> -- /bin/sh
pg_restore -h postgresql-rw.postgresql.svc.cluster.local -U $POSTGRES_USER -d $POSTGRES_DB --clean restore.dump
```

---

## Common Pitfalls

| Pitfall | Fix |
|---|---|
| `ALLOWED_HOSTS` rejects raw IP access | Expected — add the domain, not IPs |
| allauth deprecation warnings for `ACCOUNT_AUTHENTICATION_METHOD` | Use `ACCOUNT_LOGIN_METHODS = {'email'}` and `ACCOUNT_SIGNUP_FIELDS` instead |
| `manage.py check --deploy` SSL redirect warning | Set `SECURE_SSL_REDIRECT = False` — Cloudflare terminates TLS |
| `psql` fails with "database X does not exist" | Always connect with `-d postgres` first |
| base64 in `k8s/temp.yaml` is wrong | Always generate with `echo -n 'value' | base64`, never type manually |
| `kubeseal` output is empty | Ensure the controller is running: `kubectl get pods -n sealed-secrets` |
| Static files 404 in production | `collectstatic` must run during Docker build, not at container start |
| Google OAuth redirect mismatch | Authorized redirect URI in Google Cloud Console must exactly match the callback URL |
