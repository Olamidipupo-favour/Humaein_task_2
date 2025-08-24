"""
Task Parser for Natural Language Instructions

This module uses LLM reasoning to parse natural language user instructions
into structured task information that can be executed by the automation system.
"""

import json
import logging
from typing import Dict, Any, Optional
from langchain_core.language_models import BaseLanguageModel
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import PydanticOutputParser
from pydantic import BaseModel, Field

from .exceptions import TaskExecutionError


class TaskInfo(BaseModel):
    """Structured representation of a parsed user task."""
    
    task_type: str = Field(description="The type of task (e.g., 'send_email', 'upload_document')")
    target_service: str = Field(description="The target service or platform")
    recipient: Optional[str] = Field(description="Recipient or target destination")
    subject: Optional[str] = Field(description="Subject or title for the task")
    content: Optional[str] = Field(description="Main content or message body")
    attachments: Optional[list] = Field(description="List of attachments or files")
    priority: Optional[str] = Field(description="Priority level (low, medium, high)")
    scheduled_time: Optional[str] = Field(description="Scheduled execution time")
    additional_params: Optional[Dict[str, Any]] = Field(description="Additional task parameters")


class TaskParser:
    """
    Parser that converts natural language instructions into structured task information.
    
    Uses LLM reasoning to understand user intent and extract relevant parameters
    for task execution across different service providers.
    """
    
    def __init__(self, llm: BaseLanguageModel):
        self.llm = llm
        self.logger = logging.getLogger(__name__)
        self._setup_parser()
        
    def _setup_parser(self) -> None:
        """Setup the output parser and prompt template."""
        self.output_parser = PydanticOutputParser(pydantic_object=TaskInfo)
        
        self.prompt_template = ChatPromptTemplate.from_template(
            """You are a task parsing assistant that converts natural language instructions
            into structured task information for web automation.
            
            Analyze the user's instruction and extract the following information:
            - Task type (what action to perform)
            - Target service (where to perform it)
            - Recipient/destination
            - Subject/title
            - Content/body
            - Any attachments or files
            - Priority level
            - Scheduled time (if applicable)
            - Additional parameters
            
            User instruction: {user_instruction}
            
            {format_instructions}
            
            Think step by step:
            1. Identify the main action the user wants to perform
            2. Determine which service or platform this applies to
            3. Extract all relevant details and parameters
            4. Structure the information according to the schema
            
            Respond with only the JSON object, no additional text."""
        )
        
    async def parse_instruction(self, user_instruction: str) -> Dict[str, Any]:
        """
        Parse a natural language instruction into structured task information.
        
        Args:
            user_instruction: Natural language description of the task
            
        Returns:
            Dictionary containing parsed task information
            
        Raises:
            TaskExecutionError: If parsing fails
        """
        try:
            self.logger.info(f"Parsing instruction: {user_instruction}")
            
            # Format the prompt with user instruction and parser instructions
            prompt = self.prompt_template.format_messages(
                user_instruction=user_instruction,
                format_instructions=self.output_parser.get_format_instructions()
            )
            
            # Get LLM response
            response = await self.llm.agenerate([prompt])
            response_text = response.generations[0][0].text.strip()
            
            # Clean up the response (remove markdown if present)
            if response_text.startswith("```json"):
                response_text = response_text.split("```json")[1]
            if response_text.endswith("```"):
                response_text = response_text[:-3]
            response_text = response_text.strip()
            
            # Parse the JSON response
            parsed_task = self.output_parser.parse(response_text)
            
            # Convert to dictionary
            task_dict = parsed_task.dict()
            self.logger.info(f"Successfully parsed task: {task_dict}")
            
            return task_dict
            
        except Exception as e:
            self.logger.error(f"Failed to parse instruction: {e}")
            raise TaskExecutionError(f"Task parsing failed: {e}")
            
    def _extract_email_info(self, instruction: str) -> Dict[str, Any]:
        """Extract email-specific information from instruction."""
        # This is a fallback method if LLM parsing fails
        email_info = {
            "task_type": "send_email",
            "target_service": "email",
            "recipient": None,
            "subject": None,
            "content": None
        }
        
        # Simple keyword extraction as fallback
        if "to" in instruction.lower():
            # Extract recipient (simplified)
            parts = instruction.lower().split("to")
            if len(parts) > 1:
                recipient_part = parts[1].split()[0]
                email_info["recipient"] = recipient_part
                
        if "about" in instruction.lower():
            # Extract subject
            parts = instruction.lower().split("about")
            if len(parts) > 1:
                subject_part = parts[1].split("saying")[0].strip()
                email_info["subject"] = subject_part
                
        if "saying" in instruction.lower():
            # Extract content
            parts = instruction.lower().split("saying")
            if len(parts) > 1:
                content_part = parts[1].strip()
                email_info["content"] = content_part
                
        return email_info
        
    def _extract_upload_info(self, instruction: str) -> Dict[str, Any]:
        """Extract upload-specific information from instruction."""
        upload_info = {
            "task_type": "upload_document",
            "target_service": "cloud_storage",
            "recipient": None,
            "subject": None,
            "content": None,
            "attachments": []
        }
        
        # Simple keyword extraction
        if "to" in instruction.lower():
            parts = instruction.lower().split("to")
            if len(parts) > 1:
                service_part = parts[1].split()[0]
                upload_info["target_service"] = service_part
                
        return upload_info
