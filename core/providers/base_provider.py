"""
Base Provider Interface for Web Services

This module defines the abstract base class that all service providers
must implement to ensure consistent behavior across different platforms.
"""

from abc import ABC, abstractmethod
from typing import Dict, Any, Optional
from ..browser_controller import BrowserController


class BaseProvider(ABC):
    """
    Abstract base class for all service providers.
    
    This class defines the interface that all providers must implement,
    ensuring consistent behavior across different web services.
    """
    
    def __init__(self):
        self.name = self.__class__.__name__
        self.credentials = {}
        
    @abstractmethod
    def get_login_url(self) -> str:
        """Get the URL for the login page."""
        pass
        
    @abstractmethod
    def get_service_url(self) -> str:
        """Get the URL for the main service page."""
        pass
        
    @abstractmethod
    async def authenticate(
        self, 
        browser_controller: BrowserController
    ) -> Dict[str, Any]:
        """
        Authenticate with the service.
        
        Args:
            browser_controller: Browser controller instance
            
        Returns:
            Dictionary with authentication result
        """
        pass
        
    @abstractmethod
    async def execute_task(
        self,
        task_info: Dict[str, Any],
        browser_controller: BrowserController,
        ui_analysis: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Execute a specific task on this service.
        
        Args:
            task_info: Parsed task information
            browser_controller: Browser controller instance
            ui_analysis: Results from UI analysis
            
        Returns:
            Dictionary with execution result
        """
        pass
        
    def set_credentials(self, credentials: Dict[str, str]) -> None:
        """Set authentication credentials for the provider."""
        self.credentials = credentials
        
    def get_credential(self, key: str) -> Optional[str]:
        """Get a specific credential value."""
        return self.credentials.get(key)
        
    def validate_credentials(self) -> bool:
        """Validate that required credentials are present."""
        required_keys = self.get_required_credentials()
        return all(key in self.credentials for key in required_keys)
        
    @abstractmethod
    def get_required_credentials(self) -> list:
        """Get list of required credential keys."""
        pass
        
    def get_supported_tasks(self) -> list:
        """Get list of tasks this provider supports."""
        return []
        
    def can_handle_task(self, task_info: Dict[str, Any]) -> bool:
        """Check if this provider can handle the given task."""
        task_type = task_info.get("task_type", "").lower()
        supported_tasks = [t.lower() for t in self.get_supported_tasks()]
        return task_type in supported_tasks
