# Updating Your K3s Homelab to a Real Domain Name and External Access

This guide outlines the steps to transition your K3s homelab cluster from using `nip.io` for local access to a real domain name, making your services accessible from the outside internet.

## Prerequisites

*   A registered domain name (e.g., `yourdomain.com`).
*   Access to your domain registrar's DNS settings to configure A/AAAA records.
*   A public IP address for your K3s cluster (or the router/firewall forwarding to it).
*   Understanding of port forwarding on your router/firewall.
*   Basic knowledge of GitOps with ArgoCD and Kubernetes ingress.

## Overview of Changes

The primary changes will involve:

1.  **DNS Configuration:** Updating your domain's DNS records to point to your public IP address.
2.  **Ingress Hostnames:** Modifying Kubernetes Ingress resources to use your new domain.
3.  **TLS/SSL:** Setting up TLS certificates for HTTPS access (e.g., using Cert-Manager and Let's Encrypt).
4.  **CORS Configuration:** Updating any Cross-Origin Resource Sharing (CORS) policies that reference `nip.io`.
5.  **Router/Firewall Port Forwarding:** Ensuring external traffic on ports 80 and 443 is forwarded to your K3s cluster's ingress controller.

## Step-by-Step Guide

### Step 1: Configure DNS Records

At your domain registrar (e.g., Cloudflare, Namecheap, GoDaddy), create the necessary DNS records:

1.  **Wildcard A Record (Recommended):** This allows you to easily create subdomains without individual DNS entries.
    *   **Type:** `A`
    *   **Name:** `*` (or `@` for the root domain)
    *   **Value:** Your public IP address
    *   **TTL:** Automatic or a low value (e.g., 5 minutes)

    Example:
    ```
    *.yourdomain.com  A  YOUR_PUBLIC_IP_ADDRESS
    ```

2.  **Specific A Records (Alternative/Supplement):** If you prefer not to use a wildcard or need specific entries.
    *   **Type:** `A`
    *   **Name:** `argocd`
    *   **Value:** Your public IP address
    *   **TTL:** Automatic

    Example:
    ```
    argocd.yourdomain.com  A  YOUR_PUBLIC_IP_ADDRESS
    longhorn.yourdomain.com  A  YOUR_PUBLIC_IP_ADDRESS
    msv2-webapp.yourdomain.com A YOUR_PUBLIC_IP_ADDRESS
    ```

**Wait for DNS Propagation:** It can take some time (minutes to hours) for DNS changes to propagate across the internet. You can use tools like `dig` or online DNS checkers to verify.

### Step 2: Update Ingress Resources

You will need to update the `host` entries in your Ingress YAML files.

**Identify Files to Change:**

*   `components/ingress/argocd-ingress.yaml`
*   `components/ingress/longhorn-ingress.yaml`
*   `components/fastapi/ingress.yaml` (if it exists and uses `nip.io`)
*   `components/fastapi-msv2-api/ingress.yaml` (if it exists and uses `nip.io`)
*   `components/msv2-webapp/ingress.yaml` (if it exists and uses `nip.io`)
*   `components/n8n/ingress.yaml` (if it exists and uses `nip.io`)
*   `components/navidrome/ingress.yaml` (if it exists and uses `nip.io`)
*   `components/minio/ingress.yaml` (if it exists and uses `nip.io`)

**Example Modification (for `argocd-ingress.yaml`):**

**Before:**
```yaml
apiVersion: networking.k8s.io/v1
kind: Ingress
metadata:
  name: argocd-server-ingress
  namespace: argocd
  annotations:
    kubernetes.io/ingress.class: "traefik"
    traefik.ingress.kubernetes.io/router.tls: "false"
    traefik.ingress.kubernetes.io/backend-protocol: "HTTP"
    nginx.ingress.kubernetes.io/force-ssl-redirect: "false"
    nginx.ingress.kubernetes.io/ssl-redirect: "false"
spec:
  rules:
    - host: argocd.192.168.1.20.nip.io
      http:
        paths:
          - path: /
            pathType: Prefix
            backend:
              service:
                name: argocd-server
                port:
                  number: 80
```

**After:**
```yaml
apiVersion: networking.k8s.io/v1
kind: Ingress
metadata:
  name: argocd-server-ingress
  namespace: argocd
  annotations:
    kubernetes.io/ingress.class: "traefik"
    traefik.ingress.kubernetes.io/router.tls: "true" # Enable TLS
    traefik.ingress.kubernetes.io/backend-protocol: "HTTPS" # Use HTTPS for backend if your service supports it
    # Remove nginx annotations if not using Nginx Ingress Controller
    # nginx.ingress.kubernetes.io/force-ssl-redirect: "false"
    # nginx.ingress.kubernetes.io/ssl-redirect: "false"
spec:
  rules:
    - host: argocd.yourdomain.com # <--- Update this line
      http:
        paths:
          - path: /
            pathType: Prefix
            backend:
              service:
                name: argocd-server
                port:
                  number: 80 # Or 443 if backend service is HTTPS
  tls: # <--- Add this section for TLS
    - hosts:
        - argocd.yourdomain.com
      secretName: argocd-tls-secret # This secret will be created by Cert-Manager
```

**Important Considerations for Ingress:**

*   **`traefik.ingress.kubernetes.io/router.tls: "true"`:** Change this annotation to `true` to enable TLS for Traefik.
*   **`traefik.ingress.kubernetes.io/backend-protocol: "HTTPS"`:** If your backend services (e.g., ArgoCD server) are configured to serve HTTPS internally, change this to `HTTPS`. Otherwise, keep it as `HTTP` and let Traefik handle the SSL termination.
*   **`tls` section:** Add a `tls` section to each Ingress resource, specifying the `hosts` and a `secretName`. This `secretName` will be used by Cert-Manager to store the generated TLS certificate.

### Step 3: Set up Cert-Manager for Automatic TLS (Recommended)

Cert-Manager automates the issuance and renewal of TLS certificates from Let's Encrypt.

1.  **Install Cert-Manager:** Follow the official Cert-Manager documentation for installation on K3s. Typically, this involves applying a few YAML files.

    ```bash
    # Example installation (refer to official docs for the latest version)
    kubectl apply -f https://github.com/cert-manager/cert-manager/releases/download/v1.13.0/cert-manager.yaml
    ```

2.  **Create a ClusterIssuer or Issuer:** This tells Cert-Manager how to obtain certificates. For Let's Encrypt, you'll typically use an `ACME` issuer.

    Create a file named `letsencrypt-clusterissuer.yaml`:

    ```yaml
    apiVersion: cert-manager.io/v1
    kind: ClusterIssuer
    metadata:
      name: letsencrypt-prod
    spec:
      acme:
        email: your-email@example.com # <--- IMPORTANT: Replace with your email
        server: https://acme-v02.api.letsencrypt.org/directory
        privateKeySecretRef:
          name: letsencrypt-prod-private-key
        solvers:
          - http01:
              ingress:
                class: traefik # <--- Ensure this matches your ingress class
    ```

    Apply it:
    ```bash
    kubectl apply -f letsencrypt-clusterissuer.yaml
    ```

3.  **Update Ingress Annotations:** In your Ingress resources (from Step 2), add the following annotation to tell Cert-Manager to issue a certificate:

    ```yaml
    metadata:
      annotations:
        # ... existing annotations ...
        cert-manager.io/cluster-issuer: "letsencrypt-prod" # <--- Add this annotation
    ```

    After applying these changes, Cert-Manager will automatically create `Certificate` resources and then `Secret` resources (e.g., `argocd-tls-secret`) containing your TLS certificates.

### Step 4: Update CORS Configuration

If you have CORS policies that explicitly reference `nip.io` domains, you'll need to update them.

**File to Change:**

*   `components/ingress/traefik-cors-middleware.yaml`

**Example Modification:**

**Before:**
```yaml
apiVersion: traefik.io/v1alpha1
kind: Middleware
metadata:
  name: traefik-cors-headers
  namespace: glasgow-prod
spec:
  headers:
    customRequestHeaders:
      X-Forwarded-Proto: "https"
    customResponseHeaders:
      Access-Control-Allow-Origin: "http://msv2-webapp.192.168.1.20.nip.io" # <--- Update this line
      Access-Control-Allow-Credentials: "true"
      Access-Control-Allow-Methods: "GET, POST, PUT, DELETE, PATCH, OPTIONS"
      Access-Control-Allow-Headers: "Content-Type, Authorization, Accept, Origin, X-Requested-With"
      Access-Control-Max-Age: "100"
```

**After:**
```yaml
apiVersion: traefik.io/v1alpha1
kind: Middleware
metadata:
  name: traefik-cors-headers
  namespace: glasgow-prod
spec:
  headers:
    customRequestHeaders:
      X-Forwarded-Proto: "https"
    customResponseHeaders:
      Access-Control-Allow-Origin: "https://msv2-webapp.yourdomain.com" # <--- Update this line (use https)
      Access-Control-Allow-Credentials: "true"
      Access-Control-Allow-Methods: "GET, POST, PUT, DELETE, PATCH, OPTIONS"
      Access-Control-Allow-Headers: "Content-Type, Authorization, Accept, Origin, X-Requested-With"
      Access-Control-Max-Age: "100"
```

**Note:** Remember to change `http` to `https` in the `Access-Control-Allow-Origin` if you are enabling TLS.

### Step 5: Router/Firewall Port Forwarding

You need to configure your home router or firewall to forward incoming traffic on ports 80 (HTTP) and 443 (HTTPS) to the internal IP address of your K3s node where Traefik (your ingress controller) is running.

*   **External Port 80 (HTTP) -> Internal Port 80 (K3s Node IP)**
*   **External Port 443 (HTTPS) -> Internal Port 443 (K3s Node IP)**

Consult your router's documentation for specific instructions on how to set up port forwarding.

### Step 6: Review and Apply Changes with ArgoCD

1.  **Commit Changes:** After making all the necessary modifications to your YAML files, commit them to your Git repository.

    ```bash
    git add .
    git commit -m "Update ingress and CORS for new domain yourdomain.com"
    git push origin main
    ```

2.  **ArgoCD Sync:** ArgoCD will detect the changes in your Git repository and automatically apply them to your K3s cluster. Monitor the ArgoCD UI to ensure all applications sync successfully and the Ingress resources are updated.

3.  **Verify:**
    *   Check the status of your Ingress resources: `kubectl get ingress -A`
    *   Check the status of your Certificates (if using Cert-Manager): `kubectl get certificate -A`
    *   Access your services using your new domain name (e.g., `https://argocd.yourdomain.com`).

## Potential Additional Changes (Advanced)

*   **Sealed Secrets:** If any of your `SealedSecret` resources contain `nip.io` references (e.g., for OAuth redirect URIs, API endpoints, or environment variables within application configurations), you will need to:
    1.  Unseal the secret.
    2.  Update the `nip.io` references to your new domain.
    3.  Re-seal the secret with the updated values.
*   **Application Configuration:** Some applications might have their own configuration files (e.g., ConfigMaps) that contain hardcoded URLs. Review your application-specific `ConfigMap` or `Deployment` resources for any `nip.io` references.
*   **External DNS:** For more advanced setups, consider using an external-dns controller to automatically create DNS records based on your Ingress resources. This is particularly useful if your public IP address changes frequently.

By following these steps, you should be able to successfully transition your K3s homelab to use a real domain name and make your services accessible from the internet.
