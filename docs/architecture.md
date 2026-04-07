# Trophy Store Custom Backend

## Folder Structure

```text
trophy-store-backend/
  app/
    api/
      v1/
        routes/
    core/
    db/
    models/
    repositories/
    schemas/
    services/
    utils/
  alembic/
    versions/
  docs/
  migrations/
  scripts/
  storage/
  tests/
```

## Design Notes

- Existing `categories` and `products` tables are mapped as-is and never dropped or recreated.
- All new capabilities are implemented through extension tables and foreign keys.
- The API is split into storefront and admin concerns with repository and service layers between routes and SQLAlchemy.
- JWT auth uses access and refresh tokens with persisted refresh-token records for revocation support.
- File uploads are designed for local storage under `storage/` with metadata tracked in PostgreSQL.

## Primary Route Groups

- `/api/v1/auth`: register, login, refresh, forgot password
- `/api/v1/users`: profile and address management
- `/api/v1/categories`: category tree and storefront category listing
- `/api/v1/products`: product listing, details, filtering, reviews
- `/api/v1/cart`: carts, saved-for-later, checkout
- `/api/v1/orders`: customer order history and status tracking
- `/api/v1/admin`: dashboard, catalog ops, orders, customers, inventory, coupons, reviews, media, SEO, reports

## Enterprise Backlog Already Accounted For

- Roles and permissions
- Audit logging
- Coupon targeting
- Product customization rules
- Customer-uploaded files
- Inventory and low-stock reporting
- Campaigns, banners, newsletter subscribers
- Store-wide settings and SEO metadata
