"""
Lanzador y Gestor Principal Multiplataforma en Python Puro para JullEditor v3.3.0.
Sustituye completamente scripts de PowerShell (.ps1) y Batch (.bat),
ofreciendo diagnóstico de hardware, control del ciclo de vida de Ollama,
gestión de puertos y ejecución de pruebas de forma 100% nativa en Python.

Uso:
  python run.py              # Inicia servidor web FastAPI + abre navegador
  python run.py --test       # Ejecuta la suite de pruebas completa con pytest
  python run.py --cli        # Inicia el generador interactivo por terminal (TSJ)
  python run.py --tui        # Interfaz TUI Textual (canónica): flujo editorial completo
  python run.py --file <md>  # Inicia CLI precargando el archivo especificado
  python run.py --port 8000  # Especifica un puerto personalizado
"""

import argparse
import os
import platform
import socket
import subprocess
import sys
import time
import webbrowser
from pathlib import Path

WORKSPACE_ROOT = Path(__file__).resolve().parent
DEFAULT_PORT = 8000
DEFAULT_MODEL = os.getenv("GRANITE_MODEL", "granite3.3:8b")
OLLAMA_BASE_URL = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")


def print_header(title: str):
    print("=" * 80)
    print(f"   {title}")
    print("=" * 80)
    print()


def diagnose_hardware():
    """Diagnóstico rápido del sistema y recomendación de modelo IBM Granite."""
    cpu_count = os.cpu_count() or 4
    system_os = platform.system()
    ram_gb = 8.0

    try:
        if system_os == "Windows":
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
                    ("sullAvailExtendedVirtual", ctypes.c_ulonglong),
                ]
            stat = MEMORYSTATUSEX()
            stat.dwLength = ctypes.sizeof(MEMORYSTATUSEX)
            ctypes.windll.kernel32.GlobalMemoryStatusEx(ctypes.byref(stat))
            ram_gb = round(stat.ullTotalPhys / (1024 ** 3), 1)
    except Exception:
        pass

    print(f"[HARDWARE] Hilos CPU: {cpu_count} | Memoria RAM: {ram_gb} GB | SO: {system_os}")
    if ram_gb < 8.0:
        print("[RECOMENDACIÓN] RAM < 8GB: Modelo liviano 'granite3.3:2b' sugerido.")
    else:
        print("[RECOMENDACIÓN] RAM >= 8GB: Rendimiento óptimo con 'granite3.3:8b'.")
    print()


def is_port_in_use(port: int) -> bool:
    """Verifica si un puerto TCP local está en uso."""
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.settimeout(0.5)
        return s.connect_ex(("127.0.0.1", port)) == 0


def free_port(port: int):
    """Intenta liberar el puerto cerrando procesos de uvicorn/python en conflicto (Windows)."""
    if not is_port_in_use(port):
        return

    if platform.system() == "Windows":
        try:
            cmd = f'powershell -Command "Get-NetTCPConnection -LocalPort {port} -State Listen -ErrorAction SilentlyContinue | Select-Object -ExpandProperty OwningProcess"'
            res = subprocess.run(cmd, shell=True, capture_output=True, text=True)
            pids = res.stdout.strip().split()
            current_pid = os.getpid()
            for pid_str in pids:
                if pid_str.isdigit():
                    pid = int(pid_str)
                    if pid != 0 and pid != current_pid:
                        print(f"[INFO] Liberando puerto {port} ocupado por proceso previo (PID {pid})...")
                        subprocess.run(f"taskkill /PID {pid} /F", shell=True, capture_output=True)
                        time.sleep(0.6)
        except Exception:
            pass


def ensure_env_file():
    """Asegura que exista un archivo .env válido en la raíz."""
    env_file = WORKSPACE_ROOT / ".env"
    env_example = WORKSPACE_ROOT / ".env.example"
    if not env_file.exists() and env_example.exists():
        print("[INFO] Creando archivo .env a partir de .env.example...")
        env_file.write_text(env_example.read_text(encoding="utf-8"), encoding="utf-8")


def check_ollama_service() -> bool:
    """Verifica si Ollama está en línea; si no, intenta arrancarlo."""
    import urllib.request
    try:
        with urllib.request.urlopen(f"{OLLAMA_BASE_URL}/api/tags", timeout=2.0) as resp:
            if resp.status == 200:
                print(f"[OK] Servicio de Ollama activo en {OLLAMA_BASE_URL}.")
                return True
    except Exception:
        pass

    print("[PASO 1] Iniciando servicio de Ollama en segundo plano (ollama serve)...")
    try:
        creation_flag = subprocess.CREATE_NO_WINDOW if platform.system() == "Windows" else 0
        subprocess.Popen(["ollama", "serve"], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, creationflags=creation_flag)
        for _ in range(12):
            time.sleep(1)
            try:
                with urllib.request.urlopen(f"{OLLAMA_BASE_URL}/api/tags", timeout=1.5) as r:
                    if r.status == 200:
                        print("[OK] Servicio de Ollama iniciado correctamente.")
                        return True
            except Exception:
                pass
    except Exception as e:
        print(f"[AVISO] No se pudo lanzar 'ollama serve' automáticamente: {e}")

    return False


def run_linters() -> int:
    """Análisis estático con ruff (no bloqueante si no está instalado)."""
    try:
        import ruff  # noqa: F401
        has_ruff = True
    except ImportError:
        has_ruff = subprocess.run(
            [sys.executable, "-m", "ruff", "--version"],
            capture_output=True,
        ).returncode == 0
    if not has_ruff:
        print("   [AVISO] ruff no está instalado; omite el lint (pip install ruff).")
        return 0
    res = subprocess.run(
        [sys.executable, "-m", "ruff", "check", "backend/", "run.py", "--select", "E9,F"],
        cwd=str(WORKSPACE_ROOT),
    )
    return res.returncode


def run_tests():
    """Ejecuta linters + suite de pruebas completa en Pytest con cobertura."""
    print_header("EJECUTANDO SUITE COMPLETA DE PRUEBAS — JULL EDITOR v3.3.0")
    run_linters()
    cmd = [sys.executable, "-m", "pytest", "tests/", "-v", "--tb=short", "-p", "no:libtmux"]
    # Cobertura opcional (solo si pytest-cov está disponible)
    cov_probe = subprocess.run(
        [sys.executable, "-m", "pytest", "--help"], capture_output=True, text=True
    )
    if "--cov" in cov_probe.stdout:
        cmd += ["--cov=backend", "--cov-report=term-missing"]
    res = subprocess.run(cmd, cwd=str(WORKSPACE_ROOT))
    if res.returncode == 0:
        print("\n" + "=" * 80)
        print("   [OK] TODAS LAS PRUEBAS PASARON EXITOSAMENTE (0 FALLOS)")
        print("=" * 80)
    else:
        print("\n" + "=" * 80)
        print(f"   [ERROR] ALGUNAS PRUEBAS FALLARON (Código de salida: {res.returncode})")
        print("=" * 80)
    sys.exit(res.returncode)


def run_web(port: int = DEFAULT_PORT):
    """Lanza el servidor web FastAPI con recarga y abre el navegador."""
    print_header("INICIANDO JULL EDITOR v3.3.0 (CYBER-LEGAL LOCAL CPU)")
    ensure_env_file()
    diagnose_hardware()
    check_ollama_service()
    free_port(port)

    # Abrir navegador en segundo plano
    def open_browser_delayed():
        time.sleep(1.2)
        webbrowser.open(f"http://127.0.0.1:{port}")

    import threading
    threading.Thread(target=open_browser_delayed, daemon=True).start()

    print("\n=========================================================================")
    print(f"   Servidor Web Activo: http://127.0.0.1:{port}")
    print("   Presiona CTRL+C para detener la aplicación")
    print("=========================================================================\n")

    cmd = [sys.executable, "-m", "uvicorn", "backend.app:app", "--host", "127.0.0.1", "--port", str(port), "--reload"]
    try:
        subprocess.run(cmd, cwd=str(WORKSPACE_ROOT))
    except KeyboardInterrupt:
        print("\n[OK] Servidor JullEditor detenido correctamente.")


def main():
    parser = argparse.ArgumentParser(description="JullEditor — Orquestador 100% Python")
    parser.add_argument("--test", action="store_true", help="Ejecutar la suite de pruebas unitarias y de integración")
    parser.add_argument("--cli", action="store_true", help="Ejecutar el generador interactivo por terminal (modo Sentencia TSJ)")
    parser.add_argument("--tui", action="store_true", help="Interfaz TUI Textual (canónica v3.3+): flujo editorial completo en Python")
    parser.add_argument("--file", type=str, default=None, help="Ruta de un archivo .md para precargar en el CLI o la web")
    parser.add_argument("--port", type=int, default=DEFAULT_PORT, help=f"Puerto TCP del servidor web (por defecto {DEFAULT_PORT})")

    args = parser.parse_args()

    if args.test:
        run_tests()
    elif args.tui:
        from backend.tui_app import main as tui_main
        sys.exit(tui_main([args.file] if args.file else []))
    elif args.cli or args.file:
        from backend.cli_generator import main as cli_main
        if args.file:
            sys.argv = [sys.argv[0], args.file]
        else:
            sys.argv = [sys.argv[0]]
        sys.exit(cli_main())
    else:
        run_web(port=args.port)


if __name__ == "__main__":
    main()
