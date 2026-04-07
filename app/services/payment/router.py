"""Intelligent payment routing service."""

from datetime import datetime, timedelta
from decimal import Decimal
from typing import List, Optional, Tuple

from app.models.payment import PaymentGateway, PaymentGatewayConfig, PaymentMethod, PaymentRoutingRule
from app.services.payment.gateway import PaymentGateway


class PaymentRouter:
    """Intelligent payment routing with fallback and load balancing."""
    
    def __init__(self, gateways: dict[str, PaymentGateway]):
        self.gateways = gateways
        self._gateway_health_cache = {}
        self._health_cache_ttl = timedelta(minutes=5)
    
    async def select_gateway(
        self,
        amount: Decimal,
        currency_code: str,
        payment_method: PaymentMethod,
        country_code: str = "US",
        preferred_gateway: Optional[str] = None,
    ) -> Tuple[str, List[str]]:
        """
        Select the best gateway for a payment.
        
        Returns:
            Tuple of (primary_gateway, fallback_gateways)
        """
        # If preferred gateway is specified and healthy, use it
        if preferred_gateway and await self._is_gateway_healthy(preferred_gateway):
            gateway = self.gateways.get(preferred_gateway)
            if gateway and self._gateway_supports_requirements(
                gateway, amount, currency_code, payment_method
            ):
                return preferred_gateway, await self._get_fallback_gateways(
                    preferred_gateway, amount, currency_code, payment_method, country_code
                )
        
        # Find matching routing rules
        matching_rules = await self._find_matching_rules(
            amount, currency_code, payment_method, country_code
        )
        
        # Evaluate rules in priority order
        for rule in matching_rules:
            if await self._is_gateway_healthy(rule.primary_gateway):
                gateway = self.gateways.get(rule.primary_gateway)
                if gateway and self._gateway_supports_requirements(
                    gateway, amount, currency_code, payment_method
                ):
                    fallbacks = await self._get_fallback_gateways(
                        rule.primary_gateway, amount, currency_code, payment_method, country_code
                    )
                    return rule.primary_gateway, fallbacks
        
        # Fallback to any healthy gateway that supports requirements
        for gateway_name, gateway in self.gateways.items():
            if await self._is_gateway_healthy(gateway_name) and self._gateway_supports_requirements(
                gateway, amount, currency_code, payment_method
            ):
                fallbacks = await self._get_fallback_gateways(
                    gateway_name, amount, currency_code, payment_method, country_code
                )
                return gateway_name, fallbacks
        
        # No suitable gateway found
        raise ValueError("No suitable payment gateway available")
    
    async def _is_gateway_healthy(self, gateway_name: str) -> bool:
        """Check if a gateway is healthy (with caching)."""
        cache_key = f"health_{gateway_name}"
        now = datetime.utcnow()
        
        # Check cache
        if cache_key in self._gateway_health_cache:
            cached_time, is_healthy = self._gateway_health_cache[cache_key]
            if now - cached_time < self._health_cache_ttl:
                return is_healthy
        
        # Check actual health
        gateway = self.gateways.get(gateway_name)
        if not gateway:
            self._gateway_health_cache[cache_key] = (now, False)
            return False
        
        try:
            is_healthy = await gateway.health_check()
            self._gateway_health_cache[cache_key] = (now, is_healthy)
            return is_healthy
        except Exception:
            self._gateway_health_cache[cache_key] = (now, False)
            return False
    
    def _gateway_supports_requirements(
        self,
        gateway: PaymentGateway,
        amount: Decimal,
        currency_code: str,
        payment_method: PaymentMethod,
    ) -> bool:
        """Check if gateway supports the payment requirements."""
        supported_methods = gateway.get_supported_payment_methods()
        supported_currencies = gateway.get_supported_currencies()
        
        return (
            payment_method in supported_methods
            and currency_code in supported_currencies
        )
    
    async def _find_matching_rules(
        self,
        amount: Decimal,
        currency_code: str,
        payment_method: PaymentMethod,
        country_code: str,
    ) -> List[PaymentRoutingRule]:
        """Find routing rules that match the payment criteria."""
        # This would typically query the database
        # For now, return empty list - rules would be loaded from DB
        return []
    
    async def _get_fallback_gateways(
        self,
        primary_gateway: str,
        amount: Decimal,
        currency_code: str,
        payment_method: PaymentMethod,
        country_code: str,
    ) -> List[str]:
        """Get list of fallback gateways."""
        fallbacks = []
        
        for gateway_name, gateway in self.gateways.items():
            if gateway_name == primary_gateway:
                continue
            
            if (
                await self._is_gateway_healthy(gateway_name)
                and self._gateway_supports_requirements(
                    gateway, amount, currency_code, payment_method
                )
            ):
                fallbacks.append(gateway_name)
        
        return fallbacks
    
    async def get_gateway_metrics(self) -> dict[str, dict]:
        """Get metrics for all gateways."""
        metrics = {}
        
        for gateway_name, gateway in self.gateways.items():
            is_healthy = await self._is_gateway_healthy(gateway_name)
            
            metrics[gateway_name] = {
                "is_healthy": is_healthy,
                "supported_methods": [m.value for m in gateway.get_supported_payment_methods()],
                "supported_currencies": gateway.get_supported_currencies(),
                "test_mode": gateway.is_test_mode(),
            }
        
        return metrics
    
    def clear_health_cache(self):
        """Clear the health check cache."""
        self._gateway_health_cache.clear()


class LoadBalanceRouter(PaymentRouter):
    """Load balancing router with round-robin strategy."""
    
    def __init__(self, gateways: dict[str, PaymentGateway]):
        super().__init__(gateways)
        self._round_robin_counters = {}
    
    async def select_gateway(
        self,
        amount: Decimal,
        currency_code: str,
        payment_method: PaymentMethod,
        country_code: str = "US",
        preferred_gateway: Optional[str] = None,
    ) -> Tuple[str, List[str]]:
        """Select gateway using load balancing strategy."""
        if preferred_gateway:
            try:
                return await super().select_gateway(
                    amount, currency_code, payment_method, country_code, preferred_gateway
                )
            except ValueError:
                pass  # Fallback to load balancing
        
        # Find all healthy gateways that support requirements
        suitable_gateways = []
        for gateway_name, gateway in self.gateways.items():
            if (
                await self._is_gateway_healthy(gateway_name)
                and self._gateway_supports_requirements(
                    gateway, amount, currency_code, payment_method
                )
            ):
                suitable_gateways.append(gateway_name)
        
        if not suitable_gateways:
            raise ValueError("No suitable payment gateway available")
        
        # Use round-robin to select gateway
        selected_gateway = self._round_robin_select(suitable_gateways)
        fallbacks = [g for g in suitable_gateways if g != selected_gateway]
        
        return selected_gateway, fallbacks
    
    def _round_robin_select(self, gateways: List[str]) -> str:
        """Select gateway using round-robin algorithm."""
        # Sort to ensure consistent ordering
        sorted_gateways = sorted(gateways)
        
        # Get or initialize counter
        if "round_robin" not in self._round_robin_counters:
            self._round_robin_counters["round_robin"] = 0
        
        # Select gateway
        index = self._round_robin_counters["round_robin"] % len(sorted_gateways)
        selected = sorted_gateways[index]
        
        # Increment counter
        self._round_robin_counters["round_robin"] += 1
        
        return selected


class GeographyRouter(PaymentRouter):
    """Geography-based router for optimal regional performance."""
    
    def __init__(self, gateways: dict[str, PaymentGateway]):
        super().__init__(gateways)
        
        # Regional gateway preferences
        self._regional_preferences = {
            "US": ["stripe", "adyen", "paypal"],
            "EU": ["adyen", "stripe", "paypal"],
            "UK": ["stripe", "adyen", "paypal"],
            "CA": ["stripe", "adyen", "paypal"],
            "AU": ["stripe", "adyen", "paypal"],
            "JP": ["stripe", "adyen", "paypal"],
            "SG": ["stripe", "adyen", "paypal"],
        }
    
    async def select_gateway(
        self,
        amount: Decimal,
        currency_code: str,
        payment_method: PaymentMethod,
        country_code: str = "US",
        preferred_gateway: Optional[str] = None,
    ) -> Tuple[str, List[str]]:
        """Select gateway based on geography."""
        if preferred_gateway:
            try:
                return await super().select_gateway(
                    amount, currency_code, payment_method, country_code, preferred_gateway
                )
            except ValueError:
                pass  # Fallback to geography-based selection
        
        # Get regional preferences
        region = self._get_region(country_code)
        preferred_order = self._regional_preferences.get(region, list(self.gateways.keys()))
        
        # Find first suitable gateway
        for gateway_name in preferred_order:
            if gateway_name not in self.gateways:
                continue
            
            if (
                await self._is_gateway_healthy(gateway_name)
                and self._gateway_supports_requirements(
                    self.gateways[gateway_name], amount, currency_code, payment_method
                )
            ):
                fallbacks = await self._get_fallback_gateways(
                    gateway_name, amount, currency_code, payment_method, country_code
                )
                return gateway_name, fallbacks
        
        # Fallback to any suitable gateway
        return await super().select_gateway(
            amount, currency_code, payment_method, country_code
        )
    
    def _get_region(self, country_code: str) -> str:
        """Map country code to region."""
        regional_mapping = {
            "US": "US",
            "CA": "CA",
            "MX": "US",
            "GB": "UK",
            "IE": "UK",
            "FR": "EU",
            "DE": "EU",
            "IT": "EU",
            "ES": "EU",
            "NL": "EU",
            "BE": "EU",
            "AT": "EU",
            "SE": "EU",
            "DK": "EU",
            "NO": "EU",
            "FI": "EU",
            "PL": "EU",
            "CZ": "EU",
            "HU": "EU",
            "AU": "AU",
            "NZ": "AU",
            "JP": "JP",
            "SG": "SG",
            "HK": "SG",
        }
        
        return regional_mapping.get(country_code.upper(), "EU")
