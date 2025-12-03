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

## 3. Installing WireGuard Client

### Linux (Ubuntu/Debian)
```bash
sudo apt update
sudo apt install wireguard
```

### macOS
Download from the [Mac App Store](https://apps.apple.com/us/app/wireguard/id1451685025) or use Homebrew:
```bash
brew install wireguard-tools
```

### Windows
Download the official installer from [wireguard.com/install](https://www.wireguard.com/install/)

### Mobile (iOS/Android)
- **iOS**: [WireGuard on App Store](https://apps.apple.com/us/app/wireguard/id1441195209)
- **Android**: [WireGuard on Google Play](https://play.google.com/store/apps/details?id=com.wireguard.android)

## 4. Connecting Your Laptop to the VPN

### Step 1: Create a Client Configuration
1.  Open the Web UI at **http://wireguard.192.168.1.20.nip.io**
2.  Login with your password
3.  Click **+ New Client**
4.  Give it a name (e.g., `My-Laptop`)
5.  Click **Create**

### Step 2: Download the Configuration File
- Click the **Download** button next to your newly created client
- Save the `.conf` file (e.g., `My-Laptop.conf`)

### Step 3: Import and Connect

#### On Linux:
```bash
# Copy the config file to WireGuard directory
sudo cp My-Laptop.conf /etc/wireguard/wg0.conf

# Start the VPN
sudo wg-quick up wg0

# To stop the VPN
sudo wg-quick down wg0

# To enable on boot
sudo systemctl enable wg-quick@wg0
```

#### On macOS/Windows (GUI):
1.  Open the WireGuard application
2.  Click **Import tunnel(s) from file**
3.  Select your downloaded `.conf` file
4.  Click **Activate** to connect

#### On Mobile:
1.  Open the WireGuard app
2.  Tap **+** (Add Tunnel)
3.  **Option A**: Scan the QR code from the Web UI
4.  **Option B**: Import from file (if you transferred the `.conf` file)
5.  Toggle the switch to connect

### Step 4: Verify Connection
Once connected, you should be able to access your home services:
- Try opening `http://minio.192.168.1.20.nip.io` in your browser
- If it loads, you're successfully connected!

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

## 6. Troubleshooting

### No Internet Access When Connected (Full Tunnel Setup)

**Problem**: When you activate the VPN, you can't browse the web or access any internet services.

**Cause**: The VPN is routing ALL traffic through the tunnel (which is what you want for privacy), but your K3s node isn't configured to forward that traffic to the internet yet.

**Solution - Configure K3s Node as Gateway**:

The VPN is configured for **full tunnel** mode, which means:
- ✅ All your internet traffic goes through your home connection (privacy + geo-location benefits)
- ✅ You can access your cluster services
- ✅ Your public IP appears as your home IP

To make this work, you need to configure your K3s node (192.168.1.20) to act as a gateway:

1.  **SSH into your K3s node**:
    ```bash
    ssh user@192.168.1.20
    ```

2.  **Run the gateway setup script**:
    ```bash
    # Copy the script from the repo
    cd /path/to/glasgow-gitops
    chmod +x setup-vpn-gateway.sh
    sudo ./setup-vpn-gateway.sh
    ```

    This script will:
    - Enable IP forwarding
    - Configure NAT/masquerading with iptables
    - Make the changes permanent (survive reboots)

3.  **Reconnect your VPN**:
    ```bash
    sudo wg-quick down wg0
    sudo wg-quick up wg0
    ```

4.  **Test**:
    - Browse to `https://whatismyip.com` - you should see your home IP
    - Access `http://minio.192.168.1.20.nip.io` - should work
    - Regular internet browsing should work

**Alternative - Split Tunnel** (if you only want cluster access):
If you don't need the privacy/geo-location benefits and only want to access your cluster:

1.  Change `WG_ALLOWED_IPS` in `deployment.yaml` to `"192.168.1.0/24"`
2.  Redeploy and recreate your client config

### FAQ: Is it safe to expose WireGuard?
**Yes.** WireGuard is designed to be exposed to the internet.
*   **UDP 51820**: This port is "stealthy". It does not respond to pings or scans unless the sender has a valid private key. It is extremely secure.
*   **TCP 51821 (Web UI)**: This is the management interface. You should generally **NOT** expose this to the public internet. Access it only when you are home, or *through* the VPN itself.
