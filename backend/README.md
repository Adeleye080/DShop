# E-commerce Backend API

A production-ready, modular FastAPI backend for e-commerce applications, featuring robust authentication, payments, inventory, and admin management.

## Features

- User registration, login, JWT auth, email verification, password reset
- Password strength validation, rate limiting, CSRF protection, 2FA (TOTP)
- Role-based access (user/admin), soft deletes, audit logging
- Product CRUD, image upload, inventory management
- Cart and order management, order status tracking
- User address management
- Stripe and PayPal payments (with webhook signature verification)
- Email notifications (order confirmation, payment receipt, status updates)
- Admin dashboard endpoints (users, products, orders, payments overview)
- CORS, health check, global error handling, structured logging

## Project Structure

```
ecommerce-backend/
  api/           # Routers for auth, products, cart, orders, payments, admin, address
  core/          # Shared logic: database, security, logging, email_utils
  models/        # SQLAlchemy models
  schemas/       # Pydantic schemas
  templates/     # HTML email templates
  static/images/ # Product images
  main.py        # FastAPI app entrypoint
  requirements.txt
  README.md
```

## Setup

1. **Clone the repo:**
   ```bash
   git clone <repo-url>
   cd ecommerce-backend
   ```
2. **Create and activate a virtual environment:**
   ```bash
   python -m venv venv
   source venv/bin/activate  # or venv\Scripts\activate on Windows
   ```
3. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
   ```
4. **Configure environment variables:**
   - Copy `.env.example` to `.env` and fill in your secrets (DB, SMTP, Stripe, PayPal, etc.)
5. **Run the app:**
   ```bash
   uvicorn main:app --reload
   ```

## Environment Variables

See `.env.example` for all required variables, including:

- `DATABASE_URL`
- `SMTP_SERVER`, `SMTP_PORT`, `SMTP_USER`, `SMTP_PASSWORD`
- `STRIPE_SECRET_KEY`, `STRIPE_WEBHOOK_SECRET`
- `PAYPAL_CLIENT_ID`, `PAYPAL_CLIENT_SECRET`, `PAYPAL_WEBHOOK_ID`
- `SECRET_KEY` (for JWT)

## API Usage

- Interactive docs: [http://localhost:8000/docs](http://localhost:8000/docs)
- All endpoints are prefixed (e.g., `/auth/`, `/products/`, `/orders/`, `/payments/`, `/admin/`)
- Admin endpoints require an admin JWT

## Email & Payments

- Email sending uses SMTP (Gmail, Mailtrap, etc.)
- Stripe/PayPal webhooks require public endpoints (use ngrok for local dev)
- Email templates in `templates/` are rendered with Jinja2

## Testing & Deployment

- Use Alembic for DB migrations
- Add tests for endpoints and business logic
- For production: set CORS, use HTTPS, configure logging, and secure secrets

## License

MIT
