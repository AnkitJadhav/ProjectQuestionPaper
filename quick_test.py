#!/usr/bin/env python3
"""Quick test of deployed Railway app"""
import requests
import json

BASE_URL = "https://projectquestionpaper-production.up.railway.app"

def quick_test():
    print("🚀 Testing deployed app...")
    
    # Test basic endpoints
    endpoints = [
        "/",
        "/ping", 
        "/health",
        "/status",
        "/documents"
    ]
    
    for endpoint in endpoints:
        try:
            print(f"\n📡 Testing {endpoint}...")
            response = requests.get(f"{BASE_URL}{endpoint}")
            print(f"Status: {response.status_code}")
            
            if response.status_code == 200:
                data = response.json()
                print(f"Response: {json.dumps(data, indent=2)}")
                print("✅ SUCCESS")
            else:
                print(f"❌ FAILED: {response.text}")
                
        except Exception as e:
            print(f"❌ ERROR: {e}")
    
    print("\n🎯 App is ready for interaction!")
    print("Run: python interact_deployed.py")

if __name__ == "__main__":
    quick_test() 