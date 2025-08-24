"""
Custom Exceptions for Web Automation System

This module defines custom exception classes used throughout the
web automation system for better error handling and debugging.
"""


class WebAutomationError(Exception):
    """Base exception for web automation errors."""
    pass


class BrowserError(WebAutomationError):
    """Exception raised for browser-related errors."""
    pass


class ElementNotFoundError(WebAutomationError):
    """Exception raised when a DOM element cannot be found."""
    pass


class AuthenticationError(WebAutomationError):
    """Exception raised for authentication failures."""
    pass


class TaskExecutionError(WebAutomationError):
    """Exception raised when task execution fails."""
    pass


class ProviderError(WebAutomationError):
    """Exception raised for provider-specific errors."""
    pass


class UIAnalysisError(WebAutomationError):
    """Exception raised when UI analysis fails."""
    pass
