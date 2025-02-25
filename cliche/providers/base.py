"""
Base LLM provider class
"""
import platform
import psutil
from datetime import datetime
from typing import Dict, Optional, List, Tuple
from ..utils.gpu import get_gpu_info
from ..prompts import MAIN_SYSTEM_PROMPT

class LLMBase:
    def __init__(self, config: Dict):
        self.config = config
        # Set default max tokens if not specified
        if 'max_tokens' not in self.config:
            self.config['max_tokens'] = 1000  # Increased to allow for longer, more detailed responses

    def get_system_context(self, include_sys_info: bool = False) -> str:
        """Get current system context.
        
        Args:
            include_sys_info: Whether to include system information in the context.
        """
        # Start with the main personality and behavior prompt
        context = MAIN_SYSTEM_PROMPT

        # Add current time and system info if requested
        current_time = datetime.now().strftime("%I:%M %p")
        current_date = datetime.now().strftime("%B %d, %Y")

        if include_sys_info:
            cpu_usage = psutil.cpu_percent()
            memory = psutil.virtual_memory().percent
            gpu_name, gpu_usage = get_gpu_info()

            context += f"""\n\nCurrent system information:
- Current time: {current_time}
- Current date: {current_date}
- CPU Usage: {cpu_usage}%
- Memory Usage: {memory}%
- OS: {platform.system()} {platform.release()}"""

            if gpu_name != "No GPU detected":
                context += f"\n- GPU: {gpu_name} (Usage: {gpu_usage})"

            context += "\n\nFeel free to reference this system information in your responses when relevant."
        else:
            context += f"\n\nCurrent time: {current_time}, {current_date}"

        return context

    async def generate_response(self, query: str, include_sys_info: bool = False) -> str:
        raise NotImplementedError

    async def list_models(self) -> List[Tuple[str, str]]:
        """List available models for this provider.
        
        Returns:
            List of tuples containing (model_id, description)
        """
        raise NotImplementedError
