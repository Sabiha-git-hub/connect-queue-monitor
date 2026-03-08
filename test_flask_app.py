"""
Simple test script to verify Flask app initialization and security headers.

This script tests that:
1. The Flask app can be created successfully
2. Security headers are properly configured
3. The health check endpoint works
"""

from app import app

def test_app_creation():
    """Test that the Flask app can be created."""
    print("✓ Testing Flask app creation...")
    assert app is not None
    print("  ✅ Flask app created successfully!")

def test_security_headers():
    """Test that security headers are present in responses."""
    print("\n✓ Testing security headers...")
    
    with app.test_client() as client:
        # Make a request to the health check endpoint
        response = client.get('/health')
        
        # Check that response is successful
        assert response.status_code == 200
        print("  ✅ Health check endpoint responding!")
        
        # Check Content-Security-Policy header
        assert 'Content-Security-Policy' in response.headers
        csp = response.headers['Content-Security-Policy']
        assert 'frame-ancestors' in csp
        print(f"  ✅ CSP header present: {csp}")
        
        # Check X-Frame-Options header
        assert 'X-Frame-Options' in response.headers
        print(f"  ✅ X-Frame-Options header present: {response.headers['X-Frame-Options']}")
        
        # Check X-Content-Type-Options header
        assert 'X-Content-Type-Options' in response.headers
        print(f"  ✅ X-Content-Type-Options header present: {response.headers['X-Content-Type-Options']}")

def test_health_endpoint():
    """Test the health check endpoint returns correct data."""
    print("\n✓ Testing health check endpoint...")
    
    with app.test_client() as client:
        response = client.get('/health')
        data = response.get_json()
        
        assert data['status'] == 'healthy'
        assert data['iframe_ready'] == True
        print(f"  ✅ Health check data: {data}")

if __name__ == '__main__':
    print("=" * 60)
    print("Flask App Security Configuration Test")
    print("=" * 60)
    
    try:
        test_app_creation()
        test_security_headers()
        test_health_endpoint()
        
        print("\n" + "=" * 60)
        print("🎉 All tests passed! Flask app is properly configured.")
        print("=" * 60)
        
    except AssertionError as e:
        print(f"\n❌ Test failed: {e}")
    except Exception as e:
        print(f"\n❌ Unexpected error: {e}")
