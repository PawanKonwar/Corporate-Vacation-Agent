"""
Populate Employees Database Script
Creates and populates employee_data.db with 25 employees across 6 departments
"""

import sqlite3
import random
from datetime import date, timedelta
from pathlib import Path

# Database path
DB_PATH = "data/employee_data.db"

# Department configuration
DEPARTMENTS = {
    "Engineering": {"count": 6, "manager_id": "MGR001", "positions": ["Software Engineer", "Senior Engineer", "Tech Lead", "Architect"]},
    "Marketing": {"count": 5, "manager_id": "MGR002", "positions": ["Marketing Specialist", "Content Manager", "Brand Manager", "Marketing Coordinator"]},
    "Finance": {"count": 4, "manager_id": "MGR003", "positions": ["Financial Analyst", "Accountant", "Senior Analyst", "Finance Manager"]},
    "Operations": {"count": 4, "manager_id": "MGR004", "positions": ["Operations Coordinator", "Operations Analyst", "Process Manager", "Operations Specialist"]},
    "HR": {"count": 2, "manager_id": "MGR005", "positions": ["HR Specialist", "HR Coordinator", "HR Manager"]},
    "IT": {"count": 4, "manager_id": "MGR006", "positions": ["IT Support", "Systems Administrator", "Network Engineer", "IT Manager"]}
}

# Manager information
MANAGERS = {
    "MGR001": {"name": "Robert Chen", "department": "Engineering", "email": "robert.chen@company.com"},
    "MGR002": {"name": "Sarah Williams", "department": "Marketing", "email": "sarah.williams@company.com"},
    "MGR003": {"name": "Michael Brown", "department": "Finance", "email": "michael.brown@company.com"},
    "MGR004": {"name": "Jennifer Davis", "department": "Operations", "email": "jennifer.davis@company.com"},
    "MGR005": {"name": "David Martinez", "department": "HR", "email": "david.martinez@company.com"},
    "MGR006": {"name": "Lisa Anderson", "department": "IT", "email": "lisa.anderson@company.com"}
}

# Sample first and last names for generating realistic names
FIRST_NAMES = [
    "James", "Mary", "John", "Patricia", "Robert", "Jennifer", "Michael", "Linda",
    "William", "Elizabeth", "David", "Barbara", "Richard", "Susan", "Joseph", "Jessica",
    "Thomas", "Sarah", "Christopher", "Karen", "Charles", "Nancy", "Daniel", "Lisa",
    "Matthew", "Betty", "Anthony", "Margaret", "Mark", "Sandra", "Donald", "Ashley"
]

LAST_NAMES = [
    "Smith", "Johnson", "Williams", "Brown", "Jones", "Garcia", "Miller", "Davis",
    "Rodriguez", "Martinez", "Hernandez", "Lopez", "Wilson", "Anderson", "Thomas", "Taylor",
    "Moore", "Jackson", "Martin", "Lee", "Thompson", "White", "Harris", "Clark",
    "Lewis", "Robinson", "Walker", "Young", "King", "Wright", "Scott", "Torres"
]


def generate_name(used_names):
    """Generate a unique full name"""
    while True:
        first = random.choice(FIRST_NAMES)
        last = random.choice(LAST_NAMES)
        full_name = f"{first} {last}"
        if full_name not in used_names:
            used_names.add(full_name)
            return full_name


def generate_email(name):
    """Generate email from name (first.last@company.com)"""
    parts = name.lower().split()
    if len(parts) == 2:
        return f"{parts[0]}.{parts[1]}@company.com"
    return f"{name.lower().replace(' ', '.')}@company.com"


def generate_start_date():
    """Generate random start date between 2020-2024"""
    start_year = 2020
    end_year = 2024
    year = random.randint(start_year, end_year)
    month = random.randint(1, 12)
    day = random.randint(1, 28)  # Use 28 to avoid month-end issues
    return date(year, month, day)


def create_employees_table(conn):
    """Drop existing tables and create a fresh employees table"""
    cursor = conn.cursor()
    
    # Drop existing tables if they exist
    print("  Dropping existing tables...")
    cursor.execute("DROP TABLE IF EXISTS employees_new")
    cursor.execute("DROP TABLE IF EXISTS employees")
    cursor.execute("DROP TABLE IF EXISTS leave_requests")  # Also drop this to avoid FK issues
    conn.commit()
    print("  ✓ Existing tables dropped")
    
    # Create fresh employees table
    cursor.execute("""
        CREATE TABLE employees (
            employee_id TEXT PRIMARY KEY,
            name TEXT NOT NULL,
            vacation_days INTEGER NOT NULL,
            remaining_hours INTEGER NOT NULL,
            email TEXT UNIQUE NOT NULL,
            department TEXT NOT NULL,
            position TEXT NOT NULL,
            start_date DATE NOT NULL,
            manager_id TEXT,
            annual_quota INTEGER NOT NULL DEFAULT 20,
            FOREIGN KEY (manager_id) REFERENCES employees(employee_id)
        )
    """)
    
    # Recreate leave_requests table for the app
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
    print("  ✓ Fresh employees table created")


def insert_managers(conn):
    """Insert manager records first"""
    cursor = conn.cursor()
    
    for manager_id, manager_info in MANAGERS.items():
        # Managers get 25 vacation days
        vacation_days = 25
        remaining_hours = vacation_days * 8
        
        try:
            cursor.execute("""
                INSERT INTO employees 
                (employee_id, name, vacation_days, remaining_hours, email, department, position, start_date, manager_id, annual_quota)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                manager_id,
                manager_info["name"],
                vacation_days,
                remaining_hours,
                manager_info["email"],
                manager_info["department"],
                "Department Manager",
                date(2019, 1, 15),  # Managers started earlier
                None,  # Managers don't have managers
                20
            ))
        except sqlite3.IntegrityError:
            print(f"  ⚠ Manager {manager_id} already exists, skipping...")
    
    conn.commit()
    print(f"✓ Inserted {len(MANAGERS)} managers")


def insert_employees(conn):
    """Insert employee records"""
    cursor = conn.cursor()
    used_names = set(MANAGERS[mg]["name"] for mg in MANAGERS)  # Exclude manager names
    used_emails = set(MANAGERS[mg]["email"] for mg in MANAGERS)  # Exclude manager emails
    employee_counter = 1
    all_employees = []
    
    for dept_name, dept_info in DEPARTMENTS.items():
        manager_id = dept_info["manager_id"]
        positions = dept_info["positions"]
        count = dept_info["count"]
        
        for i in range(count):
            # Generate employee ID
            emp_id = f"EMP{employee_counter:03d}"
            employee_counter += 1
            
            # Generate unique name
            name = generate_name(used_names)
            
            # Generate unique email
            email = generate_email(name)
            # Ensure email uniqueness
            while email in used_emails:
                name = generate_name(used_names)
                email = generate_email(name)
            used_emails.add(email)
            
            # Assign position (non-manager positions)
            position = random.choice([p for p in positions if "Manager" not in p])
            
            # Vacation days: 12-24 for employees, 25 for managers
            vacation_days = random.randint(12, 24)
            remaining_hours = vacation_days * 8
            
            # Start date
            start_date = generate_start_date()
            
            all_employees.append({
                "employee_id": emp_id,
                "name": name,
                "vacation_days": vacation_days,
                "remaining_hours": remaining_hours,
                "email": email,
                "department": dept_name,
                "position": position,
                "start_date": start_date,
                "manager_id": manager_id,
                "annual_quota": 20
            })
    
    # Insert all employees
    for emp in all_employees:
        try:
            cursor.execute("""
                INSERT INTO employees 
                (employee_id, name, vacation_days, remaining_hours, email, department, position, start_date, manager_id, annual_quota)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                emp["employee_id"],
                emp["name"],
                emp["vacation_days"],
                emp["remaining_hours"],
                emp["email"],
                emp["department"],
                emp["position"],
                emp["start_date"],
                emp["manager_id"],
                emp["annual_quota"]
            ))
        except sqlite3.IntegrityError as e:
            print(f"  ⚠ Employee {emp['employee_id']} already exists, skipping...")
    
    conn.commit()
    print(f"✓ Inserted {len(all_employees)} employees")
    return all_employees


def display_statistics(conn):
    """Display database statistics"""
    cursor = conn.cursor()
    
    # Total employees
    cursor.execute("SELECT COUNT(*) FROM employees")
    total = cursor.fetchone()[0]
    
    # Count by department
    cursor.execute("""
        SELECT department, COUNT(*) as count 
        FROM employees 
        GROUP BY department 
        ORDER BY department
    """)
    dept_counts = cursor.fetchall()
    
    # Sample employees
    cursor.execute("""
        SELECT employee_id, name, department, position, vacation_days, email
        FROM employees
        ORDER BY RANDOM()
        LIMIT 5
    """)
    samples = cursor.fetchall()
    
    print("\n" + "="*70)
    print("DATABASE STATISTICS")
    print("="*70)
    print(f"\n✓ Total Employees: {total}")
    
    print("\n✓ Employees by Department:")
    print("-" * 70)
    for dept, count in dept_counts:
        print(f"  {dept:20s}: {count:2d} employees")
    
    print("\n✓ Sample Employees (5 random):")
    print("-" * 70)
    print(f"{'ID':<10} {'Name':<25} {'Department':<15} {'Position':<20} {'Days':<5} {'Email'}")
    print("-" * 70)
    for emp_id, name, dept, pos, days, email in samples:
        print(f"{emp_id:<10} {name:<25} {dept:<15} {pos:<20} {days:<5} {email}")
    
    print("\n" + "="*70)


def main():
    """Main execution function"""
    print("="*70)
    print("EMPLOYEE DATABASE POPULATION SCRIPT")
    print("="*70)
    print(f"\nDatabase: {DB_PATH}")
    
    # Ensure data directory exists
    Path("data").mkdir(exist_ok=True)
    
    # Connect to database
    conn = sqlite3.connect(DB_PATH)
    
    try:
        # Create fresh table (drops existing)
        print("\n1. Creating fresh employees table...")
        create_employees_table(conn)
        
        # Insert managers
        print("\n2. Inserting managers...")
        insert_managers(conn)
        
        # Insert employees
        print("\n3. Inserting employees...")
        employees = insert_employees(conn)
        
        # Display statistics
        display_statistics(conn)
        
        # Verify record count
        cursor = conn.cursor()
        cursor.execute("SELECT COUNT(*) FROM employees")
        record_count = cursor.fetchone()[0]
        
        if record_count == 31:
            print(f"\n✅ Database population completed successfully!")
            print(f"✅ Verification: Database contains exactly {record_count} records (31 expected)")
        else:
            print(f"\n⚠️  Warning: Database contains {record_count} records, expected 31")
        
    except Exception as e:
        print(f"\n❌ Error: {str(e)}")
        conn.rollback()
        raise
    finally:
        conn.close()


if __name__ == "__main__":
    main()
