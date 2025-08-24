"""
Mock Browser Controller for Testing

This module provides a mock implementation of the browser controller
for testing and development without requiring a real browser.
"""

import asyncio
import logging
from typing import Dict, Any, Optional
from .exceptions import BrowserError, ElementNotFoundError


class MockBrowserController:
    """
    Mock browser controller that simulates browser actions.
    
    This is useful for testing the agent's logic without requiring
    a fully functional Playwright setup.
    """
    
    def __init__(self, headless: bool = False, timeout: int = 30000):
        self.headless = headless
        self.timeout = timeout
        self.logger = logging.getLogger(__name__)
        self.is_launched = False
        self.current_url = ""
        self.page_title = "Mock Page"
        
    async def launch(self) -> None:
        """Simulate browser launch."""
        self.logger.info("Mock browser launched successfully")
        self.is_launched = True
        await asyncio.sleep(0.1)  # Simulate launch time
        
    async def navigate(self, url: str) -> None:
        """Simulate navigation to a URL."""
        if not self.is_launched:
            raise BrowserError("Browser not launched")
            
        self.logger.info(f"Mock browser navigating to: {url}")
        self.current_url = url
        await asyncio.sleep(0.1)  # Simulate navigation time
        
    async def wait_for_element(self, selector: str, timeout: int = 5000) -> None:
        """Simulate waiting for an element to appear."""
        self.logger.info(f"Mock browser waiting for element: {selector}")
        await asyncio.sleep(0.05)  # Simulate wait time
        
    async def click(self, selector: str) -> None:
        """Simulate clicking an element."""
        self.logger.info(f"Mock browser clicking: {selector}")
        await asyncio.sleep(0.05)  # Simulate click time
        
    async def fill(self, selector: str, value: str) -> None:
        """Simulate filling a form field."""
        self.logger.info(f"Mock browser filling {selector} with: {value}")
        await asyncio.sleep(0.05)  # Simulate fill time
        
    async def type_text(self, selector: str, text: str) -> None:
        """Simulate typing text into an element."""
        self.logger.info(f"Mock browser typing in {selector}: {text}")
        await asyncio.sleep(0.05)  # Simulate typing time
        
    async def wait_for_navigation(self) -> None:
        """Simulate waiting for navigation to complete."""
        self.logger.info("Mock browser waiting for navigation")
        await asyncio.sleep(0.1)  # Simulate navigation time
        
    async def get_page_content(self) -> Dict[str, str]:
        """Get mock page content."""
        return {
            "html": "<html><body><div>Mock page content</div></body></html>",
            "url": self.current_url,
            "title": self.page_title
        }
        
    async def close(self) -> None:
        """Simulate closing the browser."""
        self.logger.info("Mock browser closed successfully")
        self.is_launched = False
        
    @property
    def page(self):
        """Mock page object."""
        return MockPage(self)
        
    @property
    def context(self):
        """Mock context object."""
        return MockContext(self)


class MockPage:
    """Mock page object."""
    
    def __init__(self, controller: MockBrowserController):
        self.controller = controller
        
    @property
    def url(self) -> str:
        return self.controller.current_url


class MockContext:
    """Mock context object."""
    
    def __init__(self, controller: MockBrowserController):
        self.controller = controller
