"""
GPU information utilities
"""
import subprocess
from typing import Tuple

try:
    import py3nvml as nvml
    HAS_NVIDIA = True
except ImportError:
    HAS_NVIDIA = False

def get_gpu_info() -> Tuple[str, str]:
    """Get GPU information and utilization."""
    try:
        # Try nvidia-smi first
        result = subprocess.run(['nvidia-smi', '--query-gpu=gpu_name,utilization.gpu', '--format=csv,noheader,nounits'],
                            capture_output=True, text=True, check=True)
        if result.stdout.strip():
            gpu_name, utilization = result.stdout.strip().split(',')
            return gpu_name.strip(), f"{utilization.strip()}%"
    except (subprocess.SubprocessError, FileNotFoundError):
        # If nvidia-smi fails, try py3nvml
        if HAS_NVIDIA:
            try:
                nvml.nvmlInit()
                handle = nvml.nvmlDeviceGetHandleByIndex(0)
                name = nvml.nvmlDeviceGetName(handle)
                util = nvml.nvmlDeviceGetUtilizationRates(handle)
                nvml.nvmlShutdown()
                return name, f"{util.gpu}%"
            except Exception:
                pass

        # Try lspci as a last resort
        try:
            result = subprocess.run('lspci | grep -i "vga\\|3d\\|display"', 
                                shell=True, capture_output=True, text=True)
            if result.stdout:
                return result.stdout.strip().split(':')[-1].strip(), "N/A"
        except (subprocess.SubprocessError, FileNotFoundError):
            pass

    return "No GPU detected", "N/A"
