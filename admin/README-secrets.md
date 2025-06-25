# Secrets Management

This repo uses [SealedSecrets](https://github.com/bitnami-labs/sealed-secrets) to safely store secrets in Git.

## 🔑 Workflow
```sh
kubectl get pods -A | grep sealed-secrets-controller

kubectl get secret -n kube-system sealed-secret-key -o jsonpath='{.data.tls\.crt}' | base64 -d > pub-cert.pem

```

1. Create a Secret YAML (do NOT commit).
2. Seal it:
   ```sh
   kubeseal --format=yaml --cert=pub-cert.pem < mysecret.yaml > mysealedsecret.yaml
   ```
3. Commit the SealedSecret to Git.
4. ArgoCD applies it; the controller creates the real Secret.


## 🔄 Rotate/Update

- Create a new Secret YAML, seal, and replace the old SealedSecret in Git.

## 📝 Best Practices

- Never commit unsealed secrets.
- Use env vars in deployments to reference secrets.
- Keep the cluster's public key safe.

---