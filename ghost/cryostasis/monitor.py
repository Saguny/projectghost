"""System resource monitoring."""

import logging
import psutil
from typing import Optional

try:
    import pynvml
    NVIDIA_AVAILABLE = True
except ImportError:
    NVIDIA_AVAILABLE = False

from ghost.core.config import CryostasisConfig

logger = logging.getLogger(__name__)


class ResourceMonitor:
    """Monitors system resources (GPU, CPU, processes)."""
    
    def __init__(self, config: CryostasisConfig):
        self.config = config
        self.gpu_handle = None
        
        if NVIDIA_AVAILABLE:
            try:
                pynvml.nvmlInit()
                self.gpu_handle = pynvml.nvmlDeviceGetHandleByIndex(0)
                name = pynvml.nvmlDeviceGetName(self.gpu_handle)
                logger.info(f"NVIDIA GPU detected: {name}")
            except Exception as e:
                logger.warning(f"NVIDIA initialization failed: {e}")
                self.gpu_handle = None
        else:
            logger.warning("pynvml not available, GPU monitoring disabled")
    
    def get_gpu_stats(self) -> tuple[float, float]:
        """Get GPU utilization and VRAM usage."""
        if not self.gpu_handle:
            return 0.0, 0.0
        
        try:
            util = pynvml.nvmlDeviceGetUtilizationRates(self.gpu_handle)
            mem = pynvml.nvmlDeviceGetMemoryInfo(self.gpu_handle)
            
            vram_mb = mem.used / (1024 * 1024)
            return float(util.gpu), vram_mb
        except Exception as e:
            logger.error(f"GPU stats error: {e}")
            return 0.0, 0.0
    
    def get_cpu_stats(self) -> float:
        """Get CPU utilization percentage."""
        return psutil.cpu_percent(interval=0.1)
    
    def check_blacklist(self) -> Optional[str]:
        """Check if any blacklisted process is running."""
        if not self.config.blacklist_processes:
            return None
        
        blacklist_lower = [p.lower() for p in self.config.blacklist_processes]
        
        for proc in psutil.process_iter(['name']):
            try:
                proc_name = proc.info['name']
                if proc_name and proc_name.lower() in blacklist_lower:
                    return proc_name
            except (psutil.NoSuchProcess, psutil.AccessDenied):
                continue
        
        return None
    
    def get_system_summary(self) -> str:
        """Get human-readable system summary."""
        gpu_util, vram_mb = self.get_gpu_stats()
        cpu_util = self.get_cpu_stats()
        mem = psutil.virtual_memory()
        
        gpu_info = f"GPU: {gpu_util:.0f}%, VRAM: {vram_mb:.0f}MB" if self.gpu_handle else "GPU: N/A"
        
        return f"""
System Resources:
- {gpu_info}
- CPU: {cpu_util:.0f}%
- RAM: {mem.percent:.0f}% ({mem.used / (1024**3):.1f}GB / {mem.total / (1024**3):.1f}GB)
"""