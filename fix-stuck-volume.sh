#!/bin/bash
# Usage: ./fix-stuck-volume.sh <deployment-name> [namespace]

DEPLOYMENT=$1
NAMESPACE=${2:-glasgow-prod}

if [ -z "$DEPLOYMENT" ]; then
    echo "Usage: $0 <deployment-name> [namespace]"
    exit 1
fi

echo "Scaling down deployment $DEPLOYMENT in namespace $NAMESPACE..."
kubectl scale deploy "$DEPLOYMENT" --replicas=0 -n "$NAMESPACE"

echo "Waiting for pods to terminate..."
# Wait for pods to disappear. If no pods exist, this might error or return immediately, so we ignore error.
kubectl wait --for=delete pod -l app="$DEPLOYMENT" -n "$NAMESPACE" --timeout=60s || true

# Find PVCs used by the deployment
# We get the claimName from the deployment spec
PVCS=$(kubectl get deploy "$DEPLOYMENT" -n "$NAMESPACE" -o jsonpath='{.spec.template.spec.volumes[*].persistentVolumeClaim.claimName}')

for PVC in $PVCS; do
    echo "Processing PVC: $PVC"
    # Get PV name (usually same as VolumeAttachment source)
    PV=$(kubectl get pvc "$PVC" -n "$NAMESPACE" -o jsonpath='{.spec.volumeName}')
    
    if [ -z "$PV" ]; then
        echo "Could not find PV for PVC $PVC"
        continue
    fi

    # Find VolumeAttachment pointing to this PV
    # We use jsonpath to filter items where spec.source.persistentVolumeName matches the PV name
    VA=$(kubectl get volumeattachment -o jsonpath="{.items[?(@.spec.source.persistentVolumeName==\"$PV\")].metadata.name}")
    
    if [ -n "$VA" ]; then
        echo "Deleting VolumeAttachment $VA..."
        kubectl delete volumeattachment "$VA"
    else
        echo "No VolumeAttachment found for PVC $PVC (PV: $PV)"
    fi
done

echo "Waiting a few seconds for cleanup..."
sleep 5

echo "Scaling up deployment $DEPLOYMENT..."
kubectl scale deploy "$DEPLOYMENT" --replicas=1 -n "$NAMESPACE"

echo "Done. Check status with: kubectl get pods -n $NAMESPACE | grep $DEPLOYMENT"
