# 💳 Stripe Setup Guide

## Quick Start (Testing Without Stripe)

The application now works in **MOCK MODE** by default, so you can test all billing features without a Stripe account!

When running in mock mode:
- ✅ All billing features work normally
- ✅ No real charges occur
- ✅ Test subscription upgrades/downgrades
- ✅ Track usage and see billing dashboard
- ⚠️ A yellow "TEST MODE" banner appears on the billing page

## Setting Up Real Stripe Integration

### Step 1: Create a Stripe Account
1. Go to [stripe.com](https://stripe.com)
2. Click "Start now" and create your account
3. Verify your email

### Step 2: Get Your API Keys
1. Go to [Stripe Dashboard](https://dashboard.stripe.com)
2. Navigate to **Developers → API keys**
3. Copy your keys:
   - **Publishable key**: `pk_test_...` (for frontend)
   - **Secret key**: `sk_test_...` (for backend)

### Step 3: Create Products and Prices
1. Go to **Products** in Stripe Dashboard
2. Create three products:

#### Starter Plan
- Name: "API Orchestrator Starter"
- Price: $49/month
- Copy the price ID (starts with `price_`)

#### Professional Plan
- Name: "API Orchestrator Professional"
- Price: $199/month
- Copy the price ID

#### Enterprise Plan
- Name: "API Orchestrator Enterprise"
- Price: $999/month
- Copy the price ID

### Step 4: Set Up Webhook (Optional)
1. Go to **Developers → Webhooks**
2. Add endpoint: `https://your-domain.com/api/billing/webhook`
3. Select events:
   - `invoice.payment_succeeded`
   - `invoice.payment_failed`
   - `customer.subscription.deleted`
   - `customer.subscription.updated`
4. Copy the webhook secret (`whsec_...`)

### Step 5: Configure Environment Variables

Update your `.env` file:

```bash
# Stripe Configuration
STRIPE_SECRET_KEY=sk_test_your_actual_secret_key
STRIPE_PUBLISHABLE_KEY=pk_test_your_actual_publishable_key
STRIPE_WEBHOOK_SECRET=whsec_your_webhook_secret
STRIPE_STARTER_PRICE_ID=price_your_starter_price_id
STRIPE_PRO_PRICE_ID=price_your_professional_price_id
STRIPE_ENTERPRISE_PRICE_ID=price_your_enterprise_price_id
```

### Step 6: Update Frontend Environment

Create `.env` in the frontend directory:

```bash
VITE_STRIPE_PUBLISHABLE_KEY=pk_test_your_actual_publishable_key
```

### Step 7: Test Your Integration

1. Restart your backend server
2. Restart your frontend (npm run dev)
3. The "TEST MODE" banner should disappear
4. Use Stripe test cards:
   - Success: `4242 4242 4242 4242`
   - Decline: `4000 0000 0000 0002`
   - Requires auth: `4000 0025 0000 3155`

## Testing Different Scenarios

### In Mock Mode (Default)
- All features work without real payments
- Perfect for development and testing
- Users can upgrade/downgrade instantly
- Usage tracking works normally

### With Real Stripe
- Real payment processing
- Subscription management
- Invoice generation
- Webhook handling for events

## Common Issues

### "TEST MODE" banner still showing?
- Check that your `.env` has the correct Stripe keys
- Ensure frontend `.env` has `VITE_STRIPE_PUBLISHABLE_KEY`
- Restart both backend and frontend servers

### Payment failing?
- Use Stripe test cards (not real cards)
- Check Stripe Dashboard for error logs
- Verify your API keys are correct

### Webhooks not working?
- Use ngrok for local testing: `ngrok http 8000`
- Update webhook URL in Stripe Dashboard
- Check webhook secret is correct

## Support

- Stripe Documentation: [stripe.com/docs](https://stripe.com/docs)
- Test Cards: [stripe.com/docs/testing](https://stripe.com/docs/testing)
- API Reference: [stripe.com/docs/api](https://stripe.com/docs/api)

## Revenue Projections 🚀

With this billing system, here's how to reach $1B valuation:

### Year 1 Target: $1M ARR
- 100 Starter customers: $4,900/month
- 20 Professional customers: $3,980/month
- 2 Enterprise customers: $1,998/month
- **Total**: $10,878/month = $130,536/year

### Year 2 Target: $10M ARR
- 1,000 Starter: $49,000/month
- 200 Professional: $39,800/month
- 20 Enterprise: $19,980/month
- **Total**: $108,780/month = $1.3M/year

### Year 3 Target: $50M ARR
- 5,000 Starter: $245,000/month
- 1,000 Professional: $199,000/month
- 100 Enterprise: $99,900/month
- **Total**: $543,900/month = $6.5M/year

### Path to $1B Valuation
- Reach $100M ARR (10x valuation multiple)
- 10,000+ paid customers
- 50%+ YoY growth
- 140%+ net revenue retention
- International expansion