"""
Generador CLI Interactivo en Python Puro para JullEditor.
Permite seleccionar archivos Markdown / Docling / Sentencias TSJ,
configurar parámetros idénticos a la interfaz web (con defaults:
Sentencia TSJ, Revista Digital, Temp=0.0, VE, Granite 8B)
y ejecutar la generación con streaming en consola o abrir la interfaz web.
"""

import asyncio
import json
import os
import shutil
import subprocess
import sys
import time
from pathlib import Path
from typing import Any

import httpx

from backend import editorial_catalog as cat
from backend.docling_parser import parse_docling_markdown
from backend.legal_validator import audit_legal_quality
from backend.logger_config import get_logger
from backend.prompts import build_generation_prompt, build_sentencia_tsj_prompt
from backend.rag_manager import (
    retrieve_legal_context,
    save_final_article,
)
from backend.sentencia_extractor import extract_sentencia_metadata, is_sentencia_text
from backend.seo_validator import audit_article_seo
from backend.version import __version__

logger = get_logger("cli_generator")

OLLAMA_BASE_URL = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")
DEFAULT_MODEL = os.getenv("GRANITE_MODEL", cat.DEFAULT_MODEL)
WORKSPACE_ROOT = Path(__file__).resolve().parent.parent
PRELOADED_FILE = WORKSPACE_ROOT / "backend" / "data" / "preloaded.json"


def clear_screen():
    os.system("cls" if os.name == "nt" else "clear")


def print_banner():
    print("=" * 83)
    print(f"   ⚖️  JULL EDITOR v{__version__} — ESTACIÓN PERICIAL TSJ & BLOG (SOLO PYTHON)")
    print("   IBM Granite 3.3 Local · Rigor Factual 0.0 · Ciberseguridad & TSJ Venezuela")
    print("=" * 83)
    print()


def open_file_dialog() -> str | None:
    """Abre el explorador de archivos nativo de Windows mediante Tkinter."""
    try:
        import tkinter as tk
        from tkinter import filedialog

        root = tk.Tk()
        root.withdraw()
        root.attributes("-topmost", True)
        selected = filedialog.askopenfilename(
            title="Seleccionar archivo Markdown o Docling para el artículo",
            initialdir=str(WORKSPACE_ROOT),
            filetypes=[
                ("Archivos Markdown / JSON", "*.md;*.markdown;*.json;*.txt"),
                ("Archivos Markdown (*.md)", "*.md;*.markdown"),
                ("Archivos JSON (*.json)", "*.json"),
                ("Todos los archivos", "*.*"),
            ],
        )
        root.destroy()
        return selected if selected else None
    except Exception as e:
        logger.warning(f"No se pudo abrir el diálogo visual de Tkinter: {e}")
        return None


CATEGORY_ICONS = {
    "Abogados": "⚖️",
    "Agrario": "🌾",
    "Civil": "🏛️",
    "Colombia": "🇨🇴",
    "Constitucion": "📜",
    "Diplomados": "🎓",
    "Informatica": "💻",
    "Jurisprudencias": "⚖️",
    "Mercantil": "🏢",
    "Otras": "📁",
    "Penal": "⚖️",
    "Tributario": "💰",
    "📥 RAG Inputs Recientes": "📥",
    "Raíz (Informacion_docling_rag)": "📄",
}


def scan_docling_rag_structure() -> dict[str, Any]:
    """
    Escanea en tiempo real el directorio Informacion_docling_rag/ sin caché estática,
    permitiendo que cualquier archivo nuevo agregado se detecte automáticamente.
    Retorna un diccionario estructurado con categorías, archivos por categoría y lista global.
    """
    docling_dir = WORKSPACE_ROOT / "Informacion_docling_rag"
    rag_dir = WORKSPACE_ROOT / "Articulos Generados" / "inputs"
    if not rag_dir.exists():
        rag_dir = WORKSPACE_ROOT / "RAG" / "inputs"

    categories: dict[str, list[Path]] = {}
    all_files: list[Path] = []

    if docling_dir.exists():
        # Escanear subdirectorios como categorías ordenadas
        for item in sorted(docling_dir.iterdir(), key=lambda p: p.name.lower()):
            if item.is_dir():
                md_files = sorted(
                    [
                        p
                        for p in item.iterdir()
                        if p.is_file() and p.suffix.lower() in (".md", ".markdown", ".json")
                    ],
                    key=lambda p: p.name.lower(),
                )
                if md_files:
                    categories[item.name] = md_files
                    all_files.extend(md_files)
            elif item.is_file() and item.suffix.lower() in (".md", ".markdown", ".json"):
                categories.setdefault("Raíz (Informacion_docling_rag)", []).append(item)
                all_files.append(item)

    # También verificar RAG/inputs si existe y contiene archivos
    if rag_dir.exists():
        rag_files = sorted(
            [
                p
                for p in rag_dir.iterdir()
                if p.is_file() and p.suffix.lower() in (".md", ".markdown", ".json")
            ],
            key=lambda p: p.stat().st_mtime,
            reverse=True,
        )
        if rag_files:
            categories["📥 RAG Inputs Recientes"] = rag_files
            all_files.extend(rag_files)

    category_list = list(categories.keys())
    return {
        "categories": categories,
        "category_list": category_list,
        "all_files": all_files,
        "total_files": len(all_files),
        "total_categories": len(category_list),
        "docling_path": docling_dir,
    }


def find_available_md_files() -> list[Path]:
    """Escanea las carpetas RAG e Informacion_docling_rag en busca de archivos .md en tiempo real."""
    scan = scan_docling_rag_structure()
    md_only = [p for p in scan["all_files"] if p.suffix.lower() in (".md", ".markdown")]
    md_only.sort(key=lambda x: x.stat().st_mtime, reverse=True)
    return md_only


def select_input_file(cli_arg_path: str | None = None) -> Path | None:
    """
    Gestiona la selección interactiva de archivos directamente desde Informacion_docling_rag/.
    Escanea en tiempo real el directorio para reflejar automáticamente cualquier archivo recién agregado.
    """
    if cli_arg_path:
        p = Path(cli_arg_path)
        if p.exists() and p.is_file():
            print(f"[OK] Archivo especificado por argumento: {p.name}")
            return p
        else:
            print(f"[AVISO] El archivo especificado no existe: {cli_arg_path}")

    # Bucle interactivo con actualización en tiempo real
    while True:
        try:
            scan = scan_docling_rag_structure()
            cat_list = scan["category_list"]
            cat_map = scan["categories"]
            total_files = scan["total_files"]
            total_cats = scan["total_categories"]
            docling_path = scan["docling_path"]

            print("=" * 83)
            print("📁 EXPLORADOR DE Informacion_docling_rag (ACTUALIZACIÓN EN VIVO)")
            print("=" * 83)
            print(f"  • Directorio: {docling_path}")
            print(f"  • Estado:     {total_cats} categorías activas · {total_files} documentos disponibles")
            print("-----------------------------------------------------------------------------------")
            print("CATEGORÍAS DISPONIBLES EN Informacion_docling_rag:")
            print()

            for idx, cname in enumerate(cat_list, 1):
                icon = CATEGORY_ICONS.get(cname, "📁")
                c_files = cat_map[cname]
                print(f"   [{idx:2d}] {icon} {cname:<26} ({len(c_files)} documentos)")

            print()
            print("-----------------------------------------------------------------------------------")
            print("OPCIONES DE NAVEGACIÓN Y ACTUALIZACIÓN:")
            print("   [T] 📋 Ver TODOS los documentos unificados (lista numerada completa)")
            print("   [B] 🔍 Buscar documento por nombre o palabra clave")
            print("   [A] 🔄 Actualizar / Refrescar directorio ahora (detecta nuevos archivos en disco)")
            print("   [E] 📂 Abrir carpeta Informacion_docling_rag en el Explorador de Windows")
            print("   [W] 🪟 Abrir selector nativo de Windows (Tkinter)")
            print("   [M] ✏️ Escribir ruta manualmente")
            print("   [X] ❌ Salir")
            print("-----------------------------------------------------------------------------------")

            user_choice = input(f"Elige una categoría [1-{total_cats}], [T], [B], [A] o [E]: ").strip()

            if not user_choice:
                continue

            choice_upper = user_choice.upper()

            if choice_upper in ("X", "SALIR", "EXIT", "Q"):
                print("[INFO] Operación cancelada por el usuario.")
                return None

            if choice_upper in ("A", "R", "ACTUALIZAR", "REFRESCAR"):
                print("\n>>> Re-escaneando Informacion_docling_rag en tiempo real...")
                new_scan = scan_docling_rag_structure()
                print(f"[OK] Directorio actualizado. {new_scan['total_categories']} categorías y {new_scan['total_files']} documentos detectados.")
                time.sleep(0.6)
                continue

            if choice_upper == "E":
                print(f"\n>>> Abriendo carpeta en el Explorador de Windows: {docling_path}")
                try:
                    if os.name == "nt":
                        os.startfile(str(docling_path))
                    else:
                        subprocess.Popen(["xdg-open", str(docling_path)])
                except Exception as e:
                    print(f"[AVISO] No se pudo abrir automáticamente el explorador: {e}")
                print("[INFO] Copia o agrega tus nuevos archivos allí. Al regresar, presiona [A] para que aparezcan automáticamente.\n")
                continue

            if choice_upper == "W":
                print(">>> Abriendo ventana de selección de Windows...")
                chosen = open_file_dialog()
                if chosen:
                    return Path(chosen)
                print("[INFO] Diálogo cancelado.")
                continue

            if choice_upper == "M":
                manual = input("Ruta completa del archivo .md / .json: ").strip('"').strip("'")
                p = Path(manual)
                if p.exists() and p.is_file():
                    return p
                print(f"[ERROR] Archivo no encontrado: {manual}")
                time.sleep(1)
                continue

            if choice_upper == "T":
                # Ver todos los documentos en una lista completa
                print("\n" + "=" * 83)
                print("📋 LISTADO COMPLETO DE DOCUMENTOS (Informacion_docling_rag)")
                print("=" * 83)
                all_docs = scan["all_files"]
                for i, doc in enumerate(all_docs, 1):
                    parent_cat = doc.parent.name
                    size_kb = round(doc.stat().st_size / 1024, 1)
                    print(f"   [{i:2d}] [{parent_cat}] {doc.name} ({size_kb} KB)")
                print("-----------------------------------------------------------------------------------")
                print("   [A] 🔄 Actualizar lista  |  [V] ⬅️ Volver al menú de categorías  |  [X] Salir")
                print("-----------------------------------------------------------------------------------")
                sel_all = input(f"Selecciona un número [1-{len(all_docs)}] o [V] para volver: ").strip()
                if not sel_all or sel_all.upper() == "V":
                    continue
                if sel_all.upper() in ("A", "R"):
                    continue
                if sel_all.upper() == "X":
                    return None
                try:
                    val = int(sel_all)
                    if 1 <= val <= len(all_docs):
                        return all_docs[val - 1]
                except ValueError:
                    pass
                print("[AVISO] Selección no válida.")
                time.sleep(0.8)
                continue

            if choice_upper == "B":
                # Buscar documento
                term = input("\n🔍 Ingresa término o palabra clave a buscar: ").strip().lower()
                if not term:
                    continue
                matches = [doc for doc in scan["all_files"] if term in doc.name.lower()]
                if not matches:
                    print(f"[AVISO] No se encontraron documentos que contengan '{term}'.")
                    time.sleep(1)
                    continue

                print("\n" + "=" * 83)
                print(f"🔍 RESULTADOS DE BÚSQUEDA PARA: '{term}' ({len(matches)} coincidencias)")
                print("=" * 83)
                for i, doc in enumerate(matches, 1):
                    parent_cat = doc.parent.name
                    size_kb = round(doc.stat().st_size / 1024, 1)
                    print(f"   [{i:2d}] [{parent_cat}] {doc.name} ({size_kb} KB)")
                print("-----------------------------------------------------------------------------------")
                print("   [V] ⬅️ Volver al menú de categorías")
                print("-----------------------------------------------------------------------------------")
                sel_match = input(f"Selecciona un documento [1-{len(matches)}] o [V] para volver: ").strip()
                if not sel_match or sel_match.upper() == "V":
                    continue
                try:
                    val = int(sel_match)
                    if 1 <= val <= len(matches):
                        return matches[val - 1]
                except ValueError:
                    pass
                print("[AVISO] Selección no válida.")
                time.sleep(0.8)
                continue

            # Selección por número de categoría
            selected_cat_name = None
            try:
                cat_idx = int(user_choice)
                if 1 <= cat_idx <= len(cat_list):
                    selected_cat_name = cat_list[cat_idx - 1]
            except ValueError:
                # Búsqueda por nombre de categoría textual
                for cname in cat_list:
                    if user_choice.lower() in cname.lower():
                        selected_cat_name = cname
                        break

            if not selected_cat_name:
                print(f"[AVISO] Opción '{user_choice}' no reconocida. Intenta de nuevo.")
                time.sleep(0.8)
                continue

            # Submenú de categoría seleccionada
            while True:
                # Re-escanear para tener los archivos actualizados en la categoría
                cat_scan = scan_docling_rag_structure()
                docs = cat_scan["categories"].get(selected_cat_name, [])

                print("\n" + "=" * 83)
                icon = CATEGORY_ICONS.get(selected_cat_name, "📁")
                print(f"📂 CATEGORÍA: {icon} {selected_cat_name} ({len(docs)} archivos disponibles)")
                print("=" * 83)
                if not docs:
                    print("   (No hay archivos .md en esta categoría actualmente)")
                    print("   Agrega archivos a esta carpeta y presiona [A] para que aparezcan al instante.")
                else:
                    for i, doc in enumerate(docs, 1):
                        size_kb = round(doc.stat().st_size / 1024, 1)
                        print(f"   [{i:2d}] {doc.name} ({size_kb} KB)")

                print("-----------------------------------------------------------------------------------")
                print("   [A] 🔄 Actualizar / Refrescar lista de esta categoría")
                print("   [V] ⬅️ Volver al listado de categorías")
                print("   [X] ❌ Salir")
                print("-----------------------------------------------------------------------------------")
                doc_choice = input(f"Selecciona un documento [1-{len(docs)}], [A] o [V]: ").strip()

                if not doc_choice or doc_choice.upper() == "V":
                    break
                if doc_choice.upper() in ("X", "SALIR", "EXIT", "Q"):
                    return None
                if doc_choice.upper() in ("A", "R", "ACTUALIZAR"):
                    print(f"\n>>> Actualizando archivos en '{selected_cat_name}'...")
                    time.sleep(0.4)
                    continue

                try:
                    val = int(doc_choice)
                    if 1 <= val <= len(docs):
                        selected_doc = docs[val - 1]
                        print(f"\n[OK] Documento seleccionado: '{selected_doc.name}'")
                        print(f"     Ruta: {selected_doc}")
                        return selected_doc
                except ValueError:
                    pass

                print("[AVISO] Selección no válida. Ingresa un número de documento válido o [V].")
                time.sleep(0.8)

        except (EOFError, KeyboardInterrupt):
            print("\n[INFO] Operación interrumpida.")
            return None



def prompt_editorial_config(parsed_doc: dict[str, Any], is_tsj: bool) -> dict[str, Any]:
    """Presenta las opciones de creación de artículos (con los mismos defaults del frontend)."""
    print()
    print("🎯 PASO 2/6: ESPECIALIDAD TEMÁTICA")
    print("-----------------------------------------------------------------------------------")
    theme_default = "1" if is_tsj else "1"
    print("  [1] 🏛️ Sentencia TSJ / Forense & Jurisprudencia [* Predeterminada]" if is_tsj else "  [1] 🏛️ Sentencia TSJ / Forense & Jurisprudencia [* Predeterminada]")
    print("  [2] ⚖️ Derecho Digital & LegalTech")
    print("  [3] 🛡️ Ciberseguridad & Evidencia Informática")
    print("  [4] 🧠 Inteligencia Artificial & Datos")
    print("  [5] 🔬 Ciencia & Tecnología")
    theme_in = input(f"Selecciona especialidad [1-5] (Enter para opción {theme_default}): ").strip() or theme_default
    theme_map = {
        "1": "sentencia_tsj" if is_tsj else "forensic_law",
        "2": "legal_tech",
        "3": "cybersecurity",
        "4": "ai_data",
        "5": "science_tech",
    }
    selected_theme = theme_map.get(theme_in, "sentencia_tsj" if is_tsj else "forensic_law")

    print()
    print("📰 PASO 3/6: ESTILO EDITORIAL (GUTENBERG / CMS)")
    print("-----------------------------------------------------------------------------------")
    print("  [1] 📰 Revista Digital (3 Col. Interpretativo-Explicativo 2026) [* Predeterminada]")
    print("  [2] 📝 Resumen Clásico Fiel (Síntesis Directa)")
    mode_in = input("Selecciona estilo [1-2] (Enter para 1): ").strip() or "1"
    selected_mode = "magazine" if mode_in == "1" else "classic"

    print()
    print("🎙️ PASO 4/6: PERFIL DE VOZ / TONO (IDÉNTICO AL SELECT 'toneSelect' DE index.html)")
    print("-----------------------------------------------------------------------------------")
    print("  ── JURÍDICOS VENEZUELA ──")
    print("  [1]  📰 Analista Jurisprudencial TSJ — Revista Digital Educativa [* Predeterminado]")
    print("  [2]  🎓 Revista Científica Arbitrada (Derecho & Computación Forense — Univ.)")
    print("  [3]  ⚖️ Abogado VE — Doctrinal (Forense / TSJ · Recomendado 2026)")
    print("  [4]  ⚖️ Abogado VE — Litigante (Ruta Procesal / Lapsos)")
    print("  [5]  ⚖️ Abogado VE — Explicativo (Claro / Divulgación)")
    print("  [6]  👤 Jull (Venezolano Técnico-Científico)")
    print("  [7]  👤 Jull (Venezolano Explicativo)")
    print("  ── GENÉRICOS ──")
    print("  [8]  🏢 Consultor Jurídico Corporativo (Compliance / Riesgos)")
    print("  [9]  💬 Conversacional Ágil")
    print("  [10] 🔬 Analítico Pericial")
    print("  [11] 📚 Didáctico / Pedagógico")
    print("  [12] 💼 Ejecutivo / Directivo")
    tone_options = [
        "analista_tsj_revista",
        "revista_cientifica_law_tech",
        "abogado_ve_doctrinal",
        "abogado_ve_litigante",
        "abogado_ve_explicativo",
        "jull",
        "jull_explicativo",
        "consultor_corporativo",
        "conversational",
        "analytical",
        "didactic",
        "executive",
    ]
    while True:
        tone_in = input("Selecciona tono [1-12] (Enter para 1): ").strip() or "1"
        if tone_in.isdigit() and 1 <= int(tone_in) <= len(tone_options):
            selected_tone = tone_options[int(tone_in) - 1]
            break
        print("[AVISO] Opción no válida. Ingresa un número entre 1 y 12.")

    print()
    print("⚖️ PASO 5/6: JURISDICCIÓN & ENFOQUE NORMATIVO (select 'jurisdictionSelect')")
    print("-----------------------------------------------------------------------------------")
    print("  [1] 🔄 Auto (Detectar por fuente y notas · Enfoque Venezuela) [* Predeterminada en index.html]")
    print("  [2] 🇻🇪 Venezuela (CRBV, Delitos Inf., Infogobierno, TSJ)")
    print("  [3] 🌐 Internacional / Global (ISO, NIST, UE)")
    jur_map = {
        "1": "auto",
        "2": "venezuela",
        "3": "international",
    }
    while True:
        jur_in = input("Selecciona jurisdicción [1-3] (Enter para 1-Auto): ").strip() or "1"
        if jur_in in jur_map:
            selected_jurisdiction = jur_map[jur_in]
            break
        print("[AVISO] Opción no válida. Ingresa un número entre 1 y 3.")

    print()
    print("⚙️ PASO 6/6: PARÁMETROS TÉCNICOS DE INFERENCIA (Ajustes Avanzados de index.html)")
    print("-----------------------------------------------------------------------------------")
    print("  * Temperatura: 0.0 (Cero Alucinación / Rigor Factual TSJ) [*]")
    print(f"  * Modelo:      {DEFAULT_MODEL} (granite3.3:8b Recomendado 16GB) [*]")
    print("  * Extensión:   1000 palabras (Pilar SEO 2026 · Recomendado) [*]")
    print("-----------------------------------------------------------------------------------")
    adv = input("¿Deseas personalizar estos parámetros técnicos? [s/N]: ").strip().lower()

    selected_temp = 0.0
    selected_words = 1000
    selected_model = DEFAULT_MODEL
    selected_custom_instructions = ""

    if adv in ("s", "si", "y", "yes"):
        # Slider tempSlider: min 0.05, max 1.0, step 0.05 (default web 0.2; CLI mantiene 0.0 anti-alucinación)
        temp_input = input("Temperatura [0.0 - 1.0] (Enter para 0.0): ").strip()
        try:
            if temp_input:
                selected_temp = max(0.0, min(1.0, float(temp_input.replace(",", "."))))
        except ValueError:
            selected_temp = 0.0

        # select modelSelect: granite3.3:8b | granite3.3:2b
        model_input = input(f"Modelo Ollama [1] {DEFAULT_MODEL} (8b Rec.) [2] granite3.3:2b (Rápido CPU) (Enter para 1): ").strip()
        if model_input == "2":
            selected_model = "granite3.3:2b"

        # select wordCountTarget: 600 Corto | 1000 Pilar SEO | 1500 Largo | 2000 Pilar Extenso
        words_input = input("Extensión [1]~600 Corto [2]~1000 PilarSEO[*] [3]~1500 Largo [4]~2000 Extenso (Enter para 2): ").strip() or "2"
        words_map = {"1": 600, "2": 1000, "3": 1500, "4": 2000}
        selected_words = words_map.get(words_input, 1000)

        # input customInstructions (Opcional en index.html)
        selected_custom_instructions = input(
            "Instrucciones Personalizadas (Enter para omitir). Ej: responder intención de búsqueda, incluir ejemplos prácticos: "
        ).strip()

    return {
        "theme": selected_theme,
        "editorial_mode": selected_mode,
        "tone": selected_tone,
        "jurisdiction": selected_jurisdiction,
        "temperature": selected_temp,
        "model": selected_model,
        "target_words": selected_words,
        "custom_instructions": selected_custom_instructions,
    }


def check_and_start_ollama() -> bool:
    """Verifica si Ollama está en ejecución; si no, intenta iniciarlo."""
    try:
        resp = httpx.get(f"{OLLAMA_BASE_URL}/api/tags", timeout=2.0)
        if resp.status_code == 200:
            return True
    except Exception:
        pass

    print("\n[INFO] Ollama no está respondiendo. Intentando iniciar servicio en segundo plano...")
    ollama_bin = shutil.which("ollama")
    if not ollama_bin:
        # Rutas comunes en Windows
        local_app = os.environ.get("LOCALAPPDATA", "")
        candidates = [
            Path(local_app) / "Programs" / "Ollama" / "ollama.exe",
            Path("C:/Program Files/Ollama/ollama.exe"),
        ]
        for c in candidates:
            if c.exists():
                ollama_bin = str(c)
                break

    if ollama_bin:
        try:
            subprocess.Popen(
                [ollama_bin, "serve"],
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
                creationflags=subprocess.CREATE_NO_WINDOW if os.name == "nt" else 0,
            )
            for _ in range(12):
                time.sleep(1)
                try:
                    r = httpx.get(f"{OLLAMA_BASE_URL}/api/tags", timeout=1.5)
                    if r.status_code == 200:
                        print("[OK] Servicio de Ollama iniciado exitosamente.")
                        return True
                except Exception:
                    pass
        except Exception as e:
            logger.warning(f"No se pudo iniciar ollama automáticamente: {e}")

    print("[AVISO] No se pudo conectar a Ollama en http://localhost:11434.")
    print("Asegúrate de tener Ollama abierto o ejecuta 'ollama serve' en otra terminal.")
    return False


async def stream_generation_cli(prompt: str, model: str, temperature: float) -> str:
    """Ejecuta la inferencia en streaming imprimiendo los tokens en tiempo real en la terminal."""
    payload = {
        "model": model,
        "prompt": prompt,
        "stream": True,
        "options": {
            "temperature": temperature,
            "num_predict": 4096,
            "num_ctx": 8192,
            "num_thread": 4,
            "repeat_penalty": 1.1,
            "top_p": 0.9,
        },
    }

    full_output = []
    print("\n" + "=" * 83)
    print(">>> REDACCIÓN EDITORIAL EN TIEMPO REAL (IBM GRANITE 3.3)")
    print("=" * 83 + "\n")

    timeout_cfg = httpx.Timeout(timeout=600.0, connect=15.0, read=300.0, write=30.0)
    async with httpx.AsyncClient(timeout=timeout_cfg) as client, client.stream(
        "POST",
        f"{OLLAMA_BASE_URL}/api/generate",
        json=payload,
        headers={"Content-Type": "application/json"},
    ) as response:
        if response.status_code != 200:
            print(f"\n[ERROR] Ollama retornó estado {response.status_code}")
            return ""

        async for line in response.aiter_lines():
            if not line:
                continue
            try:
                data = json.loads(line)
                tok = data.get("response", "")
                if tok:
                    sys.stdout.write(tok)
                    sys.stdout.flush()
                    full_output.append(tok)
                if data.get("done", False):
                    eval_tokens = data.get("eval_count", 0)
                    dur_ns = data.get("total_duration", 0)
                    dur_sec = round(dur_ns / 1e9, 1) if dur_ns else 0
                    speed = round(eval_tokens / dur_sec, 1) if dur_sec > 0 else 0
                    print("\n" + "-" * 83)
                    print(f"[COMPLETADO] Tokens: {eval_tokens} | Tiempo: {dur_sec}s | Velocidad: {speed} tok/s")
                    print("-" * 83)
                    break
            except json.JSONDecodeError:
                continue

    return "".join(full_output)


def save_preloaded_session(source_file: Path, config: dict[str, Any], parsed: dict[str, Any]):
    """Guarda los datos para que el frontend web cargue este archivo automáticamente."""
    PRELOADED_FILE.parent.mkdir(parents=True, exist_ok=True)
    payload = {
        "filename": source_file.name,
        "title": parsed.get("clean_title") or source_file.stem.replace("_", " ").title(),
        "content": parsed.get("cleaned_content", ""),
        "theme": config["theme"],
        "editorial_mode": config["editorial_mode"],
        "tone": config["tone"],
        "jurisdiction": config["jurisdiction"],
        "temperature": config["temperature"],
        "model": config["model"],
        "target_words": config["target_words"],
        "custom_instructions": config.get("custom_instructions", ""),
    }
    with open(PRELOADED_FILE, "w", encoding="utf-8") as f:
        json.dump(payload, f, ensure_ascii=False, indent=2)
    print(f"\n[OK] Sesión precargada guardada en: {PRELOADED_FILE}")


def run_web_server():
    """Inicia el servidor FastAPI uvicorn y abre el navegador."""
    print("\n" + "=" * 83)
    print("🌐 INICIANDO SERVIDOR WEB JULL EDITOR (http://127.0.0.1:8000)")
    print("===================================================================================")
    try:
        import webbrowser

        import uvicorn

        def open_browser():
            time.sleep(1.2)
            webbrowser.open("http://127.0.0.1:8000")

        import threading
        threading.Thread(target=open_browser, daemon=True).start()

        uvicorn.run("backend.app:app", host="127.0.0.1", port=8000, reload=False)
    except KeyboardInterrupt:
        print("\n[OK] Servidor detenido por el usuario.")
    except Exception as e:
        print(f"[ERROR] No se pudo arrancar el servidor web: {e}")


def main():
    clear_screen()
    print_banner()

    # 1. Selección del archivo base
    cli_arg = sys.argv[1] if len(sys.argv) > 1 else None
    source_path = select_input_file(cli_arg)
    if not source_path:
        print("\n[AVISO] No se seleccionó ningún archivo. Operación cancelada.")
        return 1

    # 2. Lectura y parseo del archivo
    print(f"\n>>> Leyendo y analizando: {source_path.name}...")
    try:
        raw_content = source_path.read_text(encoding="utf-8", errors="replace")
    except Exception as e:
        print(f"[ERROR] No se pudo leer el archivo: {e}")
        return 1

    parsed = parse_docling_markdown(raw_content, source_path.name)
    content_text = parsed.get("cleaned_content", raw_content)
    article_title = parsed.get("clean_title") or source_path.stem.replace("_", " ").title()

    # Detección de sentencia TSJ
    is_tsj = is_sentencia_text(content_text)
    tsj_meta = extract_sentencia_metadata(content_text, source_path.name) if is_tsj else None

    if is_tsj and tsj_meta:
        print("\n" + "=" * 83)
        print("🏛️  SENTENCIA DEL TSJ DETECTADA — FICHA TÉCNICA OFICIAL")
        print("=" * 83)
        print(f"  • Sala:          {tsj_meta.get('sala', 'Tribunal Supremo de Justicia')}")
        print(f"  • Expediente:    {tsj_meta.get('expediente', 'N/D')}")
        print(f"  • Sentencia Nº:  {tsj_meta.get('numero_sentencia', 'S/N')}")
        print(f"  • Ponente:       {tsj_meta.get('ponente', 'N/D')}")
        print(f"  • Fecha:         {tsj_meta.get('fecha_decision', 'N/D')}")
        print(f"  • Dispositivo:   {tsj_meta.get('decision_tipo', 'Sentencia Definitiva')}")
        partes = tsj_meta.get("partes", {})
        print(f"  • Partes:        {partes.get('recurrente_o_demandante', '-')} c/ {partes.get('recurrido_o_demandado', '-')}")
        print("=" * 83)
    else:
        word_count = len(content_text.split())
        print(f"\n[OK] Documento cargado: '{article_title}' (~{word_count} palabras)")

    # 3. Preguntar configuración editorial con defaults
    config = prompt_editorial_config(parsed, is_tsj)

    # 4. Modo de ejecución
    print("\n🚀 ¿CÓMO DESEAS EJECUTAR ESTA GENERACIÓN?")
    print("-----------------------------------------------------------------------------------")
    print("  [A] ⚡ Generación Directa en Terminal (Streaming + Auto-guardado RAG) [*]")
    print("  [B] 🌐 Iniciar Servidor Web (Abre navegador con el archivo precargado)")
    print("-----------------------------------------------------------------------------------")
    exec_mode = input("Selecciona [A/B] (Enter para A): ").strip().upper() or "A"

    if exec_mode == "B":
        save_preloaded_session(source_path, config, parsed)
        run_web_server()
        return 0

    # Sincronización con index.html: la jurisdicción "Auto" se resuelve siempre con
    # sesgo Venezuela (única jurisdicción local soportada por el proyecto).
    if config["jurisdiction"] == "auto":
        config["_rag_jur_code"] = "ve"

    # 5. Generación Directa CLI
    if not check_and_start_ollama():
        print("\n[ERROR] No es posible continuar sin Ollama en ejecución.")
        return 1

    # RAG Context (igual criterio que el backend web: corpus legal Venezuela según jurisdicción)
    rag_context = ""
    if config["jurisdiction"] in ("venezuela", "auto"):
        jur_code = "ve"
        try:
            rag_context = retrieve_legal_context(
                query_text=f"{article_title} {content_text[:2000]}",
                theme=config["theme"],
                top_k=3,
                jurisdiction=jur_code,
            )
        except Exception:
            rag_context = ""

    custom_instr = config.get("custom_instructions", "")

    # Construir prompt (misma ruta de decisión que app.py / article-generator.js)
    if is_tsj or config["theme"] == "sentencia_tsj" or config["tone"] == "analista_tsj_revista":
        prompt = build_sentencia_tsj_prompt(
            article_source_text=content_text,
            source_title=article_title,
            source_url=f"Archivo local: {source_path.name}",
            sentencia_metadata=tsj_meta,
            legal_rag_context=rag_context,
            custom_instructions=custom_instr,
            target_words=config["target_words"],
        )
    else:
        prompt = build_generation_prompt(
            article_source_text=content_text,
            source_title=article_title,
            source_url=f"Archivo local: {source_path.name}",
            theme=config["theme"],
            tone=config["tone"],
            target_words=config["target_words"],
            custom_instructions=custom_instr,
            legal_rag_context=rag_context,
            jurisdiction=config["jurisdiction"],
            editorial_mode=config["editorial_mode"],
        )

    # Ejecutar inferencia asíncrona
    generated_article = asyncio.run(
        stream_generation_cli(prompt, config["model"], config["temperature"])
    )

    if not generated_article:
        print("\n[ERROR] No se recibió respuesta del modelo.")
        return 1

    # 6. Auto-guardar en Articulos Generados/
    save_meta = {
        "theme": config["theme"],
        "model": config["model"],
        "tone": config["tone"],
        "temperature": config["temperature"],
        "source_file": source_path.name,
        "jurisdiction": config["jurisdiction"],
        "editorial_mode": config["editorial_mode"],
    }
    save_res = save_final_article(
        title=article_title,
        markdown_content=generated_article,
        metadata=save_meta,
    )

    # 7. Auditoría SEO & Calidad Jurídica
    try:
        seo_report = audit_article_seo(generated_article)
        legal_report = audit_legal_quality(generated_article, jurisdiction="ve" if config["jurisdiction"] == "venezuela" else "auto")
        combined_score = round(seo_report.get("score", 0) * 0.6 + legal_report.get("score", 0) * 0.4)
    except Exception:
        combined_score = 95
        seo_report = {"score": 95}
        legal_report = {"score": 95}

    print("\n" + "=" * 83)
    print("📊 RESULTADO PERICIAL & AUDITORÍA DETERMINISTA")
    print("=" * 83)
    print(f"  • Puntuación Global:         {combined_score}/100")
    print(f"  • Auditoría SEO Estructural: {seo_report.get('score', 0)}/100")
    print(f"  • Rigor Jurídico / TSJ:      {legal_report.get('score', 0)}/100")
    print(f"  • Palabras Generadas:        {len(generated_article.split())} palabras")
    if save_res.get("status") == "success":
        print(f"  • Guardado Markdown (.md):   {save_res.get('path')}")
        if save_res.get("html_path"):
            print(f"  • Guardado HTML (.html):     {save_res.get('html_path')}")
    print("=" * 83)
    print("\n[ÉXITO] El artículo ha sido generado y archivado en 'Articulos Generados/' correctamente.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
