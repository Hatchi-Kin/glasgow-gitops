# Navidrome File Upload Guide

This guide provides step-by-step instructions for uploading files to Navidrome when shared storage is not working as expected.

## Prerequisites
- Kubernetes cluster with Navidrome deployed.
- `kubectl` installed and configured to access your cluster.
- Files to upload are available on your local machine.

## Steps to Upload Files

### 1. Copy a Single File to Navidrome Pod
To copy a single file to the Navidrome pod:
```bash
kubectl cp "/path/to/your/file.mp3" <namespace>/<navidrome-pod-name>:/music
```
Example:
```bash
kubectl cp "/home/kin/Music/Anne-Marie - Speak Your Mind (Deluxe) (2018) Mp3 (320kbps) [Hunter]/10. 2002.mp3" glasgow-prod/navidrome-5df46549bc-g8qpq:/music
```

### 2. Copy an Entire Directory to Navidrome Pod
To copy a directory (including subfolders and files):
```bash
kubectl cp "/path/to/your/directory" <namespace>/<navidrome-pod-name>:/music
```
Example:
```bash
kubectl cp "/home/kin/Music/Anne-Marie - Speak Your Mind (Deluxe) (2018) Mp3 (320kbps) [Hunter]/" glasgow-prod/navidrome-5df46549bc-g8qpq:/music
```

### 3. Verify Files in the Pod
After copying, verify that the files are present in the `/music` directory of the Navidrome pod:
```bash
kubectl exec -n <namespace> <navidrome-pod-name> -- ls -l /music
```
Example:
```bash
kubectl exec -n glasgow-prod navidrome-5df46549bc-g8qpq -- ls -l /music
```

### 4. Trigger a Library Scan
To make Navidrome detect the new files, trigger a library scan using its API:
```bash
kubectl exec -n <namespace> <navidrome-pod-name> -- curl -X POST http://localhost:4533/api/library/scan
```
Example:
```bash
kubectl exec -n glasgow-prod navidrome-5df46549bc-g8qpq -- curl -X POST http://localhost:4533/api/library/scan
```

### 5. Check Navidrome Logs
If the files do not appear in the UI, check the Navidrome logs for any errors:
```bash
kubectl logs -n <namespace> <navidrome-pod-name>
```
Example:
```bash
kubectl logs -n glasgow-prod navidrome-5df46549bc-g8qpq
```

### 6. Restart the Navidrome Pod (Optional)
If the files still do not appear, restart the Navidrome pod to ensure it picks up the new files:
```bash
kubectl delete pod -n <namespace> <navidrome-pod-name>
```
Example:
```bash
kubectl delete pod -n glasgow-prod navidrome-5df46549bc-g8qpq
```

## Notes
- Replace `<namespace>` with your Kubernetes namespace (e.g., `glasgow-prod`).
- Replace `<navidrome-pod-name>` with the name of your Navidrome pod (e.g., `navidrome-5df46549bc-g8qpq`).
- Ensure the files have the correct permissions and ownership for Navidrome to access them.
- This guide assumes that shared storage (e.g., RWX PVCs) is not being used due to issues.

## Troubleshooting
- If you encounter errors during file upload, ensure the file path is correct and properly escaped (e.g., spaces and special characters).
- If the library scan does not detect files, check the Navidrome logs for errors.
- For large-scale uploads, consider scripting the `kubectl cp` commands or using a different storage solution if possible.
