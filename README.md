# Corporate Vacation AI Agent

A unified, interactive AI agent for corporate vacation approval with Tool + RAG integration. This system provides a seamless employee self-service experience for leave requests, combining real-time balance queries with intelligent policy compliance checking.

## 🎯 Overview

The Corporate Vacation AI Agent automates the leave approval process by:

1. **Tool Integration**: Querying employee leave balances from a SQLite database
2. **RAG Integration**: Checking policy compliance using a vectorized corporate leave policy document
3. **Conversational Intelligence**: Providing multi-step guidance and proactive alternative options
4. **Automated Workflows**: Generating manager notifications and tracking leave requests

## 📚 Documentation

- **[USER_GUIDE.md](USER_GUIDE.md)** - Complete user guide with project structure, architecture, and usage instructions
- **[README.md](README.md)** - This file - project overview and quick start

## 🔄 System Architecture

### Tool→RAG Flow

The agent follows a two-step validation process:

```
1. TOOL QUERY FIRST → Check if employee has sufficient balance
   ↓
2. RAG QUERY SECOND → Check if request complies with corporate policies
   ↓
3. DECISION → Approve/Deny with detailed explanations and options
```

### Key Components

- **Database Tool** (`src/database_tool.py`): SQLite database with employee balances and leave history
- **Policy RAG** (`src/policy_rag.py`): Vector store of corporate leave policy with semantic search
- **Vacation Agent** (`src/vacation_agent.py`): Unified chatbot interface combining Tool + RAG
- **Web UI** (`streamlit_app.py`): Interactive web interface for submitting and managing requests
- **Utility Scripts**: `populate_employees.py`, `reset_balances.py`, `main.py` (demo)

## 📋 Features

### 1. Data & Tool Integration

- ✅ **Accrued Balances**: Vacation and sick leave tracked in hours/days
- ✅ **Annual Quotas**: Maximum leave per year based on years of service
- ✅ **Employee ID Lookup**: Quick employee information retrieval
- ✅ **Remaining Balance Queries**: Real-time balance checking via SQLite

### 2. Policy RAG & Business Rules

All business rules are extracted from the policy document via RAG:

- ✅ **60% Rule**: Cannot use >60% of annual allowance in a single request
- ✅ **Frequency Limits**: No more than 2 "long vacations" (>1 week) within a 2-month period
- ✅ **Blackout Periods**: Restricted dates during fiscal quarters and year-end
- ✅ **Notice Period**: Minimum 2-week notice for leaves >3 days

### 3. Conversational Intelligence & UX

- ✅ **Multi-step Guidance**: Compares dates against balance AND policy
- ✅ **Proactive Options**: Provides alternatives like "Option A: Take 4 days now; Option B: Shift dates..."
- ✅ **Conflict Resolution**: Explains denials with specific policy sections
- ✅ **Inline Confirmations**: Shows approved dates and remaining balance

### 4. Final Outputs

- ✅ **Approval Confirmation**: Inline display with dates and remaining balance
- ✅ **Email Generation**: Automated email to manager with all relevant details

## 🚀 Quick Start

### Prerequisites

- Python 3.8+
- OpenAI API key (for RAG functionality)

### Installation

1. **Clone or navigate to the project directory**

```bash
cd corporate-vacation-agent
```

2. **Install dependencies**

```bash
pip install -r requirements.txt
```

3. **Set up OpenAI API key**

Create a `.env` file or export environment variable:

```bash
export OPENAI_API_KEY='your-openai-api-key-here'
```

Or create `.env` file:

```
OPENAI_API_KEY=your-openai-api-key-here
```

4. **Initialize the database and vector store**

The database and vector store will be created automatically on first run, but you can also initialize sample data:

```bash
python -c "from src.database_tool import EmployeeDatabase; db = EmployeeDatabase(); db.initialize_sample_data()"
```

### Running the Web UI

Launch the professional Streamlit web interface:

```bash
streamlit run streamlit_app.py
```

The web UI will open automatically in your browser at `http://localhost:8501`

**Features:**
- 📝 Interactive leave request form
- 🔄 Visual Tool→RAG flow display
- 📊 Real-time processing results
- 💰 Balance query tool
- 📄 Policy search via RAG
- 📧 Manager email preview and download

See [USER_GUIDE.md](USER_GUIDE.md) for detailed documentation.

### Running the Demo

```bash
python main.py
```

This will run comprehensive demos showcasing:
- Balance queries
- Approved requests
- 60% rule violations
- Insufficient balance scenarios
- Blackout period violations
- Notice period violations
- Frequency limit violations
- Policy queries via RAG

## 📁 Project Structure

```
corporate-vacation-agent/
├── data/
│   ├── company_policy.md          # 2-page corporate leave policy document
│   ├── employee_data.db           # SQLite database (created on first run)
│   └── chroma_db/                 # Vector store for RAG (created on first run)
├── src/
│   ├── database_tool.py           # Database operations for balance queries
│   ├── policy_rag.py              # RAG pipeline for policy document
│   └── vacation_agent.py          # Main agent with Tool→RAG flow
├── streamlit_app.py               # Professional web UI (Streamlit dashboard)
├── main.py                        # Comprehensive demo script
├── requirements.txt               # Python dependencies
├── README.md                      # This file
└── USER_GUIDE.md                  # Complete user guide with architecture
```

## 💻 Usage Examples

### Basic Vacation Request

```python
from datetime import date
from src.vacation_agent import VacationAgent

# Initialize agent
agent = VacationAgent()

# Process vacation request
result = agent.process_vacation_request(
    employee_id="EMP001",
    leave_type="vacation",
    start_date=date(2024, 2, 15),
    end_date=date(2024, 2, 22)
)

print(result["message"])
if result["email_content"]:
    print("\nManager Email:", result["email_content"])
```

### Query Employee Balance

```python
# Query vacation balance
result = agent.query_balance("EMP001", "vacation")
print(result["message"])

# Query sick leave balance
result = agent.query_balance("EMP001", "sick")
print(result["message"])
```

### Policy Query via RAG

```python
# Get policy explanation
explanation = agent.get_policy_explanation("What is the 60% rule?")
print(explanation)
```

## 📊 Sample Employee Data

The demo includes sample employees:

| Employee ID | Name          | Years of Service | Vacation Quota | Vacation Used |
|-------------|---------------|------------------|----------------|---------------|
| EMP001      | John Smith    | 2                | 10 days        | 3 days        |
| EMP002      | Jane Doe      | 4                | 15 days        | 0 days        |
| EMP003      | Bob Johnson   | 7                | 20 days        | 5 days        |
| EMP004      | Alice Williams| 1                | 10 days        | 0 days        |

## 🔍 Policy Rules Explained

### 60% Rule (Section 2.1)
Employees cannot use more than 60% of their annual vacation allowance in a single request. This ensures balanced leave distribution throughout the year.

**Example**: An employee with 10 days annual quota can request a maximum of 6 days in one request.

### Frequency Limits (Section 2.2)
No more than 2 "long vacations" (>7 consecutive days) within any 60-day rolling period.

### Blackout Periods (Section 2.3)
- Q1 End: March 18 - March 31
- Q2 End: June 17 - June 30
- Q3 End: September 16 - September 30
- Year-End: November 15 - December 31

**Exception**: Requests <3 days are allowed during blackout periods.

### Notice Period (Section 2.4)
- 1-3 days: Minimum 5 business days notice
- 4-7 days: Minimum 2 weeks (14 calendar days) notice
- 8+ days: Minimum 3 weeks (21 calendar days) notice

## 🔧 Configuration

### Database Path
Default: `data/employee_data.db`

Modify in `VacationAgent` initialization:
```python
agent = VacationAgent(db_path="custom/path/employee_data.db")
```

### Policy Document Path
Default: `data/company_policy.md`

Modify in `VacationAgent` initialization:
```python
agent = VacationAgent(policy_path="custom/path/policy.md")
```

### Vector Store Path
Default: `data/chroma_db`

The vector store is automatically created on first run when processing the policy document.

## 🧪 Testing

Run the comprehensive demo:

```bash
python main.py
```

This tests all scenarios:
- ✅ Balance queries
- ✅ Approved requests
- ✅ Policy violations (60% rule, blackout, notice, frequency)
- ✅ Insufficient balance handling
- ✅ RAG policy queries

## 📝 Policy Document

The `data/company_policy.md` file contains the complete 2-page corporate leave policy with:
- Leave types and accrual rates
- All business rules (60% rule, frequency limits, blackout periods, notice requirements)
- Balance tracking procedures
- Request processes
- Special circumstances

The policy document is automatically vectorized and loaded into the RAG pipeline on first run.

## 🎯 Key Features Highlights

### Unified Chatbot Interface
The agent provides a single, interactive interface for all leave-related queries:
- Balance inquiries
- Leave requests
- Policy explanations
- Alternative suggestions

### Seamless Employee Self-Service
Employees can:
- Check balances instantly
- Submit requests with real-time validation
- Understand denials with policy references
- Get actionable alternatives automatically

### Intelligent Decision Making
The Tool→RAG flow ensures:
1. **Data accuracy**: Real-time balance from database
2. **Policy compliance**: Semantic policy matching via RAG
3. **Consistent decisions**: All rules enforced uniformly

## 🔐 Security Notes

- Ensure `.env` file with API keys is in `.gitignore`
- Database contains employee data - protect appropriately
- Consider encryption for sensitive employee information in production

## 🚧 Future Enhancements

Potential improvements:
- Integration with HRIS systems
- Calendar integration for team visibility
- Multi-level approval workflows
- Reporting and analytics dashboard
- Slack/Teams chatbot integration

## 📄 License

This project is provided as-is for demonstration purposes.

## 🤝 Support

For questions or issues:
- Review the policy document: `data/company_policy.md`
- Check demo examples in `main.py`
- Review code documentation in source files

---

**Built with**: Python, LangChain, OpenAI, ChromaDB, SQLite

**Architecture**: Tool + RAG Integration for Enterprise AI Agents
