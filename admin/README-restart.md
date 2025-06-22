<!-- 
name: postgres-secret
data:
  POSTGRES_DB: "GalacticaDBHjki58e"
  POSTGRES_USER: "AdamaUserHjki58e"
  POSTGRES_PASSWORD: "AdamaPssWHjki58e"
  
name: minio-secret
stringData:
  root-user: GalacticaMiniOHjki58e
  root-password: AdamaUserMinioHjki58e 
-->


# 🔄 Cluster Restart Guide

Quick commands to shutdown, start, and check the cluster.

## Quick Commands

```sh
python3 galactica_on_and_off.py off -f
python3 galactica_on_and_off.py on
python3 galactica_on_and_off.py status
```

## Manual Process

### Shutdown
```sh
kubectl drain boomer apollo starbuck --ignore-daemonsets --delete-emptydir-data
ssh boomer "sudo shutdown -h now"
ssh apollo "sudo shutdown -h now"
ssh starbuck "sudo shutdown -h now"
sleep 30
sudo shutdown -h now
```

### Startup
```sh
# Power on adama first, then workers
kubectl uncordon boomer apollo starbuck
./verify-cluster.sh
```

## Troubleshooting

| Problem | Solution |
|---------|----------|
| Pods Pending | `kubectl uncordon boomer apollo starbuck` |
| ArgoCD OutOfSync | `argocd app sync --all` |
| Port forward fails | `pkill -f "kubectl port-forward"` |

## Success Criteria
- All nodes `Ready`
- All pods `Running`
- PVCs remain `Bound`
- Data persists

---