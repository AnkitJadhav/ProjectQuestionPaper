#!/usr/bin/env python3
"""
Test Redis connectivity
"""

try:
    import redis
    
    # Test Redis connection
    r = redis.Redis(host='localhost', port=6379, db=0)
    
    # Test ping
    result = r.ping()
    print(f"✅ Redis connection successful: {result}")
    
    # Test set/get
    r.set('test_key', 'test_value')
    value = r.get('test_key')
    print(f"✅ Redis set/get test: {value.decode() if value else 'None'}")
    
    # Clean up
    r.delete('test_key')
    print("✅ Redis is working properly!")
    
except Exception as e:
    print(f"❌ Redis connection failed: {e}")
    print("Please make sure Redis server is running on localhost:6379") 