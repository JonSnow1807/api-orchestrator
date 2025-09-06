"""
Stripe Billing Integration for API Orchestrator
Handles usage-based billing, subscriptions, and payment processing
"""

import os
import stripe
from datetime import datetime, timedelta
from typing import Optional, Dict, List, Any
from decimal import Decimal
from sqlalchemy.orm import Session
from fastapi import HTTPException, status
from pydantic import BaseModel, Field
import logging
import uuid

logger = logging.getLogger(__name__)

# Initialize Stripe with production/test keys
STRIPE_SECRET_KEY = os.getenv("STRIPE_SECRET_KEY", "").strip()
STRIPE_WEBHOOK_SECRET = os.getenv("STRIPE_WEBHOOK_SECRET", "").strip()

# Only initialize Stripe if key is provided
if STRIPE_SECRET_KEY:
    stripe.api_key = STRIPE_SECRET_KEY
    logger.info(f"Stripe initialized with {'test' if 'test' in STRIPE_SECRET_KEY else 'live'} API keys")
else:
    logger.warning("STRIPE_SECRET_KEY not configured - billing features will be disabled")

# Pricing Configuration
PRICING_TIERS = {
    "free": {
        "name": "Free",
        "price": 0,
        "api_calls": 1000,
        "projects": 3,
        "team_members": 1,
        "features": ["basic_discovery", "basic_testing"]
    },
    "starter": {
        "name": "Starter",
        "price": 49,
        "stripe_price_id": os.getenv("STRIPE_STARTER_PRICE_ID"),
        "api_calls": 10000,
        "projects": 10,
        "team_members": 3,
        "features": ["all_free", "ai_analysis", "mock_servers", "export_import"]
    },
    "professional": {
        "name": "Professional",
        "price": 199,
        "stripe_price_id": os.getenv("STRIPE_PRO_PRICE_ID"),
        "api_calls": 100000,
        "projects": 50,
        "team_members": 10,
        "features": ["all_starter", "advanced_ai", "custom_integrations", "priority_support"]
    },
    "enterprise": {
        "name": "Enterprise",
        "price": 999,
        "stripe_price_id": os.getenv("STRIPE_ENTERPRISE_PRICE_ID"),
        "api_calls": -1,  # Unlimited
        "projects": -1,    # Unlimited
        "team_members": -1, # Unlimited
        "features": ["all_pro", "sso", "sla", "dedicated_support", "custom_deployment", "audit_logs"]
    }
}

# Usage-based pricing
USAGE_PRICING = {
    "api_call": Decimal("0.001"),  # $0.001 per API call over limit
    "ai_analysis": Decimal("0.10"),  # $0.10 per AI analysis
    "mock_server_hour": Decimal("0.05"),  # $0.05 per mock server hour
    "export_operation": Decimal("0.01"),  # $0.01 per export
}


class SubscriptionRequest(BaseModel):
    tier: str = Field(..., description="Subscription tier")
    payment_method_id: Optional[str] = Field(None, description="Stripe payment method ID")


class UsageEventRequest(BaseModel):
    event_type: str = Field(..., description="Type of usage event")
    quantity: int = Field(1, description="Quantity of usage")
    metadata: Optional[Dict[str, Any]] = Field(default_factory=dict)


class PaymentMethodRequest(BaseModel):
    payment_method_id: str = Field(..., description="Stripe payment method ID")


class BillingManager:
    """Manages all billing operations"""
    
    def __init__(self, db: Session):
        self.db = db
        
    def create_customer(self, user_id: int, email: str, name: str = None) -> str:
        """Create a Stripe customer for a user"""
        if not STRIPE_SECRET_KEY:
            logger.warning("Stripe not configured - skipping customer creation")
            return f"mock_customer_{user_id}"
            
        try:
            customer = stripe.Customer.create(
                email=email,
                name=name,
                metadata={
                    "user_id": str(user_id),
                    "platform": "api_orchestrator"
                }
            )
            
            # Store customer ID in database
            from src.database import User
            user = self.db.query(User).filter(User.id == user_id).first()
            if user:
                user.stripe_customer_id = customer.id
                self.db.commit()
            
            logger.info(f"Created Stripe customer {customer.id} for user {user_id}")
            return customer.id
            
        except stripe.error.StripeError as e:
            logger.error(f"Stripe error creating customer: {e}")
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Failed to create customer: {str(e)}"
            )
    
    def create_subscription(
        self, 
        user_id: int, 
        tier: str, 
        payment_method_id: str = None
    ) -> Dict[str, Any]:
        """Create or update a subscription for a user"""
        
        if tier not in PRICING_TIERS:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Invalid subscription tier: {tier}"
            )
        
        tier_config = PRICING_TIERS[tier]
        
        # Free tier doesn't need Stripe
        if tier == "free":
            return self._set_free_tier(user_id)
        
        # Check if Stripe is configured
        if not STRIPE_SECRET_KEY:
            logger.warning("Stripe not configured - cannot create paid subscription")
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="Billing system not configured. Please contact support."
            )
        
        from src.database import User
        user = self.db.query(User).filter(User.id == user_id).first()
        
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found"
            )
        
        try:
            # Create Stripe customer if doesn't exist
            if not user.stripe_customer_id:
                user.stripe_customer_id = self.create_customer(
                    user_id, user.email, user.full_name
                )
            
            # Attach payment method if provided
            if payment_method_id:
                stripe.PaymentMethod.attach(
                    payment_method_id,
                    customer=user.stripe_customer_id
                )
                
                # Set as default payment method
                stripe.Customer.modify(
                    user.stripe_customer_id,
                    invoice_settings={
                        "default_payment_method": payment_method_id
                    }
                )
            
            # Check for existing subscription
            subscriptions = stripe.Subscription.list(
                customer=user.stripe_customer_id,
                status="active"
            )
            
            if subscriptions.data:
                # Update existing subscription
                subscription = stripe.Subscription.modify(
                    subscriptions.data[0].id,
                    items=[{
                        "price": tier_config["stripe_price_id"]
                    }],
                    proration_behavior="always_invoice"
                )
            else:
                # Create new subscription
                subscription = stripe.Subscription.create(
                    customer=user.stripe_customer_id,
                    items=[{
                        "price": tier_config["stripe_price_id"]
                    }],
                    expand=["latest_invoice.payment_intent"]
                )
            
            # Update user's subscription in database
            user.subscription_tier = tier
            user.subscription_status = subscription.status
            user.subscription_id = subscription.id
            user.subscription_end_date = datetime.fromtimestamp(
                subscription.current_period_end
            )
            self.db.commit()
            
            return {
                "subscription_id": subscription.id,
                "status": subscription.status,
                "tier": tier,
                "current_period_end": subscription.current_period_end,
                "client_secret": subscription.latest_invoice.payment_intent.client_secret
                if hasattr(subscription.latest_invoice, 'payment_intent') else None
            }
            
        except stripe.error.StripeError as e:
            logger.error(f"Stripe error creating subscription: {e}")
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Failed to create subscription: {str(e)}"
            )
    
    def cancel_subscription(self, user_id: int) -> Dict[str, Any]:
        """Cancel a user's subscription"""
        try:
            from src.database import User
            user = self.db.query(User).filter(User.id == user_id).first()
            
            if not user or not user.subscription_id:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="No active subscription found"
                )
            
            # Cancel at period end to allow usage until paid period ends
            subscription = stripe.Subscription.modify(
                user.subscription_id,
                cancel_at_period_end=True
            )
            
            user.subscription_status = "canceling"
            self.db.commit()
            
            return {
                "message": "Subscription will be canceled at period end",
                "cancel_at": subscription.cancel_at
            }
            
        except stripe.error.StripeError as e:
            logger.error(f"Stripe error canceling subscription: {e}")
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Failed to cancel subscription: {str(e)}"
            )
    
    def track_usage(
        self, 
        user_id: int, 
        event_type: str, 
        quantity: int = 1,
        metadata: Dict[str, Any] = None
    ) -> Dict[str, Any]:
        """Track usage for billing purposes"""
        
        if event_type not in USAGE_PRICING:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Invalid usage event type: {event_type}"
            )
        
        try:
            from src.database import User, UsageEvent
            
            user = self.db.query(User).filter(User.id == user_id).first()
            if not user:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="User not found"
                )
            
            # Create usage event record
            usage_event = UsageEvent(
                user_id=user_id,
                event_type=event_type,
                quantity=quantity,
                unit_price=float(USAGE_PRICING[event_type]),
                total_price=float(USAGE_PRICING[event_type] * quantity),
                event_metadata=metadata or {},
                created_at=datetime.utcnow()
            )
            self.db.add(usage_event)
            
            # Update user's usage metrics
            if event_type == "api_call":
                user.api_calls_this_month = (user.api_calls_this_month or 0) + quantity
            elif event_type == "ai_analysis":
                user.ai_analyses_this_month = (user.ai_analyses_this_month or 0) + quantity
            
            # Check if user exceeded limits
            tier_config = PRICING_TIERS.get(user.subscription_tier, PRICING_TIERS["free"])
            api_limit = tier_config["api_calls"]
            
            if api_limit != -1 and user.api_calls_this_month > api_limit:
                # Create usage record in Stripe for overage
                if user.stripe_customer_id and user.subscription_tier != "free":
                    overage = user.api_calls_this_month - api_limit
                    stripe.UsageRecord.create(
                        subscription_item=user.subscription_item_id,
                        quantity=overage,
                        timestamp=int(datetime.utcnow().timestamp())
                    )
            
            self.db.commit()
            
            return {
                "event_id": usage_event.id,
                "event_type": event_type,
                "quantity": quantity,
                "cost": usage_event.total_price,
                "usage_this_month": {
                    "api_calls": user.api_calls_this_month,
                    "ai_analyses": user.ai_analyses_this_month
                }
            }
            
        except Exception as e:
            logger.error(f"Error tracking usage: {e}")
            self.db.rollback()
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed to track usage: {str(e)}"
            )
    
    def get_billing_info(self, user_id: int) -> Dict[str, Any]:
        """Get billing information for a user"""
        try:
            from src.database import User, UsageEvent
            
            user = self.db.query(User).filter(User.id == user_id).first()
            if not user:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="User not found"
                )
            
            # Get current month usage
            start_of_month = datetime.now().replace(day=1, hour=0, minute=0, second=0)
            
            usage_events = self.db.query(UsageEvent).filter(
                UsageEvent.user_id == user_id,
                UsageEvent.created_at >= start_of_month
            ).all()
            
            total_cost = sum(event.total_price for event in usage_events)
            
            # Get tier configuration
            tier_config = PRICING_TIERS.get(user.subscription_tier, PRICING_TIERS["free"])
            
            # Get payment methods if Stripe customer
            payment_methods = []
            if user.stripe_customer_id:
                try:
                    methods = stripe.PaymentMethod.list(
                        customer=user.stripe_customer_id,
                        type="card"
                    )
                    payment_methods = [
                        {
                            "id": method.id,
                            "brand": method.card.brand,
                            "last4": method.card.last4,
                            "exp_month": method.card.exp_month,
                            "exp_year": method.card.exp_year
                        }
                        for method in methods.data
                    ]
                except:
                    pass
            
            # Get invoices
            invoices = []
            if user.stripe_customer_id:
                try:
                    stripe_invoices = stripe.Invoice.list(
                        customer=user.stripe_customer_id,
                        limit=10
                    )
                    invoices = [
                        {
                            "id": invoice.id,
                            "number": invoice.number,
                            "amount": invoice.amount_paid / 100,
                            "status": invoice.status,
                            "date": datetime.fromtimestamp(invoice.created).isoformat(),
                            "pdf_url": invoice.invoice_pdf
                        }
                        for invoice in stripe_invoices.data
                    ]
                except:
                    pass
            
            return {
                "subscription": {
                    "tier": user.subscription_tier,
                    "status": user.subscription_status,
                    "price": tier_config["price"],
                    "end_date": user.subscription_end_date.isoformat() if user.subscription_end_date else None
                },
                "limits": {
                    "api_calls": tier_config["api_calls"],
                    "projects": tier_config["projects"],
                    "team_members": tier_config["team_members"]
                },
                "usage": {
                    "api_calls": user.api_calls_this_month or 0,
                    "ai_analyses": user.ai_analyses_this_month or 0,
                    "total_cost": total_cost
                },
                "payment_methods": payment_methods,
                "invoices": invoices,
                "features": tier_config["features"]
            }
            
        except Exception as e:
            logger.error(f"Error getting billing info: {e}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed to get billing information: {str(e)}"
            )
    
    def _set_free_tier(self, user_id: int) -> Dict[str, Any]:
        """Set user to free tier"""
        from src.database import User
        
        user = self.db.query(User).filter(User.id == user_id).first()
        if user:
            user.subscription_tier = "free"
            user.subscription_status = "active"
            user.subscription_id = None
            user.subscription_end_date = None
            self.db.commit()
        
        return {
            "tier": "free",
            "status": "active",
            "message": "Successfully switched to free tier"
        }
    
    def process_webhook(self, payload: bytes, signature: str) -> Dict[str, Any]:
        """Process Stripe webhook events"""
        try:
            event = stripe.Webhook.construct_event(
                payload, signature, STRIPE_WEBHOOK_SECRET
            )
            
            # Handle different event types
            if event.type == "invoice.payment_succeeded":
                # Payment successful, update user status
                self._handle_payment_success(event.data.object)
                
            elif event.type == "invoice.payment_failed":
                # Payment failed, notify user
                self._handle_payment_failure(event.data.object)
                
            elif event.type == "customer.subscription.deleted":
                # Subscription canceled, downgrade to free
                self._handle_subscription_deleted(event.data.object)
                
            elif event.type == "customer.subscription.updated":
                # Subscription updated
                self._handle_subscription_updated(event.data.object)
            
            return {"status": "success", "event": event.type}
            
        except stripe.error.SignatureVerificationError:
            logger.error("Invalid webhook signature")
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid webhook signature"
            )
        except Exception as e:
            logger.error(f"Webhook processing error: {e}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Webhook processing failed: {str(e)}"
            )
    
    def _handle_payment_success(self, invoice):
        """Handle successful payment"""
        from src.database import User
        
        customer_id = invoice.customer
        user = self.db.query(User).filter(
            User.stripe_customer_id == customer_id
        ).first()
        
        if user:
            user.subscription_status = "active"
            self.db.commit()
            logger.info(f"Payment successful for user {user.id}")
    
    def _handle_payment_failure(self, invoice):
        """Handle failed payment"""
        from src.database import User
        
        customer_id = invoice.customer
        user = self.db.query(User).filter(
            User.stripe_customer_id == customer_id
        ).first()
        
        if user:
            user.subscription_status = "past_due"
            self.db.commit()
            
            # TODO: Send email notification
            logger.warning(f"Payment failed for user {user.id}")
    
    def _handle_subscription_deleted(self, subscription):
        """Handle subscription deletion"""
        from src.database import User
        
        customer_id = subscription.customer
        user = self.db.query(User).filter(
            User.stripe_customer_id == customer_id
        ).first()
        
        if user:
            user.subscription_tier = "free"
            user.subscription_status = "canceled"
            user.subscription_id = None
            user.subscription_end_date = None
            self.db.commit()
            logger.info(f"Subscription canceled for user {user.id}")
    
    def _handle_subscription_updated(self, subscription):
        """Handle subscription update"""
        from src.database import User
        
        customer_id = subscription.customer
        user = self.db.query(User).filter(
            User.stripe_customer_id == customer_id
        ).first()
        
        if user:
            # Map price ID to tier
            price_id = subscription.items.data[0].price.id
            tier = None
            for tier_name, config in PRICING_TIERS.items():
                if config.get("stripe_price_id") == price_id:
                    tier = tier_name
                    break
            
            if tier:
                user.subscription_tier = tier
                user.subscription_status = subscription.status
                user.subscription_end_date = datetime.fromtimestamp(
                    subscription.current_period_end
                )
                self.db.commit()
                logger.info(f"Subscription updated for user {user.id} to tier {tier}")


# Export models for FastAPI
class BillingInfoResponse(BaseModel):
    subscription: Dict[str, Any]
    limits: Dict[str, Any]
    usage: Dict[str, Any]
    payment_methods: List[Dict[str, Any]]
    invoices: List[Dict[str, Any]]
    features: List[str]


class SubscriptionResponse(BaseModel):
    subscription_id: Optional[str]
    tier: str
    status: str
    current_period_end: Optional[int]
    client_secret: Optional[str]
    message: Optional[str]


class UsageResponse(BaseModel):
    event_id: int
    event_type: str
    quantity: int
    cost: float
    usage_this_month: Dict[str, int]