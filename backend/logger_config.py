"""
Configuración centralizada de Logging para el Backend de Granite Blog Writer.
Soporta salida por consola enriquecida y rotación de archivos de log.
"""

import logging
import os
import sys
from logging.handlers import RotatingFileHandler

WORKSPACE_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
LOGS_DIR = os.path.join(WORKSPACE_ROOT, "logs")
os.makedirs(LOGS_DIR, exist_ok=True)
LOG_FILE = os.path.join(LOGS_DIR, "app.log")

LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO").upper()

_initialized = False

def setup_root_logger():
    global _initialized
    if _initialized:
        return
    
    root_logger = logging.getLogger()
    root_logger.setLevel(getattr(logging, LOG_LEVEL, logging.INFO))
    
    # Formato uniforme
    log_format = logging.Formatter(
        "[%(asctime)s] [%(levelname)s] [%(name)s] %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S"
    )
    
    # Handler de Consola
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setFormatter(log_format)
    console_handler.setLevel(getattr(logging, LOG_LEVEL, logging.INFO))
    root_logger.addHandler(console_handler)
    
    # Handler de Archivo con rotación (5MB, 3 backups)
    file_handler = RotatingFileHandler(
        LOG_FILE,
        maxBytes=5 * 1024 * 1024,
        backupCount=3,
        encoding="utf-8"
    )
    file_handler.setFormatter(log_format)
    file_handler.setLevel(logging.INFO)
    root_logger.addHandler(file_handler)
    
    _initialized = True

def get_logger(name: str) -> logging.Logger:
    """Obtiene un logger configurado con el estándar del proyecto."""
    setup_root_logger()
    return logging.getLogger(name)
