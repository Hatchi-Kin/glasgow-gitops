# Get the initial admin password
kubectl -n argocd get secret argocd-initial-admin-secret -o jsonpath="{.data.password}" | base64 -d
aY2jT3EvltIww-rJ

# Glasgow GitOps

This repository contains a simplified GitOps structure for managing a K3s Kubernetes cluster. The goal is to provide a learning environment that mimics a production-like setup while remaining manageable for individual use.

## Project Structure

```
glasgow-gitops/
├── argocd/
│   ├── apps/                # Contains ArgoCD application definitions for each service
│   │   ├── minio.yaml       # ArgoCD application for MinIO
│   │   ├── postgres.yaml     # ArgoCD application for PostgreSQL
│   │   ├── fastapi.yaml      # ArgoCD application for FastAPI
│   │   └── ingress.yaml      # ArgoCD application for managing ingress resources
│   └── root-app.yaml        # Root ArgoCD application pointing to the apps directory
├── components/              # Contains Kubernetes manifests for each application
│   ├── minio/               # MinIO application resources
│   │   ├── base/            # Base configuration for MinIO
│   │   └── overlays/        # Environment-specific overlays for MinIO
│   ├── postgres/            # PostgreSQL application resources
│   │   ├── base/            # Base configuration for PostgreSQL
│   │   └── overlays/        # Environment-specific overlays for PostgreSQL
│   ├── fastapi/             # FastAPI application resources
│   │   ├── base/            # Base configuration for FastAPI
│   │   └── overlays/        # Environment-specific overlays for FastAPI
│   └── ingress/             # Ingress resources
│       ├── base/            # Base configuration for ingress
│       └── overlays/        # Environment-specific overlays for ingress
├── secrets/                 # Contains secrets for the applications
│   └── dev/                 # Development environment secrets
│       └── sops-encoded-secrets.yaml # SOPS-encoded secrets
└── README.md                # Documentation for the project
```

## Getting Started

1. **Clone the Repository**: 
   ```
   git clone <repository-url>
   cd glasgow-gitops
   ```

2. **Install Dependencies**: Ensure you have ArgoCD, Kustomize, and SOPS installed.

3. **Deploy Applications**: Use ArgoCD to deploy the applications defined in the `argocd/apps` directory.

4. **Manage Secrets**: Use SOPS to manage sensitive information in the `secrets/dev/sops-encoded-secrets.yaml` file.

## Learning Objectives

- Understand the basics of GitOps and how to manage Kubernetes resources using ArgoCD.
- Learn how to structure a GitOps repository for clarity and maintainability.
- Gain hands-on experience with Kustomize for managing Kubernetes configurations.
- Explore best practices for managing secrets in a Kubernetes environment.

Feel free to modify and extend this repository as you learn more about Kubernetes and GitOps!