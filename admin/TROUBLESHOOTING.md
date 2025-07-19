# Cluster Troubleshooting Guide

## 🔧 Common Issues and Solutions

### Pod Not Starting

**Check pod status:**
```bash
kubectl get pods -n glasgow-prod
kubectl describe pod <pod-name> -n glasgow-prod
kubectl logs <pod-name> -n glasgow-prod
```

**Common causes:**
- Image pull issues
- Secret/ConfigMap missing
- Resource constraints
- PVC not bound

### Storage Issues

**Check PVC status:**
```bash
kubectl get pvc -n glasgow-prod
kubectl describe pvc <pvc-name> -n glasgow-prod
```

**Longhorn issues:**
```bash
# Check Longhorn system pods
kubectl get pods -n longhorn-system

# Access Longhorn UI
kubectl port-forward svc/longhorn-frontend -n longhorn-system 8080:80
# Then visit: http://localhost:8080
```

### ArgoCD Sync Issues

**Check application status:**
```bash
kubectl get applications -n argocd
kubectl describe application <app-name> -n argocd
```

**Force sync:**
```bash
kubectl patch application <app-name> -n argocd --type merge -p='{"operation":{"initiatedBy":{"username":"admin"},"sync":{"revision":"HEAD"}}}'
```

**Common sync issues:**
- Git repository changes not detected
- Resource conflicts
- Validation errors
- Permission issues

### Secret Issues

**Check sealed secrets:**
```bash
kubectl get sealedsecrets -n glasgow-prod
kubectl describe sealedsecret <secret-name> -n glasgow-prod
```

**Check if regular secrets are created:**
```bash
kubectl get secrets -n glasgow-prod
```

**If sealed secret not creating regular secret:**
```bash
# Check sealed-secrets controller
kubectl logs -n kube-system -l name=sealed-secrets-controller

# Restart controller if needed
kubectl rollout restart deployment sealed-secrets-controller -n kube-system
```

### Network/Ingress Issues

**Check ingress status:**
```bash
kubectl get ingress -n glasgow-prod
kubectl describe ingress <ingress-name> -n glasgow-prod
```

**Check Traefik (built into K3s):**
```bash
kubectl get pods -n kube-system | grep traefik
kubectl logs -n kube-system <traefik-pod>
```

### Database Connection Issues

**Check if database is running:**
```bash
kubectl get pods -n glasgow-prod -l app=postgres
kubectl logs -n glasgow-prod <postgres-pod>
```

**Test connection from another pod:**
```bash
kubectl run test-pod --rm -it --image=postgres:15 -n glasgow-prod -- psql -h postgres-service -U adama -d postgres
```

## 🚨 Emergency Procedures

### Complete Cluster Reset
```bash
# WARNING: This deletes all data!
python3 admin/cluster_manager.py reset
```

### Individual App Reset
```bash
# Delete app and let ArgoCD recreate
kubectl delete deployment <app-name> -n glasgow-prod
kubectl delete pvc <app-name>-pvc -n glasgow-prod  # If you want fresh data
```

### ArgoCD Reset
```bash
# Delete and recreate ArgoCD namespace
kubectl delete namespace argocd
kubectl apply -n argocd -f https://raw.githubusercontent.com/argoproj/argo-cd/stable/manifests/install.yaml
kubectl apply -f argocd/root-app.yaml
```

## 📊 Monitoring Commands

**Quick health check:**
```bash
python3 admin/quick_check.py
```

**Watch pod status:**
```bash
watch kubectl get pods -n glasgow-prod
```

**Check resource usage:**
```bash
kubectl top nodes
kubectl top pods -n glasgow-prod
```

**Check events:**
```bash
kubectl get events -n glasgow-prod --sort-by='.lastTimestamp'
```

## 🔄 Maintenance Tasks

### Regular Maintenance
```bash
# Weekly: Check cluster health
python3 admin/quick_check.py

# Monthly: Update images (if using latest tags)
python3 admin/cluster_manager.py restart

# As needed: Force sync all apps
python3 admin/cluster_manager.py sync
```

### Backup Considerations
- Longhorn handles volume snapshots automatically
- Git repository contains all configuration (GitOps benefit)
- Export important data periodically:
  ```bash
  kubectl exec <postgres-pod> -n glasgow-prod -- pg_dump -U adama postgres > backup.sql
  ```

## 📞 Getting Help

1. **Check the logs first**: Most issues show up in pod logs
2. **Use describe**: `kubectl describe` gives detailed status info
3. **Check ArgoCD UI**: Visual representation of sync status
4. **Verify Git**: Ensure your changes are committed and pushed
5. **Test manually**: Use `kubectl apply` to test changes before committing
