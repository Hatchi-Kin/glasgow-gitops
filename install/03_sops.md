### 1. **Install SOPS and age**

```sh
curl -LO https://github.com/getsops/sops/releases/download/v3.10.2/sops-v3.10.2.linux.amd64
sudo mv sops-v3.10.2.linux.amd64 /usr/local/bin/sops
chmod +x /usr/local/bin/sops
sops --version
```

```sh
curl -LO https://github.com/FiloSottile/age/releases/download/v1.1.1/age-v1.1.1-linux-amd64.tar.gz
tar -xzf age-v1.1.1-linux-amd64.tar.gz
sudo mv age/age age/age-keygen /usr/local/bin/
rm -rf age-v1.1.1-linux-amd64.tar.gz age
age --version
age-keygen --version
```

---

### 2. **Generate an age key pair (do NOT commit the private key!)**

```sh
age-keygen -o age.key
cat age.key | grep public
```
Copy the `age1...` public key.

---

### 3. **Create `.sops.yaml` with your public key**

```sh
# Get your public key
PUBKEY=$(cat age.key | grep 'public key' | awk '{print $4}')

# Create .sops.yaml with the CORRECT syntax (no brackets)
cat > .sops.yaml <<EOF
creation_rules:
  - encrypted_regex: '^(data|stringData)$'
    age: $PUBKEY
EOF
```

Commit only `.sops.yaml`

---

### 4. **Provide the age private key to ArgoCD**

**This step is required for ArgoCD to decrypt secrets:**

```sh
kubectl -n argocd create secret generic sops-age --from-file=age.agekey=age.key
```

---

### 5. **Secure your private key**

- **Never commit `age.key` to git.**
- Back up `age.key` securely (password manager, encrypted storage, etc).

```sh
rm age.key
```
