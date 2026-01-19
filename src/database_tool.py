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
            # New schema - use vacation_days and remaining_hours directly
            # Check if sick columns exist, use defaults if not
            has_sick_quota = 'sick_annual_quota_days' in columns
            has_sick_accrued = 'sick_accrued_hours' in columns
            
            if has_sick_quota and has_sick_accrued:
                cursor.execute("""
                    SELECT vacation_days, remaining_hours, annual_quota, 
                           COALESCE(vacation_used_hours, 0), COALESCE(sick_used_hours, 0),
                           COALESCE(sick_accrued_hours, 64.0), COALESCE(sick_annual_quota_days, 8)
                    FROM employees
                    WHERE employee_id = ?
                """, (employee_id,))
            else:
                # Fallback if sick columns don't exist
                cursor.execute("""
                    SELECT vacation_days, remaining_hours, annual_quota, 
                           COALESCE(vacation_used_hours, 0), 0, 64.0, 8
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
            
            vac_days, remaining_hours, annual_quota, vac_used, sick_used, sick_accrued, sick_quota = result
            
            if leave_type.lower() == "vacation":
                # Use remaining_hours directly from new schema
                remaining_hours_val = remaining_hours
                remaining_days = remaining_hours_val / 8.0
                accrued = vac_days * 8  # Total vacation hours
                used = vac_used
                quota_days = annual_quota or 20
            else:  # sick
                remaining_hours_val = max(0, sick_accrued - sick_used)
                remaining_days = remaining_hours_val / 8.0
                accrued = sick_accrued
                used = sick_used
                quota_days = sick_quota
            
            remaining_hours = remaining_hours_val
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
            remaining_days = remaining_hours_val / 8.0
            remaining_hours = remaining_hours_val
        
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
    
    def record_leave_request(self, employee_id: str, leave_type: str, 
                           start_date: date, end_date: date, 
                           days_requested: float, status: str = "approved"):
        """Record a leave request in the database"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        hours_requested = days_requested * 8
        
        cursor.execute("""
            INSERT INTO leave_requests 
            (employee_id, leave_type, start_date, end_date, days_requested, hours_requested, status)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        """, (employee_id, leave_type, start_date.isoformat(), 
              end_date.isoformat(), days_requested, hours_requested, status))
        
        # Update used hours and remaining balance if approved
        if status == "approved":
            # Check which schema we're using
            cursor.execute("PRAGMA table_info(employees)")
            columns = [row[1] for row in cursor.fetchall()]
            
            has_remaining_hours = 'remaining_hours' in columns
            
            if leave_type.lower() == "vacation":
                cursor.execute("""
                    UPDATE employees
                    SET vacation_used_hours = vacation_used_hours + ?
                    WHERE employee_id = ?
                """, (hours_requested, employee_id))
                
                # Also decrement remaining_hours in new schema
                if has_remaining_hours:
                    cursor.execute("""
                        UPDATE employees
                        SET remaining_hours = remaining_hours - ?
                        WHERE employee_id = ?
                    """, (hours_requested, employee_id))
            else:  # sick
                cursor.execute("""
                    UPDATE employees
                    SET sick_used_hours = sick_used_hours + ?
                    WHERE employee_id = ?
                """, (hours_requested, employee_id))
                
                # Note: For sick leave, we typically don't decrement remaining_hours
                # as it's vacation-specific. If you need to track sick separately,
                # you might need a sick_remaining_hours column
        
        conn.commit()
        conn.close()
    
    def initialize_sample_data(self):
        """Initialize database with sample employee data for testing"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Clear existing data
        cursor.execute("DELETE FROM leave_requests")
        cursor.execute("DELETE FROM employees")
        
        # Insert sample employees
        employees = [
            ("EMP001", "John Smith", 2, 10, 8, 80.0, 64.0, 24.0, 8.0),  # 7 days vacation used
            ("EMP002", "Jane Doe", 4, 15, 8, 120.0, 64.0, 0.0, 0.0),    # No vacation used
            ("EMP003", "Bob Johnson", 7, 20, 8, 160.0, 64.0, 40.0, 0.0), # 5 days vacation used
            ("EMP004", "Alice Williams", 1, 10, 8, 80.0, 64.0, 0.0, 0.0), # No vacation used
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
