# PrintOscar Backend 🏆

[![FastAPI](https://img.shields.io/badge/FastAPI-0.115-blue?logo=fastapi)](https://fastapi.tiangolo.com)
[![Python](https://img.shields.io/badge/Python-3.11-green?logo=python)](https://python.org)
[![PostgreSQL](https://img.shields.io/badge/PostgreSQL-green?logo=postgresql)](https://postgresql.org)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)
[![Payments](https://img.shields.io/badge/Payments-Stripe%20PayPal%20Adyen-orange?logo=stripe)](https://stripe.com)

Production-ready **FastAPI backend** for PrintOscar trophy/awards e-commerce store. Replaces WooCommerce while preserving existing PostgreSQL schema. Includes full admin panel, multi-gateway payments, intelligent routing, and enterprise features.

## ✨ Features

### Storefront
- 🔐 JWT Auth (register/login/refresh/guest sessions/forgot-password)
- 👥 User profiles, addresses, order history
- 🏷️ Category tree & product catalog (listing/filtering/details/reviews)
- 🛒 Advanced cart (items/save-for-later/coupons/shipping quotes/customization uploads)
- 💳 Checkout & orders (track/invoice/cancel)
- 📱 Responsive API design

### Admin Panel
- 📊 Dashboard & reports (sales/customers/products/inventory)
- 📦 Catalog CRUD (products/categories/pricing/stock)
- 📋 Orders mgmt (status/shipping/refunds)
- 👥 Customers mgmt (profiles/files)
- 🎛️ Inventory, shipping/tax rules
- 🖼️ Media library (upload/compress)
- ⚙️ Settings, banners, newsletter subscribers
- 📋 Audit logs, redirect rules

### Payments (Multi-Gateway)
- Stripe, PayPal, Adyen support
- Intelligent geography/load-based routing & failover
- PCI compliance, retries, webhooks, refunds/3DS
- 30+ currencies, fraud detection

### Architecture
- Repository/Service layers
- Async SQLAlchemy + Alembic migrations
- File uploads (local storage)
- Rate limiting, CORS, validation

```
Storefront API    Admin API
     ↓              ↓
API Routes ──> Repositories ──> PostgreSQL
     ↑              ↑
 Services (Payments, Orders, etc.)
```

## 🚀 Quickstart (Clone to Production)

```bash
# 1. Clone
git clone https://github.com/faizansaiyed123/print_oscar_backend.git
cd print_oscar_backend

# 2. Setup Python env (3.11+)
python -m venv .venv
source .venv/bin/activate  # Linux/Mac
# .venv\\Scripts\\activate  # Windows

# 3. Install deps
pip install -r requirements.txt

# 4. Copy & configure env
cp .env.example .env
# Edit .env: DATABASE_URL, SECRET_KEY, payment keys

# 5. Database setup (PostgreSQL required)
# Run manual schema extensions:
psql -d trophy_store -f migrations/001_extend_schema.sql
psql -d trophy_store -f migrations/002_full_feature_extensions.sql
psql -d trophy_store -f migrations/003_dynamic_customization.sql

# Alembic migrations
alembic upgrade head

# 6. Create admin & seed (optional)
python scripts/make_superadmin.py
python scripts/seed_test_data.py

# 7. Run dev server
scripts/run_dev.ps1  # Windows
# uvicorn app.main:app --reload --host 0.0.0.0 --port 8000  # Linux/Mac

# 8. API Docs: http://localhost:8000/docs
# Admin: http://localhost:8000/api/v1/admin/dashboard
```

✅ **Frontend ready**: Connect to `/api/v1` endpoints.

## 🛠️ Production Deployment

```yaml
# docker-compose.yml (add this file)
version: '3.8'
services:
  app:
    build: .
    ports: - '8000:8000'
    env_file: .env
    depends_on: [db, redis]
  db:
    image: postgres:15
    environment:
      POSTGRES_DB: trophy_store
      POSTGRES_USER: postgres
      POSTGRES_PASSWORD: root
  redis:
    image: redis:7
```

**Scaling**: Gunicorn/Uvicorn, Nginx reverse proxy (recommended).

## 📚 API Endpoints

See [docs/endpoint-map.md](docs/endpoint-map.md) & [docs/api_cheat_sheet.md](docs/api_cheat_sheet.md).

**Swagger**: `/docs` | **ReDoc**: `/redoc`

## 🤝 Contributing

See [CONTRIBUTING.md](CONTRIBUTING.md) for guidelines.

## 📄 License

MIT - See [LICENSE](LICENSE).

---

⭐ **Star on GitHub** | 🐦 **Follow @printoscar** | 💬 **Issues welcome**

