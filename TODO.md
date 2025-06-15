## 🎯 Glasgow GitOps - Next Session Context

### ✅ What We Have (Current State)
- **Complete GitOps stack**: PostgreSQL, MinIO, FastAPI, Traefik ingress
- **Automated CI/CD**: GitHub Actions → Docker Hub → ArgoCD deployment
- **Working locally**: FastAPI accessible via `api.glasgow.local` (port-forward)
- **ArgoCD managing**: All applications with app-of-apps pattern
- **Kustomize overlays**: Base + production configurations

### 🎯 What We Want (Next Phase)

#### 1. **SOPS (Secrets Management)** 🔐
- Encrypt database passwords and MinIO credentials
- Replace ConfigMaps with proper Kubernetes Secrets
- Secure secrets in Git repository

#### 2. **Real Internet Access** 🌐
- Get actual domain name 
- Configure DNS to point to cluster
- Add SSL/TLS certificates
- Expose **only FastAPI** to internet (keep DB/MinIO internal)

#### 3. **Enhanced FastAPI Functionality** 🛠️
- Database operations: Create tables, users, CRUD
- MinIO operations: Create buckets, upload/download files
- Connect database metadata with MinIO file storage

### 🚀 Starting Point
- Repository: glasgow-gitops
- FastAPI repo: glasgow-api  
- Current access: Port-forward to test services
- All applications: Healthy and synced in ArgoCD

**Priority: Start with SOPS to secure credentials before exposing to internet.**


## more precise

### 1. Security & Secrets Management (High Priority)

Currently, your `secrets/dev/sops-encoded-secrets.yaml` is intentionally blank, and you have `MINIO_ACCESS_KEY` and `MINIO_SECRET_KEY` directly in your `Dockerfile` and `DATABASE_URL` as an environment variable in your `deployment.yaml`. This is a significant security risk for a production-like environment.

* **Implement SOPS (Mozilla SOPS):** You've correctly identified this in your `TODO.md`, and it's the most critical next step.
    * **Action:** Fully integrate SOPS for encrypting all sensitive data (database credentials, MinIO keys, API keys, etc.) that will be committed to Git.
    * **Why:** Prevents sensitive data from being exposed in your repository, even if it's private.
    * **How:**
        1.  Install SOPS.
        2.  Configure a GPG key or KMS (like AWS KMS, GCP KMS, Azure Key Vault) for encryption/decryption. For a homelab, GPG is usually sufficient.
        3.  Encrypt your `secrets.yaml` files.
        4.  Integrate SOPS decryption into your ArgoCD deployment (ArgoCD natively supports SOPS).
* **Remove Hardcoded Secrets:** Once SOPS is in place, remove any hardcoded secrets from Dockerfiles, Kubernetes manifests, and environment variables if they are sensitive.

### 2. CI/CD Pipeline (FastAPI Repo)

Your `build-and-deploy-to-docker-hub.yaml` GitHub Actions workflow is a good start, but consider these enhancements:

* **Automated Testing:** Before building and pushing to Docker Hub, include steps to run your FastAPI application's unit and integration tests.
    * **Action:** Add a `test` job or a `test` step within your `build-and-push` job.
    * **Why:** Ensures that only working code gets built into an image and pushed. Catches bugs early.
    * **Example (in your `build-and-deploy-to-docker-hub.yaml`):**
        ```yaml
        jobs:
          build-and-push:
            runs-on: ubuntu-latest
            steps:
              - name: Checkout code
                uses: actions/checkout@v4
              - name: Set up Python
                uses: actions/setup-python@v5
                with:
                  python-version: '3.10' # Or your specific Python version
              - name: Install dependencies
                run: pip install -r requirements.txt
              - name: Run tests
                run: pytest # Assuming you use pytest for testing
        ```
* **Vulnerability Scanning (Optional but Recommended):** Integrate a tool like Trivy or Clair to scan your Docker image for known vulnerabilities before pushing.
    * **Action:** Add a step for image scanning.
    * **Why:** Proactive security measure to identify and address vulnerabilities in your application dependencies or base image.

### 3. Kubernetes Manifests & Configuration

You have a solid Kustomize setup, but a few areas can be refined:

* **Health Checks (Liveness/Readiness Probes):** Your `deployment.yaml` for FastAPI doesn't explicitly show `livenessProbe` and `readinessProbe`. These are crucial for Kubernetes to manage your application's lifecycle effectively.
    * **Action:** Add `livenessProbe` and `readinessProbe` to your FastAPI deployment.
    * **Why:**
        * `livenessProbe`: Tells Kubernetes when your application is unhealthy and needs to be restarted.
        * `readinessProbe`: Tells Kubernetes when your application is ready to accept traffic. Essential for zero-downtime deployments.
    * **Example (in `components/fastapi/base/deployment.yaml`):**
        ```yaml
        spec:
          template:
            spec:
              containers:
              - name: fastapi
                # ... existing config ...
                ports:
                - containerPort: 8000
                livenessProbe:
                  httpGet:
                    path: /health # Or another health endpoint you define
                    port: 8000
                  initialDelaySeconds: 10
                  periodSeconds: 5
                readinessProbe:
                  httpGet:
                    path: /health
                    port: 8000
                  initialDelaySeconds: 5
                  periodSeconds: 3
        ```
* **Resource Requests and Limits:** You have these defined for PostgreSQL and MinIO overlays. Ensure they are also set for your FastAPI application.
    * **Action:** Add `resources` to your FastAPI deployment's container spec.
    * **Why:** Prevents your application from consuming excessive resources and helps Kubernetes schedule pods efficiently.
* **Pod Disruption Budgets (PDBs):** For multi-replica deployments (like your 2-replica FastAPI in production), PDBs ensure that a minimum number of pods are available during voluntary disruptions (e.g., node upgrades).
    * **Action:** Consider adding PDBs for your deployments.
    * **Why:** Enhances the availability of your services.
* **Persistent Storage for MinIO:** Your MinIO deployment uses an `emptyDir` for storage. This means data will be lost if the pod restarts or moves to another node.
    * **Action:** Implement a `PersistentVolumeClaim` (PVC) and `PersistentVolume` (PV) for MinIO, similar to what you've done for PostgreSQL, using `local-path` provisioner.
    * **Why:** Ensures data persistence for MinIO.

### 4. GitOps Workflow Enhancements

* **Pre-Sync & Post-Sync Hooks in ArgoCD:** For more complex deployments or dependencies, you can use ArgoCD hooks to run tasks before or after the main sync (e.g., database migrations).
    * **Action:** Research and consider using ArgoCD Sync Waves and Hooks.
    * **Why:** Provides fine-grained control over the deployment order and execution of one-off tasks.
* **Automated Image Updates (Optional, Advanced):** You manually update the image version in `deployment.yaml`. Tools like ArgoCD Image Updater or Renovate can automate this process.
    * **Action:** Explore image update automation.
    * **Why:** Reduces manual toil and ensures your deployments are always using the latest approved image. This would be a significant step in full GitOps automation.

### 5. Monitoring & Logging (Next Steps for Observability)

While not strictly a "beginning of project" improvement for the *code*, planning for observability from the start is a good practice.

* **Structured Logging:** Ensure your FastAPI application logs in a structured format (e.g., JSON).
    * **Action:** Use a logging library like `structlog` or configure Python's `logging` module to output JSON.
    * **Why:** Easier to parse and analyze logs in a log management system (ELK stack, Loki, Grafana, etc.).
* **Prometheus Exporter (for FastAPI metrics):** Expose application metrics that Prometheus can scrape.
    * **Action:** Integrate a library like `fastapi-metrics` or `prometheus-client` into your FastAPI app.
    * **Why:** Provides valuable insights into your application's performance and health.

### Summary of Priority Improvements:

1.  **Implement SOPS for secrets management.** (Critical)
2.  **Add liveness and readiness probes to FastAPI.** (High)
3.  **Ensure persistent storage for MinIO.** (High, if data persistence is required)
4.  **Add automated testing to your CI pipeline.** (High)
5.  **Define resource requests/limits for FastAPI.** (Medium)

You've built a very solid foundation. Addressing these points will significantly improve the robustness, security, and maintainability of your learning project. Keep learning and iterating!
