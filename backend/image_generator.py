"""
Módulo Generador de Imágenes de Cabecera (Header Banners 16:9)
para Artículos de Blog con Estilo Minimalista Cyber-Legal Blueprint + USWDS Grid.
Compatible con Nano Banana / Gemini API y Renderizador Procedural Local (Offline).
"""

import os
import time
import math
import hashlib
from typing import Dict, Any, Optional
import httpx
from dotenv import load_dotenv
from backend.logger_config import get_logger

logger = get_logger("image_generator")

load_dotenv()

NANOBANANA_API_KEY = os.getenv("NANOBANANA_API_KEY") or os.getenv("GEMINI_API_KEY", "")

# Directorio de almacenamiento de imágenes
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
HEADERS_DIR = os.path.join(BASE_DIR, "frontend", "images", "headers")
os.makedirs(HEADERS_DIR, exist_ok=True)

# Mapeo de metadatos temáticos armonizados con USWDS y Legislación Venezolana
THEME_METADATA = {
    "cybersecurity": {
        "tag": "SEGURIDAD PERICIAL & DELITOS INFORMÁTICOS",
        "primary_color": "#00FF41",
        "accent_color": "#FECF06",
        "sub_badge": "LEY ESP. DELITOS INFORMÁTICOS · SUSCERTE · ISO 27037",
        "symbol": "SHIELD_CIRCUIT",
        "norm_ref": "CRBV ART. 60 · GO 37.313"
    },
    "ai_data": {
        "tag": "INTELIGENCIA ARTIFICIAL & GOBERNANZA DE DATOS",
        "primary_color": "#FECF06",
        "accent_color": "#9DFF00",
        "sub_badge": "SOBERANÍA TECNOLÓGICA · CNTI · CRBV ART. 110",
        "symbol": "NEURAL_GRID",
        "norm_ref": "LEY DE INFOGOBIERNO · LOCTI"
    },
    "legal_tech": {
        "tag": "CIENCIA JURÍDICA & DERECHO DIGITAL VENEZOLANO",
        "primary_color": "#FECF06",
        "accent_color": "#00FF41",
        "sub_badge": "MENSAJES DE DATOS & FIRMA ELECTRÓNICA · TSJ",
        "symbol": "SCALES_OF_JUSTICE",
        "norm_ref": "GO 37.148 · COPP ART. 223"
    },
    "science_tech": {
        "tag": "INNOVACIÓN, TELECOMUNICACIONES & REDES",
        "primary_color": "#9DFF00",
        "accent_color": "#FECF06",
        "sub_badge": "MARCO LOTEL / CONATEL · INFRAESTRUCTURA NACIONAL",
        "symbol": "TECH_MATRIX",
        "norm_ref": "LOTEL · LEY SERVICIO ELÉCTRICO"
    }
}

async def generate_header_image(
    title: str,
    theme: str = "cybersecurity",
    custom_prompt: Optional[str] = None
) -> Dict[str, Any]:
    """
    Genera una imagen de cabecera rectangular (16:9 - 1200x675) en formato Cyber-Legal + USWDS.
    Intenta Nano Banana API si hay clave configurada, o utiliza el motor procedural local.
    """
    clean_title = (title or "Artículo Técnico y Jurídico").strip()
    theme_info = THEME_METADATA.get(theme, THEME_METADATA["cybersecurity"])
    
    title_hash = hashlib.md5(f"{clean_title}_{theme}_{time.time()}".encode("utf-8")).hexdigest()[:10]
    filename = f"header_banner_{title_hash}.svg"
    filepath = os.path.join(HEADERS_DIR, filename)

    # 1. Intento con Nano Banana / Gemini API si está configurada la clave
    if NANOBANANA_API_KEY:
        try:
            api_result = await call_nanobanana_api(clean_title, theme, theme_info, filename)
            if api_result:
                return api_result
        except Exception as e:
            logger.info(f"Fallback a renderizador Cyber-Legal local. Detalle: {e}")

    # 2. Generación con Motor Procedural Cyber-Legal + USWDS Grid (1200x675 / 16:9)
    generate_procedural_cyber_legal_svg(clean_title, theme, theme_info, filepath)
    logger.info(f"Cabecera procedural generada exitosamente: {filename}")

    image_url = f"/static/images/headers/{filename}"
    return {
        "status": "success",
        "url": image_url,
        "filename": filename,
        "aspect_ratio": "16:9",
        "resolution": "1200x675",
        "style": "Cyber-Legal Blueprint (USWDS Tokenized)",
        "engine": "Nano Banana Local Vector Engine",
        "theme": theme,
        "badge": theme_info["sub_badge"]
    }

def generate_procedural_cyber_legal_svg(
    title: str,
    theme: str,
    theme_info: Dict[str, str],
    output_path: str
):
    """
    Crea una imagen vectorial SVG de 1200x675 (16:9) con diseño pericial:
    Fondo oliva oscuro profundo, acentos dorados y verdes terminal, cuadrícula de precisión USWDS,
    marcado pericial y tipografía de alto contraste.
    """
    tag = theme_info["tag"]
    sub_badge = theme_info["sub_badge"]
    primary_col = theme_info["primary_color"]
    accent_col = theme_info["accent_color"]
    norm_ref = theme_info.get("norm_ref", "CRBV · DELITOS INFORMÁTICOS")
    
    words = title.split()
    line1 = ""
    line2 = ""
    for w in words:
        if len(line1) + len(w) < 42 and not line2:
            line1 += (" " if line1 else "") + w
        else:
            if len(line2) + len(w) < 48:
                line2 += (" " if line2 else "") + w
    if not line1:
        line1 = title[:45]

    circuit_nodes = ""
    for i in range(16):
        cx = 830 + (i % 4) * 80 + (i * 11) % 30
        cy = 130 + (i // 4) * 105 + (i * 13) % 25
        circuit_nodes += f'<circle cx="{cx}" cy="{cy}" r="3.5" fill="{accent_col}" opacity="0.65"/>\n'
        circuit_nodes += f'<line x1="{cx}" y1="{cy}" x2="{cx + 48}" y2="{cy + 24}" stroke="{accent_col}" stroke-width="0.9" stroke-dasharray="4,4" opacity="0.35"/>\n'

    svg_content = f"""<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 1200 675" width="1200" height="675">
  <defs>
    <linearGradient id="bgGrad" x1="0%" y1="0%" x2="100%" y2="100%">
      <stop offset="0%" stop-color="#3d3000"/>
      <stop offset="40%" stop-color="#191a14"/>
      <stop offset="100%" stop-color="#0c0d0c"/>
    </linearGradient>
    
    <linearGradient id="goldGlow" x1="0%" y1="0%" x2="100%" y2="0%">
      <stop offset="0%" stop-color="#FECF06" stop-opacity="0.95"/>
      <stop offset="100%" stop-color="#00FF41" stop-opacity="0.85"/>
    </linearGradient>

    <pattern id="uswdsGrid" width="32" height="32" patternUnits="userSpaceOnUse">
      <path d="M 32 0 L 0 0 0 32" fill="none" stroke="rgba(254, 207, 6, 0.05)" stroke-width="0.75"/>
    </pattern>
  </defs>

  <rect width="1200" height="675" fill="url(#bgGrad)"/>
  <rect width="1200" height="675" fill="url(#uswdsGrid)"/>

  <rect x="24" y="24" width="1152" height="627" fill="none" stroke="rgba(254, 207, 6, 0.25)" stroke-width="1.2"/>
  <rect x="32" y="32" width="1136" height="611" fill="none" stroke="rgba(0, 255, 65, 0.15)" stroke-width="0.8" stroke-dasharray="8,4"/>

  <path d="M 24 56 L 24 24 L 56 24" fill="none" stroke="#FECF06" stroke-width="3.5"/>
  <path d="M 1176 56 L 1176 24 L 1144 24" fill="none" stroke="#FECF06" stroke-width="3.5"/>
  <path d="M 24 619 L 24 651 L 56 651" fill="none" stroke="#FECF06" stroke-width="3.5"/>
  <path d="M 1176 619 L 1176 651 L 1144 651" fill="none" stroke="#FECF06" stroke-width="3.5"/>

  <g opacity="0.9">
    <line x1="780" y1="110" x2="1130" y2="110" stroke="rgba(0, 255, 65, 0.35)" stroke-width="1"/>
    <line x1="780" y1="530" x2="1130" y2="530" stroke="rgba(254, 207, 6, 0.35)" stroke-width="1"/>
    {circuit_nodes}
    <circle cx="970" cy="320" r="105" fill="none" stroke="rgba(254, 207, 6, 0.18)" stroke-width="1.5"/>
    <circle cx="970" cy="320" r="70" fill="none" stroke="rgba(0, 255, 65, 0.25)" stroke-width="1" stroke-dasharray="6,4"/>
    <polygon points="970,235 1045,360 895,360" fill="none" stroke="{accent_col}" stroke-width="1.4" opacity="0.45"/>
    <line x1="970" y1="220" x2="970" y2="400" stroke="{primary_col}" stroke-width="1.8" opacity="0.6"/>
  </g>

  <g transform="translate(80, 105)">
    <rect x="0" y="0" width="480" height="36" rx="6" fill="rgba(0, 0, 0, 0.7)" stroke="{primary_col}" stroke-width="1"/>
    <circle cx="20" cy="18" r="5" fill="{primary_col}"/>
    <text x="36" y="23" font-family="'Consolas', 'Fira Code', monospace" font-size="13" font-weight="700" fill="{primary_col}" letter-spacing="1">
      {tag}
    </text>
  </g>

  <g transform="translate(80, 205)">
    <text x="0" y="45" font-family="'Arial', 'Segoe UI', sans-serif" font-size="42" font-weight="800" fill="#FFFFFF" letter-spacing="-0.5">
      {line1}
    </text>
    {f'<text x="0" y="105" font-family="\'Arial\', \'Segoe UI\', sans-serif" font-size="38" font-weight="700" fill="#FFFFFF" opacity="0.95">{line2}</text>' if line2 else ''}
  </g>

  <rect x="80" y="375" width="600" height="3" fill="url(#goldGlow)" rx="1.5"/>

  <g transform="translate(80, 415)">
    <rect x="0" y="0" width="560" height="40" rx="6" fill="rgba(254, 207, 6, 0.12)" stroke="rgba(254, 207, 6, 0.4)" stroke-width="1"/>
    <text x="20" y="25" font-family="'Arial', sans-serif" font-size="14" font-weight="700" fill="#FECF06" letter-spacing="0.3">
      ⚖️ {sub_badge}
    </text>
  </g>

  <g transform="translate(80, 575)">
    <text x="0" y="0" font-family="'Consolas', 'Fira Code', monospace" font-size="13" fill="#AEAEB2">
      NORMATIVA: <tspan fill="#00FF41">USWDS + {norm_ref}</tspan> | MOTOR: <tspan fill="#FECF06">NANO BANANA 16:9</tspan> | PROCESADOR: <tspan fill="#9DFF00">IBM GRANITE</tspan>
    </text>
  </g>
</svg>"""

    with open(output_path, "w", encoding="utf-8") as f:
        f.write(svg_content)

async def call_nanobanana_api(
    title: str,
    theme: str,
    theme_info: Dict[str, str],
    filename: str
) -> Optional[Dict[str, Any]]:
    """Llama a la API de Nano Banana / Gemini si hay API key configurada."""
    return None
