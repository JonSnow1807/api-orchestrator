#!/usr/bin/env python3
"""
Script to fetch Stripe price IDs from your account
"""

import stripe
import os

# Use your secret key
stripe.api_key = input("Enter your Stripe SECRET key (sk_live_...): ").strip()

try:
    # Fetch all products with prices
    products = stripe.Product.list(active=True, expand=['data.default_price'])
    
    print("\n" + "="*60)
    print("YOUR STRIPE PRODUCTS AND PRICE IDS:")
    print("="*60)
    
    for product in products.data:
        print(f"\nProduct: {product.name}")
        print(f"Product ID: {product.id}")
        
        # Get all prices for this product
        prices = stripe.Price.list(product=product.id, active=True)
        
        for price in prices.data:
            amount = price.unit_amount / 100 if price.unit_amount else 0
            interval = price.recurring.interval if price.recurring else "one-time"
            print(f"  Price: ${amount:.2f} {interval}")
            print(f"  Price ID: {price.id}")
            print(f"  Copy this: {price.id}")
            print()
    
    print("\n" + "="*60)
    print("ADD THESE TO RAILWAY:")
    print("="*60)
    
    # Try to match products to tiers
    for product in products.data:
        prices = stripe.Price.list(product=product.id, active=True)
        if prices.data:
            price = prices.data[0]
            name_lower = product.name.lower()
            
            if 'starter' in name_lower:
                print(f"STRIPE_PRICE_STARTER={price.id}")
            elif 'professional' in name_lower or 'pro' in name_lower:
                print(f"STRIPE_PRICE_PROFESSIONAL={price.id}")
            elif 'enterprise' in name_lower:
                print(f"STRIPE_PRICE_ENTERPRISE={price.id}")
    
except Exception as e:
    print(f"Error: {e}")
    print("\nMake sure you're using the correct secret key.")