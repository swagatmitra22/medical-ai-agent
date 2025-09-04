"""
Medical Appointment Scheduling AI Agent - Core Agent Implementation
================================================================

This module implements the main LangGraph agent that orchestrates the entire
appointment scheduling workflow using Google's Gemini API.

Author: RagaAI Case Study Implementation
Date: September 2025
"""

import os
import logging
from typing import TypedDict, Dict, Any, List, Annotated, Literal
from datetime import datetime
import operator

# LangGraph and LangChain imports
from langgraph.graph import StateGraph, START, END
from langgraph.checkpoint.memory import MemorySaver
from langgraph.checkpoint.sqlite import SqliteSaver  
from langgraph.checkpoint.sqlite.aio import AsyncSqliteSaver

from langchain_core.messages import BaseMessage, HumanMessage, AIMessage, SystemMessage

# Google Gemini imports
from langchain_google_genai import ChatGoogleGenerativeAI
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# ============================================================================
# STATE DEFINITION
# ============================================================================

class AppointmentState(TypedDict):
    """
    Defines the shared state structure that flows between all agents in the workflow.
    """
    # Conversation management
    messages: Annotated[List[BaseMessage], operator.add]
    current_step: str
    
    # Patient information
    patient_info: Dict[str, Any]  # name, dob, phone, email, preferences
    patient_type: str  # "new" or "returning"
    existing_patient_data: Dict[str, Any]  # retrieved from database
    
    # Scheduling data
    appointment_duration: int  # 30 or 60 minutes
    doctor_preference: str
    location_preference: str
    available_slots: List[Dict[str, Any]]
    selected_slot: Dict[str, Any]
    
    # Insurance and confirmation
    insurance_data: Dict[str, Any]
    appointment_id: str
    confirmation_status: str
    calendar_booking_id: str
    
    # Error handling and flow control
    error_message: str
    retry_count: int
    needs_human_intervention: bool
    
    # Admin and reporting
    export_data: Dict[str, Any]
    reminder_schedule: List[Dict[str, Any]]

# ============================================================================
# CORE AGENT CLASS
# ============================================================================

class MedicalSchedulingAgent:
    """
    The central orchestrator for the medical appointment scheduling workflow
    using Google's Gemini API.
    """
    
    def __init__(self, gemini_model="gemini-pro", temperature=0.3, enable_persistence=True):
        """
        Initialize the Medical Scheduling Agent with Gemini API.
        
        Args:
            gemini_model: The Gemini model to use (gemini-pro, gemini-pro-vision)
            temperature: Model creativity level (0.0-1.0)
            enable_persistence: Whether to enable conversation memory
        """
        # Initialize Gemini LLM
        api_key = os.getenv("GOOGLE_API_KEY")
        if not api_key:
            raise ValueError("GOOGLE_API_KEY not found in environment variables. Please add it to your .env file.")
        
        self.llm = ChatGoogleGenerativeAI(
            model=gemini_model,
            temperature=temperature,
            google_api_key=api_key,
            convert_system_message_to_human=True  # Gemini works better with this setting
        )
        
        self.enable_persistence = enable_persistence
        
        # Initialize memory/checkpointing for conversation state
        if enable_persistence:
            self.memory = SqliteSaver.from_conn_string(":memory:")
        else:
            self.memory = None
            
        # Build the workflow graph
        self.graph = self._build_workflow_graph()
        
        logger.info(f"Medical Scheduling Agent initialized with Gemini model: {gemini_model}")
    
    def _build_workflow_graph(self):
        """
        Constructs the LangGraph workflow that defines the complete
        appointment scheduling process flow.
        """
        # Create the state graph
        workflow = StateGraph(AppointmentState)
        
        # ===== ADD WORKFLOW NODES =====
        workflow.add_node("initialize_session", self._initialize_session_node)
        workflow.add_node("patient_greeting", self._patient_greeting_node)
        workflow.add_node("collect_patient_info", self._collect_patient_info_node)
        workflow.add_node("patient_lookup", self._patient_lookup_node)
        workflow.add_node("determine_appointment_type", self._determine_appointment_type_node)
        workflow.add_node("find_available_slots", self._find_available_slots_node)
        workflow.add_node("present_slot_options", self._present_slot_options_node)
        workflow.add_node("confirm_slot_selection", self._confirm_slot_selection_node)
        workflow.add_node("collect_insurance_info", self._collect_insurance_info_node)
        workflow.add_node("create_calendar_booking", self._create_calendar_booking_node)
        workflow.add_node("generate_confirmation", self._generate_confirmation_node)
        workflow.add_node("send_notifications", self._send_notifications_node)
        workflow.add_node("setup_reminders", self._setup_reminders_node)
        workflow.add_node("export_to_excel", self._export_to_excel_node)
        workflow.add_node("handle_error", self._handle_error_node)
        workflow.add_node("request_human_help", self._request_human_help_node)
        
        # ===== DEFINE WORKFLOW EDGES =====
        workflow.add_edge(START, "initialize_session")
        workflow.add_edge("initialize_session", "patient_greeting")
        workflow.add_edge("patient_greeting", "collect_patient_info")
        
        # Conditional routing after patient info collection
        workflow.add_conditional_edges(
            "collect_patient_info",
            self._route_after_patient_info,
            {
                "continue_to_lookup": "patient_lookup",
                "need_more_info": "collect_patient_info",
                "handle_error": "handle_error"
            }
        )
        
        workflow.add_edge("patient_lookup", "determine_appointment_type")
        workflow.add_edge("determine_appointment_type", "find_available_slots")
        
        # Conditional routing after slot search
        workflow.add_conditional_edges(
            "find_available_slots",
            self._route_after_slot_search,
            {
                "present_slots": "present_slot_options",
                "no_slots_available": "handle_error",
                "system_error": "handle_error"
            }
        )
        
        workflow.add_edge("present_slot_options", "confirm_slot_selection")
        
        # Conditional routing after slot confirmation
        workflow.add_conditional_edges(
            "confirm_slot_selection",
            self._route_after_slot_confirmation,
            {
                "proceed_to_insurance": "collect_insurance_info",
                "choose_different_slot": "present_slot_options",
                "handle_error": "handle_error"
            }
        )
        
        workflow.add_edge("collect_insurance_info", "create_calendar_booking")
        
        # Conditional routing after calendar booking
        workflow.add_conditional_edges(
            "create_calendar_booking",
            self._route_after_calendar_booking,
            {
                "booking_success": "generate_confirmation",
                "booking_failed": "handle_error",
                "need_human_help": "request_human_help"
            }
        )
        
        workflow.add_edge("generate_confirmation", "send_notifications")
        workflow.add_edge("send_notifications", "setup_reminders")
        workflow.add_edge("setup_reminders", "export_to_excel")
        workflow.add_edge("export_to_excel", END)
        
        # Error handling routes
        workflow.add_conditional_edges(
            "handle_error",
            self._route_error_handling,
            {
                "retry": "collect_patient_info",
                "escalate": "request_human_help",
                "end": END
            }
        )
        
        workflow.add_edge("request_human_help", END)
        
        # Compile the workflow
        compiled_graph = workflow.compile(
            checkpointer=self.memory if self.enable_persistence else None
        )
        
        logger.info("Workflow graph compiled successfully with Gemini integration")
        return compiled_graph
    
    # ============================================================================
    # NODE IMPLEMENTATIONS
    # ============================================================================
    
    def _initialize_session_node(self, state: AppointmentState) -> AppointmentState:
        """Initialize a new appointment booking session."""
        logger.info("Initializing new appointment booking session")
        
        current_time = datetime.now().isoformat()
        
        # Set initial state values
        updated_state = {
            "current_step": "greeting",
            "patient_info": {},
            "patient_type": "",
            "existing_patient_data": {},
            "appointment_duration": 0,
            "doctor_preference": "",
            "location_preference": "",
            "available_slots": [],
            "selected_slot": {},
            "insurance_data": {},
            "appointment_id": "",
            "confirmation_status": "pending",
            "calendar_booking_id": "",
            "error_message": "",
            "retry_count": 0,
            "needs_human_intervention": False,
            "export_data": {"session_started": current_time},
            "reminder_schedule": []
        }
        
        # Add system message if this is the first interaction
        if not state.get("messages"):
            system_msg = SystemMessage(
                content="""You are a professional and empathetic medical appointment scheduling assistant for MediCare Allergy & Wellness Center. 

Your primary goals:
1. Help patients book appointments efficiently
2. Collect all necessary information (name, DOB, doctor preference, insurance)
3. Provide excellent customer service with a warm, professional tone
4. Ensure data privacy and accuracy

Key guidelines:
- Always be polite and patient-focused
- Confirm information before proceeding
- Explain each step clearly
- Handle errors gracefully
- Maintain HIPAA-compliant communication standards

Current date: September 4, 2025
Clinic hours: Monday-Friday 9:00 AM - 5:00 PM
Available doctors: Dr. Johnson (Family Medicine), Dr. Smith (Cardiology), Dr. Williams (Dermatology), Dr. Brown (Orthopedics), Dr. Davis (Internal Medicine)"""
            )
            updated_state["messages"] = [system_msg]
        
        return {**state, **updated_state}
    
    def _patient_greeting_node(self, state: AppointmentState) -> AppointmentState:
        """Handle initial patient greeting and introduction using Gemini."""
        logger.info("Processing patient greeting with Gemini")
        
        try:
            # Get the last user message
            user_messages = [msg for msg in state.get("messages", []) if isinstance(msg, HumanMessage)]
            latest_user_input = user_messages[-1].content if user_messages else ""
            
            # Create a greeting prompt for Gemini
            greeting_prompt = f"""
            A patient has just contacted our medical appointment scheduling system. Their message is: "{latest_user_input}"

            Please respond as a professional medical receptionist with:
            1. A warm, welcoming greeting
            2. Confirmation that you'll help them schedule an appointment
            3. Start collecting basic information (name, date of birth, preferred doctor)
            4. Keep the tone professional but friendly
            5. Be concise but thorough

            If they haven't provided their name yet, ask for it first.
            """
            
            # Get response from Gemini
            response = self.llm.invoke([HumanMessage(content=greeting_prompt)])
            
            # Add the response to messages
            updated_state = {
                **state,
                "current_step": "collecting_info"
            }
            updated_state["messages"] = state["messages"] + [AIMessage(content=response.content)]
            
            return updated_state
            
        except Exception as e:
            logger.error(f"Error in patient greeting: {str(e)}")
            return {
                **state, 
                "error_message": f"Greeting error: {str(e)}",
                "current_step": "error"
            }
    
    def _collect_patient_info_node(self, state: AppointmentState) -> AppointmentState:
        """Collect and validate patient information using Gemini's NLP."""
        logger.info("Collecting patient information with Gemini")
        
        try:
            from agents.patient_info_collector import collect_patient_information_with_gemini
            result = collect_patient_information_with_gemini(state, self.llm)
            return result
        except Exception as e:
            logger.error(f"Error collecting patient info: {str(e)}")
            return {
                **state,
                "error_message": f"Info collection error: {str(e)}",
                "current_step": "error"
            }
    
    def _patient_lookup_node(self, state: AppointmentState) -> AppointmentState:
        """Search for existing patient records in the database."""
        from agents.patient_lookup import perform_patient_lookup
        logger.info("Looking up patient in database")
        
        try:
            result = perform_patient_lookup(state)
            result["current_step"] = "determining_type"
            return result
        except Exception as e:
            logger.error(f"Error in patient lookup: {str(e)}")
            return {
                **state,
                "error_message": f"Database lookup error: {str(e)}",
                "current_step": "error"
            }
    
    def _determine_appointment_type_node(self, state: AppointmentState) -> AppointmentState:
        """Determine appointment type and duration using Gemini."""
        logger.info("Determining appointment type with Gemini")
        
        try:
            patient_type = state.get("patient_type", "new")
            patient_name = state.get("patient_info", {}).get("name", "Patient")
            
            if patient_type == "returning":
                appointment_duration = 30
                appointment_type = "Follow-up Visit"
                message_content = f"Welcome back, {patient_name}! I'll schedule a 30-minute follow-up visit for you."
            else:
                appointment_duration = 60
                appointment_type = "New Patient Consultation"
                message_content = f"Hello {patient_name}! As a new patient, I'll schedule a comprehensive 60-minute consultation for you."
            
            # Use Gemini to create a personalized message
            personalization_prompt = f"""
            Create a brief, professional message for a {patient_type} patient named {patient_name} 
            confirming their {appointment_duration}-minute {appointment_type}. 
            Mention that you'll now look for available time slots.
            Keep it warm and professional, under 50 words.
            """
            
            response = self.llm.invoke([HumanMessage(content=personalization_prompt)])
            
            updated_state = {
                **state,
                "appointment_duration": appointment_duration,
                "appointment_type": appointment_type,
                "current_step": "finding_slots"
            }
            
            updated_state["messages"] = state["messages"] + [AIMessage(content=response.content)]
            
            return updated_state
            
        except Exception as e:
            logger.error(f"Error determining appointment type: {str(e)}")
            return {
                **state,
                "error_message": f"Appointment type error: {str(e)}",
                "current_step": "error"
            }
    
    def _find_available_slots_node(self, state: AppointmentState) -> AppointmentState:
        """Search for available appointment slots."""
        from agents.scheduling import find_available_appointment_slots
        logger.info("Searching for available appointment slots")
        
        try:
            result = find_available_appointment_slots(state)
            result["current_step"] = "presenting_slots"
            return result
        except Exception as e:
            logger.error(f"Error finding slots: {str(e)}")
            return {
                **state,
                "error_message": f"Slot search error: {str(e)}",
                "current_step": "error"
            }
    
    def _present_slot_options_node(self, state: AppointmentState) -> AppointmentState:
        """Present available slot options using Gemini."""
        logger.info("Presenting appointment slot options with Gemini")
        
        try:
            available_slots = state.get("available_slots", [])
            patient_name = state.get("patient_info", {}).get("name", "")
            
            if not available_slots:
                return {
                    **state,
                    "error_message": "No available slots found",
                    "current_step": "error"
                }
            
            # Format slots for Gemini to present
            slots_text = ""
            for i, slot in enumerate(available_slots[:5], 1):  # Show top 5 slots
                date = slot.get("date", "")
                time = slot.get("start_time", "")
                doctor = slot.get("doctor_name", "")
                slots_text += f"{i}. {date} at {time} with {doctor}\n"
            
            slot_presentation_prompt = f"""
            Present these available appointment slots to {patient_name} in a friendly, professional manner:

            {slots_text}

            Ask them to choose their preferred option by number, or ask if they'd like to see different times.
            Keep it conversational and helpful.
            """
            
            response = self.llm.invoke([HumanMessage(content=slot_presentation_prompt)])
            
            updated_state = {
                **state,
                "current_step": "confirming_slot"
            }
            updated_state["messages"] = state["messages"] + [AIMessage(content=response.content)]
            
            return updated_state
            
        except Exception as e:
            logger.error(f"Error presenting slots: {str(e)}")
            return {
                **state,
                "error_message": f"Slot presentation error: {str(e)}",
                "current_step": "error"
            }
    
    def _confirm_slot_selection_node(self, state: AppointmentState) -> AppointmentState:
        """Confirm the patient's slot selection using Gemini."""
        from agents.scheduling import confirm_slot_selection_with_gemini
        logger.info("Confirming appointment slot selection with Gemini")
        
        try:
            result = confirm_slot_selection_with_gemini(state, self.llm)
            return result
        except Exception as e:
            logger.error(f"Error confirming slot: {str(e)}")
            return {
                **state,
                "error_message": f"Slot confirmation error: {str(e)}",
                "current_step": "error"
            }
    
    def _collect_insurance_info_node(self, state: AppointmentState) -> AppointmentState:
        """Collect patient insurance information using Gemini."""
        from agents.insurance_collector import collect_insurance_information_with_gemini
        logger.info("Collecting insurance information with Gemini")
        
        try:
            result = collect_insurance_information_with_gemini(state, self.llm)
            result["current_step"] = "creating_booking"
            return result
        except Exception as e:
            logger.error(f"Error collecting insurance: {str(e)}")
            return {
                **state,
                "error_message": f"Insurance collection error: {str(e)}",
                "current_step": "error"
            }
    
    def _create_calendar_booking_node(self, state: AppointmentState) -> AppointmentState:
        """Create the actual calendar booking."""
        from integrations.calendar_integration import create_appointment_booking
        logger.info("Creating calendar booking")
        
        try:
            result = create_appointment_booking(state)
            result["current_step"] = "generating_confirmation"
            return result
        except Exception as e:
            logger.error(f"Error creating booking: {str(e)}")
            return {
                **state,
                "error_message": f"Calendar booking error: {str(e)}",
                "current_step": "error"
            }
    
    def _generate_confirmation_node(self, state: AppointmentState) -> AppointmentState:
        """Generate appointment confirmation using Gemini."""
        logger.info("Generating appointment confirmation with Gemini")
        
        try:
            from agents.confirmation import generate_appointment_confirmation_with_gemini
            result = generate_appointment_confirmation_with_gemini(state, self.llm)
            result["current_step"] = "sending_notifications"
            return result
        except Exception as e:
            logger.error(f"Error generating confirmation: {str(e)}")
            return {
                **state,
                "error_message": f"Confirmation generation error: {str(e)}",
                "current_step": "error"
            }
    
    def _send_notifications_node(self, state: AppointmentState) -> AppointmentState:
        """Send confirmation notifications via email and SMS."""
        from integrations.communications import send_appointment_notifications
        logger.info("Sending appointment notifications")
        
        try:
            result = send_appointment_notifications(state)
            result["current_step"] = "setting_reminders"
            return result
        except Exception as e:
            logger.error(f"Error sending notifications: {str(e)}")
            return {
                **state,
                "error_message": f"Notification error: {str(e)}",
                "current_step": "error"
            }
    
    def _setup_reminders_node(self, state: AppointmentState) -> AppointmentState:
        """Setup the 3-tier reminder system."""
        from integrations.communications import setup_reminder_system
        logger.info("Setting up reminder system")
        
        try:
            result = setup_reminder_system(state)
            result["current_step"] = "exporting_data"
            return result
        except Exception as e:
            logger.error(f"Error setting up reminders: {str(e)}")
            return {
                **state,
                "error_message": f"Reminder setup error: {str(e)}",
                "current_step": "error"
            }
    
    def _export_to_excel_node(self, state: AppointmentState) -> AppointmentState:
        """Export appointment data to Excel for admin review."""
        from integrations.excel_export import export_appointment_data
        logger.info("Exporting appointment data to Excel")
        
        try:
            result = export_appointment_data(state)
            result["current_step"] = "completed"
            result["confirmation_status"] = "confirmed"
            
            # Use Gemini to create final success message
            success_prompt = f"""
            Create a final confirmation message for a patient whose appointment has been successfully booked.
            Include:
            1. Confirmation that everything is complete
            2. Mention they'll receive email confirmation and reminders
            3. Thank them for choosing MediCare Allergy & Wellness Center
            4. Remind them to complete intake forms when they receive them
            Keep it professional, warm, and concise.
            """
            
            final_response = self.llm.invoke([HumanMessage(content=success_prompt)])
            result["messages"] = state["messages"] + [AIMessage(content=final_response.content)]
            
            return result
        except Exception as e:
            logger.error(f"Error exporting data: {str(e)}")
            return {
                **state,
                "error_message": f"Excel export error: {str(e)}",
                "current_step": "error"
            }
    
    def _handle_error_node(self, state: AppointmentState) -> AppointmentState:
        """Handle errors using Gemini to create helpful error messages."""
        logger.warning(f"Handling error: {state.get('error_message', 'Unknown error')}")
        
        retry_count = state.get("retry_count", 0) + 1
        error_msg = state.get('error_message', 'An unexpected error occurred')
        
        # Use Gemini to create a helpful error response
        error_prompt = f"""
        Create a professional, empathetic response for this error situation: {error_msg}
        
        The response should:
        1. Apologize for the inconvenience
        2. Offer to try again or help in a different way
        3. Maintain confidence that we can resolve the issue
        4. Keep the tone calm and professional
        5. Be under 50 words
        """
        
        try:
            error_response = self.llm.invoke([HumanMessage(content=error_prompt)])
            response_content = error_response.content
        except:
            response_content = "I apologize for the technical difficulty. Let me try to help you in a different way."
        
        return {
            **state,
            "retry_count": retry_count,
            "messages": state["messages"] + [AIMessage(content=response_content)],
            "current_step": "error_handled"
        }
    
    def _request_human_help_node(self, state: AppointmentState) -> AppointmentState:
        """Request human intervention using Gemini."""
        logger.info("Requesting human intervention")
        
        escalation_prompt = """
        Create a professional message explaining that the system needs to connect the patient 
        with a human scheduling specialist. The message should:
        1. Apologize for not being able to complete the booking automatically
        2. Assure them a specialist will assist shortly
        3. Thank them for their patience
        4. Keep it professional and reassuring
        """
        
        try:
            escalation_response = self.llm.invoke([HumanMessage(content=escalation_prompt)])
            response_content = escalation_response.content
        except:
            response_content = "I'm having difficulty completing your appointment booking automatically. I'm connecting you with one of our scheduling specialists who will assist you shortly. Please hold on."
        
        return {
            **state,
            "needs_human_intervention": True,
            "messages": state["messages"] + [AIMessage(content=response_content)],
            "current_step": "escalated"
        }
    
    # ============================================================================
    # CONDITIONAL ROUTING FUNCTIONS (same as before)
    # ============================================================================
    
    def _route_after_patient_info(self, state: AppointmentState) -> Literal["continue_to_lookup", "need_more_info", "handle_error"]:
        """Route based on patient information completeness."""
        patient_info = state.get("patient_info", {})
        
        required_fields = ["name", "dob", "phone"]
        missing_fields = [field for field in required_fields if not patient_info.get(field)]
        
        if state.get("error_message"):
            return "handle_error"
        elif missing_fields:
            return "need_more_info"
        else:
            return "continue_to_lookup"
    
    def _route_after_slot_search(self, state: AppointmentState) -> Literal["present_slots", "no_slots_available", "system_error"]:
        """Route based on slot search results."""
        if state.get("error_message"):
            return "system_error"
        elif state.get("available_slots"):
            return "present_slots"
        else:
            return "no_slots_available"
    
    def _route_after_slot_confirmation(self, state: AppointmentState) -> Literal["proceed_to_insurance", "choose_different_slot", "handle_error"]:
        """Route based on slot confirmation status."""
        if state.get("error_message"):
            return "handle_error"
        elif state.get("selected_slot"):
            return "proceed_to_insurance"
        else:
            return "choose_different_slot"
    
    def _route_after_calendar_booking(self, state: AppointmentState) -> Literal["booking_success", "booking_failed", "need_human_help"]:
        """Route based on calendar booking results."""
        if state.get("needs_human_intervention"):
            return "need_human_help"
        elif state.get("error_message"):
            return "booking_failed"
        elif state.get("calendar_booking_id"):
            return "booking_success"
        else:
            return "booking_failed"
    
    def _route_error_handling(self, state: AppointmentState) -> Literal["retry", "escalate", "end"]:
        """Route error handling based on retry count and error type."""
        retry_count = state.get("retry_count", 0)
        
        if retry_count >= 3:
            return "escalate"
        elif state.get("needs_human_intervention"):
            return "escalate"
        else:
            return "retry"
    
    # ============================================================================
    # PUBLIC INTERFACE METHODS
    # ============================================================================
    
    def run_conversation(self, user_input: str, thread_id: str = "default") -> Dict[str, Any]:
        """
        Process a single user input through the workflow using Gemini.
        """
        config = {"configurable": {"thread_id": thread_id}}
        
        try:
            user_message = HumanMessage(content=user_input)
            
            result = self.graph.invoke(
                {"messages": [user_message]},
                config=config
            )
            
            # Extract the last assistant message
            last_message = None
            for msg in reversed(result["messages"]):
                if isinstance(msg, AIMessage):
                    last_message = msg
                    break
            
            return {
                "response": last_message.content if last_message else "I'm having trouble processing your request.",
                "state": result,
                "status": "success"
            }
            
        except Exception as e:
            logger.error(f"Error in run_conversation: {str(e)}")
            return {
                "response": "I apologize, but I'm experiencing technical difficulties. Please try again or contact our support team.",
                "state": {},
                "status": "error",
                "error": str(e)
            }
    
    def stream_conversation(self, user_input: str, thread_id: str = "default"):
        """
        Stream the conversation response for real-time UI updates.
        """
        config = {"configurable": {"thread_id": thread_id}}
        
        try:
            user_message = HumanMessage(content=user_input)
            
            for event in self.graph.stream(
                {"messages": [user_message]},
                config=config,
                stream_mode="values"
            ):
                if event.get("messages"):
                    last_message = event["messages"][-1]
                    if isinstance(last_message, AIMessage):
                        yield last_message.content
                        
        except Exception as e:
            logger.error(f"Error in stream_conversation: {str(e)}")
            yield f"Error: {str(e)}"

# ============================================================================
# FACTORY FUNCTIONS
# ============================================================================

def create_gemini_agent(
    model_name: str = "gemini-pro", 
    temperature: float = 0.3,
    api_key: str = None
) -> MedicalSchedulingAgent:
    """
    Create an agent instance using Google's Gemini API.
    
    Args:
        model_name: Gemini model to use (gemini-pro, gemini-pro-vision)
        temperature: Model creativity level (0.0 to 1.0)
        api_key: Google API key (if not in environment)
        
    Returns:
        Configured MedicalSchedulingAgent instance
    """
    if api_key:
        os.environ["GOOGLE_API_KEY"] = api_key
    
    return MedicalSchedulingAgent(
        gemini_model=model_name,
        temperature=temperature,
        enable_persistence=True
    )

# ============================================================================
# MAIN EXECUTION (FOR TESTING)
# ============================================================================

if __name__ == "__main__":
    print("Initializing Medical Scheduling Agent with Gemini...")
    
    try:
        # Create agent with Gemini
        agent = create_gemini_agent(model_name="gemini-pro", temperature=0.3)
        
        print("\n=== Testing Agent Functionality with Gemini ===")
        
        test_cases = [
            "Hi, I'd like to book an appointment",
            "My name is John Smith, DOB is 01/15/1985, and I'd like to see Dr. Johnson",
            "I prefer morning appointments if possible"
        ]
        
        thread_id = "test-gemini-session-001"
        
        for i, test_input in enumerate(test_cases, 1):
            print(f"\n--- Test {i} ---")
            print(f"User: {test_input}")
            
            result = agent.run_conversation(test_input, thread_id)
            print(f"Agent: {result['response']}")
            print(f"Status: {result['status']}")
        
        print("\n=== Gemini Agent Testing Complete ===")
        
    except Exception as e:
        print(f"Error initializing Gemini agent: {str(e)}")
        print("Please ensure GOOGLE_API_KEY is set in your .env file")
