"""
Insurance Collection Agent - Medical Appointment Scheduling System
===============================================================

This module handles intelligent extraction and collection of patient insurance
information during the appointment scheduling process using advanced pattern
matching and Gemini AI integration.

Key Responsibilities:
- Extract insurance carrier, member ID, and group number from conversation
- Validate insurance information and request missing details
- Integration with Gemini API for natural language processing
- Handle various insurance data formats and edge cases
- Provide fallback extraction methods and comprehensive error handling

Author: RagaAI Case Study Implementation
Date: September 2025
"""

import re
import logging
from typing import Dict, Any, List, Optional, Tuple
from datetime import datetime
from langchain_core.messages import HumanMessage, AIMessage, BaseMessage

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# ============================================================================
# INSURANCE DATA EXTRACTION PATTERNS
# ============================================================================

# Comprehensive regex patterns for insurance information extraction
INSURANCE_PATTERNS = {
    'carrier': [
        r"insurance carrier[:\s]+([A-Za-z\s&\.]+)",
        r"insurance company[:\s]+([A-Za-z\s&\.]+)",
        r"insurance provider[:\s]+([A-Za-z\s&\.]+)",
        r"my insurance is[:\s]+([A-Za-z\s&\.]+)",
        r"i have ([A-Za-z\s&\.]+) insurance",
        r"carrier[:\s]+([A-Za-z\s&\.]+)",
        r"provider[:\s]+([A-Za-z\s&\.]+)",
        r"insured with ([A-Za-z\s&\.]+)",
        r"covered by ([A-Za-z\s&\.]+)",
    ],
    'member_id': [
        r"member id[:\s]+([A-Za-z0-9\-]+)",
        r"member number[:\s]+([A-Za-z0-9\-]+)",
        r"policy number[:\s]+([A-Za-z0-9\-]+)",
        r"id number[:\s]+([A-Za-z0-9\-]+)",
        r"my member id is ([A-Za-z0-9\-]+)",
        r"policy id[:\s]+([A-Za-z0-9\-]+)",
        r"subscriber id[:\s]+([A-Za-z0-9\-]+)",
    ],
    'group_number': [
        r"group number[:\s]+([A-Za-z0-9\-]+)",
        r"group id[:\s]+([A-Za-z0-9\-]+)",
        r"employer group[:\s]+([A-Za-z0-9\-]+)",
        r"my group number is ([A-Za-z0-9\-]+)",
        r"group code[:\s]+([A-Za-z0-9\-]+)",
    ]
}

# Common insurance carriers for validation
COMMON_CARRIERS = [
    "BlueCross BlueShield", "Blue Cross Blue Shield", "BCBS",
    "UnitedHealthcare", "United Healthcare", "United Health",
    "Aetna", "Cigna", "Humana", "Kaiser Permanente", "Kaiser",
    "Anthem", "Molina Healthcare", "Molina", "Centene", "WellCare",
    "Medicare", "Medicaid", "Tricare", "GEHA", "Federal Employee Program"
]

# ============================================================================
# INSURANCE INFORMATION EXTRACTOR CLASS
# ============================================================================

class InsuranceInfoExtractor:
    """
    Advanced insurance information extractor using pattern matching and validation.
    """
    
    def __init__(self):
        """Initialize the extractor with patterns and carrier database."""
        self.patterns = INSURANCE_PATTERNS
        self.carriers = COMMON_CARRIERS
    
    def extract_from_text(self, text: str) -> Dict[str, str]:
        """
        Extract insurance information from a single text string.
        
        Args:
            text: Input text to analyze
            
        Returns:
            Dictionary containing extracted insurance information
        """
        extracted_info = {}
        
        try:
            # Extract carrier
            carrier = self._extract_carrier(text)
            if carrier:
                extracted_info["carrier"] = carrier
            
            # Extract member ID
            member_id = self._extract_member_id(text)
            if member_id:
                extracted_info["member_id"] = member_id
            
            # Extract group number
            group_number = self._extract_group_number(text)
            if group_number:
                extracted_info["group_number"] = group_number
            
            return extracted_info
            
        except Exception as e:
            logger.error(f"Error extracting insurance info from text: {str(e)}")
            return {}
    
    def _extract_carrier(self, text: str) -> Optional[str]:
        """Extract and validate insurance carrier."""
        for pattern in self.patterns['carrier']:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                carrier = match.group(1).strip()
                # Clean up the carrier name
                carrier = self._clean_carrier_name(carrier)
                # Validate against known carriers
                validated_carrier = self._validate_carrier(carrier)
                if validated_carrier:
                    return validated_carrier
        
        return None
    
    def _extract_member_id(self, text: str) -> Optional[str]:
        """Extract and format member ID."""
        for pattern in self.patterns['member_id']:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                member_id = match.group(1).strip().upper()
                # Basic validation - should be alphanumeric with possible hyphens
                if self._validate_member_id(member_id):
                    return member_id
        
        return None
    
    def _extract_group_number(self, text: str) -> Optional[str]:
        """Extract and format group number."""
        for pattern in self.patterns['group_number']:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                group_number = match.group(1).strip().upper()
                # Basic validation
                if self._validate_group_number(group_number):
                    return group_number
        
        return None
    
    def _clean_carrier_name(self, carrier: str) -> str:
        """Clean and standardize carrier name."""
        # Remove extra whitespace
        carrier = re.sub(r'\s+', ' ', carrier.strip())
        
        # Handle common abbreviations and variations
        carrier_map = {
            "blue cross blue shield": "BlueCross BlueShield",
            "bcbs": "BlueCross BlueShield", 
            "united healthcare": "UnitedHealthcare",
            "united health": "UnitedHealthcare",
            "kaiser permanente": "Kaiser Permanente",
            "kaiser": "Kaiser Permanente"
        }
        
        carrier_lower = carrier.lower()
        for key, value in carrier_map.items():
            if key in carrier_lower:
                return value
        
        # Title case for other carriers
        return carrier.title()
    
    def _validate_carrier(self, carrier: str) -> Optional[str]:
        """Validate carrier against known insurance companies."""
        carrier_lower = carrier.lower()
        
        # Check for exact or partial matches
        for known_carrier in self.carriers:
            if carrier_lower == known_carrier.lower():
                return known_carrier
            elif carrier_lower in known_carrier.lower() or known_carrier.lower() in carrier_lower:
                return known_carrier
        
        # If not in known list but looks valid, return as-is
        if len(carrier) > 2 and not carrier.isdigit():
            return carrier
        
        return None
    
    def _validate_member_id(self, member_id: str) -> bool:
        """Validate member ID format."""
        # Should be alphanumeric with possible hyphens, 5-15 characters
        if not member_id or len(member_id) < 5 or len(member_id) > 15:
            return False
        
        # Check for valid characters
        if not re.match(r'^[A-Za-z0-9\-]+$', member_id):
            return False
        
        return True
    
    def _validate_group_number(self, group_number: str) -> bool:
        """Validate group number format."""
        # Should be alphanumeric with possible hyphens, 3-12 characters
        if not group_number or len(group_number) < 3 or len(group_number) > 12:
            return False
        
        # Check for valid characters
        if not re.match(r'^[A-Za-z0-9\-]+$', group_number):
            return False
        
        return True

# ============================================================================
# MAIN COLLECTION FUNCTIONS FOR LANGGRAPH INTEGRATION
# ============================================================================

def collect_insurance_information_with_gemini(state: Dict[str, Any], llm) -> Dict[str, Any]:
    """
    Main function for collecting insurance information using Gemini AI assistance.
    
    Args:
        state: Current appointment state
        llm: Gemini LLM instance for intelligent processing
        
    Returns:
        Updated state with collected insurance information
    """
    logger.info("Collecting insurance information with Gemini assistance")
    
    try:
        # Initialize extractor
        extractor = InsuranceInfoExtractor()
        
        # Get conversation messages and current insurance data
        messages = state.get("messages", [])
        current_insurance_data = state.get("insurance_data", {})
        
        # Extract information from all messages
        extracted_info = {}
        for message in messages:
            if isinstance(message, (HumanMessage, BaseMessage)) and hasattr(message, 'content'):
                msg_info = extractor.extract_from_text(message.content)
                extracted_info.update(msg_info)
        
        # Merge with existing information
        updated_insurance_data = {**current_insurance_data, **extracted_info}
        
        # Check completeness
        missing_info = _get_missing_insurance_info(updated_insurance_data)
        
        # Generate appropriate response using Gemini
        if missing_info:
            response = _generate_insurance_request_with_gemini(updated_insurance_data, missing_info, llm)
        else:
            response = _generate_insurance_confirmation_with_gemini(updated_insurance_data, llm)
        
        # Update state
        updated_state = {
            **state,
            "insurance_data": updated_insurance_data,
            "missing_insurance_info": missing_info,
            "current_step": "insurance_collection"
        }
        
        if response:
            updated_state["messages"] = state["messages"] + [AIMessage(content=response)]
        
        logger.info(f"Insurance information updated: {len(updated_insurance_data)} fields")
        return updated_state
        
    except Exception as e:
        logger.error(f"Error in insurance information collection: {str(e)}")
        return {
            **state,
            "error_message": f"Insurance collection error: {str(e)}",
            "current_step": "error"
        }

def collect_insurance_information(state: Dict[str, Any]) -> Dict[str, Any]:
    """
    Basic insurance information collection without Gemini dependency.
    
    Args:
        state: Current appointment state
        
    Returns:
        Updated state with collected insurance information
    """
    logger.info("Collecting insurance information")
    
    try:
        extractor = InsuranceInfoExtractor()
        messages = state.get("messages", [])
        current_data = state.get("insurance_data", {})
        
        # Extract from messages
        extracted_info = {}
        for message in messages:
            if isinstance(message, (HumanMessage, BaseMessage)) and hasattr(message, 'content'):
                msg_info = extractor.extract_from_text(message.content)
                extracted_info.update(msg_info)
        
        # Update insurance data
        updated_data = {**current_data, **extracted_info}
        missing_info = _get_missing_insurance_info(updated_data)
        
        return {
            **state,
            "insurance_data": updated_data,
            "missing_insurance_info": missing_info,
            "current_step": "insurance_collection"
        }
        
    except Exception as e:
        logger.error(f"Error in basic insurance collection: {str(e)}")
        return {
            **state,
            "error_message": f"Insurance collection error: {str(e)}",
            "current_step": "error"
        }

# ============================================================================
# HELPER FUNCTIONS
# ============================================================================

def _get_missing_insurance_info(insurance_data: Dict[str, Any]) -> List[str]:
    """Determine what required insurance information is still missing."""
    required_fields = ["carrier", "member_id", "group_number"]
    missing = []
    
    for field in required_fields:
        if not insurance_data.get(field):
            missing.append(field)
    
    return missing

def _generate_insurance_request_with_gemini(insurance_data: Dict[str, Any], missing_info: List[str], llm) -> str:
    """Generate a natural request for missing insurance information using Gemini."""
    try:
        # Create context for what's missing
        missing_descriptions = {
            "carrier": "your insurance carrier or company name",
            "member_id": "your member ID or policy number",
            "group_number": "your group number or employer group ID"
        }
        
        missing_items = [missing_descriptions.get(item, item) for item in missing_info]
        
        # Show what we already have
        collected_info = []
        if insurance_data.get("carrier"):
            collected_info.append(f"Insurance Carrier: {insurance_data['carrier']}")
        if insurance_data.get("member_id"):
            collected_info.append(f"Member ID: {insurance_data['member_id']}")
        if insurance_data.get("group_number"):
            collected_info.append(f"Group Number: {insurance_data['group_number']}")
        
        prompt = f"""
        A patient is providing insurance information for their medical appointment.
        
        Information already collected: {', '.join(collected_info) if collected_info else 'None'}
        Still missing: {', '.join(missing_items)}
        
        Create a friendly, professional request for the missing insurance information.
        Explain that we need this for billing and appointment confirmation.
        Be conversational and reassuring about data privacy.
        Keep it under 60 words.
        """
        
        response = llm.invoke([HumanMessage(content=prompt)])
        return response.content
        
    except Exception as e:
        logger.error(f"Error generating insurance request with Gemini: {str(e)}")
        
        # Fallback response
        if "carrier" in missing_info:
            return "I'll need your insurance information for billing. Could you please tell me your insurance carrier or company name?"
        elif "member_id" in missing_info:
            return "Great! I also need your member ID or policy number. You can find this on your insurance card."
        else:
            return "Finally, I'll need your group number, which is also typically found on your insurance card."

def _generate_insurance_confirmation_with_gemini(insurance_data: Dict[str, Any], llm) -> str:
    """Generate confirmation message when all insurance info is collected."""
    try:
        carrier = insurance_data.get("carrier", "")
        member_id = insurance_data.get("member_id", "")
        group_number = insurance_data.get("group_number", "")
        
        prompt = f"""
        Create a brief, professional confirmation message for a patient who has provided 
        complete insurance information:
        
        Insurance Carrier: {carrier}
        Member ID: {member_id}
        Group Number: {group_number}
        
        Confirm that we have their insurance details and mention that we'll now 
        proceed to finalize their appointment booking.
        
        Keep it warm, professional, and under 50 words.
        """
        
        response = llm.invoke([HumanMessage(content=prompt)])
        return response.content
        
    except Exception as e:
        logger.error(f"Error generating insurance confirmation with Gemini: {str(e)}")
        return f"Perfect! I have all your insurance information: {carrier}, Member ID {member_id}, Group {group_number}. Let me finalize your appointment booking now."

def format_insurance_info_display(insurance_data: Dict[str, Any]) -> str:
    """Format insurance information for display or confirmation."""
    if not insurance_data:
        return "No insurance information collected yet."
    
    display_parts = []
    
    if insurance_data.get("carrier"):
        display_parts.append(f"Insurance Carrier: {insurance_data['carrier']}")
    
    if insurance_data.get("member_id"):
        display_parts.append(f"Member ID: {insurance_data['member_id']}")
    
    if insurance_data.get("group_number"):
        display_parts.append(f"Group Number: {insurance_data['group_number']}")
    
    return "\n".join(display_parts)

def validate_insurance_completeness(insurance_data: Dict[str, Any]) -> Tuple[bool, List[str]]:
    """Validate insurance information for completeness and accuracy."""
    issues = []
    
    # Check required fields
    if not insurance_data.get("carrier"):
        issues.append("Insurance carrier is required")
    
    if not insurance_data.get("member_id"):
        issues.append("Member ID or policy number is required")
    elif len(insurance_data["member_id"]) < 5:
        issues.append("Member ID appears to be too short")
    
    if not insurance_data.get("group_number"):
        issues.append("Group number is required")
    elif len(insurance_data["group_number"]) < 3:
        issues.append("Group number appears to be too short")
    
    return len(issues) == 0, issues

# ============================================================================
# TESTING FUNCTION
# ============================================================================

def test_insurance_extraction():
    """Test function to validate insurance information extraction capabilities."""
    
    print("Testing Insurance Information Extraction")
    print("=" * 50)
    
    test_cases = [
        "My insurance carrier is BlueCross BlueShield, member ID ABC123456, group number GRP789",
        "I have UnitedHealthcare insurance, policy number XYZ987654",
        "Insurance company: Aetna, my member id is DEF456789, group GRP123",
        "I'm covered by Kaiser Permanente, member number KP555666, employer group EMP999",
        "My carrier is Cigna and the group number is CIG789"
    ]
    
    extractor = InsuranceInfoExtractor()
    
    for i, test_text in enumerate(test_cases, 1):
        print(f"\nTest Case {i}: {test_text}")
        extracted = extractor.extract_from_text(test_text)
        print(f"Extracted: {extracted}")
        
        # Test missing info detection
        missing = _get_missing_insurance_info(extracted)
        if missing:
            print(f"Missing: {missing}")
        else:
            print("All required insurance information collected!")

if __name__ == "__main__":
    # Run tests when executed directly
    test_insurance_extraction()
