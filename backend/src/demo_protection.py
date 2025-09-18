"""
Demo Account Protection
Ensures demo accounts cannot make real payments
"""

from typing import Optional
from fastapi import HTTPException, status

# List of demo account emails that should be protected
DEMO_ACCOUNTS = [
    "demo@streamapi.dev",
    "test@streamapi.dev",
    "demo@example.com",
    "test@example.com",
    "demo@api-orchestrator.com"
]

def is_demo_account(email: str) -> bool:
    """Check if an email belongs to a demo account"""
    if not email:
        return False

    email_lower = email.lower()

    # Check exact matches
    if email_lower in [demo.lower() for demo in DEMO_ACCOUNTS]:
        return True

    # Check patterns
    demo_patterns = ["demo", "test", "trial", "sample", "example"]
    for pattern in demo_patterns:
        if pattern in email_lower:
            return True

    return False

def protect_demo_account(email: str, operation: str = "payment") -> None:
    """
    Raise an exception if a demo account tries to perform a protected operation

    Args:
        email: User email to check
        operation: The operation being attempted (payment, subscription, etc.)

    Raises:
        HTTPException: If the account is a demo account
    """
    if is_demo_account(email):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=f"Demo accounts cannot perform {operation} operations. "
                   f"This is a demo account for testing purposes only. "
                   f"To upgrade, please create a real account."
        )

def get_demo_tier_limit(email: str) -> Optional[str]:
    """
    Get the maximum tier allowed for a demo account

    Args:
        email: User email to check

    Returns:
        Maximum tier name or None if not a demo account
    """
    if is_demo_account(email):
        # Demo accounts can only use free or professional tier without payment
        return "professional"
    return None

def validate_demo_subscription(email: str, tier: str, payment_required: bool = False) -> dict:
    """
    Validate if a demo account can use the requested subscription tier

    Args:
        email: User email
        tier: Requested subscription tier
        payment_required: Whether payment is required for this operation

    Returns:
        Validation result with status and message
    """
    if not is_demo_account(email):
        return {
            "is_demo": False,
            "allowed": True,
            "message": "Regular account - all operations allowed"
        }

    # Demo account detected
    if payment_required:
        return {
            "is_demo": True,
            "allowed": False,
            "message": "Demo accounts cannot make payments. All features are already unlocked for testing.",
            "suggestion": "Use the demo account to test all features without payment."
        }

    # Check tier limits for demo accounts
    allowed_tiers = ["free", "starter", "professional"]
    if tier.lower() in allowed_tiers:
        return {
            "is_demo": True,
            "allowed": True,
            "message": f"Demo account granted {tier} tier features for testing",
            "note": "No payment required for demo accounts"
        }

    # Enterprise tier not allowed for demo
    if tier.lower() == "enterprise":
        return {
            "is_demo": True,
            "allowed": False,
            "message": "Demo accounts cannot access enterprise tier",
            "suggestion": "Create a real account and contact sales for enterprise access"
        }

    return {
        "is_demo": True,
        "allowed": False,
        "message": f"Invalid tier '{tier}' for demo account"
    }