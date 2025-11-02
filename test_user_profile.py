#!/usr/bin/env python
"""
Test script for UserProfile model functionality
"""
import os
import sys
import django

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'adhd_print_project.settings')
django.setup()

from django.contrib.auth.models import User
from tasks.models import UserProfile

def test_user_profile():
    """Test UserProfile creation and functionality"""
    print("🧪 Testing UserProfile Model")
    print("=" * 50)
    
    # Test 1: Create a user and verify profile is auto-created
    print("\n1. Testing automatic profile creation...")
    
    # Clean up any existing test user first
    User.objects.filter(username='testuser').delete()
    
    user = User.objects.create_user(
        username='testuser',
        email='test@example.com',
        password='testpass123'
    )
    
    # Check if profile was created automatically
    if hasattr(user, 'profile'):
        print("   ✅ UserProfile created automatically")
        profile = user.profile
        print(f"   Default printing method: {profile.printing_method}")
        print(f"   Local printing enabled: {profile.local_printing_enabled}")
    else:
        print("   ❌ UserProfile not created automatically")
        return False
    
    # Test 2: Test effective printing method
    print("\n2. Testing effective printing method logic...")
    
    # Default should be server
    effective = profile.get_effective_printing_method()
    print(f"   Default effective method: {effective}")
    assert effective == 'server', f"Expected 'server', got '{effective}'"
    
    # Enable local printing and set preference to local
    profile.local_printing_enabled = True
    profile.printing_method = 'local'
    profile.save()
    
    effective = profile.get_effective_printing_method()
    print(f"   With local enabled and preferred: {effective}")
    assert effective == 'local', f"Expected 'local', got '{effective}'"
    
    # Test auto mode
    profile.printing_method = 'auto'
    profile.save()
    
    effective = profile.get_effective_printing_method()
    print(f"   Auto mode with local enabled: {effective}")
    assert effective == 'local', f"Expected 'local', got '{effective}'"
    
    # Disable local printing
    profile.local_printing_enabled = False
    profile.save()
    
    effective = profile.get_effective_printing_method()
    print(f"   Auto mode with local disabled: {effective}")
    assert effective == 'server', f"Expected 'server', got '{effective}'"
    
    print("   ✅ All printing method tests passed")
    
    # Test 3: Test local printer configuration
    print("\n3. Testing local printer configuration...")
    
    # Initially no printer configured
    has_printer = profile.has_local_printer_configured()
    print(f"   Initially has printer: {has_printer}")
    assert not has_printer, "Should not have printer configured initially"
    
    # Configure a printer
    profile.preferred_local_printer = {
        'device_id': 'USB001',
        'name': 'Test Thermal Printer',
        'connection_type': 'USB'
    }
    profile.save()
    
    has_printer = profile.has_local_printer_configured()
    print(f"   After configuration: {has_printer}")
    assert has_printer, "Should have printer configured after setting device_id"
    
    print("   ✅ Local printer configuration tests passed")
    
    # Test 4: Test string representation
    print("\n4. Testing string representation...")
    profile_str = str(profile)
    print(f"   Profile string: {profile_str}")
    assert 'testuser' in profile_str, "Username should be in string representation"
    
    print("   ✅ String representation test passed")
    
    # Cleanup
    user.delete()
    
    print("\n" + "=" * 50)
    print("🎉 All UserProfile tests passed!")
    return True

if __name__ == "__main__":
    try:
        success = test_user_profile()
        if success:
            print("\n✅ UserProfile model is working correctly!")
        else:
            print("\n❌ UserProfile model has issues")
            sys.exit(1)
    except Exception as e:
        print(f"\n❌ Error testing UserProfile: {str(e)}")
        import traceback
        traceback.print_exc()
        sys.exit(1)