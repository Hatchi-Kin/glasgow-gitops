# MinIO Access Guide

MinIO provides S3-compatible object storage and a web UI.

## 🚪 Access MinIO Console

```sh
kubectl -n minio-prod port-forward svc/minio-service 9001:9001
```
Then open: [http://localhost:9001](http://localhost:9001)

**Credentials:**
- Username/Password: from your sealed secret (see `minio-prod-sealed-secret.yaml`)
- Or retrieve from the cluster:
  ```sh
  kubectl -n minio-prod get secret minio-secret -o jsonpath="{.data.root-user}" | base64 -d; echo
  kubectl -n minio-prod get secret minio-secret -o jsonpath="{.data.root-password}" | base64 -d; echo
  ```

## 📦 S3 API

- S3 API: `http://localhost:9000` (via port-forward if needed)

---
**Tip:** Credentials are in the sealed secret or by decoding `minio-secret` in `minio-prod` namespace.