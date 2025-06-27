#!/usr/bin/env python3
"""
Update Railway URL in local scripts
"""
import os
import re

def update_url_in_files(new_url):
    """Update the Railway URL in our local scripts"""
    files_to_update = [
        "interact_deployed.py",
        "quick_test.py"
    ]
    
    old_pattern = r'https://projectquestionpaper[^"]*\.up\.railway\.app'
    
    for filename in files_to_update:
        if os.path.exists(filename):
            print(f"📝 Updating {filename}...")
            
            with open(filename, 'r') as f:
                content = f.read()
            
            # Replace the URL
            updated_content = re.sub(old_pattern, new_url, content)
            
            with open(filename, 'w') as f:
                f.write(updated_content)
            
            print(f"✅ Updated {filename}")
        else:
            print(f"❌ File not found: {filename}")
    
    print(f"\n🎯 Updated scripts to use: {new_url}")

def main():
    print("🔧 Railway URL Updater")
    print("=" * 50)
    
    new_url = input("Enter your new Railway URL: ").strip()
    
    if not new_url.startswith("https://"):
        new_url = "https://" + new_url
    
    if not new_url.endswith(".up.railway.app"):
        if not new_url.endswith(".railway.app"):
            print("❌ URL should end with .up.railway.app or .railway.app")
            return
    
    print(f"🚀 Updating to: {new_url}")
    update_url_in_files(new_url)
    
    print("\n🧪 Testing new URL...")
    import requests
    try:
        response = requests.get(f"{new_url}/ping", timeout=10)
        if response.status_code == 200:
            print("✅ New URL is working!")
        else:
            print(f"⚠️  URL responded with status: {response.status_code}")
    except Exception as e:
        print(f"❌ Error testing URL: {e}")

if __name__ == "__main__":
    main() 