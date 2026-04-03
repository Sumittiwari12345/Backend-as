#  Finance Data Processing & Access Control Backend

> A modern, production-ready REST API for managing financial data with intelligent role-based access control.

##  What You Get

This backend provides everything you need to build a finance dashboard system:

 **Financial Records Management** — Create, read, update, and delete financial transactions with smart filtering  
 **User & Role Management** — Manage team members with three distinct access levels  
 **Smart Access Control** — Viewer, Analyst, and Admin roles with enforced permissions  
 **Dashboard Analytics** — Real-time summaries and trends (monthly/weekly breakdowns)  
 **Secure Authentication** — JWT token-based login with password hashing  
 **Production Ready** — Built with FastAPI, SQLAlchemy, and SQLite



##  Tech Stack

| Component | Technology | Why? |
|-----------|-----------|------|
| **Language** | Python 3.13 | Modern, clean, type-safe |
| **Framework** | FastAPI | Lightning-fast, auto-docs, async-ready |
| **Database** | SQLite | Simple, portable, zero setup |
| **ORM** | SQLAlchemy 2.0 | Type-safe, powerful queries |
| **Auth** | PyJWT + PBKDF2 | Secure tokens, strong hashing |

---

##  Core Features

 **User Management**  
   - Create team members with specific roles  
   - Activate/deactivate accounts  
   - Change roles and permissions  

 **Financial Records**  
   - Log income and expense transactions  
   - Organize by category and date  
   - Add notes for context  
   - Never truly delete (soft delete keeps history)  

 **Smart Filtering**  
   - Filter by date range, category, amount, type  
   - Pagination support (perfect for large datasets)  
   - Case-insensitive searches  

 **Dashboard Analytics**  
   - Total income/expense and net balance  
   - Category-wise breakdown  
   - Recent activity feed  
   - Monthly/weekly trend analysis  

 **Role-Based Access**  
   - **Viewers** → Dashboard only  
   - **Analysts** → View & analyze records  
   - **Admins** → Full control

---

## User Roles & Permissions

### **Viewer**
Perfect for stakeholders who need to see the big picture:
-  View dashboard summary and trends
-  Cannot create, edit, or delete records
-  Ideal for executives and report viewers

###  **Analyst**
For team members who need to analyze data:
-  View and analyze all financial records
-  Access dashboard and trends
-  Filter and search records
-  Cannot create, edit, or delete records
-  Cannot manage users
-  Ideal for budget analysts and auditors

### ⚙️ **Admin**
Full power to manage everything:
-  Complete access to all features
-  Create, edit, delete records
-  Create and manage users
-  Change user roles
-  View all dashboards
-  Ideal for system administrators

---

##  Project Structure

```
 Backend Assignment
│
├──  README.md                 ← You are here!
├──  requirements.txt          ← All dependencies
├
│
├──  app/                      ← Main application code
│   ├── main.py                  ← FastAPI app setup
│   ├── config.py                ← Configuration (env vars)
│   ├── database.py              ← Database connection
│   ├── models.py                ← SQLAlchemy models (User, FinancialRecord)
│   ├── schemas.py               ← Pydantic validation schemas
│   ├── security.py              ← Password hashing & JWT tokens
│   ├── dependencies.py          ← Reusable auth checks
│   ├── bootstrap.py             ← Database initialization
│   │
│   └──  routers/              ← API endpoints organized by feature
│       ├── auth.py              ← Login & token endpoints
│       ├── users.py             ← User management endpoints
│       ├── records.py           ← Financial record endpoints
│       └── dashboard.py         ← Dashboard summary & trends
│
└──  tests/
    └── test_api.py              ← Automated tests (all passing )
```

---

##  Quick Start (5 Minutes)

### Step 1️ Set Up Your Environment

**Create a virtual environment** to keep dependencies isolated:

bash
python -m venv .venv


**Activate it:**

```bash
#  On Windows (PowerShell)
.venv\Scripts\Activate.ps1

#  On Linux/Mac
source .venv/bin/activate
```

You'll see `(.venv)` in your terminal when active.

### Step 2️ Install Dependencies

bash
pip install -r requirements.txt


This installs FastAPI, SQLAlchemy, JWT, and other packages.

### Step 3️ Start the Server

bash
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000


You should see:

 Uvicorn running on http://0.0.0.0:8000 (Press CTRL+C to quit)
 Application startup complete




##  Running Tests

Want to verify everything works?

bash
pytest tests/ -v


You'll see all tests pass :

 test_role_based_permissions PASSED
 test_summary_calculation_and_filters PASSED
 test_prevent_disabling_last_admin PASSED




##  Using the API

### Option 1: Interactive Swagger UI (Easiest!)

Open your browser and go to:

http://localhost:8000/docs


You can:
-  See all endpoints with descriptions
-  Try each API call directly
-  View request/response examples

### Option 2: ReDoc Alternative

For a cleaner, read-only view:
http://localhost:8000/redoc


### Option 3: Command Line with curl

Or use curl if you prefer the terminal!

---

##  Authentication

All endpoints (except `/health`) require a login token.

### Step-by-Step:

**1. Login to get a token:**
bash
curl -X POST "http://localhost:8000/auth/login" \
  -H "Content-Type: application/json" \
  -d '{"email": "admin@financeapp.com", "password": "Admin@123"}'


*Response:**
json
{
  "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "token_type": "bearer"
}


**2. Use the token on protected endpoints:**

Copy that `access_token` value and include it in the header:

bash
curl -X GET "http://localhost:8000/auth/me" \
  -H "Authorization: Bearer YOUR_TOKEN_HERE"


That's it! 


##  Default Admin Account

When the server starts, it automatically creates:

| Field | Value |
|-------|-------|
| Email | `admin@financeapp.com` |
| Password | `Admin@123` |
| Role | Admin (full access) |

 **Change this** by setting environment variables:
bash
set DEFAULT_ADMIN_EMAIL=your-email@company.com
set DEFAULT_ADMIN_PASSWORD=YourSecurePassword123




##  Common API Endpoints

###  System
-'GET /health` — Check server status (no auth needed)

### Authentication
- `POST /auth/login` — Get access token
- `GET /auth/me` — Get current user info

###  Users (Admin Only)
- `POST /users` — Create new user
- `GET /users` — List all users
- `GET /users/{id}` — Get user details
- `PATCH /users/{id}` — Update user
- `DELETE /users/{id}` — Deactivate user

###  Financial Records (Analyst/Admin)
- `POST /records` — Create transaction (admin)
- `GET /records` — List transactions with filters
- `GET /records/{id}` — Get single transaction
- `PATCH /records/{id}` — Edit transaction (admin)
- `DELETE /records/{id}` — Delete transaction (admin, soft delete)

**Filters on `/records`:**
```
?start_date=2026-01-01
&end_date=2026-12-31
&category=Salary
&type=income              (or "expense")
&min_amount=100
&max_amount=5000
&page=1
&page_size=20
```

###  Dashboard (Viewer/Analyst/Admin)
- `GET /dashboard/summary` — Get totals and category breakdown
- `GET /dashboard/trends` — Get monthly/weekly trends

**Parameters:**

?period=monthly          (or "weekly")
&points=6               (how many periods to return)
&start_date=2026-01-01
&end_date=2026-12-31


---

##  Design Decisions

Here's why we built it this way:

###  Security
- **PBKDF2 hashing** with 210,000 iterations keeps passwords safe
- **JWT tokens** expire after 2 hours for security
- Each endpoint checks user role before proceeding
- Inactive users cannot use the system

###  Data Integrity
- **Soft delete** on records means nothing is permanently lost
  - Keeps audit trail intact
  - Data can be recovered if needed
  - Perfect for compliance requirements

###  Role Enforcement
- Viewers can only see dashboards (safe for executives)
- Analysts can analyze but not modify (safe for reports)
- Admins make all changes (with constraints to prevent accidents)

###  Database Choice
- **SQLite** chosen for simplicity and portability
  - No separate database server needed
  - Perfect for development and small deployments
  - Can scale to PostgreSQL later if needed

###  Query Optimization
- Key fields are indexed (email, type, category, date)
- Results sorted by date (newest first)
- Pagination prevents loading everything at once

---

##  Error Handling

The API is smart about errors and tells you what went wrong:

| Status | Meaning | Example |
|--------|---------|---------|
| **200** | Success | Request worked perfectly |
| **201** | Created | New user/record added |
| **204** | Deleted | Record successfully removed |
| **400** | Bad Input | start_date is after end_date |
| **401** | Not Logged In | Missing or invalid token |
| **403** | Not Allowed | Viewer trying to create record |
| **404** | Not Found | Record with ID 999 doesn't exist |
| **409** | Duplicate | Email already exists |
| **422** | Invalid Format | Password too short, invalid email |

**Example error response:**
```json
{
  "detail": "Role 'viewer' is not allowed for this action."
}


---

##  API Response Format

### Success Response
json
{
  "id": 1,
  "email": "user@example.com",
  "full_name": "John Doe",
  "role": "analyst",
  "is_active": true,
  "created_at": "2026-01-15T10:30:00+00:00",
  "updated_at": "2026-01-15T10:30:00+00:00"
}


### Error Response
json
{
  "detail": "A user with this email already exists."
}


---

##  Roadmap & Future Ideas

Things you could add later:

-  Email notifications when records are created/updated
-  Export to CSV/Excel functionality
-  Alerts for budget thresholds
-  Mobile app integration
-  Advanced analytics and ML predictions
-  Multi-currency support
-  Two-factor authentication

---

##  Troubleshooting

### "Module not found" error
bash
# Make sure virtual environment is activated:
.venv\Scripts\Activate.ps1  # Windows
source .venv/bin/activate  # Linux/Mac

# Then reinstall dependencies:
pip install -r requirements.txt


### "Address already in use" error
bash
# Port 8000 is taken. Use a different port:
uvicorn app.main:app --reload --port 8001


### Tests failing
bash
# Make sure you're in the right directory:
cd "c:\Users\DELL\Downloads\Backend Assignment"

# Run tests:
pytest tests/ -v


### Can't login
- Check email is lowercase: `admin@financeapp.com`
- Check password is: `Admin@123`
- Or create new user via admin account

---

##  Learn More

- **FastAPI Docs**: https://fastapi.tiangolo.com
- **SQLAlchemy Guide**: https://docs.sqlalchemy.org
- **JWT Explained**: https://jwt.io
- **REST API Best Practices**: https://restfulapi.net


"# Backend-as" 
