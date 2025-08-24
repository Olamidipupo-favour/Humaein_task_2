"""
UI Analyzer for Web Page Analysis

This module uses LLM reasoning to analyze web page structure and identify
interactive elements, form fields, and UI components for automation.
"""

import logging
from typing import Dict, Any, List, Optional
from langchain_core.language_models import BaseLanguageModel
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import PydanticOutputParser
from pydantic import BaseModel, Field

from .browser_controller import BrowserController
from .exceptions import UIAnalysisError


class UIElement(BaseModel):
    """Represents a UI element found on the page."""
    
    selector: str = Field(description="CSS selector or XPath to locate the element")
    element_type: str = Field(description="Type of element (button, input, link, etc.)")
    text_content: Optional[str] = Field(description="Visible text content of the element")
    attributes: Dict[str, str] = Field(description="Key attributes like id, class, name")
    purpose: str = Field(description="Inferred purpose of the element")
    confidence: float = Field(description="Confidence score for the purpose inference")


class PageAnalysis(BaseModel):
    """Comprehensive analysis of a web page."""
    
    page_title: str = Field(description="Page title")
    main_actions: List[UIElement] = Field(description="Primary action elements (buttons, links)")
    form_fields: List[UIElement] = Field(description="Input fields and form elements")
    navigation_elements: List[UIElement] = Field(description="Navigation and menu elements")
    content_areas: List[UIElement] = Field(description="Main content containers")
    interactive_elements: List[UIElement] = Field(description="All interactive elements")
    page_structure: Dict[str, Any] = Field(description="Overall page structure and layout")


class UIAnalyzer:
    """
    Analyzes web page structure using LLM reasoning to identify UI elements.
    
    This analyzer helps the automation system understand how to interact with
    different web interfaces by identifying buttons, forms, and other elements.
    """
    
    def __init__(self, llm: BaseLanguageModel):
        self.llm = llm
        self.logger = logging.getLogger(__name__)
        self._setup_analyzer()
        
    def _setup_analyzer(self) -> None:
        """Setup the output parser and prompt templates."""
        self.output_parser = PydanticOutputParser(pydantic_object=PageAnalysis)
        
        # Main analysis prompt
        self.analysis_prompt = ChatPromptTemplate.from_template(
            """You are a web UI analysis expert. Analyze the HTML content of a web page
            and identify key UI elements for automation purposes.
            
            HTML Content:
            {html_content}
            
            Page URL: {page_url}
            Page Title: {page_title}
            
            Analyze the page and identify:
            1. Main action elements (buttons, links for primary actions)
            2. Form fields (input boxes, textareas, select dropdowns)
            3. Navigation elements (menus, breadcrumbs, pagination)
            4. Content areas (main content containers, sidebars)
            5. Interactive elements (anything clickable or fillable)
            
            For each element, provide:
            - A reliable CSS selector to locate it
            - The element type
            - Visible text content
            - Key attributes (id, class, name, etc.)
            - Inferred purpose (what the element does)
            - Confidence score (0.0 to 1.0)
            
            {format_instructions}
            
            Focus on elements that would be useful for web automation tasks.
            """
        )
        
        # Element purpose inference prompt
        self.purpose_prompt = ChatPromptTemplate.from_template(
            """Analyze this UI element and determine its purpose:
            
            Element Type: {element_type}
            Text Content: {text_content}
            Attributes: {attributes}
            Surrounding Context: {context}
            
            What is the most likely purpose of this element?
            Choose from common web actions like:
            - compose_email, send_email, attach_file
            - login, logout, submit_form
            - navigate_menu, search, filter
            - upload_file, download_file
            - schedule_meeting, create_event
            
            Respond with just the purpose and a confidence score (0.0-1.0).
            """
        )
        
    async def analyze_page(self, browser_controller: BrowserController) -> Dict[str, Any]:
        """
        Analyze the current page to identify UI elements and structure.
        
        Args:
            browser_controller: Browser controller instance
            
        Returns:
            Dictionary containing page analysis results
            
        Raises:
            UIAnalysisError: If analysis fails
        """
        try:
            self.logger.info("Starting page analysis")
            
            # Get page content
            page_content = await browser_controller.get_page_content()
            html_content = page_content["html"]
            page_url = page_content["url"]
            page_title = page_content["title"]
            
            # Truncate HTML if too long (LLM context limits)
            if len(html_content) > 8000:
                html_content = html_content[:8000] + "... [truncated]"
                
            # Analyze the page using LLM
            analysis_result = await self._analyze_with_llm(
                html_content, page_url, page_title
            )
            
            # Convert to dictionary for easier handling
            analysis_dict = analysis_result.dict()
            self.logger.info(f"Page analysis completed: {len(analysis_dict.get('interactive_elements', []))} elements found")
            
            return analysis_dict
            
        except Exception as e:
            self.logger.error(f"Page analysis failed: {e}")
            raise UIAnalysisError(f"UI analysis failed: {e}")
            
    async def _analyze_with_llm(
        self, 
        html_content: str, 
        page_url: str, 
        page_title: str
    ) -> PageAnalysis:
        """Use LLM to analyze the page content."""
        try:
            # Format the analysis prompt
            prompt = self.analysis_prompt.format_messages(
                html_content=html_content,
                page_url=page_url,
                page_title=page_title,
                format_instructions=self.output_parser.get_format_instructions()
            )
            
            # Get LLM response
            response = await self.llm.agenerate([prompt])
            response_text = response.generations[0][0].text.strip()
            
            # Clean up response
            if response_text.startswith("```json"):
                response_text = response_text.split("```json")[1]
            if response_text.endswith("```"):
                response_text = response_text[:-3]
            response_text = response_text.strip()
            
            # Parse the response
            analysis = self.output_parser.parse(response_text)
            return analysis
            
        except Exception as e:
            self.logger.error(f"LLM analysis failed: {e}")
            # Fallback to basic analysis
            return self._fallback_analysis(html_content, page_title)
            
    def _fallback_analysis(self, html_content: str, page_title: str) -> PageAnalysis:
        """Fallback analysis when LLM fails."""
        self.logger.warning("Using fallback UI analysis")
        
        # Basic element detection using common patterns
        elements = []
        
        # Look for common button patterns
        if "compose" in html_content.lower():
            elements.append(UIElement(
                selector="[data-testid='compose'], .compose, button:contains('Compose')",
                element_type="button",
                text_content="Compose",
                attributes={"purpose": "compose_email"},
                purpose="compose_email",
                confidence=0.8
            ))
            
        if "send" in html_content.lower():
            elements.append(UIElement(
                selector="[data-testid='send'], .send, button:contains('Send')",
                element_type="button",
                text_content="Send",
                attributes={"purpose": "send_email"},
                purpose="send_email",
                confidence=0.8
            ))
            
        # Look for form fields
        if "input" in html_content.lower():
            elements.append(UIElement(
                selector="input[type='text'], input[type='email']",
                element_type="input",
                text_content="",
                attributes={"type": "text"},
                purpose="text_input",
                confidence=0.7
            ))
            
        return PageAnalysis(
            page_title=page_title,
            main_actions=elements,
            form_fields=elements,
            navigation_elements=[],
            content_areas=[],
            interactive_elements=elements,
            page_structure={"method": "fallback"}
        )
        
    async def find_element_by_purpose(
        self, 
        purpose: str, 
        page_analysis: Dict[str, Any]
    ) -> Optional[UIElement]:
        """
        Find a UI element by its intended purpose.
        
        Args:
            purpose: The purpose to search for
            page_analysis: Results from page analysis
            
        Returns:
            UIElement if found, None otherwise
        """
        interactive_elements = page_analysis.get("interactive_elements", [])
        
        # Look for exact purpose match
        for element in interactive_elements:
            if element.get("purpose") == purpose:
                return element
                
        # Look for partial matches
        for element in interactive_elements:
            element_purpose = element.get("purpose", "").lower()
            if purpose.lower() in element_purpose or element_purpose in purpose.lower():
                return element
                
        # Look for text content matches
        for element in interactive_elements:
            text_content = element.get("text_content", "").lower()
            if purpose.lower() in text_content:
                return element
                
        return None
        
    def get_best_selector(self, element: UIElement) -> str:
        """
        Get the best CSS selector for an element.
        
        Args:
            element: UI element to get selector for
            
        Returns:
            CSS selector string
        """
        # Prefer ID-based selectors
        if "id" in element.attributes:
            return f"#{element.attributes['id']}"
            
        # Then data-testid
        if "data-testid" in element.attributes:
            return f"[data-testid='{element.attributes['data-testid']}']"
            
        # Then name attribute
        if "name" in element.attributes:
            return f"[name='{element.attributes['name']}']"
            
        # Fallback to the provided selector
        return element.selector
