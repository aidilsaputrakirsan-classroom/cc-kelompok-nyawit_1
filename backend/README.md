# Backend - FastAPI Application

## 📁 Folder Structure

```
backend/
├── app/                    # Main application code
│   ├── core/              # Core configurations, security, dependencies
│   │   ├── config.py      # Application settings and configuration
│   │   ├── deps.py        # Dependency injection functions
│   │   └── security.py    # Authentication and authorization logic
│   ├── db/                # Database configuration
│   │   ├── base.py        # SQLAlchemy base classes
│   │   └── session.py     # Database session management
│   ├── models/            # SQLAlchemy ORM models
│   │   ├── user.py        # User model
│   │   ├── purchase_requisition.py
│   │   ├── purchase_order.py
│   │   ├── grn_document.py
│   │   ├── pr_line_item.py
│   │   ├── token_blacklist.py
│   │   └── enums.py       # Enum definitions
│   ├── routers/           # API route handlers
│   │   ├── auth.py        # Authentication endpoints
│   │   ├── requisitions.py       # Purchase requisition endpoints (user)
│   │   ├── requisitions_admin.py # Purchase requisition endpoints (admin)
│   │   ├── purchase_orders.py    # Purchase order endpoints
│   │   ├── grn.py         # GRN endpoints (user)
│   │   └── grn_admin.py   # GRN endpoints (admin)
│   ├── schemas/           # Pydantic schemas for request/response validation
│   │   ├── auth.py
│   │   ├── user.py
│   │   ├── purchase_requisition.py
│   │   ├── purchase_order.py
│   │   ├── grn_document.py
│   │   ├── pr_line_item.py
│   │   └── common.py      # Common response schemas
│   ├── utils/             # Utility functions
│   ├── main.py            # FastAPI application entry point
│   └── seed.py            # Database seeding script
├── tests/                 # Test files
│   ├── conftest.py        # pytest fixtures and configuration
│   ├── test_auth.py       # Authentication tests
│   ├── test_health.py     # Health check tests
│   └── test_requisitions.py # Requisition tests
├── alembic/               # Database migration files
│   ├── versions/          # Migration scripts
│   ├── env.py             # Alembic environment configuration
│   └── script.py.mako     # Migration template
├── uploads/               # User-uploaded files (not tracked by git)
├── .env.example           # Environment variable template
├── .gitignore            # Git ignore rules for backend
├── Dockerfile             # Docker build configuration
├── requirements.txt       # Python dependencies
├── alembic.ini           # Alembic configuration
├── pytest.ini            # pytest configuration
└── main.py               # Convenience wrapper (imports from app/main)
```

## 🚀 Quick Start

### Local Development

1. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

2. **Set up environment variables:**
   ```bash
   cp .env.example .env.local
   # Edit .env.local with your configuration
   ```

3. **Run database migrations:**
   ```bash
   alembic upgrade head
   ```

4. **Seed the database (optional):**
   ```bash
   python app/seed.py
   ```

5. **Start the development server:**
   ```bash
   uvicorn app.main:app --reload
   ```

### Running Tests

```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=app --cov-report=html

# Run specific test file
pytest tests/test_auth.py
```

### Database Migrations

```bash
# Create a new migration
alembic revision --autogenerate -m "Description of changes"

# Apply migrations
alembic upgrade head

# Rollback one migration
alembic downgrade -1
```

## 📋 Key Technologies

- **FastAPI**: Modern, fast web framework for building APIs
- **SQLAlchemy**: SQL toolkit and ORM
- **Alembic**: Database migration tool
- **Pydantic**: Data validation using Python type annotations
- **JWT**: JSON Web Tokens for authentication
- **PostgreSQL**: Primary database (configured via environment variables)

## 🔐 Security Notes

- Never commit `.env.local` or any file containing secrets
- All sensitive data should be stored in environment variables
- Passwords are hashed using bcrypt
- JWT tokens are used for authentication with blacklist support

## 📝 Code Conventions

- Follow PEP 8 style guide
- Use type hints for all function parameters and return values
- Write docstrings for all public functions and classes
- Keep business logic in services, not in routers
- Use dependency injection for database sessions and authentication

## 🧪 Testing Guidelines

- Write tests for all new features
- Maintain test coverage above 80%
- Use fixtures from `conftest.py` for common test setup
- Mock external services and database calls where appropriate
