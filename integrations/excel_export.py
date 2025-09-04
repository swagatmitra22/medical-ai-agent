"""
Excel Export Integration - Medical Appointment Scheduling System
=============================================================

This module handles comprehensive Excel export functionality for administrative
reporting and data analysis including appointment summaries, revenue tracking,
and multi-sheet reports with professional formatting.

Key Responsibilities:
- Export appointment data to Excel with multiple sheets
- Generate administrative summary statistics and reports
- Create formatted Excel files with professional styling
- Handle revenue tracking and patient analytics
- Provide comprehensive error handling and logging
- Support batch exports and scheduled reporting

Author: RagaAI Case Study Implementation
Date: September 2025
"""

import os
import pandas as pd
import logging
from typing import Dict, Any, List, Optional, Tuple
from datetime import datetime, timedelta
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# ============================================================================
# EXCEL EXPORT MANAGER CLASS
# ============================================================================

class AppointmentExporter:
    """
    Comprehensive Excel exporter for appointment data and administrative reports.
    """
    
    def __init__(self, export_directory: str = "data"):
        """
        Initialize the appointment exporter.
        
        Args:
            export_directory: Directory to save exported Excel files
        """
        self.export_directory = export_directory
        self.ensure_export_directory()
        
        # Clinic information for reports
        self.clinic_info = {
            "name": "MediCare Allergy & Wellness Center",
            "address": "456 Healthcare Boulevard, Suite 300",
            "phone": "(555) 123-4567",
            "website": "www.medicare-wellness.com"
        }
    
    def ensure_export_directory(self):
        """Ensure the export directory exists."""
        if not os.path.exists(self.export_directory):
            os.makedirs(self.export_directory)
            logger.info(f"Created export directory: {self.export_directory}")
    
    def export_appointment_data(self, 
                              appointments_df: pd.DataFrame, 
                              filename: Optional[str] = None) -> str:
        """
        Export appointment data to Excel with multiple sheets and formatting.
        
        Args:
            appointments_df: DataFrame containing appointment data
            filename: Optional custom filename for the export
            
        Returns:
            Path to the exported Excel file
        """
        try:
            # Generate filename if not provided
            if not filename:
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                filename = f"admin_appointment_report_{timestamp}.xlsx"
            
            filepath = os.path.join(self.export_directory, filename)
            
            # Create Excel writer with xlsxwriter engine for formatting
            with pd.ExcelWriter(filepath, engine='xlsxwriter') as writer:
                # Write main appointments data
                appointments_df.to_excel(writer, sheet_name='Appointments', index=False)
                
                # Generate and write summary statistics
                summary_df = self._generate_summary_statistics(appointments_df)
                summary_df.to_excel(writer, sheet_name='Summary', index=False)
                
                # Generate and write daily schedule
                daily_schedule_df = self._generate_daily_schedule(appointments_df)
                daily_schedule_df.to_excel(writer, sheet_name='Daily_Schedule', index=False)
                
                # Generate and write doctor statistics
                doctor_stats_df = self._generate_doctor_statistics(appointments_df)
                doctor_stats_df.to_excel(writer, sheet_name='Doctor_Statistics', index=False)
                
                # Generate and write revenue analysis
                revenue_df = self._generate_revenue_analysis(appointments_df)
                revenue_df.to_excel(writer, sheet_name='Revenue_Analysis', index=False)
                
                # Apply formatting to all sheets
                self._format_excel_workbook(writer, appointments_df, summary_df, 
                                          daily_schedule_df, doctor_stats_df, revenue_df)
            
            logger.info(f"Appointment data exported successfully to {filepath}")
            return filepath
            
        except Exception as e:
            logger.error(f"Error exporting appointment data: {str(e)}")
            raise
    
    def _generate_summary_statistics(self, appointments_df: pd.DataFrame) -> pd.DataFrame:
        """Generate comprehensive summary statistics."""
        try:
            total_appointments = len(appointments_df)
            
            # Calculate totals by patient type
            new_patients = len(appointments_df[appointments_df.get('Patient_Type', '') == 'new']) if 'Patient_Type' in appointments_df.columns else 0
            returning_patients = total_appointments - new_patients
            
            # Calculate revenue statistics
            total_revenue = appointments_df.get('Estimated_Revenue', pd.Series([0])).sum()
            avg_revenue = appointments_df.get('Estimated_Revenue', pd.Series([0])).mean()
            
            # Calculate duration statistics
            avg_duration = appointments_df.get('Duration_Minutes', pd.Series([0])).mean()
            
            # Calculate date range
            if 'Appointment_Date' in appointments_df.columns:
                dates = pd.to_datetime(appointments_df['Appointment_Date'], errors='coerce').dropna()
                if len(dates) > 0:
                    date_range = f"{dates.min().strftime('%m/%d/%Y')} - {dates.max().strftime('%m/%d/%Y')}"
                else:
                    date_range = "N/A"
            else:
                date_range = "N/A"
            
            # Create summary data
            summary_data = [
                {"Metric": "Report Generated", "Value": datetime.now().strftime("%m/%d/%Y %H:%M:%S")},
                {"Metric": "Date Range", "Value": date_range},
                {"Metric": "Total Appointments", "Value": total_appointments},
                {"Metric": "New Patients", "Value": new_patients},
                {"Metric": "Returning Patients", "Value": returning_patients},
                {"Metric": "Total Estimated Revenue", "Value": f"${total_revenue:,.2f}"},
                {"Metric": "Average Revenue per Appointment", "Value": f"${avg_revenue:,.2f}"},
                {"Metric": "Average Appointment Duration (minutes)", "Value": f"{avg_duration:.1f}"},
                {"Metric": "New Patient Percentage", "Value": f"{(new_patients/total_appointments*100):.1f}%" if total_appointments > 0 else "0%"},
            ]
            
            return pd.DataFrame(summary_data)
            
        except Exception as e:
            logger.error(f"Error generating summary statistics: {str(e)}")
            return pd.DataFrame([{"Metric": "Error", "Value": "Could not generate statistics"}])
    
    def _generate_daily_schedule(self, appointments_df: pd.DataFrame) -> pd.DataFrame:
        """Generate daily schedule view."""
        try:
            if 'Appointment_Date' not in appointments_df.columns:
                return pd.DataFrame([{"Message": "No appointment date information available"}])
            
            # Get today's appointments
            today = datetime.now().strftime('%m/%d/%Y')
            today_appointments = appointments_df[appointments_df['Appointment_Date'] == today].copy()
            
            if len(today_appointments) == 0:
                return pd.DataFrame([{"Message": f"No appointments scheduled for {today}"}])
            
            # Sort by appointment time if available
            if 'Appointment_Time' in today_appointments.columns:
                today_appointments = today_appointments.sort_values('Appointment_Time')
            
            # Select relevant columns for daily view
            display_columns = ['Appointment_Time', 'Patient_Name', 'Doctor', 'Duration_Minutes', 'Patient_Type']
            available_columns = [col for col in display_columns if col in today_appointments.columns]
            
            daily_schedule = today_appointments[available_columns].copy()
            
            return daily_schedule
            
        except Exception as e:
            logger.error(f"Error generating daily schedule: {str(e)}")
            return pd.DataFrame([{"Message": "Error generating daily schedule"}])
    
    def _generate_doctor_statistics(self, appointments_df: pd.DataFrame) -> pd.DataFrame:
        """Generate per-doctor statistics."""
        try:
            if 'Doctor' not in appointments_df.columns:
                return pd.DataFrame([{"Message": "No doctor information available"}])
            
            # Group by doctor and calculate statistics
            doctor_stats = []
            
            for doctor in appointments_df['Doctor'].unique():
                doctor_appointments = appointments_df[appointments_df['Doctor'] == doctor]
                
                total_appointments = len(doctor_appointments)
                total_revenue = doctor_appointments.get('Estimated_Revenue', pd.Series([0])).sum()
                avg_duration = doctor_appointments.get('Duration_Minutes', pd.Series([0])).mean()
                new_patients = len(doctor_appointments[doctor_appointments.get('Patient_Type', '') == 'new'])
                
                doctor_stats.append({
                    'Doctor': doctor,
                    'Specialty': doctor_appointments.get('Specialty', pd.Series(['N/A'])).iloc[0] if 'Specialty' in doctor_appointments.columns else 'N/A',
                    'Total_Appointments': total_appointments,
                    'New_Patients': new_patients,
                    'Returning_Patients': total_appointments - new_patients,
                    'Total_Revenue': f"${total_revenue:,.2f}",
                    'Average_Duration_Minutes': f"{avg_duration:.1f}",
                    'Utilization_Rate': f"{(total_appointments / len(appointments_df) * 100):.1f}%"
                })
            
            return pd.DataFrame(doctor_stats)
            
        except Exception as e:
            logger.error(f"Error generating doctor statistics: {str(e)}")
            return pd.DataFrame([{"Message": "Error generating doctor statistics"}])
    
    def _generate_revenue_analysis(self, appointments_df: pd.DataFrame) -> pd.DataFrame:
        """Generate revenue analysis by date, doctor, and patient type."""
        try:
            if 'Estimated_Revenue' not in appointments_df.columns:
                return pd.DataFrame([{"Message": "No revenue information available"}])
            
            revenue_analysis = []
            
            # Revenue by patient type
            if 'Patient_Type' in appointments_df.columns:
                for patient_type in appointments_df['Patient_Type'].unique():
                    type_data = appointments_df[appointments_df['Patient_Type'] == patient_type]
                    revenue = type_data['Estimated_Revenue'].sum()
                    count = len(type_data)
                    avg_revenue = revenue / count if count > 0 else 0
                    
                    revenue_analysis.append({
                        'Category': f'{patient_type.title()} Patients',
                        'Appointments': count,
                        'Total_Revenue': f"${revenue:,.2f}",
                        'Average_Revenue': f"${avg_revenue:,.2f}",
                        'Percentage_of_Total': f"{(revenue / appointments_df['Estimated_Revenue'].sum() * 100):.1f}%"
                    })
            
            # Revenue by doctor
            if 'Doctor' in appointments_df.columns:
                for doctor in appointments_df['Doctor'].unique():
                    doctor_data = appointments_df[appointments_df['Doctor'] == doctor]
                    revenue = doctor_data['Estimated_Revenue'].sum()
                    count = len(doctor_data)
                    avg_revenue = revenue / count if count > 0 else 0
                    
                    revenue_analysis.append({
                        'Category': doctor,
                        'Appointments': count,
                        'Total_Revenue': f"${revenue:,.2f}",
                        'Average_Revenue': f"${avg_revenue:,.2f}",
                        'Percentage_of_Total': f"{(revenue / appointments_df['Estimated_Revenue'].sum() * 100):.1f}%"
                    })
            
            return pd.DataFrame(revenue_analysis)
            
        except Exception as e:
            logger.error(f"Error generating revenue analysis: {str(e)}")
            return pd.DataFrame([{"Message": "Error generating revenue analysis"}])
    
    def _format_excel_workbook(self, writer, appointments_df, summary_df, daily_schedule_df, doctor_stats_df, revenue_df):
        """Apply comprehensive formatting to the Excel workbook."""
        try:
            workbook = writer.book
            
            # Define formats
            header_format = workbook.add_format({
                'bold': True,
                'text_wrap': True,
                'valign': 'top',
                'fg_color': '#4472C4',
                'font_color': 'white',
                'border': 1
            })
            
            currency_format = workbook.add_format({
                'num_format': '$#,##0.00',
                'border': 1
            })
            
            percentage_format = workbook.add_format({
                'num_format': '0.0%',
                'border': 1
            })
            
            date_format = workbook.add_format({
                'num_format': 'mm/dd/yyyy',
                'border': 1
            })
            
            time_format = workbook.add_format({
                'num_format': 'hh:mm AM/PM',
                'border': 1
            })
            
            # Format each sheet
            sheets_data = [
                ('Appointments', appointments_df),
                ('Summary', summary_df),
                ('Daily_Schedule', daily_schedule_df),
                ('Doctor_Statistics', doctor_stats_df),
                ('Revenue_Analysis', revenue_df)
            ]
            
            for sheet_name, df in sheets_data:
                if sheet_name in writer.sheets:
                    worksheet = writer.sheets[sheet_name]
                    
                    # Format headers
                    for col_num, value in enumerate(df.columns.values):
                        worksheet.write(0, col_num, value, header_format)
                    
                    # Auto-adjust column widths
                    for i, col in enumerate(df.columns):
                        # Calculate max width
                        max_len = max(df[col].astype(str).map(len).max(), len(col)) + 2
                        worksheet.set_column(i, i, min(max_len, 50))  # Cap at 50 characters
                        
                        # Apply specific formatting based on column content
                        if 'revenue' in col.lower() or 'revenue' in str(df[col].dtype).lower():
                            worksheet.set_column(i, i, max_len, currency_format)
                        elif 'percentage' in col.lower():
                            worksheet.set_column(i, i, max_len, percentage_format)
                        elif 'date' in col.lower():
                            worksheet.set_column(i, i, max_len, date_format)
                        elif 'time' in col.lower():
                            worksheet.set_column(i, i, max_len, time_format)
                    
                    # Add autofilter
                    if len(df) > 0:
                        worksheet.autofilter(0, 0, len(df), len(df.columns) - 1)
            
            logger.info("Excel formatting applied successfully")
            
        except Exception as e:
            logger.error(f"Error formatting Excel workbook: {str(e)}")

# ============================================================================
# CONVENIENCE FUNCTIONS FOR LANGGRAPH INTEGRATION
# ============================================================================

def export_appointment_data(appointments_data: List[Dict[str, Any]], 
                          export_directory: str = "data") -> str:
    """
    Convenience function to export appointment data from list of dictionaries.
    
    Args:
        appointments_data: List of appointment dictionaries
        export_directory: Directory to save the export
        
    Returns:
        Path to the exported Excel file
    """
    try:
        if not appointments_data:
            logger.warning("No appointment data provided for export")
            return ""
        
        # Convert to DataFrame
        appointments_df = pd.DataFrame(appointments_data)
        
        # Initialize exporter and export
        exporter = AppointmentExporter(export_directory)
        return exporter.export_appointment_data(appointments_df)
        
    except Exception as e:
        logger.error(f"Error in export_appointment_data: {str(e)}")
        return ""

def generate_admin_report(state: Dict[str, Any]) -> Dict[str, Any]:
    """
    Generate administrative report from appointment state.
    
    Args:
        state: Current appointment state with confirmation details
        
    Returns:
        Updated state with export information
    """
    logger.info("Generating administrative report")
    
    try:
        # Extract confirmation details from state
        confirmation_details = state.get('confirmation_details', {})
        
        if not confirmation_details:
            return {
                **state,
                "error_message": "No confirmation details available for report generation",
                "export_status": "failed"
            }
        
        # Create appointment data for export
        appointment_data = [{
            'Confirmation_ID': confirmation_details.get('confirmation_id', ''),
            'Patient_Name': confirmation_details.get('patient_name', ''),
            'Patient_Type': confirmation_details.get('patient_type', ''),
            'Phone': confirmation_details.get('patient_phone', ''),
            'Email': confirmation_details.get('patient_email', ''),
            'Appointment_Date': confirmation_details.get('appointment_date', ''),
            'Appointment_Time': confirmation_details.get('appointment_time', ''),
            'Duration_Minutes': confirmation_details.get('appointment_duration', ''),
            'Doctor': confirmation_details.get('doctor_name', ''),
            'Specialty': confirmation_details.get('doctor_specialty', ''),
            'Insurance_Carrier': confirmation_details.get('insurance_carrier', ''),
            'Member_ID': confirmation_details.get('member_id', ''),
            'Estimated_Revenue': confirmation_details.get('estimated_revenue', 0),
            'Booking_Status': confirmation_details.get('booking_status', ''),
            'Confirmation_Time': confirmation_details.get('confirmation_timestamp', ''),
            'Forms_Required': 'Yes' if confirmation_details.get('requires_forms') else 'No'
        }]
        
        # Export the data
        export_path = export_appointment_data(appointment_data)
        
        if export_path:
            updated_state = {
                **state,
                "admin_export_path": export_path,
                "export_status": "success"
            }
        else:
            updated_state = {
                **state,
                "error_message": "Failed to generate admin report",
                "export_status": "failed"
            }
        
        return updated_state
        
    except Exception as e:
        logger.error(f"Error generating admin report: {str(e)}")
        return {
            **state,
            "error_message": f"Admin report generation error: {str(e)}",
            "export_status": "failed"
        }

# ============================================================================
# UTILITY FUNCTIONS
# ============================================================================

def validate_appointment_data(appointments_df: pd.DataFrame) -> Tuple[bool, List[str]]:
    """
    Validate appointment data for export readiness.
    
    Args:
        appointments_df: DataFrame to validate
        
    Returns:
        Tuple of (is_valid, list_of_issues)
    """
    issues = []
    
    # Check if DataFrame is empty
    if appointments_df.empty:
        issues.append("Appointment DataFrame is empty")
        return False, issues
    
    # Check for required columns
    required_columns = ['Patient_Name', 'Appointment_Date', 'Doctor']
    missing_columns = [col for col in required_columns if col not in appointments_df.columns]
    
    if missing_columns:
        issues.append(f"Missing required columns: {missing_columns}")
    
    # Check for data quality issues
    if 'Appointment_Date' in appointments_df.columns:
        invalid_dates = appointments_df['Appointment_Date'].isna().sum()
        if invalid_dates > 0:
            issues.append(f"{invalid_dates} appointments have invalid dates")
    
    if 'Estimated_Revenue' in appointments_df.columns:
        negative_revenue = (appointments_df['Estimated_Revenue'] < 0).sum()
        if negative_revenue > 0:
            issues.append(f"{negative_revenue} appointments have negative revenue")
    
    return len(issues) == 0, issues

def create_backup_export(appointments_df: pd.DataFrame, backup_directory: str = "data/backups") -> str:
    """
    Create a backup export of appointment data.
    
    Args:
        appointments_df: DataFrame to backup
        backup_directory: Directory for backup files
        
    Returns:
        Path to backup file
    """
    try:
        os.makedirs(backup_directory, exist_ok=True)
        
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        backup_filename = f"appointment_backup_{timestamp}.xlsx"
        backup_path = os.path.join(backup_directory, backup_filename)
        
        # Simple export without formatting
        appointments_df.to_excel(backup_path, index=False)
        
        logger.info(f"Backup created: {backup_path}")
        return backup_path
        
    except Exception as e:
        logger.error(f"Error creating backup: {str(e)}")
        return ""

# ============================================================================
# TESTING FUNCTIONS
# ============================================================================

def test_excel_export():
    """Test function to validate Excel export functionality."""
    
    print("Testing Excel Export System")
    print("=" * 50)
    
    # Create test data
    test_data = [
        {
            'Confirmation_ID': 'TEST-001',
            'Patient_Name': 'John Test Patient',
            'Patient_Type': 'new',
            'Phone': '(555) 123-4567',
            'Email': 'john@test.com',
            'Appointment_Date': '09/10/2025',
            'Appointment_Time': '10:00 AM',
            'Duration_Minutes': 60,
            'Doctor': 'Dr. Johnson',
            'Specialty': 'Family Medicine',
            'Insurance_Carrier': 'BlueCross BlueShield',
            'Member_ID': 'BC123456',
            'Estimated_Revenue': 250.00,
            'Booking_Status': 'confirmed',
            'Forms_Required': 'Yes'
        },
        {
            'Confirmation_ID': 'TEST-002',
            'Patient_Name': 'Jane Test Patient',
            'Patient_Type': 'returning',
            'Phone': '(555) 987-6543',
            'Email': 'jane@test.com',
            'Appointment_Date': '09/11/2025',
            'Appointment_Time': '2:30 PM',
            'Duration_Minutes': 30,
            'Doctor': 'Dr. Smith',
            'Specialty': 'Cardiology',
            'Insurance_Carrier': 'UnitedHealthcare',
            'Member_ID': 'UHC789012',
            'Estimated_Revenue': 150.00,
            'Booking_Status': 'confirmed',
            'Forms_Required': 'No'
        }
    ]
    
    # Test export
    try:
        export_path = export_appointment_data(test_data)
        
        if export_path and os.path.exists(export_path):
            print(f"✅ Test export successful: {export_path}")
            
            # Test data validation
            df = pd.DataFrame(test_data)
            is_valid, issues = validate_appointment_data(df)
            
            if is_valid:
                print("✅ Data validation passed")
            else:
                print(f"❌ Data validation issues: {issues}")
            
        else:
            print("❌ Test export failed")
            
    except Exception as e:
        print(f"❌ Test error: {str(e)}")
    
    print("\n" + "=" * 50)
    print("Excel export test completed!")

if __name__ == "__main__":
    # Run tests when executed directly
    test_excel_export()
