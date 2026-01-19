"""
Policy RAG Pipeline
Vectorizes and retrieves information from the Corporate Leave Policy document
"""

import os
from typing import List, Dict, Optional
from pathlib import Path
from dotenv import load_dotenv

# Load environment variables from .env file BEFORE initializing OpenAI clients
# Find .env file in project root (parent directory of src/)
env_path = Path(__file__).parent.parent / '.env'
load_dotenv(dotenv_path=env_path)

from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_openai import OpenAIEmbeddings, ChatOpenAI
from langchain_community.vectorstores import Chroma
from langchain_core.documents import Document


class PolicyRAG:
    """RAG system for querying corporate leave policy"""
    
    def __init__(self, policy_path: str = "data/company_policy.md", 
                 persist_directory: str = "data/chroma_db"):
        """
        Initialize RAG pipeline with policy document
        
        Args:
            policy_path: Path to policy markdown file
            persist_directory: Directory to persist vector store
        """
        self.policy_path = policy_path
        self.persist_directory = persist_directory
        
        # Initialize embeddings and LLM
        self.embeddings = OpenAIEmbeddings()
        self.llm = ChatOpenAI(model="gpt-4o-mini", temperature=0)
        
        # Load or create vector store
        self._initialize_vector_store()
    
    def _initialize_vector_store(self):
        """Load policy document and create/load vector store"""
        # Check if vector store exists
        if os.path.exists(self.persist_directory) and os.listdir(self.persist_directory):
            # Load existing vector store (LangChain 1.x uses embedding_function)
            self.vectorstore = Chroma(
                persist_directory=self.persist_directory,
                embedding_function=self.embeddings
            )
            print(f"Loaded existing vector store from {self.persist_directory}")
        else:
            # Create new vector store
            self._create_vector_store()
    
    def _create_vector_store(self):
        """Read policy document, split into chunks, and create vector store"""
        # Read policy document
        with open(self.policy_path, 'r', encoding='utf-8') as f:
            policy_text = f.read()
        
        # Create document
        documents = [Document(page_content=policy_text, metadata={"source": "company_policy.md"})]
        
        # Split into chunks
        text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=1000,
            chunk_overlap=200,
            length_function=len
        )
        chunks = text_splitter.split_documents(documents)
        
        # Create vector store
        self.vectorstore = Chroma.from_documents(
            documents=chunks,
            embedding=self.embeddings,
            persist_directory=self.persist_directory
        )
        print(f"Created vector store with {len(chunks)} chunks from policy document")
    
    def query_policy(self, query: str, k: int = 3) -> List[Dict]:
        """
        Query policy document using RAG
        
        Args:
            query: Natural language query about policy
            k: Number of relevant chunks to retrieve
            
        Returns:
            List of dictionaries with relevant policy sections
        """
        # Retrieve relevant chunks
        docs = self.vectorstore.similarity_search(query, k=k)
        
        results = []
        for doc in docs:
            results.append({
                "content": doc.page_content,
                "metadata": doc.metadata
            })
        
        return results
    
    def check_policy_compliance(self, request_info: Dict) -> Dict:
        """
        Check if a leave request complies with policy rules
        
        Args:
            request_info: Dictionary with:
                - employee_id
                - leave_type (vacation/sick)
                - days_requested
                - start_date
                - end_date
                - annual_quota_days
                - notice_days (days between request date and start date)
                
        Returns:
            Dictionary with compliance check results
        """
        violations = []
        warnings = []
        compliant = True
        
        leave_type = request_info.get("leave_type", "vacation").lower()
        days_requested = request_info.get("days_requested", 0)
        annual_quota = request_info.get("annual_quota_days", 10)
        notice_days = request_info.get("notice_days", 0)
        
        # Check 60% Rule (Section 2.1) - for vacation only
        if leave_type == "vacation":
            max_single_request = annual_quota * 0.6
            if days_requested > max_single_request:
                violations.append({
                    "rule": "60% Rule (Section 2.1)",
                    "description": f"Cannot use more than 60% of annual allowance ({max_single_request} days) in a single request",
                    "requested": days_requested,
                    "maximum": max_single_request
                })
                compliant = False
        
        # Check Notice Period (Section 2.4)
        if days_requested > 3:
            if notice_days < 14:  # 2 weeks
                violations.append({
                    "rule": "Notice Period (Section 2.4)",
                    "description": f"Minimum 2-week notice required for leaves >3 days",
                    "notice_provided": notice_days,
                    "required": 14
                })
                compliant = False
        elif days_requested >= 1:
            if notice_days < 5:  # 5 business days
                warnings.append({
                    "rule": "Notice Period (Section 2.4)",
                    "description": "Recommended minimum 5 business days notice for 1-3 day leaves",
                    "notice_provided": notice_days,
                    "type": "warning"  # Mark as non-blocking warning
                })
        
        # Check Blackout Periods (Section 2.3) - will be checked in agent logic
        # This is date-specific and requires calendar checking
        
        # Frequency limits will be checked separately using database
        
        return {
            "compliant": compliant,
            "violations": violations,
            "warnings": warnings,
            "section_references": [v["rule"] for v in violations + warnings]
        }
    
    def get_blackout_periods(self) -> List[Dict]:
        """
        Get blackout periods from policy
        Returns list of blackout period date ranges
        """
        # Query policy for blackout periods
        query = "What are the blackout periods for vacation requests? Include specific dates for fiscal quarters and year-end"
        results = self.query_policy(query, k=2)
        
        # Parse blackout periods (hardcoded based on policy document)
        blackout_periods = [
            {"name": "Q1 End", "start": "2024-03-18", "end": "2024-03-31"},
            {"name": "Q2 End", "start": "2024-06-17", "end": "2024-06-30"},
            {"name": "Q3 End", "start": "2024-09-16", "end": "2024-09-30"},
            {"name": "Year-End", "start": "2024-11-15", "end": "2024-12-31"},
        ]
        
        return blackout_periods
    
    def explain_policy_section(self, section_name: str) -> str:
        """
        Get detailed explanation of a policy section
        
        Args:
            section_name: Name of policy section (e.g., "60% Rule", "Notice Period")
            
        Returns:
            Detailed explanation of the section
        """
        query = f"Explain the {section_name} policy rule in detail. Include examples and requirements."
        results = self.query_policy(query, k=2)
        
        if results:
            # Combine relevant chunks
            explanation = "\n\n".join([r["content"] for r in results])
            return explanation
        else:
            return f"No information found about {section_name}"
    
    def suggest_alternatives(self, violation_info: Dict) -> List[str]:
        """
        Suggest alternative options when a request violates policy
        
        Args:
            violation_info: Information about the violation
            
        Returns:
            List of alternative options as strings
        """
        alternatives = []
        
        rule = violation_info.get("rule", "")
        
        if "60% Rule" in rule:
            max_days = violation_info.get("maximum", 0)
            requested = violation_info.get("requested", 0)
            alternatives.append(
                f"Option A: Reduce request to {max_days} days to comply with 60% rule"
            )
            alternatives.append(
                f"Option B: Split into two separate requests (e.g., {max_days} days now, {requested - max_days} days later)"
            )
        
        elif "Notice Period" in rule:
            required = violation_info.get("required", 14)
            provided = violation_info.get("notice_provided", 0)
            days_needed = required - provided
            alternatives.append(
                f"Option A: Shift start date {days_needed} days later to meet {required}-day notice requirement"
            )
            alternatives.append(
                "Option B: Request manager override for emergency circumstances"
            )
        
        elif "Blackout Period" in rule:
            alternatives.append(
                "Option A: Shift dates to avoid blackout period"
            )
            alternatives.append(
                "Option B: Reduce request to less than 3 days (allowed during blackout)"
            )
            alternatives.append(
                "Option C: Request manager override for special circumstances"
            )
        
        elif "Frequency Limits" in rule:
            alternatives.append(
                "Option A: Delay this request until the 60-day window expires"
            )
            alternatives.append(
                "Option B: Reduce duration to 7 days or less to avoid 'long vacation' classification"
            )
        
        return alternatives


# Example usage
if __name__ == "__main__":
    # Note: Requires OPENAI_API_KEY environment variable
    rag = PolicyRAG()
    
    # Test query
    results = rag.query_policy("What is the 60% rule for vacation requests?")
    print("\nPolicy Query Results:")
    for i, result in enumerate(results, 1):
        print(f"\n--- Result {i} ---")
        print(result["content"][:500])
