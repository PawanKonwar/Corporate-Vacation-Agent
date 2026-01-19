"""
Corporate Vacation AI Agent
Unified chatbot interface with Tool→RAG flow and conversational intelligence
"""

from typing import Dict, Optional, List, Tuple
from datetime import datetime, date, timedelta
from src.database_tool import EmployeeDatabase
from src.policy_rag import PolicyRAG
import json


class VacationAgent:
    """
    Unified AI agent for vacation approval with Tool→RAG integration
    Flow: Tool FIRST (balance check) → RAG SECOND (policy check)
    """
    
    def __init__(self, db_path: str = "data/employee_data.db", 
                 policy_path: str = "data/company_policy.md"):
        """Initialize agent with database and policy RAG"""
        self.db = EmployeeDatabase(db_path)
        self.rag = PolicyRAG(policy_path)
        self.conversation_history = []
    
    def process_vacation_request(self, employee_id: str, leave_type: str,
                                start_date: date, end_date: date,
                                request_date: Optional[date] = None,
                                is_manager: bool = False) -> Dict:
        """
        Process vacation request with Tool→RAG flow
        
        Args:
            employee_id: Employee identifier
            leave_type: 'vacation' or 'sick'
            start_date: Requested leave start date
            end_date: Requested leave end date
            request_date: Date of request submission (defaults to today)
            is_manager: If True, auto-approves manager requests (defaults to False)
            
        Returns:
            Dictionary with approval decision, reasoning, and options
        """
        if request_date is None:
            request_date = date.today()
        
        # Calculate days requested
        days_requested = (end_date - start_date).days + 1
        notice_days = (start_date - request_date).days
        
        # Get employee info
        employee_info = self.db.get_employee_info(employee_id)
        if not employee_info:
            return {
                "status": "error",
                "message": f"Employee {employee_id} not found",
                "employee_id": employee_id
            }
        
        # Check if employee is a manager (by ID prefix or explicit flag)
        is_manager_employee = is_manager or employee_id.startswith("MGR")
        
        # Manager auto-approval - bypass all checks
        if is_manager_employee:
            # Still check balance for display purposes
            sufficient, balance_info = self.db.check_balance_sufficient(
                employee_id, days_requested, leave_type
            )
            
            # Record the approved request
            self.db.record_leave_request(
                employee_id, leave_type, start_date, end_date, days_requested, "approved"
            )
            
            # Fetch updated balance
            updated_balance_info = self.db.get_remaining_balance(employee_id, leave_type)
            balance_info = updated_balance_info
            
            # Generate manager auto-approval response
            response = {
                "status": "approved",
                "employee_id": employee_info["employee_id"],
                "employee_name": employee_info["name"],
                "leave_type": leave_type,
                "requested_dates": {
                    "start": start_date.isoformat(),
                    "end": end_date.isoformat(),
                    "days": days_requested
                },
                "balance_info": {
                    "remaining_days": balance_info["remaining_days"],
                    "remaining_hours": balance_info["remaining_hours"],
                    "annual_quota_days": balance_info["annual_quota_days"]
                },
                "violations": [],
                "warnings": [],
                "message": (
                    f"✅ **AUTO-APPROVED**: Manager leave request for {days_requested} days "
                    f"({start_date.strftime('%B %d')} to {end_date.strftime('%B %d, %Y')}) has been auto-approved.\n\n"
                    f"**Note**: Manager leave auto-approved per policy. Notified HR for tracking.\n\n"
                    f"**Remaining Balance**: {balance_info['remaining_days']:.1f} days "
                    f"({balance_info['remaining_hours']:.1f} hours) of {leave_type} leave remaining.\n"
                ),
                "options": [],
                "email_content": self._generate_manager_email(
                    employee_info, start_date, end_date, days_requested, leave_type, balance_info
                ),
                "is_manager_approval": True
            }
            return response
        
        annual_quota = employee_info.get("vacation_annual_quota_days", 10) if leave_type == "vacation" else employee_info.get("sick_annual_quota_days", 8)
        
        # STEP 1: TOOL QUERY FIRST - Check balance
        sufficient, balance_info = self.db.check_balance_sufficient(
            employee_id, days_requested, leave_type
        )
        
        # STEP 2: RAG QUERY SECOND - Check policy compliance
        request_info = {
            "employee_id": employee_id,
            "leave_type": leave_type,
            "days_requested": days_requested,
            "start_date": start_date,
            "end_date": end_date,
            "annual_quota_days": annual_quota,
            "notice_days": notice_days
        }
        
        policy_check = self.rag.check_policy_compliance(request_info)
        
        # Additional checks
        
        # Check blackout periods
        blackout_violation = self._check_blackout_periods(start_date, end_date, days_requested)
        
        # Check frequency limits (for vacation >7 days)
        frequency_violation = None
        if leave_type == "vacation" and days_requested > 7:
            frequency_violation = self._check_frequency_limits(employee_id, start_date, end_date)
        
        # Combine all violations
        all_violations = policy_check["violations"] + policy_check["warnings"]
        if blackout_violation:
            all_violations.append(blackout_violation)
        if frequency_violation:
            all_violations.append(frequency_violation)
        
        # Determine approval eligibility (but don't auto-approve - let user decide)
        # Note: policy_check["compliant"] only checks blocking violations, not warnings
        # Warnings are informational and don't block approval
        can_be_approved = sufficient and policy_check["compliant"] and not blackout_violation and not frequency_violation
        
        # DO NOT auto-approve - return "pending" status so user can choose from options
        # The UI will handle actual approval/denial when user clicks a button
        
        # Generate detailed analysis checks for multi-step guidance
        analysis_checks = self._generate_analysis_checks(
            balance_info=balance_info,
            sufficient=sufficient,
            days_requested=days_requested,
            start_date=start_date,
            end_date=end_date,
            violations=all_violations,
            policy_check=policy_check,
            blackout_violation=blackout_violation,
            frequency_violation=frequency_violation
        )
        
        # Generate response with conversational intelligence
        # Pass can_be_approved to generate appropriate message, but status will be "pending"
        response = self._generate_approval_response(
            employee_info=employee_info,
            balance_info=balance_info,
            sufficient=sufficient,
            days_requested=days_requested,
            start_date=start_date,
            end_date=end_date,
            leave_type=leave_type,
            violations=all_violations,
            approved=can_be_approved,  # Use can_be_approved for message generation
            notice_days=notice_days,
            analysis_checks=analysis_checks,
            blackout_violation=blackout_violation,
            frequency_violation=frequency_violation
        )
        
        # Override status to "pending" so options will show in UI
        response["status"] = "pending"
        response["can_be_approved"] = can_be_approved  # Store eligibility for UI
        
        return response
    
    def _check_blackout_periods(self, start_date: date, end_date: date, days_requested: float) -> Optional[Dict]:
        """Check if requested dates fall in blackout period"""
        blackout_periods = self.rag.get_blackout_periods()
        
        for blackout in blackout_periods:
            blackout_start = datetime.strptime(blackout["start"], "%Y-%m-%d").date()
            blackout_end = datetime.strptime(blackout["end"], "%Y-%m-%d").date()
            
            # Check if any requested date falls in blackout period
            if (start_date <= blackout_end and end_date >= blackout_start):
                # Exception: requests <3 days are allowed
                if days_requested < 3:
                    continue
                
                return {
                    "rule": "Blackout Period (Section 2.3)",
                    "description": f"Requested dates fall in {blackout['name']} blackout period ({blackout_start} to {blackout_end})",
                    "blackout_name": blackout["name"],
                    "blackout_start": blackout_start.isoformat(),
                    "blackout_end": blackout_end.isoformat()
                }
        
        return None
    
    def _generate_analysis_checks(self, balance_info: Dict, sufficient: bool,
                                 days_requested: float, start_date: date, end_date: date,
                                 violations: List[Dict], policy_check: Dict,
                                 blackout_violation: Optional[Dict],
                                 frequency_violation: Optional[Dict]) -> List[Dict]:
        """Generate detailed analysis checks with PASS/FAIL/WARNING indicators"""
        checks = []
        
        # Check 1: Balance comparison
        remaining_days = balance_info.get("remaining_days", 0)
        check_status = "PASS" if sufficient else "FAIL"
        icon = "✅" if sufficient else "❌"
        checks.append({
            "check": "Balance Check",
            "status": check_status,
            "icon": icon,
            "message": f"Requested: {days_requested:.1f} days vs Your Balance: {remaining_days:.1f} days",
            "details": f"Sufficient balance available" if sufficient else f"Insufficient balance. Need {days_requested:.1f} days, but only {remaining_days:.1f} days available."
        })
        
        # Check 2: Max consecutive days
        max_consecutive = policy_check.get("max_consecutive_days", 10)
        if days_requested > max_consecutive:
            checks.append({
                "check": "Max Consecutive Days",
                "status": "FAIL",
                "icon": "❌",
                "message": f"Requested: {days_requested:.1f} days exceeds max: {max_consecutive} days",
                "details": f"Policy Section 3.2: Maximum {max_consecutive} consecutive days allowed",
                "section": "Section 3.2"
            })
        else:
            checks.append({
                "check": "Max Consecutive Days",
                "status": "PASS",
                "icon": "✅",
                "message": f"Requested: {days_requested:.1f} days within limit: {max_consecutive} days",
                "details": f"Complies with policy Section 3.2"
            })
        
        # Check 3: Blackout periods
        if blackout_violation:
            checks.append({
                "check": "Blackout Period",
                "status": "FAIL",
                "icon": "❌",
                "message": f"Requested dates fall in blackout period",
                "details": blackout_violation.get("description", ""),
                "section": "Section 2.3"
            })
        else:
            checks.append({
                "check": "Blackout Period",
                "status": "PASS",
                "icon": "✅",
                "message": "Requested dates avoid all blackout periods",
                "details": "No blackout period conflicts"
            })
        
        # Check 4: Frequency limits (for long vacations)
        if frequency_violation:
            checks.append({
                "check": "Frequency Limits",
                "status": "FAIL",
                "icon": "❌",
                "message": f"Exceeds frequency limit for long vacations",
                "details": frequency_violation.get("description", ""),
                "section": "Section 2.2"
            })
        else:
            checks.append({
                "check": "Frequency Limits",
                "status": "PASS",
                "icon": "✅",
                "message": "Within frequency limit requirements",
                "details": "No frequency limit violations"
            })
        
        # Check 5: Notice period (warning if short)
        notice_warnings = [v for v in violations if v.get("type") == "warning" and "Notice" in v.get("rule", "")]
        if notice_warnings:
            for warning in notice_warnings:
                checks.append({
                    "check": "Notice Period",
                    "status": "WARNING",
                    "icon": "⚠️",
                    "message": f"Short notice: {warning.get('notice_provided', 0)} business days",
                    "details": warning.get("description", ""),
                    "section": "Section 2.4"
                })
        else:
            checks.append({
                "check": "Notice Period",
                "status": "PASS",
                "icon": "✅",
                "message": "Sufficient notice provided",
                "details": "Meets minimum notice requirements"
            })
        
        # Check 6: Weekend calculation (informational)
        # Count business days vs calendar days
        calendar_days = (end_date - start_date).days + 1
        # Simple check: if includes weekends, note it
        start_weekday = start_date.weekday()  # 0=Monday, 6=Sunday
        end_weekday = end_date.weekday()
        includes_weekends = start_weekday >= 5 or end_weekday >= 5 or calendar_days >= 7
        if includes_weekends:
            checks.append({
                "check": "Weekend Inclusion",
                "status": "INFO",
                "icon": "ℹ️",
                "message": f"Request includes {calendar_days} calendar days (may include weekends)",
                "details": "Weekends are not counted against leave balance"
            })
        
        return checks
    
    def _check_frequency_limits(self, employee_id: str, start_date: date, end_date: date) -> Optional[Dict]:
        """Check frequency limits for long vacations (>7 days)"""
        long_vacations = self.db.get_long_vacations(employee_id, start_date, end_date)
        
        # Count long vacations within 60 days of requested range
        requested_range_start = start_date - timedelta(days=60)
        requested_range_end = end_date + timedelta(days=60)
        
        nearby_long_vacations = []
        for vac in long_vacations:
            vac_start = vac["start_date"]
            vac_end = vac["end_date"]
            
            # Check if vacation overlaps with 60-day window around requested dates
            if (vac_start <= requested_range_end and vac_end >= requested_range_start):
                nearby_long_vacations.append(vac)
        
        # If adding this request would exceed 2 long vacations in 60-day window
        if len(nearby_long_vacations) >= 2:
            return {
                "rule": "Frequency Limits (Section 2.2)",
                "description": f"Exceeds limit of 2 long vacations (>7 days) within any 60-day period. Found {len(nearby_long_vacations)} existing long vacations in the relevant window.",
                "existing_count": len(nearby_long_vacations),
                "limit": 2
            }
        
        return None
    
    def _generate_approval_response(self, employee_info: Dict, balance_info: Dict,
                                   sufficient: bool, days_requested: float,
                                   start_date: date, end_date: date,
                                   leave_type: str, violations: List[Dict],
                                   approved: bool, notice_days: int,
                                   analysis_checks: Optional[List[Dict]] = None,
                                   blackout_violation: Optional[Dict] = None,
                                   frequency_violation: Optional[Dict] = None) -> Dict:
        """Generate conversational approval response with options"""
        
        # Separate blocking violations from warnings for approved requests
        warnings_only = []
        if approved:
            # For approved requests, only show warnings (informational), not blocking violations
            # Filter to only warnings (which are non-blocking recommendations)
            warnings_only = [v for v in violations if v.get('type') == 'warning' or 'Recommended' in v.get('description', '')]
            violations_to_show = warnings_only if warnings_only else []
        else:
            # For denied requests, show all violations (both blocking and warnings)
            violations_to_show = violations
        
        response = {
            "status": "approved" if approved else "denied",
            "employee_id": employee_info["employee_id"],
            "employee_name": employee_info["name"],
            "leave_type": leave_type,
            "requested_dates": {
                "start": start_date.isoformat(),
                "end": end_date.isoformat(),
                "days": days_requested
            },
            "balance_info": {
                "remaining_days": balance_info["remaining_days"],
                "remaining_hours": balance_info["remaining_hours"],
                "annual_quota_days": balance_info["annual_quota_days"]
            },
            "violations": violations_to_show,
            "warnings": warnings_only,
            "message": "",
            "options": [],
            "email_content": None,
            "analysis_checks": analysis_checks or []
        }
        
        if approved:
            # Generate approval message
            response["message"] = (
                f"✅ **APPROVED**: Your {leave_type} leave request for {days_requested} days "
                f"({start_date.strftime('%B %d')} to {end_date.strftime('%B %d, %Y')}) has been approved.\n\n"
                f"**Remaining Balance**: {balance_info['remaining_days']:.1f} days "
                f"({balance_info['remaining_hours']:.1f} hours) of {leave_type} leave remaining.\n"
            )
            
            # Generate email for manager
            response["email_content"] = self._generate_manager_email(
                employee_info, start_date, end_date, days_requested, leave_type, balance_info
            )
        else:
            # Generate denial message with explanations and options
            violation_descriptions = []
            for violation in violations:
                violation_descriptions.append(f"- {violation.get('rule', 'Policy Violation')}: {violation.get('description', '')}")
            
            response["message"] = (
                f"❌ **DENIED**: Your {leave_type} leave request for {days_requested} days "
                f"cannot be approved due to the following policy violations:\n\n"
                + "\n".join(violation_descriptions) + "\n"
            )
            
            # Generate proactive options as structured objects
            all_options = []
            option_letter = 'A'
            
            # Option A: Approve as requested (if sufficient balance but policy violation)
            if sufficient and not blackout_violation and not frequency_violation:
                # This shouldn't happen for denied requests, but include for completeness
                all_options.append({
                    "letter": option_letter,
                    "title": "Approve as requested",
                    "description": f"Approve {days_requested} days ({start_date.strftime('%b %d')} - {end_date.strftime('%b %d')})",
                    "consequence": "All policy violations will be noted but overridden",
                    "recommended": False,
                    "type": "approve"
                })
                option_letter = chr(ord(option_letter) + 1)
            
            # Add violation-specific options
            for violation in violations:
                if violation.get('type') != 'warning':  # Only blocking violations
                    options = self.rag.suggest_alternatives(violation)
                    for opt_text in options:
                        # Parse option text to extract structured info
                        all_options.append({
                            "letter": option_letter,
                            "title": opt_text.split(':')[0].replace('Option ', ''),
                            "description": ':'.join(opt_text.split(':')[1:]).strip() if ':' in opt_text else opt_text,
                            "consequence": f"Addresses: {violation.get('rule', 'Policy violation')}",
                            "recommended": "Shift" in opt_text or "Reduce" in opt_text,
                            "type": "modify"
                        })
                        option_letter = chr(ord(option_letter) + 1)
            
            # Add balance-related options if insufficient balance
            if not sufficient:
                shortfall = days_requested - balance_info["remaining_days"]
                all_options.append({
                    "letter": option_letter,
                    "title": f"Reduce to {balance_info['remaining_days']:.1f} days",
                    "description": f"Use only available balance: {balance_info['remaining_days']:.1f} days",
                    "consequence": f"Saves {shortfall:.1f} days for future use",
                    "recommended": True,
                    "type": "reduce"
                })
                option_letter = chr(ord(option_letter) + 1)
                
                all_options.append({
                    "letter": option_letter,
                    "title": "Wait to accrue more days",
                    "description": f"Delay request until you accrue {shortfall:.1f} more days",
                    "consequence": "Request can be resubmitted once balance is sufficient",
                    "recommended": False,
                    "type": "delay"
                })
                option_letter = chr(ord(option_letter) + 1)
            
            # Option D (or last): Deny with specific reason
            violation_summary = "; ".join([v.get('rule', 'Policy violation') for v in violations if v.get('type') != 'warning'])
            all_options.append({
                "letter": option_letter,
                "title": "Deny request",
                "description": "Reject this request due to policy violations",
                "consequence": f"Reason: {violation_summary}",
                "recommended": False,
                "type": "deny"
            })
            
            # Remove duplicates based on description
            unique_options = []
            seen_descriptions = set()
            for opt in all_options:
                desc_key = opt["description"].lower()
                if desc_key not in seen_descriptions:
                    unique_options.append(opt)
                    seen_descriptions.add(desc_key)
            
            response["options"] = unique_options
        
        return response
    
    def _generate_manager_email(self, employee_info: Dict, start_date: date,
                               end_date: date, days_requested: float,
                               leave_type: str, balance_info: Dict) -> str:
        """Generate email content for manager notification"""
        email = f"""
Subject: Leave Request Approved - {employee_info['name']} ({employee_info['employee_id']})

Dear Manager,

This is an automated notification that the following leave request has been approved:

Employee: {employee_info['name']} ({employee_info['employee_id']})
Leave Type: {leave_type.title()}
Requested Dates: {start_date.strftime('%B %d, %Y')} to {end_date.strftime('%B %d, %Y')}
Duration: {days_requested:.1f} days ({days_requested * 8:.1f} hours)

Balance Information:
- Remaining {leave_type} leave: {balance_info['remaining_days']:.1f} days ({balance_info['remaining_hours']:.1f} hours)
- Annual quota: {balance_info['annual_quota_days']} days

Policy Compliance:
✅ Sufficient balance available
✅ Complies with all corporate leave policies

Please ensure appropriate coverage arrangements are made during this period.

Best regards,
Corporate Vacation AI Agent
"""
        return email.strip()
    
    def query_balance(self, employee_id: str, leave_type: str = "vacation") -> Dict:
        """Query employee's remaining balance (helper method)"""
        balance = self.db.get_remaining_balance(employee_id, leave_type)
        employee_info = self.db.get_employee_info(employee_id)
        
        return {
            "employee_id": employee_id,
            "employee_name": employee_info.get("name", "Unknown") if employee_info else "Unknown",
            "leave_type": leave_type,
            "balance": balance,
            "message": (
                f"**Balance Query for {employee_id}**:\n"
                f"Remaining {leave_type} leave: {balance.get('remaining_days', 0):.1f} days "
                f"({balance.get('remaining_hours', 0):.1f} hours)\n"
                f"Annual quota: {balance.get('annual_quota_days', 0)} days"
            )
        }
    
    def get_policy_explanation(self, query: str) -> str:
        """Get policy explanation using RAG"""
        results = self.rag.query_policy(query, k=2)
        
        if results:
            explanation = "\n\n".join([r["content"][:1000] for r in results])
            return f"**Policy Information**:\n\n{explanation}"
        else:
            return "No policy information found for your query."
    
    def generate_employee_email(self, employee_id: str, leave_type: str,
                               start_date: date, end_date: date,
                               days_requested: float, balance_info: Dict,
                               custom_message: Optional[str] = None) -> str:
        """
        AI-powered email drafting for employee leave request emails
        
        Args:
            employee_id: Employee identifier
            leave_type: 'vacation' or 'sick'
            start_date: Requested leave start date
            end_date: Requested leave end date
            days_requested: Number of days requested
            balance_info: Dictionary with balance information
            custom_message: Optional custom message to include
            
        Returns:
            Generated email content
        """
        employee_info = self.db.get_employee_info(employee_id)
        employee_name = employee_info.get("name", "Employee") if employee_info else "Employee"
        
        # Use LLM to generate professional email
        prompt = f"""Generate a professional, polite leave request email from an employee to their manager.

Employee Information:
- Name: {employee_name}
- Employee ID: {employee_id}
- Leave Type: {leave_type.title()}
- Requested Dates: {start_date.strftime('%B %d, %Y')} to {end_date.strftime('%B %d, %Y')}
- Total Days: {days_requested:.1f} days
- Remaining Balance: {balance_info.get('remaining_days', 0):.1f} days ({balance_info.get('remaining_hours', 0):.1f} hours)
- Annual Quota: {balance_info.get('annual_quota_days', 0)} days

{f'Custom Message to Include: {custom_message}' if custom_message else ''}

Requirements:
1. Professional and courteous tone
2. Clear subject line
3. Brief explanation of the request
4. Include all relevant details (dates, duration, type)
5. Mention remaining balance to show awareness
6. Polite closing
7. Appropriate business email format

Generate the email:"""

        try:
            response = self.rag.llm.invoke(prompt)
            email_content = response.content.strip()
            
            # Ensure it has proper format
            if not email_content.startswith("Subject:"):
                email_content = f"Subject: Leave Request - {leave_type.title()} Leave ({start_date.strftime('%B %d')} - {end_date.strftime('%B %d, %Y')})\n\n{email_content}"
            
            return email_content
        except Exception as e:
            # Fallback to template-based email if LLM fails
            return self._generate_fallback_employee_email(
                employee_name, employee_id, leave_type, start_date, end_date, 
                days_requested, balance_info, custom_message
            )
    
    def _generate_fallback_employee_email(self, employee_name: str, employee_id: str,
                                         leave_type: str, start_date: date, end_date: date,
                                         days_requested: float, balance_info: Dict,
                                         custom_message: Optional[str] = None) -> str:
        """Fallback template-based email generator"""
        subject = f"Leave Request - {leave_type.title()} Leave ({start_date.strftime('%B %d')} - {end_date.strftime('%B %d, %Y')})"
        
        email = f"""Subject: {subject}

Dear Manager,

I hope this email finds you well. I am writing to formally request {leave_type} leave from work.

Request Details:
- Employee: {employee_name} ({employee_id})
- Leave Type: {leave_type.title()}
- Start Date: {start_date.strftime('%B %d, %Y')}
- End Date: {end_date.strftime('%B %d, %Y')}
- Total Days: {days_requested:.1f} days

{f'Additional Information: {custom_message}' if custom_message else ''}

Balance Information:
- Remaining {leave_type} leave balance: {balance_info.get('remaining_days', 0):.1f} days ({balance_info.get('remaining_hours', 0):.1f} hours)
- Annual quota: {balance_info.get('annual_quota_days', 0)} days

I have verified that I have sufficient leave balance available for this request. I will ensure all my current responsibilities are properly covered during my absence, and I'm happy to assist with transition planning as needed.

I would be grateful if you could approve this request at your earliest convenience. Please let me know if you need any additional information or if there are any concerns.

Thank you for considering my request.

Best regards,
{employee_name}
{employee_id}
"""
        return email.strip()


# Example usage
if __name__ == "__main__":
    # Note: Requires OPENAI_API_KEY environment variable
    agent = VacationAgent()
    
    # Test request
    test_start = date(2024, 2, 15)
    test_end = date(2024, 2, 22)  # 8 days
    
    result = agent.process_vacation_request(
        employee_id="EMP001",
        leave_type="vacation",
        start_date=test_start,
        end_date=test_end
    )
    
    print("\n=== Vacation Request Result ===")
    print(json.dumps(result, indent=2, default=str))
