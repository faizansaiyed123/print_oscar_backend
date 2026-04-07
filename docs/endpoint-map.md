# Endpoint Map

## Customer

- `POST /api/v1/auth/register`
- `POST /api/v1/auth/login`
- `POST /api/v1/auth/refresh`
- `POST /api/v1/auth/logout`
- `POST /api/v1/auth/forgot-password`
- `POST /api/v1/auth/reset-password`
- `POST /api/v1/auth/guest-session`
- `GET /api/v1/users/me`
- `PUT /api/v1/users/me`
- `GET /api/v1/users/me/addresses`
- `POST /api/v1/users/me/addresses`
- `PUT /api/v1/users/me/addresses/{address_id}`
- `DELETE /api/v1/users/me/addresses/{address_id}`
- `GET /api/v1/users/me/reviews`
- `GET /api/v1/categories`
- `GET /api/v1/categories/tree`
- `GET /api/v1/categories/{category_id}`
- `GET /api/v1/products`
- `GET /api/v1/products/slug/{slug}`
- `GET /api/v1/products/{product_id}`
- `GET /api/v1/products/{product_id}/reviews`
- `POST /api/v1/products/{product_id}/reviews`
- `POST /api/v1/cart`
- `GET /api/v1/cart/{cart_id}`
- `POST /api/v1/cart/{cart_id}/items`
- `PUT /api/v1/cart/{cart_id}/items/{item_id}`
- `DELETE /api/v1/cart/{cart_id}/items/{item_id}`
- `POST /api/v1/cart/{cart_id}/items/{item_id}/save-for-later`
- `GET /api/v1/cart/saved`
- `DELETE /api/v1/cart/saved/{item_id}`
- `POST /api/v1/cart/apply-coupon`
- `POST /api/v1/cart/shipping-quotes`
- `POST /api/v1/cart/uploads/customization`
- `POST /api/v1/cart/checkout`
- `GET /api/v1/orders`
- `GET /api/v1/orders/{order_id}`
- `POST /api/v1/orders/{order_id}/cancel`
- `GET /api/v1/orders/{order_id}/track`
- `GET /api/v1/orders/{order_id}/invoice`

## Admin

- Dashboard, activity logs, sales reports
- Customer growth and product performance report endpoints
- Category CRUD
- Product CRUD
- Bulk product import, price update, stock update, delete
- Review moderation
- Order listing, status updates, invoices, shipping labels
- Customer file listing, download, delete
- Customer management and email queueing
- Admin-triggered customer password reset
- Coupon CRUD
- Inventory adjustments and movement logs
- Shipping method and shipping rule CRUD
- Tax rule CRUD
- Media upload/list/delete/compress
- Role and admin-user management
- Store setting CRUD
- Banner and campaign CRUD plus campaign dispatch
- Newsletter subscriber management
- Redirect CRUD and sitemap generation
