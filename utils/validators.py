"""
Data Validators - Medical Appointment Scheduling System
====================================================

This module provides comprehensive data validation utilities for the medical
appointment scheduling AI system. It includes validators for patient information,
appointment data, insurance details, and business rule enforcement.

Key Features:
- HIPAA-compliant validation (no sensitive data in logs)
- Medical-specific validation rules and formats
- Comprehensive patient data validation
- Insurance and contact information verification
- Appointment scheduling business rule validation
- Integration with error handling system
- Sanitization and data cleaning utilities

Author: RagaAI Case Study Implementation
Date: September 2025
"""

import re
import logging
from typing import Dict, Any, List, Optional, Tuple, Union
from datetime import datetime, date, timedelta
from enum import Enum

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# ============================================================================
# CONSTANTS AND ENUMS
# ============================================================================

class PatientType(Enum):
    """Enumeration for patient types."""
    NEW = "new"
    RETURNING = "returning"
    EXISTING = "existing"

class AppointmentDuration(Enum):
    """Standard appointment durations in minutes."""
    NEW_PATIENT = 60
    RETURNING_PATIENT = 30
    CONSULTATION = 45
    FOLLOW_UP = 15

class Gender(Enum):
    """Valid gender options."""
    MALE = "male"
    FEMALE = "female"
    OTHER = "other"
    PREFER_NOT_TO_SAY = "prefer_not_to_say"

# Valid US states (abbreviated)
US_STATES = {
    'AL', 'AK', 'AZ', 'AR', 'CA', 'CO', 'CT', 'DE', 'FL', 'GA',
    'HI', 'ID', 'IL', 'IN', 'IA', 'KS', 'KY', 'LA', 'ME', 'MD',
    'MA', 'MI', 'MN', 'MS', 'MO', 'MT', 'NE', 'NV', 'NH', 'NJ',
    'NM', 'NY', 'NC', 'ND', 'OH', 'OK', 'OR', 'PA', 'RI', 'SC',
    'SD', 'TN', 'TX', 'UT', 'VT', 'VA', 'WA', 'WV', 'WI', 'WY'
}

# Common insurance carriers
INSURANCE_CARRIERS = {
    'BlueCross BlueShield', 'BCBS', 'UnitedHealthcare', 'United Healthcare',
    'Aetna', 'Cigna', 'Humana', 'Kaiser Permanente', 'Kaiser',
    'Anthem', 'Molina Healthcare', 'Molina', 'Centene', 'WellCare',
    'Medicare', 'Medicaid', 'Tricare', 'GEHA'
}

# ============================================================================
# VALIDATION EXCEPTION CLASSES
# ============================================================================

class ValidationError(Exception):
    """Base class for validation errors."""
    
    def __init__(self, message: str, field: Optional[str] = None, value: Any = None):
        """
        Initialize validation error.
        
        Args:
            message: Error description
            field: Field name that failed validation
            value: Sanitized representation of the invalid value
        """
        super().__init__(message)
        self.message = message
        self.field = field
        self.value = self._sanitize_value(value)
    
    def _sanitize_value(self, value: Any) -> str:
        """Sanitize value for logging (remove potential PHI)."""
        if value is None:
            return "None"
        
        value_str = str(value)
        
        # Check for potential PHI patterns and redact
        if re.search(r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b', value_str):
            return "[EMAIL_REDACTED]"
        elif re.search(r'\b\d{3}[-.]?\d{3}[-.]?\d{4}\b', value_str):
            return "[PHONE_REDACTED]"
        elif re.search(r'\b[A-Z][a-z]+ [A-Z][a-z]+\b', value_str):
            return "[NAME_REDACTED]"
        elif len(value_str) > 50:
            return f"[VALUE_TOO_LONG_{len(value_str)}_CHARS]"
        else:
            return value_str

class PatientValidationError(ValidationError):
    """Validation error specific to patient data."""
    pass

class AppointmentValidationError(ValidationError):
    """Validation error specific to appointment data."""
    pass

class InsuranceValidationError(ValidationError):
    """Validation error specific to insurance data."""
    pass

# ============================================================================
# CORE VALIDATOR CLASSES
# ============================================================================

class PatientDataValidator:
    """Validator for patient-related data."""
    
    @staticmethod
    def validate_patient_name(name: str) -> Tuple[bool, Optional[str]]:
        """
        Validate patient name.
        
        Args:
            name: Patient name to validate
            
        Returns:
            Tuple of (is_valid, error_message)
        """
        if not name or not isinstance(name, str):
            return False, "Name is required and must be a string"
        
        name = name.strip()
        
        if len(name) < 2:
            return False, "Name must be at least 2 characters long"
        
        if len(name) > 100:
            return False, "Name must be less than 100 characters"
        
        # Allow letters, spaces, hyphens, apostrophes, and periods
        if not re.match(r"^[A-Za-z\s\-'.]+$", name):
            return False, "Name can only contain letters, spaces, hyphens, apostrophes, and periods"
        
        # Check for at least one letter
        if not re.search(r'[A-Za-z]', name):
            return False, "Name must contain at least one letter"
        
        # Validate name parts
        name_parts = name.split()
        if len(name_parts) < 1:
            return False, "Name must have at least one part"
        
        for part in name_parts:
            if len(part.replace('-', '').replace("'", "").replace(".", "")) == 0:
                return False, "Name parts cannot be empty after removing punctuation"
        
        return True, None
    
    @staticmethod
    def validate_date_of_birth(dob: str) -> Tuple[bool, Optional[str]]:
        """
        Validate date of birth.
        
        Args:
            dob: Date of birth string
            
        Returns:
            Tuple of (is_valid, error_message)
        """
        if not dob or not isinstance(dob, str):
            return False, "Date of birth is required"
        
        # Try different date formats
        date_formats = ['%m/%d/%Y', '%m-%d-%Y', '%Y-%m-%d', '%d/%m/%Y', '%d-%m-%Y']
        parsed_date = None
        
        for fmt in date_formats:
            try:
                parsed_date = datetime.strptime(dob.strip(), fmt)
                break
            except ValueError:
                continue
        
        if not parsed_date:
            return False, "Invalid date format. Use MM/DD/YYYY, MM-DD-YYYY, or YYYY-MM-DD"
        
        # Validate date range
        today = datetime.now()
        min_date = datetime(1900, 1, 1)
        
        if parsed_date > today:
            return False, "Date of birth cannot be in the future"
        
        if parsed_date < min_date:
            return False, "Date of birth cannot be before 1900"
        
        # Calculate age
        age = today.year - parsed_date.year
        if today.month < parsed_date.month or (today.month == parsed_date.month and today.day < parsed_date.day):
            age -= 1
        
        if age > 150:
            return False, "Age cannot exceed 150 years"
        
        return True, None
    
    @staticmethod
    def validate_phone_number(phone: str) -> Tuple[bool, Optional[str]]:
        """
        Validate phone number.
        
        Args:
            phone: Phone number to validate
            
        Returns:
            Tuple of (is_valid, error_message)
        """
        if not phone or not isinstance(phone, str):
            return False, "Phone number is required"
        
        # Remove all non-digit characters
        digits_only = re.sub(r'[^\d]', '', phone)
        
        # Check for valid US phone number patterns
        if len(digits_only) == 10:
            # Standard 10-digit US number
            if not re.match(r'^[2-9]\d{2}[2-9]\d{6}$', digits_only):
                return False, "Invalid US phone number format"
        elif len(digits_only) == 11 and digits_only.startswith('1'):
            # 11-digit with country code
            if not re.match(r'^1[2-9]\d{2}[2-9]\d{6}$', digits_only):
                return False, "Invalid US phone number with country code"
        else:
            return False, "Phone number must be 10 digits (US) or 11 digits with country code"
        
        return True, None
    
    @staticmethod
    def validate_email_address(email: str) -> Tuple[bool, Optional[str]]:
        """
        Validate email address.
        
        Args:
            email: Email address to validate
            
        Returns:
            Tuple of (is_valid, error_message)
        """
        if not email or not isinstance(email, str):
            return False, "Email address is required"
        
        email = email.strip().lower()
        
        # Basic email format validation
        email_pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
        if not re.match(email_pattern, email):
            return False, "Invalid email address format"
        
        # Additional checks
        if len(email) > 320:  # RFC 5321 limit
            return False, "Email address is too long"
        
        local_part, domain_part = email.rsplit('@', 1)
        
        if len(local_part) > 64:  # RFC 5321 limit for local part
            return False, "Email local part is too long"
        
        if len(domain_part) > 255:  # RFC 5321 limit for domain
            return False, "Email domain is too long"
        
        # Check for consecutive dots
        if '..' in email:
            return False, "Email address cannot contain consecutive dots"
        
        return True, None
    
    @staticmethod
    def validate_gender(gender: str) -> Tuple[bool, Optional[str]]:
        """
        Validate gender selection.
        
        Args:
            gender: Gender value to validate
            
        Returns:
            Tuple of (is_valid, error_message)
        """
        if not gender or not isinstance(gender, str):
            return False, "Gender is required"
        
        gender_lower = gender.strip().lower()
        valid_genders = [g.value for g in Gender]
        
        if gender_lower not in valid_genders:
            return False, f"Gender must be one of: {', '.join(valid_genders)}"
        
        return True, None

class AddressValidator:
    """Validator for address and location data."""
    
    @staticmethod
    def validate_street_address(address: str) -> Tuple[bool, Optional[str]]:
        """Validate street address."""
        if not address or not isinstance(address, str):
            return False, "Street address is required"
        
        address = address.strip()
        
        if len(address) < 5:
            return False, "Street address must be at least 5 characters"
        
        if len(address) > 200:
            return False, "Street address must be less than 200 characters"
        
        # Must contain at least one digit (house number)
        if not re.search(r'\d', address):
            return False, "Street address must contain a house number"
        
        return True, None
    
    @staticmethod
    def validate_city(city: str) -> Tuple[bool, Optional[str]]:
        """Validate city name."""
        if not city or not isinstance(city, str):
            return False, "City is required"
        
        city = city.strip()
        
        if len(city) < 2:
            return False, "City name must be at least 2 characters"
        
        if len(city) > 50:
            return False, "City name must be less than 50 characters"
        
        # Allow letters, spaces, hyphens, and apostrophes
        if not re.match(r"^[A-Za-z\s\-'.]+$", city):
            return False, "City name can only contain letters, spaces, hyphens, apostrophes, and periods"
        
        return True, None
    
    @staticmethod
    def validate_state(state: str) -> Tuple[bool, Optional[str]]:
        """Validate US state."""
        if not state or not isinstance(state, str):
            return False, "State is required"
        
        state = state.strip().upper()
        
        if state not in US_STATES:
            return False, f"Invalid US state code. Must be one of: {', '.join(sorted(US_STATES))}"
        
        return True, None
    
    @staticmethod
    def validate_zip_code(zip_code: str) -> Tuple[bool, Optional[str]]:
        """Validate US ZIP code."""
        if not zip_code or not isinstance(zip_code, str):
            return False, "ZIP code is required"
        
        zip_code = zip_code.strip()
        
        # Standard 5-digit ZIP or ZIP+4
        if not re.match(r'^\d{5}(-\d{4})?$', zip_code):
            return False, "ZIP code must be 5 digits or 5+4 format (12345 or 12345-6789)"
        
        return True, None

class InsuranceValidator:
    """Validator for insurance-related data."""
    
    @staticmethod
    def validate_insurance_carrier(carrier: str) -> Tuple[bool, Optional[str]]:
        """Validate insurance carrier name."""
        if not carrier or not isinstance(carrier, str):
            return False, "Insurance carrier is required"
        
        carrier = carrier.strip()
        
        if len(carrier) < 2:
            return False, "Insurance carrier name must be at least 2 characters"
        
        if len(carrier) > 100:
            return False, "Insurance carrier name must be less than 100 characters"
        
        # Check if it's a known carrier (case-insensitive)
        carrier_lower = carrier.lower()
        known_carriers_lower = {c.lower() for c in INSURANCE_CARRIERS}
        
        if carrier_lower not in known_carriers_lower:
            logger.info(f"Unknown insurance carrier provided: {carrier[:20]}...")  # Log first 20 chars only
        
        return True, None
    
    @staticmethod
    def validate_member_id(member_id: str) -> Tuple[bool, Optional[str]]:
        """Validate insurance member ID."""
        if not member_id or not isinstance(member_id, str):
            return False, "Member ID is required"
        
        member_id = member_id.strip()
        
        if len(member_id) < 3:
            return False, "Member ID must be at least 3 characters"
        
        if len(member_id) > 20:
            return False, "Member ID must be less than 20 characters"
        
        # Allow alphanumeric characters, hyphens, and underscores
        if not re.match(r'^[A-Za-z0-9\-_]+$', member_id):
            return False, "Member ID can only contain letters, numbers, hyphens, and underscores"
        
        return True, None
    
    @staticmethod
    def validate_group_number(group_number: str) -> Tuple[bool, Optional[str]]:
        """Validate insurance group number."""
        if not group_number or not isinstance(group_number, str):
            return False, "Group number is required"
        
        group_number = group_number.strip()
        
        if len(group_number) < 3:
            return False, "Group number must be at least 3 characters"
        
        if len(group_number) > 15:
            return False, "Group number must be less than 15 characters"
        
        # Allow alphanumeric characters and hyphens
        if not re.match(r'^[A-Za-z0-9\-]+$', group_number):
            return False, "Group number can only contain letters, numbers, and hyphens"
        
        return True, None

class AppointmentValidator:
    """Validator for appointment-related data."""
    
    @staticmethod
    def validate_appointment_date(appointment_date: str) -> Tuple[bool, Optional[str]]:
        """Validate appointment date."""
        if not appointment_date or not isinstance(appointment_date, str):
            return False, "Appointment date is required"
        
        # Try different date formats
        date_formats = ['%m/%d/%Y', '%Y-%m-%d', '%m-%d-%Y']
        parsed_date = None
        
        for fmt in date_formats:
            try:
                parsed_date = datetime.strptime(appointment_date.strip(), fmt)
                break
            except ValueError:
                continue
        
        if not parsed_date:
            return False, "Invalid date format. Use MM/DD/YYYY, YYYY-MM-DD, or MM-DD-YYYY"
        
        # Must be today or in the future
        today = datetime.now().date()
        if parsed_date.date() < today:
            return False, "Appointment date cannot be in the past"
        
        # Not too far in the future (1 year max)
        max_future_date = today + timedelta(days=365)
        if parsed_date.date() > max_future_date:
            return False, "Appointment date cannot be more than 1 year in the future"
        
        return True, None
    
    @staticmethod
    def validate_appointment_time(appointment_time: str) -> Tuple[bool, Optional[str]]:
        """Validate appointment time."""
        if not appointment_time or not isinstance(appointment_time, str):
            return False, "Appointment time is required"
        
        # Try different time formats
        time_formats = ['%I:%M %p', '%H:%M', '%I:%M%p']  # 2:30 PM, 14:30, 2:30PM
        parsed_time = None
        
        for fmt in time_formats:
            try:
                parsed_time = datetime.strptime(appointment_time.strip().upper(), fmt)
                break
            except ValueError:
                continue
        
        if not parsed_time:
            return False, "Invalid time format. Use HH:MM AM/PM or HH:MM (24-hour)"
        
        # Check if time is within business hours (8 AM - 6 PM)
        hour = parsed_time.hour
        if hour < 8 or hour >= 18:
            return False, "Appointment time must be between 8:00 AM and 6:00 PM"
        
        # Check if minutes are in 15-minute intervals
        if parsed_time.minute % 15 != 0:
            return False, "Appointment time must be in 15-minute intervals (e.g., 2:00, 2:15, 2:30, 2:45)"
        
        return True, None
    
    @staticmethod
    def validate_appointment_duration(duration: int, patient_type: str) -> Tuple[bool, Optional[str]]:
        """Validate appointment duration based on patient type."""
        if duration is None or not isinstance(duration, int):
            return False, "Appointment duration is required and must be an integer"
        
        if duration <= 0:
            return False, "Appointment duration must be positive"
        
        if duration > 240:  # 4 hours max
            return False, "Appointment duration cannot exceed 4 hours"
        
        # Validate based on patient type
        patient_type_lower = patient_type.lower() if patient_type else ""
        
        if patient_type_lower == PatientType.NEW.value:
            if duration != AppointmentDuration.NEW_PATIENT.value:
                return False, f"New patient appointments must be {AppointmentDuration.NEW_PATIENT.value} minutes"
        elif patient_type_lower in [PatientType.RETURNING.value, PatientType.EXISTING.value]:
            if duration != AppointmentDuration.RETURNING_PATIENT.value:
                return False, f"Returning patient appointments must be {AppointmentDuration.RETURNING_PATIENT.value} minutes"
        
        return True, None
    
    @staticmethod
    def validate_doctor_name(doctor_name: str) -> Tuple[bool, Optional[str]]:
        """Validate doctor name."""
        if not doctor_name or not isinstance(doctor_name, str):
            return False, "Doctor name is required"
        
        doctor_name = doctor_name.strip()
        
        if len(doctor_name) < 5:  # At least "Dr. X"
            return False, "Doctor name must be at least 5 characters"
        
        if len(doctor_name) > 100:
            return False, "Doctor name must be less than 100 characters"
        
        # Must start with "Dr." or "Doctor"
        if not (doctor_name.startswith("Dr. ") or doctor_name.startswith("Doctor ")):
            return False, "Doctor name must start with 'Dr. ' or 'Doctor '"
        
        return True, None

# ============================================================================
# COMPOSITE VALIDATORS
# ============================================================================

class PatientRecordValidator:
    """Comprehensive validator for complete patient records."""
    
    @staticmethod
    def validate_patient_record(patient_data: Dict[str, Any]) -> Tuple[bool, List[str]]:
        """
        Validate complete patient record.
        
        Args:
            patient_data: Patient data dictionary
            
        Returns:
            Tuple of (is_valid, list_of_errors)
        """
        errors = []
        
        # Required fields
        required_fields = ['name', 'dob', 'phone', 'email']
        for field in required_fields:
            if field not in patient_data or not patient_data[field]:
                errors.append(f"Required field '{field}' is missing")
        
        # Validate individual fields
        validators = {
            'name': PatientDataValidator.validate_patient_name,
            'dob': PatientDataValidator.validate_date_of_birth,
            'phone': PatientDataValidator.validate_phone_number,
            'email': PatientDataValidator.validate_email_address,
            'gender': PatientDataValidator.validate_gender,
            'street_address': AddressValidator.validate_street_address,
            'city': AddressValidator.validate_city,
            'state': AddressValidator.validate_state,
            'zip_code': AddressValidator.validate_zip_code,
        }
        
        for field, validator in validators.items():
            if field in patient_data and patient_data[field]:
                is_valid, error_msg = validator(patient_data[field])
                if not is_valid:
                    errors.append(f"{field.title()}: {error_msg}")
        
        return len(errors) == 0, errors

class AppointmentRecordValidator:
    """Comprehensive validator for appointment records."""
    
    @staticmethod
    def validate_appointment_record(appointment_data: Dict[str, Any]) -> Tuple[bool, List[str]]:
        """
        Validate complete appointment record.
        
        Args:
            appointment_data: Appointment data dictionary
            
        Returns:
            Tuple of (is_valid, list_of_errors)
        """
        errors = []
        
        # Required fields
        required_fields = ['patient_name', 'appointment_date', 'appointment_time', 'doctor_name']
        for field in required_fields:
            if field not in appointment_data or not appointment_data[field]:
                errors.append(f"Required field '{field}' is missing")
        
        # Validate individual fields
        if 'appointment_date' in appointment_data:
            is_valid, error_msg = AppointmentValidator.validate_appointment_date(appointment_data['appointment_date'])
            if not is_valid:
                errors.append(f"Appointment date: {error_msg}")
        
        if 'appointment_time' in appointment_data:
            is_valid, error_msg = AppointmentValidator.validate_appointment_time(appointment_data['appointment_time'])
            if not is_valid:
                errors.append(f"Appointment time: {error_msg}")
        
        if 'doctor_name' in appointment_data:
            is_valid, error_msg = AppointmentValidator.validate_doctor_name(appointment_data['doctor_name'])
            if not is_valid:
                errors.append(f"Doctor name: {error_msg}")
        
        if 'duration' in appointment_data and 'patient_type' in appointment_data:
            is_valid, error_msg = AppointmentValidator.validate_appointment_duration(
                appointment_data['duration'], 
                appointment_data['patient_type']
            )
            if not is_valid:
                errors.append(f"Appointment duration: {error_msg}")
        
        return len(errors) == 0, errors

# ============================================================================
# UTILITY FUNCTIONS
# ============================================================================

def validate_required_fields(data: Dict[str, Any], required_fields: List[str]) -> List[str]:
    """
    Validate that required fields are present and non-empty.
    
    Args:
        data: Data dictionary to validate
        required_fields: List of required field names
        
    Returns:
        List of missing field names
    """
    missing_fields = []
    
    for field in required_fields:
        if field not in data or not data[field] or (isinstance(data[field], str) and not data[field].strip()):
            missing_fields.append(field)
    
    return missing_fields

def sanitize_input(input_str: str) -> str:
    """
    Sanitize input string by removing dangerous characters.
    
    Args:
        input_str: String to sanitize
        
    Returns:
        Sanitized string
    """
    if not isinstance(input_str, str):
        return ""
    
    # Remove potential script injection attempts
    dangerous_patterns = [
        r'<script.*?</script>',
        r'javascript:',
        r'onload=',
        r'onerror=',
        r'<.*?>',  # HTML tags
    ]
    
    sanitized = input_str
    for pattern in dangerous_patterns:
        sanitized = re.sub(pattern, '', sanitized, flags=re.IGNORECASE | re.DOTALL)
    
    return sanitized.strip()

def format_phone_number(phone: str) -> str:
    """
    Format phone number to standard (XXX) XXX-XXXX format.
    
    Args:
        phone: Phone number to format
        
    Returns:
        Formatted phone number
    """
    if not phone:
        return ""
    
    # Extract digits only
    digits = re.sub(r'[^\d]', '', phone)
    
    if len(digits) == 10:
        return f"({digits[:3]}) {digits[3:6]}-{digits[6:]}"
    elif len(digits) == 11 and digits.startswith('1'):
        return f"+1 ({digits[1:4]}) {digits[4:7]}-{digits[7:]}"
    else:
        return phone  # Return original if can't format

def normalize_name(name: str) -> str:
    """
    Normalize name to title case.
    
    Args:
        name: Name to normalize
        
    Returns:
        Normalized name
    """
    if not name or not isinstance(name, str):
        return ""
    
    # Split on spaces and handle each part
    parts = []
    for part in name.strip().split():
        # Handle hyphenated names
        if '-' in part:
            hyphen_parts = [p.capitalize() for p in part.split('-')]
            parts.append('-'.join(hyphen_parts))
        # Handle apostrophes (like O'Connor)
        elif "'" in part:
            apos_parts = part.split("'")
            if len(apos_parts) == 2 and apos_parts[0] and apos_parts[1]:
                parts.append(f"{apos_parts[0].capitalize()}'{apos_parts[1].capitalize()}")
            else:
                parts.append(part.capitalize())
        else:
            parts.append(part.capitalize())
    
    return ' '.join(parts)

# ============================================================================
# TESTING FUNCTIONS
# ============================================================================

def test_validators():
    """Comprehensive test function for all validators."""
    
    print("Testing Medical AI Validator System")
    print("=" * 50)
    
    # Test patient data validation
    print("\n1. Testing Patient Data Validation:")
    
    # Valid data
    valid_patient = {
        'name': 'John Doe',
        'dob': '01/15/1985',
        'phone': '(555) 123-4567',
        'email': 'john.doe@email.com',
        'gender': 'male'
    }
    
    is_valid, errors = PatientRecordValidator.validate_patient_record(valid_patient)
    print(f"✅ Valid patient record: {is_valid}")
    if errors:
        print(f"   Errors: {errors}")
    
    # Invalid data
    invalid_patient = {
        'name': 'J',  # Too short
        'dob': '13/45/2025',  # Invalid date
        'phone': '123',  # Too short
        'email': 'invalid-email',  # Invalid format
        'gender': 'unknown'  # Invalid gender
    }
    
    is_valid, errors = PatientRecordValidator.validate_patient_record(invalid_patient)
    print(f"❌ Invalid patient record: {is_valid}")
    print(f"   Expected errors found: {len(errors)}")
    
    # Test appointment validation
    print("\n2. Testing Appointment Validation:")
    
    valid_appointment = {
        'patient_name': 'John Doe',
        'appointment_date': '12/15/2025',
        'appointment_time': '2:30 PM',
        'doctor_name': 'Dr. Johnson',
        'duration': 60,
        'patient_type': 'new'
    }
    
    is_valid, errors = AppointmentRecordValidator.validate_appointment_record(valid_appointment)
    print(f"✅ Valid appointment record: {is_valid}")
    if errors:
        print(f"   Errors: {errors}")
    
    # Test utility functions
    print("\n3. Testing Utility Functions:")
    
    # Test phone formatting
    formatted_phone = format_phone_number("5551234567")
    print(f"✅ Phone formatting: {formatted_phone}")
    
    # Test name normalization
    normalized_name = normalize_name("john o'connor-smith")
    print(f"✅ Name normalization: {normalized_name}")
    
    # Test input sanitization
    sanitized = sanitize_input("<script>alert('hack')</script>John Doe")
    print(f"✅ Input sanitization: {sanitized}")
    
    print("\n" + "=" * 50)
    print("Validator system test completed!")

if __name__ == "__main__":
    # Run tests when executed directly
    test_validators()
