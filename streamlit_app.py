"""
Corporate Vacation AI Agent - Web UI
Professional Streamlit dashboard for employee leave requests
"""

import streamlit as st
import os
import sqlite3
import pandas as pd
from datetime import date, timedelta, datetime
from pathlib import Path
from dotenv import load_dotenv

# Load environment variables
env_path = Path(__file__).parent / '.env'
load_dotenv(dotenv_path=env_path)

from src.vacation_agent import VacationAgent
from src.database_tool import EmployeeDatabase

# Page configuration
st.set_page_config(
    page_title="Corporate Vacation AI Agent",
    page_icon="🏢",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Enhanced Modern CSS
st.markdown("""
    <style>
        /* Hide default Streamlit elements */
        #MainMenu {visibility: hidden;}
        footer {visibility: hidden;}
        header {visibility: hidden;}
        
        /* Main header with gradient */
        .main-header {
            font-size: 3rem;
            font-weight: 800;
            background: linear-gradient(135deg, #1f4e79 0%, #4a90e2 100%);
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
            text-align: center;
            margin-bottom: 0.5rem;
            letter-spacing: -0.5px;
        }
        
        .sub-header {
            font-size: 1.2rem;
            color: #64748b;
            text-align: center;
            margin-bottom: 3rem;
            font-weight: 400;
        }
        
        /* Modern card styling */
        .stCard {
            background: white;
            padding: 2rem;
            border-radius: 16px;
            box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.1), 0 2px 4px -1px rgba(0, 0, 0, 0.06);
            border: 1px solid #e2e8f0;
            margin-bottom: 1.5rem;
        }
        
        /* Enhanced form container - bordered */
        .form-container {
            background: linear-gradient(135deg, #f8fafc 0%, #ffffff 100%);
            padding: 2.5rem;
            border-radius: 20px;
            box-shadow: 0 10px 25px -5px rgba(0, 0, 0, 0.1);
            border: 2px solid #cbd5e1;
            border-left: 5px solid #1e40af;
        }
        /* Form section headers with icons */
        .form-section-header {
            font-size: 1rem;
            font-weight: 600;
            color: #1e40af;
            margin-bottom: 0.75rem;
            padding: 0.5rem 0;
            border-bottom: 1px solid #e2e8f0;
            display: flex;
            align-items: center;
            gap: 0.5rem;
        }
        
        /* Modern flow step cards */
        .flow-step {
            padding: 1.5rem;
            border-radius: 12px;
            margin: 1rem 0;
            background: linear-gradient(135deg, #f0f7ff 0%, #e6f3ff 100%);
            border-left: 5px solid #1f4e79;
            box-shadow: 0 2px 8px rgba(31, 78, 121, 0.1);
            transition: transform 0.2s, box-shadow 0.2s;
        }
        
        .flow-step:hover {
            transform: translateX(5px);
            box-shadow: 0 4px 12px rgba(31, 78, 121, 0.15);
        }
        
        .flow-step.active {
            background: linear-gradient(135deg, #e6f3ff 0%, #cce7ff 100%);
            border-left-color: #4a90e2;
            animation: pulse 2s infinite;
        }
        
        .flow-step.completed {
            background: linear-gradient(135deg, #d4edda 0%, #c3e6cb 100%);
            border-left-color: #28a745;
        }
        
        .flow-step.error {
            background: linear-gradient(135deg, #f8d7da 0%, #f5c6cb 100%);
            border-left-color: #dc3545;
        }
        
        @keyframes pulse {
            0%, 100% { opacity: 1; }
            50% { opacity: 0.8; }
        }
        
        /* Status badges */
        .status-badge {
            display: inline-block;
            padding: 0.5rem 1rem;
            border-radius: 20px;
            font-size: 0.875rem;
            font-weight: 600;
            margin: 0.5rem 0;
        }
        
        .badge-approved {
            background: #d4edda;
            color: #155724;
        }
        
        .badge-denied {
            background: #f8d7da;
            color: #721c24;
        }
        
        /* Enhanced result boxes */
        .result-box {
            padding: 2rem;
            border-radius: 16px;
            margin: 1.5rem 0;
            box-shadow: 0 4px 12px rgba(0, 0, 0, 0.1);
        }
        
        .approved-box {
            background: linear-gradient(135deg, #d4edda 0%, #c3e6cb 100%);
            border: 2px solid #28a745;
            border-left: 6px solid #28a745;
        }
        
        .denied-box {
            background: linear-gradient(135deg, #f8d7da 0%, #f5c6cb 100%);
            border: 2px solid #dc3545;
            border-left: 6px solid #dc3545;
        }
        
        /* Modern violation/option items */
        .violation-item {
            padding: 1.25rem;
            margin: 0.75rem 0;
            background: linear-gradient(135deg, #fff3cd 0%, #ffe69c 100%);
            border-left: 4px solid #ffc107;
            border-radius: 10px;
            box-shadow: 0 2px 4px rgba(255, 193, 7, 0.2);
        }
        
        .option-item {
            padding: 1.25rem;
            margin: 0.75rem 0;
            background: linear-gradient(135deg, #e7f3ff 0%, #d0e7ff 100%);
            border-left: 4px solid #4a90e2;
            border-radius: 10px;
            box-shadow: 0 2px 4px rgba(74, 144, 226, 0.2);
            transition: transform 0.2s;
        }
        
        .option-item:hover {
            transform: translateX(5px);
        }
        
        /* Enhanced email preview */
        .email-preview {
            padding: 1.5rem;
            background: #f8f9fa;
            border: 2px solid #dee2e6;
            border-radius: 12px;
            font-family: 'Courier New', monospace;
            font-size: 0.9rem;
            white-space: pre-wrap;
            box-shadow: inset 0 2px 4px rgba(0, 0, 0, 0.05);
        }
        
        /* Metric cards */
        .metric-card {
            background: white;
            padding: 1.5rem;
            border-radius: 12px;
            box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
            border: 1px solid #e2e8f0;
            transition: transform 0.2s, box-shadow 0.2s;
        }
        
        .metric-card:hover {
            transform: translateY(-2px);
            box-shadow: 0 8px 12px rgba(0, 0, 0, 0.15);
        }
        
        /* Sidebar enhancements */
        .sidebar-section {
            background: white;
            padding: 1.5rem;
            border-radius: 12px;
            margin-bottom: 1.5rem;
            box-shadow: 0 2px 4px rgba(0, 0, 0, 0.05);
            border: 1px solid #e2e8f0;
        }
        
        /* Employee card styling */
        .employee-card {
            padding: 0.75rem 1rem;
            margin: 0.5rem 0;
            background: #f8fafc;
            border-left: 3px solid #4a90e2;
            border-radius: 8px;
            font-size: 0.9rem;
            transition: all 0.2s;
        }
        
        .employee-card:hover {
            background: #e6f3ff;
            transform: translateX(5px);
        }
        
        /* Button enhancements */
        .stButton > button {
            border-radius: 10px;
            font-weight: 600;
            padding: 0.75rem 1.5rem;
            transition: all 0.3s;
        }
        
        .stButton > button:hover {
            transform: translateY(-2px);
            box-shadow: 0 4px 8px rgba(0, 0, 0, 0.15);
        }
        
        /* Input enhancements */
        .stTextInput > div > div > input {
            border-radius: 8px;
            border: 2px solid #e2e8f0;
        }
        
        .stTextInput > div > div > input:focus {
            border-color: #4a90e2;
            box-shadow: 0 0 0 3px rgba(74, 144, 226, 0.1);
        }
        
        /* Section headers */
        .section-header {
            font-size: 1.5rem;
            font-weight: 700;
            color: #1f4e79;
            margin: 2rem 0 1rem 0;
            padding-bottom: 0.5rem;
            border-bottom: 3px solid #4a90e2;
        }
        
        /* Improved spacing */
        .main-container {
            padding: 2rem 0;
        }
        
        /* Flow connector */
        .flow-connector {
            text-align: center;
            color: #94a3b8;
            font-size: 1.5rem;
            margin: -0.5rem 0;
        }
        
        /* Analysis check cards */
        .analysis-check-card {
            padding: 1rem;
            margin: 0.5rem 0;
            border-radius: 8px;
            border-left: 4px solid;
            background: #f8fafc;
            transition: transform 0.2s;
        }
        
        .analysis-check-card:hover {
            transform: translateX(5px);
        }
        
        /* Option cards */
        .option-card {
            position: relative;
            padding: 1.5rem;
            margin: 0.5rem 0;
            border-radius: 12px;
            border: 2px solid;
            background: linear-gradient(135deg, #ffffff 0%, #f8fafc 100%);
            box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.1);
            transition: transform 0.2s, box-shadow 0.2s;
            cursor: pointer;
        }
        
        .option-card:hover {
            transform: translateY(-2px);
            box-shadow: 0 8px 12px -2px rgba(0, 0, 0, 0.15);
        }
        
        .option-card.recommended {
            border-color: #f59e0b;
            background: linear-gradient(135deg, #fffbeb 0%, #fef3c7 100%);
        }
        
        /* Conflict resolution cards */
        .conflict-card {
            padding: 1.5rem;
            margin: 1rem 0;
            border-radius: 12px;
            background: linear-gradient(135deg, #fee2e2 0%, #fecaca 100%);
            border-left: 5px solid #ef4444;
        }
    </style>
""", unsafe_allow_html=True)

# Initialize all session state variables in one place
def _init_session_state():
    defaults = {
        "request_result": None,
        "processing_steps": [],
        "employee_email_draft": None,
        "email_sent_status": None,
        "email_custom_message": "",
        "show_alternatives": False,
        "show_split_form": False,
        "show_better_dates": False,
        "show_balance": False,
        "show_policy": False,
        "selected_employee_id": None,
        "selected_employee_index": 0,
    }
    for key, val in defaults.items():
        if key not in st.session_state:
            st.session_state[key] = val

_init_session_state()

if "agent" not in st.session_state:
    with st.spinner("Initializing AI Agent..."):
        try:
            st.session_state.agent = VacationAgent()
            st.session_state.db = EmployeeDatabase()
            if not os.path.exists("data/employee_data.db") or os.path.getsize("data/employee_data.db") == 0:
                st.session_state.db.initialize_sample_data()
        except Exception as e:
            st.error(f"Error initializing agent: {str(e)}")
            st.stop()

# Enhanced Header
st.markdown('<h1 class="main-header">🏢 Corporate Vacation AI Agent</h1>', unsafe_allow_html=True)
st.markdown('<p class="sub-header">Unified AI-powered leave management system with Tool → RAG integration</p>', unsafe_allow_html=True)

# Enhanced Sidebar
with st.sidebar:
    # Employee Directory with search (at top)
    st.markdown('### 👥 Employee Directory')
    search_query = st.text_input("Search", placeholder="Search employee...", key="emp_search", label_visibility="collapsed")
    st.write("")
    
    try:
        conn_dir = sqlite3.connect("data/employee_data.db")
        cur_dir = conn_dir.cursor()
        cur_dir.execute("""
            SELECT employee_id, name, department, COALESCE(remaining_hours, 0) as remaining_hours
            FROM employees
            ORDER BY employee_id
        """)
        dir_employees = cur_dir.fetchall()
        conn_dir.close()
        
        search_lower = (search_query or "").strip().lower()
        if search_lower:
            filtered = [
                e for e in dir_employees
                if search_lower in (e[0] or "").lower()
                or search_lower in (e[1] or "").lower()
                or search_lower in (str(e[2] or "")).lower()
            ]
        else:
            filtered = dir_employees
        
        for emp in filtered[:20]:  # Limit to 20 for performance
            emp_id, name, dept, rem_hrs = emp
            rem_days = round(rem_hrs / 8.0, 1)
            with st.expander(f"**{emp_id}** · {name}"):
                st.markdown(f"**ID:** {emp_id}")
                st.markdown(f"**Name:** {name}")
                st.markdown(f"**Remaining Days:** {rem_days}")
                st.markdown(f"**Department:** {dept or '—'}")
        if not filtered:
            st.caption("No employees match your search.")
    except Exception as ex:
        st.caption(f"Directory unavailable: {str(ex)}")
    
    st.markdown("---")
    
    st.markdown('<div class="sidebar-section">', unsafe_allow_html=True)
    st.markdown('### 🚀 Quick Actions')
    st.markdown('</div>', unsafe_allow_html=True)
    
    # Table of all employees with remaining leave days (at top for visibility)
    st.markdown('### 📊 All Employees - Leave Balance')
    try:
        conn_tbl = sqlite3.connect("data/employee_data.db")
        cur_tbl = conn_tbl.cursor()
        cur_tbl.execute("""
            SELECT employee_id, COALESCE(remaining_hours, 0) as remaining_hours
            FROM employees
            ORDER BY employee_id
        """)
        emp_rows = cur_tbl.fetchall()
        conn_tbl.close()
        if emp_rows:
            emp_data = [(r[0], round(r[1] / 8.0, 1)) for r in emp_rows]
            df_emp = pd.DataFrame(emp_data, columns=["Employee ID", "Remaining Days"])
            st.dataframe(df_emp, use_container_width=True, hide_index=True)
        else:
            st.caption("No employees in database. Run populate_employees.py first.")
    except Exception as ex:
        st.warning(f"Table unavailable: {str(ex)}")
    
    st.markdown("---")
    
    col1, col2 = st.columns(2)
    with col1:
        if st.button("💰", use_container_width=True, help="Check Balance"):
            st.session_state.show_balance = True
    with col2:
        if st.button("📄", use_container_width=True, help="View Policy"):
            st.session_state.show_policy = True
    
    st.markdown("---")
    
    st.markdown('<div class="sidebar-section">', unsafe_allow_html=True)
    st.markdown('### 👥 Employees')
    
    # Fetch all employees from database
    FALLBACK_EMPLOYEES = [
        ("EMP001", "John Smith", "Engineering", "Developer", 14, 112.0),
        ("EMP002", "Jane Doe", "Marketing", "Specialist", 15, 120.0),
        ("EMP003", "Bob Johnson", "Finance", "Analyst", 10, 80.0),
        ("EMP004", "Alice Williams", "HR", "Coordinator", 10, 80.0),
    ]
    try:
        conn = sqlite3.connect("data/employee_data.db")
        cursor = conn.cursor()
        
        # Get total count
        cursor.execute("SELECT COUNT(*) FROM employees")
        total_count = cursor.fetchone()[0]
        
        # Get department breakdown
        cursor.execute("""
            SELECT department, COUNT(*) as count 
            FROM employees 
            GROUP BY department 
            ORDER BY department
        """)
        dept_counts = cursor.fetchall()
        
        # Get all employees with details
        cursor.execute("""
            SELECT employee_id, name, department, position, vacation_days, remaining_hours
            FROM employees
            ORDER BY employee_id
        """)
        all_employees = cursor.fetchall()
        conn.close()
    except Exception as e:
        st.warning(f"Could not load employees: {str(e)}")
        st.caption("Using sample data.")
        all_employees = FALLBACK_EMPLOYEES
        total_count = len(all_employees)
        dept_counts = [("Sample", total_count)]
    
    # Display total count and employee list (uses all_employees from try or fallback)
    st.markdown(f'**Total Employees: {total_count}**')
    dept_breakdown = ", ".join([f"{dept} ({count})" for dept, count in dept_counts])
    st.markdown(f'<small style="color: #64748b;">📊 Departments: {dept_breakdown}</small>', unsafe_allow_html=True)
    st.markdown("---")
    
    employee_options = {f"{emp[0]} - {emp[1]} ({emp[2]})": emp[0] for emp in all_employees}
    employee_labels = list(employee_options.keys())
    default_index = 0
    if 'selected_employee_index' in st.session_state:
        try:
            default_index = st.session_state.selected_employee_index
            if default_index >= len(employee_labels):
                default_index = 0
        except:
            default_index = 0
    
    selected_employee_label = st.selectbox(
        "Select Employee:",
        options=employee_labels,
        index=default_index,
        key="employee_selector",
        help="Select an employee to view their details or submit a request"
    )
    selected_employee_id = employee_options[selected_employee_label]
    st.session_state.selected_employee_id = selected_employee_id
    st.session_state.selected_employee_index = employee_labels.index(selected_employee_label)
    
    selected_emp = next((e for e in all_employees if e[0] == selected_employee_id), None)
    if selected_emp:
        emp_id, emp_name, emp_dept, emp_pos, emp_vac_days, emp_rem_hrs = selected_emp
        st.markdown(f"""
        <div class="employee-card" style="background: #e6f3ff; border-left: 4px solid #4a90e2;">
            <strong>{emp_id}</strong> - {emp_name}<br>
            <small>📁 {emp_dept} | {emp_pos}</small><br>
            <small>📅 {emp_vac_days} days ({emp_rem_hrs} hours) remaining</small>
        </div>
        """, unsafe_allow_html=True)
    
    st.markdown("---")
    with st.expander(f"📋 View All Employees ({total_count} total)"):
        st.markdown(f'<small style="color: #64748b;">All {total_count} employees from database</small>', unsafe_allow_html=True)
        for emp_id, emp_name, emp_dept, emp_pos, emp_vac_days, emp_rem_hrs in all_employees:
            is_manager = emp_id.startswith("MGR")
            card_color = "#fff3cd" if is_manager else "#f8fafc"
            border_color = "#ffc107" if is_manager else "#4a90e2"
            badge = "👑" if is_manager else "👤"
            st.markdown(f'''
            <div class="employee-card" style="background: {card_color}; border-left: 3px solid {border_color}; margin: 0.25rem 0;">
                {badge} <strong>{emp_id}</strong> - {emp_name}<br>
                <small>📁 {emp_dept} | 💼 {emp_pos} | 📅 {emp_vac_days} days ({emp_rem_hrs} hrs)</small>
            </div>
            ''', unsafe_allow_html=True)
    
    st.markdown('</div>', unsafe_allow_html=True)
    
    st.markdown("---")
    
    st.markdown('<div class="sidebar-section">', unsafe_allow_html=True)
    st.markdown('### 🔄 System Flow')
    st.markdown("""
    <div style="line-height: 2;">
        <strong>1.</strong> 🔍 Tool Query<br>
        <span style="color: #94a3b8;">Check balance</span><br><br>
        <strong>2.</strong> 🧠 RAG Query<br>
        <span style="color: #94a3b8;">Check policy</span><br><br>
        <strong>3.</strong> ✅ Decision<br>
        <span style="color: #94a3b8;">Approve/Deny</span>
    </div>
    """, unsafe_allow_html=True)
    st.markdown('</div>', unsafe_allow_html=True)

# Main Content
col1, col2 = st.columns([1.2, 1])

with col1:
    show_balance = st.toggle("👁️ Show Balance", value=False, key="balance_toggle")
    
    # Your Current Leave Balance section (outside form)
    bal_employee_id = st.session_state.get("selected_employee_id")
    if show_balance and bal_employee_id:
        st.markdown("### 📊 Your Current Leave Balance")
        try:
            balance = st.session_state.db.get_remaining_balance(bal_employee_id, "vacation")
            if "error" not in balance:
                bal_col1, bal_col2, bal_col3 = st.columns(3)
                with bal_col1:
                    st.metric("📅 Remaining Days", f"{balance['remaining_days']:.1f}", help="Days of leave available")
                with bal_col2:
                    st.metric("⏱️ Remaining Hours", f"{balance['remaining_hours']:.0f}", help="Hours of leave available")
                with bal_col3:
                    st.metric("📋 Annual Quota", f"{balance['annual_quota_days']} days", help="Total annual allowance")
            else:
                st.warning(f"Could not load balance: {balance.get('error', 'Unknown error')}")
        except Exception as e:
            st.warning(f"Balance unavailable: {str(e)}")
    elif show_balance and not bal_employee_id:
        st.info("👈 **Please select an employee from the sidebar first**")
        st.caption("Your leave balance will appear here")
    st.write("")
    
    st.markdown('<div class="form-container">', unsafe_allow_html=True)
    
    with st.form("leave_request_form", clear_on_submit=False):
        st.header("📝 Submit Leave Request")
        st.write("")
        
        left_col, right_col = st.columns(2)
        
        with left_col:
            st.markdown('<div class="form-section-header">👤 Employee & Leave Type</div>', unsafe_allow_html=True)
            st.write("")
            selected_emp_id = st.session_state.get("selected_employee_id") or ""
            emp_col1, emp_col2 = st.columns([3, 1])
            with emp_col1:
                employee_id = st.text_input(
                    "👤 Employee ID",
                    placeholder="e.g., EMP001",
                    value=selected_emp_id,
                    key="employee_id_input",
                    help="Enter your employee ID or select from sidebar"
                )
            with emp_col2:
                st.write("")
                if st.form_submit_button("🔍", help="Quick lookup", use_container_width=True):
                    st.session_state.show_balance = True
            st.write("")
            leave_type = st.selectbox("📋 Leave Type", ["vacation", "sick"], help="Select vacation or sick leave")
            st.write("")
            is_manager_request = st.checkbox(
                "👑 Manager's leave request (auto-approve)",
                value=employee_id.startswith("MGR") if employee_id else False,
                help="Managers' leave requests are auto-approved per company policy"
            )
        
        with right_col:
            st.markdown('<div class="form-section-header">📅 Requested Dates</div>', unsafe_allow_html=True)
            st.write("")
            start_date = st.date_input("📅 Start Date", value=date.today() + timedelta(days=14), help="First day of leave")
            st.write("")
            end_date = st.date_input("📅 End Date", value=date.today() + timedelta(days=17), help="Last day of leave")
            st.write("")
            if start_date and end_date:
                days_requested = (end_date - start_date).days + 1
                biz_days = sum(1 for i in range(days_requested) if (start_date + timedelta(days=i)).weekday() < 5) if days_requested > 0 else 0
                st.info(f"📊 **{days_requested}** calendar day{'s' if days_requested != 1 else ''} · **{biz_days}** business day{'s' if biz_days != 1 else ''}")
        
        st.write("")
        st.write("")
        btn_col1, btn_col2, btn_col3 = st.columns([1, 2, 1])
        with btn_col2:
            submitted = st.form_submit_button("🚀 Process Request", use_container_width=True, type="primary")
        
        if submitted:
            if end_date < start_date:
                st.error("❌ End date must be after start date")
            else:
                with st.spinner("⏳ Processing your request..."):
                    try:
                        st.session_state.processing_steps = []
                        
                        days_requested = (end_date - start_date).days + 1
                        
                        # Check if manager request - different flow
                        if is_manager_request or employee_id.startswith("MGR"):
                            # Manager auto-approval flow
                            st.session_state.processing_steps.append({
                                "step": 1,
                                "name": "Manager Verification",
                                "status": "completed",
                                "message": f"Manager identified: {employee_id}"
                            })
                            
                            st.session_state.processing_steps.append({
                                "step": 2,
                                "name": "Auto-Approval",
                                "status": "completed",
                                "message": "Manager leave auto-approved per policy. HR notified for tracking."
                            })
                            
                            try:
                                result = st.session_state.agent.process_vacation_request(
                                    employee_id=employee_id,
                                    leave_type=leave_type,
                                    start_date=start_date,
                                    end_date=end_date,
                                    is_manager=True
                                )
                            except TypeError as e:
                                if "is_manager" in str(e):
                                    # Agent was initialized with old code - reinitialize it
                                    st.warning("🔄 Reloading agent with latest code...")
                                    import importlib
                                    import src.vacation_agent
                                    importlib.reload(src.vacation_agent)
                                    from src.vacation_agent import VacationAgent
                                    st.session_state.agent = VacationAgent()
                                    # Retry the request
                                    result = st.session_state.agent.process_vacation_request(
                                        employee_id=employee_id,
                                        leave_type=leave_type,
                                        start_date=start_date,
                                        end_date=end_date,
                                        is_manager=True
                                    )
                                else:
                                    raise
                            st.session_state.request_result = result
                        else:
                            # Regular employee flow
                            # Step 1: Tool Query - Compare dates against balance
                            st.session_state.processing_steps.append({
                                "step": 1,
                                "name": "Database Tool Query",
                                "status": "processing",
                                "message": f"Comparing requested {days_requested} days ({start_date.strftime('%b %d')} - {end_date.strftime('%b %d')}) against available balance..."
                            })
                            
                            sufficient, balance_info = st.session_state.db.check_balance_sufficient(
                                employee_id, days_requested, leave_type
                            )
                            
                            st.session_state.processing_steps.append({
                                "step": 1,
                                "name": "Database Tool Query",
                                "status": "completed" if sufficient else "error",
                                "message": f"Balance check: {balance_info['remaining_days']:.1f} days available. {'✓ Sufficient' if sufficient else '✗ Insufficient'}"
                            })
                            
                            # Step 2: RAG Query - Compare dates against policy constraints
                            st.session_state.processing_steps.append({
                                "step": 2,
                                "name": "Policy RAG Query",
                                "status": "processing",
                                "message": f"Checking policy compliance for {days_requested} days starting {start_date.strftime('%b %d, %Y')}..."
                            })
                            
                            result = st.session_state.agent.process_vacation_request(
                                employee_id=employee_id,
                                leave_type=leave_type,
                                start_date=start_date,
                                end_date=end_date,
                                is_manager=False
                            )
                            
                            st.session_state.request_result = result
                            st.session_state.processing_steps.append({
                                "step": 2,
                                "name": "Policy RAG Query",
                                "status": "completed",
                                "message": "Policy compliance checked"
                            })
                            
                            # Step 3: Decision
                            st.session_state.processing_steps.append({
                                "step": 3,
                                "name": "Decision",
                                "status": "completed" if result.get("status") == "approved" else "error",
                                "message": f"Request {result.get('status', 'processed').upper()}"
                            })
                        
                        # Store form values for email generation
                        st.session_state.form_employee_id = employee_id
                        st.session_state.form_leave_type = leave_type
                        st.session_state.form_start_date = start_date
                        st.session_state.form_end_date = end_date
                        
                        st.rerun()
                        
                    except Exception as e:
                        st.error(f"Error processing request: {str(e)}")
    
    st.markdown('</div>', unsafe_allow_html=True)

# Results Column
with col2:
    st.markdown('<div class="section-header">🔄 Processing Flow</div>', unsafe_allow_html=True)
    if st.session_state.processing_steps:
        for i, step_info in enumerate(st.session_state.processing_steps):
            status_class = step_info.get("status", "")
            icon_map = {
                "processing": "⏳",
                "completed": "✅",
                "error": "❌"
            }
            icon = icon_map.get(status_class, "⚪")
            
            step_html = f"""
            <div class="flow-step {status_class}">
                <strong>{icon} Step {step_info['step']}: {step_info['name']}</strong><br>
                <span style="color: #64748b; font-size: 0.9rem;">{step_info['message']}</span>
            </div>
            """
            st.markdown(step_html, unsafe_allow_html=True)
            
            # Add connector if not last
            if i < len(st.session_state.processing_steps) - 1:
                st.markdown('<div class="flow-connector">↓</div>', unsafe_allow_html=True)
    else:
        st.info("Submit a request first to see the processing flow.")

# Full-width results section
if st.session_state.request_result:
    st.markdown("---")
    
    result = st.session_state.request_result
    status = result.get("status", "unknown")
    
    
    # NEW: Multi-Step Analysis Section (BEFORE approval/denial)
    if result.get("analysis_checks"):
        st.markdown('<div class="section-header">📊 Request Analysis</div>', unsafe_allow_html=True)
        st.info("🔍 **Analysis Complete**: Review the checks below to understand how your request compares against balance and policy constraints.")
        
        # Display each check with status indicators
        analysis_col1, analysis_col2 = st.columns([1, 1])
        
        for i, check in enumerate(result["analysis_checks"]):
            col = analysis_col1 if i % 2 == 0 else analysis_col2
            
            with col:
                status_color = {
                    "PASS": "#10b981",
                    "FAIL": "#ef4444",
                    "WARNING": "#f59e0b",
                    "INFO": "#3b82f6"
                }.get(check.get("status", "INFO"), "#64748b")
                
                check_html = f"""
                <div style="padding: 1rem; margin: 0.5rem 0; border-radius: 8px; 
                           border-left: 4px solid {status_color}; background: #f8fafc;">
                    <div style="display: flex; align-items: center; gap: 0.5rem; margin-bottom: 0.5rem;">
                        <span style="font-size: 1.5rem;">{check.get('icon', '⚪')}</span>
                        <strong style="color: {status_color};">{check.get('check', 'Check')}</strong>
                        <span style="margin-left: auto; padding: 0.25rem 0.75rem; 
                                    background: {status_color}; color: white; border-radius: 12px; 
                                    font-size: 0.75rem; font-weight: bold;">
                            {check.get('status', 'UNKNOWN')}
                        </span>
                    </div>
                    <div style="color: #64748b; font-size: 0.9rem; margin-bottom: 0.25rem;">
                        {check.get('message', '')}
                    </div>
                    <div style="color: #94a3b8; font-size: 0.85rem; font-style: italic;">
                        {check.get('details', '')}
                    </div>
                    {f"<div style='color: #3b82f6; font-size: 0.8rem; margin-top: 0.25rem;'><strong>Policy:</strong> {check.get('section', '')}</div>" if check.get('section') else ''}
                </div>
                """
                st.markdown(check_html, unsafe_allow_html=True)
    
    # NEW: Comprehensive Options Section with Working Buttons
    # Show options section AFTER analysis checks (moved outside if block to ensure it always shows)
    # Show options if request is pending (not yet approved or denied)
    should_show_options = (status == "pending" or (status not in ["approved", "denied"] and status != "unknown"))
    
    if should_show_options and result.get("requested_dates"):
        st.markdown('<div class="section-header">🎯 CHOOSE AN ACTION</div>', unsafe_allow_html=True)
        
        # Extract request details
        employee_id = result.get("employee_id")
        leave_type = result.get("leave_type")
        start_date_str = result.get("requested_dates", {}).get("start")
        end_date_str = result.get("requested_dates", {}).get("end")
        days_requested = result.get("requested_dates", {}).get("days", 0)
        balance_info = result.get("balance_info", {})
        remaining_days = balance_info.get("remaining_days", 0)
        remaining_hours = balance_info.get("remaining_hours", 0)
        
        if start_date_str and end_date_str:
            start_date_obj = datetime.strptime(start_date_str, "%Y-%m-%d").date()
            end_date_obj = datetime.strptime(end_date_str, "%Y-%m-%d").date()
            
            # Calculate new balance if approved
            new_remaining_days = max(0, remaining_days - days_requested)
            new_remaining_hours = max(0, remaining_hours - (days_requested * 8))
            
            # Check if all checks passed
            all_checks_passed = all(
                check.get("status") == "PASS" or check.get("status") == "INFO" or check.get("status") == "WARNING"
                for check in result.get("analysis_checks", [])
            )
            has_failures = any(
                check.get("status") == "FAIL" for check in result.get("analysis_checks", [])
            )
            
            # OPTION A: Approve Exactly as Requested
            with st.container():
                st.markdown("---")
                opt_a_col1, opt_a_col2 = st.columns([3, 1])
                with opt_a_col1:
                    status_icon = "✅" if all_checks_passed else "⚠️"
                    status_text = "All checks passed" if all_checks_passed else "Some warnings present"
                    st.markdown(f"""
                    **Option A: ✅ Approve Exactly as Requested**
                    - **Status:** {status_icon} {status_text}
                    - **Action:** Approve {days_requested:.1f} days from {start_date_obj.strftime('%B %d')} to {end_date_obj.strftime('%B %d, %Y')}
                    - **New Balance:** {new_remaining_days:.1f} days ({new_remaining_hours:.1f} hours)
                    - **Email:** Will be sent to manager
                    """)
                with opt_a_col2:
                    if st.button("APPROVE THIS OPTION", key="opt_a_approve", use_container_width=True, 
                               type="primary", disabled=(result.get("status") == "approved")):
                        try:
                            st.session_state.db.record_leave_request(
                                employee_id, leave_type, start_date_obj, end_date_obj, days_requested, "approved"
                            )
                            updated_balance = st.session_state.db.get_remaining_balance(employee_id, leave_type)
                            result["status"] = "approved"
                            result["balance_info"] = updated_balance
                            result["message"] = (
                                f"✅ **APPROVED**: Your {leave_type} leave request for {days_requested} days "
                                f"({start_date_obj.strftime('%B %d')} to {end_date_obj.strftime('%B %d, %Y')}) has been approved.\n\n"
                                f"**Remaining Balance**: {updated_balance['remaining_days']:.1f} days "
                                f"({updated_balance['remaining_hours']:.1f} hours) of {leave_type} leave remaining.\n"
                            )
                            st.session_state.request_result = result
                            st.success("✅ **Request Approved!**")
                            st.rerun()
                        except Exception as e:
                            st.error(f"Error: {str(e)}")
                
                # OPTION B: Suggest Better Dates
                with st.container():
                    st.markdown("---")
                    opt_b_col1, opt_b_col2 = st.columns([3, 1])
                    with opt_b_col1:
                        # Generate actual alternative date suggestions
                        alt_suggestions = []
                        if days_requested > 7:
                            # Suggest splitting into 2 parts
                            part1_days = min(7.0, days_requested / 2)
                            part1_end = start_date_obj + timedelta(days=int(part1_days) - 1)
                            alt_suggestions.append({
                                "dates": f"{start_date_obj.strftime('%b %d')} - {part1_end.strftime('%b %d, %Y')}",
                                "days": part1_days,
                                "benefit": "Complies with max 7-day consecutive limit"
                            })
                            
                            part2_days = days_requested - part1_days
                            part2_start = start_date_obj + timedelta(days=14)
                            part2_end = part2_start + timedelta(days=int(part2_days) - 1)
                            alt_suggestions.append({
                                "dates": f"{part2_start.strftime('%b %d')} - {part2_end.strftime('%b %d, %Y')}",
                                "days": part2_days,
                                "benefit": "2 weeks later - better team coverage"
                            })
                        else:
                            # Suggest shifting by 1 week
                            shift_start = start_date_obj + timedelta(days=7)
                            shift_end = end_date_obj + timedelta(days=7)
                            alt_suggestions.append({
                                "dates": f"{shift_start.strftime('%b %d')} - {shift_end.strftime('%b %d, %Y')}",
                                "days": days_requested,
                                "benefit": "1 week later - better team planning"
                            })
                            # Suggest shifting by 2 weeks
                            shift_start2 = start_date_obj + timedelta(days=14)
                            shift_end2 = end_date_obj + timedelta(days=14)
                            alt_suggestions.append({
                                "dates": f"{shift_start2.strftime('%b %d')} - {shift_end2.strftime('%b %d, %Y')}",
                                "days": days_requested,
                                "benefit": "2 weeks later - improved coverage"
                            })
                        
                        suggestions_text = "\n".join([
                            f"- **Suggestion {i+1}:** {sug['dates']} ({sug['days']:.1f} days) - {sug['benefit']}"
                            for i, sug in enumerate(alt_suggestions)
                        ])
                        
                        st.markdown(f"""
                        **Option B: 🔄 Suggest Better Dates**
                        - **Status:** ⚠️ Alternative suggestions
                        {suggestions_text}
                        - **New Balance:** Same {days_requested:.1f} days total
                        """)
                    with opt_b_col2:
                        show_suggestions = st.session_state.get("show_better_dates", False)
                        if st.button("VIEW SUGGESTIONS", key="opt_b_suggestions", use_container_width=True):
                            st.session_state.show_better_dates = not show_suggestions
                            st.rerun()
                
                        if st.session_state.get("show_better_dates", False):
                            st.markdown("**💡 Use these dates when submitting your next request**")
                
                # OPTION C: Split Request
                with st.container():
                    st.markdown("---")
                    opt_c_col1, opt_c_col2 = st.columns([3, 1])
                    with opt_c_col1:
                        # Fix split date calculations to ensure valid date ranges
                        part1_days = int(days_requested / 2)  # Use integer days for clean splits
                        if part1_days < 1:
                            part1_days = 1
                        part1_end = start_date_obj + timedelta(days=part1_days - 1)  # -1 because start date is included
                        
                        part2_days = days_requested - part1_days
                        if part2_days < 1:
                            part2_days = 1
                            part1_days = days_requested - 1
                            part1_end = start_date_obj + timedelta(days=part1_days - 1)
                        
                        part2_start = start_date_obj + timedelta(days=14)
                        part2_end = part2_start + timedelta(days=part2_days - 1)
                        
                        st.markdown(f"""
                        **Option C: ✂️ Split Request**
                        - **Status:** ⚠️ For better team coverage
                        - **Part 1:** {part1_days} days on {start_date_obj.strftime('%b %d')} - {part1_end.strftime('%b %d, %Y')}
                        - **Part 2:** {part2_days} days on {part2_start.strftime('%b %d')} - {part2_end.strftime('%b %d, %Y')}
                        - **Benefit:** Maintains team productivity
                        """)
                    with opt_c_col2:
                        if st.button("SPLIT REQUEST", key="opt_c_split", use_container_width=True):
                            st.session_state.show_split_form = not st.session_state.get("show_split_form", False)
                            st.rerun()
                
                # Split form (fixed to prevent Streamlit error)
                if st.session_state.get("show_split_form", False):
                    with st.form("split_request_form"):
                        original_days = float(days_requested)
                        balance_days = float(remaining_days)
                        
                        # Fix: value must be <= max_value
                        default_val_1 = min(original_days / 2, original_days, balance_days)
                        default_val_1 = max(0.5, default_val_1)  # Ensure at least 0.5
                        
                        split_col1, split_col2 = st.columns(2)
                        with split_col1:
                            split_days_1 = st.number_input(
                                "Segment 1 - Days", 
                                min_value=0.5, 
                                max_value=float(original_days), 
                                value=default_val_1,
                                step=0.5
                            )
                        with split_col2:
                            max_val_2 = float(original_days - split_days_1)
                            default_val_2 = max(0.0, float(original_days - split_days_1))
                            split_days_2 = st.number_input(
                                "Segment 2 - Days", 
                                min_value=0.0, 
                                max_value=max_val_2 if max_val_2 > 0 else 0.5, 
                                value=default_val_2,
                                step=0.5
                            )
                        
                        if st.form_submit_button("🚀 Process Split Request", use_container_width=True):
                            if abs(split_days_1 + split_days_2 - original_days) < 0.1:  # Allow small floating point differences
                                st.success(f"✅ Split request created: **Segment 1:** {split_days_1} days, **Segment 2:** {split_days_2} days")
                                st.info("💡 You can now submit each segment as a separate request.")
                                st.session_state.show_split_form = False
                            else:
                                st.error(f"❌ Total days ({split_days_1 + split_days_2:.1f}) must equal original request ({original_days} days)")
                
                # OPTION D: Deny with Explanation (only show if there are blocking violations OR as override)
                violations = result.get("violations", [])
                blocking_violations = [v for v in violations if v.get("type") != "warning"]
                
                # Only show deny option if there are blocking violations, or make it an override option
                if blocking_violations or True:  # Always show, but label differently
                    with st.container():
                        st.markdown("---")
                        opt_d_col1, opt_d_col2 = st.columns([3, 1])
                        with opt_d_col1:
                            if blocking_violations:
                                violation_text = "\n".join([
                                    f"- {v.get('rule', 'Policy Violation')}: {v.get('description', '')}"
                                    for v in blocking_violations[:2]
                                ])
                                policy_refs = ", ".join([v.get('rule', '').split('(')[1].split(')')[0] 
                                                        for v in blocking_violations if '(' in v.get('rule', '')])[:1]
                                suggestion_text = "Please review the policy violations above and adjust your request accordingly."
                                
                                st.markdown(f"""
                                **Option D: ❌ Deny with Explanation**
                                - **Status:** ❌ Policy violation detected
                                {violation_text}
                                - **Policy Reference:** {policy_refs}
                                - **Suggestion:** {suggestion_text}
                                """)
                            else:
                                st.markdown(f"""
                                **Option D: ❌ Deny Anyway (Manager Override)**
                                - **Status:** ⚠️ Override required (no policy violations)
                                - **Note:** This request can be approved, but you may deny it with manager override
                                - **Reason:** Please provide a reason for override when denying
                                """)
                        with opt_d_col2:
                            if st.button("DENY REQUEST", key="opt_d_deny", use_container_width=True,
                                       disabled=(result.get("status") == "denied")):
                                try:
                                    st.session_state.db.record_leave_request(
                                        employee_id, leave_type, start_date_obj, end_date_obj, days_requested, "denied"
                                    )
                                    result["status"] = "denied"
                                    if blocking_violations:
                                        result["message"] = "❌ **DENIED**: This request has been denied. See policy violations above for details."
                                    else:
                                        result["message"] = "❌ **DENIED**: This request has been denied with manager override (no policy violations detected)."
                                    st.session_state.request_result = result
                                    st.warning("❌ **Request Denied!**")
                                    st.rerun()
                                except Exception as e:
                                    st.error(f"Error: {str(e)}")
            
            st.markdown("---")
    
    # Status header (only show if actually approved or denied, not pending)
    if status == "approved":
        is_manager_approval = result.get("is_manager_approval", False)
        st.markdown('<div class="result-box approved-box">', unsafe_allow_html=True)
        if is_manager_approval:
            st.markdown(f"### 👑 Manager Request Auto-Approved")
        else:
            st.markdown(f"### ✅ Request Approved")
        # Show full message for manager approvals (includes the note)
        message_to_show = result.get('message', 'Request approved')
        if is_manager_approval:
            st.markdown(message_to_show)
        else:
            st.markdown(message_to_show.split('\n')[0])
        st.markdown('</div>', unsafe_allow_html=True)
    elif status == "denied":
        st.markdown('<div class="result-box denied-box">', unsafe_allow_html=True)
        st.markdown(f"### ❌ Request Denied")
        st.markdown(result.get('message', 'Request denied').split('\n')[0])
        st.markdown('</div>', unsafe_allow_html=True)
    # If status is "pending", don't show status header - options section will handle it
    
    # Balance metrics
    if "balance_info" in result:
        st.markdown('<div class="section-header">💰 Balance Information</div>', unsafe_allow_html=True)
        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric("Remaining Days", f"{result['balance_info']['remaining_days']:.1f}", help="Days of leave remaining")
        with col2:
            st.metric("Remaining Hours", f"{result['balance_info']['remaining_hours']:.1f}", help="Hours of leave remaining")
        with col3:
            st.metric("Annual Quota", f"{result['balance_info']['annual_quota_days']} days", help="Total annual allowance")
    
    # Conflict Resolution Section (for denied requests with policy citations)
    if result.get("violations") and result.get("status") == "denied":
        st.markdown('<div class="section-header">⚠️ Conflict Resolution</div>', unsafe_allow_html=True)
        st.warning("🚫 **Request Denied**: The following policy violations prevent approval. Review the conflicts and suggested alternatives below.")
        
        for violation in result["violations"]:
            if violation.get('type') != 'warning':  # Only show blocking violations
                section = violation.get('rule', '').split('(')[1].split(')')[0] if '(' in violation.get('rule', '') else 'N/A'
                violation_html = f"""
                <div style="padding: 1.5rem; margin: 1rem 0; border-radius: 12px; 
                           background: linear-gradient(135deg, #fee2e2 0%, #fecaca 100%);
                           border-left: 5px solid #ef4444;">
                    <div style="display: flex; align-items: start; gap: 1rem;">
                        <span style="font-size: 2rem;">📌</span>
                        <div style="flex: 1;">
                            <strong style="color: #dc2626; font-size: 1.1rem;">
                                {violation.get('rule', 'Policy Violation')}
                            </strong>
                            <div style="margin-top: 0.5rem; color: #64748b;">
                                {violation.get('description', '')}
                            </div>
                            <div style="margin-top: 0.75rem; padding: 0.5rem; background: white; 
                                       border-radius: 6px; border-left: 3px solid #3b82f6;">
                                <strong style="color: #3b82f6;">Policy Reference:</strong> 
                                <code style="background: #f1f5f9; padding: 0.2rem 0.5rem; 
                                            border-radius: 4px; margin-left: 0.5rem;">{section}</code>
                            </div>
                        </div>
                    </div>
                </div>
                """
                st.markdown(violation_html, unsafe_allow_html=True)
    
    # Policy Notices/Warnings (show for approved requests with recommendations)
    if result.get("violations") and result.get("status") == "approved":
        # These are warnings/recommendations, not blocking violations
        st.markdown('<div class="section-header">ℹ️ Policy Notices</div>', unsafe_allow_html=True)
        st.info("ℹ️ These are informational notices, not blocking violations. Your request has been approved.")
        for violation in result["violations"]:
            notice_html = f"""
            <div class="option-item">
                <strong>💡 {violation.get('rule', 'Policy Notice')}</strong><br>
                <span style="color: #64748b;">{violation.get('description', '')}</span>
            </div>
            """
            st.markdown(notice_html, unsafe_allow_html=True)
    
    # Proactive Options Section (Interactive Cards)
    if result.get("options"):
        st.markdown('<div class="section-header">💡 Proactive Options</div>', unsafe_allow_html=True)
        st.info("🎯 **Choose an Option**: Select how you'd like to proceed. Each option addresses the policy conflicts differently.")
        
        # Display options as interactive cards
        options_per_row = 2
        option_rows = [result["options"][i:i+options_per_row] for i in range(0, len(result["options"]), options_per_row)]
        
        for row_options in option_rows:
            cols = st.columns(len(row_options))
            for idx, option in enumerate(row_options):
                with cols[idx]:
                    # Handle both old string format and new dict format
                    if isinstance(option, dict):
                        option_letter = option.get("letter", "?")
                        option_title = option.get("title", "Option")
                        option_desc = option.get("description", "")
                        option_cons = option.get("consequence", "")
                        is_recommended = option.get("recommended", False)
                        option_type = option.get("type", "modify")
                    else:
                        # Legacy string format
                        option_letter = option.split(':')[0].split()[-1] if ':' in option else "?"
                        option_title = f"Option {option_letter}"
                        option_desc = option.split(':', 1)[1].strip() if ':' in option else option
                        option_cons = ""
                        is_recommended = False
                        option_type = "modify"
                    
                    # Determine card styling
                    card_color = {
                        "approve": "#10b981",
                        "reduce": "#3b82f6",
                        "delay": "#f59e0b",
                        "deny": "#ef4444",
                        "modify": "#6366f1"
                    }.get(option_type, "#64748b")
                    
                    recommended_badge = """
                    <div style="position: absolute; top: 0.5rem; right: 0.5rem; 
                               background: #f59e0b; color: white; padding: 0.25rem 0.75rem; 
                               border-radius: 12px; font-size: 0.75rem; font-weight: bold;">
                        ⭐ Recommended
                    </div>
                    """ if is_recommended else ""
                    
                    option_html = f"""
                    <div style="position: relative; padding: 1.5rem; margin: 0.5rem 0; 
                               border-radius: 12px; border: 2px solid {card_color}; 
                               background: linear-gradient(135deg, #ffffff 0%, #f8fafc 100%);
                               box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.1);
                               transition: transform 0.2s, box-shadow 0.2s;
                               cursor: pointer;">
                        {recommended_badge}
                        <div style="display: flex; align-items: center; gap: 0.5rem; margin-bottom: 0.75rem;">
                            <span style="font-size: 1.5rem; font-weight: bold; color: {card_color};">
                                Option {option_letter}
                            </span>
                        </div>
                        <div style="font-weight: 600; color: #1f2937; margin-bottom: 0.5rem; font-size: 1.05rem;">
                            {option_title}
                        </div>
                        <div style="color: #64748b; font-size: 0.9rem; margin-bottom: 0.75rem;">
                            {option_desc}
                        </div>
                        {f'<div style="padding: 0.5rem; background: #f1f5f9; border-radius: 6px; margin-top: 0.5rem; font-size: 0.85rem; color: #475569;"><strong>Consequence:</strong> {option_cons}</div>' if option_cons else ''}
                    </div>
                    """
                    st.markdown(option_html, unsafe_allow_html=True)
                    
                    # Action button for each option
                    button_label = "✅ Select This Option" if option_type != "deny" else "❌ Confirm Denial"
                    button_type = "primary" if is_recommended else "secondary"
                    if st.button(button_label, key=f"option_{option_letter}_{idx}", use_container_width=True, type=button_type if option_type != "deny" else "primary"):
                        st.info(f"✅ **Selected: Option {option_letter}** - {option_title}")
                        st.session_state.selected_option = option
                        # Note: In a real implementation, this would trigger the actual action
                        # For now, we just show feedback
        
        st.markdown("---")
    
    # AI-Powered Employee Email Drafting
    st.markdown("---")
    st.markdown('<div class="section-header">✉️ AI-Powered Email Drafting</div>', unsafe_allow_html=True)
    
    # Email generation section
    email_col1, email_col2 = st.columns([3, 1])
    
    with email_col1:
        st.markdown("**Customize your leave request email** (optional)")
        email_custom_message = st.text_area(
            "Add any additional information or personal message:",
            value=st.session_state.get("email_custom_message", ""),
            height=100,
            placeholder="e.g., I will ensure all tasks are completed before my leave, or any other relevant details...",
            help="Optional: Add any context or personal message to include in your email",
            key="email_custom_input"
        )
        st.session_state.email_custom_message = email_custom_message
    
    with email_col2:
        st.markdown("<br>", unsafe_allow_html=True)
        if st.button("🤖 Generate Email", use_container_width=True, type="primary"):
            with st.spinner("Generating professional email with AI..."):
                try:
                    # Get values from result or form state
                    emp_id = result.get("employee_id", st.session_state.get("form_employee_id", ""))
                    lv_type = result.get("leave_type", st.session_state.get("form_leave_type", ""))
                    s_date = st.session_state.get("form_start_date", result.get("requested_dates", {}).get("start", date.today()))
                    e_date = st.session_state.get("form_end_date", result.get("requested_dates", {}).get("end", date.today()))
                    
                    # Convert string dates if needed
                    if isinstance(s_date, str):
                        s_date = datetime.strptime(s_date, "%Y-%m-%d").date()
                    if isinstance(e_date, str):
                        e_date = datetime.strptime(e_date, "%Y-%m-%d").date()
                    
                    employee_email = st.session_state.agent.generate_employee_email(
                        employee_id=emp_id,
                        leave_type=lv_type,
                        start_date=s_date,
                        end_date=e_date,
                        days_requested=(e_date - s_date).days + 1,
                        balance_info=result.get("balance_info", {}),
                        custom_message=email_custom_message if email_custom_message else None
                    )
                    st.session_state.employee_email_draft = employee_email
                    st.session_state.email_sent_status = None
                    st.rerun()
                except Exception as e:
                    st.error(f"Error generating email: {str(e)}")
    
    # Display generated email
    if st.session_state.employee_email_draft:
        st.markdown("**📝 Generated Email Preview**")
        st.markdown('<div class="email-preview">', unsafe_allow_html=True)
        
        # Editable email (using text_area for editing)
        edited_email = st.text_area(
            "Edit your email:",
            value=st.session_state.employee_email_draft,
            height=300,
            key="email_editor"
        )
        st.session_state.employee_email_draft = edited_email
        st.markdown('</div>', unsafe_allow_html=True)
        
        # Email actions
        col_send, col_download, col_copy = st.columns([2, 1, 1])
        
        with col_send:
            if st.button("📤 Send Email to Manager", use_container_width=True, type="primary"):
                # Simulate sending email (in production, integrate with email service)
                timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                st.session_state.email_sent_status = {
                    "status": "sent",
                    "timestamp": timestamp,
                    "email_content": edited_email
                }
                st.success("✅ Email sent successfully to manager!")
                st.balloons()
                st.rerun()
        
        with col_download:
            st.download_button(
                label="📥 Download",
                data=edited_email,
                file_name=f"leave_request_email_{st.session_state.get('form_employee_id', 'EMP')}_{st.session_state.get('form_start_date', date.today()).strftime('%Y%m%d')}.txt",
                mime="text/plain",
                use_container_width=True
            )
        
        with col_copy:
            if st.button("📋 Copy", use_container_width=True, help="Copy email to clipboard"):
                st.code(edited_email, language=None)
                st.info("💡 Click the code block above and copy, or use the download button")
        
        # Show sent status
        if st.session_state.email_sent_status:
            status_info = st.session_state.email_sent_status
            if status_info.get("status") == "sent":
                st.markdown("---")
                st.markdown('<div class="result-box approved-box">', unsafe_allow_html=True)
                st.markdown("### ✅ Email Sent Successfully")
                st.markdown(f"""
                **Status:** Sent to Manager  
                **Timestamp:** {status_info.get('timestamp', 'N/A')}  
                **Recipient:** Manager  
                **Subject:** Leave Request - {st.session_state.get('form_leave_type', 'vacation').title()} Leave
                """)
                st.markdown('</div>', unsafe_allow_html=True)
    
    # Manager notification email (separate section)
    if result.get("email_content"):
        st.markdown("---")
        st.markdown('<div class="section-header">📧 Manager Notification Email (System Generated)</div>', unsafe_allow_html=True)
        st.info("This is the automated system notification sent to your manager. The email above is your personal request email.")
        st.markdown('<div class="email-preview">', unsafe_allow_html=True)
        st.text(result["email_content"])
        st.markdown('</div>', unsafe_allow_html=True)
        
        st.download_button(
            label="📥 Download Manager Notification",
            data=result["email_content"],
            file_name=f"manager_notification_{employee_id}_{start_date.strftime('%Y%m%d')}.txt",
            mime="text/plain",
            use_container_width=False
        )
else:
    st.markdown("---")
    st.info("No active request. Submit a leave request to see results.")

# Balance Query Modal
if st.session_state.get("show_balance", False):
    st.markdown("---")
    with st.expander("💰 Balance Query", expanded=True):
        bal_employee_id = st.text_input("Employee ID", placeholder="e.g., EMP001", value="EMP001", key="bal_emp_id")
        bal_leave_type = st.selectbox("Leave Type", ["vacation", "sick"], key="balance_leave_type")
        
        if st.button("Check Balance", key="check_balance_btn"):
            try:
                balance_result = st.session_state.agent.query_balance(bal_employee_id, bal_leave_type)
                st.success(balance_result["message"])
            except Exception as e:
                st.error(f"Error: {str(e)}")
        
        if st.button("Close", key="close_balance"):
            st.session_state.show_balance = False
            st.rerun()

# Policy Search Modal
if st.session_state.get("show_policy", False):
    st.markdown("---")
    with st.expander("📄 Corporate Leave Policy", expanded=True):
        policy_query = st.text_input("Search Policy", placeholder="e.g., 60% rule, blackout periods", key="policy_search")
        
        if st.button("Search Policy", key="search_policy"):
            if policy_query:
                try:
                    explanation = st.session_state.agent.get_policy_explanation(policy_query)
                    st.markdown(explanation)
                except Exception as e:
                    st.error(f"Error: {str(e)}")
        
        if st.button("Close", key="close_policy"):
            st.session_state.show_policy = False
            st.rerun()
        
        with st.expander("📋 Policy Highlights"):
            st.markdown("""
            - **60% Rule**: Cannot use >60% of annual allowance in single request
            - **Frequency Limits**: Max 2 long vacations (>7 days) per 60-day period
            - **Blackout Periods**: Restricted dates during fiscal quarters
            - **Notice Period**: Minimum 2-week notice for leaves >3 days
            """)

# Enhanced Footer
st.markdown("---")
st.markdown(
    '<div style="text-align: center; color: #94a3b8; padding: 2rem 0;">'
    '<strong>Corporate Vacation AI Agent</strong> | Tool → RAG Integration | Built with Streamlit<br>'
    '<small>© 2024 Corporate Leave Management System</small>'
    '</div>',
    unsafe_allow_html=True
)
