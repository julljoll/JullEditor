"""
Módulo de diagnóstico y perfilado del sistema para Granite Blog Writer.
Detecta CPU, memoria RAM, plataforma y calcula automáticamente los parámetros
óptimos de inferencia para Ollama y el modelo IBM Granite.
"""

import logging
import os
import platform

logger = logging.getLogger("app.system_profiler")

def detect_system_resources() -> dict:
    """
    Detecta de forma segura los recursos del sistema (CPU, RAM, OS, Arquitectura)
    sin dependencias externas pesadas.
    """
    cpu_count = os.cpu_count() or 4
    system_os = platform.system()
    architecture = platform.machine()
    ram_gb = 8.0  # Fallback seguro

    if system_os == "Windows":
        try:
            import ctypes
            class MEMORYSTATUSEX(ctypes.Structure):
                _fields_ = [
                    ("dwLength", ctypes.c_ulong),
                    ("dwMemoryLoad", ctypes.c_ulong),
                    ("ullTotalPhys", ctypes.c_ulonglong),
                    ("ullAvailPhys", ctypes.c_ulonglong),
                    ("ullTotalPageFile", ctypes.c_ulonglong),
                    ("ullAvailPageFile", ctypes.c_ulonglong),
                    ("ullTotalVirtual", ctypes.c_ulonglong),
                    ("ullAvailVirtual", ctypes.c_ulonglong),
                    ("ullAvailExtendedVirtual", ctypes.c_ulonglong),
                ]
            stat = MEMORYSTATUSEX()
            stat.dwLength = ctypes.sizeof(stat)
            if ctypes.windll.kernel32.GlobalMemoryStatusEx(ctypes.byref(stat)):
                ram_gb = round(stat.ullTotalPhys / (1024 ** 3), 1)
        except Exception as e:
            logger.debug(f"Error detectando RAM en Windows: {e}")
    elif system_os == "Linux":
        try:
            with open("/proc/meminfo") as f:
                for line in f:
                    if line.startswith("MemTotal:"):
                        kb = int(line.split()[1])
                        ram_gb = round(kb / (1024 ** 2), 1)
                        break
        except Exception as e:
            logger.debug(f"Error detectando RAM en Linux: {e}")
    elif system_os == "Darwin":
        try:
            import subprocess
            out = subprocess.check_output(["sysctl", "-n", "hw.memsize"]).strip()
            ram_gb = round(int(out) / (1024 ** 3), 1)
        except Exception:
            pass

    # Heurística de optimización para CPU/GPU con IBM Granite
    if ram_gb >= 16:
        recommended_model = "granite3.3:8b"
        recommended_ctx = 8192
        recommended_threads = min(cpu_count, 8)
        tier = "high"
    elif ram_gb >= 8:
        recommended_model = "granite3.3:8b"
        recommended_ctx = 4096
        recommended_threads = min(cpu_count, 6)
        tier = "balanced"
    else:
        recommended_model = "granite3.3:2b"
        recommended_ctx = 4096
        recommended_threads = min(cpu_count, 4)
        tier = "light"

    return {
        "os": system_os,
        "arch": architecture,
        "cpu_count": cpu_count,
        "ram_gb": ram_gb,
        "tier": tier,
        "recommended_model": recommended_model,
        "recommended_ctx": recommended_ctx,
        "recommended_threads": recommended_threads
    }
