## Kubernetes Setup

The app deploys to the same k8s cluster as jautolog, in a dedicated namespace `unscripted-living`.

---

### Namespace & Deployment

`k8s/deployment.yaml` contains:
1. Namespace: `unscripted-living`
2. Deployment with an init container that runs `migrate` before the app starts
3. LoadBalancer service (port 80 → 8000)

All credentials come from the `unscripted-living` SealedSecret (see `05_postgres_setup.md`).

---

### Build & Push Docker Image

```bash
uv lock  # ensure uv.lock is up to date first
docker buildx build --platform linux/amd64,linux/arm64 -t jaysuzi5/unscripted-living:latest --push .
```

---

### Deploy

```bash
# First time: apply everything
kubectl apply -f k8s/secrets.yaml
kubectl apply -f k8s/deployment.yaml

# Subsequent deploys (after pushing new image)
kubectl rollout restart deployment unscripted-living -n unscripted-living
```

---

### Verify

```bash
kubectl get all -n unscripted-living
kubectl logs -n unscripted-living deploy/unscripted-living --follow
```

---

### Access

After the LoadBalancer gets an IP from MetalLB:

```bash
kubectl get service unscripted-living -n unscripted-living
```

---

### Cloudflare Tunnel

Add a route in Cloudflare Zero Trust (same tunnel as jautolog):

1. Go to **Networks → Connectors** → Edit existing tunnel
2. **Add a published application route:**
   - Subdomain: `unscripted`
   - Domain: `jaycurtis.org`
   - Type: HTTP
   - URL: `unscripted-living.unscripted-living.svc.cluster.local:80`

Test at: https://unscripted.jaycurtis.org/

---

### Post-Deploy Steps

After first deploy with a fresh database:

1. Exec into the pod:
   ```bash
   kubectl exec -n unscripted-living -it $(kubectl get pod -n unscripted-living -l app=unscripted-living -o name | head -1) -- /bin/sh
   ```

2. Create superuser:
   ```bash
   uv run python manage.py createsuperuser
   ```

3. Log in to `/admin` and:
   - Create Categories (name, slug, icon, color, description)
   - Register Google OAuth Social App (after configuring Google Cloud)
