# WireGuard VPN (wg-easy)

This guide explains how to use the self-hosted WireGuard VPN installed in the cluster.

## 1. Setup & Configuration

### Setting the Password (SealedSecret)
Before the VPN will work, you must set a password using SealedSecrets.

1.  **Generate the Secret**:
    Run this command in your terminal (replace `YOUR_PASSWORD` with your desired password):
    ```bash
    echo -n "YOUR_PASSWORD" | kubectl create secret generic wireguard-secret --dry-run=client --from-file=PASSWORD=/dev/stdin -o json -n glasgow-prod | kubeseal --controller-name=sealed-secrets --controller-namespace=kube-system --format yaml
    ```
    *Note: Ensure you have `kubeseal` installed and context set to your cluster.*

2.  **Update File**:
    Copy the `encryptedData` block from the output and paste it into `components/wireguard/sealed-secret.yaml`.

3.  **Push**: Commit and push the changes. ArgoCD will sync the secret.

## 2. Accessing the UI

The Web UI is available at:
**http://wireguard.192.168.1.20.nip.io**

**Login**: Use the password you sealed in step 1.

*Note: This UI is for managing clients. It is accessible from your local network. It is generally NOT recommended to expose this UI to the public internet unless you have strict security measures (e.g., strong password, rate limiting, etc.).*

## 3. Connecting Devices

1.  **Login** to the Web UI.
2.  Click **+ New Client**.
3.  Name it (e.g., `Laptop`, `Phone`).
4.  **Mobile**: Scan the QR code.
5.  **Desktop**: Download the `.conf` file and import it into the WireGuard app.

## 4. Workflows: How to use it?

### Scenario A: At Home (Local Network)
*   **Without VPN**: You access your apps normally (e.g., `http://minio.192.168.1.20.nip.io`). Your traffic goes directly from your device to the server.
*   **With VPN**: You *can* leave the VPN on. Your traffic will go to the WireGuard pod first, then to the app. It works fine but is slightly slower due to encryption.

### Scenario B: Away from Home (Coffee Shop / Travel)
*   **Without VPN**: You cannot access your home apps (unless you exposed them all to the public internet, which is risky).
*   **With VPN**:
    1.  Open WireGuard app on your laptop/phone.
    2.  Click **Activate**.
    3.  You are now "virtually" at home.
    4.  Open your browser and go to `http://minio.192.168.1.20.nip.io`. It works exactly as if you were sitting on your couch.

### Impact on Cluster
*   **Zero Impact**: Deploying WireGuard does not change how your existing apps (Minio, etc.) work. They are unaware of the VPN.
*   **Security**: It allows you to keep your other apps *private* (not exposed to the internet) while still accessing them remotely via the secure VPN tunnel.

## 5. External Access Setup (Critical)

For "Scenario B" to work, you must configure your home router and deployment:

### A. Port Forwarding (Router)
You **must** log in to your home router (Livebox) and forward **UDP Port 51820** to `192.168.1.20` (Your K3s Node).
*   **Protocol**: UDP
*   **Internal Port**: 51820
*   **External Port**: 51820
*   **Device/IP**: 192.168.1.20

### B. Domain Name / Public IP (Deployment)
You need to tell WireGuard what your "Public Address" is so clients know where to connect.

1.  **Edit `components/wireguard/deployment.yaml`**:
    *   Find the `WG_HOST` environment variable.
    *   Change it to your **Public IP** OR your **Domain Name** (e.g., `vpn.yourdomain.com`).
2.  **DNS**:
    *   If using a domain (e.g., `vpn.yourdomain.com`), ensure you have an **A Record** in your DNS settings pointing `vpn` to your **Home Public IP**.
    *   *Tip: If your home IP changes (Dynamic IP), use a DDNS service to keep the domain updated.*

### FAQ: Is it safe to expose WireGuard?
**Yes.** WireGuard is designed to be exposed to the internet.
*   **UDP 51820**: This port is "stealthy". It does not respond to pings or scans unless the sender has a valid private key. It is extremely secure.
*   **TCP 51821 (Web UI)**: This is the management interface. You should generally **NOT** expose this to the public internet. Access it only when you are home, or *through* the VPN itself.
