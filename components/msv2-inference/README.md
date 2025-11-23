# msv2-inference Service

## Overview
GPU-accelerated serverless inference service using Knative Serving. Automatically scales to zero after 1 hour of inactivity.

## Configuration
- **Image**: `hatchikin/msv2-inference-gpu:latest`
- **GPU**: 1x NVIDIA GPU (GTX 950M on `adama` node)
- **Scale-to-zero**: 3600s (1 hour) grace period
- **Min replicas**: 0 (scales to zero when idle)
- **Node**: Pinned to `adama` (GPU node)

## Calling from msv2-api

The service is accessible via Knative's internal DNS:

```python
import httpx

# Knative service URL (internal cluster DNS)
INFERENCE_URL = "http://msv2-inference.glasgow-prod.svc.cluster.local"

async def get_embedding(audio_file_path: str):
    """
    Call the inference service to get audio embeddings.
    
    Knative will automatically:
    1. Scale up from 0 if needed (takes ~30-60s for cold start)
    2. Keep the service warm while in use
    3. Scale to 0 after 1 hour of inactivity
    """
    async with httpx.AsyncClient(timeout=120.0) as client:  # Long timeout for cold starts
        response = await client.post(
            f"{INFERENCE_URL}/embed",
            json={"audio_path": audio_file_path}
        )
        response.raise_for_status()
        return response.json()

# Example usage
embedding = await get_embedding("megaset/audio/track123.mp3")
```

## Manual Scaling

### Scale to 1 (wake up the service)
```bash
# Trigger a request to wake it up
kubectl run -it --rm curl --image=curlimages/curl --restart=Never -- \
  curl -X POST http://msv2-inference.glasgow-prod.svc.cluster.local/health
```

### Check service status
```bash
# View Knative service
kubectl get ksvc msv2-inference -n glasgow-prod

# View pods
kubectl get pods -n glasgow-prod -l serving.knative.dev/service=msv2-inference

# View logs
kubectl logs -n glasgow-prod -l serving.knative.dev/service=msv2-inference -c user-container --tail=100
```

## Deployment

The service is managed by ArgoCD. Changes to `components/msv2-inference/service.yaml` will be automatically synced.

## Prerequisites (Node Setup)

The `adama` node requires:
1. **NVIDIA Drivers**: `nvidia-driver-535` (installed)
2. **NVIDIA Container Toolkit**: Configured for k3s containerd
3. **NVIDIA Device Plugin**: Deployed via ArgoCD (`nvidia-device-plugin` application)

### One-time setup commands (already done):
```bash
# On adama node:
sudo apt install -y nvidia-driver-535
sudo apt install -y nvidia-container-toolkit
sudo nvidia-ctk runtime configure --runtime=containerd \
  --config=/var/lib/rancher/k3s/agent/etc/containerd/config.toml.d/nvidia.toml
sudo systemctl restart k3s
```

## Troubleshooting

### Service won't start
```bash
# Check revision status
kubectl describe revision -n glasgow-prod | grep -A 10 "Conditions:"

# Check for GPU availability
kubectl describe node adama | grep nvidia.com/gpu
```

### DNS resolution issues
Ensure MinIO endpoint is set correctly:
```yaml
env:
  - name: MINIO_ENDPOINT
    value: "minio-service.glasgow-prod.svc.cluster.local:9000"
```

### Cold start timeout
First request after scale-to-zero takes 30-60 seconds:
- Model download from MinIO
- GPU initialization
- Container startup

Use a longer timeout (120s) in your HTTP client.
