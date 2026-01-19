# Utility Scripts

This directory contains utility scripts for managing the Corporate Vacation AI Agent.

## Available Scripts

### `populate_employees.py`

**Purpose:** Initialize and populate the employee database

**Location:** Root directory (move to `scripts/` if desired)

**Usage:**
```bash
python populate_employees.py
```

**What it does:**
- Creates the `employees` table with proper schema
- Inserts 31 employees (6 managers + 25 employees)
- Distributes employees across 6 departments
- Sets up initial balances and quotas

### `reset_balances.py`

**Purpose:** Reset all employee balances to fresh starting values

**Location:** Root directory

**Usage:**
```bash
python reset_balances.py
```

**What it does:**
- Archives existing leave requests to `leave_requests_archive` table
- Resets all vacation balances to original allocation
- Resets sick leave to 64 hours accrued, 0 used
- Clears all used hours

### `main.py`

**Purpose:** CLI demonstration script

**Location:** Root directory

**Usage:**
```bash
python main.py
```

**What it does:**
- Runs 8 comprehensive test scenarios
- Demonstrates all agent features
- Useful for development and testing
- Shows Tool→RAG flow in action

## Running Scripts

All scripts should be run from the project root directory:

```bash
cd /path/to/corporate-vacation-agent
python script_name.py
```
