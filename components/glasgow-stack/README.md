# Kustomize Cheat Sheet

This directory contains all the Kubernetes resources for the `glasgow-stack`, managed by Kustomize.

## 🧠 Core Kustomize Concepts

- **What is a `base`?**
  - The `base/` directory contains the core, environment-agnostic YAML definitions for each application (Deployment, Service, etc.). These are the templates.
  - The `base/kustomization.yaml` lists all the components that are part of the stack.

- **What is an `overlay`?**
  - The `overlays/` directory contains environment-specific *patches*. For example, `overlays/prod/` contains patches for the production environment.
  - These patches can change things like replica counts, add Ingresses, or point to different secrets.

- **How do I add a new application?**
  1.  Create a new directory under `base/` (e.g., `base/new-app`).
  2.  Add the core YAML files (Deployment, Service) to `base/new-app`.
  3.  Add a `kustomization.yaml` to `base/new-app`.
  4.  Add the new application to the `resources` list in `base/kustomization.yaml`.

## 📦 Common Kustomize Commands

While ArgoCD runs Kustomize for you, you can preview the final YAML that will be generated.

```sh
# See the final YAML for the production environment
kubectl kustomize components/glasgow-stack/overlays/prod

# See the final YAML for the base configuration
kubectl kustomize components/glasgow-stack/base
```

---
