# 🔄 Glasgow GitOps - Cluster Restart Guide

## Quick Commands

```bash
# Shutdown cluster
python3 galactica_on_and_off.py off -f

# Startup cluster  
python3 galactica_on_and_off.py on

# Check status
python3 galactica_on_and_off.py status
```

## Manual Process (if needed)

### Shutdown
```bash
# 1. Drain workers
kubectl drain boomer apollo starbuck --ignore-daemonsets --delete-emptydir-data

# 2. Shutdown (workers first, then master)
ssh boomer "sudo shutdown -h now"
ssh apollo "sudo shutdown -h now" 
ssh starbuck "sudo shutdown -h now"
sleep 30
sudo shutdown -h now
```

### Startup
```bash
# 1. Power on: adama first, then workers
# 2. Uncordon workers
kubectl uncordon boomer apollo starbuck

# 3. Verify
./verify-cluster.sh
```

## Recovery Time: ~10 minutes

**Critical:** Always uncordon worker nodes after restart!

## Troubleshooting

| Problem | Solution |
|---------|----------|
| Pods stuck `Pending` | `kubectl uncordon boomer apollo starbuck` |
| ArgoCD `OutOfSync` | `argocd app sync --all` |
| Port forward fails | `pkill -f "kubectl port-forward"` |

## Success Criteria
- ✅ All nodes `Ready` (not `SchedulingDisabled`)
- ✅ All pods `Running`
- ✅ PVCs remain `Bound`
- ✅ Data persists