# FinSight — Budget Planner with Savings Goals

A production-ready personal finance desktop application with a full-stack architecture.

## Architecture

```
┌──────────────────────────────────────────────────┐
│              CustomTkinter GUI                    │
│  (Dashboard · Add TX · Goals · Budget · Insights) │
└───────────────────────┬──────────────────────────┘
                        │ HTTP (httpx)
                        ▼
┌──────────────────────────────────────────────────┐
│              FastAPI REST API                      │
│         JWT Auth · CORS · Rate Limiting           │
├──────────────────────────────────────────────────┤
│                 Service Layer                      │
│  Auth · Transaction · Goal · Budget · Analytics   │
├──────────────────────────────────────────────────┤
│               Repository Layer                     │
│  UserRepo · TxRepo · GoalRepo · BudgetRepo        │
├──────────────────────────────────────────────────┤
│              Database Layer (MySQL)                │
│  7 tables · Indexes · Foreign Keys · Constraints  │
└──────────────────────────────────────────────────┘
```

The GUI never accesses MySQL directly. All database operations go through the REST API.

## Features

- **Dashboard**: Income/expense summary, pie charts, trend charts, transaction list with edit/delete
- **Transactions**: Add income/expense with categories, currencies (INR/USD/NPR), recurring support, receipt attachments
- **Goals**: Create savings goals with progress tracking, auto-fund, confetti on completion
- **Budgets**: Monthly per-category limits with color-coded progress bars and smart tips
- **AI Insights**: Spending prediction (Linear Regression), behavior clustering (K-Means), category suggester (Logistic Regression), personalized tips
- **Reports**: PDF report generation
- **Auth**: JWT-based authentication with bcrypt password hashing

## Tech Stack

| Layer | Technology |
|-------|-----------|
| GUI | CustomTkinter |
| API | FastAPI (Python 3.13) |
| Database | MySQL 8.0 |
| Auth | JWT + bcrypt |
| ML | scikit-learn (LinearRegression, LogisticRegression, KMeans) |
| PDF | ReportLab |
| Testing | Pytest + FastAPI TestClient |
| CI/CD | GitHub Actions |
| Container | Docker / docker-compose |

## Quick Start

### Prerequisites

- Python 3.13+
- MySQL 8.0
- uv (package manager) or pip

### 1. Environment Setup

```bash
# Clone the repo
git clone <repo-url>
cd finsight

# Copy .env.example to .env and edit with your credentials
cp .env.example .env
```

### 2. Database Setup

```bash
# Create the database
mysql -u root -p < database/schema.sql
mysql -u root -p < database/migration_v2.sql
mysql -u root -p < database/migration_v3.sql
mysql -u root -p < database/migration_v4.sql
mysql -u root -p < database/migration_v5.sql

# (Optional) Seed demo data
uv run python scripts/seed_demo.py
```

### 3. Install & Run

```bash
# Install dependencies
uv sync

# Start the API server
uv run uvicorn api.main:app --reload

# In another terminal, start the GUI
uv run python main.py
```

### Docker Setup

```bash
docker-compose up --build
```

## API Endpoints

### Authentication
| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/auth/register` | Register a new user |
| POST | `/auth/login` | Login, returns JWT token |
| GET | `/auth/me` | Get current user profile |

### Transactions
| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/transactions` | List transactions (paginated, filterable) |
| GET | `/transactions/{id}` | Get single transaction |
| POST | `/transactions` | Create transaction |
| PUT | `/transactions/{id}` | Update transaction |
| DELETE | `/transactions/{id}` | Delete (soft by default) |
| POST | `/transactions/{id}/restore` | Restore soft-deleted |
| GET | `/transactions/deleted/recent` | Recently deleted |

### Categories
| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/categories` | List categories (optional type filter) |

### Goals
| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/goals` | List savings goals |
| POST | `/goals` | Create goal |
| POST | `/goals/{id}/fund` | Add funds to goal |
| POST | `/goals/{id}/complete` | Complete goal |
| POST | `/goals/{id}/cancel` | Cancel goal |

### Budgets
| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/budgets` | List budget limits |
| POST | `/budgets` | Set budget limit |
| PUT | `/budgets/{id}` | Update budget limit |
| DELETE | `/budgets/{id}` | Delete budget limit |
| GET | `/budgets/utilization` | Budget utilization for month |

### Analytics
| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/dashboard` | Full dashboard summary |
| GET | `/analytics/trends` | Monthly income/expense trends |
| GET | `/analytics/summary` | Period summary |

### Insights
| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/insights/predict` | Spending prediction |
| GET | `/insights/suggest-category` | AI category suggester |
| GET | `/insights/cluster` | Spending behavior clusters |

### Other
| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/report/generate` | Generate PDF report |
| GET | `/health` | Health check |
| GET | `/docs` | Swagger UI docs |
| GET | `/redoc` | ReDoc docs |

## Project Structure

```
finsight/
├── api/
│   ├── __init__.py
│   └── main.py              # FastAPI routes
├── api_client/
│   ├── __init__.py
│   └── client.py            # HTTP client for GUI
├── database/
│   ├── schema.sql           # Base schema
│   ├── migration_v2.sql     # Currency columns
│   ├── migration_v3.sql     # Budgets, recurring, receipts
│   ├── migration_v4.sql     # Soft-delete, splits, bills
│   └── migration_v5.sql     # Indexes, constraints
├── repositories/
│   ├── __init__.py
│   ├── base.py              # Base repository
│   ├── user_repository.py
│   ├── transaction_repository.py
│   ├── goal_repository.py
│   ├── budget_repository.py
│   └── category_repository.py
├── services/
│   ├── __init__.py
│   ├── auth_service.py       # JWT + bcrypt
│   ├── transaction_service.py
│   ├── goal_service.py
│   ├── budget_service.py
│   └── analytics_service.py
├── schemas/
│   ├── __init__.py
│   ├── auth.py               # Pydantic models
│   ├── transactions.py
│   ├── goals.py
│   ├── budgets.py
│   └── analytics.py
├── views/
│   ├── auth_view.py
│   ├── dashboard_view.py
│   ├── add_transaction_view.py
│   ├── goals_view.py
│   ├── budget_view.py
│   └── insights_view.py
├── utils/
│   ├── db_manager.py         # Legacy DB connector
│   ├── config_manager.py     # .env + credentials
│   ├── currency.py           # Conversion & formatting
│   ├── date_picker.py        # Calendar widget
│   ├── insights.py           # ML models
│   ├── recurring.py          # Auto-recurring processor
│   └── report_generator.py   # PDF + email
├── tests/
│   ├── conftest.py
│   ├── test_db_manager.py
│   ├── test_api.py
│   ├── test_currency.py
│   └── test_date_picker.py
├── scripts/
│   ├── seed_demo.py
│   ├── test_api.py
│   └── capture_screenshots.py
├── .github/workflows/
│   └── ci.yml                # CI/CD pipeline
├── main.py                   # GUI entry point
├── docker-compose.yml
├── Dockerfile.api
├── .env.example
└── pyproject.toml
```

## Testing

```bash
# Run all tests
pytest tests/ -v

# Run API tests (requires MySQL with FINSIGHT_DB_PASSWORD set)
pytest tests/test_api.py -v
```

## CI/CD

GitHub Actions runs on push to main/develop:
- **Lint**: ruff code quality checks
- **Test**: Database tests with MySQL service container
- **API Test**: Integration tests against live API

## Security

- JWT-based authentication (HS256)
- bcrypt password hashing
- Pydantic input validation on all endpoints
- CORS middleware configured
- SQL injection prevention via parameterized queries
- Environment-based secret management
- No hardcoded credentials
