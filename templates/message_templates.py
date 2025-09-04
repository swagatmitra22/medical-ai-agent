"""
Message Templates - Medical Appointment Scheduling System
======================================================

This module provides comprehensive SMS and notification templates for appointment
reminders, confirmations, and patient communications. All templates are optimized
for SMS character limits while maintaining professional medical communication standards.

Key Features:
- Professional medical-grade SMS templates
- 160-character optimized messages for standard SMS
- 3-tier reminder system (24hr, 4hr, 1hr)
- Template variables for personalization
- Action-based reminders with response requests
- Integration with LangGraph workflow system
- HIPAA-compliant communication standards

Author: RagaAI Case Study Implementation
Date: September 2025
"""

import logging
from typing import Dict, Any, List, Optional
from datetime import datetime, timedelta

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# ============================================================================
# SMS MESSAGE TEMPLATES
# ============================================================================

# Standard SMS templates (optimized for 160 characters)
SMS_REMINDER_TEMPLATES = {
    # 24-hour reminder (standard reminder)
    "24_hour": "Hi {patient_name}, reminder: You have an appointment tomorrow ({appointment_date}) at {appointment_time} with {doctor_name}. Please arrive 15 min early. {clinic_name} - {clinic_phone}",
    
    # 4-hour reminder (with form check and confirmation request)
    "4_hour": "Hi {patient_name}, your appointment with {doctor_name} is in 4 hours at {appointment_time}. Have you completed your intake forms? Please reply YES to confirm attendance. {clinic_name} - {clinic_phone}",
    
    # 1-hour final reminder (with confirmation request and cancellation option)
    "1_hour": "FINAL REMINDER: {patient_name}, your appointment is in 1 hour at {appointment_time} with {doctor_name}. Please reply YES to confirm or call {clinic_phone} if canceling. {clinic_name}",
}

# Appointment confirmation messages
CONFIRMATION_SMS_TEMPLATES = {
    "appointment_confirmed": "✅ Appointment CONFIRMED! {patient_name}, you're scheduled for {appointment_date} at {appointment_time} with {doctor_name}. Confirmation ID: {confirmation_id}. {clinic_name}",
    
    "new_patient_confirmed": "✅ Welcome {patient_name}! Your first visit is confirmed for {appointment_date} at {appointment_time} with {doctor_name}. Check email for intake forms. {clinic_name} - {clinic_phone}",
    
    "returning_patient_confirmed": "✅ Welcome back {patient_name}! Your follow-up is confirmed for {appointment_date} at {appointment_time} with {doctor_name}. See you soon! {clinic_name}",
}

# Form-related notifications
FORM_NOTIFICATION_TEMPLATES = {
    "forms_sent": "📋 {patient_name}, your intake forms have been emailed. Please complete before your {appointment_date} appointment. Need help? Call {clinic_phone}. {clinic_name}",
    
    "forms_reminder": "📋 Reminder: Please complete your intake forms before tomorrow's appointment at {appointment_time} with {doctor_name}. Questions? Call {clinic_phone}. {clinic_name}",
    
    "forms_incomplete": "📋 {patient_name}, we haven't received your completed forms. Please submit before your appointment at {appointment_time} today. {clinic_name} - {clinic_phone}",
}

# Cancellation and rescheduling messages
CANCELLATION_SMS_TEMPLATES = {
    "appointment_cancelled": "❌ {patient_name}, your appointment on {appointment_date} at {appointment_time} has been cancelled. To reschedule, call {clinic_phone}. {clinic_name}",
    
    "patient_cancellation_confirmed": "✅ {patient_name}, your cancellation for {appointment_date} at {appointment_time} is confirmed. To reschedule, call {clinic_phone}. Thank you! {clinic_name}",
    
    "reschedule_confirmed": "📅 {patient_name}, your appointment has been rescheduled to {appointment_date} at {appointment_time} with {doctor_name}. Confirmation ID: {confirmation_id}. {clinic_name}",
}

# Response handling templates
RESPONSE_TEMPLATES = {
    "confirmation_received": "Thank you {patient_name}! Your attendance is confirmed for {appointment_time} with {doctor_name}. We look forward to seeing you! {clinic_name}",
    
    "cancellation_received": "Thank you for notifying us {patient_name}. Your {appointment_date} appointment is cancelled. Reason: {cancellation_reason}. To reschedule: {clinic_phone}. {clinic_name}",
    
    "forms_completed_confirmed": "✅ Thank you {patient_name}! We've received your completed forms. See you at {appointment_time} for your appointment with {doctor_name}. {clinic_name}",
    
    "invalid_response": "We didn't understand your response. For {appointment_date} appointment: Reply YES to confirm, NO to cancel, or call {clinic_phone}. {clinic_name}",
}

# General notification templates
NOTIFICATION_TEMPLATES = {
    "welcome_message": "Welcome to {clinic_name}! We're committed to providing excellent healthcare. For appointments or questions, call {clinic_phone}.",
    
    "insurance_reminder": "📄 {patient_name}, please bring your insurance card and photo ID to your {appointment_date} appointment. {clinic_name}",
    
    "arrival_reminder": "🏥 {patient_name}, please arrive 15 minutes early for check-in at your {appointment_time} appointment today. {clinic_name} - {clinic_address}",
    
    "post_visit_followup": "Thank you for visiting {clinic_name} today, {patient_name}! If you have any questions about your visit, please call {clinic_phone}.",
}

# Emergency and urgent templates
URGENT_TEMPLATES = {
    "appointment_today": "🚨 {patient_name}, you have an appointment TODAY at {appointment_time} with {doctor_name}. Please confirm by replying YES or call {clinic_phone} immediately. {clinic_name}",
    
    "late_arrival": "⏰ {patient_name}, you're late for your {appointment_time} appointment. Please call {clinic_phone} immediately if you're still coming. {clinic_name}",
    
    "no_show_followup": "We missed you at your {appointment_time} appointment today, {patient_name}. Please call {clinic_phone} to reschedule. {clinic_name}",
}

# ============================================================================
# MESSAGE TEMPLATE ENGINE CLASS
# ============================================================================

class MessageTemplateEngine:
    """
    Comprehensive SMS message template engine for medical appointment communications.
    """
    
    def __init__(self):
        """Initialize the message template engine."""
        self.templates = {
            'reminders': SMS_REMINDER_TEMPLATES,
            'confirmations': CONFIRMATION_SMS_TEMPLATES,
            'forms': FORM_NOTIFICATION_TEMPLATES,
            'cancellations': CANCELLATION_SMS_TEMPLATES,
            'responses': RESPONSE_TEMPLATES,
            'notifications': NOTIFICATION_TEMPLATES,
            'urgent': URGENT_TEMPLATES
        }
        
        # Default clinic information
        self.default_clinic_info = {
            'clinic_name': 'MediCare Wellness',  # Shortened for SMS
            'clinic_phone': '(555) 123-4567',
            'clinic_address': '456 Healthcare Blvd, Suite 300'
        }
        
        # SMS character limits
        self.SMS_LIMIT_STANDARD = 160
        self.SMS_LIMIT_EXTENDED = 1600
    
    def get_reminder_message(self, appointment_details: Dict[str, Any], reminder_type: str) -> str:
        """
        Get SMS reminder message for the specified type.
        
        Args:
            appointment_details: Dictionary containing appointment information
            reminder_type: Type of reminder ('24_hour', '4_hour', '1_hour')
            
        Returns:
            Formatted SMS message string
        """
        try:
            # Merge appointment details with default clinic info
            template_vars = {**self.default_clinic_info, **appointment_details}
            
            # Get the appropriate template
            template = self.templates['reminders'].get(reminder_type)
            if not template:
                logger.error(f"Unknown reminder type: {reminder_type}")
                return self._get_fallback_reminder(template_vars, reminder_type)
            
            # Format the message
            message = template.format(**template_vars)
            
            # Validate message length
            if len(message) > self.SMS_LIMIT_STANDARD:
                logger.warning(f"SMS message exceeds {self.SMS_LIMIT_STANDARD} characters: {len(message)}")
                return self._truncate_message(message, self.SMS_LIMIT_STANDARD)
            
            return message
            
        except Exception as e:
            logger.error(f"Error generating reminder message: {str(e)}")
            return self._get_fallback_reminder(appointment_details, reminder_type)
    
    def get_confirmation_message(self, appointment_details: Dict[str, Any]) -> str:
        """
        Get appointment confirmation SMS message.
        
        Args:
            appointment_details: Dictionary containing appointment information
            
        Returns:
            Formatted confirmation message string
        """
        try:
            template_vars = {**self.default_clinic_info, **appointment_details}
            patient_type = appointment_details.get('patient_type', 'returning')
            
            # Select appropriate confirmation template
            if patient_type == 'new':
                template = self.templates['confirmations']['new_patient_confirmed']
            else:
                template = self.templates['confirmations']['returning_patient_confirmed']
            
            message = template.format(**template_vars)
            
            # Validate message length
            if len(message) > self.SMS_LIMIT_STANDARD:
                message = self._truncate_message(message, self.SMS_LIMIT_STANDARD)
            
            return message
            
        except Exception as e:
            logger.error(f"Error generating confirmation message: {str(e)}")
            return self._get_fallback_confirmation(appointment_details)
    
    def get_form_notification_message(self, appointment_details: Dict[str, Any], notification_type: str) -> str:
        """
        Get form-related notification message.
        
        Args:
            appointment_details: Dictionary containing appointment information
            notification_type: Type of notification ('forms_sent', 'forms_reminder', 'forms_incomplete')
            
        Returns:
            Formatted notification message string
        """
        try:
            template_vars = {**self.default_clinic_info, **appointment_details}
            template = self.templates['forms'].get(notification_type)
            
            if not template:
                logger.error(f"Unknown form notification type: {notification_type}")
                return self._get_fallback_form_message(template_vars)
            
            message = template.format(**template_vars)
            
            if len(message) > self.SMS_LIMIT_STANDARD:
                message = self._truncate_message(message, self.SMS_LIMIT_STANDARD)
            
            return message
            
        except Exception as e:
            logger.error(f"Error generating form notification: {str(e)}")
            return self._get_fallback_form_message(appointment_details)
    
    def get_cancellation_message(self, appointment_details: Dict[str, Any], cancellation_type: str) -> str:
        """
        Get cancellation or rescheduling message.
        
        Args:
            appointment_details: Dictionary containing appointment information
            cancellation_type: Type of cancellation message
            
        Returns:
            Formatted cancellation message string
        """
        try:
            template_vars = {**self.default_clinic_info, **appointment_details}
            template = self.templates['cancellations'].get(cancellation_type)
            
            if not template:
                logger.error(f"Unknown cancellation type: {cancellation_type}")
                return self._get_fallback_cancellation(template_vars)
            
            message = template.format(**template_vars)
            
            if len(message) > self.SMS_LIMIT_STANDARD:
                message = self._truncate_message(message, self.SMS_LIMIT_STANDARD)
            
            return message
            
        except Exception as e:
            logger.error(f"Error generating cancellation message: {str(e)}")
            return self._get_fallback_cancellation(appointment_details)
    
    def get_response_message(self, appointment_details: Dict[str, Any], response_type: str) -> str:
        """
        Get response acknowledgment message.
        
        Args:
            appointment_details: Dictionary containing appointment information
            response_type: Type of response ('confirmation_received', 'cancellation_received', etc.)
            
        Returns:
            Formatted response message string
        """
        try:
            template_vars = {**self.default_clinic_info, **appointment_details}
            template = self.templates['responses'].get(response_type)
            
            if not template:
                logger.error(f"Unknown response type: {response_type}")
                return "Thank you for your response. We'll be in touch soon!"
            
            message = template.format(**template_vars)
            
            if len(message) > self.SMS_LIMIT_STANDARD:
                message = self._truncate_message(message, self.SMS_LIMIT_STANDARD)
            
            return message
            
        except Exception as e:
            logger.error(f"Error generating response message: {str(e)}")
            return "Thank you for contacting us!"
    
    def _truncate_message(self, message: str, max_length: int) -> str:
        """Truncate message to fit SMS limits."""
        if len(message) <= max_length:
            return message
        
        # Truncate and add ellipsis
        truncated = message[:max_length-3] + "..."
        logger.warning(f"Message truncated from {len(message)} to {len(truncated)} characters")
        
        return truncated
    
    def _get_fallback_reminder(self, appointment_details: Dict[str, Any], reminder_type: str) -> str:
        """Generate simple fallback reminder message."""
        patient_name = appointment_details.get('patient_name', 'Patient')
        appointment_time = appointment_details.get('appointment_time', 'TBD')
        clinic_phone = self.default_clinic_info['clinic_phone']
        
        if reminder_type == '1_hour':
            return f"REMINDER: {patient_name}, your appointment is in 1 hour at {appointment_time}. Call {clinic_phone} if needed."
        elif reminder_type == '4_hour':
            return f"Reminder: {patient_name}, your appointment is in 4 hours at {appointment_time}. Please confirm."
        else:
            return f"Reminder: {patient_name}, you have an appointment tomorrow at {appointment_time}."
    
    def _get_fallback_confirmation(self, appointment_details: Dict[str, Any]) -> str:
        """Generate simple fallback confirmation message."""
        patient_name = appointment_details.get('patient_name', 'Patient')
        appointment_date = appointment_details.get('appointment_date', 'TBD')
        appointment_time = appointment_details.get('appointment_time', 'TBD')
        
        return f"Confirmed: {patient_name}, your appointment is {appointment_date} at {appointment_time}. MediCare Wellness"
    
    def _get_fallback_form_message(self, appointment_details: Dict[str, Any]) -> str:
        """Generate simple fallback form message."""
        patient_name = appointment_details.get('patient_name', 'Patient')
        return f"Hi {patient_name}, please complete your intake forms. Call (555) 123-4567 for help. MediCare Wellness"
    
    def _get_fallback_cancellation(self, appointment_details: Dict[str, Any]) -> str:
        """Generate simple fallback cancellation message."""
        patient_name = appointment_details.get('patient_name', 'Patient')
        return f"Hi {patient_name}, regarding your appointment: Please call (555) 123-4567. MediCare Wellness"

# ============================================================================
# CONVENIENCE FUNCTIONS FOR LANGGRAPH INTEGRATION
# ============================================================================

def get_sms_template(template_category: str, template_type: str, appointment_details: Dict[str, Any]) -> str:
    """
    Get SMS template message for the specified category and type.
    
    Args:
        template_category: Category of template ('reminders', 'confirmations', etc.)
        template_type: Specific template type within the category
        appointment_details: Appointment information for template variables
        
    Returns:
        Formatted SMS message string
    """
    engine = MessageTemplateEngine()
    
    if template_category == 'reminders':
        return engine.get_reminder_message(appointment_details, template_type)
    elif template_category == 'confirmations':
        return engine.get_confirmation_message(appointment_details)
    elif template_category == 'forms':
        return engine.get_form_notification_message(appointment_details, template_type)
    elif template_category == 'cancellations':
        return engine.get_cancellation_message(appointment_details, template_type)
    elif template_category == 'responses':
        return engine.get_response_message(appointment_details, template_type)
    else:
        logger.error(f"Unknown template category: {template_category}")
        return "Thank you for contacting MediCare Wellness. We'll be in touch soon!"

def render_sms_message(template_name: str, **kwargs) -> str:
    """
    Render SMS message template with provided variables.
    
    Args:
        template_name: Name of the template (format: category.type)
        **kwargs: Template variables
        
    Returns:
        Rendered SMS message string
    """
    try:
        engine = MessageTemplateEngine()
        
        # Parse template name
        if '.' in template_name:
            category, template_type = template_name.split('.', 1)
        else:
            category = 'reminders'
            template_type = template_name
        
        # Merge with default clinic info
        template_vars = {**engine.default_clinic_info, **kwargs}
        
        # Get template
        template = engine.templates.get(category, {}).get(template_type, '')
        
        if not template:
            logger.error(f"Template not found: {template_name}")
            return "Message template not available."
        
        message = template.format(**template_vars)
        
        # Validate length
        if len(message) > engine.SMS_LIMIT_STANDARD:
            message = engine._truncate_message(message, engine.SMS_LIMIT_STANDARD)
        
        return message
        
    except Exception as e:
        logger.error(f"Error rendering SMS template {template_name}: {str(e)}")
        return "Unable to generate message."

def create_reminder_message(appointment_details: Dict[str, Any], hours_before: int) -> str:
    """
    Create reminder message based on hours before appointment.
    
    Args:
        appointment_details: Appointment information
        hours_before: Number of hours before appointment (24, 4, or 1)
        
    Returns:
        Formatted reminder message
    """
    reminder_type_map = {
        24: '24_hour',
        4: '4_hour',
        1: '1_hour'
    }
    
    reminder_type = reminder_type_map.get(hours_before, '24_hour')
    engine = MessageTemplateEngine()
    
    return engine.get_reminder_message(appointment_details, reminder_type)

def validate_sms_length(message: str) -> Dict[str, Any]:
    """
    Validate SMS message length and provide recommendations.
    
    Args:
        message: SMS message to validate
        
    Returns:
        Dictionary with validation results
    """
    length = len(message)
    
    result = {
        'length': length,
        'is_standard_sms': length <= 160,
        'is_extended_sms': length <= 1600,
        'segment_count': (length // 160) + 1 if length > 160 else 1,
        'recommendation': 'OK'
    }
    
    if length > 1600:
        result['recommendation'] = 'Message too long - will be truncated'
    elif length > 160:
        result['recommendation'] = f'Long message - will be split into {result["segment_count"]} segments'
    
    return result

# ============================================================================
# TESTING FUNCTIONS
# ============================================================================

def test_message_templates():
    """Test function to validate message template generation."""
    
    print("Testing SMS Message Template System")
    print("=" * 50)
    
    # Test data
    test_appointment = {
        'patient_name': 'John Test',
        'appointment_date': '09/15/2025',
        'appointment_time': '10:00 AM',
        'doctor_name': 'Dr. Johnson',
        'confirmation_id': 'TEST-12345'
    }
    
    engine = MessageTemplateEngine()
    
    # Test reminder messages
    print("\n1. Testing Reminder Messages:")
    for reminder_type in ['24_hour', '4_hour', '1_hour']:
        message = engine.get_reminder_message(test_appointment, reminder_type)
        validation = validate_sms_length(message)
        print(f"✅ {reminder_type}: {len(message)} chars - {validation['recommendation']}")
        print(f"   Message: {message}")
    
    # Test confirmation message
    print("\n2. Testing Confirmation Messages:")
    for patient_type in ['new', 'returning']:
        test_appointment['patient_type'] = patient_type
        message = engine.get_confirmation_message(test_appointment)
        validation = validate_sms_length(message)
        print(f"✅ {patient_type} patient: {len(message)} chars - {validation['recommendation']}")
        print(f"   Message: {message}")
    
    # Test form notifications
    print("\n3. Testing Form Notifications:")
    for form_type in ['forms_sent', 'forms_reminder', 'forms_incomplete']:
        message = engine.get_form_notification_message(test_appointment, form_type)
        validation = validate_sms_length(message)
        print(f"✅ {form_type}: {len(message)} chars - {validation['recommendation']}")
    
    # Test convenience functions
    print("\n4. Testing Convenience Functions:")
    reminder_msg = create_reminder_message(test_appointment, 24)
    print(f"✅ 24-hour reminder via convenience function: {len(reminder_msg)} chars")
    
    print("\n" + "=" * 50)
    print("SMS message template system test completed!")

if __name__ == "__main__":
    # Run tests when executed directly
    test_message_templates()
