#!/usr/bin/env python3
"""
Test script for Render.com deployment
"""
import requests
import json
import time

def test_render_deployment(base_url):
    """Test the deployed app on Render.com"""
    print("🚀 Testing Render.com deployment...")
    print(f"📡 Base URL: {base_url}")
    print()
    
    tests = [
        ("GET", "/", "Basic health check"),
        ("GET", "/health", "Health endpoint"),
        ("GET", "/ping", "Ping endpoint"),
        ("GET", "/status", "Status endpoint"),
        ("GET", "/documents", "Documents endpoint"),
    ]
    
    success_count = 0
    total_tests = len(tests)
    
    for method, endpoint, description in tests:
        url = f"{base_url.rstrip('/')}{endpoint}"
        print(f"📡 Testing {description}...")
        print(f"   {method} {endpoint}")
        
        try:
            response = requests.get(url, timeout=30)
            status = response.status_code
            
            if status == 200:
                print(f"   ✅ SUCCESS: {status}")
                try:
                    data = response.json()
                    if 'mode' in data:
                        print(f"   📊 Mode: {data['mode']}")
                    if 'status' in data:
                        print(f"   📊 Status: {data['status']}")
                except:
                    print(f"   📊 Response: {response.text[:100]}...")
                success_count += 1
            else:
                print(f"   ❌ FAILED: {status}")
                print(f"   📊 Response: {response.text[:200]}...")
                
        except requests.RequestException as e:
            print(f"   ❌ ERROR: {str(e)}")
        
        print()
    
    print(f"🎯 Test Results: {success_count}/{total_tests} tests passed")
    
    if success_count >= 3:
        print("✅ Deployment is working!")
        print("🎉 Your app is live on Render.com!")
    else:
        print("❌ Some issues detected. Check Render.com logs.")
    
    return success_count >= 3

def main():
    print("🔧 Render.com Deployment Tester")
    print("=" * 50)
    
    # Prompt for URL
    url = input("Enter your Render.com app URL: ").strip()
    
    if not url:
        print("❌ No URL provided")
        return
    
    if not url.startswith('http'):
        url = f"https://{url}"
    
    print(f"🎯 Testing: {url}")
    print()
    
    # Test deployment
    success = test_render_deployment(url)
    
    if success:
        print("\n🚀 Next Steps:")
        print("1. Test file upload functionality")
        print("2. Try generating questions")
        print("3. Check the React frontend")
        print("4. Monitor performance in Render dashboard")

if __name__ == "__main__":
    main() 