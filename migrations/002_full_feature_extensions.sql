-- Additional safe extensions for the full custom backend.
-- Apply after 001_extend_schema.sql.

ALTER TABLE users ADD COLUMN IF NOT EXISTS marketing_opt_in BOOLEAN NOT NULL DEFAULT FALSE;

ALTER TABLE addresses ADD COLUMN IF NOT EXISTS label VARCHAR(100);
ALTER TABLE addresses ADD COLUMN IF NOT EXISTS delivery_notes TEXT;

CREATE TABLE IF NOT EXISTS password_reset_tokens (
    id BIGSERIAL PRIMARY KEY,
    user_id BIGINT NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    token_hash VARCHAR(255) NOT NULL UNIQUE,
    expires_at TIMESTAMPTZ NOT NULL,
    used_at TIMESTAMPTZ,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

ALTER TABLE products ADD COLUMN IF NOT EXISTS stock_quantity INTEGER NOT NULL DEFAULT 0;

CREATE TABLE IF NOT EXISTS product_meta (
    product_id INTEGER PRIMARY KEY REFERENCES products(id) ON DELETE CASCADE,
    slug VARCHAR(255) NOT NULL UNIQUE,
    short_description TEXT,
    is_enabled BOOLEAN NOT NULL DEFAULT TRUE,
    is_featured BOOLEAN NOT NULL DEFAULT FALSE,
    meta_title VARCHAR(255),
    meta_description TEXT,
    sort_order INTEGER NOT NULL DEFAULT 0,
    popularity_score INTEGER NOT NULL DEFAULT 0,
    low_stock_threshold INTEGER NOT NULL DEFAULT 5,
    size_guide TEXT,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS product_categories (
    product_id INTEGER NOT NULL REFERENCES products(id) ON DELETE CASCADE,
    category_id INTEGER NOT NULL REFERENCES categories(id) ON DELETE CASCADE,
    PRIMARY KEY (product_id, category_id)
);

ALTER TABLE carts ADD COLUMN IF NOT EXISTS guest_email VARCHAR(255);

ALTER TABLE coupons ADD COLUMN IF NOT EXISTS description TEXT;
ALTER TABLE coupons ADD COLUMN IF NOT EXISTS starts_at TIMESTAMPTZ;
ALTER TABLE coupons ADD COLUMN IF NOT EXISTS min_order_amount NUMERIC(12,2);
ALTER TABLE coupons ADD COLUMN IF NOT EXISTS applies_to_all_products BOOLEAN NOT NULL DEFAULT TRUE;

ALTER TABLE orders ADD COLUMN IF NOT EXISTS payment_method VARCHAR(50);
ALTER TABLE orders ADD COLUMN IF NOT EXISTS refunded_amount NUMERIC(12,2) NOT NULL DEFAULT 0;

ALTER TABLE product_reviews ADD COLUMN IF NOT EXISTS is_spam BOOLEAN NOT NULL DEFAULT FALSE;

CREATE TABLE IF NOT EXISTS shipping_methods (
    id BIGSERIAL PRIMARY KEY,
    code VARCHAR(50) NOT NULL UNIQUE,
    name VARCHAR(150) NOT NULL,
    description TEXT,
    base_rate NUMERIC(12,2) NOT NULL DEFAULT 0,
    estimated_days INTEGER,
    is_enabled BOOLEAN NOT NULL DEFAULT TRUE,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS shipping_rate_rules (
    id BIGSERIAL PRIMARY KEY,
    shipping_method_id BIGINT NOT NULL REFERENCES shipping_methods(id) ON DELETE CASCADE,
    country_code CHAR(2),
    state VARCHAR(120),
    zip_prefix VARCHAR(20),
    min_order_amount NUMERIC(12,2),
    extra_charge NUMERIC(12,2) NOT NULL DEFAULT 0,
    is_active BOOLEAN NOT NULL DEFAULT TRUE,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS tax_rules (
    id BIGSERIAL PRIMARY KEY,
    country_code CHAR(2) NOT NULL DEFAULT 'US',
    state VARCHAR(120),
    zip_prefix VARCHAR(20),
    rate_percent NUMERIC(5,2) NOT NULL DEFAULT 0,
    is_active BOOLEAN NOT NULL DEFAULT TRUE,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    CONSTRAINT uq_tax_rules_scope UNIQUE (country_code, state, zip_prefix)
);

CREATE TABLE IF NOT EXISTS inventory_movements (
    id BIGSERIAL PRIMARY KEY,
    product_id INTEGER NOT NULL REFERENCES products(id) ON DELETE CASCADE,
    variant_id BIGINT REFERENCES product_variants(id) ON DELETE SET NULL,
    warehouse_name VARCHAR(120),
    movement_type VARCHAR(30) NOT NULL,
    quantity_delta INTEGER NOT NULL,
    balance_after INTEGER,
    reason TEXT,
    created_by_user_id BIGINT REFERENCES users(id) ON DELETE SET NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS redirect_rules (
    id BIGSERIAL PRIMARY KEY,
    source_path VARCHAR(255) NOT NULL UNIQUE,
    target_path VARCHAR(255) NOT NULL,
    status_code INTEGER NOT NULL DEFAULT 301,
    is_active BOOLEAN NOT NULL DEFAULT TRUE,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS ix_products_stock_quantity ON products(stock_quantity);
CREATE INDEX IF NOT EXISTS ix_product_meta_slug ON product_meta(slug);
CREATE INDEX IF NOT EXISTS ix_shipping_methods_code ON shipping_methods(code);
CREATE INDEX IF NOT EXISTS ix_redirect_rules_source_path ON redirect_rules(source_path);
