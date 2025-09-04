"""
Appointment Confirmation Agent - Medical Appointment Scheduling System
===================================================================

This module handles the generation of comprehensive appointment confirmations
using Google's Gemini AI. It creates personalized confirmation messages,
manages confirmation details, and integrates with the communication system.

Key Responsibilities:
- Generate personalized confirmation messages using Gemini AI
- Create comprehensive appointment confirmation details
- Calculate estimated revenue for appointments
- Setup reminder schedules for 3-tier notification system
- Handle new vs returning patient confirmation differences
- Integrate with email and SMS notification systems
- Generate confirmation IDs and tracking information

Author: RagaAI Case Study Implementation
Date: September 2025
"""

import logging
from typing import Dict, Any, List, Optional, Tuple
from datetime import datetime, timedelta
from langchain_core.messages import HumanMessage, AIMessage, BaseMessage
import uuid
import random

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# ============================================================================
# CONFIRMATION TEMPLATES AND CONSTANTS
# ============================================================================

# Revenue estimates by appointment type and specialty
REVENUE_ESTIMATES = {
    "Family Medicine": {"new": 275, "returning": 150},
    "Cardiology": {"new": 450, "returning": 200},
    "Dermatology": {"new": 350, "returning": 180},
    "Orthopedics": {"new": 400, "returning": 220},
    "Internal Medicine": {"new": 300, "returning": 160}
}

# Default revenue if specialty not found
DEFAULT_REVENUE = {"new": 300, "returning": 175}

# Clinic information for confirmations
CLINIC_INFO = {
    "name": "MediCare Allergy & Wellness Center",
    "address": "456 Healthcare Boulevard, Suite 300",
    "phone": "(555) 123-4567",
    "email": "appointments@medicare-wellness.com",
    "website": "www.medicare-wellness.com"
}

# ============================================================================
# CONFIRMATION GENERATOR CLASS
# ============================================================================

class AppointmentConfirmationGenerator:
    """
    Handles comprehensive appointment confirmation generation and processing.
    """
    
    def __init__(self):
        """Initialize the confirmation generator."""
        self.clinic_info = CLINIC_INFO
        self.revenue_estimates = REVENUE_ESTIMATES
    
    def generate_confirmation_id(self) -> str:
        """Generate a unique confirmation ID."""
        timestamp = datetime.now().strftime('%Y%m%d%H%M%S')
        random_suffix = str(random.randint(1000, 9999))
        return f"CONF-{timestamp}-{random_suffix}"
    
    def calculate_estimated_revenue(self, patient_type: str, doctor_specialty: str) -> float:
        """
        Calculate estimated revenue for the appointment.
        
        Args:
            patient_type: Type of patient ('new' or 'returning')
            doctor_specialty: Doctor's specialty
            
        Returns:
            Estimated revenue amount
        """
        try:
            # Clean up specialty name
            specialty = doctor_specialty.replace('(', '').replace(')', '').strip()
            
            # Get revenue estimate
            specialty_rates = self.revenue_estimates.get(specialty, DEFAULT_REVENUE)
            revenue = specialty_rates.get(patient_type, specialty_rates.get("new", 300))
            
            # Add some variation (±10%)
            variation = random.uniform(0.9, 1.1)
            return round(revenue * variation, 2)
            
        except Exception as e:
            logger.error(f"Error calculating revenue: {str(e)}")
            return DEFAULT_REVENUE.get(patient_type, 300)
    
    def create_reminder_schedule(self, appointment_date: str, appointment_time: str) -> List[Dict[str, Any]]:
        """
        Create 3-tier reminder schedule.
        
        Args:
            appointment_date: Appointment date string (MM/DD/YYYY)
            appointment_time: Appointment time string
            
        Returns:
            List of reminder schedule items
        """
        try:
            # Parse appointment datetime
            datetime_str = f"{appointment_date} {appointment_time}"
            formats = ['%m/%d/%Y %I:%M %p', '%m/%d/%Y %H:%M']
            
            appointment_datetime = None
            for fmt in formats:
                try:
                    appointment_datetime = datetime.strptime(datetime_str, fmt)
                    break
                except ValueError:
                    continue
            
            if not appointment_datetime:
                logger.warning(f"Could not parse appointment datetime: {datetime_str}")
                return []
            
            # Create reminder schedule
            reminders = []
            
            # 24-hour reminder
            reminder_24hr = appointment_datetime - timedelta(hours=24)
            reminders.append({
                'reminder_type': '24_hour',
                'send_time': reminder_24hr.isoformat(),
                'method': 'email',
                'includes_form_check': False
            })
            
            # 4-hour reminder
            reminder_4hr = appointment_datetime - timedelta(hours=4)
            reminders.append({
                'reminder_type': '4_hour',
                'send_time': reminder_4hr.isoformat(),
                'method': 'sms',
                'includes_form_check': True
            })
            
            # 1-hour reminder
            reminder_1hr = appointment_datetime - timedelta(hours=1)
            reminders.append({
                'reminder_type': '1_hour',
                'send_time': reminder_1hr.isoformat(),
                'method': 'sms',
                'includes_form_check': False
            })
            
            return reminders
            
        except Exception as e:
            logger.error(f"Error creating reminder schedule: {str(e)}")
            return []
    
    def create_confirmation_details(self, state: Dict[str, Any]) -> Dict[str, Any]:
        """
        Create comprehensive confirmation details dictionary.
        
        Args:
            state: Current appointment state
            
        Returns:
            Dictionary containing all confirmation details
        """
        try:
            # Extract information from state
            patient_info = state.get("patient_info", {})
            selected_slot = state.get("selected_slot", {})
            insurance_data = state.get("insurance_data", {})
            patient_type = state.get("patient_type", "new")
            appointment_duration = state.get("appointment_duration", 60)
            
            # Generate confirmation ID
            confirmation_id = self.generate_confirmation_id()
            
            # Calculate estimated revenue
            doctor_specialty = selected_slot.get("specialty", "General")
            estimated_revenue = self.calculate_estimated_revenue(patient_type, doctor_specialty)
            
            # Create reminder schedule
            reminder_schedule = self.create_reminder_schedule(
                selected_slot.get("date", ""),
                selected_slot.get("start_time", "")
            )
            
            # Determine if forms are required (new patients)
            requires_forms = patient_type == "new"
            
            # Create comprehensive confirmation details
            confirmation_details = {
                'confirmation_id': confirmation_id,
                'confirmation_timestamp': datetime.now().isoformat(),
                'patient_name': patient_info.get("name", ""),
                'patient_type': patient_type,
                'patient_phone': patient_info.get("phone", ""),
                'patient_email': patient_info.get("email", ""),
                'appointment_date': selected_slot.get("date", ""),
                'appointment_time': selected_slot.get("start_time", ""),
                'appointment_end_time': selected_slot.get("end_time", ""),
                'appointment_duration': appointment_duration,
                'doctor_name': selected_slot.get("doctor_name", ""),
                'doctor_specialty': doctor_specialty,
                'insurance_carrier': insurance_data.get("carrier", ""),
                'member_id': insurance_data.get("member_id", ""),
                'group_number': insurance_data.get("group_number", ""),
                'estimated_revenue': estimated_revenue,
                'requires_forms': requires_forms,
                'booking_status': 'confirmed',
                'reminder_schedule': reminder_schedule,
                'clinic_name': self.clinic_info['name'],
                'clinic_address': self.clinic_info['address'],
                'clinic_phone': self.clinic_info['phone'],
                'clinic_email': self.clinic_info['email'],
                'clinic_website': self.clinic_info['website']
            }
            
            return confirmation_details
            
        except Exception as e:
            logger.error(f"Error creating confirmation details: {str(e)}")
            return {'confirmation_id': 'ERROR', 'error': str(e)}

# ============================================================================
# MAIN CONFIRMATION FUNCTIONS FOR LANGGRAPH INTEGRATION
# ============================================================================

def generate_appointment_confirmation_with_gemini(state: Dict[str, Any], llm) -> Dict[str, Any]:
    """
    Generate comprehensive appointment confirmation using Gemini AI.
    
    Args:
        state: Current appointment state
        llm: Gemini LLM instance for generating confirmation message
        
    Returns:
        Updated state with confirmation details and message
    """
    logger.info("Generating appointment confirmation with Gemini")
    
    try:
        # Initialize confirmation generator
        generator = AppointmentConfirmationGenerator()
        
        # Create comprehensive confirmation details
        confirmation_details = generator.create_confirmation_details(state)
        
        if 'error' in confirmation_details:
            return {
                **state,
                "error_message": f"Confirmation generation error: {confirmation_details['error']}",
                "current_step": "error"
            }
        
        # Generate personalized confirmation message using Gemini
        confirmation_message = _generate_confirmation_message_with_gemini(confirmation_details, llm)
        
        # Update state with all confirmation information
        updated_state = {
            **state,
            "confirmation_details": confirmation_details,
            "confirmation_message": confirmation_message,
            "confirmation_id": confirmation_details['confirmation_id'],
            "estimated_revenue": confirmation_details['estimated_revenue'],
            "reminder_schedule": confirmation_details['reminder_schedule'],
            "requires_forms": confirmation_details['requires_forms'],
            "confirmation_status": "generated",
            "current_step": "notifications"
        }
        
        # Add confirmation message to conversation
        if confirmation_message:
            updated_state["messages"] = state["messages"] + [AIMessage(content=confirmation_message)]
        
        logger.info(f"Confirmation generated successfully: {confirmation_details['confirmation_id']}")
        return updated_state
        
    except Exception as e:
        logger.error(f"Error in appointment confirmation generation: {str(e)}")
        return {
            **state,
            "error_message": f"Confirmation generation error: {str(e)}",
            "current_step": "error"
        }

def _generate_confirmation_message_with_gemini(confirmation_details: Dict[str, Any], llm) -> str:
    """
    Generate personalized confirmation message using Gemini.
    
    Args:
        confirmation_details: Complete confirmation details
        llm: Gemini LLM instance
        
    Returns:
        Generated confirmation message
    """
    try:
        # Create detailed prompt for Gemini
        prompt = f"""
        Create a professional, warm, and comprehensive appointment confirmation message for a medical patient.
        
        Patient Information:
        - Name: {confirmation_details.get('patient_name', '')}
        - Type: {confirmation_details.get('patient_type', '').title()} Patient
        - Phone: {confirmation_details.get('patient_phone', '')}
        - Email: {confirmation_details.get('patient_email', '')}
        
        Appointment Details:
        - Date: {confirmation_details.get('appointment_date', '')}
        - Time: {confirmation_details.get('appointment_time', '')} - {confirmation_details.get('appointment_end_time', '')}
        - Duration: {confirmation_details.get('appointment_duration', '')} minutes
        - Doctor: {confirmation_details.get('doctor_name', '')}
        - Specialty: {confirmation_details.get('doctor_specialty', '')}
        - Confirmation ID: {confirmation_details.get('confirmation_id', '')}
        
        Clinic Information:
        - Name: {confirmation_details.get('clinic_name', '')}
        - Address: {confirmation_details.get('clinic_address', '')}
        - Phone: {confirmation_details.get('clinic_phone', '')}
        
        Additional Instructions:
        {"- New patients: You'll receive intake forms via email. Please complete them before your visit." if confirmation_details.get('requires_forms') else "- Please arrive 15 minutes early for check-in."}
        
        Guidelines for the message:
        1. Start with a warm congratulatory tone
        2. Include ALL appointment details clearly
        3. Mention the confirmation ID prominently
        4. Include clinic location and contact information
        5. Add appropriate instructions based on patient type
        6. Include reminder about insurance card and ID
        7. Mention our 3-tier reminder system
        8. End with a welcoming note
        9. Keep it professional but personable
        10. Use proper formatting with clear sections
        
        Make it comprehensive but easy to read, like a professional medical office would send.
        """
        
        # Generate message using Gemini
        response = llm.invoke([HumanMessage(content=prompt)])
        
        return response.content
        
    except Exception as e:
        logger.error(f"Error generating confirmation message with Gemini: {str(e)}")
        
        # Fallback confirmation message
        patient_name = confirmation_details.get('patient_name', 'Patient')
        appointment_date = confirmation_details.get('appointment_date', 'TBD')
        appointment_time = confirmation_details.get('appointment_time', 'TBD')
        doctor_name = confirmation_details.get('doctor_name', 'your doctor')
        confirmation_id = confirmation_details.get('confirmation_id', 'N/A')
        
        return f"""🎉 Appointment Confirmed!

Dear {patient_name},

Your appointment has been successfully scheduled!

📅 APPOINTMENT DETAILS:
Date: {appointment_date}
Time: {appointment_time}
Doctor: {doctor_name}
Confirmation ID: {confirmation_id}

🏥 LOCATION:
MediCare Allergy & Wellness Center
456 Healthcare Boulevard, Suite 300
Phone: (555) 123-4567

📋 IMPORTANT REMINDERS:
• Please arrive 15 minutes early
• Bring your insurance card and photo ID
• You'll receive email confirmation and reminders

Thank you for choosing MediCare Allergy & Wellness Center. We look forward to providing you with excellent care!"""

# ============================================================================
# UTILITY FUNCTIONS
# ============================================================================

def format_confirmation_summary(confirmation_details: Dict[str, Any]) -> str:
    """
    Format confirmation details into a readable summary.
    
    Args:
        confirmation_details: Confirmation details dictionary
        
    Returns:
        Formatted summary string
    """
    try:
        return f"""
APPOINTMENT CONFIRMATION SUMMARY
================================

Confirmation ID: {confirmation_details.get('confirmation_id', 'N/A')}
Patient: {confirmation_details.get('patient_name', 'N/A')}
Type: {confirmation_details.get('patient_type', 'N/A').title()} Patient
Date: {confirmation_details.get('appointment_date', 'N/A')}
Time: {confirmation_details.get('appointment_time', 'N/A')} - {confirmation_details.get('appointment_end_time', 'N/A')}
Duration: {confirmation_details.get('appointment_duration', 'N/A')} minutes
Doctor: {confirmation_details.get('doctor_name', 'N/A')} ({confirmation_details.get('doctor_specialty', 'N/A')})
Insurance: {confirmation_details.get('insurance_carrier', 'N/A')}
Estimated Revenue: ${confirmation_details.get('estimated_revenue', 0):.2f}
Requires Forms: {'Yes' if confirmation_details.get('requires_forms') else 'No'}
Reminders Scheduled: {len(confirmation_details.get('reminder_schedule', []))}
Status: {confirmation_details.get('booking_status', 'N/A').title()}
        """.strip()
        
    except Exception as e:
        logger.error(f"Error formatting confirmation summary: {str(e)}")
        return "Error generating confirmation summary"

def validate_confirmation_completeness(confirmation_details: Dict[str, Any]) -> Tuple[bool, List[str]]:
    """
    Validate confirmation details for completeness.
    
    Args:
        confirmation_details: Confirmation details to validate
        
    Returns:
        Tuple of (is_complete, list_of_missing_items)
    """
    required_fields = [
        'confirmation_id', 'patient_name', 'appointment_date', 'appointment_time',
        'doctor_name', 'patient_phone', 'patient_email'
    ]
    
    missing_fields = []
    for field in required_fields:
        if not confirmation_details.get(field):
            missing_fields.append(field)
    
    return len(missing_fields) == 0, missing_fields

# ============================================================================
# TESTING FUNCTIONS
# ============================================================================

def test_confirmation_generation():
    """Test function to validate confirmation generation."""
    
    print("Testing Appointment Confirmation System")
    print("=" * 50)
    
    # Test data
    test_state = {
        "patient_info": {
            "name": "John Test Patient",
            "phone": "(555) 123-4567",
            "email": "john@test.com"
        },
        "selected_slot": {
            "date": "09/15/2025",
            "start_time": "10:00 AM",
            "end_time": "11:00 AM",
            "doctor_name": "Dr. Johnson",
            "specialty": "Family Medicine"
        },
        "insurance_data": {
            "carrier": "BlueCross BlueShield",
            "member_id": "BC123456789",
            "group_number": "GRP001"
        },
        "patient_type": "new",
        "appointment_duration": 60,
        "messages": []
    }
    
    # Test confirmation details generation
    print("\n1. Testing Confirmation Details Generation:")
    generator = AppointmentConfirmationGenerator()
    confirmation_details = generator.create_confirmation_details(test_state)
    
    print(f"✅ Confirmation ID: {confirmation_details.get('confirmation_id')}")
    print(f"✅ Estimated Revenue: ${confirmation_details.get('estimated_revenue', 0):.2f}")
    print(f"✅ Reminders Scheduled: {len(confirmation_details.get('reminder_schedule', []))}")
    
    # Test validation
    print("\n2. Testing Validation:")
    is_complete, missing = validate_confirmation_completeness(confirmation_details)
    print(f"✅ Confirmation Complete: {is_complete}")
    if missing:
        print(f"   Missing fields: {missing}")
    
    # Test summary formatting
    print("\n3. Testing Summary Formatting:")
    summary = format_confirmation_summary(confirmation_details)
    print("✅ Summary generated successfully")
    print(summary[:200] + "..." if len(summary) > 200 else summary)
    
    print("\n" + "=" * 50)
    print("Confirmation system test completed!")

if __name__ == "__main__":
    # Run tests when executed directly
    test_confirmation_generation()
