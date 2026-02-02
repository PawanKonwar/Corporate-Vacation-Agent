"""
Database Tool for Employee Leave Balance Queries
Handles SQLite database operations for vacation and sick leave balances
"""

import sqlite3
import os
from typing import Dict, Optional, List, Tuple
from datetime import datetime, date


class EmployeeDatabase:
    """Database tool for querying employee leave balances and records"""
    
    def __init__(self, db_path: str = "data/employee_data.db"):
        """Initialize database connection"""
        self.db_path = db_path
        self._ensure_db_exists()
    
    def _ensure_db_exists(self):
        """Create database and tables if they don't exist"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Check if employees table exists and what schema it uses
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='employees'")
        table_exists = cursor.fetchone()
        
        if table_exists:
            # Check columns to determine schema
            cursor.execute("PRAGMA table_info(employees)")
            columns = [row[1] for row in cursor.fetchall()]
            
            # If old schema (vacation_accrued_hours), migrate or adapt
            if 'vacation_accrued_hours' in columns:
                # Old schema - keep as is for backward compatibility
                pass
            elif 'vacation_days' in columns and 'remaining_hours' in columns:
                # New schema - add tracking columns if missing
                if 'vacation_used_hours' not in columns:
                    cursor.execute("ALTER TABLE employees ADD COLUMN vacation_used_hours REAL DEFAULT 0.0")
                    cursor.execute("ALTER TABLE employees ADD COLUMN sick_used_hours REAL DEFAULT 0.0")
                    cursor.execute("ALTER TABLE employees ADD COLUMN sick_accrued_hours REAL DEFAULT 64.0")
                    # Initialize used_hours based on difference
                    cursor.execute("""
                        UPDATE employees 
                        SET vacation_used_hours = (vacation_days * 8) - remaining_hours
                        WHERE vacation_used_hours IS NULL OR vacation_used_hours = 0
                    """)
                # Cap vacation_days and remaining_hours at annual_quota (fix inconsistent data)
                if 'annual_quota' in columns:
                    cursor.execute("""
                        UPDATE employees
                        SET vacation_days = CASE WHEN vacation_days > COALESCE(annual_quota, 20) 
                            THEN COALESCE(annual_quota, 20) ELSE vacation_days END,
                            remaining_hours = CASE WHEN remaining_hours > (COALESCE(annual_quota, 20) * 8) 
                            THEN (COALESCE(annual_quota, 20) * 8) ELSE remaining_hours END
                        WHERE vacation_days > COALESCE(annual_quota, 20) OR remaining_hours > (COALESCE(annual_quota, 20) * 8)
                    """)
        else:
            # Create employees table with new schema (for fresh installs)
            cursor.execute("""
                CREATE TABLE employees (
                    employee_id TEXT PRIMARY KEY,
                    name TEXT NOT NULL,
                    vacation_days INTEGER NOT NULL,
                    remaining_hours INTEGER NOT NULL,
                    email TEXT UNIQUE,
                    department TEXT,
                    position TEXT,
                    start_date DATE,
                    manager_id TEXT,
                    annual_quota INTEGER DEFAULT 20,
                    vacation_used_hours REAL DEFAULT 0.0,
                    sick_used_hours REAL DEFAULT 0.0,
                    sick_accrued_hours REAL DEFAULT 64.0,
                    years_of_service INTEGER DEFAULT 0,
                    vacation_annual_quota_days INTEGER,
                    sick_annual_quota_days INTEGER DEFAULT 8,
                    vacation_accrued_hours REAL,
                    FOREIGN KEY (manager_id) REFERENCES employees(employee_id)
                )
            """)
            # Initialize vacation_accrued_hours from vacation_days
            # This will be populated when data is inserted
        
        # Create leave_requests table for tracking frequency limits
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS leave_requests (
                request_id INTEGER PRIMARY KEY AUTOINCREMENT,
                employee_id TEXT NOT NULL,
                leave_type TEXT NOT NULL,
                start_date DATE NOT NULL,
                end_date DATE NOT NULL,
                days_requested INTEGER NOT NULL,
                hours_requested REAL NOT NULL,
                status TEXT DEFAULT 'approved',
                request_date DATE DEFAULT CURRENT_DATE,
                FOREIGN KEY (employee_id) REFERENCES employees(employee_id)
            )
        """)
        
        conn.commit()
        conn.close()
    
    def get_remaining_balance(self, employee_id: str, leave_type: str = "vacation") -> Dict:
        """
        Query remaining balance for an employee
        
        Args:
            employee_id: Employee identifier
            leave_type: 'vacation' or 'sick'
            
        Returns:
            Dictionary with balance information including:
            - remaining_days
            - remaining_hours
            - accrued_hours
            - used_hours
            - annual_quota_days
            - annual_quota_hours
        """
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Check which schema columns exist
        cursor.execute("PRAGMA table_info(employees)")
        columns = [row[1] for row in cursor.fetchall()]
        
        if 'vacation_days' in columns and 'remaining_hours' in columns:
            # New schema - vacation: use remaining_hours; sick: sick_accrued_hours - sick_used_hours
            has_sick_accrued = 'sick_accrued_hours' in columns
            has_sick_used = 'sick_used_hours' in columns
            # No sick_annual_quota_days column; use 8 (sick_accrued default 64/8)
            if has_sick_accrued and has_sick_used:
                cursor.execute("""
                    SELECT vacation_days, remaining_hours, annual_quota, 
                           COALESCE(vacation_used_hours, 0), COALESCE(sick_used_hours, 0),
                           COALESCE(sick_accrued_hours, 64.0)
                    FROM employees
                    WHERE employee_id = ?
                """, (employee_id,))
            else:
                cursor.execute("""
                    SELECT vacation_days, remaining_hours, annual_quota, 
                           COALESCE(vacation_used_hours, 0), 0, 64.0
                    FROM employees
                    WHERE employee_id = ?
                """, (employee_id,))
            
            result = cursor.fetchone()
            conn.close()
            
            if not result:
                return {
                    "error": f"Employee {employee_id} not found",
                    "remaining_days": 0,
                    "remaining_hours": 0,
                    "annual_quota_days": 0
                }
            
            vac_days, remaining_hours, annual_quota, vac_used, sick_used, sick_accrued = result
            
            if leave_type.lower() == "vacation":
                remaining_hours_val = max(0.0, float(remaining_hours))
                accrued = vac_days * 8
                used = vac_used
                quota_days = annual_quota or 20
            else:  # sick
                # remaining_hours = sick_accrued_hours - sick_used_hours
                # remaining_days = remaining_hours / 8
                # annual_quota_days = 8 (sick_accrued 64 / 8)
                remaining_hours_val = max(0.0, float(sick_accrued) - float(sick_used))
                accrued = sick_accrued
                used = sick_used
                quota_days = 8  # From sick_accrued_hours default 64 / 8
            
            remaining_hours = round(remaining_hours_val, 2)
            max_hours = round(quota_days * 8, 2)
            remaining_hours = min(remaining_hours, max_hours)
            remaining_days = round(remaining_hours / 8.0, 2)
        else:
            # Old schema - use accrued/used model
            cursor.execute("""
                SELECT vacation_accrued_hours, sick_accrued_hours,
                       vacation_used_hours, sick_used_hours,
                       vacation_annual_quota_days, sick_annual_quota_days
                FROM employees
                WHERE employee_id = ?
            """, (employee_id,))
            
            result = cursor.fetchone()
            conn.close()
            
            if not result:
                return {
                    "error": f"Employee {employee_id} not found",
                    "remaining_days": 0,
                    "remaining_hours": 0,
                    "annual_quota_days": 0
                }
            
            vac_accrued, sick_accrued, vac_used, sick_used, vac_quota, sick_quota = result
            
            if leave_type.lower() == "vacation":
                accrued = vac_accrued
                used = vac_used
                quota_days = vac_quota
            else:  # sick
                accrued = sick_accrued
                used = sick_used
                quota_days = sick_quota
            
            remaining_hours_val = max(0, accrued - used)
            remaining_hours = round(remaining_hours_val, 2)
            quota_days_val = quota_days or 20
            max_hours = round(quota_days_val * 8, 2)
            remaining_hours = min(remaining_hours, max_hours)
            remaining_days = round(remaining_hours / 8.0, 2)
        
        return {
            "employee_id": employee_id,
            "leave_type": leave_type,
            "remaining_days": round(remaining_days, 2),
            "remaining_hours": round(remaining_hours, 2),
            "accrued_hours": round(accrued, 2),
            "used_hours": round(used, 2),
            "annual_quota_days": quota_days,
            "annual_quota_hours": quota_days * 8
        }
    
    def check_balance_sufficient(self, employee_id: str, days_requested: float, leave_type: str = "vacation") -> Tuple[bool, Dict]:
        """
        Check if employee has sufficient balance for request
        
        Returns:
            Tuple of (is_sufficient, balance_info)
        """
        balance = self.get_remaining_balance(employee_id, leave_type)
        if "error" in balance:
            return False, balance
        
        hours_needed = days_requested * 8
        is_sufficient = balance["remaining_hours"] >= hours_needed
        
        return is_sufficient, balance
    
    def get_employee_info(self, employee_id: str) -> Optional[Dict]:
        """Get employee information including annual quotas"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Check which schema columns exist
        cursor.execute("PRAGMA table_info(employees)")
        columns = [row[1] for row in cursor.fetchall()]
        
        if 'annual_quota' in columns:
            # New schema
            # Check if years_of_service exists
            has_years = 'years_of_service' in columns
            has_sick_quota = 'sick_annual_quota_days' in columns
            
            if has_years and has_sick_quota:
                cursor.execute("""
                    SELECT employee_id, name, COALESCE(years_of_service, 0), 
                           annual_quota, COALESCE(sick_annual_quota_days, 8)
                    FROM employees
                    WHERE employee_id = ?
                """, (employee_id,))
            elif has_years:
                cursor.execute("""
                    SELECT employee_id, name, COALESCE(years_of_service, 0), 
                           annual_quota, 8
                    FROM employees
                    WHERE employee_id = ?
                """, (employee_id,))
            else:
                # Calculate years_of_service from start_date if available
                has_start_date = 'start_date' in columns
                if has_start_date:
                    cursor.execute("""
                        SELECT employee_id, name, 
                               COALESCE(CAST((julianday('now') - julianday(start_date)) / 365.25 AS INTEGER), 0) as years,
                               annual_quota, 8
                        FROM employees
                        WHERE employee_id = ?
                    """, (employee_id,))
                else:
                    cursor.execute("""
                        SELECT employee_id, name, 0, annual_quota, 8
                        FROM employees
                        WHERE employee_id = ?
                    """, (employee_id,))
            
            result = cursor.fetchone()
            conn.close()
            
            if not result:
                return None
            
            emp_id, name, years, vac_quota, sick_quota = result
            return {
                "employee_id": emp_id,
                "name": name,
                "years_of_service": years,
                "vacation_annual_quota_days": vac_quota or 20,
                "sick_annual_quota_days": sick_quota
            }
        else:
            # Old schema
            cursor.execute("""
                SELECT employee_id, name, years_of_service,
                       vacation_annual_quota_days, sick_annual_quota_days
                FROM employees
                WHERE employee_id = ?
            """, (employee_id,))
            
            result = cursor.fetchone()
            conn.close()
            
            if not result:
                return None
            
            emp_id, name, years, vac_quota, sick_quota = result
            return {
                "employee_id": emp_id,
                "name": name,
                "years_of_service": years,
                "vacation_annual_quota_days": vac_quota,
                "sick_annual_quota_days": sick_quota
            }
    
    def get_long_vacations(self, employee_id: str, start_date: date, end_date: date) -> List[Dict]:
        """
        Get long vacations (>7 days) within 60 days of the requested date range
        Used for frequency limit checking
        """
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Calculate 60 days before start and 60 days after end
        # We need to check if there are more than 2 long vacations in any 60-day window
        
        # Get all approved long vacation requests (>7 days) for this employee
        cursor.execute("""
            SELECT start_date, end_date, days_requested, request_date
            FROM leave_requests
            WHERE employee_id = ? 
            AND leave_type = 'vacation'
            AND days_requested > 7
            AND status = 'approved'
            ORDER BY start_date DESC
        """, (employee_id,))
        
        results = cursor.fetchall()
        conn.close()
        
        vacations = []
        for row in results:
            vac_start, vac_end, days, req_date = row
            # Convert string dates to date objects
            if isinstance(vac_start, str):
                vac_start = datetime.strptime(vac_start, "%Y-%m-%d").date()
            if isinstance(vac_end, str):
                vac_end = datetime.strptime(vac_end, "%Y-%m-%d").date()
            
            vacations.append({
                "start_date": vac_start,
                "end_date": vac_end,
                "days": days
            })
        
        return vacations
    
    def _update_employee_balance(
        self, cursor, employee_id: str, leave_type: str, days_change: float
    ) -> None:
        """Update employee balance. hours_change = days_change * 8.
        Updates BOTH days and hours columns to keep them synchronized.
        Positive days_change = use leave = deduct. Negative = add back."""
        hours_change = float(days_change) * 8
        if hours_change == 0:
            return

        cursor.execute("PRAGMA table_info(employees)")
        columns = [row[1] for row in cursor.fetchall()]
        has_vacation_days = "vacation_days" in columns
        has_remaining_hours = "remaining_hours" in columns
        has_vacation_used = "vacation_used_hours" in columns
        has_sick_used = "sick_used_hours" in columns
        has_remaining_sick_hours = "remaining_sick_hours" in columns

        if leave_type.lower() == "vacation":
            # 1. vacation_days = vacation_days - days_change, capped to [0, annual_quota]
            # 2. remaining_hours = remaining_hours - (days_change * 8)
            has_annual_quota = "annual_quota" in columns
            if has_vacation_days:
                if has_annual_quota:
                    cursor.execute(
                        """
                        UPDATE employees
                        SET vacation_days = CASE 
                            WHEN vacation_days - ? < 0 THEN 0 
                            WHEN vacation_days - ? > COALESCE(annual_quota, 20) THEN COALESCE(annual_quota, 20)
                            ELSE vacation_days - ?
                        END
                        WHERE employee_id = ?
                        """,
                        (days_change, days_change, days_change, employee_id),
                    )
                else:
                    cursor.execute(
                        """
                        UPDATE employees
                        SET vacation_days = CASE 
                            WHEN vacation_days - ? < 0 THEN 0 
                            ELSE vacation_days - ?
                        END
                        WHERE employee_id = ?
                        """,
                        (days_change, days_change, employee_id),
                    )
            if has_remaining_hours:
                if has_annual_quota:
                    cursor.execute(
                        """
                        UPDATE employees
                        SET remaining_hours = CASE 
                            WHEN remaining_hours - ? < 0 THEN 0 
                            WHEN remaining_hours - ? > COALESCE(annual_quota, 20) * 8 THEN COALESCE(annual_quota, 20) * 8
                            ELSE remaining_hours - ?
                        END
                        WHERE employee_id = ?
                        """,
                        (hours_change, hours_change, hours_change, employee_id),
                    )
                else:
                    cursor.execute(
                        """
                        UPDATE employees
                        SET remaining_hours = CASE 
                            WHEN remaining_hours - ? < 0 THEN 0 
                            ELSE remaining_hours - ?
                        END
                        WHERE employee_id = ?
                        """,
                        (hours_change, hours_change, employee_id),
                    )
            if has_vacation_used:
                cursor.execute(
                    """
                    UPDATE employees
                    SET vacation_used_hours = vacation_used_hours + ?
                    WHERE employee_id = ?
                    """,
                    (hours_change, employee_id),
                )
        else:  # sick
            # Sick: update sick_used_hours and remaining_sick_hours (if column exists)
            if has_sick_used:
                cursor.execute(
                    """
                    UPDATE employees
                    SET sick_used_hours = sick_used_hours + ?
                    WHERE employee_id = ?
                    """,
                    (hours_change, employee_id),
                )
            if has_remaining_sick_hours:
                cursor.execute(
                    """
                    UPDATE employees
                    SET remaining_sick_hours = CASE 
                        WHEN remaining_sick_hours - ? < 0 THEN 0 
                        ELSE remaining_sick_hours - ?
                    END
                    WHERE employee_id = ?
                    """,
                    (hours_change, hours_change, employee_id),
                )
    
    def record_leave_request(self, employee_id: str, leave_type: str, 
                           start_date: date, end_date: date, 
                           days_requested: float, status: str = "approved"):
        """Record a leave request in the database. Reduces balance when approved."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Hours = days * 8 (8 working hours per day)
        hours_requested = float(days_requested) * 8
        
        cursor.execute("""
            INSERT INTO leave_requests 
            (employee_id, leave_type, start_date, end_date, days_requested, hours_requested, status)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        """, (employee_id, leave_type, start_date.isoformat(), 
              end_date.isoformat(), days_requested, hours_requested, status))
        
        if status == "approved":
            self._update_employee_balance(cursor, employee_id, leave_type, days_requested)
        
        conn.commit()
        conn.close()
    
    def get_leave_history(self, employee_id: Optional[str] = None, limit: int = 20) -> List[Dict]:
        """Get leave request history, optionally filtered by employee_id"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        if employee_id:
            cursor.execute("""
                SELECT lr.employee_id, e.name, lr.leave_type, lr.start_date, lr.end_date,
                       lr.days_requested, lr.status, lr.request_date
                FROM leave_requests lr
                LEFT JOIN employees e ON lr.employee_id = e.employee_id
                WHERE lr.employee_id = ?
                ORDER BY lr.request_date DESC, lr.start_date DESC
                LIMIT ?
            """, (employee_id, limit))
        else:
            cursor.execute("""
                SELECT lr.employee_id, e.name, lr.leave_type, lr.start_date, lr.end_date,
                       lr.days_requested, lr.status, lr.request_date
                FROM leave_requests lr
                LEFT JOIN employees e ON lr.employee_id = e.employee_id
                ORDER BY lr.request_date DESC, lr.start_date DESC
                LIMIT ?
            """, (limit,))
        
        rows = cursor.fetchall()
        conn.close()
        
        history = []
        for row in rows:
            emp_id, name, leave_type, start_d, end_d, days, status, req_date = row
            history.append({
                "employee_id": emp_id,
                "employee_name": name or emp_id,
                "leave_type": leave_type,
                "start_date": start_d,
                "end_date": end_d,
                "days_requested": days,
                "status": status,
                "request_date": req_date,
            })
        return history
    
    def initialize_sample_data(self):
        """Initialize database with sample employee data for testing.
        remaining_hours must equal vacation_days * 8 (or adjusted for used balance)."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute("PRAGMA table_info(employees)")
        columns = [row[1] for row in cursor.fetchall()]
        use_new_schema = "vacation_days" in columns and "remaining_hours" in columns
        
        cursor.execute("DELETE FROM leave_requests")
        cursor.execute("DELETE FROM employees")
        
        if use_new_schema:
            # New schema: vacation_days <= annual_quota (default 20), remaining_hours = days * 8
            employees = [
                ("EMP001", "John Smith", 14, 112.0, 20),   # 14 days, quota 20
                ("EMP002", "Jane Doe", 15, 120.0, 20),     # 15 days, quota 20
                ("EMP003", "Bob Johnson", 10, 80.0, 20),   # 10 days, quota 20
                ("EMP004", "Alice Williams", 10, 80.0, 20), # 10 days, quota 20
            ]
            cols = "employee_id, name, vacation_days, remaining_hours, annual_quota"
            placeholders = ", ".join(["?"] * 5)
            for emp_id, name, vac_days, rem_hrs, quota in employees:
                cursor.execute(
                    f"INSERT INTO employees ({cols}) VALUES ({placeholders})",
                    (emp_id, name, vac_days, rem_hrs, quota),
                )
        else:
            # Old schema: accrued/used model (remaining = accrued - used; remaining_days = remaining/8)
            employees = [
                ("EMP001", "John Smith", 2, 10, 8, 112.0, 64.0, 0.0, 0.0),   # 14 days=112hrs accrued, 0 used
                ("EMP002", "Jane Doe", 4, 15, 8, 120.0, 64.0, 0.0, 0.0),     # 15 days=120hrs
                ("EMP003", "Bob Johnson", 7, 20, 8, 160.0, 64.0, 80.0, 0.0), # 10 days=80hrs remain (160-80)
                ("EMP004", "Alice Williams", 1, 10, 8, 80.0, 64.0, 0.0, 0.0), # 10 days=80hrs
            ]
            cursor.executemany("""
                INSERT INTO employees 
                (employee_id, name, years_of_service, vacation_annual_quota_days,
                 sick_annual_quota_days, vacation_accrued_hours, sick_accrued_hours,
                 vacation_used_hours, sick_used_hours)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, employees)
        
        conn.commit()
        conn.close()
        print(f"Sample data initialized in {self.db_path}")


# Example usage
if __name__ == "__main__":
    db = EmployeeDatabase()
    db.initialize_sample_data()
    
    # Test queries
    balance = db.get_remaining_balance("EMP001", "vacation")
    print(f"\nEmployee EMP001 Vacation Balance: {balance}")
    
    sufficient, info = db.check_balance_sufficient("EMP001", 5.0, "vacation")
    print(f"\nCan take 5 days? {sufficient}")
    print(f"Balance info: {info}")
