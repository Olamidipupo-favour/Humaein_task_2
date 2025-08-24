"""
Browser Controller for Web Automation

This module provides a high-level interface for browser automation using Playwright,
including navigation, DOM interaction, and screenshot capabilities.
"""

import asyncio
import logging
from typing import Optional, Dict, Any, List
from pathlib import Path
from playwright.async_api import async_playwright, Browser, Page, BrowserContext

from .exceptions import BrowserError, ElementNotFoundError


class BrowserController:
    """
    High-level browser automation controller using Playwright.
    
    Handles browser lifecycle, navigation, and common DOM operations
    with error handling and logging.
    """
    
    def __init__(self, headless: bool = False, timeout: int = 30000):
        self.headless = headless
        self.timeout = timeout
        self.playwright = None
        self.browser: Optional[Browser] = None
        self.context: Optional[BrowserContext] = None
        self.page: Optional[Page] = None
        self.logger = logging.getLogger(__name__)
        
    async def launch(self) -> None:
        """Launch the browser and create a new context."""
        try:
            self.logger.debug("Starting Playwright...")
            self.playwright = await async_playwright().start()
            self.logger.debug(f"Playwright object: {type(self.playwright)}")
            
            if not self.playwright:
                raise BrowserError("Failed to start Playwright")
            
            self.logger.debug("Launching Chromium browser...")
            self.browser = await self.playwright.chromium.launch(
                headless=self.headless
            )
            self.logger.debug(f"Browser object: {type(self.browser)}")
            
            if not self.browser:
                raise BrowserError("Failed to create browser instance")
            
            self.logger.debug("Creating browser context...")
            # Create a new context with viewport and user agent
            self.context = await self.browser.new_context(
                viewport={"width": 1280, "height": 720},
                user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
            )
            self.logger.debug(f"Context object: {type(self.context)}")
            
            if not self.context:
                raise BrowserError("Failed to create browser context")
            
            self.logger.debug("Creating new page...")
            # Create a new page
            self.page = await self.context.new_page()
            self.logger.debug(f"Page object: {type(self.page)}")
            
            if not self.page:
                raise BrowserError("Failed to create browser page")
            
            self.logger.debug("Setting page timeout...")
            # Set the timeout on the page - wrap in try-catch to handle potential issues
            try:
                await self.page.set_default_timeout(self.timeout)
                self.logger.debug("Page timeout set successfully")
            except Exception as timeout_error:
                self.logger.warning(f"Could not set page timeout: {timeout_error}")
                # Continue anyway, this is not critical
                pass
            
            self.logger.info("Browser launched successfully")
            
        except Exception as e:
            self.logger.error(f"Failed to launch browser: {e}")
            # Clean up any partially created resources
            await self._cleanup_on_error()
            raise BrowserError(f"Browser launch failed: {e}")
            
    async def navigate(self, url: str) -> None:
        """Navigate to a specific URL."""
        if not self.page:
            raise BrowserError("Browser not launched")
            
        try:
            self.logger.info(f"Navigating to: {url}")
            await self.page.goto(url, wait_until="networkidle")
            self.logger.info(f"Successfully navigated to: {url}")
            
        except Exception as e:
            self.logger.error(f"Navigation failed: {e}")
            raise BrowserError(f"Navigation to {url} failed: {e}")
            
    async def wait_for_element(
        self, 
        selector: str, 
        timeout: Optional[int] = None
    ) -> None:
        """Wait for an element to appear on the page."""
        if not self.page:
            raise BrowserError("Browser not launched")
            
        try:
            timeout = timeout or self.timeout
            await self.page.wait_for_selector(selector, timeout=timeout)
            self.logger.debug(f"Element found: {selector}")
            
        except Exception as e:
            self.logger.error(f"Element not found: {selector}")
            raise ElementNotFoundError(f"Element {selector} not found within {timeout}ms")
            
    async def click(self, selector: str) -> None:
        """Click on an element."""
        if not self.page:
            raise BrowserError("Browser not launched")
            
        try:
            await self.wait_for_element(selector)
            await self.page.click(selector)
            self.logger.info(f"Clicked element: {selector}")
            
        except Exception as e:
            self.logger.error(f"Click failed on {selector}: {e}")
            raise BrowserError(f"Click failed: {e}")
            
    async def fill(self, selector: str, value: str) -> None:
        """Fill a form field with a value."""
        if not self.page:
            raise BrowserError("Browser not launched")
            
        try:
            await self.wait_for_element(selector)
            await self.page.fill(selector, value)
            self.logger.info(f"Filled {selector} with: {value}")
            
        except Exception as e:
            self.logger.error(f"Fill failed on {selector}: {e}")
            raise BrowserError(f"Fill failed: {e}")
            
    async def type_text(self, selector: str, text: str, delay: int = 100) -> None:
        """Type text into a field with optional delay between characters."""
        if not self.page:
            raise BrowserError("Browser not launched")
            
        try:
            await self.wait_for_element(selector)
            await self.page.type(selector, text, delay=delay)
            self.logger.info(f"Typed text into {selector}")
            
        except Exception as e:
            self.logger.error(f"Type failed on {selector}: {e}")
            raise BrowserError(f"Type failed: {e}")
            
    async def get_text(self, selector: str) -> str:
        """Get text content from an element."""
        if not self.page:
            raise BrowserError("Browser not launched")
            
        try:
            await self.wait_for_element(selector)
            text = await self.page.text_content(selector)
            return text or ""
            
        except Exception as e:
            self.logger.error(f"Get text failed on {selector}: {e}")
            raise BrowserError(f"Get text failed: {e}")
            
    async def get_attribute(self, selector: str, attribute: str) -> Optional[str]:
        """Get an attribute value from an element."""
        if not self.page:
            raise BrowserError("Browser not launched")
            
        try:
            await self.wait_for_element(selector)
            value = await self.page.get_attribute(selector, attribute)
            return value
            
        except Exception as e:
            self.logger.error(f"Get attribute failed on {selector}: {e}")
            raise BrowserError(f"Get attribute failed: {e}")
            
    async def take_screenshot(self, path: Optional[str] = None) -> str:
        """Take a screenshot of the current page."""
        if not self.page:
            raise BrowserError("Browser not launched")
            
        try:
            if not path:
                path = f"screenshot_{int(asyncio.get_event_loop().time())}.png"
                
            await self.page.screenshot(path=path)
            self.logger.info(f"Screenshot saved to: {path}")
            return path
            
        except Exception as e:
            self.logger.error(f"Screenshot failed: {e}")
            raise BrowserError(f"Screenshot failed: {e}")
            
    async def get_page_content(self) -> Dict[str, Any]:
        """Get comprehensive page content including HTML and metadata."""
        if not self.page:
            raise BrowserError("Browser not launched")
            
        try:
            content = await self.page.content()
            title = await self.page.title()
            url = self.page.url
            
            return {
                "html": content,
                "title": title,
                "url": url,
                "timestamp": asyncio.get_event_loop().time()
            }
            
        except Exception as e:
            self.logger.error(f"Get page content failed: {e}")
            raise BrowserError(f"Get page content failed: {e}")
            
    async def wait_for_navigation(self, timeout: Optional[int] = None) -> None:
        """Wait for page navigation to complete."""
        if not self.page:
            raise BrowserError("Browser not launched")
            
        try:
            timeout = timeout or self.timeout
            await self.page.wait_for_load_state("networkidle", timeout=timeout)
            self.logger.debug("Page navigation completed")
            
        except Exception as e:
            self.logger.error(f"Navigation wait failed: {e}")
            raise BrowserError(f"Navigation wait failed: {e}")
            
    async def close(self) -> None:
        """Close the browser and clean up resources."""
        try:
            if self.page:
                await self.page.close()
                self.page = None
                
            if self.context:
                await self.context.close()
                self.context = None
                
            if self.browser:
                await self.browser.close()
                self.browser = None
                
            if self.playwright:
                await self.playwright.stop()
                self.playwright = None
                
            self.logger.info("Browser closed successfully")
            
        except Exception as e:
            self.logger.error(f"Error closing browser: {e}")
            # Don't raise here as we're cleaning up
            
    async def _cleanup_on_error(self) -> None:
        """Clean up resources when an error occurs during launch."""
        try:
            if self.page:
                await self.page.close()
                self.page = None
                
            if self.context:
                await self.context.close()
                self.context = None
                
            if self.browser:
                await self.browser.close()
                self.browser = None
                
            if self.playwright:
                await self.playwright.stop()
                self.playwright = None
                
        except Exception as cleanup_error:
            self.logger.warning(f"Error during cleanup: {cleanup_error}")
            # Don't raise cleanup errors
