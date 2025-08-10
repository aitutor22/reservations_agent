"""
Guardrails for Restaurant RealtimeAgent
Prevents misuse and ensures safe, appropriate interactions
"""

from typing import Any, Dict, List, Union
from agents import GuardrailFunctionOutput, RunContextWrapper, input_guardrail, output_guardrail
from agents.items import TResponseInputItem


@input_guardrail
async def restaurant_input_guardrail(
    ctx: RunContextWrapper,
    agent: Any,  # Agent type from TYPE_CHECKING
    input: Union[str, List[TResponseInputItem]]
) -> GuardrailFunctionOutput:
    """
    Input guardrail for restaurant reservation agent.
    Prevents misuse attempts and inappropriate requests.
    """
    
    # Handle both string and list inputs
    if isinstance(input, list):
        # For list inputs, concatenate all text content
        input_text = " ".join(str(item) for item in input)
    else:
        input_text = str(input) if input else ""
    
    # Convert input to lowercase for checking
    input_lower = input_text.lower()
    
    # Define prohibited patterns that might indicate misuse
    prohibited_patterns = [
        # Attempts to access system or execute commands
        ("system", "command"), ("execute", "script"), ("run", "code"),
        ("bash", "shell"), ("sudo", "admin"), ("password", "credential"),
        
        # Attempts to manipulate or access unauthorized data
        ("delete", "all"), ("drop", "table"), ("sql", "injection"),
        ("hack", "system"), ("bypass", "security"), ("exploit", "vulnerability"),
        
        # Inappropriate content
        ("illegal", "activity"), ("harmful", "content"), ("explicit", "material"),
        
        # Attempts to get the agent to act outside its scope
        ("ignore", "instructions"), ("forget", "rules"), ("override", "settings"),
        ("pretend", "you"), ("act", "as"), ("roleplay", "as"),
        
        # Financial fraud attempts
        ("credit", "card", "fraud"), ("steal", "money"), ("launder", "money"),
        ("phishing", "scam"), ("identity", "theft")
    ]
    
    # Check for prohibited patterns
    tripwire_triggered = False
    detected_issue = None
    
    for pattern in prohibited_patterns:
        # Check if all words in the pattern appear in the input
        if all(word in input_lower for word in pattern):
            tripwire_triggered = True
            detected_issue = f"Input contains potentially harmful pattern: {' '.join(pattern)}"
            break
    
    # Check for attempts to extract system information
    system_info_keywords = [
        "api key", "api_key", "secret key", "private key",
        "environment variable", "env var", "config file",
        "database password", "db password", "connection string",
        "internal system", "backend system", "server info"
    ]
    
    if not tripwire_triggered:
        for keyword in system_info_keywords:
            if keyword in input_lower:
                tripwire_triggered = True
                detected_issue = f"Input requests sensitive system information: {keyword}"
                break
    
    # Check for extremely long inputs that might be attempting buffer overflow
    if not tripwire_triggered and len(input_text) > 5000:
        tripwire_triggered = True
        detected_issue = "Input exceeds maximum allowed length"
    
    # Check for suspicious patterns in reservation requests
    if not tripwire_triggered:
        # Check for unreasonable party sizes
        import re
        party_size_match = re.search(r'\b(\d+)\s*(people|guests|party)\b', input_lower)
        if party_size_match:
            party_size = int(party_size_match.group(1))
            if party_size > 50:  # Reasonable limit for a ramen restaurant
                tripwire_triggered = True
                detected_issue = f"Unreasonable party size requested: {party_size}"
    
    # Log the guardrail check
    if tripwire_triggered:
        print(f"[InputGuardrail] BLOCKED: {detected_issue}")
        print(f"[InputGuardrail] Original input: {input_text[:100]}...")  # Log first 100 chars
    else:
        print(f"[InputGuardrail] PASSED: Input appears safe")
    
    return GuardrailFunctionOutput(
        output_info={
            "checked": True,
            "issue_detected": detected_issue if tripwire_triggered else None,
            "input_length": len(input_text)
        },
        tripwire_triggered=tripwire_triggered
    )


@output_guardrail
async def restaurant_output_guardrail(
    ctx: RunContextWrapper,
    agent: Any,  # Agent type
    output: Any  # Can be various output types
) -> GuardrailFunctionOutput:
    """
    Output guardrail for restaurant reservation agent.
    Ensures responses don't contain sensitive information or inappropriate content.
    """
    
    # Convert output to string for checking
    output_text = str(output) if output else ""
    output_lower = output_text.lower()
    
    # Check for accidental exposure of sensitive information
    sensitive_patterns = [
        # API keys and credentials (common formats)
        r'api[_-]?key["\']?\s*[:=]\s*["\']?[\w-]{10,}',  # Reduced min length to catch more patterns
        r'sk-[\w-]{10,}',  # OpenAI-style keys
        r'secret[_-]?key["\']?\s*[:=]\s*["\']?[\w-]{10,}',
        r'password["\']?\s*[:=]\s*["\']?[\w-]+',
        r'token["\']?\s*[:=]\s*["\']?[\w-]{20,}',
        
        # Database connection strings
        r'mongodb://[\w:@.-]+',
        r'postgres://[\w:@.-]+',
        r'mysql://[\w:@.-]+',
        
        # Environment variables that shouldn't be exposed
        r'OPENAI_API_KEY',
        r'DATABASE_URL',
        r'SECRET_KEY',
        
        # Internal system paths
        r'/home/[\w/]+',
        r'/var/[\w/]+',
        r'/etc/[\w/]+',
        r'C:\\Users\\[\w\\]+',  # Windows paths with single backslash
        r'C:\\\\Users\\\\[\w\\\\]+',  # Windows paths with escaped backslash
    ]
    
    tripwire_triggered = False
    detected_issue = None
    
    # Check for sensitive patterns using regex
    import re
    for pattern in sensitive_patterns:
        if re.search(pattern, output_text, re.IGNORECASE):
            tripwire_triggered = True
            detected_issue = f"Output contains potentially sensitive information matching pattern: {pattern[:30]}..."
            break
    
    # Check for inappropriate language or content
    if not tripwire_triggered:
        inappropriate_words = [
            "hack", "exploit", "vulnerability", "injection",
            "malware", "virus", "trojan", "backdoor",
            "profanity", "explicit", "inappropriate"
        ]
        
        for word in inappropriate_words:
            if word in output_lower:
                # Context check - some words might be okay in certain contexts
                # For example, "injection" might appear in "SQL injection prevention"
                if word == "injection" and "prevention" in output_lower:
                    continue
                if word == "vulnerability" and ("report" in output_lower or "fix" in output_lower):
                    continue
                    
                tripwire_triggered = True
                detected_issue = f"Output contains potentially inappropriate content: {word}"
                break
    
    # Check for attempts to provide information outside restaurant scope
    if not tripwire_triggered:
        out_of_scope_patterns = [
            ("how", "to", "hack"),
            ("how", "to", "exploit"),
            ("bypass", "security"),
            ("code", "injection"),
            ("system", "command"),
        ]
        
        for pattern in out_of_scope_patterns:
            if all(word in output_lower for word in pattern):
                tripwire_triggered = True
                detected_issue = f"Output attempts to provide out-of-scope information: {' '.join(pattern)}"
                break
    
    # Check for personal information that shouldn't be shared broadly
    if not tripwire_triggered:
        # Phone number patterns (various formats including Singapore)
        phone_patterns = [
            r'\b\d{3}[-.]?\d{3}[-.]?\d{4}\b',  # 555-123-4567 or 555.123.4567 (US format)
            r'\(\d{3}\)\s?\d{3}[-.]?\d{4}',  # (555) 123-4567 (US with area code)
            r'\b[689]\d{3}[-.]?\d{4}\b',  # 6123-4567, 8123-4567, 9123-4567 (Singapore mobile)
            r'\b\d{4}[-.]?\d{4}\b',  # 1234-5678 or 1234.5678 (Singapore format)
        ]
        # Use a set to avoid counting overlapping matches
        phone_matches = set()
        for pattern in phone_patterns:
            matches = re.findall(pattern, output_text)
            phone_matches.update(matches)
        phone_matches = list(phone_matches)
        if len(phone_matches) > 3:  # Allow up to 3 phone numbers (being more lenient for examples)
            tripwire_triggered = True
            detected_issue = f"Output contains multiple phone numbers ({len(phone_matches)}), potential privacy issue"
        
        # Email pattern
        email_pattern = r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b'
        email_matches = re.findall(email_pattern, output_text)
        if len(email_matches) > 2:  # Allow up to 2 emails
            tripwire_triggered = True
            detected_issue = f"Output contains multiple email addresses ({len(email_matches)}), potential privacy issue"
    
    # Log the guardrail check
    if tripwire_triggered:
        print(f"[OutputGuardrail] BLOCKED: {detected_issue}")
        print(f"[OutputGuardrail] Output preview: {output_text[:100]}...")  # Log first 100 chars
    else:
        print(f"[OutputGuardrail] PASSED: Output appears safe")
    
    return GuardrailFunctionOutput(
        output_info={
            "checked": True,
            "issue_detected": detected_issue if tripwire_triggered else None,
            "output_length": len(output_text)
        },
        tripwire_triggered=tripwire_triggered
    )


# Additional utility function for content filtering
async def check_reservation_validity(reservation_data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Additional check for reservation data validity.
    This can be called by the reservation tools to ensure data integrity.
    """
    
    issues = []
    
    # Check party size
    party_size = reservation_data.get("party_size", 0)
    if party_size <= 0:
        issues.append("Invalid party size: must be at least 1")
    elif party_size > 50:
        issues.append("Party size too large: maximum 50 for restaurant capacity")
    
    # Check date/time validity
    import datetime
    reservation_date = reservation_data.get("date")
    reservation_time = reservation_data.get("time")
    
    if reservation_date:
        try:
            date_obj = datetime.datetime.strptime(reservation_date, "%Y-%m-%d")
            # Check if date is not too far in the future (e.g., max 6 months)
            max_future_date = datetime.datetime.now() + datetime.timedelta(days=180)
            if date_obj > max_future_date:
                issues.append("Reservation date too far in the future (max 6 months)")
            # Check if date is not in the past
            if date_obj.date() < datetime.datetime.now().date():
                issues.append("Cannot make reservations for past dates")
        except ValueError:
            issues.append("Invalid date format")
    
    # Check for suspicious patterns in special requests
    special_requests = reservation_data.get("special_requests", "")
    if special_requests:
        suspicious_keywords = ["hack", "exploit", "system", "admin", "password"]
        for keyword in suspicious_keywords:
            if keyword in special_requests.lower():
                issues.append(f"Suspicious content in special requests: {keyword}")
                break
    
    return {
        "valid": len(issues) == 0,
        "issues": issues,
        "data": reservation_data if len(issues) == 0 else None
    }