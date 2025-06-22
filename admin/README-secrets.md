# Secrets Management

This repo uses [SealedSecrets](https://github.com/bitnami-labs/sealed-secrets) to safely store secrets in Git.

## 🔑 Workflow

1. Create a Secret YAML (do NOT commit).
2. Seal it:
   ```sh
   kubeseal --format=yaml --cert=pub-cert.pem < mysecret.yaml > mysealedsecret.yaml
   ```
3. Commit the SealedSecret to Git.
4. ArgoCD applies it; the controller creates the real Secret.

## 📁 Where Secrets Live

- SealedSecrets are in each component's overlay, e.g.:
  - `components/minio/overlays/prod/minio-prod-sealed-secret.yaml`
  - `components/postgres/overlays/prod/postgres-prod-sealed-secret.yaml`

## 🔄 Rotate/Update

- Create a new Secret YAML, seal, and replace the old SealedSecret in Git.

## 📝 Best Practices

- Never commit unsealed secrets.
- Use env vars in deployments to reference secrets.
- Keep the cluster's public key safe.

---