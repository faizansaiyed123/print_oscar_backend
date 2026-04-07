-- Migration to make product customization rules dynamic.
-- Removes the hardcoded field_type constraint and adds validation_rules JSONB column.

-- 1. Remove the existing check constraint
ALTER TABLE product_customization_rules DROP CONSTRAINT IF EXISTS ck_customization_field_type;

-- 2. Add the validation_rules column
ALTER TABLE product_customization_rules ADD COLUMN IF NOT EXISTS validation_rules JSONB;

-- 3. (Optional) Update existing records if needed (not required here as it defaults to NULL)

-- 4. Add index for performance on product_id if not already there (it should be there from REFERENCES but good to be sure)
CREATE INDEX IF NOT EXISTS ix_product_customization_rules_product_id ON product_customization_rules(product_id);
