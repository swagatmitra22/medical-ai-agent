"""
Sample Data Generator - Medical Appointment Scheduling System
==========================================================

This module generates synthetic medical data for testing and demonstration
of the appointment scheduling system including:
- 50 patient records (CSV format)
- Doctor schedules with availability slots (Excel format)
- Realistic medical data patterns and demographics

Key Features:
- HIPAA-compliant synthetic data (no real patient information)
- Diverse demographic representation
- Realistic medical conditions and insurance patterns
- Multiple doctor specialties and schedules
- Configurable appointment availability patterns

Author: RagaAI Case Study Implementation  
Date: September 2025
"""

import pandas as pd
import random
import os
from datetime import datetime, timedelta, time
from typing import List, Dict, Any
import string
import json

# Configure random seed for reproducible results
random.seed(42)

# ============================================================================
# DATA CONSTANTS AND CONFIGURATIONS
# ============================================================================

# Patient Demographics Data
FIRST_NAMES_MALE = [
    "James", "Robert", "John", "Michael", "David", "William", "Richard", "Charles",
    "Joseph", "Thomas", "Christopher", "Daniel", "Paul", "Mark", "Donald", "Steven",
    "Andrew", "Joshua", "Kenneth", "Kevin", "Brian", "George", "Timothy", "Ronald"
]

FIRST_NAMES_FEMALE = [
    "Mary", "Patricia", "Jennifer", "Linda", "Elizabeth", "Barbara", "Susan", "Jessica",
    "Sarah", "Karen", "Lisa", "Nancy", "Betty", "Helen", "Sandra", "Donna",
    "Carol", "Ruth", "Sharon", "Michelle", "Laura", "Sarah", "Kimberly", "Deborah"
]

LAST_NAMES = [
    "Smith", "Johnson", "Williams", "Brown", "Jones", "Garcia", "Miller", "Davis",
    "Rodriguez", "Martinez", "Hernandez", "Lopez", "Gonzalez", "Wilson", "Anderson",
    "Thomas", "Taylor", "Moore", "Jackson", "Martin", "Lee", "Perez", "Thompson",
    "White", "Harris", "Sanchez", "Clark", "Ramirez", "Lewis", "Robinson", "Walker",
    "Young", "Allen", "King", "Wright", "Scott", "Torres", "Nguyen", "Hill", "Flores",
    "Green", "Adams", "Nelson", "Baker", "Hall", "Rivera", "Campbell", "Mitchell"
]

# Insurance Providers
INSURANCE_PROVIDERS = [
    "BlueCross BlueShield",
    "UnitedHealthcare", 
    "Aetna",
    "Cigna",
    "Humana",
    "Kaiser Permanente",
    "Anthem",
    "Molina Healthcare",
    "Centene Corporation",
    "WellCare"
]

# Medical Conditions (for returning patients)
MEDICAL_CONDITIONS = [
    "Hypertension", "Diabetes Type 2", "High Cholesterol", "Asthma", "Allergies",
    "Arthritis", "Depression", "Anxiety", "GERD", "Migraine", "Chronic Pain",
    "Sleep Apnea", "Osteoporosis", "Thyroid Disorders", "Heart Disease"
]

# Doctor Information
DOCTORS_DATA = [
    {
        "doctor_id": "D001",
        "name": "Dr. Johnson",
        "specialty": "Family Medicine",
        "years_experience": 12,
        "location": "Main Campus"
    },
    {
        "doctor_id": "D002", 
        "name": "Dr. Smith",
        "specialty": "Cardiology",
        "years_experience": 15,
        "location": "Heart Center"
    },
    {
        "doctor_id": "D003",
        "name": "Dr. Williams", 
        "specialty": "Dermatology",
        "years_experience": 8,
        "location": "Skin Care Center"
    },
    {
        "doctor_id": "D004",
        "name": "Dr. Brown",
        "specialty": "Orthopedics", 
        "years_experience": 18,
        "location": "Orthopedic Center"
    },
    {
        "doctor_id": "D005",
        "name": "Dr. Davis",
        "specialty": "Internal Medicine",
        "years_experience": 10,
        "location": "Main Campus"
    }
]

# Address Components
STREET_NAMES = [
    "Main St", "Oak Ave", "Pine Dr", "Maple Ln", "Cedar Rd", "Elm St", "Park Ave",
    "Washington St", "Lincoln Ave", "Jefferson Dr", "Madison Ln", "Adams Rd"
]

CITIES = [
    "Springfield", "Franklin", "Clinton", "Georgetown", "Madison", "Salem",
    "Fairview", "Riverside", "Mount Pleasant", "Oak Grove", "Hillcrest", "Lakewood"
]

STATES = ["TX", "CA", "FL", "NY", "PA", "IL", "OH", "GA", "NC", "MI"]

# ============================================================================
# PATIENT DATA GENERATION
# ============================================================================

def generate_patient_data(num_patients: int = 50) -> pd.DataFrame:
    """
    Generate synthetic patient data with realistic medical patterns.
    
    Args:
        num_patients: Number of patient records to generate
        
    Returns:
        DataFrame containing patient records
    """
    print(f"Generating {num_patients} synthetic patient records...")
    
    patients = []
    
    for i in range(num_patients):
        # Basic demographics
        gender = random.choice(["Male", "Female", "Other"])
        if gender == "Male":
            first_name = random.choice(FIRST_NAMES_MALE)
        else:
            first_name = random.choice(FIRST_NAMES_FEMALE)
        
        last_name = random.choice(LAST_NAMES)
        
        # Generate age-appropriate birth date (18-85 years old)
        age = random.randint(18, 85)
        birth_date = datetime.now() - timedelta(days=age * 365 + random.randint(0, 365))
        
        # Patient type distribution (70% returning, 30% new for realistic clinic)
        patient_type = "returning" if random.random() < 0.7 else "new"
        
        # Generate last visit for returning patients
        last_visit = ""
        if patient_type == "returning":
            days_ago = random.randint(30, 730)  # 1 month to 2 years ago
            last_visit_date = datetime.now() - timedelta(days=days_ago)
            last_visit = last_visit_date.strftime("%m/%d/%Y")
        
        # Insurance information
        insurance_carrier = random.choice(INSURANCE_PROVIDERS)
        member_id = generate_member_id()
        group_number = f"GRP{random.randint(1000, 9999)}"
        
        # Contact information  
        phone = generate_phone_number()
        email = f"{first_name.lower()}.{last_name.lower()}{random.randint(1, 999)}@email.com"
        
        # Address
        address = generate_address()
        
        # Emergency contact
        emergency_contact = generate_emergency_contact()
        
        # Medical history for returning patients
        medical_history = ""
        if patient_type == "returning" and random.random() < 0.6:  # 60% have medical conditions
            conditions = random.sample(MEDICAL_CONDITIONS, random.randint(1, 3))
            medical_history = "; ".join(conditions)
        
        # Create patient record
        patient = {
            "patient_id": f"P{i+1:04d}",
            "name": f"{first_name} {last_name}",
            "dob": birth_date.strftime("%m/%d/%Y"),
            "gender": gender,
            "age": age,
            "phone": phone,
            "email": email,
            "address": address,
            "city": random.choice(CITIES),
            "state": random.choice(STATES),
            "zip_code": f"{random.randint(10000, 99999)}",
            "patient_type": patient_type,
            "last_visit": last_visit,
            "insurance_carrier": insurance_carrier,
            "member_id": member_id,
            "group_number": group_number,
            "emergency_contact": emergency_contact,
            "medical_history": medical_history,
            "preferred_doctor": random.choice(DOCTORS_DATA)["name"] if random.random() < 0.4 else "",
            "preferred_language": "English" if random.random() < 0.85 else random.choice(["Spanish", "French", "German"]),
            "registration_date": (datetime.now() - timedelta(days=random.randint(30, 1095))).strftime("%m/%d/%Y"),
            "notes": generate_patient_notes(patient_type)
        }
        
        patients.append(patient)
    
    df = pd.DataFrame(patients)
    print(f"✅ Generated {len(df)} patient records successfully")
    return df

def generate_member_id() -> str:
    """Generate realistic insurance member ID."""
    return f"{''.join(random.choices(string.ascii_uppercase, k=2))}{random.randint(100000000, 999999999)}"

def generate_phone_number() -> str:
    """Generate realistic US phone number."""
    area_code = random.randint(200, 999)
    exchange = random.randint(200, 999)  
    number = random.randint(1000, 9999)
    return f"({area_code}) {exchange}-{number}"

def generate_address() -> str:
    """Generate realistic street address."""
    number = random.randint(100, 9999)
    street = random.choice(STREET_NAMES)
    return f"{number} {street}"

def generate_emergency_contact() -> str:
    """Generate emergency contact information."""
    relationships = ["Spouse", "Parent", "Child", "Sibling", "Friend", "Partner"]
    relationship = random.choice(relationships)
    name = f"{random.choice(FIRST_NAMES_MALE + FIRST_NAMES_FEMALE)} {random.choice(LAST_NAMES)}"
    phone = generate_phone_number()
    return f"{name} ({relationship}) - {phone}"

def generate_patient_notes(patient_type: str) -> str:
    """Generate realistic patient notes."""
    if patient_type == "new":
        notes = [
            "New patient registration complete",
            "Referred by primary care physician", 
            "Self-referral for consultation",
            "Insurance verification pending"
        ]
    else:
        notes = [
            "Regular follow-up patient",
            "Medication compliance good",
            "Responds well to treatment", 
            "Monitor condition closely",
            "Patient very cooperative"
        ]
    
    return random.choice(notes) if random.random() < 0.3 else ""

# ============================================================================
# DOCTOR SCHEDULE GENERATION  
# ============================================================================

def generate_doctor_schedules(num_days: int = 21) -> pd.DataFrame:
    """
    Generate doctor schedules with realistic availability patterns.
    
    Args:
        num_days: Number of days to generate schedules for
        
    Returns:
        DataFrame containing doctor schedule data
    """
    print(f"Generating doctor schedules for {num_days} days...")
    
    schedules = []
    
    # Generate schedules for each doctor
    for doctor in DOCTORS_DATA:
        doctor_schedules = generate_single_doctor_schedule(doctor, num_days)
        schedules.extend(doctor_schedules)
    
    df = pd.DataFrame(schedules)
    print(f"✅ Generated {len(df)} schedule slots successfully")
    return df

def generate_single_doctor_schedule(doctor: Dict[str, Any], num_days: int) -> List[Dict[str, Any]]:
    """Generate schedule for a single doctor."""
    doctor_schedule = []
    
    for day_offset in range(num_days):
        current_date = datetime.now().date() + timedelta(days=day_offset)
        
        # Skip weekends for most doctors (90% probability)
        if current_date.weekday() >= 5 and random.random() < 0.9:
            continue
        
        # Generate daily schedule based on doctor specialty
        daily_slots = generate_daily_schedule(doctor, current_date)
        doctor_schedule.extend(daily_slots)
    
    return doctor_schedule

def generate_daily_schedule(doctor: Dict[str, Any], date) -> List[Dict[str, Any]]:
    """Generate daily schedule slots for a doctor."""
    daily_schedule = []
    
    # Determine working hours based on specialty
    if doctor["specialty"] == "Family Medicine":
        start_hour, end_hour = 8, 17  # 8 AM to 5 PM
    elif doctor["specialty"] == "Cardiology":
        start_hour, end_hour = 9, 16  # 9 AM to 4 PM  
    elif doctor["specialty"] == "Dermatology":
        start_hour, end_hour = 10, 18  # 10 AM to 6 PM
    else:
        start_hour, end_hour = 9, 17  # 9 AM to 5 PM
    
    # Generate 30-minute time slots
    current_time = time(start_hour, 0)
    end_time = time(end_hour, 0)
    
    while current_time < end_time:
        # Calculate next slot time
        next_time = (datetime.combine(date, current_time) + timedelta(minutes=30)).time()
        
        # Determine availability status
        # 70% available, 20% booked, 10% blocked
        rand = random.random()
        if rand < 0.70:
            status = "available"
        elif rand < 0.90:
            status = "booked" 
        else:
            status = "blocked"  # lunch, meetings, etc.
        
        # Lunch break (12:00-13:00) is typically blocked
        if current_time.hour == 12:
            status = "blocked"
        
        # Create schedule slot
        slot = {
            "doctor_id": doctor["doctor_id"],
            "doctor_name": doctor["name"],
            "specialty": doctor["specialty"],
            "location": doctor["location"],
            "date": date.strftime("%m/%d/%Y"),
            "day_of_week": date.strftime("%A"),
            "start_time": current_time.strftime("%H:%M"),
            "end_time": next_time.strftime("%H:%M"),
            "duration_minutes": 30,
            "availability_status": status,
            "notes": generate_schedule_notes(status)
        }
        
        daily_schedule.append(slot)
        current_time = next_time
    
    return daily_schedule

def generate_schedule_notes(status: str) -> str:
    """Generate notes for schedule slots."""
    if status == "booked":
        return random.choice(["Patient appointment", "Follow-up visit", "New patient consultation"])
    elif status == "blocked":
        return random.choice(["Lunch break", "Administrative time", "Meeting", "Surgery"])
    else:
        return ""

# ============================================================================
# APPOINTMENT HISTORY GENERATION
# ============================================================================

def generate_appointment_history(num_appointments: int = 100) -> pd.DataFrame:
    """Generate historical appointment data for analytics."""
    print(f"Generating {num_appointments} historical appointments...")
    
    appointments = []
    
    for i in range(num_appointments):
        # Random date in the past 6 months
        days_ago = random.randint(1, 180)
        appointment_date = datetime.now() - timedelta(days=days_ago)
        
        # Random time during business hours
        hour = random.randint(8, 17)
        minute = random.choice([0, 30])
        appointment_time = time(hour, minute)
        
        # Random doctor and patient
        doctor = random.choice(DOCTORS_DATA)
        
        # Patient type distribution
        patient_type = "returning" if random.random() < 0.75 else "new"
        duration = 30 if patient_type == "returning" else 60
        
        # Appointment status
        status_choices = ["completed", "no-show", "cancelled", "rescheduled"]
        status_weights = [0.80, 0.10, 0.07, 0.03]  # Realistic distribution
        status = random.choices(status_choices, weights=status_weights)[0]
        
        appointment = {
            "appointment_id": f"APPT-{appointment_date.strftime('%Y%m%d')}-{i+1:03d}",
            "patient_name": f"{random.choice(FIRST_NAMES_MALE + FIRST_NAMES_FEMALE)} {random.choice(LAST_NAMES)}",
            "doctor_id": doctor["doctor_id"],
            "doctor_name": doctor["name"],
            "specialty": doctor["specialty"],
            "appointment_date": appointment_date.strftime("%m/%d/%Y"),
            "appointment_time": appointment_time.strftime("%H:%M"),
            "duration_minutes": duration,
            "patient_type": patient_type,
            "status": status,
            "insurance_carrier": random.choice(INSURANCE_PROVIDERS),
            "copay_amount": random.choice([0, 15, 25, 30, 50]) if status == "completed" else 0,
            "revenue": random.randint(150, 400) if status == "completed" else 0,
            "created_date": (appointment_date - timedelta(days=random.randint(1, 30))).strftime("%m/%d/%Y"),
            "notes": generate_appointment_notes(status)
        }
        
        appointments.append(appointment)
    
    df = pd.DataFrame(appointments)
    print(f"✅ Generated {len(df)} appointment records successfully")
    return df

def generate_appointment_notes(status: str) -> str:
    """Generate notes for appointments based on status."""
    notes_map = {
        "completed": [
            "Appointment completed successfully", 
            "Patient satisfied with care",
            "Follow-up recommended in 6 months",
            "Prescription updated"
        ],
        "no-show": [
            "Patient did not show up",
            "No call, no show", 
            "Attempted to contact patient"
        ],
        "cancelled": [
            "Patient cancelled due to illness",
            "Emergency cancellation",
            "Requested to reschedule"
        ],
        "rescheduled": [
            "Rescheduled per patient request",
            "Doctor availability conflict", 
            "Insurance authorization pending"
        ]
    }
    
    return random.choice(notes_map.get(status, [""]))

# ============================================================================
# FILE GENERATION AND SAVING
# ============================================================================

def save_patient_data(patients_df: pd.DataFrame, filename: str = "data/patients.csv"):
    """Save patient data to CSV file."""
    # Create directory if it doesn't exist
    os.makedirs(os.path.dirname(filename), exist_ok=True)
    
    # Save to CSV
    patients_df.to_csv(filename, index=False)
    print(f"✅ Patient data saved to {filename}")

def save_doctor_schedules(schedules_df: pd.DataFrame, filename: str = "data/doctor_schedules.xlsx"):
    """Save doctor schedules to Excel file with multiple sheets."""
    # Create directory if it doesn't exist  
    os.makedirs(os.path.dirname(filename), exist_ok=True)
    
    with pd.ExcelWriter(filename, engine='xlsxwriter') as writer:
        # Main schedule data
        schedules_df.to_excel(writer, sheet_name='Schedule', index=False)
        
        # Doctor information sheet
        doctors_df = pd.DataFrame(DOCTORS_DATA)
        doctors_df.to_excel(writer, sheet_name='Doctors', index=False)
        
        # Summary statistics
        summary_stats = generate_schedule_summary(schedules_df)
        summary_stats.to_excel(writer, sheet_name='Summary', index=False)
        
        # Format worksheets
        workbook = writer.book
        
        # Add formats
        header_format = workbook.add_format({
            'bold': True,
            'text_wrap': True,
            'valign': 'top',
            'fg_color': '#D7E4BC',
            'border': 1
        })
        
        # Format headers
        for sheet_name in writer.sheets:
            worksheet = writer.sheets[sheet_name]
            worksheet.set_row(0, None, header_format)
            worksheet.autofit()
    
    print(f"✅ Doctor schedules saved to {filename}")

def save_appointment_history(appointments_df: pd.DataFrame, filename: str = "data/appointment_history.xlsx"):
    """Save appointment history to Excel file."""
    os.makedirs(os.path.dirname(filename), exist_ok=True)
    appointments_df.to_excel(filename, index=False)
    print(f"✅ Appointment history saved to {filename}")

def generate_schedule_summary(schedules_df: pd.DataFrame) -> pd.DataFrame:
    """Generate summary statistics for doctor schedules."""
    summary_data = []
    
    for doctor in DOCTORS_DATA:
        doctor_slots = schedules_df[schedules_df['doctor_id'] == doctor['doctor_id']]
        
        total_slots = len(doctor_slots)
        available_slots = len(doctor_slots[doctor_slots['availability_status'] == 'available'])
        booked_slots = len(doctor_slots[doctor_slots['availability_status'] == 'booked'])
        blocked_slots = len(doctor_slots[doctor_slots['availability_status'] == 'blocked'])
        
        availability_rate = (available_slots / total_slots * 100) if total_slots > 0 else 0
        
        summary_data.append({
            'Doctor': doctor['name'],
            'Specialty': doctor['specialty'],
            'Total Slots': total_slots,
            'Available': available_slots,
            'Booked': booked_slots, 
            'Blocked': blocked_slots,
            'Availability Rate (%)': round(availability_rate, 1)
        })
    
    return pd.DataFrame(summary_data)

# ============================================================================
# MAIN GENERATION FUNCTION
# ============================================================================

def generate_all_sample_data():
    """Generate all sample data files for the medical appointment system."""
    
    print("🏥 MEDICARE ALLERGY & WELLNESS CENTER")
    print("=" * 60)
    print("Generating Sample Data for Appointment Scheduling System")
    print("=" * 60)
    
    try:
        # Generate patient data
        print("\n📋 GENERATING PATIENT DATA")
        print("-" * 30)
        patients_df = generate_patient_data(num_patients=50)
        save_patient_data(patients_df)
        
        # Generate doctor schedules  
        print("\n📅 GENERATING DOCTOR SCHEDULES")
        print("-" * 30)
        schedules_df = generate_doctor_schedules(num_days=21)  # 3 weeks
        save_doctor_schedules(schedules_df)
        
        # Generate appointment history
        print("\n📊 GENERATING APPOINTMENT HISTORY")
        print("-" * 30)
        appointments_df = generate_appointment_history(num_appointments=100)
        save_appointment_history(appointments_df)
        
        # Generate summary report
        print("\n📈 GENERATING SUMMARY REPORT")
        print("-" * 30)
        generate_data_summary(patients_df, schedules_df, appointments_df)
        
        print("\n" + "=" * 60)
        print("✅ ALL SAMPLE DATA GENERATED SUCCESSFULLY!")
        print("=" * 60)
        
        print(f"""
📁 Generated Files:
   • data/patients.csv ({len(patients_df)} records)
   • data/doctor_schedules.xlsx ({len(schedules_df)} slots)
   • data/appointment_history.xlsx ({len(appointments_df)} appointments)

🎯 Ready for Demo:
   • {len(patients_df)} diverse patient profiles
   • {len(schedules_df)} appointment slots across {len(DOCTORS_DATA)} doctors
   • {len(appointments_df)} historical appointments for analytics
   • Realistic medical data patterns and demographics
        """)
        
    except Exception as e:
        print(f"❌ Error generating sample data: {str(e)}")
        raise

def generate_data_summary(patients_df: pd.DataFrame, schedules_df: pd.DataFrame, appointments_df: pd.DataFrame):
    """Generate and display data summary statistics."""
    
    # Patient statistics
    new_patients = len(patients_df[patients_df['patient_type'] == 'new'])
    returning_patients = len(patients_df[patients_df['patient_type'] == 'returning'])
    
    # Schedule statistics
    available_slots = len(schedules_df[schedules_df['availability_status'] == 'available'])
    total_slots = len(schedules_df)
    
    # Insurance distribution
    insurance_dist = patients_df['insurance_carrier'].value_counts()
    
    print(f"""
📊 DATA SUMMARY:
   
   Patients:
   • Total Patients: {len(patients_df)}
   • New Patients: {new_patients} ({new_patients/len(patients_df)*100:.1f}%)
   • Returning Patients: {returning_patients} ({returning_patients/len(patients_df)*100:.1f}%)
   
   Schedules:
   • Total Time Slots: {total_slots}
   • Available Slots: {available_slots} ({available_slots/total_slots*100:.1f}%)
   • Doctors: {len(DOCTORS_DATA)} across {len(set([d['specialty'] for d in DOCTORS_DATA]))} specialties
   
   Top Insurance Providers:
   {chr(10).join([f"   • {provider}: {count} patients" for provider, count in insurance_dist.head(3).items()])}
    """)

# ============================================================================
# UTILITY FUNCTIONS FOR TESTING
# ============================================================================

def validate_generated_data():
    """Validate the generated sample data for consistency."""
    
    print("\n🔍 VALIDATING GENERATED DATA")
    print("-" * 30)
    
    issues = []
    
    try:
        # Check if files exist
        files_to_check = [
            "data/patients.csv",
            "data/doctor_schedules.xlsx", 
            "data/appointment_history.xlsx"
        ]
        
        for file_path in files_to_check:
            if not os.path.exists(file_path):
                issues.append(f"Missing file: {file_path}")
            else:
                print(f"✅ Found: {file_path}")
        
        # Validate patient data
        if os.path.exists("data/patients.csv"):
            patients_df = pd.read_csv("data/patients.csv")
            
            # Check required columns
            required_columns = ['patient_id', 'name', 'dob', 'phone', 'email', 'patient_type']
            missing_columns = [col for col in required_columns if col not in patients_df.columns]
            
            if missing_columns:
                issues.append(f"Missing patient columns: {missing_columns}")
            
            # Check data types and values
            if patients_df['patient_type'].nunique() < 2:
                issues.append("Patient type should have both 'new' and 'returning'")
        
        # Validate schedule data
        if os.path.exists("data/doctor_schedules.xlsx"):
            schedules_df = pd.read_excel("data/doctor_schedules.xlsx")
            
            required_columns = ['doctor_id', 'doctor_name', 'date', 'start_time', 'availability_status']
            missing_columns = [col for col in required_columns if col not in schedules_df.columns]
            
            if missing_columns:
                issues.append(f"Missing schedule columns: {missing_columns}")
        
        if issues:
            print("❌ Validation Issues Found:")
            for issue in issues:
                print(f"   • {issue}")
        else:
            print("✅ All data validation checks passed!")
            
    except Exception as e:
        print(f"❌ Error during validation: {str(e)}")

def cleanup_generated_files():
    """Clean up generated files for fresh start."""
    files_to_remove = [
        "data/patients.csv",
        "data/doctor_schedules.xlsx",
        "data/appointment_history.xlsx"
    ]
    
    removed_count = 0
    for file_path in files_to_remove:
        if os.path.exists(file_path):
            os.remove(file_path)
            removed_count += 1
            print(f"🗑️  Removed: {file_path}")
    
    if removed_count == 0:
        print("📁 No files to clean up")
    else:
        print(f"✅ Cleaned up {removed_count} files")

# ============================================================================
# MAIN EXECUTION
# ============================================================================

if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="Generate sample data for medical appointment scheduling system")
    parser.add_argument("--patients", type=int, default=50, help="Number of patients to generate")
    parser.add_argument("--days", type=int, default=21, help="Number of days for doctor schedules")
    parser.add_argument("--appointments", type=int, default=100, help="Number of historical appointments")
    parser.add_argument("--validate", action="store_true", help="Validate generated data")
    parser.add_argument("--cleanup", action="store_true", help="Clean up existing files before generating")
    
    args = parser.parse_args()
    
    try:
        if args.cleanup:
            cleanup_generated_files()
            print()
        
        # Generate all sample data
        generate_all_sample_data()
        
        if args.validate:
            validate_generated_data()
            
        print(f"\n🎉 Sample data generation completed successfully!")
        print(f"Ready for RagaAI Medical Appointment Scheduling Demo!")
        
    except KeyboardInterrupt:
        print("\n⚠️  Generation cancelled by user")
    except Exception as e:
        print(f"\n❌ Error: {str(e)}")
        exit(1)
