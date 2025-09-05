"""
Patient Information Collector Agent - Medical Appointment Scheduling System
========================================================================

This module handles intelligent extraction of patient information from
natural language conversation messages using advanced pattern matching
and natural language processing techniques.

Key Responsibilities:
- Extract patient name, date of birth, phone number, email address
- Parse doctor preferences and specialties from conversational text
- Handle location preferences and appointment type requests
- Validate and standardize extracted information
- Integrate with LangGraph workflow state management
- Provide fallback extraction methods and error handling

Author: RagaAI Case Study Implementation
Date: September 2025
"""
import json

import re
import logging
from typing import Dict, Any, List, Optional, Tuple
from datetime import datetime
from langchain_core.messages import HumanMessage, AIMessage, BaseMessage

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# ============================================================================
# EXTRACTION PATTERNS AND CONSTANTS
# ============================================================================

# Regex patterns for information extraction
PATTERNS = {
    'name': [
        r"my name is ([A-Za-z\s\-'\.]+)",
        r"i'm ([A-Za-z\s\-'\.]+)",
        r"i am ([A-Za-z\s\-'\.]+)", 
        r"this is ([A-Za-z\s\-'\.]+)",
        r"call me ([A-Za-z\s\-'\.]+)",
        r"name[:\s]+([A-Za-z\s\-'\.]+)",
        r"([A-Z][a-z]+\s+[A-Z][a-z]+)",  # Two capitalized words
    ],
    'dob': [
        r"(\d{1,2}[\/\-]\d{1,2}[\/\-]\d{4})",
        r"(\d{4}[\/\-]\d{1,2}[\/\-]\d{1,2})",
        r"DOB[:\s]*(\d{1,2}[\/\-]\d{1,2}[\/\-]\d{4})",
        r"date of birth[:\s]*(\d{1,2}[\/\-]\d{1,2}[\/\-]\d{4})",
        r"born[:\s]*(\d{1,2}[\/\-]\d{1,2}[\/\-]\d{4})",
        r"birthday[:\s]*(\d{1,2}[\/\-]\d{1,2}[\/\-]\d{4})",
    ],
    'phone': [
        r"(\+?1?[-.\s]?\(?[2-9]\d{2}\)?[-.\s]?\d{3}[-.\s]?\d{4})",
        r"phone[:\s]*(\+?1?[-.\s]?\(?[2-9]\d{2}\)?[-.\s]?\d{3}[-.\s]?\d{4})",
        r"number[:\s]*(\+?1?[-.\s]?\(?[2-9]\d{2}\)?[-.\s]?\d{3}[-.\s]?\d{4})",
        r"call me at[:\s]*(\+?1?[-.\s]?\(?[2-9]\d{2}\)?[-.\s]?\d{3}[-.\s]?\d{4})",
    ],
    'email': [
        r"([a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,})",
        r"email[:\s]*([a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,})",
        r"e-mail[:\s]*([a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,})",
    ]
}

# Available doctors and specialties
AVAILABLE_DOCTORS = {
    "johnson": "Dr. Johnson (Family Medicine)",
    "smith": "Dr. Smith (Cardiology)",
    "williams": "Dr. Williams (Dermatology)", 
    "brown": "Dr. Brown (Orthopedics)",
    "davis": "Dr. Davis (Internal Medicine)"
}

SPECIALTIES_MAP = {
    "family medicine": "Dr. Johnson (Family Medicine)",
    "family": "Dr. Johnson (Family Medicine)",
    "cardiology": "Dr. Smith (Cardiology)",
    "heart": "Dr. Smith (Cardiology)",
    "cardiac": "Dr. Smith (Cardiology)",
    "dermatology": "Dr. Williams (Dermatology)",
    "skin": "Dr. Williams (Dermatology)",
    "dermatologist": "Dr. Williams (Dermatology)",
    "orthopedics": "Dr. Brown (Orthopedics)",
    "orthopedic": "Dr. Brown (Orthopedics)",
    "bones": "Dr. Brown (Orthopedics)",
    "joint": "Dr. Brown (Orthopedics)",
    "internal medicine": "Dr. Davis (Internal Medicine)",
    "internal": "Dr. Davis (Internal Medicine)",
    "general": "Dr. Johnson (Family Medicine)"
}

# ============================================================================
# CORE EXTRACTION CLASS
# ============================================================================

class PatientInfoExtractor:
    """
    Advanced patient information extractor using pattern matching and NLP techniques.
    """
    
    def __init__(self):
        """Initialize the extractor with patterns and validation rules."""
        self.patterns = PATTERNS
        self.doctors = AVAILABLE_DOCTORS
        self.specialties = SPECIALTIES_MAP
    
    def extract_from_text(self, text: str) -> Dict[str, Any]:
        """
        Extract all available patient information from a text string.
        
        Args:
            text: Input text to analyze
            
        Returns:
            Dictionary containing extracted patient information
        """
        extracted_info = {}
        
        try:
            # Extract basic information
            extracted_info.update(self._extract_name(text))
            extracted_info.update(self._extract_dob(text))
            extracted_info.update(self._extract_phone(text))
            extracted_info.update(self._extract_email(text))
            extracted_info.update(self._extract_doctor_preference(text))
            extracted_info.update(self._extract_location_preference(text))
            extracted_info.update(self._extract_urgency_level(text))
            
            return extracted_info
            
        except Exception as e:
            logger.error(f"Error extracting info from text: {str(e)}")
            return {}
    
    def _extract_name(self, text: str) -> Dict[str, str]:
        """Extract patient name using multiple patterns."""
        for pattern in self.patterns['name']:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                name = match.group(1).strip()
                # Clean up the name
                name = re.sub(r'\s+', ' ', name)
                name = name.title()
                
                # Validate name (should have at least 2 parts)
                name_parts = name.split()
                if len(name_parts) >= 2 and all(part.isalpha() or part in ["'", "-", "."] for part in name_parts):
                    return {"name": name}
        
        return {}
    
    def _extract_dob(self, text: str) -> Dict[str, str]:
        """Extract and validate date of birth."""
        for pattern in self.patterns['dob']:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                date_str = match.group(1)
                validated_date = self._validate_date(date_str)
                if validated_date:
                    return {"dob": validated_date}
        
        return {}
    
    def _extract_phone(self, text: str) -> Dict[str, str]:
        """Extract and format phone number."""
        for pattern in self.patterns['phone']:
            match = re.search(pattern, text)
            if match:
                phone = match.group(1)
                formatted_phone = self._format_phone(phone)
                if formatted_phone:
                    return {"phone": formatted_phone}
        
        return {}
    
    def _extract_email(self, text: str) -> Dict[str, str]:
        """Extract and validate email address."""
        for pattern in self.patterns['email']:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                email = match.group(1).lower()
                if self._validate_email(email):
                    return {"email": email}
        
        return {}
    
    def _extract_doctor_preference(self, text: str) -> Dict[str, str]:
        """Extract doctor preference by name or specialty."""
        text_lower = text.lower()
        
        # Check for specific doctor names
        for doctor_key, doctor_name in self.doctors.items():
            if f"dr. {doctor_key}" in text_lower or f"dr {doctor_key}" in text_lower or f"doctor {doctor_key}" in text_lower:
                return {"doctor_preference": doctor_name}
        
        # Check for specialties
        for specialty_key, doctor_name in self.specialties.items():
            if specialty_key in text_lower:
                return {"doctor_preference": doctor_name}
        
        return {}
    
    def _extract_location_preference(self, text: str) -> Dict[str, str]:
        """Extract location or branch preference."""
        text_lower = text.lower()
        locations = ["main", "downtown", "north", "south", "east", "west", "branch"]
        
        for location in locations:
            if location in text_lower:
                return {"location_preference": location.title()}
        
        return {}
    
    def _extract_urgency_level(self, text: str) -> Dict[str, str]:
        """Extract urgency or priority level from text."""
        text_lower = text.lower()
        
        urgent_keywords = ["urgent", "asap", "emergency", "right away", "immediately"]
        routine_keywords = ["routine", "regular", "normal", "not urgent"]
        
        if any(keyword in text_lower for keyword in urgent_keywords):
            return {"urgency_level": "urgent"}
        elif any(keyword in text_lower for keyword in routine_keywords):
            return {"urgency_level": "routine"}
        
        return {}
    
    def _validate_date(self, date_str: str) -> Optional[str]:
        """Validate and standardize date format."""
        try:
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
            logger.error(f"Error validating date {date_str}: {str(e)}")
        
        return None
    
    def _format_phone(self, phone: str) -> Optional[str]:
        """Format phone number to standard format."""
        try:
            # Remove all non-digit characters
            digits = re.sub(r'[^\d]', '', phone)
            
            # Validate US phone number
            if len(digits) == 10:
                return f"({digits[:3]}) {digits[3:6]}-{digits[6:]}"
            elif len(digits) == 11 and digits.startswith('1'):
                return f"+1 ({digits[1:4]}) {digits[4:7]}-{digits[7:]}"
        
        except Exception as e:
            logger.error(f"Error formatting phone {phone}: {str(e)}")
        
        return None
    
    def _validate_email(self, email: str) -> bool:
        """Validate email format."""
        try:
            email_pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
            return bool(re.match(email_pattern, email))
        except Exception:
            return False

# ============================================================================
# MAIN COLLECTION FUNCTIONS FOR LANGGRAPH INTEGRATION
# ============================================================================

def collect_patient_information_with_gemini(state: Dict[str, Any], llm) -> Dict[str, Any]:
    """
    Main function for collecting patient information using a structured JSON output
    from the Gemini AI to ensure accuracy and prevent parsing errors.
    """
    logger.info("Collecting patient information with structured Gemini assistance")
    
    try:
        # 1. Get current state and focus only on the latest user message
        messages = state.get("messages", [])
        current_patient_info = state.get("patient_info", {})
        user_messages = [msg for msg in messages if isinstance(msg, HumanMessage)]
        
        if not user_messages:
            return state
            
        latest_user_input = user_messages[-1].content
        
        # 2. Define the required fields and create a structured prompt for Gemini
        required_fields = ["name", "dob", "phone"]
        
        prompt = f"""
        You are an expert at extracting patient information from a conversation for a medical appointment system.
        Your task is to analyze the user's latest message and extract the required information.
        The required fields are: {required_fields}.

        Here is the information we have already collected: {current_patient_info}
        Here is the user's latest message: "{latest_user_input}"

        Analyze the message and return a JSON object with two keys:
        1. "extracted_info": A dictionary containing any NEW information you found for the fields: "name", "dob", "phone".
        2. "missing_info": A list of the required fields that are STILL missing after analyzing this new message.

        Example:
        If we already have the name and the user provides their DOB, the output should be:
        {{
            "extracted_info": {{"dob": "01/15/1990"}},
            "missing_info": ["phone"]
        }}

        IMPORTANT: Only extract the specific information. Do not include extra words from the user's message. Ensure dob is in MM/DD/YYYY format.

        JSON Response:
        """

        # 3. Call Gemini and robustly parse the JSON response
        response_str = llm.invoke(prompt).content
        
        json_match = re.search(r'```json\s*([\s\S]*?)\s*```', response_str)
        if json_match:
            response_str = json_match.group(1)
        
        try:
            parsed_response = json.loads(response_str)
            extracted_info = parsed_response.get("extracted_info", {})
            missing_info = parsed_response.get("missing_info", [])
        except json.JSONDecodeError:
            logger.error(f"Failed to parse JSON response from Gemini: {response_str}")
            missing_info = _get_missing_required_info(current_patient_info)
            extracted_info = {}

        # 4. Update patient info and generate the next response
        updated_patient_info = {**current_patient_info, **extracted_info}

        if 'dob' in updated_patient_info and updated_patient_info['dob']:
            try:
                dob_obj = datetime.strptime(str(updated_patient_info['dob']), '%m/%d/%Y')
                updated_patient_info['dob'] = dob_obj.strftime('%m/%d/%Y')
            except (ValueError, TypeError):
                logger.warning(f"LLM returned an invalid date format for DOB: {updated_patient_info['dob']}")
                if 'dob' in updated_patient_info: del updated_patient_info['dob']
                missing_info = _get_missing_required_info(updated_patient_info)

        if missing_info:
            response_content = _generate_info_request_with_gemini(updated_patient_info, missing_info, llm)
        else:
            response_content = _generate_info_confirmation_with_gemini(updated_patient_info, llm)
            
        # 5. Update and return the state
        updated_state = {
            **state,
            "patient_info": updated_patient_info,
            "missing_patient_info": missing_info,
            "current_step": "patient_info_collection"
        }
        
        if response_content:
            updated_state["messages"] = state["messages"] + [AIMessage(content=response_content)]
        
        logger.info(f"Patient information updated: {updated_patient_info}")
        return updated_state
        
    except Exception as e:
        logger.error(f"Error in patient information collection: {str(e)}")
        return {
            **state,
            "error_message": f"Patient info collection error: {str(e)}",
            "current_step": "error"
        }

def collect_patient_information(state: Dict[str, Any]) -> Dict[str, Any]:
    """
    Basic patient information collection without Gemini dependency.
    
    Args:
        state: Current appointment state
        
    Returns:
        Updated state with collected information
    """
    logger.info("Collecting patient information")
    
    try:
        extractor = PatientInfoExtractor()
        messages = state.get("messages", [])
        current_info = state.get("patient_info", {})
        
        # Extract from messages
        extracted_info = {}
        for message in messages:
            if isinstance(message, (HumanMessage, BaseMessage)) and hasattr(message, 'content'):
                msg_info = extractor.extract_from_text(message.content)
                extracted_info.update(msg_info)
        
        # Update patient info
        updated_info = {**current_info, **extracted_info}
        missing_info = _get_missing_required_info(updated_info)
        
        return {
            **state,
            "patient_info": updated_info,
            "missing_patient_info": missing_info,
            "current_step": "patient_info_collection"
        }
        
    except Exception as e:
        logger.error(f"Error in basic patient info collection: {str(e)}")
        return {
            **state,
            "error_message": f"Patient info error: {str(e)}",
            "current_step": "error"
        }

# ============================================================================
# HELPER FUNCTIONS
# ============================================================================

def _get_missing_required_info(patient_info: Dict[str, Any]) -> List[str]:
    """Determine what required information is still missing."""
    required_fields = ["name", "dob", "phone"]
    missing = []
    
    for field in required_fields:
        if not patient_info.get(field):
            missing.append(field)
    
    return missing

def _generate_info_request_with_gemini(patient_info: Dict[str, Any], missing_info: List[str], llm) -> str:
    """Generate a natural request for missing information using Gemini."""
    try:
        name = patient_info.get("name", "")
        
        # Create context for what's missing
        missing_descriptions = {
            "name": "your full name",
            "dob": "your date of birth (MM/DD/YYYY format)",
            "phone": "your phone number"
        }
        
        missing_items = [missing_descriptions.get(item, item) for item in missing_info]
        
        prompt = f"""
        A patient is scheduling an appointment. I have some of their information but need more.
        
        Current information: {', '.join([f"{k}: {v}" for k, v in patient_info.items() if v])}
        Missing information: {', '.join(missing_items)}
        
        Create a friendly, professional request for the missing information. 
        Be conversational and make it clear why we need this information.
        Keep it under 50 words and sound natural.
        """
        
        response = llm.invoke([HumanMessage(content=prompt)])
        return response.content
        
    except Exception as e:
        logger.error(f"Error generating info request with Gemini: {str(e)}")
        
        # Fallback response
        if "name" in missing_info:
            return "I'd be happy to help you schedule an appointment! Could you please tell me your full name?"
        elif "dob" in missing_info:
            return f"Thank you, {name}! I'll also need your date of birth to look up your records. Please provide it in MM/DD/YYYY format."
        else:
            return "I need a few more details to complete your appointment booking. Could you provide the missing information?"

def _generate_info_confirmation_with_gemini(patient_info: Dict[str, Any], llm) -> str:
    """Generate confirmation message when all info is collected."""
    try:
        name = patient_info.get("name", "Patient")
        
        prompt = f"""
        Create a brief, professional confirmation message for a patient named {name} 
        who has provided all their required information for appointment scheduling.
        
        Confirm that we have their details and mention that we'll now search 
        for their records in our system.
        
        Keep it warm, professional, and under 40 words.
        """
        
        response = llm.invoke([HumanMessage(content=prompt)])
        return response.content
        
    except Exception as e:
        logger.error(f"Error generating confirmation with Gemini: {str(e)}")
        return f"Thank you, {name}! I have all the information I need. Let me search for your records in our system."

def format_patient_info_display(patient_info: Dict[str, Any]) -> str:
    """Format patient information for display or confirmation."""
    if not patient_info:
        return "No patient information collected yet."
    
    display_parts = []
    
    if patient_info.get("name"):
        display_parts.append(f"Name: {patient_info['name']}")
    
    if patient_info.get("dob"):
        display_parts.append(f"Date of Birth: {patient_info['dob']}")
    
    if patient_info.get("phone"):
        display_parts.append(f"Phone: {patient_info['phone']}")
    
    if patient_info.get("email"):
        display_parts.append(f"Email: {patient_info['email']}")
    
    if patient_info.get("doctor_preference"):
        display_parts.append(f"Doctor Preference: {patient_info['doctor_preference']}")
    
    if patient_info.get("location_preference"):
        display_parts.append(f"Location: {patient_info['location_preference']}")
    
    if patient_info.get("urgency_level"):
        display_parts.append(f"Urgency: {patient_info['urgency_level']}")
    
    return "\n".join(display_parts)

def validate_patient_info_completeness(patient_info: Dict[str, Any]) -> Tuple[bool, List[str]]:
    """Validate patient information for completeness and accuracy."""
    issues = []
    
    # Check required fields
    if not patient_info.get("name"):
        issues.append("Patient name is required")
    elif len(patient_info["name"].split()) < 2:
        issues.append("Please provide full name (first and last)")
    
    if not patient_info.get("dob"):
        issues.append("Date of birth is required")
    
    if not patient_info.get("phone"):
        issues.append("Phone number is required")
    
    # Validate email format if provided
    if patient_info.get("email"):
        email_pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
        if not re.match(email_pattern, patient_info["email"]):
            issues.append("Please provide a valid email address")
    
    return len(issues) == 0, issues

# ============================================================================
# TESTING FUNCTION
# ============================================================================

def test_patient_info_extraction():
    """Test function to validate information extraction capabilities."""
    
    print("Testing Patient Information Extraction")
    print("=" * 50)
    
    test_cases = [
        "Hi, my name is John Smith, DOB 01/15/1985, phone (555) 123-4567",
        "I'm Sarah Johnson, born 03/22/1990, and I'd like to see Dr. Williams for dermatology",
        "This is Michael Brown, date of birth 12/05/1978, email michael@email.com",
        "Hello, I need an urgent appointment with Dr. Smith for cardiology issues",
        "My name is Lisa Davis and I prefer the downtown location"
    ]
    
    extractor = PatientInfoExtractor()
    
    for i, test_text in enumerate(test_cases, 1):
        print(f"\nTest Case {i}: {test_text}")
        extracted = extractor.extract_from_text(test_text)
        print(f"Extracted: {extracted}")
        
        # Test missing info detection
        missing = _get_missing_required_info(extracted)
        if missing:
            print(f"Missing: {missing}")
        else:
            print("All required information collected!")

if __name__ == "__main__":
    # Run tests when executed directly
    test_patient_info_extraction()
