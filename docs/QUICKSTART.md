# Quickstart Guide

## Local Development (5 mins)

1. **Prerequisites**: Python 3.11+, PostgreSQL 15+, Redis (optional)

2. **Clone & Env**
   ```
   git clone https://github.com/faizansaiyed123/print_oscar_backend
   cd print_oscar_backend
   cp .env.example .env
   # Edit .env
   ```

3. **Install**
   ```
   pip install -r requirements.txt
   ```

4. **Database**
   ```
   # Create DB
   createdb trophy_store
   
   # Schema extensions (REQUIRED)
   psql trophy_store < migrations/001_extend_schema.sql
   psql trophy_store < migrations/002_full_feature_extensions.sql
   psql trophy_store < migrations/003_dynamic_customization.sql
   
   # Alembic
   alembic upgrade head
   ```

5. **Seed & Admin**
   ```
   python scripts/make_superadmin.py  # Creates first admin
   python scripts/seed_test_data.py   # Sample products/customers
   ```

6. **Run**
   ```
   uvicorn app.main:app --reload
   # Open http://localhost:8000/docs
   ```

## Docker Production

```bash
docker-compose up -d
```

## Verification Checklist

- [ ] API docs load at `/docs`
- [ ] Admin dashboard at `/api/v1/admin/dashboard`
- [ ] Test login: `admin@printoscar.com` / `admin123`
- [ ] Products list: `GET /api/v1/products`
- [ ] Payment health: `GET /api/v1/payments/health` (admin token req'd)

## Troubleshooting

| Issue | Solution |
|-------|----------|
| DB connection | Check `DATABASE_URL` in `.env` |
| CORS errors | Update `BACKEND_CORS_ORIGINS` |
| Payment errors | Add test keys to `.env` |
| Migrations fail | Run manual SQL first, then Alembic |

Need help? [Open an issue](https://github.com/faizansaiyed123/print_oscar_backend/issues/new)
