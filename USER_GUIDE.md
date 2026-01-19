# Corporate Vacation AI Agent - User Guide

## 📖 Table of Contents

1. [Project Overview](#project-overview)
2. [Project Structure](#project-structure)
3. [System Architecture](#system-architecture)
4. [Key Components](#key-components)
5. [Getting Started](#getting-started)
6. [Using the Web UI](#using-the-web-ui)
7. [Understanding the Flow](#understanding-the-flow)
8. [Utility Scripts](#utility-scripts)
9. [Troubleshooting](#troubleshooting)

---

## 🎯 Project Overview

The **Corporate Vacation AI Agent** is an intelligent leave management system that automates vacation request approvals. It combines:

- **Database queries** to check employee leave balances
- **AI-powered policy checks** using RAG (Retrieval-Augmented Generation)
- **Interactive web interface** for submitting and managing requests
- **Automated decision-making** with detailed explanations

### What This System Does

1. ✅ Checks if employees have sufficient leave balance
2. ✅ Validates requests against corporate policies (60% rule, blackout periods, notice requirements)
3. ✅ Provides alternative options when requests can't be approved as-is
4. ✅ Generates manager notification emails
5. ✅ Tracks all leave requests and updates balances

---

## 📁 Project Structure

```
corporate-vacation-agent/
│
├── 📂 src/                      # Core source code
│   ├── __init__.py
│   ├── database_tool.py         # Database operations (balance queries, employee info)
│   ├── policy_rag.py            # RAG system for policy compliance checks
│   └── vacation_agent.py        # Main agent orchestrating Tool→RAG flow
│
├── 📂 data/                     # Data files
│   ├── company_policy.md        # Corporate leave policy document (source for RAG)
│   ├── employee_data.db         # SQLite database (employees, balances, requests)
│   └── chroma_db/               # Vector store for policy embeddings (auto-generated)
│
├── 📄 streamlit_app.py          # Web UI application (main entry point)
│
├── 🔧 Utility Scripts
│   ├── main.py                  # CLI demo script (testing/demonstration)
│   ├── populate_employees.py    # Create/populate employee database
│   └── reset_balances.py        # Reset all employees to fresh balances
│
├── 📚 Documentation
│   ├── README.md                # Project documentation
│   ├── USER_GUIDE.md            # This file - user guide
│   └── WEB_UI_README.md         # Web UI specific documentation
│
├── ⚙️ Configuration
│   ├── requirements.txt         # Python dependencies
│   ├── .env                     # Environment variables (OPENAI_API_KEY)
│   └── .gitignore              # Git ignore rules
│
└── 📦 __pycache__/             # Python cache (auto-generated, ignored by git)
```

---

## 🏗️ System Architecture

### The Tool→RAG Flow

The system follows a **two-step validation process**:

```
┌─────────────────────────────────────────────────────────────┐
│  USER SUBMITS LEAVE REQUEST                                 │
└────────────────────────┬────────────────────────────────────┘
                         │
                         ▼
┌─────────────────────────────────────────────────────────────┐
│  STEP 1: TOOL QUERY (Database)                              │
│  • Check employee balance                                    │
│  • Verify sufficient days/hours available                    │
│  • Get employee information                                  │
└────────────────────────┬────────────────────────────────────┘
                         │
                         ▼
┌─────────────────────────────────────────────────────────────┐
│  STEP 2: RAG QUERY (Policy Check)                           │
│  • Search policy document for compliance rules               │
│  • Check 60% rule, blackout periods, notice requirements    │
│  • Validate frequency limits                                 │
└────────────────────────┬────────────────────────────────────┘
                         │
                         ▼
┌─────────────────────────────────────────────────────────────┐
│  STEP 3: ANALYSIS & OPTIONS                                 │
│  • Display all checks (Balance, Policy, Blackout, etc.)     │
│  • Show 4 options: Approve, Suggest Dates, Split, Deny      │
│  • User chooses → Request processed → Balance updated        │
└─────────────────────────────────────────────────────────────┘
```

### Key Files & Their Roles

| File | Purpose |
|------|---------|
| `streamlit_app.py` | **Main web application** - user interface for submitting requests |
| `src/vacation_agent.py` | **Core logic** - orchestrates Tool→RAG flow, generates responses |
| `src/database_tool.py` | **Database layer** - queries employee data, updates balances |
| `src/policy_rag.py` | **Policy checker** - uses RAG to validate against company policy |
| `data/company_policy.md` | **Policy source** - corporate leave policy (vectorized for RAG) |
| `data/employee_data.db` | **Data store** - SQLite database with employees, balances, requests |

---

## 🔧 Key Components Explained

### 1. Database Tool (`src/database_tool.py`)

**What it does:**
- Stores employee information (name, department, position)
- Tracks leave balances (vacation days, remaining hours, sick leave)
- Records all leave requests (approved, denied, pending)
- Updates balances when requests are approved

**Key Functions:**
- `get_remaining_balance()` - Check available leave days/hours
- `get_employee_info()` - Get employee details
- `record_leave_request()` - Save a request and update balance
- `check_balance_sufficient()` - Validate if balance is enough

### 2. Policy RAG (`src/policy_rag.py`)

**What it does:**
- Loads the corporate leave policy document
- Converts policy text into vector embeddings
- Uses semantic search to find relevant policy sections
- Validates requests against business rules

**Key Functions:**
- `check_policy_compliance()` - Validate request against policies
- `get_blackout_periods()` - List restricted dates
- `explain_policy_section()` - Explain specific policy rules
- `suggest_alternatives()` - Provide alternative options

**Policy Rules Checked:**
- ✅ **60% Rule**: Max 60% of annual quota in single request
- ✅ **Notice Period**: 14 days for >3 days, 5 days for ≤3 days
- ✅ **Blackout Periods**: Restricted dates (Q1, Q4 year-end)
- ✅ **Frequency Limits**: Max 2 long vacations (>7 days) per 60 days

### 3. Vacation Agent (`src/vacation_agent.py`)

**What it does:**
- Orchestrates the entire Tool→RAG flow
- Generates conversational responses
- Creates detailed analysis checks
- Provides proactive options

**Key Functions:**
- `process_vacation_request()` - Main function processing requests
- `_generate_analysis_checks()` - Create detailed check breakdowns
- `_generate_approval_response()` - Generate response messages
- `generate_employee_email()` - Create manager notification emails

**Request Status Flow:**
```
Pending → [User chooses option] → Approved/Denied → Balance Updated
```

---

## 🚀 Getting Started

### Prerequisites

1. **Python 3.8+** installed
2. **OpenAI API Key** (for RAG features)
3. **SQLite** (usually included with Python)

### Installation Steps

1. **Clone or download the project**
   ```bash
   cd corporate-vacation-agent
   ```

2. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

3. **Set up environment variables**
   Create a `.env` file in the project root:
   ```bash
   OPENAI_API_KEY=your_api_key_here
   ```

4. **Initialize the database**
   ```bash
   python populate_employees.py
   ```
   This creates the database with 31 employees (6 managers + 25 employees).

5. **Run the web application**
   ```bash
   streamlit run streamlit_app.py
   ```
   The app will open in your browser at `http://localhost:8501`

### First-Time Setup Checklist

- [ ] Python installed (3.8+)
- [ ] Dependencies installed (`pip install -r requirements.txt`)
- [ ] `.env` file created with `OPENAI_API_KEY`
- [ ] Database initialized (`python populate_employees.py`)
- [ ] Web app starts successfully (`streamlit run streamlit_app.py`)

---

## 🖥️ Using the Web UI

### Interface Overview

The Streamlit web interface has **three main sections**:

#### 1. **Sidebar** (Left)
- Employee lookup and selection
- View all 31 employees
- See employee balances at a glance

#### 2. **Main Form** (Center-Left)
- Employee ID input
- Leave type selection (Vacation/Sick)
- Date range selection (Start/End dates)
- Manager checkbox (for auto-approval)
- Submit button

#### 3. **Results Panel** (Right)
- **Processing Flow**: Shows Tool→RAG steps in real-time
- **Request Analysis**: Detailed checks (Balance, Policy, etc.)
- **Options**: Approve, Suggest Alternatives, Split, or Deny

### Submitting a Request

1. **Select an employee** from the sidebar (or type ID)
2. **Choose leave type** (Vacation or Sick)
3. **Select dates** (Start and End)
4. **Check manager box** if it's a manager's request (auto-approved)
5. **Click "Process Request"**

### Understanding the Results

After submitting, you'll see:

#### **Processing Flow**
- ✅ Step 1: Database Tool Query - Balance check
- ✅ Step 2: Policy RAG Query - Policy compliance check
- ✅ Step 3: Decision - Request status

#### **Request Analysis**
Shows 6 checks with PASS/FAIL/WARNING status:
- ✅ **Balance Check**: Do you have enough days?
- ✅ **Max Consecutive Days**: Within 10-day limit?
- ✅ **Blackout Period**: Dates available?
- ✅ **Frequency Limits**: Within vacation frequency rules?
- ✅ **Notice Period**: Sufficient advance notice?
- ⚠️ **Weekend Inclusion**: Includes weekends (informational)

#### **Choose an Action**
Four options appear:

1. **✅ Approve Exactly as Requested**
   - Click "APPROVE THIS OPTION" to approve
   - Balance will be updated automatically

2. **🔄 Suggest Better Dates**
   - Click "VIEW SUGGESTIONS" to see alternative dates
   - Dates are shifted to avoid conflicts

3. **✂️ Split Request**
   - Click "SPLIT REQUEST" to divide into smaller segments
   - Use the form to specify segment days

4. **❌ Deny with Explanation**
   - Click "DENY REQUEST" to deny
   - Shows policy violations if any

---

## 🔄 Understanding the Flow

### Complete Request Lifecycle

```
1. User fills form → Submits request
   ↓
2. System checks balance (Tool Query)
   - ✅ Sufficient? Continue
   - ❌ Insufficient? Show error
   ↓
3. System checks policy (RAG Query)
   - ✅ Compliant? Status: "pending"
   - ❌ Violations? Status: "pending" (with violations listed)
   ↓
4. Display analysis checks
   - Balance: PASS/FAIL
   - Policy: PASS/FAIL/WARNING
   ↓
5. Show options (if pending)
   - Option A: Approve
   - Option B: Suggest alternatives
   - Option C: Split request
   - Option D: Deny
   ↓
6. User chooses option → Action processed
   ↓
7. If approved: Balance updated, request recorded
   If denied: Request recorded (no balance change)
```

### Status Types

- **`pending`**: Request analyzed, waiting for user decision
- **`approved`**: Request approved, balance updated
- **`denied`**: Request denied, balance unchanged

---

## 🔧 Utility Scripts

### `populate_employees.py`

**Purpose:** Create and populate the employee database

**Usage:**
```bash
python populate_employees.py
```

**What it does:**
- Creates `employees` table with schema
- Inserts 31 employees:
  - 6 managers (MGR001-MGR006)
  - 25 employees (EMP001-EMP025)
- Sets up departments: Engineering, Marketing, Finance, Operations, HR, IT
- Initializes balances (12-30 vacation days, 64 sick hours)

### `reset_balances.py`

**Purpose:** Reset all employees to fresh starting balances

**Usage:**
```bash
python reset_balances.py
```

**What it does:**
- Archives existing leave requests
- Resets vacation balance to original allocation
- Resets sick leave to 64 hours (0 used)
- Clears all used hours

### `main.py`

**Purpose:** CLI demo script for testing

**Usage:**
```bash
python main.py
```

**What it does:**
- Runs 8 different test scenarios
- Demonstrates all features
- Shows Tool→RAG flow in action
- Useful for development/testing

---

## 🐛 Troubleshooting

### Common Issues

#### 1. **"OPENAI_API_KEY not found" Error**

**Problem:** RAG features won't work without API key

**Solution:**
- Create `.env` file in project root
- Add: `OPENAI_API_KEY=your_key_here`
- Restart Streamlit app

#### 2. **"No such table: employees" Error**

**Problem:** Database not initialized

**Solution:**
```bash
python populate_employees.py
```

#### 3. **Options Not Showing After Analysis**

**Problem:** Status might be "approved" instead of "pending"

**Solution:**
- Check `src/vacation_agent.py` line 189: `response["status"] = "pending"`
- Restart Streamlit to reload code changes
- Clear browser cache if needed

#### 4. **Balance Not Updating After Approval**

**Problem:** Request might not be recorded

**Solution:**
- Check database connection
- Verify `record_leave_request()` is called
- Check `src/database_tool.py` - `record_leave_request()` updates `remaining_hours`

#### 5. **Streamlit Errors After Code Changes**

**Problem:** Streamlit caches Python modules

**Solution:**
- Stop Streamlit (Ctrl+C)
- Clear cache: `rm -rf ~/.streamlit/cache`
- Restart: `streamlit run streamlit_app.py`

### Getting Help

1. **Check the logs** - Streamlit shows errors in terminal
2. **Verify database** - Use `sqlite3 data/employee_data.db` to inspect
3. **Test components** - Run `python main.py` to test agent logic
4. **Check .env** - Ensure `OPENAI_API_KEY` is set correctly

---

## 📊 Database Schema

### `employees` Table

| Column | Type | Description |
|--------|------|-------------|
| `employee_id` | TEXT | Primary key (e.g., "EMP001") |
| `name` | TEXT | Employee full name |
| `email` | TEXT | Email address |
| `department` | TEXT | Department name |
| `position` | TEXT | Job title |
| `vacation_days` | INTEGER | Annual vacation allocation |
| `remaining_hours` | REAL | Current available hours |
| `annual_quota` | INTEGER | Annual quota days |
| `vacation_used_hours` | REAL | Hours used this year |
| `sick_accrued_hours` | REAL | Sick leave accrued (default 64) |
| `sick_used_hours` | REAL | Sick leave used |

### `leave_requests` Table

| Column | Type | Description |
|--------|------|-------------|
| `request_id` | INTEGER | Primary key (auto-increment) |
| `employee_id` | TEXT | Employee identifier |
| `leave_type` | TEXT | "vacation" or "sick" |
| `start_date` | DATE | Leave start date |
| `end_date` | DATE | Leave end date |
| `days_requested` | REAL | Number of days |
| `hours_requested` | REAL | Number of hours |
| `status` | TEXT | "approved", "denied", or "pending" |
| `request_date` | DATE | Date request was submitted |

---

## 🎓 Learning More

### Understanding RAG

**RAG (Retrieval-Augmented Generation)** combines:
- **Retrieval**: Searching vectorized policy document
- **Augmentation**: Adding policy context to AI prompts
- **Generation**: AI generates compliance checks

The policy document (`data/company_policy.md`) is converted to vectors using OpenAI embeddings, stored in ChromaDB (`data/chroma_db/`), and searched semantically when checking compliance.

### Understanding the Tool→RAG Flow

This pattern ensures:
1. **Fast checks first** (database queries)
2. **Intelligent checks second** (policy RAG)
3. **Human decision last** (user chooses from options)

This approach is more efficient than using AI for everything and ensures accurate balance calculations.

---

## 📝 Summary

This Corporate Vacation AI Agent provides:

✅ **Intelligent leave management** with AI-powered policy checks  
✅ **Real-time balance tracking** via SQLite database  
✅ **Interactive web interface** for easy request submission  
✅ **Automated decision support** with multiple options  
✅ **Manager notifications** via email generation  

**Main Entry Point:** `streamlit run streamlit_app.py`  
**Key File:** `src/vacation_agent.py` (core logic)  
**Data:** `data/employee_data.db` (database)  
**Policy:** `data/company_policy.md` (policy source)

---

*Last Updated: 2026*  
*Version: 1.0*
