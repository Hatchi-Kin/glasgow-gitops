# Pre-Flight Checklist - Remove Laptop Node

Complete these checks before starting the migration.

## ✅ Prerequisites

### 1. Cluster Health
```bash
# Run health check
python3 admin/quick_check.py
```

**Verify:**
- [ ] All 4 nodes are Ready
- [ ] All ArgoCD applications are Healthy
- [ ] All pods in glasgow-prod are Running
- [ ] All PVCs are Bound

### 2. Backup Created
```bash
# Sealed secrets key (CRITICAL - without this you can't decrypt secrets!)
kubectl get secret -n kube-system sealed-secrets-key -o yaml > /tmp/sealed-secrets-key-backup.yaml

# Postgres database (safety backup)
kubectl exec -n glasgow-prod deployment/postgres -- pg_dumpall -U postgres > /tmp/postgres_backup_$(date +%Y%m%d).sql
```

**Verify:**
- [ ] sealed-secrets-key-backup.yaml exists and is not empty
- [ ] postgres_backup.sql exists and is > 100MB

### 3. Tools Available
```bash
# Check required tools
which kubectl sshpass git python3 jq

# Check cluster access
kubectl get nodes
```

**Verify:**
- [ ] kubectl works
- [ ] Can SSH to all nodes
- [ ] Git is configured
- [ ] Python3 available

### 4. Current State Documented
```bash
# Save current state
kubectl get nodes -o wide > /tmp/nodes_before.txt
kubectl get pods -A -o wide > /tmp/pods_before.txt
kubectl get pvc -A > /tmp/pvcs_before.txt
kubectl get applications -n argocd > /tmp/apps_before.txt
```

**Verify:**
- [ ] Files saved with current cluster state

### 5. Network Access
```bash
# Verify you can reach all nodes
for ip in 192.168.1.20 192.168.1.21 192.168.1.22 192.168.1.23; do
  echo -n "$ip: "
  ping -c 1 -W 1 $ip > /dev/null && echo "OK" || echo "FAIL"
done
```

**Verify:**
- [ ] All nodes are reachable

---

## 📋 Configuration Changes Preview

### Files to Remove
```bash
# Check what will be removed
ls -la argocd/apps/msv2-inference.yaml
ls -la argocd/apps/nvidia-device-plugin.yaml
ls -la components/msv2-inference/
ls -la components/nvidia-device-plugin/
```

**Verify:**
- [ ] Files exist and can be deleted

### Files to Update
```bash
# Check files exist
ls -la admin/quick_check.py
ls -la admin/cleanup_longhorn.py
ls -la admin/shutdown_cluster.py
ls -la admin/fix_routes.sh
ls -la README.md
```

**Verify:**
- [ ] All admin scripts exist

### IP Update Scope
```bash
# See how many files will change
grep -r "192.168.1.20" components/ argocd/ | wc -l
```

**Verify:**
- [ ] ~15-25 files with IP references found

---

## 🎯 Migration Readiness

### Cluster Capacity Check
```bash
# Check if 3 nodes can handle current load
kubectl top nodes
```

**Current resources:**
- Total CPU needed: ~5 cores
- Total RAM needed: ~11GB
- 3x N100 nodes: 12 cores, 48GB RAM

**Verify:**
- [ ] 3 nodes have sufficient capacity (should be plenty)

### Storage Check
```bash
# Verify Longhorn replicas are on workers
for node in boomer apollo starbuck; do
  echo "=== $node ==="
  sshpass -p "mlop!" ssh -o StrictHostKeyChecking=no bsg@192.168.1.$([ "$node" = "boomer" ] && echo 21 || [ "$node" = "apollo" ] && echo 22 || echo 23) \
    "sudo du -sh /var/lib/longhorn/replicas 2>/dev/null"
done
```

**Verify:**
- [ ] boomer has significant storage (~226GB)
- [ ] apollo has some storage
- [ ] starbuck has minimal storage (<50GB)

### Service Dependencies
```bash
# Check what's running on adama
kubectl get pods -A -o wide | grep adama
```

**Expected:**
- MinIO pod likely on adama
- Some system pods
- These will move to other nodes during drain

**Verify:**
- [ ] Noted which pods are on adama

---

## ⏰ Time Planning

**Estimated Timeline:**
- Backups: 10 minutes
- Git changes: 20 minutes
- Control plane setup: 30 minutes
- Node drain: 15 minutes
- Verification: 20 minutes
- **Total: ~2 hours**

**Best time to execute:**
- [ ] During low-usage period
- [ ] When you have 2-3 hours uninterrupted
- [ ] When you can handle 5-10 min downtime

---

## 🚨 Safety Checks

### Before Starting
- [ ] Backups are complete and verified
- [ ] You have sealed-secrets key backup
- [ ] You understand the rollback process
- [ ] You have time to complete migration
- [ ] Cluster is healthy (all green in health check)

### Abort Conditions
**Stop migration if:**
- Sealed secrets backup fails
- Can't reach starbuck node
- Cluster health check shows issues
- ArgoCD has multiple out-of-sync apps
- You find critical workloads on adama you didn't know about

---

## 📞 Emergency Contacts

**If something goes wrong:**

1. **Don't panic** - Migration is reversible until node deletion
2. **Check rollback plan** in REMOVE_LAPTOP_NODE.md
3. **Uncordon adama** if you need to restore: `kubectl uncordon adama`

---

## ✅ Final Go/No-Go Decision

**I am ready to proceed because:**
- [ ] All prerequisite checks passed
- [ ] Backups are complete
- [ ] I have 2-3 hours available
- [ ] Cluster is healthy
- [ ] I understand the changes
- [ ] I have read the migration plan

**Date/Time:** _______________

**Proceed:** YES / NO

---

## 🚀 Next Step

If all checks pass:

```bash
# Start the migration
cd /home/kin/Documents/glasgow-gitops
cat docs/REMOVE_LAPTOP_NODE.md
```

Follow Phase 1 → Phase 2 → Phase 3 → Phase 4 → Phase 5 → Phase 6

Good luck! 🎯
