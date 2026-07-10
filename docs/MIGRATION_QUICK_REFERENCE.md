# Migration Quick Reference - GitOps Flow

One-page command reference for removing laptop node.

**GitOps Principle:** Prepare Git changes → Migrate infrastructure → Push changes → ArgoCD syncs

## Architecture Change

```
BEFORE:  adama (master, .20) + boomer (.21) + apollo (.22) + starbuck (.23)
AFTER:   starbuck (master, .23) + boomer (.21) + apollo (.22)
```

---

## Phase 1: Backup (10 min)

```bash
# Critical backup
kubectl get secret -n kube-system sealed-secrets-key -o yaml > /tmp/sealed-secrets-key-backup.yaml

# Optional safety backup
kubectl exec -n glasgow-prod deployment/postgres -- pg_dumpall -U postgres > /tmp/postgres_backup.sql

# Document current state
kubectl get nodes -o wide > /tmp/nodes_before.txt
```

---

## Phase 2: Prepare Git Changes (30 min) - DON'T PUSH YET

```bash
cd /home/kin/Documents/glasgow-gitops

# Remove GPU services
rm argocd/apps/msv2-inference.yaml argocd/apps/nvidia-device-plugin.yaml
rm -rf components/msv2-inference/ components/nvidia-device-plugin/

# Update IPs
python3 admin/update_network_ips.py
# OLD: 192.168.1.20  NEW: 192.168.1.23

# Update admin scripts (manual edits)
# - admin/quick_check.py → starbuck as master
# - admin/cleanup_longhorn.py → starbuck as master
# - admin/shutdown_cluster.py → starbuck last
# - admin/fix_routes.sh → .23 restart
# - admin/choose_master.py → update list
# - README.md → new architecture

# Review but DON'T commit yet
git status
git diff
```

---

## Phase 3: Infrastructure Migration (45 min)

```bash
# Get token from adama
ssh bsg@192.168.1.20
sudo cat /var/lib/rancher/k3s/server/node-token
exit

# On starbuck - add as control plane
ssh bsg@192.168.1.23
sudo systemctl stop k3s-agent
sudo systemctl disable k3s-agent

curl -sfL https://get.k3s.io | K3S_TOKEN="<token>" \
  sh -s - server \
  --server https://192.168.1.20:6443 \
  --disable traefik \
  --write-kubeconfig-mode 644 \
  --tls-san 192.168.1.23
exit

# Verify dual control plane
kubectl get nodes  # Should see 4 nodes, 2 control-planes

# Drain adama
kubectl cordon adama
kubectl drain adama --ignore-daemonsets --delete-emptydir-data --force
watch kubectl get pods -A -o wide  # Wait for all Running

# Delete node
kubectl delete node adama
kubectl get nodes  # Should see 3 nodes

# Update kubectl config
scp bsg@192.168.1.23:/etc/rancher/k3s/k3s.yaml ~/.kube/config
sed -i 's/127.0.0.1/192.168.1.23/g' ~/.kube/config
kubectl get nodes  # Test connection
```

---

## Phase 4: GitOps Sync (20 min)

```bash
cd /home/kin/Documents/glasgow-gitops

# NOW commit and push
git add .
git commit -m "Remove laptop node (adama), promote starbuck to control plane

- Remove msv2-inference (OpenL3 GPU service)
- Remove nvidia-device-plugin  
- Update all IPs: 192.168.1.20 → 192.168.1.23
- New control plane: starbuck (192.168.1.23)"

git push origin main

# Watch ArgoCD sync
watch kubectl get applications -n argocd

# Clean up removed apps if needed
kubectl delete application msv2-inference nvidia-device-plugin -n argocd --ignore-not-found
kubectl delete service.serving.knative.dev msv2-inference -n glasgow-prod --ignore-not-found
kubectl delete daemonset nvidia-device-plugin-daemonset -n kube-system --ignore-not-found

# Force sync root app
kubectl patch application root-app -n argocd --type merge \
  -p='{"operation":{"sync":{"revision":"HEAD"}}}'

# Or use UI
kubectl port-forward svc/argocd-server -n argocd 8080:443
# https://localhost:8080
```

---

## Phase 5: Cleanup Laptop (5 min)

```bash
# On laptop
ssh bsg@192.168.1.20
/usr/local/bin/k3s-uninstall.sh
sudo shutdown -h now
```

---

## Phase 6: Verify (15 min)

```bash
# Health check
python3 admin/quick_check.py

# Test services (with new IP .23)
curl http://msv2-api.192.168.1.23.nip.io/health
curl http://fastapi.192.168.1.23.nip.io/health

# Check storage
kubectl get pv
kubectl get pods -n longhorn-system

# Access UI
http://msv2-webapp.192.168.1.23.nip.io
http://longhorn.192.168.1.23.nip.io
```

---

## Rollback (if needed)

```bash
# Before node deletion:
kubectl uncordon adama

# After node deletion:
# Re-add laptop as server, revert Git changes
git revert HEAD
git push
```

---

## Expected Results

✅ 3 nodes (starbuck master, boomer + apollo workers)
✅ All services running (except OpenL3)
✅ All ArgoCD apps synced
✅ All storage healthy
✅ Power consumption reduced 50%

❌ OpenL3 inference unavailable (expected)


---

## GitOps Flow Summary

1. **Prepare Git** (source of truth) - don't push yet
2. **Migrate infrastructure** (add starbuck control plane, remove adama)
3. **Push Git changes** (trigger ArgoCD)
4. **ArgoCD reconciles** (syncs cluster to match Git)

**Repo remains source of truth throughout!**
