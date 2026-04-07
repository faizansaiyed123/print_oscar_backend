#!/usr/bin/env python3
"""
Payment System Setup Script

This script helps set up the payment system for your trophy store.
It validates configuration, creates database tables, and initializes gateways.
"""

import asyncio
import sys
from pathlib import Path

# Add the project root to Python path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from app.core.payment_config import get_payment_settings, validate_payment_config
from app.core.database import get_db_session
from app.models.payment import PaymentGatewayConfig, PaymentRoutingRule
from app.services.payment.service import PaymentService


async def setup_payment_system():
    """Set up the payment system."""
    print("🚀 Setting up Payment System...")
    
    # 1. Validate configuration
    print("\n📋 Validating configuration...")
    config_validation = validate_payment_config()
    
    if not config_validation["valid"]:
        print("❌ Configuration validation failed:")
        for issue in config_validation["issues"]:
            print(f"  - {issue}")
        return False
    
    if config_validation["warnings"]:
        print("⚠️  Configuration warnings:")
        for warning in config_validation["warnings"]:
            print(f"  - {warning}")
    
    print("✅ Configuration validation passed")
    print(f"📊 Enabled gateways: {', '.join(config_validation['enabled_gateways'])}")
    
    # 2. Database setup
    print("\n🗄️  Setting up database...")
    try:
        async with get_db_session() as db:
            # Initialize payment service
            payment_service = PaymentService(db)
            await payment_service.initialize()
            
            print("✅ Payment service initialized")
            
            # Create default gateway configurations
            await create_default_gateway_configs(db, config_validation["enabled_gateways"])
            
            # Create default routing rules
            await create_default_routing_rules(db)
            
            print("✅ Database setup completed")
            
    except Exception as e:
        print(f"❌ Database setup failed: {str(e)}")
        return False
    
    # 3. Test gateway connectivity
    print("\n🔗 Testing gateway connectivity...")
    try:
        async with get_db_session() as db:
            payment_service = PaymentService(db)
            await payment_service.initialize()
            
            health_status = await payment_service._router.get_gateway_metrics()
            
            for gateway, metrics in health_status.items():
                status = "✅" if metrics["is_healthy"] else "❌"
                print(f"  {status} {gateway}: {'Healthy' if metrics['is_healthy'] else 'Unhealthy'}")
                
                if not metrics["is_healthy"]:
                    print(f"    Check your {gateway} configuration")
            
    except Exception as e:
        print(f"❌ Gateway connectivity test failed: {str(e)}")
        return False
    
    # 4. Display setup summary
    print("\n🎉 Payment System Setup Complete!")
    print("\n📝 Next Steps:")
    print("1. Update your .env file with actual gateway credentials")
    print("2. Test payment flows using test cards/methods")
    print("3. Set up webhook endpoints in your gateway dashboards")
    print("4. Configure monitoring and alerting")
    print("5. Run comprehensive tests before production deployment")
    
    print("\n📚 Documentation:")
    print("  - Full documentation: docs/payment_system.md")
    print("  - Environment example: .env.example.payment")
    print("  - API endpoints: /api/v1/payments")
    
    return True


async def create_default_gateway_configs(db, enabled_gateways):
    """Create default gateway configurations."""
    print("  📝 Creating gateway configurations...")
    
    for gateway_name in enabled_gateways:
        # Check if config already exists
        existing = await db.get(PaymentGatewayConfig, {"gateway": gateway_name})
        if existing:
            print(f"    ⏭️  {gateway_name} config already exists")
            continue
        
        config = PaymentGatewayConfig(
            gateway=gateway_name,
            is_active=True,
            is_test_mode=True,
            priority=1,
            config_data={
                "max_retries": 3,
                "timeout": 30,
            },
            max_requests_per_minute=100,
            is_healthy=True,
        )
        
        db.add(config)
        print(f"    ✅ Created {gateway_name} configuration")
    
    await db.commit()


async def create_default_routing_rules(db):
    """Create default routing rules."""
    print("  📝 Creating routing rules...")
    
    default_rules = [
        {
            "name": "US Customers - Stripe Priority",
            "currency_codes": ["USD"],
            "country_codes": ["US"],
            "primary_gateway": "stripe",
            "fallback_gateways": ["adyen", "paypal"],
            "routing_strategy": "priority",
        },
        {
            "name": "EU Customers - Adyen Priority", 
            "currency_codes": ["EUR", "GBP"],
            "country_codes": ["GB", "DE", "FR", "IT", "ES", "NL"],
            "primary_gateway": "adyen",
            "fallback_gateways": ["stripe", "paypal"],
            "routing_strategy": "priority",
        },
        {
            "name": "High Value - Load Balance",
            "amount_min": 1000.00,
            "primary_gateway": "stripe",
            "fallback_gateways": ["adyen"],
            "routing_strategy": "load_balance",
        },
    ]
    
    for rule_data in default_rules:
        # Check if rule already exists
        existing = await db.get(PaymentRoutingRule, {"name": rule_data["name"]})
        if existing:
            print(f"    ⏭️  Rule '{rule_data['name']}' already exists")
            continue
        
        rule = PaymentRoutingRule(
            name=rule_data["name"],
            is_active=True,
            priority=1,
            currency_codes=rule_data.get("currency_codes"),
            amount_min=rule_data.get("amount_min"),
            country_codes=rule_data.get("country_codes"),
            primary_gateway=rule_data["primary_gateway"],
            fallback_gateways=rule_data["fallback_gateways"],
            routing_strategy=rule_data["routing_strategy"],
        )
        
        db.add(rule)
        print(f"    ✅ Created rule '{rule_data['name']}'")
    
    await db.commit()


def print_test_cards():
    """Print test card information for development."""
    print("\n💳 Test Cards for Development:")
    print("\nStripe Test Cards:")
    print("  Card Number: 4242424242424242 (Visa)")
    print("  Card Number: 4000000000000002 (Card declined)")
    print("  Card Number: 4000000000009995 (Insufficient funds)")
    print("  Expiry: Any future date")
    print("  CVC: Any 3 digits")
    print("  ZIP: Any 5 digits")
    
    print("\nPayPal Sandbox:")
    print("  Use sandbox accounts at: https://developer.paypal.com/developer/accounts/")
    
    print("\nAdyen Test Cards:")
    print("  Card Number: 4111111111111111 (Visa)")
    print("  Card Number: 5555555555554444 (Mastercard)")
    print("  Expiry: 03/2030")
    print("  CVC: 737")


def main():
    """Main setup function."""
    try:
        success = asyncio.run(setup_payment_system())
        
        if success:
            print_test_cards()
            print("\n✨ Setup completed successfully!")
            sys.exit(0)
        else:
            print("\n❌ Setup failed. Please fix the issues above.")
            sys.exit(1)
            
    except KeyboardInterrupt:
        print("\n⏹️  Setup cancelled by user")
        sys.exit(1)
    except Exception as e:
        print(f"\n💥 Unexpected error: {str(e)}")
        sys.exit(1)


if __name__ == "__main__":
    main()
