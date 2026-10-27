"""
Módulo de Auto-Arranque (Bootstrap) para JullEditor — 100% Python.

Encargado de que el doble clic en crear_articulo.bat funcione incluso en una
computadora recién formateada:

  1. Analiza la computadora donde se está ejecutando (CPU, RAM, SO, arquitectura).
  2. Verifica las dependencias del proyecto (paquetes de requirements.txt);
     si faltan, las instala de una vez con pip.
  3. Verifica Ollama; si no está instalado, lo instala automáticamente
     (Windows: winget → fallback descarga oficial del instalador .exe;
      Linux/macOS: script oficial curl | sh / brew).
  4. Según las características detectadas, descarga el modelo IBM Granite
     acorde al hardware (granite3.3:8b o granite3.3:2b) vía 'ollama pull'.

Todo el diagnóstico pesado reutiliza backend.system_profiler (fuente única
de verdad), y el control de servicios reutiliza las funciones de run.py.
"""

from __future__ import annotations

import importlib.metadata
import logging
import os
import platform
import shutil
import subprocess
import sys
import time
import urllib.request
from pathlib import Path

from backend.system_profiler import detect_system_resources

logger = logging.getLogger("app.bootstrap")

WORKSPACE_ROOT = Path(__file__).resolve().parent.parent
REQUIREMENTS_FILE = WORKSPACE_ROOT / "requirements.txt"
OLLAMA_INSTALLER_URL = "https://ollama.com/download/OllamaSetup.exe"
OLLAMA_LINUX_INSTALL_CMD = "curl -fsSL https://ollama.com/install.sh | sh"


# --------------------------------------------------------------------------
# Utilidades de ejecución
# --------------------------------------------------------------------------
def _creation_flags() -> int:
    return subprocess.CREATE_NO_WINDOW if platform.system() == "Windows" else 0


def _run_quiet(cmd: list[str] | str, timeout: int = 60) -> subprocess.CompletedProcess:
    """Ejecuta un comando sin ruido; nunca lanza excepción por fallo del SO."""
    try:
        return subprocess.run(
            cmd, shell=isinstance(cmd, str), capture_output=True, text=True,
            timeout=timeout, creationflags=_creation_flags(),
        )
    except Exception as e:
        logger.debug("Fallo ejecutando %r: %s", cmd, e)
        res = subprocess.CompletedProcess(cmd, returncode=1, stdout="", stderr=str(e))
        return res


# --------------------------------------------------------------------------
# 1. Análisis de la computadora
# --------------------------------------------------------------------------
def analyze_computer() -> dict:
    """Analiza y muestra el perfil de hardware de la máquina actual."""
    profile = detect_system_resources()
    print("=" * 74)
    print("  ANALISIS DE LA COMPUTADORA (perfil de hardware)")
    print("=" * 74)
    print(f"  Sistema Operativo : {profile['os']} ({profile['arch']})")
    print(f"  Hilos de CPU      : {profile['cpu_count']}")
    print(f"  Memoria RAM       : {profile['ram_gb']} GB")
    print(f"  Tier estimado     : {profile['tier'].upper()}")
    print(f"  Modelo Granite recomendado segun hardware: {profile['recommended_model']}")
    print("=" * 74)
    return profile


# --------------------------------------------------------------------------
# 2. Dependencias Python (pip)
# --------------------------------------------------------------------------
def _requirement_name(spec: str) -> str | None:
    """Extrae el nombre del paquete de una línea de requirements.txt."""
    line = spec.strip()
    if not line or line.startswith("#") or line.startswith("-"):
        return None
    for sep in (">=", "<=", "==", "!=", "~=", ">", "<", "[", " "):
        if sep in line:
            line = line.split(sep)[0]
    return line.strip() or None


def missing_python_packages() -> list[str]:
    """Paquetes de requirements.txt cuyo dist-info no está instalado."""
    if not REQUIREMENTS_FILE.exists():
        return []
    missing: list[str] = []
    for raw in REQUIREMENTS_FILE.read_text(encoding="utf-8").splitlines():
        name = _requirement_name(raw)
        if not name:
            continue
        try:
            importlib.metadata.distribution(name)
        except importlib.metadata.PackageNotFoundError:
            missing.append(name)
    return missing


def ensure_python_dependencies(auto_install: bool = True) -> bool:
    """Verifica dependencias; opcionalmente las instala de una vez con pip."""
    missing = missing_python_packages()
    if not missing:
        print("[OK] Dependencias Python verificadas (requirements.txt completo).")
        return True
    print(f"[INFO] Faltan {len(missing)} dependencias Python: {', '.join(missing)}")
    if not auto_install:
        print("[AVISO] Instalacion omitida (--no-bootstrap). Ejecuta: pip install -r requirements.txt")
        return False
    print("[PASO] Instalando dependencias con pip (esto puede tardar unos minutos)...")
    res = subprocess.run(
        [sys.executable, "-m", "pip", "install", "-r", str(REQUIREMENTS_FILE)],
        creationflags=_creation_flags(),
    )
    if res.returncode == 0:
        print("[OK] Dependencias instaladas correctamente.")
        return True
    print("[ERROR] pip fallo al instalar dependencias. Revisa el mensaje anterior.")
    return False


# --------------------------------------------------------------------------
# 3. Ollama: verificar / instalar
# --------------------------------------------------------------------------
def _candidate_ollama_paths() -> list[str]:
    """Rutas típicas donde los instaladores colocan el ejecutable de Ollama."""
    exe = "ollama.exe" if platform.system() == "Windows" else "ollama"
    paths = [str(Path(d) / exe) for d in _windows_ollama_paths()]
    paths += [str(Path.home() / ".local" / "bin" / "ollama"), "/usr/local/bin/ollama"]
    return paths


def refresh_ollama_path() -> None:
    """Agrega al PATH del proceso las rutas típicas de instalación de Ollama.

    Tras una instalación silenciosa (winget / instalador oficial / script curl),
    el registro ya contiene la ruta pero este proceso no la ve hasta refrescar.
    """
    env_path = os.environ.get("PATH", "")
    dirs = [*_windows_ollama_paths(), str(Path.home() / ".local" / "bin"), "/usr/local/bin"]
    additions = [d for d in dirs if d not in env_path]
    if additions:
        os.environ["PATH"] = env_path + os.pathsep + os.pathsep.join(additions)


def is_ollama_installed() -> bool:
    if shutil.which("ollama"):
        return True
    return any(Path(c).exists() for c in _candidate_ollama_paths())


def _wait_ollama_ready(base_url: str, seconds: int = 90) -> bool:
    """Espera a que el servicio HTTP de Ollama responda."""
    deadline = time.time() + seconds
    while time.time() < deadline:
        try:
            with urllib.request.urlopen(f"{base_url}/api/tags", timeout=2.0) as resp:
                if resp.status == 200:
                    return True
        except Exception:
            pass
        time.sleep(2)
    return False


def _windows_ollama_paths() -> list[str]:
    """Rutas típicas donde el instalador de Ollama coloca ollama.exe."""
    program_files = os.environ.get("PROGRAMFILES", r"C:\Program Files")
    local_appdata = os.environ.get("LOCALAPPDATA") or str(Path.home() / "AppData" / "Local")
    return [str(Path(local_appdata) / "Programs" / "Ollama"),
            str(Path(program_files) / "Ollama")]


def install_ollama_windows() -> bool:
    """Instala Ollama en Windows vía winget; si no hay winget, descarga el
    instalador oficial y lo ejecuta en modo silencioso."""
    print("[PASO] Intentando instalar Ollama con winget...")
    res = _run_quiet(["winget", "install", "--id", "Ollama.Ollama",
                      "-e", "--accept-package-agreements", "--accept-source-agreements"],
                     timeout=900)
    refresh_ollama_path()
    if res.returncode == 0 and is_ollama_installed():
        print("[OK] Ollama instalado via winget.")
        return True

    print("[INFO] winget no disponible o fallo; descargando instalador oficial de Ollama...")
    installer = Path(os.environ.get("TEMP", str(Path.home()))) / "OllamaSetup.exe"
    try:
        urllib.request.urlretrieve(OLLAMA_INSTALLER_URL, installer)
        print(f"[INFO] Descarga lista: {installer} — ejecutando instalador silencioso...")
        _run_quiet([str(installer), "/SILENT", "/NORESTART"], timeout=600)
    except Exception as e:
        print(f"[ERROR] No se pudo descargar/ejecutar el instalador de Ollama: {e}")
        print(f"        Descargalo manualmente desde: {OLLAMA_INSTALLER_URL}")
        return False

    # El instalador agrega ollama.exe al PATH del registro; refrescamos rutas
    refresh_ollama_path()
    if is_ollama_installed():
        print("[OK] Ollama instalado via instalador oficial.")
        return True
    print("[AVISO] La instalacion comenzo; si 'ollama' sigue sin responder,"
          f" instala manualmente desde {OLLAMA_INSTALLER_URL} y vuelve a abrir el .bat.")
    return False


def install_ollama_posix() -> bool:
    """Instala Ollama en Linux (script oficial) o macOS (brew/script)."""
    system = platform.system()
    if system == "Darwin" and shutil.which("brew"):
        print("[PASO] Instalando Ollama con Homebrew...")
        res = _run_quiet(["brew", "install", "ollama"], timeout=1200)
        if res.returncode == 0 and is_ollama_installed():
            print("[OK] Ollama instalado via Homebrew.")
            return True
    print("[PASO] Ejecutando script oficial de instalacion de Ollama (curl | sh)...")
    res = _run_quiet(OLLAMA_LINUX_INSTALL_CMD, timeout=1200)
    refresh_ollama_path()
    if is_ollama_installed():
        print("[OK] Ollama instalado.")
        return True
    print(f"[ERROR] Instalacion automatica fallo: {res.stderr.strip()[:300]}")
    return False


def ensure_ollama_installed(auto_install: bool = True) -> bool:
    """Verifica Ollama; si falta y auto_install=True, lo instala según el SO."""
    if is_ollama_installed():
        print("[OK] Ollama esta instalado en el sistema.")
        return True
    print("[INFO] Ollama NO esta instalado en esta computadora.")
    if not auto_install:
        print("[AVISO] Auto-instalacion desactivada (--no-bootstrap).")
        return False
    if platform.system() == "Windows":
        return install_ollama_windows()
    return install_ollama_posix()


def ensure_ollama_service_running(base_url: str = "http://localhost:11434") -> bool:
    """Arranca 'ollama serve' en segundo plano si el servicio no responde."""
    try:
        with urllib.request.urlopen(f"{base_url}/api/tags", timeout=2.0) as resp:
            if resp.status == 200:
                return True
    except Exception:
        pass
    if not is_ollama_installed():
        return False
    print("[PASO] Iniciando servicio de Ollama en segundo plano...")
    try:
        subprocess.Popen(["ollama", "serve"], stdout=subprocess.DEVNULL,
                         stderr=subprocess.DEVNULL, creationflags=_creation_flags())
    except Exception as e:
        print(f"[AVISO] No se pudo lanzar 'ollama serve': {e}")
        return False
    if _wait_ollama_ready(base_url, seconds=30):
        print("[OK] Servicio de Ollama activo.")
        return True
    print("[AVISO] El servicio tardo demasiado en responder.")
    return False


# --------------------------------------------------------------------------
# 4. Descarga del modelo Granite acorde al hardware
# --------------------------------------------------------------------------
def installed_ollama_models(base_url: str = "http://localhost:11434") -> list[str]:
    """Lista los modelos ya descargados en Ollama (nombres con tag)."""
    import json
    try:
        with urllib.request.urlopen(f"{base_url}/api/tags", timeout=5.0) as resp:
            data = json.loads(resp.read().decode("utf-8"))
            return [m.get("name", "") for m in data.get("models", [])]
    except Exception:
        return []


def download_granite_model(recommended: str, base_url: str = "http://localhost:11434") -> bool:
    """Descarga (ollama pull) el modelo Granite acorde al hardware detectado."""
    already = any(name == recommended or name.startswith(recommended.split(":")[0])
                  for name in installed_ollama_models(base_url))
    if already:
        print(f"[OK] El modelo '{recommended}' ya esta descargado en Ollama.")
        return True
    print(f"[PASO] Descargando el modelo acorde a tu hardware: ollama pull {recommended}")
    print("       (peso aproximado: ~5 GB para 8b / ~2 GB para 2b — no cierres esta ventana)")
    try:
        res = subprocess.run(["ollama", "pull", recommended],
                             creationflags=_creation_flags(), timeout=3600)
        if res.returncode == 0:
            print(f"[OK] Modelo '{recommended}' descargado y listo para generar.")
            return True
    except Exception as e:
        print(f"[ERROR] Fallo la descarga automatica: {e}")
    print(f"[AVISO] Descargalo manualmente cuando puedas con: ollama pull {recommended}")
    return False


# --------------------------------------------------------------------------
# Orquestador del auto-arranque
# --------------------------------------------------------------------------
def run_bootstrap(auto_install: bool = True, base_url: str | None = None) -> dict:
    """Pipeline completo de arranque: analizar PC → deps → Ollama → modelo.

    Devuelve el perfil de hardware con claves adicionales:
      deps_ok, ollama_ok, model_ready, recommended_model.
    """
    base_url = base_url or os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")
    profile = analyze_computer()

    print("\n--- Verificacion de dependencias Python ---")
    profile["deps_ok"] = ensure_python_dependencies(auto_install)

    print("\n--- Verificacion de Ollama ---")
    profile["ollama_ok"] = ensure_ollama_installed(auto_install)
    if profile["ollama_ok"]:
        profile["ollama_ok"] = ensure_ollama_service_running(base_url)

    print("\n--- Modelo Granite acorde a tu computadora ---")
    model_ready = False
    if profile["ollama_ok"]:
        model_ready = download_granite_model(profile["recommended_model"], base_url)
    else:
        print("[AVISO] Sin Ollama disponible: la generacion local estara en modo demo/plantilla.")
    profile["model_ready"] = model_ready

    model_status = "LISTO" if model_ready else f"PENDIENTE (descarga manual: ollama pull {profile['recommended_model']})"
    print("\n" + "=" * 74)
    print("  RESUMEN DE ARRANQUE")
    print(f"  Hardware        : {profile['os']} | {profile['cpu_count']} hilos | {profile['ram_gb']} GB RAM ({profile['tier']})")
    print(f"  Python deps     : {'OK' if profile['deps_ok'] else 'INCOMPLETAS'}")
    print(f"  Ollama          : {'OK' if profile['ollama_ok'] else 'NO DISPONIBLE'}")
    print(f"  Modelo Granite  : {profile['recommended_model']} — {model_status}")
    print("=" * 74 + "\n")
    return profile


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    run_bootstrap(auto_install="--no-bootstrap" not in sys.argv)
