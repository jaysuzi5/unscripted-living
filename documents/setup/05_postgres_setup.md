## PostgreSQL Setup

The `unscripted-living` blog uses a shared PostgreSQL instance (same server as jautolog).

---

### Database Details
- **Instance:** Shared k8s PostgreSQL
- **External address:** 192.168.86.201:30004 (for local dev)
- **Internal k8s address:** `postgresql-rw.postgresql.svc.cluster.local:5432` (for k8s pods)
- **Database name:** `unscripted-living`

Credentials are stored in:
- `.env` — for local development (gitignored, never committed)
- `k8s/secrets.yaml` — SealedSecret for k8s deployment (safe to commit when sealed)

---

### Create the Database (already done)

```bash
PGPASSWORD='...' psql -h 192.168.86.201 -p 30004 -U jcurtis -d postgres -c 'CREATE DATABASE "unscripted-living" OWNER jcurtis;'
```

---

### Run Django Migrations (already done — initial setup)

```bash
uv run python manage.py migrate
```

---

### Create Superuser

```bash
uv run python manage.py createsuperuser
```

---

### Kubernetes Sealed Secrets

Credentials for k8s are managed as SealedSecrets so they can be safely committed to git.

**Step 1 — Check `k8s/temp.yaml` exists** (created during project setup, gitignored)

**Step 2 — Seal it:**

```bash
kubeseal -f k8s/temp.yaml -o yaml > k8s/secrets.yaml
```

**Step 3 — Delete temp.yaml immediately:**

```bash
rm k8s/temp.yaml
```

**Step 4 — Apply the sealed secret:**

```bash
kubectl apply -f k8s/secrets.yaml
```

**Step 5 — Verify:**

```bash
kubectl get secrets -n unscripted-living
```

---

### pgAdmin Connection (Local Reference)

To connect via pgAdmin:
- **Host:** 192.168.86.201
- **Port:** 30004
- **Database:** unscripted-living
- **Username:** (see .env)

---

### Backup

Backups are not yet configured. See roadmap Phase 10 for the cronjob-backup.yaml setup.
The `k8s/backup-pvc.yaml` is already created for when backups are enabled.
