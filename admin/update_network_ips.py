#!/usr/bin/env python3
"""
Update Network IPs Script
Automatically updates all IP references in the GitOps repo when moving to a new network
"""

import os
import sys
import subprocess
from pathlib import Path

def run_command(cmd):
    """Run a command and return success status"""
    try:
        result = subprocess.run(cmd, shell=True, capture_output=True, text=True)
        return result.returncode == 0, result.stdout, result.stderr
    except Exception as e:
        return False, "", str(e)

def find_and_replace_ip(old_ip, new_ip, dry_run=False):
    """Find and replace IP addresses in all YAML files"""
    
    directories = ['components', 'sealed-secrets', 'argocd', 'apps']
    files_changed = []
    
    print(f"🔍 Searching for '{old_ip}' in YAML files...")
    print()
    
    for directory in directories:
        if not os.path.exists(directory):
            continue
            
        # Find all YAML files
        for root, dirs, files in os.walk(directory):
            for file in files:
                if file.endswith(('.yaml', '.yml')):
                    filepath = os.path.join(root, file)
                    
                    # Read file
                    with open(filepath, 'r') as f:
                        content = f.read()
                    
                    # Check if old IP exists
                    if old_ip in content:
                        files_changed.append(filepath)
                        print(f"  📄 Found in: {filepath}")
                        
                        if not dry_run:
                            # Replace IP
                            new_content = content.replace(old_ip, new_ip)
                            with open(filepath, 'w') as f:
                                f.write(new_content)
                            print(f"     ✅ Updated")
                        else:
                            print(f"     [DRY RUN - would update]")
    
    return files_changed

def update_kubectl_config(old_ip, new_ip):
    """Update kubectl config with new control plane IP"""
    kubeconfig = Path.home() / '.kube' / 'config'
    
    if not kubeconfig.exists():
        print(f"⚠️  kubectl config not found at {kubeconfig}")
        return False
    
    print(f"\n🔧 Updating kubectl config...")
    
    with open(kubeconfig, 'r') as f:
        content = f.read()
    
    if old_ip in content:
        new_content = content.replace(f"https://{old_ip}:6443", f"https://{new_ip}:6443")
        
        # Backup original
        backup_path = kubeconfig.with_suffix('.config.backup')
        with open(backup_path, 'w') as f:
            f.write(content)
        print(f"  💾 Backup saved to: {backup_path}")
        
        # Write new config
        with open(kubeconfig, 'w') as f:
            f.write(new_content)
        print(f"  ✅ kubectl config updated")
        return True
    else:
        print(f"  ℹ️  No changes needed in kubectl config")
        return False

def main():
    print("=" * 60)
    print("Glasgow GitOps - Network IP Update Tool")
    print("=" * 60)
    print()
    
    # Get current and new IPs
    print("This script will update all IP references in your GitOps repo.")
    print()
    
    old_ip = input("Enter OLD IP address (e.g., 192.168.1.20): ").strip()
    new_ip = input("Enter NEW IP address (e.g., 192.168.0.20): ").strip()
    
    if not old_ip or not new_ip:
        print("❌ Both IPs are required!")
        sys.exit(1)
    
    # Validate IP format (basic)
    import re
    ip_pattern = r'^\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}$'
    if not re.match(ip_pattern, old_ip) or not re.match(ip_pattern, new_ip):
        print("❌ Invalid IP format!")
        sys.exit(1)
    
    print()
    print(f"Will replace: {old_ip} → {new_ip}")
    print()
    
    # Dry run first
    dry_run = input("Run in DRY RUN mode first? (y/n): ").strip().lower()
    is_dry_run = dry_run == 'y'
    
    print()
    print("=" * 60)
    if is_dry_run:
        print("DRY RUN MODE - No files will be modified")
    else:
        print("LIVE MODE - Files will be modified")
    print("=" * 60)
    print()
    
    # Find and replace in YAML files
    files_changed = find_and_replace_ip(old_ip, new_ip, dry_run=is_dry_run)
    
    if not files_changed:
        print("\n✅ No files found with old IP address")
        return
    
    print()
    print(f"📊 Summary: {len(files_changed)} file(s) {'would be' if is_dry_run else 'were'} updated")
    
    if is_dry_run:
        print()
        proceed = input("Proceed with actual update? (yes/no): ").strip().lower()
        if proceed != 'yes':
            print("Cancelled.")
            return
        
        print()
        print("=" * 60)
        print("LIVE MODE - Updating files...")
        print("=" * 60)
        print()
        
        # Run again without dry run
        find_and_replace_ip(old_ip, new_ip, dry_run=False)
    
    # Update kubectl config
    update_kubectl_config(old_ip, new_ip)
    
    # Show git diff
    print()
    print("=" * 60)
    print("Git Changes:")
    print("=" * 60)
    run_command("git diff --stat")
    
    print()
    print("=" * 60)
    print("✅ Update Complete!")
    print("=" * 60)
    print()
    print("Next steps:")
    print("  1. Review changes: git diff")
    print("  2. Test kubectl: kubectl get nodes")
    print("  3. Commit changes: git add . && git commit -m 'Update network IPs'")
    print("  4. Push to repo: git push origin main")
    print("  5. Sync ArgoCD: python3 admin/cluster_manager.py sync")
    print()

if __name__ == "__main__":
    main()
