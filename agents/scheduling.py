"""
Smart Scheduling Agent - Medical Appointment Scheduling System
===========================================================

This module handles intelligent appointment scheduling including:
- Finding available time slots based on doctor schedules
- Smart duration assignment (30min returning vs 60min new patients)
- Slot optimization and business logic implementation
- Integration with Gemini API for natural language responses
- Calendar conflict resolution and availability management

Key Responsibilities:
- Read doctor schedules from Excel files
- Apply business rules for appointment durations
- Find optimal appointment slots based on patient preferences
- Handle slot selection and confirmation with Gemini AI
- Manage calendar updates and booking confirmations

Author: RagaAI Case Study Implementation
Date: September 2025
"""

import os
import pandas as pd
import logging
from typing import Dict, Any, List, Optional, Tuple
from datetime import datetime, timedelta, time
from dotenv import load_dotenv
from langchain_core.messages import HumanMessage, AIMessage
import random

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# ============================================================================
# DOCTOR SCHEDULE MANAGER CLASS
# ============================================================================

class DoctorScheduleManager:
    """
    Manages doctor schedules and appointment slot availability.
    """
    
    def __init__(self, schedule_path: str = None):
        """
        Initialize the doctor schedule manager.
        
        Args:
            schedule_path: Path to the doctor schedules Excel file
        """
        self.schedule_path = schedule_path or os.getenv("DOCTOR_SCHEDULE_PATH", "data/doctor_schedules.xlsx")
        self.schedules_df = None
        self._load_schedules()
    
    def _load_schedules(self):
        """Load doctor schedules from Excel file."""
        try:
            if os.path.exists(self.schedule_path):
                self.schedules_df = pd.read_excel(self.schedule_path)
                logger.info(f"Loaded {len(self.schedules_df)} schedule entries from {self.schedule_path}")
                
                # Ensure required columns exist
                required_columns = ['doctor_id', 'doctor_name', 'specialty', 'date', 
                                  'start_time', 'end_time', 'availability_status']
                missing_columns = [col for col in required_columns if col not in self.schedules_df.columns]
                
                if missing_columns:
                    logger.error(f"Missing required columns in schedule file: {missing_columns}")
                    self._create_empty_schedule()
                else:
                    # Convert date column to datetime
                    self.schedules_df['date'] = pd.to_datetime(self.schedules_df['date']).dt.strftime('%m/%d/%Y')
            else:
                logger.warning(f"Doctor schedules file not found at {self.schedule_path}")
                self._create_empty_schedule()
        except Exception as e:
            logger.error(f"Error loading doctor schedules: {str(e)}")
            self._create_empty_schedule()
    
    def _create_empty_schedule(self):
        """Create an empty schedule DataFrame with proper structure."""
        self.schedules_df = pd.DataFrame(columns=[
            'doctor_id', 'doctor_name', 'specialty', 'date', 
            'start_time', 'end_time', 'availability_status'
        ])
    
    def get_available_doctors(self) -> List[Dict[str, Any]]:
        """Get list of all available doctors with their specialties."""
        if self.schedules_df.empty:
            return []
        
        doctors = self.schedules_df.groupby(['doctor_id', 'doctor_name', 'specialty']).size().reset_index()
        doctors = doctors.drop(columns=[0])  # Remove the count column
        
        return doctors.to_dict('records')
    
    def find_available_slots(self, doctor_preference: str = None, 
                           duration_minutes: int = 60, 
                           preferred_date: str = None,
                           max_days_ahead: int = 14) -> List[Dict[str, Any]]:
        """
        Find available appointment slots based on criteria.
        
        Args:
            doctor_preference: Preferred doctor name or specialty
            duration_minutes: Required appointment duration (30 or 60 minutes)
            preferred_date: Preferred appointment date (MM/DD/YYYY)
            max_days_ahead: Maximum days to look ahead
            
        Returns:
            List of available appointment slots
        """
        if self.schedules_df.empty:
            logger.warning("No doctor schedules available")
            return []
        
        try:
            # Filter by availability status
            available_slots = self.schedules_df[
                self.schedules_df['availability_status'] == 'available'
            ].copy()
            
            if available_slots.empty:
                return []
            
            # Filter by doctor preference if provided
            if doctor_preference:
                doctor_filtered = self._filter_by_doctor_preference(available_slots, doctor_preference)
                if not doctor_filtered.empty:
                    available_slots = doctor_filtered
            
            # Filter by date preferences
            if preferred_date:
                date_filtered = available_slots[available_slots['date'] == preferred_date]
                if not date_filtered.empty:
                    available_slots = date_filtered
            else:
                # Filter to next 14 days by default
                available_slots = self._filter_by_date_range(available_slots, max_days_ahead)
            
            # Find slots that can accommodate the required duration
            suitable_slots = self._find_duration_compatible_slots(available_slots, duration_minutes)
            
            # Sort and optimize slot selection
            optimized_slots = self._optimize_slot_selection(suitable_slots, duration_minutes)
            
            return optimized_slots
            
        except Exception as e:
            logger.error(f"Error finding available slots: {str(e)}")
            return []
    
    def _filter_by_doctor_preference(self, df: pd.DataFrame, preference: str) -> pd.DataFrame:
        """Filter slots by doctor name or specialty preference."""
        preference_lower = preference.lower()
        
        # Try exact doctor name match first
        name_matches = df[df['doctor_name'].str.lower().str.contains(preference_lower, na=False)]
        if not name_matches.empty:
            return name_matches
        
        # Try specialty match
        specialty_matches = df[df['specialty'].str.lower().str.contains(preference_lower, na=False)]
        if not specialty_matches.empty:
            return specialty_matches
        
        # Return all if no specific match found
        return df
    
    def _filter_by_date_range(self, df: pd.DataFrame, max_days_ahead: int) -> pd.DataFrame:
        """Filter slots to within the specified date range."""
        try:
            today = datetime.now().date()
            max_date = today + timedelta(days=max_days_ahead)
            
            # Convert date strings to datetime objects for comparison
            df_copy = df.copy()
            df_copy['date_obj'] = pd.to_datetime(df_copy['date'], format='%m/%d/%Y').dt.date
            
            # Filter by date range
            date_filtered = df_copy[
                (df_copy['date_obj'] >= today) & 
                (df_copy['date_obj'] <= max_date)
            ]
            
            # Remove the temporary date_obj column
            date_filtered = date_filtered.drop(columns=['date_obj'])
            
            return date_filtered
            
        except Exception as e:
            logger.error(f"Error filtering by date range: {str(e)}")
            return df
    
    def _find_duration_compatible_slots(self, df: pd.DataFrame, duration_minutes: int) -> List[Dict[str, Any]]:
        """Find slots that can accommodate the required duration."""
        suitable_slots = []
        
        try:
            # Group by doctor and date to find consecutive slots
            grouped = df.groupby(['doctor_id', 'doctor_name', 'date'])
            
            for (doctor_id, doctor_name, date), group in grouped:
                # Sort by start time
                group_sorted = group.sort_values('start_time')
                
                # Convert time strings to datetime objects for calculation
                for i in range(len(group_sorted)):
                    row = group_sorted.iloc[i]
                    start_time = self._parse_time(row['start_time'])
                    end_time = self._parse_time(row['end_time'])
                    
                    if start_time and end_time:
                        # Calculate slot duration
                        slot_duration = (datetime.combine(datetime.today(), end_time) - 
                                        datetime.combine(datetime.today(), start_time)).total_seconds() / 60
                        
                        # Check if this slot or consecutive slots can accommodate the duration
                        if slot_duration >= duration_minutes:
                            suitable_slots.append({
                                'doctor_id': doctor_id,
                                'doctor_name': doctor_name,
                                'specialty': row['specialty'],
                                'date': date,
                                'start_time': row['start_time'],
                                'end_time': row['end_time'],
                                'duration': int(slot_duration),
                                'required_duration': duration_minutes,
                                'slot_type': 'single'
                            })
                        elif duration_minutes > 30:
                            # Check for consecutive slots for longer appointments
                            consecutive_slot = self._find_consecutive_slot(group_sorted, i, duration_minutes) #<-- FIX IS HERE
                            if consecutive_slot:
                                suitable_slots.append(consecutive_slot)
            
            return suitable_slots
            
        except Exception as e:
            logger.error(f"Error finding duration-compatible slots: {str(e)}")
            return []
    
    def _find_consecutive_slot(self, group_df: pd.DataFrame, current_idx: int, duration_minutes: int) -> Optional[Dict[str, Any]]:
        """Find consecutive slots that can accommodate the required duration."""
        try:
            current_row = group_df.iloc[current_idx]
            current_end = self._parse_time(current_row['end_time'])
            
            total_duration = self._get_slot_duration(current_row)
            combined_end_time = current_row['end_time']
            
            # Check next slots
            for next_idx in range(current_idx + 1, len(group_df)):
                next_row = group_df.iloc[next_idx]
                next_start = self._parse_time(next_row['start_time'])
                next_end = self._parse_time(next_row['end_time'])
                
                # Check if slots are consecutive (no gap)
                if current_end == next_start:
                    total_duration += self._get_slot_duration(next_row)
                    combined_end_time = next_row['end_time']
                    current_end = next_end
                    
                    if total_duration >= duration_minutes:
                        return {
                            'doctor_id': current_row['doctor_id'],
                            'doctor_name': current_row['doctor_name'],
                            'specialty': current_row['specialty'],
                            'date': current_row['date'],
                            'start_time': current_row['start_time'],
                            'end_time': combined_end_time,
                            'duration': int(total_duration),
                            'required_duration': duration_minutes,
                            'slot_type': 'consecutive'
                        }
                else:
                    break  # No consecutive slot found
            
            return None
            
        except Exception as e:
            logger.error(f"Error finding consecutive slots: {str(e)}")
            return None
    
    def _parse_time(self, time_str: str) -> Optional[time]:
        """Parse time string to time object."""
        try:
            # Handle different time formats
            formats = ['%H:%M', '%I:%M %p', '%H:%M:%S']
            
            for fmt in formats:
                try:
                    return datetime.strptime(str(time_str).strip(), fmt).time()
                except ValueError:
                    continue
            
            return None
            
        except Exception as e:
            logger.error(f"Error parsing time {time_str}: {str(e)}")
            return None
    
    def _get_slot_duration(self, row: pd.Series) -> float:
        """Calculate duration of a slot in minutes."""
        try:
            start_time = self._parse_time(row['start_time'])
            end_time = self._parse_time(row['end_time'])
            
            if start_time and end_time:
                duration = (datetime.combine(datetime.today(), end_time) - 
                           datetime.combine(datetime.today(), start_time)).total_seconds() / 60
                return duration
            
            return 30.0  # Default 30-minute slot
            
        except Exception as e:
            logger.error(f"Error calculating slot duration: {str(e)}")
            return 30.0
    
    def _optimize_slot_selection(self, slots: List[Dict[str, Any]], duration_minutes: int) -> List[Dict[str, Any]]:
        """
        Optimize slot selection based on business rules.
        
        Business Rules:
        1. Prefer morning slots for new patients (60min)
        2. Prefer exact duration matches over longer slots
        3. Prefer single slots over consecutive slots
        4. Sort by date and time
        """
        try:
            if not slots:
                return []
            
            # Apply business rules scoring
            for slot in slots:
                score = 0
                
                # Parse start time for scoring
                start_time = self._parse_time(slot['start_time'])
                if start_time:
                    # Morning preference for new patients (60min appointments)
                    if duration_minutes == 60 and start_time.hour < 12:
                        score += 20
                    
                    # Prefer earlier times generally
                    score += (24 - start_time.hour)
                
                # Prefer exact duration matches
                if slot['duration'] == duration_minutes:
                    score += 15
                elif slot['duration'] < duration_minutes + 30:
                    score += 10
                
                # Prefer single slots over consecutive
                if slot['slot_type'] == 'single':
                    score += 10
                
                # Add random factor to prevent always selecting the same slots
                score += random.uniform(0, 5)
                
                slot['optimization_score'] = score
            
            # Sort by score (highest first), then by date and time
            sorted_slots = sorted(slots, key=lambda x: (
                -x['optimization_score'],
                datetime.strptime(x['date'], '%m/%d/%Y'),
                self._parse_time(x['start_time']) or time.min
            ))
            
            # Return top 10 options
            return sorted_slots[:10]
            
        except Exception as e:
            logger.error(f"Error optimizing slot selection: {str(e)}")
            return slots
    
    def reserve_slot(self, slot: Dict[str, Any], patient_info: Dict[str, Any]) -> Dict[str, Any]:
        """
        Reserve a specific time slot for a patient.
        
        Args:
            slot: Selected appointment slot
            patient_info: Patient information
            
        Returns:
            Reservation confirmation details
        """
        try:
            # In a real system, this would update the database
            # For this demo, we'll simulate the reservation
            
            reservation_id = f"RES-{datetime.now().strftime('%Y%m%d%H%M%S')}"
            
            reservation_details = {
                'reservation_id': reservation_id,
                'status': 'reserved',
                'patient_name': patient_info.get('name', ''),
                'doctor_name': slot['doctor_name'],
                'date': slot['date'],
                'start_time': slot['start_time'],
                'end_time': slot['end_time'],
                'duration': slot['required_duration'],
                'reserved_at': datetime.now().isoformat()
            }
            
            logger.info(f"Slot reserved successfully: {reservation_id}")
            return reservation_details
            
        except Exception as e:
            logger.error(f"Error reserving slot: {str(e)}")
            return {'status': 'error', 'message': str(e)}

# ============================================================================
# MAIN SCHEDULING FUNCTIONS FOR LANGGRAPH INTEGRATION
# ============================================================================

def find_available_appointment_slots(state: Dict[str, Any]) -> Dict[str, Any]:
    """
    Find available appointment slots based on patient information and preferences.
    
    This function is called by the LangGraph core agent to search for
    available appointment slots.
    
    Args:
        state: Current appointment state
        
    Returns:
        Updated state with available slots
    """
    logger.info("Finding available appointment slots")
    
    try:
        # Extract scheduling requirements from state
        patient_info = state.get("patient_info", {})
        appointment_duration = state.get("appointment_duration", 60)
        doctor_preference = patient_info.get("doctor_preference", "")
        location_preference = patient_info.get("location_preference", "")
        
        # Initialize schedule manager
        schedule_manager = DoctorScheduleManager()
        
        # Find available slots
        available_slots = schedule_manager.find_available_slots(
            doctor_preference=doctor_preference,
            duration_minutes=appointment_duration,
            max_days_ahead=14
        )
        
        if available_slots:
            logger.info(f"Found {len(available_slots)} available appointment slots")
            
            updated_state = {
                **state,
                "available_slots": available_slots,
                "slot_search_status": "success"
            }
        else:
            logger.warning("No available slots found matching criteria")
            
            updated_state = {
                **state,
                "available_slots": [],
                "slot_search_status": "no_slots",
                "error_message": "No available appointment slots found matching your preferences. Please try different criteria or dates."
            }
        
        return updated_state
        
    except Exception as e:
        logger.error(f"Error finding appointment slots: {str(e)}")
        return {
            **state,
            "available_slots": [],
            "slot_search_status": "error",
            "error_message": f"Error searching for appointment slots: {str(e)}"
        }

def present_appointment_options(state: Dict[str, Any], llm) -> Dict[str, Any]:
    """
    Present available appointment options to the patient using Gemini AI.
    
    Args:
        state: Current appointment state with available slots
        llm: Gemini LLM instance for generating responses
        
    Returns:
        Updated state with formatted slot presentation
    """
    logger.info("Presenting appointment options with Gemini")
    
    try:
        available_slots = state.get("available_slots", [])
        patient_name = state.get("patient_info", {}).get("name", "")
        appointment_duration = state.get("appointment_duration", 60)
        
        if not available_slots:
            no_slots_message = f"""I apologize, {patient_name}, but I couldn't find any available appointment slots that match your preferences. 

This could be due to:
- High demand for your preferred doctor
- Limited availability for {appointment_duration}-minute appointments
- Booking timeframe restrictions

Would you like me to:
1. Check with a different doctor
2. Look at dates further in the future
3. Consider alternative appointment times

I'm here to help find the best option for you!"""
            
            return {
                **state,
                "messages": state["messages"] + [AIMessage(content=no_slots_message)]
            }
        
        # Prepare slot information for Gemini
        slots_info = ""
        for i, slot in enumerate(available_slots[:5], 1):  # Show top 5 slots
            date_formatted = datetime.strptime(slot['date'], '%m/%d/%Y').strftime('%A, %B %d, %Y')
            time_formatted = slot['start_time']
            doctor = slot['doctor_name']
            specialty = slot['specialty']
            
            slots_info += f"{i}. {date_formatted} at {time_formatted}\n"
            slots_info += f"   With {doctor} ({specialty})\n"
            slots_info += f"   Duration: {appointment_duration} minutes\n\n"
        
        # Create prompt for Gemini
        presentation_prompt = f"""
        Present these available appointment slots to {patient_name} in a professional, friendly manner:

        {slots_info}

        Guidelines:
        1. Welcome them and acknowledge their appointment request
        2. Present the options clearly with numbers
        3. Ask them to choose by number or ask for alternatives
        4. Mention they can request different times if needed
        5. Keep tone professional but warm
        6. Be concise but informative

        Patient context: {appointment_duration}-minute appointment ({state.get('patient_type', 'new')} patient)
        """
        
        response = llm.invoke([HumanMessage(content=presentation_prompt)])
        
        return {
            **state,
            "messages": state["messages"] + [AIMessage(content=response.content)]
        }
        
    except Exception as e:
        logger.error(f"Error presenting appointment options: {str(e)}")
        
        fallback_message = """I found some appointment options for you, but I'm having trouble presenting them clearly right now. 

Let me connect you with our scheduling team who can provide you with available times and help you book the perfect appointment slot."""
        
        return {
            **state,
            "messages": state["messages"] + [AIMessage(content=fallback_message)],
            "error_message": f"Error presenting slots: {str(e)}"
        }

def confirm_slot_selection_with_gemini(state: Dict[str, Any], llm) -> Dict[str, Any]:
    """
    Handle patient's slot selection and confirmation using Gemini.
    
    Args:
        state: Current appointment state
        llm: Gemini LLM instance for processing selection
        
    Returns:
        Updated state with selected slot confirmation
    """
    logger.info("Processing slot selection with Gemini")
    
    try:
        # Get the latest user message
        user_messages = [msg for msg in state.get("messages", []) if hasattr(msg, 'type') and msg.type == 'human']
        if not user_messages:
            return {
                **state,
                "error_message": "No user selection received"
            }
        
        latest_user_input = user_messages[-1].content
        available_slots = state.get("available_slots", [])
        
        if not available_slots:
            return {
                **state,
                "error_message": "No available slots to select from"
            }
        
        # Parse user selection using Gemini
        selection_prompt = f"""
        The user said: "{latest_user_input}"
        
        Available appointment slots:
        {chr(10).join([f"{i+1}. {slot['date']} at {slot['start_time']} with {slot['doctor_name']}" 
                      for i, slot in enumerate(available_slots[:5])])}
        
        Tasks:
        1. Determine which slot number (1-5) the user selected, if any
        2. If no clear selection, ask for clarification
        3. Respond with just the number (1-5) if selection is clear, or "unclear" if not
        
        Response format: Just the number or "unclear"
        """
        
        selection_response = llm.invoke([HumanMessage(content=selection_prompt)])
        selection_text = selection_response.content.strip().lower()
        
        # Process the selection
        selected_slot_index = None
        
        # Try to extract number from response
        for i in range(1, 6):
            if str(i) in selection_text:
                selected_slot_index = i - 1  # Convert to 0-based index
                break
        
        if selected_slot_index is not None and selected_slot_index < len(available_slots):
            # Valid selection made
            selected_slot = available_slots[selected_slot_index]
            
            # Reserve the slot
            schedule_manager = DoctorScheduleManager()
            reservation = schedule_manager.reserve_slot(selected_slot, state.get("patient_info", {}))
            
            if reservation.get('status') == 'reserved':
                # Create confirmation message using Gemini
                confirmation_prompt = f"""
                Create a professional appointment confirmation message for:
                
                Patient: {state.get('patient_info', {}).get('name', 'Patient')}
                Doctor: {selected_slot['doctor_name']} ({selected_slot['specialty']})
                Date: {selected_slot['date']}
                Time: {selected_slot['start_time']}
                Duration: {selected_slot['required_duration']} minutes
                
                Include:
                1. Confirmation of the appointment booking
                2. All appointment details
                3. What happens next (insurance info collection)
                4. Professional, reassuring tone
                
                Keep it concise and clear.
                """
                
                confirmation_response = llm.invoke([HumanMessage(content=confirmation_prompt)])
                
                return {
                    **state,
                    "selected_slot": selected_slot,
                    "reservation_details": reservation,
                    "current_step": "insurance_collection",
                    "messages": state["messages"] + [AIMessage(content=confirmation_response.content)]
                }
            else:
                return {
                    **state,
                    "error_message": "Failed to reserve the selected slot. Please try again.",
                    "messages": state["messages"] + [AIMessage(content="I apologize, but there was an issue reserving that time slot. Let me show you the available options again.")]
                }
        
        else:
            # Unclear selection - ask for clarification using Gemini
            clarification_prompt = f"""
            The user said: "{latest_user_input}"
            
            Create a polite clarification request asking them to choose a specific appointment slot by number (1-5) from the options previously shown.
            
            Be helpful and understanding, acknowledging their input but asking for a clear number selection.
            Keep it brief and friendly.
            """
            
            clarification_response = llm.invoke([HumanMessage(content=clarification_prompt)])
            
            return {
                **state,
                "messages": state["messages"] + [AIMessage(content=clarification_response.content)]
            }
        
    except Exception as e:
        logger.error(f"Error in slot selection confirmation: {str(e)}")
        
        return {
            **state,
            "error_message": f"Error processing slot selection: {str(e)}",
            "messages": state["messages"] + [AIMessage(content="I'm having trouble processing your selection. Could you please tell me which appointment slot you'd prefer by number (1, 2, 3, etc.)?")]
        }

# ============================================================================
# UTILITY FUNCTIONS
# ============================================================================

def format_appointment_summary(selected_slot: Dict[str, Any], patient_info: Dict[str, Any]) -> str:
    """
    Format a comprehensive appointment summary.
    
    Args:
        selected_slot: The selected appointment slot
        patient_info: Patient information
        
    Returns:
        Formatted appointment summary string
    """
    try:
        date_formatted = datetime.strptime(selected_slot['date'], '%m/%d/%Y').strftime('%A, %B %d, %Y')
        
        summary = f"""
📅 **APPOINTMENT CONFIRMATION**

**Patient**: {patient_info.get('name', 'N/A')}
**Doctor**: {selected_slot['doctor_name']} ({selected_slot['specialty']})
**Date**: {date_formatted}
**Time**: {selected_slot['start_time']} - {selected_slot['end_time']}
**Duration**: {selected_slot['required_duration']} minutes
**Type**: {'New Patient Consultation' if selected_slot['required_duration'] == 60 else 'Follow-up Visit'}

**Next Steps**:
1. Insurance information collection
2. Email confirmation and intake forms
3. Appointment reminders via email and SMS

**Location**: MediCare Allergy & Wellness Center
456 Healthcare Boulevard, Suite 300
Phone: (555) 123-4567
        """
        
        return summary.strip()
        
    except Exception as e:
        logger.error(f"Error formatting appointment summary: {str(e)}")
        return f"Appointment scheduled with {selected_slot.get('doctor_name', 'Doctor')} on {selected_slot.get('date', 'TBD')}"

def validate_slot_availability(slot: Dict[str, Any]) -> Tuple[bool, str]:
    """
    Validate if a slot is still available for booking.
    
    Args:
        slot: Appointment slot to validate
        
    Returns:
        Tuple of (is_available, status_message)
    """
    try:
        # In a real system, this would check the current database status
        # For this demo, we'll simulate availability checking
        
        appointment_date = datetime.strptime(slot['date'], '%m/%d/%Y').date()
        today = datetime.now().date()
        
        # Check if appointment is in the past
        if appointment_date < today:
            return False, "Selected appointment date has passed"
        
        # Check if appointment is too far in the future (more than 90 days)
        if appointment_date > today + timedelta(days=90):
            return False, "Appointment date is too far in the future"
        
        # Simulate random availability (95% chance of being available)
        if random.random() < 0.95:
            return True, "Slot is available"
        else:
            return False, "Slot was recently booked by another patient"
            
    except Exception as e:
        logger.error(f"Error validating slot availability: {str(e)}")
        return False, f"Error checking availability: {str(e)}"

def get_alternative_slots(original_slot: Dict[str, Any], schedule_manager: DoctorScheduleManager) -> List[Dict[str, Any]]:
    """
    Find alternative slots if the original selection is unavailable.
    
    Args:
        original_slot: The originally requested slot
        schedule_manager: DoctorScheduleManager instance
        
    Returns:
        List of alternative appointment slots
    """
    try:
        # Find similar slots with same doctor or specialty
        alternatives = schedule_manager.find_available_slots(
            doctor_preference=original_slot['doctor_name'],
            duration_minutes=original_slot['required_duration'],
            max_days_ahead=21
        )
        
        # Remove the original slot from alternatives
        alternatives = [slot for slot in alternatives 
                       if not (slot['date'] == original_slot['date'] and 
                              slot['start_time'] == original_slot['start_time'])]
        
        return alternatives[:3]  # Return top 3 alternatives
        
    except Exception as e:
        logger.error(f"Error finding alternative slots: {str(e)}")
        return []

# ============================================================================
# TESTING FUNCTIONS
# ============================================================================

def test_scheduling_system():
    """Test function to validate scheduling system functionality."""
    
    print("Testing Medical Appointment Scheduling System")
    print("=" * 60)
    
    # Initialize schedule manager
    schedule_manager = DoctorScheduleManager()
    
    # Test 1: Get available doctors
    print("\n1. Testing Available Doctors:")
    doctors = schedule_manager.get_available_doctors()
    print(f"Found {len(doctors)} doctors")
    for doctor in doctors[:3]:
        print(f"  - {doctor.get('doctor_name', 'Unknown')} ({doctor.get('specialty', 'General')})")
    
    # Test 2: Find slots for new patient (60 minutes)
    print("\n2. Testing New Patient Slot Search (60 minutes):")
    new_patient_slots = schedule_manager.find_available_slots(
        doctor_preference="Dr. Johnson",
        duration_minutes=60,
        max_days_ahead=7
    )
    print(f"Found {len(new_patient_slots)} available 60-minute slots")
    for slot in new_patient_slots[:3]:
        print(f"  - {slot['date']} at {slot['start_time']} with {slot['doctor_name']}")
    
    # Test 3: Find slots for returning patient (30 minutes)
    print("\n3. Testing Returning Patient Slot Search (30 minutes):")
    returning_patient_slots = schedule_manager.find_available_slots(
        duration_minutes=30,
        max_days_ahead=14
    )
    print(f"Found {len(returning_patient_slots)} available 30-minute slots")
    for slot in returning_patient_slots[:3]:
        print(f"  - {slot['date']} at {slot['start_time']} with {slot['doctor_name']}")
    
    # Test 4: Test slot reservation
    print("\n4. Testing Slot Reservation:")
    if new_patient_slots:
        test_patient = {
            "name": "John Test Patient",
            "phone": "(555) 123-4567",
            "email": "john@test.com"
        }
        
        reservation = schedule_manager.reserve_slot(new_patient_slots[0], test_patient)
        print(f"Reservation Status: {reservation.get('status', 'Unknown')}")
        print(f"Reservation ID: {reservation.get('reservation_id', 'N/A')}")
    
    print("\n" + "=" * 60)
    print("Scheduling system test completed!")

if __name__ == "__main__":
    # Run tests if script is executed directly
    test_scheduling_system()
