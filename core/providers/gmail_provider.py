"""
Gmail Provider for Web Automation

This module implements the Gmail-specific provider for sending emails
through the Gmail web interface using browser automation.
"""

import logging
from typing import Dict, Any, List
from .base_provider import BaseProvider
from ..browser_controller import BrowserController
from ..exceptions import AuthenticationError, TaskExecutionError


class GmailProvider(BaseProvider):
    """
    Gmail service provider for web automation.
    
    Handles authentication and email composition/sending through the
    Gmail web interface.
    """
    
    def __init__(self):
        super().__init__()
        self.name = "Gmail"
        self.logger = logging.getLogger(__name__)
        
    def get_login_url(self) -> str:
        """Get Gmail login URL."""
        return "https://accounts.google.com/signin"
        
    def get_service_url(self) -> str:
        """Get Gmail main service URL."""
        return "https://mail.google.com/mail/u/0/#compose"
        
    def get_required_credentials(self) -> List[str]:
        """Get required credential keys for Gmail."""
        return ["email", "password"]
        
    def get_supported_tasks(self) -> List[str]:
        """Get list of tasks Gmail supports."""
        return ["send_email", "compose_email", "reply_email"]
        
    async def authenticate(
        self, 
        browser_controller: BrowserController
    ) -> Dict[str, Any]:
        """
        Authenticate with Gmail using stored credentials.
        
        Args:
            browser_controller: Browser controller instance
            
        Returns:
            Dictionary with authentication result
            
        Raises:
            AuthenticationError: If authentication fails
        """
        try:
            if not self.validate_credentials():
                raise AuthenticationError("Missing required credentials")
                
            email = self.get_credential("email")
            password = self.get_credential("password")
            
            self.logger.info(f"Authenticating with Gmail as {email}")
            
            # Navigate to login page
            await browser_controller.navigate(self.get_login_url())
            
            # Wait for page to load and find email field
            await browser_controller.wait_for_element("input[type='email']")
            
            # Enter email
            await browser_controller.fill("input[type='email']", email)
            await browser_controller.click("#identifierNext")
            
            # Wait for password field and enter password
            await browser_controller.wait_for_element("input[type='password']")
            await browser_controller.fill("input[type='password']", password)
            await browser_controller.click("#passwordNext")
            
            # Wait for navigation to Gmail
            await browser_controller.wait_for_navigation()
            
            # Check if we're on Gmail
            current_url = browser_controller.page.url
            if "mail.google.com" in current_url:
                self.logger.info("Successfully authenticated with Gmail")
                return {"success": True, "message": "Authentication successful"}
            else:
                raise AuthenticationError("Failed to reach Gmail after login")
                
        except Exception as e:
            self.logger.error(f"Gmail authentication failed: {e}")
            raise AuthenticationError(f"Gmail authentication failed: {e}")
            
    async def execute_task(
        self,
        task_info: Dict[str, Any],
        browser_controller: BrowserController,
        ui_analysis: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Execute email task on Gmail.
        
        Args:
            task_info: Parsed task information
            browser_controller: Browser controller instance
            ui_analysis: Results from UI analysis
            
        Returns:
            Dictionary with execution result
        """
        try:
            task_type = task_info.get("task_type", "").lower()
            
            if task_type == "send_email":
                return await self._send_email(task_info, browser_controller, ui_analysis)
            else:
                return {
                    "success": False,
                    "error": f"Unsupported task type: {task_type}"
                }
                
        except Exception as e:
            self.logger.error(f"Gmail task execution failed: {e}")
            return {
                "success": False,
                "error": str(e)
            }
            
    async def _send_email(
        self,
        task_info: Dict[str, Any],
        browser_controller: BrowserController,
        ui_analysis: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Send an email using Gmail compose."""
        try:
            self.logger.info("Starting email composition in Gmail")
            
            # Navigate to compose page
            await browser_controller.navigate(self.get_service_url())
            
            # Wait for compose interface to load
            await browser_controller.wait_for_element("div[role='textbox']")
            
            # Extract email details
            recipient = task_info.get("recipient", "")
            subject = task_info.get("subject", "")
            content = task_info.get("content", "")
            
            # Fill recipient field (look for various possible selectors)
            recipient_selectors = [
                "input[name='to']",
                "input[aria-label*='To']",
                "input[placeholder*='To']",
                "input[data-tooltip*='To']"
            ]
            
            recipient_filled = False
            for selector in recipient_selectors:
                try:
                    await browser_controller.wait_for_element(selector, timeout=5000)
                    await browser_controller.fill(selector, recipient)
                    recipient_filled = True
                    self.logger.info(f"Filled recipient field with: {recipient}")
                    break
                except:
                    continue
                    
            if not recipient_filled:
                raise TaskExecutionError("Could not find recipient field")
                
            # Fill subject field
            subject_selectors = [
                "input[name='subjectbox']",
                "input[aria-label*='Subject']",
                "input[placeholder*='Subject']"
            ]
            
            subject_filled = False
            for selector in subject_selectors:
                try:
                    await browser_controller.wait_for_element(selector, timeout=5000)
                    await browser_controller.fill(selector, subject)
                    subject_filled = True
                    self.logger.info(f"Filled subject field with: {subject}")
                    break
                except:
                    continue
                    
            if not subject_filled:
                raise TaskExecutionError("Could not find subject field")
                
            # Fill content field
            content_selectors = [
                "div[role='textbox']",
                "div[aria-label*='Message Body']",
                "div[contenteditable='true']"
            ]
            
            content_filled = False
            for selector in content_selectors:
                try:
                    await browser_controller.wait_for_element(selector, timeout=5000)
                    await browser_controller.click(selector)
                    await browser_controller.type_text(selector, content)
                    content_filled = True
                    self.logger.info(f"Filled content field")
                    break
                except:
                    continue
                    
            if not content_filled:
                raise TaskExecutionError("Could not find content field")
                
            # Send the email
            send_selectors = [
                "div[data-tooltip*='Send']",
                "div[aria-label*='Send']",
                "div[role='button']:contains('Send')"
            ]
            
            email_sent = False
            for selector in send_selectors:
                try:
                    await browser_controller.wait_for_element(selector, timeout=5000)
                    await browser_controller.click(selector)
                    email_sent = True
                    self.logger.info("Clicked send button")
                    break
                except:
                    continue
                    
            if not email_sent:
                raise TaskExecutionError("Could not find send button")
                
            # Wait a moment for the email to be sent
            await browser_controller.wait_for_navigation()
            
            self.logger.info("Email sent successfully")
            return {
                "success": True,
                "message": "Email sent successfully",
                "recipient": recipient,
                "subject": subject,
                "provider": "Gmail"
            }
            
        except Exception as e:
            self.logger.error(f"Email sending failed: {e}")
            raise TaskExecutionError(f"Failed to send email: {e}")
            
    def _find_element_by_text(
        self, 
        text: str, 
        ui_analysis: Dict[str, Any]
    ) -> str:
        """Find element selector by text content."""
        interactive_elements = ui_analysis.get("interactive_elements", [])
        
        for element in interactive_elements:
            element_text = element.get("text_content", "").lower()
            if text.lower() in element_text:
                return element.get("selector", "")
                
        return ""
