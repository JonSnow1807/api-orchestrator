#!/usr/bin/env python3
"""
Test Demo Account Payment Protection
Verifies that demo accounts cannot make real payments
"""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'backend'))

from backend.src.demo_protection import (
    is_demo_account,
    protect_demo_account,
    validate_demo_subscription,
    get_demo_tier_limit
)

def test_demo_detection():
    """Test demo account detection"""
    print("\n🔍 TESTING DEMO ACCOUNT DETECTION")
    print("-" * 40)

    test_emails = [
        ("demo@streamapi.dev", True),
        ("test@streamapi.dev", True),
        ("demo@example.com", True),
        ("test@example.com", True),
        ("demo@api-orchestrator.com", True),
        ("demouser@gmail.com", True),
        ("testaccount@company.com", True),
        ("trial@business.com", True),
        ("real@company.com", False),
        ("user@gmail.com", False),
        ("john.doe@enterprise.com", False)
    ]

    all_passed = True
    for email, expected in test_emails:
        result = is_demo_account(email)
        status = "✅" if result == expected else "❌"
        print(f"{status} {email}: {'DEMO' if result else 'REGULAR'} account")
        if result != expected:
            all_passed = False

    return all_passed

def test_payment_protection():
    """Test payment protection for demo accounts"""
    print("\n💳 TESTING PAYMENT PROTECTION")
    print("-" * 40)

    demo_emails = ["demo@streamapi.dev", "test@example.com"]
    regular_emails = ["user@company.com", "john@gmail.com"]

    print("\nDemo Accounts (should be blocked):")
    for email in demo_emails:
        try:
            protect_demo_account(email, "payment")
            print(f"❌ {email}: Payment NOT blocked (unexpected)")
            return False
        except Exception as e:
            if "Demo accounts cannot perform payment" in str(e):
                print(f"✅ {email}: Payment blocked correctly")
            else:
                print(f"⚠️ {email}: Unexpected error: {str(e)[:50]}")
                return False

    print("\nRegular Accounts (should be allowed):")
    for email in regular_emails:
        try:
            protect_demo_account(email, "payment")
            print(f"✅ {email}: Payment allowed")
        except Exception as e:
            print(f"❌ {email}: Payment blocked (unexpected): {str(e)[:50]}")
            return False

    return True

def test_subscription_validation():
    """Test subscription tier validation for demo accounts"""
    print("\n📋 TESTING SUBSCRIPTION VALIDATION")
    print("-" * 40)

    demo_email = "demo@streamapi.dev"
    regular_email = "user@company.com"

    # Test demo account tiers
    print(f"\nDemo Account ({demo_email}):")
    tiers = ["free", "starter", "professional", "enterprise"]
    for tier in tiers:
        validation = validate_demo_subscription(demo_email, tier, payment_required=False)
        status = "✅" if validation["allowed"] else "❌"
        print(f"  {status} {tier}: {validation['message'][:50]}...")

    # Test demo with payment
    print(f"\nDemo Account with Payment Attempt:")
    validation = validate_demo_subscription(demo_email, "professional", payment_required=True)
    if not validation["allowed"]:
        print(f"  ✅ Payment blocked: {validation['message'][:60]}...")
    else:
        print(f"  ❌ Payment allowed (unexpected)")
        return False

    # Test regular account
    print(f"\nRegular Account ({regular_email}):")
    validation = validate_demo_subscription(regular_email, "professional", payment_required=True)
    if validation["allowed"]:
        print(f"  ✅ All operations allowed")
    else:
        print(f"  ❌ Operations blocked (unexpected)")
        return False

    return True

def test_demo_tier_limits():
    """Test tier limits for demo accounts"""
    print("\n🎯 TESTING DEMO TIER LIMITS")
    print("-" * 40)

    test_cases = [
        ("demo@streamapi.dev", "professional"),
        ("test@example.com", "professional"),
        ("user@company.com", None)
    ]

    all_passed = True
    for email, expected_limit in test_cases:
        limit = get_demo_tier_limit(email)
        status = "✅" if limit == expected_limit else "❌"
        print(f"{status} {email}: Max tier = {limit or 'No limit'}")
        if limit != expected_limit:
            all_passed = False

    return all_passed

def main():
    """Run all tests"""
    print("\n" + "="*60)
    print("🛡️ DEMO ACCOUNT PAYMENT PROTECTION TEST SUITE")
    print("="*60)

    tests = [
        ("Demo Detection", test_demo_detection),
        ("Payment Protection", test_payment_protection),
        ("Subscription Validation", test_subscription_validation),
        ("Tier Limits", test_demo_tier_limits)
    ]

    results = {}
    for test_name, test_func in tests:
        try:
            results[test_name] = test_func()
        except Exception as e:
            print(f"\n⚠️ Test '{test_name}' failed with error: {e}")
            results[test_name] = False

    # Summary
    print("\n" + "="*60)
    print("📊 TEST SUMMARY")
    print("="*60)

    total_tests = len(results)
    passed_tests = sum(1 for r in results.values() if r)

    for test_name, passed in results.items():
        status = "✅ PASSED" if passed else "❌ FAILED"
        print(f"{status}: {test_name}")

    print(f"\n📈 Overall: {passed_tests}/{total_tests} tests passed")

    if passed_tests == total_tests:
        print("\n🎉 ALL TESTS PASSED - DEMO PAYMENT PROTECTION IS WORKING!")
        print("✅ Demo accounts cannot make real payments")
        print("✅ Demo accounts get professional features for free")
        print("✅ Regular accounts can make payments normally")
        return 0
    else:
        print("\n⚠️ SOME TESTS FAILED - Review the protection logic")
        return 1

if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code)