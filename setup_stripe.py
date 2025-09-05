#!/usr/bin/env python
"""
Stripe Setup Script - Creates products and prices automatically
Run this after you have your Stripe API keys
"""

import os
import stripe
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Get Stripe key
STRIPE_SECRET_KEY = os.getenv("STRIPE_SECRET_KEY")

if not STRIPE_SECRET_KEY:
    print("❌ STRIPE_SECRET_KEY not found in .env file")
    print("\nPlease follow these steps:")
    print("1. Go to https://stripe.com and create an account")
    print("2. Go to Developers → API keys")
    print("3. Copy your Secret key (starts with sk_test_)")
    print("4. Add it to your .env file:")
    print("   STRIPE_SECRET_KEY=sk_test_your_key_here")
    exit(1)

stripe.api_key = STRIPE_SECRET_KEY

def create_products():
    """Create products and prices in Stripe"""
    
    print("🚀 Setting up Stripe products...")
    
    products_config = [
        {
            "name": "API Orchestrator Starter",
            "description": "Perfect for small teams and startups",
            "price": 4900,  # in cents
            "features": [
                "10,000 API calls per month",
                "AI-powered analysis",
                "Mock server generation",
                "Email support"
            ]
        },
        {
            "name": "API Orchestrator Professional",
            "description": "For growing businesses and teams",
            "price": 19900,  # in cents
            "features": [
                "100,000 API calls per month",
                "Advanced AI insights",
                "Custom integrations",
                "Priority support",
                "API analytics dashboard"
            ]
        },
        {
            "name": "API Orchestrator Enterprise",
            "description": "For large organizations with custom needs",
            "price": 99900,  # in cents
            "features": [
                "Unlimited API calls",
                "SSO/SAML authentication",
                "SLA guarantees",
                "Dedicated support",
                "Custom deployment",
                "Audit logs"
            ]
        }
    ]
    
    created_prices = []
    
    for config in products_config:
        try:
            # Create product
            product = stripe.Product.create(
                name=config["name"],
                description=config["description"],
                metadata={"features": ", ".join(config["features"])}
            )
            
            # Create price
            price = stripe.Price.create(
                product=product.id,
                unit_amount=config["price"],
                currency="usd",
                recurring={"interval": "month"}
            )
            
            created_prices.append({
                "name": config["name"],
                "product_id": product.id,
                "price_id": price.id,
                "amount": config["price"] / 100
            })
            
            print(f"✅ Created: {config['name']}")
            print(f"   Product ID: {product.id}")
            print(f"   Price ID: {price.id}")
            print(f"   Monthly: ${config['price'] / 100}")
            print()
            
        except stripe.error.StripeError as e:
            print(f"❌ Error creating {config['name']}: {e}")
    
    return created_prices

def setup_webhook():
    """Instructions for setting up webhook"""
    
    print("\n📮 Webhook Setup Instructions:")
    print("=" * 50)
    print("\n1. For LOCAL testing (recommended first):")
    print("   a. Install ngrok: brew install ngrok (Mac) or download from ngrok.com")
    print("   b. Run: ngrok http 8000")
    print("   c. Copy the HTTPS URL (like https://abc123.ngrok.io)")
    print("\n2. Go to Stripe Dashboard → Developers → Webhooks")
    print("3. Click 'Add endpoint'")
    print("4. Enter endpoint URL:")
    print("   - Local: https://YOUR-NGROK-URL.ngrok.io/api/billing/webhook")
    print("   - Production: https://yourdomain.com/api/billing/webhook")
    print("\n5. Select these events:")
    print("   ✓ checkout.session.completed")
    print("   ✓ invoice.payment_succeeded")
    print("   ✓ invoice.payment_failed")
    print("   ✓ customer.subscription.deleted")
    print("   ✓ customer.subscription.updated")
    print("\n6. Click 'Add endpoint'")
    print("7. Copy the 'Signing secret' (starts with whsec_)")
    print("8. Add to your .env: STRIPE_WEBHOOK_SECRET=whsec_your_secret")

def generate_env_file(prices):
    """Generate .env configuration"""
    
    print("\n📄 Environment Configuration:")
    print("=" * 50)
    print("\nAdd these to your .env file:\n")
    
    env_content = f"""# Stripe Configuration (PRODUCTION READY)
STRIPE_SECRET_KEY={STRIPE_SECRET_KEY}
STRIPE_PUBLISHABLE_KEY=pk_test_YOUR_PUBLISHABLE_KEY_HERE
STRIPE_WEBHOOK_SECRET=whsec_YOUR_WEBHOOK_SECRET_HERE
"""
    
    if prices:
        env_content += f"""
# Stripe Price IDs (auto-generated)
STRIPE_STARTER_PRICE_ID={prices[0]['price_id']}
STRIPE_PRO_PRICE_ID={prices[1]['price_id']}
STRIPE_ENTERPRISE_PRICE_ID={prices[2]['price_id']}
"""
    
    print(env_content)
    
    # Save to file
    with open('.env.stripe.production', 'w') as f:
        f.write(env_content)
    
    print("\n✅ Configuration saved to .env.stripe.production")

def test_connection():
    """Test Stripe connection"""
    
    print("🔌 Testing Stripe connection...")
    
    try:
        # Try to retrieve account info
        account = stripe.Account.retrieve()
        print(f"✅ Connected to Stripe account: {account.email}")
        print(f"   Account ID: {account.id}")
        print(f"   Mode: {'TEST' if 'test' in STRIPE_SECRET_KEY else 'LIVE'} mode")
        return True
    except stripe.error.AuthenticationError:
        print("❌ Invalid API key. Please check your STRIPE_SECRET_KEY")
        return False
    except Exception as e:
        print(f"❌ Connection failed: {e}")
        return False

def main():
    print("🎯 Stripe Production Setup Script")
    print("=" * 50)
    
    if not test_connection():
        exit(1)
    
    print("\n" + "=" * 50)
    
    # Ask if user wants to create products
    create = input("\n📦 Do you want to create products automatically? (y/n): ")
    
    if create.lower() == 'y':
        prices = create_products()
        generate_env_file(prices)
    else:
        print("\n⚠️  You'll need to create products manually in Stripe Dashboard")
        generate_env_file([])
    
    setup_webhook()
    
    print("\n" + "=" * 50)
    print("🎉 Stripe setup complete!")
    print("\nNext steps:")
    print("1. Copy the configuration from .env.stripe.production to your .env")
    print("2. Get your Publishable key from Stripe Dashboard")
    print("3. Set up the webhook endpoint")
    print("4. Update frontend/.env with VITE_STRIPE_PUBLISHABLE_KEY")
    print("5. Restart your servers")
    print("\n💳 You're ready to accept payments!")

if __name__ == "__main__":
    main()