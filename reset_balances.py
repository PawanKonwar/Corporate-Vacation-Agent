"""
Reset Employee Balances Script
Resets all employees to fresh starting values:
- Vacation: Original allocation (vacation_days from database)
- Sick: 64 hours accrued, 0 used
- Clear all used hours
- Archive existing requests
"""

import sqlite3
from pathlib import Path
from datetime import datetime

DB_PATH = "data/employee_data.db"


def archive_leave_requests(conn):
    """Move existing leave requests to an archive table"""
    cursor = conn.cursor()
    
    # Create archive table if it doesn't exist
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS leave_requests_archive (
            request_id INTEGER PRIMARY KEY,
            employee_id TEXT NOT NULL,
            leave_type TEXT NOT NULL,
            start_date DATE NOT NULL,
            end_date DATE NOT NULL,
            days_requested INTEGER NOT NULL,
            hours_requested REAL NOT NULL,
            status TEXT DEFAULT 'approved',
            request_date DATE DEFAULT CURRENT_DATE,
            archived_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)
    
    # Copy all requests to archive
    cursor.execute("""
        INSERT INTO leave_requests_archive 
        (request_id, employee_id, leave_type, start_date, end_date, 
         days_requested, hours_requested, status, request_date)
        SELECT request_id, employee_id, leave_type, start_date, end_date,
               days_requested, hours_requested, status, request_date
        FROM leave_requests
    """)
    
    archived_count = cursor.rowcount
    
    # Clear current requests table
    cursor.execute("DELETE FROM leave_requests")
    
    conn.commit()
    print(f"  ✓ Archived {archived_count} leave requests")
    return archived_count


def reset_employee_balances(conn):
    """Reset all employee balances to original values"""
    cursor = conn.cursor()
    
    # Get all employees with their original vacation_days
    cursor.execute("""
        SELECT employee_id, name, vacation_days 
        FROM employees 
        ORDER BY employee_id
    """)
    employees = cursor.fetchall()
    
    reset_count = 0
    
    for emp_id, name, original_vacation_days in employees:
        # Calculate original remaining_hours from vacation_days
        original_remaining_hours = original_vacation_days * 8
        
        # Update employee balance
        cursor.execute("""
            UPDATE employees
            SET remaining_hours = ?,
                vacation_used_hours = 0.0,
                sick_used_hours = 0.0,
                sick_accrued_hours = 64.0
            WHERE employee_id = ?
        """, (original_remaining_hours, emp_id))
        
        reset_count += 1
    
    conn.commit()
    print(f"  ✓ Reset balances for {reset_count} employees")
    
    # Verify the reset
    cursor.execute("""
        SELECT employee_id, name, vacation_days, remaining_hours, 
               vacation_used_hours, sick_used_hours, sick_accrued_hours
        FROM employees
        LIMIT 5
    """)
    sample = cursor.fetchall()
    
    print("\n  Sample reset results:")
    print("  " + "-" * 90)
    print(f"  {'ID':<10} {'Name':<20} {'Vac Days':<10} {'Rem Hrs':<10} {'Used Hrs':<10} {'Sick Acc':<10}")
    print("  " + "-" * 90)
    for row in sample:
        emp_id, name, vac_days, rem_hrs, used_hrs, sick_used, sick_acc = row
        print(f"  {emp_id:<10} {name[:18]:<20} {vac_days:<10} {rem_hrs:<10} {used_hrs or 0:<10} {sick_acc or 64:<10}")
    
    return reset_count


def verify_reset(conn):
    """Verify all balances are reset correctly"""
    cursor = conn.cursor()
    
    # Check for any employees with incorrect balances
    cursor.execute("""
        SELECT employee_id, name, vacation_days, remaining_hours,
               vacation_used_hours, sick_used_hours
        FROM employees
        WHERE remaining_hours != (vacation_days * 8)
           OR (vacation_used_hours IS NOT NULL AND vacation_used_hours != 0)
           OR (sick_used_hours IS NOT NULL AND sick_used_hours != 0)
    """)
    
    issues = cursor.fetchall()
    
    if issues:
        print("\n  ⚠️  WARNING: Found employees with incorrect balances:")
        for row in issues:
            print(f"    {row[0]}: {row[1]} - Expected {row[2]*8} hours, got {row[3]}")
        return False
    else:
        print("\n  ✅ All balances verified correctly!")
        return True


def main():
    """Main function to reset all balances"""
    print("=" * 70)
    print("EMPLOYEE BALANCE RESET SCRIPT")
    print("=" * 70)
    
    db_path = Path(DB_PATH)
    if not db_path.exists():
        print(f"\n❌ Error: Database not found at {DB_PATH}")
        return
    
    conn = sqlite3.connect(DB_PATH)
    
    try:
        # Phase 1: Archive existing requests
        print("\n[PHASE 1] Archiving existing leave requests...")
        archived_count = archive_leave_requests(conn)
        
        # Phase 2: Reset all balances
        print("\n[PHASE 2] Resetting employee balances...")
        reset_count = reset_employee_balances(conn)
        
        # Phase 3: Verify
        print("\n[PHASE 3] Verifying reset...")
        verify_reset(conn)
        
        # Summary
        print("\n" + "=" * 70)
        print("RESET SUMMARY")
        print("=" * 70)
        print(f"  • Employees reset: {reset_count}")
        print(f"  • Requests archived: {archived_count}")
        print(f"  • Sick leave: All set to 64 hours accrued, 0 used")
        print(f"  • Vacation leave: All reset to original allocation")
        print("\n✅ Balance reset completed successfully!")
        print("=" * 70)
        
    except Exception as e:
        print(f"\n❌ Error during reset: {str(e)}")
        conn.rollback()
        raise
    finally:
        conn.close()


if __name__ == "__main__":
    main()
