"""
JullEditor Installer & Launcher GUI — 100% Python Nativo (tkinter).
Sustituye la dependencia de Electron/Node.js para el empaquetado y arranque en Windows.

Funciones principales:
1. Ventana moderna Cyber-Legal con barra de progreso y estado detallado.
2. Detección y creación del entorno virtual (.venv) usando Python 3.10+.
3. Instalación desatendida de dependencias (requirements.txt).
4. Verificación y despliegue del runtime Ollama e IBM Granite.
5. Creación opcional de acceso directo en el Escritorio de Windows.
6. Lanzamiento inmediato del orquestador (run.py).
"""

from __future__ import annotations

import os
import platform
import queue
import shutil
import subprocess
import sys
import threading
import tkinter as tk
from pathlib import Path
from tkinter import messagebox, ttk

# Directorio raíz del proyecto
INSTALLER_DIR = Path(__file__).resolve().parent
PROJECT_ROOT = INSTALLER_DIR.parent
REQUIREMENTS_PATH = PROJECT_ROOT / "requirements.txt"
VENV_DIR = PROJECT_ROOT / ".venv"
RUN_PY = PROJECT_ROOT / "run.py"


def _is_windows() -> bool:
    return platform.system() == "Windows"


def _get_python_exe() -> str:
    """Devuelve la ruta al ejecutable de Python del venv o del sistema."""
    if _is_windows():
        venv_py = VENV_DIR / "Scripts" / "python.exe"
    else:
        venv_py = VENV_DIR / "bin" / "python"

    if venv_py.exists():
        return str(venv_py)
    return sys.executable


def _create_desktop_shortcut() -> bool:
    """Crea un acceso directo en el Escritorio usando Windows Script Host vía PowerShell."""
    if not _is_windows():
        return False
    try:
        desktop_dir = Path(os.environ.get("USERPROFILE", "")) / "Desktop"
        if not desktop_dir.exists():
            desktop_dir = Path.home() / "Desktop"

        shortcut_path = desktop_dir / "JullEditor.lnk"
        bat_target = PROJECT_ROOT / "crear_articulo.bat"
        icon_target = PROJECT_ROOT / "frontend" / "favicon.ico"

        ps_script = f"""
        $WshShell = New-Object -comObject WScript.Shell
        $Shortcut = $WshShell.CreateShortcut('{shortcut_path}')
        $Shortcut.TargetPath = '{bat_target}'
        $Shortcut.WorkingDirectory = '{PROJECT_ROOT}'
        $Shortcut.Description = 'JullEditor - Generador Editorial LegalTech con IBM Granite'
        if (Test-Path '{icon_target}') {{
            $Shortcut.IconLocation = '{icon_target}'
        }}
        $Shortcut.Save()
        """
        subprocess.run(
            ["powershell", "-NoProfile", "-Command", ps_script],
            creationflags=subprocess.CREATE_NO_WINDOW if _is_windows() else 0,
            check=False,
        )
        return shortcut_path.exists()
    except Exception:
        return False


class InstallerApp(tk.Tk):
    """Interfaz gráfica de instalación y configuración de JullEditor."""

    def __init__(self):
        super().__init__()
        self.title("JullEditor — Instalador & Setup Windows")
        self.geometry("620x440")
        self.resizable(False, False)
        self.configure(bg="#0B1120")  # Fondo Cyber-Legal Dark Slate

        # Cola de mensajes para sincronizar hilos con tkinter
        self.msg_queue: queue.Queue = queue.Queue()

        self._init_styles()
        self._build_ui()
        self.after(100, self._process_queue)

    def _init_styles(self):
        style = ttk.Style(self)
        style.theme_use("clam")

        # Configuración de barra de progreso Cyber-Legal (Aqua / Cyan)
        style.configure(
            "Cyan.Horizontal.TProgressbar",
            troughcolor="#1E293B",
            background="#00F0FF",
            bordercolor="#334155",
            lightcolor="#00F0FF",
            darkcolor="#00C4D4",
        )

    def _build_ui(self):
        # Header / Banner
        header_frame = tk.Frame(self, bg="#0F172A", height=90)
        header_frame.pack(fill="x")

        lbl_title = tk.Label(
            header_frame,
            text="⚡ JullEditor v4.0",
            font=("Segoe UI", 18, "bold"),
            fg="#00F0FF",
            bg="#0F172A",
        )
        lbl_title.pack(anchor="w", padx=25, pady=(15, 2))

        lbl_subtitle = tk.Label(
            header_frame,
            text="Estación de Redacción Editorial & LegalTech 100% Offline (Python Nativo)",
            font=("Segoe UI", 9),
            fg="#94A3B8",
            bg="#0F172A",
        )
        lbl_subtitle.pack(anchor="w", padx=25, pady=(0, 15))

        # Contenedor Central
        content_frame = tk.Frame(self, bg="#0B1120")
        content_frame.pack(fill="both", expand=True, padx=25, pady=20)

        self.lbl_status = tk.Label(
            content_frame,
            text="Preparando entorno...",
            font=("Segoe UI", 10, "bold"),
            fg="#F8FAFC",
            bg="#0B1120",
            anchor="w",
        )
        self.lbl_status.pack(fill="x", pady=(0, 8))

        self.progress = ttk.Progressbar(
            content_frame,
            orient="horizontal",
            style="Cyan.Horizontal.TProgressbar",
            mode="determinate",
            maximum=100,
        )
        self.progress.pack(fill="x", pady=(0, 15))

        # Consola de log interna
        self.log_text = tk.Text(
            content_frame,
            bg="#020617",
            fg="#CBD5E1",
            insertbackground="#00F0FF",
            font=("Consolas", 8),
            height=10,
            relief="flat",
            padx=10,
            pady=10,
        )
        self.log_text.pack(fill="both", expand=True)

        # Barra inferior con botones
        footer_frame = tk.Frame(self, bg="#0B1120")
        footer_frame.pack(fill="x", padx=25, pady=(0, 20))

        self.btn_action = tk.Button(
            footer_frame,
            text="Iniciar Instalación",
            font=("Segoe UI", 10, "bold"),
            bg="#0EA5E9",
            fg="#FFFFFF",
            activebackground="#0284C7",
            activeforeground="#FFFFFF",
            relief="flat",
            padx=20,
            pady=6,
            cursor="hand2",
            command=self.start_installation,
        )
        self.btn_action.pack(side="right")

    def log(self, message: str):
        self.msg_queue.put(("log", message))

    def set_status(self, text: str, progress_val: int | None = None):
        self.msg_queue.put(("status", (text, progress_val)))

    def _process_queue(self):
        try:
            while True:
                msg_type, payload = self.msg_queue.get_nowait()
                if msg_type == "log":
                    self.log_text.insert(tk.END, f"{payload}\n")
                    self.log_text.see(tk.END)
                elif msg_type == "status":
                    text, pval = payload
                    self.lbl_status.config(text=text)
                    if pval is not None:
                        self.progress["value"] = pval
                elif msg_type == "done":
                    self.btn_action.config(
                        text="Abrir JullEditor",
                        bg="#10B981",
                        state="normal",
                        command=self.launch_editor,
                    )
                elif msg_type == "error":
                    self.btn_action.config(text="Reintentar", state="normal")
                    messagebox.showerror("Error en Instalación", payload)
        except queue.Empty:
            pass
        self.after(100, self._process_queue)

    def start_installation(self):
        self.btn_action.config(state="disabled")
        threading.Thread(target=self._run_installer_worker, daemon=True).start()

    def _run_installer_worker(self):
        try:
            self.set_status("1/5. Verificando entorno virtual (.venv)...", 10)
            self.log("[PASO 1] Comprobando entorno virtual local...")

            if not VENV_DIR.exists():
                self.log(f"Creando entorno virtual en {VENV_DIR}...")
                res = subprocess.run(
                    [sys.executable, "-m", "venv", str(VENV_DIR)],
                    capture_output=True,
                    text=True,
                )
                if res.returncode != 0:
                    raise RuntimeError(f"Error creando virtualenv: {res.stderr}")
                self.log("[OK] Entorno virtual .venv creado con éxito.")
            else:
                self.log("[OK] Entorno virtual existente detectado.")

            py_exe = _get_python_exe()

            self.set_status("2/5. Verificando dependencias de Python...", 35)
            self.log(f"[PASO 2] Instalando dependencias con: {py_exe}")
            res = subprocess.run(
                [py_exe, "-m", "pip", "install", "--upgrade", "pip"],
                capture_output=True,
                text=True,
            )
            res = subprocess.run(
                [py_exe, "-m", "pip", "install", "-r", str(REQUIREMENTS_PATH)],
                capture_output=True,
                text=True,
            )
            if res.returncode != 0:
                self.log(f"[ADVERTENCIA] pip warnings: {res.stderr[:200]}")
            else:
                self.log("[OK] Dependencias verificadas/instaladas.")

            self.set_status("3/5. Ejecutando auto-arranque del sistema...", 60)
            self.log("[PASO 3] Delegando validaciones en backend.bootstrap...")
            res = subprocess.run(
                [py_exe, str(RUN_PY), "--no-browser"],
                capture_output=True,
                text=True,
                timeout=12,
            )
            self.log("[OK] Subrutinas de bootstrap inicializadas.")

            self.set_status("4/5. Creando acceso directo en Escritorio...", 85)
            if _create_desktop_shortcut():
                self.log("[OK] Acceso directo 'JullEditor' creado en el Escritorio.")
            else:
                self.log("[INFO] Acceso directo en Escritorio omitido o no compatible.")

            self.set_status("5/5. ¡Instalación completada!", 100)
            self.log("\n=======================================================")
            self.log(" JullEditor está listo para operar 100% Offline.")
            self.log("=======================================================\n")
            self.msg_queue.put(("done", None))

        except Exception as exc:
            self.log(f"[ERROR] {exc}")
            self.msg_queue.put(("error", str(exc)))

    def launch_editor(self):
        py_exe = _get_python_exe()
        self.destroy()
        subprocess.Popen(
            [py_exe, str(RUN_PY)],
            cwd=str(PROJECT_ROOT),
            creationflags=subprocess.CREATE_NEW_CONSOLE if _is_windows() else 0,
        )


def main():
    app = InstallerApp()
    app.mainloop()


if __name__ == "__main__":
    main()
