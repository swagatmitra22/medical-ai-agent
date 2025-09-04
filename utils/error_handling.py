"""
Error Handling Module - Medical Appointment Scheduling System
==========================================================

This module provides comprehensive error handling, logging, and exception management
for the medical appointment scheduling AI system. It includes custom exception classes,
decorators, context managers, and centralized logging capabilities.

Key Features:
- Custom exception hierarchy for medical scheduling operations
- Centralized error logging with file and console output
- Decorator-based error handling for functions
- Context manager for block-level error handling
- Integration with LangGraph workflow error management
- Graceful degradation and fallback mechanisms
- HIPAA-compliant error logging (no sensitive data)

Author: RagaAI Case Study Implementation
Date: September 2025
"""

import os
import sys
import logging
import traceback
import functools
from typing import Any, Callable, Optional, Dict, List
from datetime import datetime
from contextlib import contextmanager

# ============================================================================
# LOGGING SETUP
# ============================================================================

# Ensure logs directory exists
LOGS_DIR = "logs"
if not os.path.exists(LOGS_DIR):
    os.makedirs(LOGS_DIR)

# Configure logging
def setup_logging():
    """Setup comprehensive logging configuration."""
    
    # Create logger
    logger = logging.getLogger('medical_ai_agent')
    logger.setLevel(logging.DEBUG)
    
    # Prevent duplicate logs
    if logger.handlers:
        return logger
    
    # File handler for errors
    error_file_handler = logging.FileHandler(
        os.path.join(LOGS_DIR, 'error.log'),
        mode='a',
        encoding='utf-8'
    )
    error_file_handler.setLevel(logging.ERROR)
    
    # File handler for general logs
    general_file_handler = logging.FileHandler(
        os.path.join(LOGS_DIR, 'medical_agent.log'),
        mode='a',
        encoding='utf-8'
    )
    general_file_handler.setLevel(logging.INFO)
    
    # Console handler
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(logging.INFO)
    
    # Formatter
    formatter = logging.Formatter(
        '%(asctime)s | %(name)s | %(levelname)s | %(funcName)s:%(lineno)d | %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    
    # Apply formatters
    error_file_handler.setFormatter(formatter)
    general_file_handler.setFormatter(formatter)
    console_handler.setFormatter(formatter)
    
    # Add handlers to logger
    logger.addHandler(error_file_handler)
    logger.addHandler(general_file_handler)
    logger.addHandler(console_handler)
    
    return logger

# Initialize logger
logger = setup_logging()

# ============================================================================
# CUSTOM EXCEPTION CLASSES
# ============================================================================

class MedicalAgentError(Exception):
    """Base exception class for all medical agent errors."""
    
    def __init__(self, message: str, error_code: Optional[str] = None, context: Optional[Dict] = None):
        """
        Initialize medical agent error.
        
        Args:
            message: Error description
            error_code: Optional error code for categorization
            context: Optional context dictionary (sanitized, no PHI)
        """
        super().__init__(message)
        self.message = message
        self.error_code = error_code
        self.context = context or {}
        self.timestamp = datetime.now()
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert error to dictionary for logging."""
        return {
            'error_type': self.__class__.__name__,
            'message': self.message,
            'error_code': self.error_code,
            'context': self.context,
            'timestamp': self.timestamp.isoformat()
        }

class PatientDataError(MedicalAgentError):
    """Exception raised for patient data validation and processing errors."""
    pass

class SchedulingError(MedicalAgentError):
    """Exception raised for appointment scheduling errors."""
    pass

class CalendarIntegrationError(MedicalAgentError):
    """Exception raised for calendar integration failures."""
    pass

class CommunicationError(MedicalAgentError):
    """Exception raised for email/SMS communication failures."""
    pass

class ValidationError(MedicalAgentError):
    """Exception raised for data validation failures."""
    pass

class DatabaseError(MedicalAgentError):
    """Exception raised for database operation failures."""
    pass

class ExternalServiceError(MedicalAgentError):
    """Exception raised for external service integration failures."""
    pass

class LangGraphError(MedicalAgentError):
    """Exception raised for LangGraph workflow errors."""
    pass

class ConfigurationError(MedicalAgentError):
    """Exception raised for configuration and setup errors."""
    pass

class AuthenticationError(MedicalAgentError):
    """Exception raised for authentication and authorization errors."""
    pass

# ============================================================================
# ERROR HANDLER CLASS
# ============================================================================

class ErrorHandler:
    """
    Centralized error handler for the medical appointment scheduling system.
    """
    
    def __init__(self, logger_instance: Optional[logging.Logger] = None):
        """
        Initialize error handler.
        
        Args:
            logger_instance: Optional logger instance, uses default if not provided
        """
        self.logger = logger_instance or logger
        self.error_counts = {}
        self.recent_errors = []
        self.max_recent_errors = 100
    
    def log_error(self, 
                  error: Exception, 
                  context: Optional[str] = None, 
                  additional_info: Optional[Dict] = None) -> None:
        """
        Log error with comprehensive information.
        
        Args:
            error: The exception that occurred
            context: Optional context string
            additional_info: Optional additional information dictionary
        """
        try:
            # Sanitize additional info to remove any PHI
            sanitized_info = self._sanitize_info(additional_info or {})
            
            # Create error entry
            error_entry = {
                'timestamp': datetime.now().isoformat(),
                'error_type': type(error).__name__,
                'error_message': str(error),
                'context': context,
                'additional_info': sanitized_info,
                'traceback': traceback.format_exc() if context != 'suppress_traceback' else None
            }
            
            # Log the error
            if isinstance(error, MedicalAgentError):
                self.logger.error(f"Medical Agent Error in {context or 'unknown context'}: {error.message}")
                if error.error_code:
                    self.logger.error(f"Error Code: {error.error_code}")
                if error.context:
                    self.logger.error(f"Error Context: {error.context}")
            else:
                self.logger.error(f"Unexpected Error in {context or 'unknown context'}: {str(error)}")
                self.logger.error(f"Error Type: {type(error).__name__}")
            
            # Log traceback for debugging
            if context != 'suppress_traceback':
                self.logger.debug(f"Traceback: {traceback.format_exc()}")
            
            # Track error statistics
            error_type = type(error).__name__
            self.error_counts[error_type] = self.error_counts.get(error_type, 0) + 1
            
            # Maintain recent errors list
            self.recent_errors.append(error_entry)
            if len(self.recent_errors) > self.max_recent_errors:
                self.recent_errors.pop(0)
                
        except Exception as logging_error:
            # Fallback logging in case error logging itself fails
            print(f"ERROR IN ERROR LOGGING: {logging_error}")
            print(f"Original error: {error}")
    
    def _sanitize_info(self, info: Dict) -> Dict:
        """
        Sanitize information dictionary to remove potential PHI.
        
        Args:
            info: Dictionary to sanitize
            
        Returns:
            Sanitized dictionary
        """
        # List of keys that might contain PHI
        phi_keys = [
            'patient_name', 'name', 'first_name', 'last_name',
            'email', 'phone', 'ssn', 'dob', 'date_of_birth',
            'address', 'medical_record_number', 'mrn'
        ]
        
        sanitized = {}
        for key, value in info.items():
            if key.lower() in phi_keys:
                sanitized[key] = '[REDACTED]'
            elif isinstance(value, str) and len(value) > 0:
                # Simple heuristic to detect potential PHI
                if '@' in value and '.' in value:  # Potential email
                    sanitized[key] = '[EMAIL_REDACTED]'
                elif value.replace('-', '').replace('(', '').replace(')', '').replace(' ', '').isdigit():  # Potential phone
                    sanitized[key] = '[PHONE_REDACTED]'
                else:
                    sanitized[key] = value
            else:
                sanitized[key] = value
        
        return sanitized
    
    def get_error_statistics(self) -> Dict[str, Any]:
        """Get error statistics for monitoring."""
        return {
            'error_counts': self.error_counts,
            'total_errors': sum(self.error_counts.values()),
            'recent_error_count': len(self.recent_errors),
            'most_common_errors': sorted(self.error_counts.items(), key=lambda x: x[1], reverse=True)
        }
    
    def clear_statistics(self) -> None:
        """Clear error statistics."""
        self.error_counts.clear()
        self.recent_errors.clear()

# Global error handler instance
error_handler = ErrorHandler()

# ============================================================================
# DECORATORS
# ============================================================================

def handle_exceptions(context: Optional[str] = None, 
                     reraise: bool = False, 
                     fallback_return: Any = None,
                     suppress_traceback: bool = False):
    """
    Decorator to handle exceptions in functions.
    
    Args:
        context: Context string for error logging
        reraise: Whether to reraise the exception after logging
        fallback_return: Value to return if exception occurs and not reraising
        suppress_traceback: Whether to suppress traceback in logs
        
    Returns:
        Decorated function
    """
    def decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        def wrapper(*args, **kwargs) -> Any:
            try:
                return func(*args, **kwargs)
            except Exception as e:
                error_context = context or f"{func.__module__}.{func.__name__}"
                if suppress_traceback:
                    error_context = 'suppress_traceback'
                
                error_handler.log_error(e, error_context)
                
                if reraise:
                    raise
                else:
                    return fallback_return
        return wrapper
    return decorator

def log_exceptions(context: Optional[str] = None):
    """
    Decorator to log exceptions without affecting function flow.
    
    Args:
        context: Context string for error logging
        
    Returns:
        Decorated function
    """
    def decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        def wrapper(*args, **kwargs) -> Any:
            try:
                return func(*args, **kwargs)
            except Exception as e:
                error_context = context or f"{func.__module__}.{func.__name__}"
                error_handler.log_error(e, error_context)
                raise  # Re-raise the exception
        return wrapper
    return decorator

def retry_on_failure(max_retries: int = 3, 
                    delay: float = 1.0, 
                    exceptions: tuple = (Exception,)):
    """
    Decorator to retry function execution on failure.
    
    Args:
        max_retries: Maximum number of retry attempts
        delay: Delay between retries in seconds
        exceptions: Tuple of exception types to catch and retry
        
    Returns:
        Decorated function
    """
    def decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        def wrapper(*args, **kwargs) -> Any:
            import time
            
            last_exception = None
            
            for attempt in range(max_retries + 1):
                try:
                    return func(*args, **kwargs)
                except exceptions as e:
                    last_exception = e
                    
                    if attempt < max_retries:
                        error_handler.log_error(
                            e, 
                            f"{func.__name__} - Attempt {attempt + 1}/{max_retries + 1}",
                            {'attempt': attempt + 1, 'max_retries': max_retries + 1}
                        )
                        time.sleep(delay)
                    else:
                        error_handler.log_error(
                            e, 
                            f"{func.__name__} - All retry attempts failed"
                        )
                        raise
            
            # This should never be reached, but just in case
            if last_exception:
                raise last_exception
                
        return wrapper
    return decorator

# ============================================================================
# CONTEXT MANAGERS
# ============================================================================

@contextmanager
def error_context(context_name: str, 
                 suppress_errors: bool = False, 
                 fallback_result: Any = None):
    """
    Context manager for error handling in code blocks.
    
    Args:
        context_name: Name of the context for error logging
        suppress_errors: Whether to suppress errors (return fallback_result)
        fallback_result: Result to return if errors are suppressed
        
    Yields:
        Dictionary that can be used to access error information
    """
    error_info = {'error': None, 'result': None}
    
    try:
        yield error_info
    except Exception as e:
        error_info['error'] = e
        error_handler.log_error(e, context_name)
        
        if suppress_errors:
            error_info['result'] = fallback_result
        else:
            raise

@contextmanager
def graceful_degradation(context_name: str, 
                        fallback_function: Optional[Callable] = None):
    """
    Context manager for graceful degradation on errors.
    
    Args:
        context_name: Name of the context for error logging
        fallback_function: Optional fallback function to call on error
        
    Yields:
        Dictionary containing error and result information
    """
    result = {'error': None, 'result': None, 'degraded': False}
    
    try:
        yield result
    except Exception as e:
        result['error'] = e
        result['degraded'] = True
        
        error_handler.log_error(e, f"{context_name} - Graceful degradation activated")
        
        if fallback_function:
            try:
                result['result'] = fallback_function()
                logger.info(f"Fallback function executed successfully in {context_name}")
            except Exception as fallback_error:
                error_handler.log_error(
                    fallback_error, 
                    f"{context_name} - Fallback function failed"
                )

# ============================================================================
# UTILITY FUNCTIONS
# ============================================================================

def log_error(error: Exception, 
              context: Optional[str] = None, 
              additional_info: Optional[Dict] = None) -> None:
    """
    Convenience function to log errors using the global error handler.
    
    Args:
        error: The exception that occurred
        context: Optional context string
        additional_info: Optional additional information dictionary
    """
    error_handler.log_error(error, context, additional_info)

def handle_graceful_degradation(primary_function: Callable, 
                               fallback_function: Callable, 
                               context: str) -> Any:
    """
    Execute primary function with graceful degradation to fallback.
    
    Args:
        primary_function: Primary function to execute
        fallback_function: Fallback function if primary fails
        context: Context string for logging
        
    Returns:
        Result from primary function or fallback function
    """
    try:
        return primary_function()
    except Exception as e:
        error_handler.log_error(e, f"{context} - Primary function failed, using fallback")
        try:
            return fallback_function()
        except Exception as fallback_error:
            error_handler.log_error(fallback_error, f"{context} - Fallback function also failed")
            raise

def create_error_response(error: Exception, 
                         context: str = "", 
                         user_friendly: bool = True) -> Dict[str, Any]:
    """
    Create standardized error response dictionary.
    
    Args:
        error: The exception that occurred
        context: Context string
        user_friendly: Whether to include user-friendly messages
        
    Returns:
        Standardized error response dictionary
    """
    error_response = {
        'success': False,
        'error_type': type(error).__name__,
        'context': context,
        'timestamp': datetime.now().isoformat()
    }
    
    if user_friendly:
        # Map technical errors to user-friendly messages
        user_messages = {
            'PatientDataError': 'There was an issue with the patient information provided.',
            'SchedulingError': 'Unable to schedule the appointment at this time.',
            'CalendarIntegrationError': 'Calendar service is temporarily unavailable.',
            'CommunicationError': 'Unable to send notifications at this time.',
            'ValidationError': 'Please check the information provided and try again.',
            'DatabaseError': 'Service temporarily unavailable. Please try again later.',
            'ExternalServiceError': 'External service temporarily unavailable.',
            'AuthenticationError': 'Authentication failed. Please check your credentials.',
            'ConfigurationError': 'System configuration issue. Please contact support.'
        }
        
        error_response['user_message'] = user_messages.get(
            type(error).__name__, 
            'An unexpected error occurred. Please try again or contact support.'
        )
    else:
        error_response['technical_message'] = str(error)
    
    return error_response

def validate_environment() -> List[str]:
    """
    Validate environment setup and return list of issues.
    
    Returns:
        List of environment issues found
    """
    issues = []
    
    # Check logs directory
    if not os.path.exists(LOGS_DIR):
        issues.append(f"Logs directory '{LOGS_DIR}' does not exist")
    elif not os.access(LOGS_DIR, os.W_OK):
        issues.append(f"Logs directory '{LOGS_DIR}' is not writable")
    
    # Check required environment variables
    required_env_vars = ['GOOGLE_API_KEY']
    for var in required_env_vars:
        if not os.getenv(var):
            issues.append(f"Required environment variable '{var}' is not set")
    
    return issues

# ============================================================================
# TESTING FUNCTIONS
# ============================================================================

def test_error_handling():
    """Test function to validate error handling functionality."""
    
    print("Testing Error Handling System")
    print("=" * 50)
    
    # Test custom exceptions
    print("\n1. Testing Custom Exceptions:")
    try:
        raise PatientDataError("Test patient data error", error_code="PD001")
    except PatientDataError as e:
        error_handler.log_error(e, "test_custom_exception")
        print(f"✅ Custom exception logged: {e.message}")
    
    # Test decorator
    print("\n2. Testing Error Decorator:")
    
    @handle_exceptions(context="test_decorator", fallback_return="fallback_result")
    def test_function(should_fail: bool = False):
        if should_fail:
            raise ValueError("Test error")
        return "success"
    
    result1 = test_function(False)
    result2 = test_function(True)
    print(f"✅ Decorator test - Success: {result1}, Failure: {result2}")
    
    # Test context manager
    print("\n3. Testing Context Manager:")
    with error_context("test_context", suppress_errors=True, fallback_result="context_fallback") as ctx:
        raise RuntimeError("Test context error")
    
    print(f"✅ Context manager - Error: {type(ctx['error']).__name__}, Result: {ctx['result']}")
    
    # Test graceful degradation
    print("\n4. Testing Graceful Degradation:")
    
    def primary_func():
        raise ConnectionError("Primary function failed")
    
    def fallback_func():
        return "fallback_executed"
    
    result = handle_graceful_degradation(primary_func, fallback_func, "test_graceful_degradation")
    print(f"✅ Graceful degradation result: {result}")
    
    # Test error statistics
    print("\n5. Testing Error Statistics:")
    stats = error_handler.get_error_statistics()
    print(f"✅ Error statistics: {stats['total_errors']} total errors")
    for error_type, count in stats['most_common_errors']:
        print(f"   {error_type}: {count}")
    
    print("\n" + "=" * 50)
    print("Error handling system test completed!")

if __name__ == "__main__":
    # Run tests when executed directly
    test_error_handling()
