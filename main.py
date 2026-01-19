"""
Main Demo Script for Corporate Vacation AI Agent
Demonstrates all required features: Tool→RAG flow, conversational UX, policy checks, and email generation
"""

import os
from datetime import date, timedelta
from pathlib import Path
from dotenv import load_dotenv

# Load environment variables from .env file BEFORE importing modules that need OPENAI_API_KEY
# Find .env file in project root
env_path = Path(__file__).parent / '.env'
load_dotenv(dotenv_path=env_path)

from src.vacation_agent import VacationAgent
from src.database_tool import EmployeeDatabase


def print_separator(title: str = ""):
    """Print a formatted separator"""
    if title:
        print(f"\n{'='*70}")
        print(f"  {title}")
        print('='*70)
    else:
        print("\n" + "-"*70)


def demo_balance_query(agent: VacationAgent):
    """Demo: Query employee balance"""
    print_separator("DEMO 1: Balance Query")
    
    employee_id = "EMP001"
    result = agent.query_balance(employee_id, "vacation")
    print(result["message"])
    
    # Also show sick leave balance
    print("\n--- Sick Leave Balance ---")
    result_sick = agent.query_balance(employee_id, "sick")
    print(result_sick["message"])


def demo_approved_request(agent: VacationAgent):
    """Demo: Approved vacation request"""
    print_separator("DEMO 2: Approved Vacation Request")
    
    employee_id = "EMP001"
    # Request 3 days well in advance (compliant request)
    start_date = date(2024, 2, 15)
    end_date = date(2024, 2, 17)  # 3 days
    
    result = agent.process_vacation_request(
        employee_id=employee_id,
        leave_type="vacation",
        start_date=start_date,
        end_date=end_date,
        request_date=date.today() - timedelta(days=21)  # 3 weeks notice
    )
    
    print(result["message"])
    if result["email_content"]:
        print("\n--- Manager Email ---")
        print(result["email_content"])


def demo_60_percent_rule_violation(agent: VacationAgent):
    """Demo: 60% Rule violation"""
    print_separator("DEMO 3: 60% Rule Violation")
    
    employee_id = "EMP001"  # Has 10 days annual quota (max 6 days in single request)
    # Request 7 days - exceeds 60% of 10 days (6 days max)
    start_date = date(2024, 3, 1)
    end_date = date(2024, 3, 7)  # 7 days
    
    result = agent.process_vacation_request(
        employee_id=employee_id,
        leave_type="vacation",
        start_date=start_date,
        end_date=end_date,
        request_date=date.today() - timedelta(days=21)
    )
    
    print(result["message"])
    if result["options"]:
        print("\n--- Suggested Options ---")
        for i, option in enumerate(result["options"], 1):
            print(f"{i}. {option}")


def demo_insufficient_balance(agent: VacationAgent):
    """Demo: Insufficient balance"""
    print_separator("DEMO 4: Insufficient Balance")
    
    employee_id = "EMP001"  # Has ~7 days remaining after previous demo
    # Request more days than available
    start_date = date(2024, 4, 1)
    end_date = date(2024, 4, 10)  # 10 days
    
    result = agent.process_vacation_request(
        employee_id=employee_id,
        leave_type="vacation",
        start_date=start_date,
        end_date=end_date,
        request_date=date.today() - timedelta(days=21)
    )
    
    print(result["message"])
    if result["options"]:
        print("\n--- Suggested Options ---")
        for i, option in enumerate(result["options"], 1):
            print(f"{i}. {option}")


def demo_blackout_period(agent: VacationAgent):
    """Demo: Blackout period violation"""
    print_separator("DEMO 5: Blackout Period Violation")
    
    employee_id = "EMP002"  # Fresh employee with full balance
    # Request dates in Q1 blackout period (March 18-31)
    start_date = date(2024, 3, 20)
    end_date = date(2024, 3, 25)  # 6 days in blackout
    
    result = agent.process_vacation_request(
        employee_id=employee_id,
        leave_type="vacation",
        start_date=start_date,
        end_date=end_date,
        request_date=date.today() - timedelta(days=21)
    )
    
    print(result["message"])
    if result["options"]:
        print("\n--- Suggested Options ---")
        for i, option in enumerate(result["options"], 1):
            print(f"{i}. {option}")


def demo_notice_period_violation(agent: VacationAgent):
    """Demo: Insufficient notice period"""
    print_separator("DEMO 6: Notice Period Violation")
    
    employee_id = "EMP002"
    # Request 5 days with only 10 days notice (need 14 days for >3 days)
    start_date = date.today() + timedelta(days=10)
    end_date = start_date + timedelta(days=4)  # 5 days
    
    result = agent.process_vacation_request(
        employee_id=employee_id,
        leave_type="vacation",
        start_date=start_date,
        end_date=end_date,
        request_date=date.today()
    )
    
    print(result["message"])
    if result["options"]:
        print("\n--- Suggested Options ---")
        for i, option in enumerate(result["options"], 1):
            print(f"{i}. {option}")


def demo_frequency_limit(agent: VacationAgent):
    """Demo: Frequency limit violation"""
    print_separator("DEMO 7: Frequency Limit Violation")
    
    employee_id = "EMP003"  # Has used some vacation
    # First, record two long vacations in the past 60 days
    db = EmployeeDatabase()
    
    # Simulate existing long vacations
    past_date1 = date.today() - timedelta(days=30)
    past_date2 = date.today() - timedelta(days=45)
    
    db.record_leave_request(employee_id, "vacation", past_date1, past_date1 + timedelta(days=8), 9, "approved")
    db.record_leave_request(employee_id, "vacation", past_date2, past_date2 + timedelta(days=10), 11, "approved")
    
    # Now try to request another long vacation within 60 days
    start_date = date.today() + timedelta(days=20)
    end_date = start_date + timedelta(days=8)  # 9 days (long vacation)
    
    result = agent.process_vacation_request(
        employee_id=employee_id,
        leave_type="vacation",
        start_date=start_date,
        end_date=end_date,
        request_date=date.today() - timedelta(days=21)
    )
    
    print(result["message"])
    if result["options"]:
        print("\n--- Suggested Options ---")
        for i, option in enumerate(result["options"], 1):
            print(f"{i}. {option}")


def demo_policy_query(agent: VacationAgent):
    """Demo: Policy explanation via RAG"""
    print_separator("DEMO 8: Policy Query via RAG")
    
    query = "What is the 60% rule for vacation requests?"
    explanation = agent.get_policy_explanation(query)
    print(explanation)


def main():
    """Run all demo scenarios"""
    print("\n" + "="*70)
    print("  CORPORATE VACATION AI AGENT - COMPREHENSIVE DEMO")
    print("="*70)
    print("\nThis demo showcases all features of the unified AI agent:")
    print("  • Tool→RAG flow (Balance check → Policy check)")
    print("  • Conversational UX with proactive options")
    print("  • Policy compliance checks (60% rule, blackout, notice, frequency)")
    print("  • Manager email generation")
    print("  • Balance tracking and remaining balance display")
    
    # Check for API key
    if not os.getenv("OPENAI_API_KEY"):
        print("\n⚠️  WARNING: OPENAI_API_KEY not set. RAG features will not work.")
        print("   Set it using: export OPENAI_API_KEY='your-key-here'")
        print("   Or create a .env file with: OPENAI_API_KEY=your-key-here")
    
    # Initialize agent (will create database if needed)
    print("\nInitializing agent and database...")
    agent = VacationAgent()
    
    # Initialize sample data
    db = EmployeeDatabase()
    try:
        db.initialize_sample_data()
        print("✓ Sample employee data initialized")
    except Exception as e:
        print(f"Note: Database may already exist - {e}")
    
    print("\nStarting demos...")
    
    # Run all demos
    try:
        demo_balance_query(agent)
        demo_approved_request(agent)
        demo_60_percent_rule_violation(agent)
        demo_insufficient_balance(agent)
        demo_blackout_period(agent)
        demo_notice_period_violation(agent)
        demo_frequency_limit(agent)
        demo_policy_query(agent)
        
        print_separator("DEMO COMPLETE")
        print("\n✓ All demo scenarios completed successfully!")
        print("\nThe agent demonstrates:")
        print("  ✓ Tool-first approach (balance queries)")
        print("  ✓ RAG-powered policy compliance checks")
        print("  ✓ Conversational responses with options")
        print("  ✓ Email generation for manager notifications")
        print("  ✓ All business rules enforced (60% rule, blackouts, notice, frequency)")
        
    except Exception as e:
        print(f"\n❌ Error during demo: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()
