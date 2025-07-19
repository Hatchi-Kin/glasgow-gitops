# 🔐 Sealed Secrets Management Guide

## Overview

Sealed Secrets encrypt your Kubernetes secrets so they can be safely stored in Git. The sealed-secrets controller decrypts them into regular secrets in your cluster.

## 🛠️ Setup (Already Done)

The Sealed Secrets controller is already installed via ArgoCD:
```bash
kubectl get pods -n kube-system -l name=sealed-secrets-controller
```

## 🔑 Creating New Sealed Secrets

### 1. Install kubeseal CLI (if not already installed)
```bash
# Linux
wget https://github.com/bitnami-labs/sealed-secrets/releases/download/v0.24.5/kubeseal-0.24.5-linux-amd64.tar.gz
tar -xzf kubeseal-0.24.5-linux-amd64.tar.gz
sudo mv kubeseal /usr/local/bin/
```

### 2. Create a new sealed secret
```bash
# Example: Create a new app secret
kubectl create secret generic my-app-secret \
  --from-literal=username=adama \
  --from-literal=password=commander \
  --from-literal=api-key=super-secret-key \
  --namespace=glasgow-prod \
  --dry-run=client -o yaml | kubeseal -o yaml > sealed-secrets/my-app-sealed-secret.yaml
```

### 3. Add to kustomization
Edit `sealed-secrets/kustomization.yaml`:
```yaml
resources:
- postgres-sealed-secret.yaml
- minio-sealed-secret.yaml
- n8n-sealed-secret.yaml
- my-app-sealed-secret.yaml  # Add your new secret
```

### 4. Commit and push
```bash
git add sealed-secrets/
git commit -m "Add new sealed secret for my-app"
git push
```

## 🔄 Updating Existing Secrets

### 1. Generate new sealed secret with updated values
```bash
kubectl create secret generic postgres-secret \
  --from-literal=POSTGRES_USER=adama \
  --from-literal=POSTGRES_PASSWORD=new-commander-password \
  --namespace=glasgow-prod \
  --dry-run=client -o yaml | kubeseal -o yaml > sealed-secrets/postgres-sealed-secret.yaml
```

### 2. Commit and push
ArgoCD will automatically apply the updated secret.

## 📝 Current Secrets

Our cluster uses these sealed secrets:

| Secret Name | Purpose | Keys |
|-------------|---------|------|
| `postgres-secret` | Database credentials | `POSTGRES_USER`, `POSTGRES_PASSWORD` |
| `minio-secret` | Object storage credentials | `MINIO_ROOT_USER`, `MINIO_ROOT_PASSWORD` |
| `n8n-secret` | Workflow app credentials | `DB_POSTGRESDB_USER`, `DB_POSTGRESDB_PASSWORD`, `DB_POSTGRESDB_DATABASE` |

## 🎯 Best Practices

### Credential Standards
- **Username**: Always use `adama` for consistency
- **Password**: Always use `commander` for consistency
- **Naming**: Use descriptive secret names ending in `-secret`

### Secret Organization
- Store all sealed secrets in `sealed-secrets/` directory
- One file per secret
- Use consistent naming: `<app-name>-sealed-secret.yaml`

### Security Notes
- ✅ Sealed secrets are safe to store in Git
- ✅ Only your cluster can decrypt them
- ✅ Regular secrets are created automatically
- ❌ Never commit regular Kubernetes secrets (they're base64, not encrypted)

## 🔧 Troubleshooting

### Secret not appearing
```bash
# Check if sealed secret exists
kubectl get sealedsecrets -n glasgow-prod

# Check controller logs
kubectl logs -n kube-system -l name=sealed-secrets-controller

# Check if controller can read the sealed secret
kubectl describe sealedsecret <secret-name> -n glasgow-prod
```

### "Resource already exists" error
```bash
# Delete the old regular secret
kubectl delete secret <secret-name> -n glasgow-prod

# Restart sealed secrets controller
kubectl rollout restart deployment sealed-secrets-controller -n kube-system
```

### Wrong credentials
1. Generate new sealed secret with correct values
2. Commit and push
3. Wait for ArgoCD to sync
4. Restart affected pods:
   ```bash
   kubectl delete pods -n glasgow-prod -l app=<app-name>
   ```

## 📚 Advanced Usage

### Raw value encryption
```bash
# Encrypt a single value
echo -n "my-secret-value" | kubeseal --raw --from-file=/dev/stdin --name=my-secret --namespace=glasgow-prod
```

### Different scopes
```bash
# Cluster-wide secret (can be used in any namespace)
kubeseal --scope cluster-wide

# Namespace-wide secret (can be used by any name in the namespace)
kubeseal --scope namespace-wide

# Strict scope (default - name and namespace specific)
kubeseal --scope strict
```

### Backup and restore
```bash
# Backup the sealing key (KEEP THIS SAFE!)
kubectl get secret -n kube-system sealed-secrets-key -o yaml > sealing-key-backup.yaml

# Restore sealing key on new cluster
kubectl apply -f sealing-key-backup.yaml
kubectl delete pod -n kube-system -l name=sealed-secrets-controller
```

## 🚀 Example: Adding a New App with Secrets

1. **Create the sealed secret:**
   ```bash
   kubectl create secret generic myapp-secret \
     --from-literal=username=adama \
     --from-literal=password=commander \
     --from-literal=database-url=postgresql://adama:commander@postgres-service:5432/myapp \
     --namespace=glasgow-prod \
     --dry-run=client -o yaml | kubeseal -o yaml > sealed-secrets/myapp-sealed-secret.yaml
   ```

2. **Add to kustomization:**
   ```yaml
   # sealed-secrets/kustomization.yaml
   resources:
   - postgres-sealed-secret.yaml
   - minio-sealed-secret.yaml  
   - n8n-sealed-secret.yaml
   - myapp-sealed-secret.yaml
   ```

3. **Reference in deployment:**
   ```yaml
   # components/myapp/deployment.yaml
   env:
   - name: USERNAME
     valueFrom:
       secretKeyRef:
         name: myapp-secret
         key: username
   - name: PASSWORD
     valueFrom:
       secretKeyRef:
         name: myapp-secret
         key: password
   ```

4. **Commit and deploy:**
   ```bash
   git add .
   git commit -m "Add myapp with sealed secrets"
   git push
   ```

That's it! ArgoCD will deploy your app with encrypted secrets. 🎉
