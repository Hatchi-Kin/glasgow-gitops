# K3s Homelab Cluster

A simple bare-metal K3s cluster for learning and homelab use.

## Nodes

| Hostname   | Role           | Specs           | IP              |
|------------|----------------|-----------------|-----------------|
| adama      | control plane  | i5-7200U, 8GB   | 192.168.1.20    |
| boomer     | worker         | N150, 16GB      | 192.168.1.21    |
| apollo     | worker         | N150, 16GB      | 192.168.1.22    |
| starbuck   | worker         | N150, 16GB      | 192.168.1.23    |

## Install Steps

1. **Install K3s on control plane:**
   ```sh
   ssh bsg@adama
   curl -sfL https://get.k3s.io | sh -
   ```
2. **Get node token:**
   ```sh
   sudo cat /var/lib/rancher/k3s/server/node-token
   ```
3. **Join workers:**
   ```sh
   ssh bsg@<worker>
   curl -sfL https://get.k3s.io | K3S_URL=https://192.168.1.20:6443 K3S_TOKEN=<NODE_TOKEN> sh -s - agent
   ```
4. **Verify:**
   ```sh
   kubectl get nodes
   ```
5. **Label workers:**
   ```sh# MinIO Access Guide

MinIO provides S3-compatible object storage and a web UI for management.

## 🚪 Accessing the MinIO Console (UI)

To access the MinIO web UI (console) on port 9001:

```bash
kubectl -n minio-prod port-forward svc/minio-service 9001:9001
```

Then open your browser and go to:  
[http://localhost:9001](http://localhost:9001)

**Login credentials:**  
- Username/Password: from your sealed secret (see `minio-prod-sealed-secret.yaml`)
- Or retrieve from the cluster:
  ```sh
  kubectl -n minio-prod get secret minio-secret -o jsonpath="{.data.root-user}" | base64 -d; echo
  kubectl -n minio-prod get secret minio-secret -o jsonpath="{.data.root-password}" | base64 -d; echo
  ```

## 📦 S3 API

- The S3 API is available at `http://localhost:9000` (via port-forward if needed).

---

**Tip:**  
You can find your MinIO credentials in the `minio-prod-sealed-secret.yaml` or by decoding the `minio-secret` in the `minio-prod` namespace.
   kubectl label node boomer node-role.kubernetes.io/worker=worker
   kubectl label node apollo node-role.kubernetes.io/worker=worker
   kubectl label node starbuck node-role.kubernetes.io/worker=worker
   ```
6. **Remote kubeconfig:**
   ```sh
   sudo cp /etc/rancher/k3s/k3s.yaml ~/k3s-remote.yaml
   sed -i 's/127.0.0.1/192.168.1.20/' ~/k3s-remote.yaml
   scp bsg@192.168.1.20:~/k3s-remote.yaml ~/k3s.yaml
   export KUBECONFIG=~/k3s.yaml
   ```

---

- [K3s Docs](https://k3s.io/)
- [Kubernetes Docs](https://kubernetes.io/docs/)
