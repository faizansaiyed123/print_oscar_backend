from datetime import datetime, timezone
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.catalog import Product, ProductCustomizationRule, Category, CategoryCustomizationRule

class CustomizationResolver:
    """
    Intelligently resolves customization rules for any product by traversing 
    the category hierarchy. Rules defined on parent categories automatically 
    flow down to sub-categories and products.
    """

    @staticmethod
    async def resolve_rules(product: Product, session: AsyncSession) -> list[ProductCustomizationRule]:
        # 1. Start with rules defined directly on the product
        resolved_rules = list(product.customization_rules)
        existing_labels = {rule.label.lower() for rule in resolved_rules}
        
        # 2. Traverse the Category Tree to find inherited rules
        # We start from the product's primary category
        current_category_id = product.category_id
        
        while current_category_id:
            # Fetch the current category with its rules and parent
            stmt = (
                select(Category)
                .options(
                    selectinload(Category.customization_rules),
                    selectinload(Category.parent)
                )
                .where(Category.id == current_category_id)
            )
            result = await session.execute(stmt)
            category = result.scalar_one_or_none()
            
            if not category:
                break
                
            # Add rules from this category if they haven't been shadowed by a child
            for rule in category.customization_rules:
                if rule.is_enabled and rule.label.lower() not in existing_labels:
                    # Convert CategoryCustomizationRule to a virtual ProductCustomizationRule
                    # using its database ID or a virtual one
                    resolved_rules.append(
                        ProductCustomizationRule(
                            id=rule.id,  # Use the category rule's ID
                            product_id=product.id,
                            field_type=rule.field_type,
                            label=rule.label,
                            is_required=rule.is_required,
                            max_file_size_mb=rule.max_file_size_mb,
                            allowed_file_types=rule.allowed_file_types,
                            help_text=rule.help_text,
                            validation_rules=rule.validation_rules,
                            is_enabled=True,
                            created_at=rule.created_at,
                            updated_at=rule.updated_at
                        )
                    )
                    existing_labels.add(rule.label.lower())
            
            # Move up to the parent category
            current_category_id = category.parent_id

        return resolved_rules
