# Backup Setup Instructions

This documents the steps required to get the daily/monthly/yearly S3 backups working. These steps were first debugged on `unscripted-living` and apply identically to any project using the same k8s + SealedSecrets + `jay-curtis-backup` pattern.

---

## How the backup system works

Four CronJobs run in the app's k8s namespace:

| Job | Schedule | What it does |
|-----|----------|--------------|
| `<app>-backup-local` | Every 6h | `pg_dump` → PVC (7-day rolling retention) |
| `<app>-backup-cloud-daily` | 2 AM daily | Uploads latest dump → `s3://jay-curtis-backup/<app>/backups/daily/YYYY/MM/DD/` |
| `<app>-backup-cloud-monthly` | 3 AM on 1st | Uploads latest dump → `s3://jay-curtis-backup/<app>/backups/monthly/YYYY/MM/` |
| `<app>-backup-cloud-yearly` | 4 AM on Jan 1 | Uploads latest dump → `s3://jay-curtis-backup/<app>/backups/yearly/YYYY/` |

The local job writes to a PersistentVolumeClaim; the cloud jobs read from that same PVC and upload to S3 using the AWS CLI.

---

## Three things that commonly break this

### 1. Wrong IAM credentials in the secret

The cloud backup jobs need credentials for the **backup IAM user**, which has write access to `jay-curtis-backup`. Projects often have a **media IAM user** stored in the secret instead — that user has no access to `jay-curtis-backup` and silently fails.

**How to check:** decode the secret and look at the key ID.

```bash
kubectl get secret <app> -n <app> -o jsonpath='{.data.aws_access_key_id}' | base64 -d
```

If the key ID matches the media user (not the backup user), it's wrong for backups. Cross-reference against the `jautolog` secret's `AWS_ACCESS_KEY_ID` — that's the known-good backup user key.

**Fix:** add `backup_access_key_id` and `backup_secret_access_key` to the secret with the backup user's credentials, reseal, and update the cronjob YAML to reference those keys (see steps below).

Alternatively, if the project has no separate media S3 user, the existing `aws_access_key_id`/`aws_secret_access_key` keys can simply be updated to the backup user values.

### 2. PVC missing storage class

Without `storageClassName: nfs-client`, the PVC stays `Pending` and the backup pod never schedules.

**How to check:**
```bash
kubectl get pvc -n <app>
```
A `Pending` PVC with no `STORAGECLASS` listed is the symptom.

**Fix:** add `storageClassName: nfs-client` to `k8s/backup-pvc.yaml`, delete the old PVC, and reapply.

### 3. CronJobs never deployed

The YAML exists in the repo but `kubectl apply` was never run.

**How to check:**
```bash
kubectl get cronjobs -n <app>
```
If this returns nothing, the jobs are not deployed.

---

## Step-by-step fix

### Step 1 — Update the sealed secret

Create `k8s/temp.yaml` with all existing secret values **plus** the backup credentials. Include every existing key so the seal replaces the whole secret correctly.

```yaml
apiVersion: v1
kind: Secret
metadata:
  name: <app>
  namespace: <app>
type: Opaque
stringData:
  # ... all existing keys/values ...
  backup_access_key_id: "<backup-iam-key-id>"
  backup_secret_access_key: "<backup-iam-secret>"
```

Seal it and delete the plaintext file immediately:

```bash
kubeseal --format=yaml --secret-file k8s/temp.yaml > k8s/secrets.yaml
rm k8s/temp.yaml
kubectl apply -f k8s/secrets.yaml
```

### Step 2 — Fix the cronjob YAML

In `k8s/cronjob-backup.yaml`, all three cloud jobs (`daily`, `monthly`, `yearly`) must reference the backup credentials, not the media credentials:

```yaml
env:
- name: AWS_ACCESS_KEY_ID
  valueFrom:
    secretKeyRef:
      name: <app>
      key: backup_access_key_id        # not aws_access_key_id
- name: AWS_SECRET_ACCESS_KEY
  valueFrom:
    secretKeyRef:
      name: <app>
      key: backup_secret_access_key    # not aws_secret_access_key
```

### Step 3 — Fix the PVC

Ensure `k8s/backup-pvc.yaml` has the storage class:

```yaml
spec:
  accessModes:
    - ReadWriteOnce
  storageClassName: nfs-client
  resources:
    requests:
      storage: 5Gi
```

If the PVC already exists without the storage class:

```bash
kubectl delete pvc <app>-postgres-backup-pvc -n <app>
kubectl apply -f k8s/backup-pvc.yaml
```

### Step 4 — Deploy the cronjobs

```bash
kubectl apply -f k8s/cronjob-backup.yaml
kubectl get cronjobs -n <app>
```

---

## Testing

Run the local and cloud jobs manually to verify before waiting for the schedule:

```bash
# Local backup
kubectl create job -n <app> --from=cronjob/<app>-backup-local test-local-1
kubectl wait -n <app> --for=condition=complete job/test-local-1 --timeout=120s
kubectl logs -n <app> job/test-local-1

# Daily cloud upload
kubectl create job -n <app> --from=cronjob/<app>-backup-cloud-daily test-cloud-1
kubectl wait -n <app> --for=condition=complete job/test-cloud-1 --timeout=120s
kubectl logs -n <app> job/test-cloud-1

# Clean up
kubectl delete job -n <app> test-local-1 test-cloud-1
```

A successful cloud upload log ends with:

```
Uploaded to: s3://jay-curtis-backup/<app>/backups/daily/YYYY/MM/DD/<filename>.dump
```

---

## IAM reference

| User | Key ID | Has access to |
|------|--------|---------------|
| Backup user | (retrieve from `jautolog` secret → `AWS_ACCESS_KEY_ID`) | `jay-curtis-backup` (all projects) |
| unscripted-living media user | (retrieve from `unscripted-living` secret → `aws_access_key_id`) | `unscripted-living-media` only |
| jAutolog media user | (retrieve from `jautolog` secret → `AWS_MEDIA_ACCESS_KEY_ID`) | `jautolog-media` only |

The backup user credentials live in the `jautolog` secret under `AWS_ACCESS_KEY_ID` / `AWS_SECRET_ACCESS_KEY` if you need to retrieve them from a known-good source.
