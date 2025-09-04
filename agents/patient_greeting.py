"""
Patient Greeting Agent - Medical Appointment Scheduling System
===========================================================

This module handles the initial patient greeting and information collection
for the medical appointment scheduling workflow using Google's Gemini API.

Key Responsibilities:
- Welcome patients professionally
- Collect basic patient information (name, DOB, doctor preference, location)
- Extract information using NLP and pattern matching
- Validate and sanitize patient inputs
- Handle missing information with follow-up questions
- Maintain HIPAA-compliant communication standards

Author: RagaAI Case Study Implementation
Date: September 2025
"""

import re
import logging
from typing import Dict, Any, Optional, List, Tuple
from datetime import datetime, timedelta
from langchain_core.messages import HumanMessage, AIMessage, SystemMessage

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# ============================================================================
# DATA VALIDATION PATTERNS
# ============================================================================

# Regex patterns for extracting patient information
NAME_PATTERNS = [
    r"my name is ([A-Za-z\s\-'\.]+)",
    r"i'm ([A-Za-z\s\-'\.]+)",
    r"i am ([A-Za-z\s\-'\.]+)",
    r"this is ([A-Za-z\s\-'\.]+)",
    r"call me ([A-Za-z\s\-'\.]+)",
    r"name[:\s]+([A-Za-z\s\-'\.]+)",
]

DOB_PATTERNS = [
    r"(\d{1,2}[\/\-]\d{1,2}[\/\-]\d{4})",
    r"(\d{4}[\/\-]\d{1,2}[\/\-]\d{1,2})",
    r"DOB[:\s]*(\d{1,2}[\/\-]\d{1,2}[\/\-]\d{4})",
    r"date of birth[:\s]*(\d{1,2}[\/\-]\d{1,2}[\/\-]\d{4})",
    r"born[:\s]*(\d{1,2}[\/\-]\d{1,2}[\/\-]\d{4})",
]

DOCTOR_PATTERNS = [
    r"dr\.?\s+([A-Za-z]+)",
    r"doctor\s+([A-Za-z]+)",
    r"see\s+dr\.?\s+([A-Za-z]+)",
    r"with\s+dr\.?\s+([A-Za-z]+)",
    r"appointment\s+with\s+dr\.?\s+([A-Za-z]+)",
]

PHONE_PATTERNS = [
    r"(\+?1?[-.\s]?\(?[2-9]\d{2}\)?[-.\s]?\d{3}[-.\s]?\d{4})",
    r"phone[:\s]*(\+?1?[-.\s]?\(?[2-9]\d{2}\)?[-.\s]?\d{3}[-.\s]?\d{4})",
    r"number[:\s]*(\+?1?[-.\s]?\(?[2-9]\d{2}\)?[-.\s]?\d{3}[-.\s]?\d{4})",
]

EMAIL_PATTERNS = [
    r"([a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,})",
    r"email[:\s]*([a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,})",
]

# Available doctors at MediCare Allergy & Wellness Center
AVAILABLE_DOCTORS = {
    "johnson": "Dr. Johnson (Family Medicine)",
    "smith": "Dr. Smith (Cardiology)", 
    "williams": "Dr. Williams (Dermatology)",
    "brown": "Dr. Brown (Orthopedics)",
    "davis": "Dr. Davis (Internal Medicine)"
}

# ============================================================================
# MAIN GREETING HANDLER
# ============================================================================

def handle_patient_greeting(state: Dict[str, Any], llm) -> Dict[str, Any]:
    """
    Main handler for patient greeting and initial information collection.
    
    Args:
        state: Current appointment state containing conversation history
        llm: Gemini LLM instance for natural language processing
        
    Returns:
        Updated state with greeting response and any extracted patient info
    """
    logger.info("Processing patient greeting with Gemini")
    
    try:
        # Get the latest user message
        user_messages = [msg for msg in state.get("messages", []) if isinstance(msg, HumanMessage)]
        if not user_messages:
            return _handle_initial_greeting(state, llm)
        
        latest_user_input = user_messages[-1].content
        current_patient_info = state.get("patient_info", {})
        
        # Extract information from user input
        extracted_info = extract_patient_information(latest_user_input)
        
        # Merge extracted information with existing patient info
        updated_patient_info = {**current_patient_info, **extracted_info}
        
        # Determine what information is still missing
        missing_info = get_missing_required_info(updated_patient_info)
        
        # Generate appropriate response based on current state
        if not missing_info:
            # All required info collected, ready to proceed
            response = _generate_info_complete_response(updated_patient_info, llm)
        else:
            # Still need more information
            response = _generate_info_request_response(updated_patient_info, missing_info, llm)
        
        # Update state
        updated_state = {
            **state,
            "patient_info": updated_patient_info,
            "current_step": "greeting" if missing_info else "info_complete"
        }
        
        # Add response to conversation
        if response:
            updated_state["messages"] = state["messages"] + [AIMessage(content=response)]
        
        return updated_state
        
    except Exception as e:
        logger.error(f"Error in patient greeting handler: {str(e)}")
        return _handle_greeting_error(state, str(e))

def _handle_initial_greeting(state: Dict[str, Any], llm) -> Dict[str, Any]:
    """Handle the very first interaction when no user message exists yet."""
    
    initial_greeting = """Hello! Welcome to MediCare Allergy & Wellness Center. 
    
I'm here to help you schedule your appointment today. To get started, I'll need to collect some basic information.

Could you please tell me your full name?"""
    
    updated_state = {
        **state,
        "current_step": "greeting",
        "patient_info": {}
    }
    
    updated_state["messages"] = state.get("messages", []) + [AIMessage(content=initial_greeting)]
    
    return updated_state

# ============================================================================
# INFORMATION EXTRACTION FUNCTIONS
# ============================================================================

def extract_patient_information(text: str) -> Dict[str, Any]:
    """
    Extract patient information from natural language text using regex patterns.
    
    Args:
        text: User input text
        
    Returns:
        Dictionary containing extracted patient information
    """
    extracted_info = {}
    text_lower = text.lower().strip()
    
    # Extract name
    name = extract_patient_name(text)
    if name:
        extracted_info["name"] = name
    
    # Extract date of birth
    dob = extract_date_of_birth(text)
    if dob:
        extracted_info["dob"] = dob
    
    # Extract doctor preference
    doctor = extract_doctor_preference(text)
    if doctor:
        extracted_info["doctor_preference"] = doctor
    
    # Extract phone number
    phone = extract_phone_number(text)
    if phone:
        extracted_info["phone"] = phone
    
    # Extract email
    email = extract_email_address(text)
    if email:
        extracted_info["email"] = email
    
    # Extract location preference
    location = extract_location_preference(text)
    if location:
        extracted_info["location_preference"] = location
    
    return extracted_info

def extract_patient_name(text: str) -> Optional[str]:
    """Extract patient name from text using multiple patterns."""
    
    for pattern in NAME_PATTERNS:
        match = re.search(pattern, text, re.IGNORECASE)
        if match:
            name = match.group(1).strip()
            # Clean up the name
            name = re.sub(r'\s+', ' ', name)  # Replace multiple spaces with single space
            name = name.title()  # Convert to title case
            
            # Validate name (should only contain letters, spaces, hyphens, apostrophes, dots)
            if re.match(r"^[A-Za-z\s\-'\.]+$", name) and len(name.split()) >= 2:
                return name
    
    return None

def extract_date_of_birth(text: str) -> Optional[str]:
    """Extract and validate date of birth from text."""
    
    for pattern in DOB_PATTERNS:
        match = re.search(pattern, text)
        if match:
            date_str = match.group(1)
            validated_date = validate_date_of_birth(date_str)
            if validated_date:
                return validated_date
    
    return None

def extract_doctor_preference(text: str) -> Optional[str]:
    """Extract doctor preference from text."""
    
    for pattern in DOCTOR_PATTERNS:
        match = re.search(pattern, text, re.IGNORECASE)
        if match:
            doctor_last_name = match.group(1).lower()
            
            # Check if it matches any available doctor
            if doctor_last_name in AVAILABLE_DOCTORS:
                return AVAILABLE_DOCTORS[doctor_last_name]
    
    # Check for specialty mentions
    specialties = {
        "family": "Dr. Johnson (Family Medicine)",
        "cardiology": "Dr. Smith (Cardiology)",
        "heart": "Dr. Smith (Cardiology)",
        "dermatology": "Dr. Williams (Dermatology)",
        "skin": "Dr. Williams (Dermatology)",
        "orthopedic": "Dr. Brown (Orthopedics)",
        "bone": "Dr. Brown (Orthopedics)",
        "internal": "Dr. Davis (Internal Medicine)"
    }
    
    text_lower = text.lower()
    for keyword, doctor in specialties.items():
        if keyword in text_lower:
            return doctor
    
    return None

def extract_phone_number(text: str) -> Optional[str]:
    """Extract and format phone number from text."""
    
    for pattern in PHONE_PATTERNS:
        match = re.search(pattern, text)
        if match:
            phone = match.group(1)
            # Clean and format phone number
            cleaned_phone = re.sub(r'[^\d]', '', phone)
            
            # Validate US phone number (10 or 11 digits)
            if len(cleaned_phone) == 10:
                return f"({cleaned_phone[:3]}) {cleaned_phone[3:6]}-{cleaned_phone[6:]}"
            elif len(cleaned_phone) == 11 and cleaned_phone.startswith('1'):
                return f"+1 ({cleaned_phone[1:4]}) {cleaned_phone[4:7]}-{cleaned_phone[7:]}"
    
    return None

def extract_email_address(text: str) -> Optional[str]:
    """Extract and validate email address from text."""
    
    for pattern in EMAIL_PATTERNS:
        match = re.search(pattern, text, re.IGNORECASE)
        if match:
            email = match.group(1).lower()
            # Basic email validation
            if '@' in email and '.' in email.split('@')[1]:
                return email
    
    return None

def extract_location_preference(text: str) -> Optional[str]:
    """Extract location preference from text."""
    
    locations = ["downtown", "north", "south", "east", "west", "main", "branch"]
    text_lower = text.lower()
    
    for location in locations:
        if location in text_lower:
            return location.title()
    
    return None

# ============================================================================
# VALIDATION FUNCTIONS
# ============================================================================

def validate_date_of_birth(date_str: str) -> Optional[str]:
    """
    Validate and standardize date of birth format.
    
    Args:
        date_str: Date string in various formats
        
    Returns:
        Standardized date string (MM/DD/YYYY) or None if invalid
    """
    try:
        # Try different date formats
        formats = ['%m/%d/%Y', '%m-%d-%Y', '%Y/%m/%d', '%Y-%m-%d']
        
        for fmt in formats:
            try:
                date_obj = datetime.strptime(date_str, fmt)
                
                # Validate age (should be between 0 and 120 years)
                today = datetime.now()
                age = today.year - date_obj.year
                
                if date_obj.replace(year=today.year) > today:
                    age -= 1
                
                if 0 <= age <= 120:
                    return date_obj.strftime('%m/%d/%Y')
                
            except ValueError:
                continue
                
    except Exception as e:
        logger.error(f"Error validating date of birth: {str(e)}")
    
    return None

def get_missing_required_info(patient_info: Dict[str, Any]) -> List[str]:
    """
    Determine what required information is still missing.
    
    Args:
        patient_info: Current patient information dictionary
        
    Returns:
        List of missing required field names
    """
    required_fields = {
        "name": "your full name",
        "dob": "your date of birth",
        "phone": "your phone number"
    }
    
    missing = []
    for field, description in required_fields.items():
        if not patient_info.get(field):
            missing.append(field)
    
    return missing

def validate_patient_info_completeness(patient_info: Dict[str, Any]) -> Tuple[bool, List[str]]:
    """
    Validate if patient information is complete and properly formatted.
    
    Returns:
        Tuple of (is_complete, list_of_issues)
    """
    issues = []
    
    # Check name
    name = patient_info.get("name", "")
    if not name:
        issues.append("Name is required")
    elif len(name.split()) < 2:
        issues.append("Please provide your full name (first and last)")
    
    # Check date of birth
    dob = patient_info.get("dob", "")
    if not dob:
        issues.append("Date of birth is required")
    elif not validate_date_of_birth(dob):
        issues.append("Please provide a valid date of birth (MM/DD/YYYY)")
    
    # Check phone number
    phone = patient_info.get("phone", "")
    if not phone:
        issues.append("Phone number is required")
    
    return len(issues) == 0, issues

# ============================================================================
# RESPONSE GENERATION FUNCTIONS
# ============================================================================

def _generate_info_complete_response(patient_info: Dict[str, Any], llm) -> str:
    """Generate response when all required information is collected."""
    
    name = patient_info.get("name", "")
    doctor = patient_info.get("doctor_preference", "")
    
    prompt = f"""
    Create a professional, warm response for a patient named {name} who has provided all their basic information for appointment scheduling.
    
    The response should:
    1. Thank them for providing their information
    2. Confirm their details briefly
    3. Mention that you'll now search for them in our system
    4. If they mentioned a doctor preference ({doctor}), acknowledge it
    5. Keep it concise and professional (under 60 words)
    
    Make it sound natural and personalized.
    """
    
    try:
        response = llm.invoke([HumanMessage(content=prompt)])
        return response.content
    except Exception as e:
        logger.error(f"Error generating complete info response: {str(e)}")
        return f"Thank you, {name}! I have all the information I need. Let me search for your records in our system and find available appointment times."

def _generate_info_request_response(patient_info: Dict[str, Any], missing_info: List[str], llm) -> str:
    """Generate response to request missing information."""
    
    name = patient_info.get("name", "")
    
    # Determine what to ask for next
    if "name" in missing_info:
        return "Hello! I'd be happy to help you schedule an appointment. Could you please tell me your full name?"
    
    elif "dob" in missing_info:
        greeting = f"Thank you, {name}!" if name else "Thank you!"
        return f"{greeting} I'll need your date of birth to look up your records. Please provide it in MM/DD/YYYY format."
    
    elif "phone" in missing_info:
        return "Great! I'll also need a phone number where we can reach you for appointment confirmations and reminders."
    
    else:
        # Use Gemini to generate a natural request for remaining info
        prompt = f"""
        A patient {name if name else "someone"} is scheduling an appointment. They still need to provide: {', '.join(missing_info)}.
        
        Create a friendly, professional request for this information. 
        Keep it under 40 words and make it sound natural.
        """
        
        try:
            response = llm.invoke([HumanMessage(content=prompt)])
            return response.content
        except Exception as e:
            logger.error(f"Error generating info request: {str(e)}")
            return "I'll need a bit more information to proceed. Could you please provide the missing details?"

def _handle_greeting_error(state: Dict[str, Any], error_msg: str) -> Dict[str, Any]:
    """Handle errors in the greeting process."""
    
    logger.error(f"Greeting error: {error_msg}")
    
    error_response = """I apologize, but I'm experiencing a technical issue. 
    Let me try to help you schedule your appointment. Could you please tell me your name?"""
    
    updated_state = {
        **state,
        "error_message": error_msg,
        "current_step": "greeting_error"
    }
    
    updated_state["messages"] = state.get("messages", []) + [AIMessage(content=error_response)]
    
    return updated_state

# ============================================================================
# UTILITY FUNCTIONS
# ============================================================================

def format_patient_info_summary(patient_info: Dict[str, Any]) -> str:
    """Format patient information for display or confirmation."""
    
    summary_parts = []
    
    if patient_info.get("name"):
        summary_parts.append(f"Name: {patient_info['name']}")
    
    if patient_info.get("dob"):
        summary_parts.append(f"Date of Birth: {patient_info['dob']}")
    
    if patient_info.get("phone"):
        summary_parts.append(f"Phone: {patient_info['phone']}")
    
    if patient_info.get("email"):
        summary_parts.append(f"Email: {patient_info['email']}")
    
    if patient_info.get("doctor_preference"):
        summary_parts.append(f"Preferred Doctor: {patient_info['doctor_preference']}")
    
    if patient_info.get("location_preference"):
        summary_parts.append(f"Preferred Location: {patient_info['location_preference']}")
    
    return "\n".join(summary_parts)

def clean_text_input(text: str) -> str:
    """Clean and sanitize text input for security and consistency."""
    
    if not text:
        return ""
    
    # Remove extra whitespace
    cleaned = re.sub(r'\s+', ' ', text.strip())
    
    # Remove potentially harmful characters (basic sanitization)
    cleaned = re.sub(r'[<>{}]', '', cleaned)
    
    return cleaned

# ============================================================================
# TESTING AND VALIDATION FUNCTIONS
# ============================================================================

def test_information_extraction():
    """Test function to validate information extraction patterns."""
    
    test_cases = [
        "Hi, my name is John Smith, DOB 01/15/1985",
        "I'm Jane Doe, born 03/22/1990, and I'd like to see Dr. Johnson",
        "This is Michael Brown, date of birth 12/05/1978, phone 555-123-4567",
        "Hello, I am Sarah Wilson, 02-18-1995, email sarah@email.com",
        "My name is David Lee and I need an appointment with Dr. Smith for cardiology"
    ]
    
    print("Testing Information Extraction:")
    print("=" * 50)
    
    for i, test_text in enumerate(test_cases, 1):
        print(f"\nTest Case {i}: {test_text}")
        extracted = extract_patient_information(test_text)
        print(f"Extracted: {extracted}")
        
        missing = get_missing_required_info(extracted)
        print(f"Missing: {missing}")

if __name__ == "__main__":
    # Run tests if script is executed directly
    test_information_extraction()
