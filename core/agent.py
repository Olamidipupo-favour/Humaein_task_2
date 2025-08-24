"""
Universal Web Action Agent - Core Agent Implementation

This module provides the main agent class that can execute user goals
across multiple web service providers with different UI layouts.
"""

from typing import Dict, List, Optional, Any
from dataclasses import dataclass

import logging
from pathlib import Path

from langchain_community.chat_models import ChatOpenAI


from .browser_controller import BrowserController
from .providers.base_provider import BaseProvider
from .providers.gmail_provider import GmailProvider
from .providers.outlook_provider import OutlookProvider
from .task_parser import TaskParser
from .ui_analyzer import UIAnalyzer


@dataclass
class AgentConfig:
    """Configuration for the web action agent."""
    openai_api_key: str
    headless: bool = False
    timeout: int = 30000
    log_level: str = "INFO"
    screenshot_dir: Optional[Path] = None


class UniversalWebAgent:
    """
    Universal Web Action Agent that can execute tasks across multiple service providers.
    
    This agent uses LLM reasoning to understand user goals and translate them into
    browser automation actions, abstracting away provider-specific UI differences.
    """
    
    def __init__(self, config: AgentConfig):
        self.config = config
        self.setup_logging()
        self.setup_llm()
        self.setup_providers()
        self.browser_controller = BrowserController(
            headless=config.headless,
            timeout=config.timeout
        )
        self.task_parser = TaskParser(self.llm)
        self.ui_analyzer = UIAnalyzer(self.llm)
        
    def setup_logging(self) -> None:
        """Setup logging configuration for the agent."""
        logging.basicConfig(
            level=getattr(logging, self.config.log_level),
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )
        self.logger = logging.getLogger(__name__)
        
    def setup_llm(self) -> None:
        """Initialize the LLM for reasoning and UI analysis."""
        try:
            self.llm = ChatOpenAI(
                api_key=self.config.openai_api_key,
                model="gpt-4",
                temperature=0.1
            )
        except Exception as e:
            self.logger.error(f"Failed to initialize LLM: {e}")
            raise
            
    def setup_providers(self) -> None:
        """Initialize supported service providers."""
        self.providers: Dict[str, BaseProvider] = {
            "gmail": GmailProvider(),
            "outlook": OutlookProvider(),
            # Add more providers here as needed
        }
        
    async def execute_task(self, user_instruction: str) -> Dict[str, Any]:
        """
        Execute a user task across multiple service providers.
        
        Args:
            user_instruction: Natural language description of the task
            
        Returns:
            Dictionary containing execution results and logs
        """
        self.logger.info(f"Starting task execution: {user_instruction}")
        
        try:
            # Step 1: Parse and understand the user task
            task_info = await self.task_parser.parse_instruction(user_instruction)
            self.logger.info(f"Parsed task: {task_info}")
            
            # Step 2: Determine which providers to use
            target_providers = self._select_providers(task_info)
            
            # Step 3: Execute task on each provider
            results = {}
            for provider_name in target_providers:
                self.logger.info(f"Executing on {provider_name}")
                result = await self._execute_on_provider(
                    provider_name, task_info
                )
                results[provider_name] = result
                
            return {
                "success": True,
                "task": task_info,
                "results": results,
                "logs": self._get_execution_logs()
            }
            
        except Exception as e:
            self.logger.error(f"Task execution failed: {e}")
            return {
                "success": False,
                "error": str(e),
                "logs": self._get_execution_logs()
            }
            
    def _select_providers(self, task_info: Dict[str, Any]) -> List[str]:
        """Select appropriate providers based on task type."""
        task_type = task_info.get("task_type", "").lower()
        
        if "email" in task_type:
            return ["gmail", "outlook"]
        elif "upload" in task_type:
            return ["gmail", "outlook"]  # Placeholder - would be drive/dropbox
        elif "calendar" in task_type:
            return ["gmail", "outlook"]  # Placeholder - would be calendar services
        else:
            # Default to all providers for unknown tasks
            return list(self.providers.keys())
            
    async def _execute_on_provider(
        self, 
        provider_name: str, 
        task_info: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Execute the task on a specific provider."""
        provider = self.providers[provider_name]
        
        try:
            # Launch browser and navigate to provider
            await self.browser_controller.launch()
            await self.browser_controller.navigate(provider.get_login_url())
            
            # Authenticate with the provider
            auth_result = await provider.authenticate(self.browser_controller)
            if not auth_result["success"]:
                return {"success": False, "error": "Authentication failed"}
                
            # Navigate to the main service page
            await self.browser_controller.navigate(provider.get_service_url())
            
            # Analyze the UI and execute the task
            ui_analysis = await self.ui_analyzer.analyze_page(
                self.browser_controller
            )
            
            execution_result = await provider.execute_task(
                task_info, 
                self.browser_controller,
                ui_analysis
            )
            
            return execution_result
            
        except Exception as e:
            self.logger.error(f"Provider execution failed: {e}")
            return {"success": False, "error": str(e)}
            
        finally:
            # Always close the browser
            await self.browser_controller.close()
            
    def _get_execution_logs(self) -> List[str]:
        """Get execution logs for debugging and monitoring."""
        # This would collect logs from various components
        return ["Task execution completed", "Browser automation finished"]
        
    async def close(self) -> None:
        """Clean up resources."""
        await self.browser_controller.close()
        self.logger.info("Agent resources cleaned up")
