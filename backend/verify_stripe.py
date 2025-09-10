#!/usr/bin/env python
"""
Stripe Configuration Verification
Checks that your Stripe keys and price IDs are properly configured
"""

import os
import sys
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

def check_stripe_config():
    print("="*60)
    print("🔍 STRIPE CONFIGURATION CHECK")
    print("="*60)
    
    required_vars = {
        "STRIPE_SECRET_KEY": "Secret key for Stripe API",
        "STRIPE_PUBLISHABLE_KEY": "Publishable key for frontend",
        "STRIPE_WEBHOOK_SECRET": "Webhook endpoint secret",
        "STRIPE_STARTER_PRICE_ID": "Price ID for Starter tier",
        "STRIPE_PRO_PRICE_ID": "Price ID for Professional tier",
        "STRIPE_ENTERPRISE_PRICE_ID": "Price ID for Enterprise tier"
    }
    
    optional_vars = {
        "STRIPE_PRICE_STARTER": "Starter price amount",
        "STRIPE_PRICE_PROFESSIONAL": "Professional price amount",
        "STRIPE_PRICE_ENTERPRISE": "Enterprise price amount",
        "VITE_STRIPE_PUBLISHABLE_KEY": "Frontend Stripe key"
    }
    
    missing = []
    configured = []
    
    print("\n📋 Required Variables:")
    for var, description in required_vars.items():
        value = os.getenv(var)
        if value:
            # Mask the value for security
            masked = value[:7] + "..." + value[-4:] if len(value) > 11 else "***"
            print(f"✅ {var}: {masked}")
            configured.append(var)
        else:
            print(f"❌ {var}: NOT SET - {description}")
            missing.append(var)
    
    print("\n📋 Optional Variables:")
    for var, description in optional_vars.items():
        value = os.getenv(var)
        if value:
            masked = value[:7] + "..." if len(value) > 7 else value
            print(f"✅ {var}: {masked}")
        else:
            print(f"⚠️ {var}: Not set ({description})")
    
    # Test Stripe API connection if keys are available
    if "STRIPE_SECRET_KEY" in configured:
        print("\n🔗 Testing Stripe API Connection...")
        try:
            import stripe
            stripe.api_key = os.getenv("STRIPE_SECRET_KEY")
            
            # Try to list products (won't reveal sensitive data)
            try:
                products = stripe.Product.list(limit=1)
                print(f"✅ Stripe API connected successfully")
                print(f"   Found {len(products.data)} products")
                
                # Check if price IDs are valid
                price_ids = [
                    os.getenv("STRIPE_STARTER_PRICE_ID"),
                    os.getenv("STRIPE_PRO_PRICE_ID"),
                    os.getenv("STRIPE_ENTERPRISE_PRICE_ID")
                ]
                
                for price_id in price_ids:
                    if price_id:
                        try:
                            price = stripe.Price.retrieve(price_id)
                            print(f"✅ Price ID {price_id[:10]}... is valid (${price.unit_amount/100:.2f})")
                        except Exception as e:
                            print(f"❌ Price ID {price_id[:10]}... is invalid: {e}")
                
            except stripe.error.AuthenticationError:
                print("❌ Invalid Stripe secret key")
            except Exception as e:
                print(f"❌ Stripe API error: {e}")
                
        except ImportError:
            print("⚠️ Stripe library not installed (pip install stripe)")
    
    # Summary
    print("\n" + "="*60)
    print("📊 SUMMARY")
    print("="*60)
    
    if not missing:
        print("✅ All required Stripe variables are configured!")
        print("✅ Your Stripe integration should work correctly")
        
        print("\n🚀 Next Steps:")
        print("1. Deploy to Railway (git push will auto-deploy)")
        print("2. Set up Stripe webhook endpoint:")
        print(f"   https://YOUR-RAILWAY-URL/api/webhooks/stripe")
        print("3. Test with a real payment flow")
    else:
        print(f"❌ Missing {len(missing)} required variables:")
        for var in missing:
            print(f"   - {var}")
        print("\n⚠️ Please set these in Railway dashboard")
    
    return len(missing) == 0

def check_railway_vars():
    """Check if running on Railway"""
    print("\n" + "="*60)
    print("🚂 RAILWAY ENVIRONMENT CHECK")
    print("="*60)
    
    railway_vars = {
        "RAILWAY_ENVIRONMENT": os.getenv("RAILWAY_ENVIRONMENT"),
        "RAILWAY_PROJECT_ID": os.getenv("RAILWAY_PROJECT_ID"),
        "RAILWAY_SERVICE_ID": os.getenv("RAILWAY_SERVICE_ID"),
        "DATABASE_URL": os.getenv("DATABASE_URL")
    }
    
    is_railway = any(railway_vars.values())
    
    if is_railway:
        print("✅ Running on Railway platform")
        for var, value in railway_vars.items():
            if value:
                masked = value[:10] + "..." if len(value) > 10 else value
                print(f"   {var}: {masked}")
    else:
        print("📍 Running locally (not on Railway)")
    
    return is_railway

if __name__ == "__main__":
    # Check Stripe configuration
    stripe_ok = check_stripe_config()
    
    # Check Railway environment
    is_railway = check_railway_vars()
    
    print("\n" + "="*60)
    print("🎯 FINAL STATUS")
    print("="*60)
    
    if stripe_ok:
        if is_railway:
            print("✅ PRODUCTION READY on Railway with Stripe!")
        else:
            print("✅ Stripe configured for local development")
            print("📝 Note: Set the same variables in Railway dashboard for production")
    else:
        print("⚠️ Please configure missing Stripe variables")
        print("📝 Add them to Railway dashboard or .env file")
    
    sys.exit(0 if stripe_ok else 1)