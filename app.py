"""
MediCare AI Appointment Scheduler - Streamlit Application
======================================================

Main Streamlit application for the medical appointment scheduling AI agent.
Features include patient chat interface, admin dashboard, Excel exports,
and comprehensive error handling.

Author: RagaAI Case Study Implementation
Date: September 2025
"""

import streamlit as st
import pandas as pd
import os
import logging
from datetime import datetime, timedelta
from typing import Dict, Any
import plotly.express as px
import plotly.graph_objects as go

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Import core components
try:
    from agents.core_agent import create_agent, MedicalSchedulingAgent
    from data.sample_data_generator import generate_all_sample_data
    from integrations.excel_export import export_appointment_data
    from dotenv import load_dotenv
    
    # Load environment variables
    load_dotenv()
    
except ImportError as e:
    st.error(f"Import Error: {str(e)}")
    st.error("Please ensure all required modules are installed and available.")
    st.stop()

# ============================================================================
# PAGE CONFIGURATION AND STYLING
# ============================================================================

st.set_page_config(
    page_title="MediCare AI Scheduler",
    page_icon="🏥",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS for professional medical styling
st.markdown("""
<style>
    .main-header {
        background: linear-gradient(90deg, #4CAF50, #2196F3);
        padding: 1rem;
        border-radius: 10px;
        margin-bottom: 2rem;
        color: white;
        text-align: center;
    }
    
    .chat-user {
        background-color: #E3F2FD;
        padding: 10px 15px;
        border-radius: 15px 15px 5px 15px;
        margin: 5px 0;
        margin-left: 20%;
        color: black;
        text-align: right;
    }
    
    .chat-assistant {
        background-color: #F1F8E9;
        padding: 10px 15px;
        border-radius: 15px 15px 15px 5px;
        margin: 5px 0;
        margin-right: 20%;
        border-left: 4px solid #4CAF50;
        color: black;
    }
    
    .metric-card {
        background-color: #FAFAFA;
        padding: 1rem;
        border-radius: 8px;
        border: 1px solid #E0E0E0;
        margin: 0.5rem 0;
        color: black;
    }
    
    .status-success {
        color: #4CAF50;
        font-weight: bold;
    }
    
    .status-error {
        color: #F44336;
        font-weight: bold;
    }
    
    .clinic-info {
        background-color: #E8F5E8;
        padding: 1rem;
        border-radius: 8px;
        border-left: 4px solid #4CAF50;
        margin: 1rem 0;
        color: black;
    }
</style>
""", unsafe_allow_html=True)

# ============================================================================
# SESSION STATE INITIALIZATION
# ============================================================================

def initialize_session_state():
    """Initialize all session state variables."""
    
    # Core agent initialization
    if 'agent' not in st.session_state:
        try:
            st.session_state.agent = create_agent()
            st.session_state.agent_status = "✅ Connected"
            logger.info("Groq agent initialized successfully")
        except Exception as e:
            st.session_state.agent = None
            st.session_state.agent_status = "❌ Connection Failed"
            logger.error(f"Failed to initialize agent: {str(e)}")
    
    # Chat conversation history
    if 'messages' not in st.session_state:
        st.session_state.messages = []
    
    # Current conversation thread ID
    if 'thread_id' not in st.session_state:
        st.session_state.thread_id = f"session-{datetime.now().strftime('%Y%m%d%H%M%S')}"
    
    # Application state
    if 'current_page' not in st.session_state:
        st.session_state.current_page = "Patient Chat"
    
    # Sample data status
    if 'data_generated' not in st.session_state:
        st.session_state.data_generated = False
    
    # Admin dashboard data
    if 'admin_data' not in st.session_state:
        st.session_state.admin_data = None

# Initialize session state
initialize_session_state()

# ============================================================================
# UTILITY FUNCTIONS
# ============================================================================

def check_data_files():
    """Check if required data files exist."""
    files_to_check = [
        "data/patients.csv",
        "data/doctor_schedules.xlsx"
    ]
    
    existing_files = []
    missing_files = []
    
    for file_path in files_to_check:
        if os.path.exists(file_path):
            existing_files.append(file_path)
        else:
            missing_files.append(file_path)
    
    return existing_files, missing_files

def load_admin_data():
    """Load data for admin dashboard."""
    try:
        admin_data = {}
        
        # Load patients data
        if os.path.exists("data/patients.csv"):
            admin_data['patients'] = pd.read_csv("data/patients.csv")
        
        # Load doctor schedules
        if os.path.exists("data/doctor_schedules.xlsx"):
            admin_data['schedules'] = pd.read_excel("data/doctor_schedules.xlsx")
        
        # Load appointments if exists
        if os.path.exists("data/admin_appointment_report.xlsx"):
            admin_data['appointments'] = pd.read_excel("data/admin_appointment_report.xlsx", sheet_name="Appointments")
        
        return admin_data
    
    except Exception as e:
        logger.error(f"Error loading admin data: {str(e)}")
        return {}

def format_message_display(message, is_user=False):
    """Format chat message for display."""
    if is_user:
        return f'<div class="chat-user">👤 <strong>You:</strong> {message}</div>'
    else:
        return f'<div class="chat-assistant">🏥 <strong>MediCare Assistant:</strong> {message}</div>'

# ============================================================================
# MAIN APPLICATION HEADER
# ============================================================================

st.markdown("""
<div class="main-header">
    <h1>🏥 MediCare Allergy & Wellness Center</h1>
    <h3>AI-Powered Appointment Scheduling Assistant</h3>
    <p>Streamlining healthcare appointments with intelligent conversation</p>
</div>
""", unsafe_allow_html=True)

# ============================================================================
# SIDEBAR NAVIGATION
# ============================================================================

st.sidebar.title("🔧 Navigation & Controls")

# Page selection
page_options = ["Patient Chat", "Admin Dashboard", "System Status", "Help & Demo"]
st.session_state.current_page = st.sidebar.selectbox(
    "Select Page", 
    page_options, 
    index=page_options.index(st.session_state.current_page)
)

st.sidebar.markdown("---")

# System status in sidebar
st.sidebar.subheader("🔄 System Status")
st.sidebar.markdown(f"**Gemini Agent:** {st.session_state.agent_status}")

# Check API key status
api_key_status = "✅ Configured" if os.getenv("GOOGLE_API_KEY") else "❌ Missing"
st.sidebar.markdown(f"**API Key:** {api_key_status}")

# Data files status
existing_files, missing_files = check_data_files()
st.sidebar.markdown(f"**Data Files:** {len(existing_files)}/{len(existing_files) + len(missing_files)} Ready")

st.sidebar.markdown("---")

# Quick actions
st.sidebar.subheader("⚡ Quick Actions")

if st.sidebar.button("🔄 Reset Conversation"):
    st.session_state.messages = []
    st.session_state.thread_id = f"session-{datetime.now().strftime('%Y%m%d%H%M%S')}"
    st.success("Conversation reset!")
    st.rerun()

if st.sidebar.button("📊 Generate Sample Data"):
    with st.spinner("Generating sample data..."):
        try:
            generate_all_sample_data()
            st.session_state.data_generated = True
            st.success("Sample data generated successfully!")
            st.rerun()
        except Exception as e:
            st.error(f"Error generating data: {str(e)}")

# ============================================================================
# PAGE ROUTING
# ============================================================================

if st.session_state.current_page == "Patient Chat":
    # ========================================================================
    # PATIENT CHAT INTERFACE
    # ========================================================================
    
    col1, col2 = st.columns([2, 1])
    
    with col1:
        st.header("💬 Chat with MediCare Assistant")
        
        # Check if agent is available
        if st.session_state.agent is None:
            st.error("⚠️ AI Agent is not available. Please check your configuration.")
            st.info("Make sure your Google Gemini API key is set in the .env file.")
        else:
            # Chat interface
            st.markdown("**Start a conversation to schedule your medical appointment:**")
            
            # Display conversation history
            if st.session_state.messages:
                st.markdown("### Conversation History")
                for msg in st.session_state.messages:
                    # Determine who sent the message based on the 'role' key
                    is_user = msg["role"] == "user"
                    # Display the message content
                    st.markdown(format_message_display(msg["content"], is_user), unsafe_allow_html=True)
            
            # Chat input
            st.markdown("---")
            user_input = st.text_input(
                "Type your message here:", 
                key="chat_input",
                placeholder="Hi, I'd like to schedule an appointment..."
            )
            
            col_send, col_example = st.columns([1, 2])
            
            with col_send:
                send_button = st.button("📤 Send Message", type="primary")
            
            with col_example:
                if st.button("💡 Try Example"):
                    user_input = "Hi, I'm John Smith, DOB 01/15/1985, and I'd like to schedule an appointment with Dr. Johnson"
            
            # Process user input
            if send_button and user_input.strip():
                with st.spinner("🤖 AI Agent is thinking..."):
                    try:
                        # Call the agent
                        result = st.session_state.agent.run_conversation(
                            user_input, 
                            st.session_state.thread_id
                        )
                        
                        if result['status'] == 'success':
                            # Add messages to display history
                            # --- START CHANGE ---
                            # Add the user's message to the history as a dictionary
                            st.session_state.messages.append({"role": "user", "content": user_input})
                            # Add the assistant's response to the history as a dictionary
                            st.session_state.messages.append({"role": "assistant", "content": result['response']})
                            # --- END CHANGE ---
                            st.success("✅ Message processed successfully!")
                            st.rerun()
                        else:
                            st.error(f"❌ Error: {result.get('error', 'Unknown error')}")
                    
                    except Exception as e:
                        st.error(f"❌ Agent Error: {str(e)}")
                        logger.error(f"Agent error: {str(e)}")
    
    with col2:
        st.markdown("""
        <div class="clinic-info">
            <h4>🏥 Clinic Information</h4>
            <p><strong>MediCare Allergy & Wellness Center</strong></p>
            <p>📍 456 Healthcare Boulevard, Suite 300</p>
            <p>📞 (555) 123-4567</p>
            <p>🕒 Mon-Fri: 8:00 AM - 6:00 PM</p>
            <p>🕒 Sat: 9:00 AM - 2:00 PM</p>
        </div>
        """, unsafe_allow_html=True)
        
        st.subheader("👨‍⚕️ Available Doctors")
        doctors_info = [
            "Dr. Johnson - Family Medicine",
            "Dr. Smith - Cardiology", 
            "Dr. Williams - Dermatology",
            "Dr. Brown - Orthopedics",
            "Dr. Davis - Internal Medicine"
        ]
        
        for doctor in doctors_info:
            st.write(f"• {doctor}")
        
        st.subheader("📋 What I Can Help With")
        help_items = [
            "Schedule new appointments",
            "Find returning patient records", 
            "Check doctor availability",
            "Collect insurance information",
            "Send appointment confirmations",
            "Handle appointment changes"
        ]
        
        for item in help_items:
            st.write(f"✓ {item}")

elif st.session_state.current_page == "Admin Dashboard":
    # ========================================================================
    # ADMIN DASHBOARD
    # ========================================================================
    
    st.header("📊 Administrative Dashboard")
    
    # Load admin data
    admin_data = load_admin_data()
    
    if not admin_data:
        st.warning("⚠️ No data available. Please generate sample data first.")
        if st.button("🔄 Generate Sample Data"):
            with st.spinner("Generating sample data..."):
                try:
                    generate_all_sample_data()
                    st.success("Sample data generated!")
                    st.rerun()
                except Exception as e:
                    st.error(f"Error: {str(e)}")
    else:
        # Dashboard metrics
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            total_patients = len(admin_data.get('patients', []))
            st.metric("👥 Total Patients", total_patients)
        
        with col2:
            if 'schedules' in admin_data:
                available_slots = len(admin_data['schedules'][admin_data['schedules']['availability_status'] == 'available'])
                st.metric("📅 Available Slots", available_slots)
            else:
                st.metric("📅 Available Slots", "N/A")
        
        with col3:
            if 'appointments' in admin_data:
                confirmed_appointments = len(admin_data['appointments'])
                st.metric("✅ Appointments", confirmed_appointments)
            else:
                st.metric("✅ Appointments", 0)
        
        with col4:
            if 'appointments' in admin_data and 'Estimated_Revenue' in admin_data['appointments'].columns:
                total_revenue = admin_data['appointments']['Estimated_Revenue'].sum()
                st.metric("💰 Est. Revenue", f"${total_revenue:,.2f}")
            else:
                st.metric("💰 Est. Revenue", "$0.00")
        
        st.markdown("---")
        
        # Data tables
        tab1, tab2, tab3 = st.tabs(["📋 Patients", "📅 Schedules", "💾 Export Data"])
        
        with tab1:
            if 'patients' in admin_data:
                st.subheader("Patient Database")
                st.dataframe(admin_data['patients'], use_container_width=True)
                
                # Patient type distribution
                if not admin_data['patients'].empty:
                    patient_types = admin_data['patients']['patient_type'].value_counts()
                    fig = px.pie(values=patient_types.values, names=patient_types.index, 
                                title="Patient Type Distribution")
                    st.plotly_chart(fig, use_container_width=True)
        
        with tab2:
            if 'schedules' in admin_data:
                st.subheader("Doctor Schedules")
                st.dataframe(admin_data['schedules'], use_container_width=True)
                
                # Availability chart
                if not admin_data['schedules'].empty:
                    availability = admin_data['schedules']['availability_status'].value_counts()
                    fig = px.bar(x=availability.index, y=availability.values,
                                title="Slot Availability Status")
                    st.plotly_chart(fig, use_container_width=True)
        
        with tab3:
            st.subheader("📊 Data Export Options")
            
            col1, col2 = st.columns(2)
            
            with col1:
                if st.button("📥 Download Patient Data"):
                    if 'patients' in admin_data:
                        csv = admin_data['patients'].to_csv(index=False)
                        st.download_button(
                            label="Download CSV",
                            data=csv,
                            file_name=f"patients_{datetime.now().strftime('%Y%m%d')}.csv",
                            mime="text/csv"
                        )
            
            with col2:
                if st.button("📈 Download Schedule Report"):
                    if 'schedules' in admin_data:
                        # Convert to Excel bytes
                        from io import BytesIO
                        output = BytesIO()
                        with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
                            admin_data['schedules'].to_excel(writer, sheet_name='Schedules', index=False)
                        
                        st.download_button(
                            label="Download Excel",
                            data=output.getvalue(),
                            file_name=f"schedules_{datetime.now().strftime('%Y%m%d')}.xlsx",
                            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
                        )

elif st.session_state.current_page == "System Status":
    # ========================================================================
    # SYSTEM STATUS PAGE
    # ========================================================================
    
    st.header("🔧 System Status & Configuration")
    
    # Environment check
    st.subheader("🌍 Environment Configuration")
    
    env_status = {
        "Google Gemini API": bool(os.getenv("GOOGLE_API_KEY")),
        "Calendly API": bool(os.getenv("CALENDLY_API_KEY")), 
        "Twilio SMS": bool(os.getenv("TWILIO_ACCOUNT_SID")),
        "Email SMTP": bool(os.getenv("SMTP_EMAIL")),
    }
    
    for service, status in env_status.items():
        status_icon = "✅" if status else "❌"
        status_text = "Configured" if status else "Missing"
        st.write(f"{status_icon} **{service}**: {status_text}")
    
    st.markdown("---")
    
    # File system check
    st.subheader("📁 Data Files Status")
    
    existing_files, missing_files = check_data_files()
    
    st.write("**✅ Available Files:**")
    for file in existing_files:
        file_size = os.path.getsize(file) if os.path.exists(file) else 0
        st.write(f"• {file} ({file_size:,} bytes)")
    
    if missing_files:
        st.write("**❌ Missing Files:**")
        for file in missing_files:
            st.write(f"• {file}")
    
    st.markdown("---")
    
    # Agent status
    st.subheader("🤖 AI Agent Status")
    
    if st.session_state.agent:
        st.success("✅ Gemini Agent: Connected and Ready")
        st.info(f"Thread ID: {st.session_state.thread_id}")
        st.info(f"Messages in Session: {len(st.session_state.messages)}")
    else:
        st.error("❌ Gemini Agent: Not Available")
        st.warning("Check your Google API key configuration")
    
    # Test connection button
    if st.button("🔄 Test Agent Connection"):
        if st.session_state.agent:
            try:
                test_result = st.session_state.agent.run_conversation("Hello, this is a test message.", "test-thread")
                if test_result['status'] == 'success':
                    st.success("✅ Agent test successful!")
                else:
                    st.error(f"❌ Agent test failed: {test_result.get('error')}")
            except Exception as e:
                st.error(f"❌ Agent test error: {str(e)}")
        else:
            st.error("❌ No agent available for testing")

else:  # Help & Demo page
    # ========================================================================
    # HELP & DEMO PAGE
    # ========================================================================
    
    st.header("🎯 Help & Demo Guide")
    
    st.markdown("""
    ### 🚀 Welcome to MediCare AI Scheduler!
    
    This intelligent appointment scheduling system demonstrates the power of AI in healthcare operations.
    
    #### 🎪 **Demo Scenarios**
    
    Try these conversation examples in the Patient Chat:
    
    **New Patient Booking:**
    ```
    Hi, I'm Sarah Johnson, DOB 03/15/1990. I'd like to schedule an appointment with Dr. Williams for a skin consultation.
    ```
    
    **Returning Patient:**
    ```
    Hello, this is Mike Davis, born 07/22/1985. I need a follow-up appointment with Dr. Smith for my heart condition.
    ```
    
    **Quick Booking:**
    ```
    I need an appointment next week. My name is Lisa Brown, DOB 11/30/1992, phone (555) 987-6543.
    ```
    """)
    
    st.markdown("---")
    
    # System architecture
    st.subheader("🏗️ System Architecture")
    
    architecture_info = """
    **🧠 AI Framework:**
    - **LangGraph**: Multi-agent workflow orchestration
    - **LangChain**: LLM integration and tools
    - **Google Gemini**: Natural language processing
    
    **🔧 Core Agents:**
    - **Patient Greeting**: Collects patient information
    - **Patient Lookup**: Searches EMR database  
    - **Smart Scheduling**: Finds optimal appointment slots
    - **Confirmation**: Generates confirmations and exports
    
    **🔗 Integrations:**
    - **Calendly API**: Calendar management
    - **Email/SMS**: Automated communications
    - **Excel Export**: Administrative reporting
    """
    
    st.markdown(architecture_info)
    
    st.markdown("---")
    
    # Features showcase
    st.subheader("✨ Key Features")
    
    features = [
        "🧠 **Smart Patient Classification**: Automatically detects new vs returning patients",
        "⏱️ **Dynamic Scheduling**: 60min new patient, 30min follow-up appointments", 
        "📊 **Excel Integration**: Comprehensive admin reporting and data export",
        "📱 **Multi-channel Communication**: Email confirmations and SMS reminders",
        "🔄 **3-Tier Reminder System**: 24hr, 4hr, and 1hr appointment reminders",
        "📋 **Form Distribution**: Automated intake form delivery for new patients",
        "🛡️ **Error Handling**: Graceful degradation and comprehensive error management",
        "📈 **Analytics Dashboard**: Real-time insights into clinic operations"
    ]
    
    for feature in features:
        st.markdown(feature)
    
    st.markdown("---")
    
    # Technical details
    with st.expander("🔬 Technical Implementation Details"):
        st.markdown("""
        **Framework Choice: LangGraph + LangChain**
        
        ✅ **Advantages:**
        - Multi-agent orchestration with complex workflows
        - State management across conversation turns
        - Conditional routing and error handling
        - Integration with multiple LLM providers
        - Extensible architecture for future enhancements
        
        **Key Technologies:**
        - **Python 3.9+**: Core programming language
        - **Streamlit**: Web interface and user experience
        - **Pandas**: Data manipulation and analysis
        - **OpenPyXL**: Excel file operations
        - **Plotly**: Interactive data visualizations
        - **Twilio**: SMS messaging service
        - **SMTP**: Email delivery system
        """)
    
    # Contact and support
    st.markdown("---")
    st.subheader("📞 Support & Contact")
    
    st.markdown("""
    **🏥 MediCare Allergy & Wellness Center**
    
    📍 **Address:** 456 Healthcare Boulevard, Suite 300  
    📞 **Phone:** (555) 123-4567  
    📧 **Email:** appointments@medicare-wellness.com  
    🌐 **Website:** www.medicare-wellness.com  
    
    **Business Hours:**
    - Monday - Friday: 8:00 AM - 6:00 PM
    - Saturday: 9:00 AM - 2:00 PM
    - Sunday: Closed
    """)

# ============================================================================
# FOOTER
# ============================================================================

st.markdown("---")
st.markdown("""
<div style='text-align: center; color: #666; padding: 1rem;'>
    <p>🤖 <strong>MediCare AI Scheduler</strong> | Powered by LangGraph + LangChain + Google Gemini</p>
    <p>Built for RagaAI Case Study | © 2025 Medical AI Solutions</p>
    <p>Streamlining healthcare through intelligent automation</p>
</div>
""", unsafe_allow_html=True)

# ============================================================================
# MAIN EXECUTION
# ============================================================================

if __name__ == "__main__":
    # This section runs when the script is executed directly
    # Streamlit apps don't typically need this, but it's here for completeness
    pass
