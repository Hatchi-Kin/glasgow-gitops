# Remove Laptop Node (adama) - GitOps Migration Plan

## Overview

Remove the laptop node (adama) from the cluster to reduce power consumption while maintaining all services except GPU-based OpenL3 inference.

**GitOps Principle:** Prepare all Git changes first, THEN adjust infrastructure. The repo is the source of truth.

## Current Architecture

```
Master:  adama     (192.168.1.20)  - Laptop with GPU
Workers: boomer    (192.168.1.21)  - N100, primary storage node (226GB Longhorn)
         apollo    (192.168.1.22)  - N100
         starbuck  (192.168.1.23)  - N100
```

## New Architecture

```
Master:  starbuck  (192.168.1.23)  - N100, new control plane
Workers: boomer    (192.168.1.21)  - N100, primary storage node
         apollo    (192.168.1.22)  - N100
```

**Why starbuck?**
- Lowest disk usage (11%) - plenty of room for control plane
- Separates control plane from heavy storage (boomer has 226GB Longhorn data)
- Better architecture for resilience

---

## What Changes

### Services Removed (via GitOps)
- ❌ **msv2-inference** (OpenL3 Knative service) - GPU inference
- ❌ **nvidia-device-plugin** - GPU management

### Services Unchanged
- ✅ All applications continue running (postgres, minio, apis, webapp)
- ✅ CLAP inference (CPU-based) remains operational
- ✅ Existing OpenL3 embeddings in database remain accessible
- ✅ Longhorn storage continues on workers (already there)
- ✅ All other infrastructure (ArgoCD, Traefik, etc.)

### Configuration Updates (via GitOps)
- 🔄 IP addresses: 192.168.1.20 → 192.168.1.23
- 🔄 Admin scripts: Update node lists

### Infrastructure Changes (manual)
- 🔧 Control plane: adama → starbuck
- 🔧 Cluster nodes: 4 → 3

---

## Migration Steps

### Phase 1: Prepare & Backup (10 minutes)

#### 1.1 Backup Critical Components

```bash
cd /home/kin/Documents/glasgow-gitops

# Backup sealed secrets master key (CRITICAL!)
kubectl get secret -n kube-system sealed-secrets-key -o yaml > /tmp/sealed-secrets-key-backup.yaml

# Verify backup
cat /tmp/sealed-secrets-key-backup.yaml | grep -A 1 "tls.crt"

# Backup postgres (optional - for safety)
kubectl exec -n glasgow-prod deployment/postgres -- pg_dumpall -U postgres > /tmp/postgres_backup_$(date +%Y%m%d).sql

# Document current state
kubectl get nodes -o wide > /tmp/nodes_before.txt
kubectl get pods -A -o wide > /tmp/pods_before.txt
kubectl get applications -n argocd > /tmp/apps_before.txt
```

#### 1.2 Verify Current Health

```bash
# Run health check
python3 admin/quick_check.py

# Ensure all nodes are Ready and all apps are Healthy
```

---

### Phase 2: Prepare All GitOps Changes (30 minutes)

**Important:** Make ALL Git changes in this phase. Do NOT push until Phase 4.

#### 2.1 Create a Migration Branch (Optional but Recommended)

```bash
cd /home/kin/Documents/glasgow-gitops

# Create branch for changes
git checkout -b remove-laptop-node

# Or work directly on main
```

#### 2.2 Remove GPU Services

```bash
# Remove OpenL3 inference service
rm argocd/apps/msv2-inference.yaml
rm -rf components/msv2-inference/

# Remove NVIDIA device plugin
rm argocd/apps/nvidia-device-plugin.yaml
rm -rf components/nvidia-device-plugin/

# Verify removals
git status
```

#### 2.3 Update msv2-api Configuration (Optional)

If you want to clean up the reference to removed OpenL3 service:

**Edit `components/fastapi-msv2-api/configmap.yaml`:**
```yaml
# Comment out or remove:
# MSV2_INFERENCE_URL: "http://msv2-inference.glasgow-prod.svc.cluster.local"
```

Or leave it as-is if your API code handles unavailable services gracefully.

#### 2.4 Update IP Addresses Automatically

```bash
# Run automated IP update script
python3 admin/update_network_ips.py

# When prompted:
# OLD IP: 192.168.1.20
# NEW IP: 192.168.1.23
# Run in DRY RUN mode first: y
# Review changes
# Then run again for real: n (no dry run), yes (proceed)
```

This updates:
- All ingress resources (*.nip.io domains)
- ArgoCD configuration
- CORS origins
- MinIO browser URL
- Home Assistant config
- Traefik middleware

#### 2.5 Update Admin Scripts

**Edit `admin/quick_check.py`:**
```python
HOSTS = [
    ("starbuck", "192.168.1.23", "master"),  # New control plane
    ("boomer", "192.168.1.21", "worker"),
    ("apollo", "192.168.1.22", "worker"),
]
```

**Edit `admin/cleanup_longhorn.py`:**
```python
HOSTS = [
    ("starbuck", "192.168.1.23", "master"),  # New control plane
    ("boomer", "192.168.1.21", "worker"),
    ("apollo", "192.168.1.22", "worker"),
]
```

**Edit `admin/shutdown_cluster.py`:**
```python
NODES = [
    ("boomer", "192.168.1.21"),
    ("apollo", "192.168.1.22"),
    ("starbuck", "192.168.1.23"),  # Control plane last
]
```

**Edit `admin/fix_routes.sh`:**
```bash
NODES=("192.168.1.21" "192.168.1.22" "192.168.1.23")

# Update the restart line at the end (around line 13):
sshpass -p "$PASSWORD" ssh -o StrictHostKeyChecking=no bsg@192.168.1.23 'sudo systemctl restart k3s'
```

**Edit `admin/choose_master.py`:**
```python
WORKERS = [
    ("boomer", "192.168.1.21"),
    ("apollo", "192.168.1.22"),
    ("starbuck", "192.168.1.23"),  # Now it's the master, but keep in list
]
```

#### 2.6 Update README

**Edit `README.md`:**

Find the Architecture section and update to:
```markdown
## 🏗️ Architecture Overview

- **Kubernetes**: K3s v1.32.6+k3s1
- **Control Plane**: starbuck (192.168.1.23)
- **Workers**: boomer (192.168.1.21), apollo (192.168.1.22)
- **Storage**: Longhorn distributed storage (primarily on boomer)
- **GitOps**: ArgoCD for automated deployments
- **Ingress**: Traefik with nip.io for external access
- **Secrets**: Sealed Secrets for secure credential management

## 🌐 Service Access

All services are accessible via the control plane IP with nip.io:

| Service | URL | Credentials |
|---------|-----|-------------|
| **FastAPI** | http://fastapi.192.168.1.23.nip.io | - |
| **MinIO Console** | http://minio.192.168.1.23.nip.io | See Sealed Secrets |
| **n8n Workflow** | http://n8n.192.168.1.23.nip.io | See Sealed Secrets |
| **ArgoCD** | http://argocd.192.168.1.23.nip.io| `admin` / see admin password |

*Note: GPU-based OpenL3 inference removed to reduce power consumption*

# if SchedulingDisabled
```sh
NAME       STATUS                     ROLES                  AGE    VERSION
starbuck   Ready                      control-plane,master   116d   v1.32.6+k3s1
``` 

**Network Info:**
- Control Plane: `starbuck` (192.168.1.23)
- Workers: `boomer` (192.168.1.21), `apollo` (192.168.1.22)
```

#### 2.7 Review All Changes

```bash
# Review everything before committing
git status
git diff

# Check expected changes:
# - GPU services removed (2 apps, 2 component dirs)
# - IPs updated (192.168.1.20 → 192.168.1.23)
# - Admin scripts updated (5 files)
# - README updated

# Count changed files
git status --short | wc -l
# Should be around 20-30 files
```

**STOP HERE - DO NOT COMMIT OR PUSH YET!**

---

### Phase 3: Infrastructure Migration (45 minutes)

**Now we prepare the cluster infrastructure to match the Git changes.**

#### 3.1 Get Token from Current Master

```bash
# SSH into adama
ssh bsg@192.168.1.20

# Get the K3s server token
sudo cat /var/lib/rancher/k3s/server/node-token

# Copy this token - you'll need it next
# Exit SSH
exit
```

#### 3.2 Add Starbuck as Control Plane

```bash
# SSH into starbuck
ssh bsg@192.168.1.23

# Stop the k3s agent service
sudo systemctl stop k3s-agent
sudo systemctl disable k3s-agent

# Install K3s as a server (control plane), joining existing cluster
curl -sfL https://get.k3s.io | K3S_TOKEN="<paste-token-from-adama>" \
  sh -s - server \
  --server https://192.168.1.20:6443 \
  --disable traefik \
  --write-kubeconfig-mode 644 \
  --tls-san 192.168.1.23

# Wait for service to start
sudo systemctl status k3s

# Check logs if needed
sudo journalctl -u k3s -f

# Exit SSH
exit
```

#### 3.3 Verify Dual Control Plane

```bash
# From your workstation - check nodes
kubectl get nodes

# Should see 4 nodes with TWO control-planes:
# NAME       STATUS   ROLES                  AGE
# adama      Ready    control-plane,master   356d
# starbuck   Ready    control-plane,master   1m    ← NEW
# boomer     Ready    worker                 356d
# apollo     Ready    worker                 356d

# Verify etcd/control plane health
kubectl get pods -n kube-system | grep -E "kube-apiserver|kube-scheduler|kube-controller"

# Check both control planes are working
kubectl get endpoints -n kube-system
```

#### 3.4 Drain Laptop Node

```bash
# Cordon adama (prevent new pods from scheduling)
kubectl cordon adama

# Verify cordoned
kubectl get nodes
# adama should show "Ready,SchedulingDisabled"

# Drain all workloads from adama
kubectl drain adama --ignore-daemonsets --delete-emptydir-data --force

# This will:
# - Evict all pods from adama
# - Cause ~5 minutes downtime as pods reschedule
# - MinIO will move to another node

# Watch pods reschedule
watch 'kubectl get pods -A -o wide | grep -v Running'

# Wait until all pods are Running on other nodes
# Press Ctrl+C when done
```

**Expected:** Pods will restart on boomer, apollo, or starbuck. MinIO will likely move to boomer.

#### 3.5 Delete Laptop Node from Cluster

```bash
# Verify no important pods are still on adama
kubectl get pods -A -o wide | grep adama
# Should only show daemonsets or nothing

# Remove node from cluster
kubectl delete node adama

# Verify removal
kubectl get nodes
# Should show only 3 nodes:
# starbuck (control-plane), boomer (worker), apollo (worker)
```

#### 3.6 Update Local kubectl Config

```bash
# Get kubeconfig from new control plane (starbuck)
scp bsg@192.168.1.23:/etc/rancher/k3s/k3s.yaml ~/.kube/config

# Update server IP in config
sed -i 's/127.0.0.1/192.168.1.23/g' ~/.kube/config

# Test connection
kubectl get nodes

# Should show 3 nodes, all Ready:
# NAME       STATUS   ROLES                  AGE
# starbuck   Ready    control-plane,master   Xm
# boomer     Ready    worker                 356d
# apollo     Ready    worker                 356d
```

---

### Phase 4: GitOps Sync (20 minutes)

**Now push Git changes and let ArgoCD reconcile everything.**

#### 4.1 Commit and Push Changes

```bash
cd /home/kin/Documents/glasgow-gitops

# Final review
git status
git diff --stat

# Commit everything
git add .
git commit -m "Remove laptop node (adama), promote starbuck to control plane

- Remove msv2-inference (OpenL3 GPU service)
- Remove nvidia-device-plugin  
- Update all service IPs: 192.168.1.20 → 192.168.1.23
- Update admin scripts for 3-node cluster
- New control plane: starbuck (192.168.1.23)
- Storage primary: boomer (192.168.1.21)"

# Push to trigger ArgoCD reconciliation
git push origin main
```

#### 4.2 Monitor ArgoCD Sync

```bash
# Watch ArgoCD detect and sync changes
watch kubectl get applications -n argocd

# Expected changes:
# - msv2-inference: will disappear (app removed from Git)
# - nvidia-device-plugin: will disappear (app removed from Git)
# - Other apps: may show "OutOfSync" then "Synced" as they update
```

#### 4.3 Handle Removed Applications

ArgoCD will see that msv2-inference and nvidia-device-plugin are gone from Git:

```bash
# Check if apps auto-deleted
kubectl get application msv2-inference -n argocd
kubectl get application nvidia-device-plugin -n argocd

# If they still exist, delete manually
kubectl delete application msv2-inference -n argocd --ignore-not-found
kubectl delete application nvidia-device-plugin -n argocd --ignore-not-found

# Delete the actual Knative service and daemonset
kubectl delete service.serving.knative.dev msv2-inference -n glasgow-prod --ignore-not-found
kubectl delete daemonset nvidia-device-plugin-daemonset -n kube-system --ignore-not-found
```

#### 4.4 Sync All Applications

```bash
# Force sync of root app to cascade to all children
kubectl patch application root-app -n argocd --type merge \
  -p='{"operation":{"initiatedBy":{"username":"admin"},"sync":{"revision":"HEAD"}}}'

# Or sync via ArgoCD UI
kubectl port-forward svc/argocd-server -n argocd 8080:443 &

# Open browser to: https://localhost:8080
# Login: admin / <get password with command below>
kubectl -n argocd get secret argocd-initial-admin-secret -o jsonpath="{.data.password}" | base64 -d && echo

# In UI: Sync root-app and all out-of-sync apps
```

#### 4.5 Wait for Full Reconciliation

```bash
# Watch until all apps are synced
watch kubectl get applications -n argocd

# All remaining apps should show:
# SYNC STATUS: Synced
# HEALTH STATUS: Healthy

# Check pods have restarted with new configurations
kubectl get pods -A -o wide

# Ingress resources should have new IPs
kubectl get ingress -A
# Should show 192.168.1.23.nip.io domains
```

---

### Phase 5: Cleanup Laptop (5 minutes)

```bash
# SSH into laptop
ssh bsg@192.168.1.20

# Uninstall K3s completely
/usr/local/bin/k3s-uninstall.sh

# Verify removal
sudo systemctl status k3s
# Should show "could not be found"

# Optional: Clean up NVIDIA artifacts
sudo apt-get remove --purge nvidia-container-toolkit
sudo apt-get autoremove

# Shutdown laptop
sudo shutdown -h now
```

**You can now physically unplug the laptop.**

---

### Phase 6: Verification (15 minutes)

#### 6.1 Cluster Health

```bash
# Run comprehensive health check
python3 admin/quick_check.py

# Verify:
# - 3 nodes (starbuck, boomer, apollo)
# - All nodes Ready
# - System temp check works for all 3
```

#### 6.2 ArgoCD Applications

```bash
# Check all apps are synced
kubectl get applications -n argocd

# Should NOT see:
# - msv2-inference
# - nvidia-device-plugin

# Should see all others as Synced/Healthy:
# - argocd-image-updater
# - cert-manager
# - coredns
# - fastapi
# - fastapi-msv2-api
# - glasgow-sealed-secrets
# - home-assistant
# - ingress
# - knative
# - longhorn
# - minio
# - msv2-clap-inference (CLAP remains!)
# - msv2-webapp
# - n8n
# - postgres
# - sealed-secrets
# - wireguard
```

#### 6.3 Storage Health

```bash
# Check Longhorn volumes
kubectl get pv

# All should be Bound
kubectl get pvc -A

# Check Longhorn UI (with new IP)
# Open: http://longhorn.192.168.1.23.nip.io

# Verify:
# - All volumes Healthy
# - Replicas distributed across boomer and apollo
# - No degraded volumes
```

#### 6.4 Test Services with New IPs

```bash
# API health checks
curl http://fastapi.192.168.1.23.nip.io/health
curl http://msv2-api.192.168.1.23.nip.io/health

# MinIO
curl http://minio.192.168.1.23.nip.io

# ArgoCD
curl -k https://argocd.192.168.1.23.nip.io
```

**Access in browser:**
- http://msv2-webapp.192.168.1.23.nip.io
- http://msv2-api.192.168.1.23.nip.io/docs
- http://minio.192.168.1.23.nip.io
- http://argocd.192.168.1.23.nip.io
- http://longhorn.192.168.1.23.nip.io
- http://homeassistant.192.168.1.23.nip.io

#### 6.5 Test Application Features

- [ ] Webapp loads and shows music library
- [ ] File explorer view works
- [ ] CLAP semantic search works (CPU-based)
- [ ] pgvector similarity search works (using existing embeddings)
- [ ] 3D visualizations render
- [ ] LangGraph agent responds
- [ ] MinIO console accessible
- [ ] Can stream/play music files

**Expected failures:**
- ❌ OpenL3 inference endpoint unavailable (removed)
- ❌ Any features that call msv2-inference service

#### 6.6 Verify Resource Distribution

```bash
# Check which node hosts what
kubectl get pods -A -o wide | awk '{print $8}' | sort | uniq -c

# Check resource usage
kubectl top nodes

# Starbuck should have:
# - Control plane components
# - Some application pods

# Boomer should have:
# - Heavy storage workloads (MinIO likely here)
# - Many application pods

# Apollo should have:
# - Application pods
# - Balanced workloads
```

---

## Rollback Plan

### Before Node Deletion

If you need to abort before deleting adama:

```bash
# Uncordon adama
kubectl uncordon adama

# Pods will start scheduling back on it
```

### After Node Deletion

If you need to restore after deleting adama:

```bash
# 1. Revert Git changes
git revert HEAD
git push origin main

# 2. Re-add laptop as server
# On laptop:
curl -sfL https://get.k3s.io | K3S_TOKEN="<token>" \
  sh -s - server \
  --server https://192.168.1.23:6443

# 3. ArgoCD will restore GPU services
```

---

## Post-Migration Tasks

### Update External Documentation

```bash
# Search for any remaining references
grep -r "192.168.1.20" docs/
grep -r "adama" docs/ | grep -v "REMOVE_LAPTOP_NODE"

# Update found files
```

### Monitor for 24-48 Hours

```bash
# Run periodic health checks
watch -n 300 'python3 admin/quick_check.py'

# Monitor ArgoCD
kubectl get applications -n argocd

# Check for any pod restarts
kubectl get pods -A | grep -v "Running\|Completed"
```

### Power Down Permanently

After 24-48 hours of stable operation:
- Unplug laptop from power
- Store safely (can be added back if needed)

---

## Summary

**Time Required:** ~2 hours total
**Downtime:** ~5 minutes (during pod drain/reschedule)
**Risk Level:** Low (GitOps-driven, reversible)

**GitOps Flow:**
1. ✅ Prepare all Git changes (source of truth)
2. ✅ Migrate infrastructure (add starbuck, remove adama)
3. ✅ Push Git changes
4. ✅ ArgoCD reconciles everything automatically

**What You Gain:**
- ✅ ~45W power savings (50% reduction)
- ✅ Simpler 3-node cluster
- ✅ Better architecture (control plane separate from storage)
- ✅ All critical services maintained
- ✅ Full GitOps control

**What You Lose:**
- ❌ OpenL3 GPU inference (not actively used)

**Repo remains source of truth - GitOps philosophy maintained!**
