# Medical AI Agent

The **Medical AI Agent** is an intelligent, AI-powered system designed to streamline the process of medical appointment scheduling. It leverages advanced natural language processing (NLP) models, workflow orchestration, and integrations with external systems to provide a seamless experience for both patients and healthcare providers.

---

## Table of Contents
1. [Overview](#overview)
2. [Features](#features)
3. [System Architecture](#system-architecture)
4. [Core Components](#core-components)
5. [Installation](#installation)
6. [Usage](#usage)
7. [File Structure](#file-structure)
8. [License](#license)

---

## Overview

The **Medical AI Agent** is built to:
- Assist patients in booking appointments efficiently.
- Collect and validate patient information.
- Handle errors gracefully and escalate to human intervention when necessary.
- Automate notifications, reminders, and data exports for administrative purposes.

### Key Technologies:
- **LangGraph**: Multi-agent workflow orchestration.
- **LangChain**: LLM integration and tools.
- **Google Gemini**: Advanced NLP for natural conversations.
- **Streamlit**: Web-based user interface.
- **Pandas**: Data manipulation and analysis.
- **OpenPyXL**: Excel file operations.
- **Twilio**: SMS messaging service.
- **SMTP**: Email delivery system.

---

## Features

### Patient-Facing Features:
- **Smart Patient Classification**: Automatically detects new vs. returning patients.
- **Dynamic Scheduling**: Handles 60-minute new patient consultations and 30-minute follow-ups.
- **Multi-Channel Communication**: Sends email confirmations and SMS reminders.
- **Error Handling**: Provides clear, empathetic responses for errors.

### Admin-Facing Features:
- **Excel Integration**: Exports appointment data for reporting.
- **Analytics Dashboard**: Real-time insights into clinic operations.
- **3-Tier Reminder System**: Sends reminders 24 hours, 4 hours, and 1 hour before appointments.

---

## System Architecture

The system is built around a **stateful workflow** using LangGraph. The workflow includes the following steps:
1. **Patient Greeting**: Welcomes the patient and collects basic information.
2. **Patient Lookup**: Searches the database for existing patient records.
3. **Appointment Scheduling**: Finds and confirms appointment slots.
4. **Insurance Collection**: Collects insurance details if required.
5. **Confirmation and Notifications**: Sends appointment confirmations via email/SMS.
6. **Reminders**: Sets up automated reminders.
7. **Data Export**: Exports data to Excel for administrative use.

### Workflow Diagram:
```plaintext
START -> Patient Greeting -> Collect Patient Info -> Patient Lookup -> Determine Appointment Type
      -> Find Available Slots -> Present Slot Options -> Confirm Slot Selection -> Collect Insurance Info
      -> Create Calendar Booking -> Generate Confirmation -> Send Notifications -> Setup Reminders -> Export Data -> END
```

---

## Core Components

### Agents
- **Patient Greeting Agent**: Handles initial interactions with patients.
- **Patient Info Collector**: Collects and validates patient information.
- **Scheduling Agent**: Finds and confirms appointment slots.
- **Insurance Collector**: Collects insurance details.
- **Confirmation Agent**: Generates appointment confirmations.

### Integrations
- **Google Gemini**: For natural language understanding and response generation.
- **Twilio**: For SMS notifications.
- **SMTP**: For email notifications.
- **OpenPyXL**: For exporting data to Excel.

### Utilities
- **Error Handling**: Comprehensive logging and graceful error recovery.
- **Data Generators**: Tools for generating sample data for testing.

---

## Installation

### Prerequisites
- Python 3.9+
- Pipenv or virtualenv for dependency management.
- `.env` file with the following keys  - `GOOGLE_API_KEY`
  - `GROQ_API_KEY`
  - `TWILIO_ACCOUNT_SID`
  - `TWILIO_AUTH_TOKEN`
  - `SMTP_SERVER`, `SMTP_PORT`, `SMTP_USER`, `SMTP_PASSWORD`

### Steps
1. Clone the repository:
   ```bash
   git clone https://github.com/your-repo/medical-ai-agent.git
   cd medical-ai-agent
   ```

2. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

3. Set up the `.env` file:
   ```plaintext
   GOOGLE_API_KEY=your_google_api_key
   GROQ_API_KEY=your_groq_api_key
   TWILIO_ACCOUNT_SID=your_twilio_account_sid
   TWILIO_AUTH_TOKEN=your_twilio_auth_token
   SMTP_SERVER=smtp.example.com
   SMTP_PORT=587
   SMTP_USER=your_email@example.com
   SMTP_PASSWORD=your_email_password
   ```

4. Run the application:
   ```bash
   streamlit run app.py
   ```

---

## Usage

### Running the Application
1. Start the Streamlit app:
   ```bash
   streamlit run app.py
   ```
2. Open the app in your browser at `http://localhost:8501`.

### Testing the Agent
You can test the agent's functionality by interacting with the chatbot in the "Patient Chat" section of the app. Example inputs:
- "Hi, I'd like to book an appointment."
- "My name is John Doe, DOB 01/01/1980, and I want to see Dr. Smith."

---

## License

This project is licensed under the **Apache License 2.0**. See the [LICENSE](LICENSE) file for details.

---

## Contact

**🏥 MediCare Allergy & Wellness Center**  
📍 Address: 456 Healthcare Boulevard, Suite 300  
📞 Phone: (555) 123-4567  
📧 Email: appointments@medicare-wellness.com  
🌐 Website: [www.medicare-wellness.com](http://www.medicare-wellness.com)

**Business Hours:**
- Monday - Friday: 8:00 AM - 6:00 PM
- Saturday: 9:00 AM - 2:00 PM
- Sunday: Closed