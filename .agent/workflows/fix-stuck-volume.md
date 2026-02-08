---
description: Fix stuck Longhorn volumes after power failure or node crash
---

This workflow helps you recover from "FailedMount" or "Multi-Attach error" issues with Longhorn volumes, typically occurring after a power cut or ungraceful node shutdown.

1. **Identify the stuck deployment**
   Check which pod is stuck in `ContainerCreating` or has mount errors.
   ```bash
   kubectl get pods -n glasgow-prod
   kubectl describe pod <pod-name> -n glasgow-prod
   ```

2. **Run the fix script**
   Use the provided script to safely detach the volume and restart the deployment.
   Replace `<deployment-name>` with the name of your deployment (e.g., `wireguard`).
   
   ```bash
   ./fix-stuck-volume.sh <deployment-name> glasgow-prod
   ```
   
   // turbo
   ```bash
   ./fix-stuck-volume.sh wireguard glasgow-prod
   ```

3. **Verify the fix**
   Check if the pod is Running.
   ```bash
   kubectl get pods -n glasgow-prod | grep <deployment-name>
   ```
