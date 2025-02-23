"""
Base LLM provider class
"""
import platform
import psutil
from datetime import datetime
from typing import Dict, Optional
from ..utils.gpu import get_gpu_info

class LLMBase:
    def __init__(self, config: Dict):
        self.config = config
        # Set default max tokens if not specified
        if 'max_tokens' not in self.config:
            self.config['max_tokens'] = 300  # Increased default to allow for complete roasts

    def get_system_context(self, include_sys_info: bool = False) -> str:
        """Get current system context.
        
        Args:
            include_sys_info: Whether to include system information in the context.
        """
        current_time = datetime.now().strftime("%I:%M %p")
        current_date = datetime.now().strftime("%B %d, %Y")

        if include_sys_info:
            cpu_usage = psutil.cpu_percent()
            memory = psutil.virtual_memory().percent
            gpu_name, gpu_usage = get_gpu_info()

            context = f"""You are a snarky terminal assistant. Current system information:
- Current time: {current_time}
- Current date: {current_date}
- CPU Usage: {cpu_usage}%
- Memory Usage: {memory}%
- OS: {platform.system()} {platform.release()}"""

            if gpu_name != "No GPU detected":
                context += f"\n- GPU: {gpu_name} (Usage: {gpu_usage})"

            context += "\n\nPlease provide concise, slightly sarcastic responses that reference this system information."
        else:
            context = f"""You are a snarky terminal assistant. Current time: {current_time}, {current_date}.
Please provide concise, slightly sarcastic responses."""

        return context

    async def generate_response(self, query: str, include_sys_info: bool = False) -> str:
        raise NotImplementedError
