"""
Patient Lookup Agent - Medical Appointment Scheduling System
========================================================

This module handles patient database lookups to determine if a patient
is new or returning, and retrieves existing patient information.

Key Responsibilities:
- Search patient database (CSV) for existing records
- Implement fuzzy matching for names and dates
- Classify patients as "new" or "returning"
- Retrieve existing patient data and insurance information
- Handle data inconsistencies and edge cases
- Update patient type for appointment duration determination

Author: RagaAI Case Study Implementation
Date: September 2025
"""

import os
import pandas as pd
import logging
from typing import Dict, Any, Optional, List, Tuple
from datetime import datetime, timedelta
from fuzzywuzzy import fuzz
from dotenv import load_dotenv
import re

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# ============================================================================
# PATIENT DATABASE MANAGER CLASS
# ============================================================================

class PatientDatabaseManager:
    """
    Manages patient database operations including search, lookup, and updates.
    """
    
    def __init__(self, db_path: str = None):
        """
        Initialize the patient database manager.
        
        Args:
            db_path: Path to the patient CSV file
        """
        self.db_path = db_path or os.getenv("PATIENT_DB_PATH", "data/patients.csv")
        self.patients_df = None
        self._load_database()
    
    def _load_database(self):
        """Load patient database from CSV file."""
        try:
            if os.path.exists(self.db_path):
                self.patients_df = pd.read_csv(self.db_path)
                logger.info(f"Loaded {len(self.patients_df)} patient records from {self.db_path}")
            else:
                logger.warning(f"Patient database not found at {self.db_path}")
                # Create empty DataFrame with expected columns
                self.patients_df = pd.DataFrame(columns=[
                    'patient_id', 'name', 'dob', 'phone', 'email', 'patient_type',
                    'last_visit', 'insurance_carrier', 'member_id', 'group_number',
                    'address', 'emergency_contact', 'medical_history'
                ])
        except Exception as e:
            logger.error(f"Error loading patient database: {str(e)}")
            self.patients_df = pd.DataFrame()
    
    def search_patient(self, name: str, dob: str, phone: str = None) -> Dict[str, Any]:
        """
        Search for a patient in the database using multiple criteria.
        
        Args:
            name: Patient's full name
            dob: Date of birth (MM/DD/YYYY format)
            phone: Optional phone number for additional verification
            
        Returns:
            Dictionary containing search results and patient classification
        """
        if self.patients_df.empty:
            return {
                "found": False,
                "patient_type": "new",
                "confidence": 0,
                "existing_data": {},
                "matches": []
            }
        
        # Primary search: Exact and fuzzy matching
        exact_matches = self._find_exact_matches(name, dob)
        fuzzy_matches = self._find_fuzzy_matches(name, dob)
        
        # Combine and rank matches
        all_matches = self._rank_matches(exact_matches + fuzzy_matches, name, dob, phone)
        
        if all_matches:
            best_match = all_matches[0]
            
            # Determine if this is a returning patient based on confidence threshold
            is_returning = best_match["confidence"] >= 85
            
            return {
                "found": is_returning,
                "patient_type": "returning" if is_returning else "new",
                "confidence": best_match["confidence"],
                "existing_data": best_match["data"] if is_returning else {},
                "matches": all_matches[:3],  # Return top 3 matches
                "best_match": best_match
            }
        
        return {
            "found": False,
            "patient_type": "new",
            "confidence": 0,
            "existing_data": {},
            "matches": []
        }
    
    def _find_exact_matches(self, name: str, dob: str) -> List[Dict[str, Any]]:
        """Find exact matches for name and date of birth."""
        matches = []
        
        try:
            # Normalize inputs
            name_normalized = self._normalize_name(name)
            dob_normalized = self._normalize_date(dob)
            
            if not dob_normalized:
                return matches
            
            for idx, row in self.patients_df.iterrows():
                db_name = self._normalize_name(str(row.get('name', '')))
                db_dob = self._normalize_date(str(row.get('dob', '')))
                
                if db_name == name_normalized and db_dob == dob_normalized:
                    matches.append({
                        "index": idx,
                        "confidence": 100,
                        "match_type": "exact",
                        "data": row.to_dict()
                    })
        
        except Exception as e:
            logger.error(f"Error in exact match search: {str(e)}")
        
        return matches
    
    def _find_fuzzy_matches(self, name: str, dob: str) -> List[Dict[str, Any]]:
        """Find fuzzy matches using string similarity algorithms."""
        matches = []
        
        try:
            name_normalized = self._normalize_name(name)
            dob_normalized = self._normalize_date(dob)
            
            if not dob_normalized:
                return matches
            
            for idx, row in self.patients_df.iterrows():
                db_name = self._normalize_name(str(row.get('name', '')))
                db_dob = self._normalize_date(str(row.get('dob', '')))
                
                # Calculate name similarity
                name_similarity = fuzz.ratio(name_normalized, db_name)
                
                # Calculate DOB similarity (more strict)
                dob_similarity = 100 if db_dob == dob_normalized else 0
                
                # Weighted confidence score
                confidence = (name_similarity * 0.7) + (dob_similarity * 0.3)
                
                # Only include matches above minimum threshold
                if confidence >= 60:
                    matches.append({
                        "index": idx,
                        "confidence": round(confidence, 1),
                        "match_type": "fuzzy",
                        "name_similarity": name_similarity,
                        "dob_similarity": dob_similarity,
                        "data": row.to_dict()
                    })
        
        except Exception as e:
            logger.error(f"Error in fuzzy match search: {str(e)}")
        
        return matches
    
    def _rank_matches(self, matches: List[Dict], name: str, dob: str, phone: str = None) -> List[Dict]:
        """
        Rank matches by confidence and additional verification criteria.
        
        Args:
            matches: List of potential matches
            name: Original name query
            dob: Original DOB query
            phone: Optional phone for additional verification
            
        Returns:
            Sorted list of matches by confidence score
        """
        if not matches:
            return []
        
        # Add phone verification bonus if provided
        if phone:
            phone_normalized = self._normalize_phone(phone)
            
            for match in matches:
                db_phone = self._normalize_phone(str(match["data"].get("phone", "")))
                if db_phone and phone_normalized == db_phone:
                    match["confidence"] = min(100, match["confidence"] + 15)
                    match["phone_verified"] = True
                else:
                    match["phone_verified"] = False
        
        # Sort by confidence (highest first)
        ranked_matches = sorted(matches, key=lambda x: x["confidence"], reverse=True)
        
        return ranked_matches
    
    def _normalize_name(self, name: str) -> str:
        """Normalize name for consistent comparison."""
        if not name or pd.isna(name):
            return ""
        
        # Convert to lowercase, remove extra spaces, handle special characters
        normalized = re.sub(r'[^\w\s]', '', str(name).lower().strip())
        normalized = re.sub(r'\s+', ' ', normalized)
        
        return normalized
    
    def _normalize_date(self, date_str: str) -> str:
        """Normalize date string to MM/DD/YYYY format."""
        if not date_str or pd.isna(date_str):
            return ""
        
        try:
            # Try different date formats
            formats = ['%m/%d/%Y', '%m-%d-%Y', '%Y/%m/%d', '%Y-%m-%d', '%m/%d/%y', '%m-%d-%y']
            
            for fmt in formats:
                try:
                    date_obj = datetime.strptime(str(date_str).strip(), fmt)
                    return date_obj.strftime('%m/%d/%Y')
                except ValueError:
                    continue
            
            return ""
            
        except Exception as e:
            logger.error(f"Error normalizing date {date_str}: {str(e)}")
            return ""
    
    def _normalize_phone(self, phone: str) -> str:
        """Normalize phone number for comparison."""
        if not phone or pd.isna(phone):
            return ""
        
        # Remove all non-digit characters
        digits_only = re.sub(r'[^\d]', '', str(phone))
        
        # Handle US phone numbers (10 or 11 digits)
        if len(digits_only) == 11 and digits_only.startswith('1'):
            digits_only = digits_only[1:]
        
        return digits_only if len(digits_only) == 10 else ""
    
    def update_patient_record(self, patient_data: Dict[str, Any]) -> bool:
        """
        Update existing patient record or create new one.
        
        Args:
            patient_data: Patient information dictionary
            
        Returns:
            True if successful, False otherwise
        """
        try:
            if "patient_id" in patient_data and patient_data["patient_id"]:
                # Update existing record
                mask = self.patients_df['patient_id'] == patient_data['patient_id']
                if mask.any():
                    for key, value in patient_data.items():
                        if key in self.patients_df.columns:
                            self.patients_df.loc[mask, key] = value
                    logger.info(f"Updated patient record: {patient_data['patient_id']}")
                    return True
            
            # Create new patient record
            new_patient_id = self._generate_patient_id()
            patient_data['patient_id'] = new_patient_id
            patient_data['created_date'] = datetime.now().strftime('%Y-%m-%d')
            
            new_row = pd.DataFrame([patient_data])
            self.patients_df = pd.concat([self.patients_df, new_row], ignore_index=True)
            
            logger.info(f"Created new patient record: {new_patient_id}")
            return True
            
        except Exception as e:
            logger.error(f"Error updating patient record: {str(e)}")
            return False
    
    def _generate_patient_id(self) -> str:
        """Generate a unique patient ID."""
        timestamp = datetime.now().strftime('%Y%m%d%H%M%S')
        return f"P{timestamp}"
    
    def save_database(self) -> bool:
        """Save the current database state to CSV file."""
        try:
            self.patients_df.to_csv(self.db_path, index=False)
            logger.info(f"Patient database saved to {self.db_path}")
            return True
        except Exception as e:
            logger.error(f"Error saving patient database: {str(e)}")
            return False

# ============================================================================
# MAIN LOOKUP FUNCTION FOR LANGGRAPH INTEGRATION
# ============================================================================

def perform_patient_lookup(state: Dict[str, Any]) -> Dict[str, Any]:
    """
    Main function to perform patient lookup and classification.
    
    This function is called by the LangGraph core agent to search for
    existing patient records and determine patient type.
    
    Args:
        state: Current appointment state containing patient info
        
    Returns:
        Updated state with patient lookup results
    """
    logger.info("Performing patient database lookup")
    
    try:
        # Extract patient information from state
        patient_info = state.get("patient_info", {})
        name = patient_info.get("name", "")
        dob = patient_info.get("dob", "")
        phone = patient_info.get("phone", "")
        
        # Validate required information
        if not name or not dob:
            return {
                **state,
                "error_message": "Name and date of birth required for patient lookup",
                "patient_type": "new",
                "existing_patient_data": {}
            }
        
        # Initialize database manager
        db_manager = PatientDatabaseManager()
        
        # Perform patient search
        search_results = db_manager.search_patient(name, dob, phone)
        
        # Update state based on search results
        updated_state = {
            **state,
            "patient_type": search_results["patient_type"],
            "existing_patient_data": search_results["existing_data"],
            "patient_lookup_confidence": search_results["confidence"],
            "patient_matches": search_results.get("matches", [])
        }
        
        # Log results
        if search_results["found"]:
            logger.info(f"Found returning patient: {name} (confidence: {search_results['confidence']}%)")
            
            # Merge existing data with current patient info
            merged_info = {**search_results["existing_data"], **patient_info}
            updated_state["patient_info"] = merged_info
            
        else:
            logger.info(f"New patient identified: {name}")
            
            # Create new patient record
            new_patient_data = {
                **patient_info,
                "patient_type": "new",
                "first_visit": True,
                "registration_date": datetime.now().strftime('%Y-%m-%d')
            }
            
            # Save to database
            db_manager.update_patient_record(new_patient_data)
            db_manager.save_database()
        
        return updated_state
        
    except Exception as e:
        logger.error(f"Error in patient lookup: {str(e)}")
        return {
            **state,
            "error_message": f"Patient lookup error: {str(e)}",
            "patient_type": "new",
            "existing_patient_data": {}
        }

# ============================================================================
# UTILITY FUNCTIONS
# ============================================================================

def format_patient_lookup_summary(state: Dict[str, Any]) -> str:
    """
    Format a human-readable summary of patient lookup results.
    
    Args:
        state: Appointment state with lookup results
        
    Returns:
        Formatted summary string
    """
    patient_type = state.get("patient_type", "unknown")
    confidence = state.get("patient_lookup_confidence", 0)
    patient_info = state.get("patient_info", {})
    name = patient_info.get("name", "Unknown")
    
    if patient_type == "returning":
        existing_data = state.get("existing_patient_data", {})
        last_visit = existing_data.get("last_visit", "Unknown")
        insurance = existing_data.get("insurance_carrier", "Not on file")
        
        return f"""Patient Lookup Results:
        
Patient: {name}
Status: Returning Patient (Confidence: {confidence}%)
Last Visit: {last_visit}
Insurance: {insurance}
        
Welcome back! I found your information in our system."""
    
    else:
        return f"""Patient Lookup Results:
        
Patient: {name}
Status: New Patient
        
Welcome to MediCare Allergy & Wellness Center! I'll set up your patient profile."""

def validate_patient_data_integrity(patient_data: Dict[str, Any]) -> Tuple[bool, List[str]]:
    """
    Validate patient data for completeness and consistency.
    
    Args:
        patient_data: Patient information dictionary
        
    Returns:
        Tuple of (is_valid, list_of_issues)
    """
    issues = []
    
    # Check required fields
    required_fields = ["name", "dob", "phone"]
    for field in required_fields:
        if not patient_data.get(field):
            issues.append(f"Missing required field: {field}")
    
    # Validate date format
    dob = patient_data.get("dob", "")
    if dob:
        try:
            datetime.strptime(dob, "%m/%d/%Y")
        except ValueError:
            issues.append("Invalid date of birth format (expected MM/DD/YYYY)")
    
    # Validate phone format
    phone = patient_data.get("phone", "")
    if phone:
        phone_digits = re.sub(r'[^\d]', '', phone)
        if len(phone_digits) not in [10, 11]:
            issues.append("Invalid phone number format")
    
    # Validate email format
    email = patient_data.get("email", "")
    if email and not re.match(r'^[^@]+@[^@]+\.[^@]+$', email):
        issues.append("Invalid email format")
    
    return len(issues) == 0, issues

def get_patient_history_summary(patient_data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Generate a summary of patient's visit history and key information.
    
    Args:
        patient_data: Existing patient data from database
        
    Returns:
        Dictionary containing patient history summary
    """
    if not patient_data:
        return {"visit_count": 0, "summary": "No previous visits"}
    
    last_visit = patient_data.get("last_visit", "")
    insurance_carrier = patient_data.get("insurance_carrier", "")
    member_id = patient_data.get("member_id", "")
    
    # Calculate days since last visit
    days_since_visit = 0
    if last_visit:
        try:
            last_visit_date = datetime.strptime(last_visit, "%m/%d/%Y")
            days_since_visit = (datetime.now() - last_visit_date).days
        except ValueError:
            pass
    
    return {
        "last_visit": last_visit,
        "days_since_visit": days_since_visit,
        "insurance_carrier": insurance_carrier,
        "member_id": member_id,
        "has_insurance": bool(insurance_carrier),
        "visit_frequency": "regular" if days_since_visit < 365 else "infrequent" if days_since_visit < 730 else "rare"
    }

# ============================================================================
# TESTING AND DEVELOPMENT FUNCTIONS
# ============================================================================

def test_patient_lookup():
    """Test function to validate patient lookup functionality."""
    
    print("Testing Patient Lookup System")
    print("=" * 50)
    
    # Initialize test database manager
    db_manager = PatientDatabaseManager()
    
    # Test cases
    test_cases = [
        {"name": "John Smith", "dob": "01/15/1985", "phone": "(555) 123-4567"},
        {"name": "Jane Doe", "dob": "03/22/1990", "phone": "(555) 987-6543"},
        {"name": "Michael Johnson", "dob": "12/05/1978", "phone": "(555) 456-7890"},
        {"name": "New Patient", "dob": "06/10/1995", "phone": "(555) 000-0000"}
    ]
    
    for i, test_case in enumerate(test_cases, 1):
        print(f"\nTest Case {i}: {test_case['name']}")
        print(f"Input: {test_case}")
        
        # Create test state
        test_state = {
            "patient_info": test_case,
            "messages": []
        }
        
        # Perform lookup
        result = perform_patient_lookup(test_state)
        
        print(f"Patient Type: {result['patient_type']}")
        print(f"Confidence: {result.get('patient_lookup_confidence', 0)}%")
        
        if result.get('existing_patient_data'):
            existing = result['existing_patient_data']
            print(f"Existing Data: {existing.get('name', 'N/A')} - {existing.get('insurance_carrier', 'No insurance')}")

if __name__ == "__main__":
    # Run tests if script is executed directly
    test_patient_lookup()
