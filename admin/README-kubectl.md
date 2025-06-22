# Kubectl Quick Reference

Essential `kubectl` commands for managing your K3s cluster.

## 🚦 Status

```sh
kubectl get nodes
kubectl get pods -A
kubectl get svc -n <namespace>
```

## 🔍 Inspect

```sh
kubectl describe pod <pod> -n <ns>
kubectl logs <pod> -n <ns>
kubectl logs -f <pod> -n <ns>
```

## 🚀 Deployments

```sh
kubectl rollout restart deployment/<name> -n <ns>
kubectl rollout status deployment/<name> -n <ns>
```

## 🔄 Port Forward

```sh
kubectl port-forward svc/<svc> -n <ns> <local>:<svc-port>
```

## 🔑 Secrets & ConfigMaps

```sh
kubectl get secrets -n <ns>
kubectl get secret <name> -n <ns> -o yaml
kubectl get secret <name> -n <ns> -o jsonpath="{.data.<key>}" | base64 -d
kubectl get configmap -n <ns>
```

## 🛠️ Troubleshooting

```sh
kubectl describe pod <pod> -n <ns>
kubectl get events -A --sort-by='.metadata.creationTimestamp'
```

## 🧹 Cleanup

```sh
kubectl delete pod <pod> -n <ns>
kubectl delete deployment <name> -n <ns>
```

---
- [kubectl Cheat Sheet](https://kubernetes.io/docs/reference/kubectl/cheatsheet/)
- [Kubernetes Docs](https://kubernetes.io/docs/)
