### 1. **Install SOPS and age**

https://github.com/getsops/sops/releases

```sh
# Download the binary
curl -LO https://github.com/getsops/sops/releases/download/v3.10.2/sops-v3.10.2.linux.amd64

# Move the binary in to your PATH
sudo mv sops-v3.10.2.linux.amd64 /usr/local/bin/sops

# Make the binary executable
chmod +x /usr/local/bin/sops
```

test if installed correctly:
```sh
sops --version
```
### 2. **Install age**
```sh
curl -LO https://github.com/FiloSottile/age/releases/download/v1.1.1/age-v1.1.1-linux-amd64.tar.gz
tar -xzf age-v1.1.1-linux-amd64.tar.gz
sudo mv age/age age/age-keygen /usr/local/bin/
```
delete the downloaded files:
```sh
rm -rf age-v1.1.1-linux-amd64.tar.gz age
```

test if installed correctly:
```sh
age --version
age-keygen --version
```

### 3. **Generate an age key pair**
```sh
age-keygen -o age.key
cat age.key | grep public
```

save into .sops.yaml:
```sh   
PUBKEY=$(cat age.key | grep 'public key' | awk '{print $4}')
echo "creation_rules:
  - encrypted_regex: '^(data|stringData)$'
    age: [ \"$PUBKEY\" ]
" > .sops.yaml
```
```sh
rm age.key
```
