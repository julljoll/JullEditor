"""
Extractor de Metadatos de Sentencias del Tribunal Supremo de Justicia (TSJ).
Diseñado para archivos Markdown generados por IBM Docling / LegalProcessor.
100% Offline — Heurísticas y Expresiones Regulares sobre la estructura judicial venezolana.
"""

import json
import os
import re
from typing import Any


def extract_metadata(text: str, filename: str = "") -> dict[str, Any]:
    """
    Analiza el texto de una sentencia del TSJ y extrae su Ficha Técnica estructurada.
    """
    clean_text = text or ""
    result: dict[str, Any] = {
        "sala": "Tribunal Supremo de Justicia",
        "expediente": "",
        "numero_sentencia": "",
        "ponente": "",
        "fecha_decision": "",
        "partes": {
            "recurrente_o_demandante": "",
            "recurrido_o_demandado": ""
        },
        "materia": "",
        "delito_asunto": "",
        "decision_tipo": "",
        "leyes_citadas": [],
        "caracter_vinculante": False,
        "votos_salvados": False,
        "ratio_decidendi_sintesis": ""
    }

    # 1. SALA (incluyendo caracteres espaciados por OCR de Docling como S A L A  D E  C A S A C I O N)
    compact_upper = re.sub(r"\s+", "", clean_text[:1200].upper())
    if "SALADECASACIONPENAL" in compact_upper:
        result["sala"] = "Sala de Casación Penal"
    elif "SALADECASACIONCIVIL" in compact_upper:
        result["sala"] = "Sala de Casación Civil"
    elif "SALADECASACIONSOCIAL" in compact_upper:
        result["sala"] = "Sala de Casación Social"
    elif "SALACONSTITUCIONAL" in compact_upper:
        result["sala"] = "Sala Constitucional"
    elif "SALAPOLITICOADMINISTRATIVA" in compact_upper or "SALAPOLITICO-ADMINISTRATIVA" in compact_upper:
        result["sala"] = "Sala Político-Administrativa"
    elif "SALAELECTORAL" in compact_upper:
        result["sala"] = "Sala Electoral"
    elif "SALAPLENA" in compact_upper:
        result["sala"] = "Sala Plena"
    else:
        sala_match = re.search(
            r"(?:Sala\s+de\s+Casaci[oó]n\s+(?:Penal|Civil|Social)|Sala\s+Constitucional|Sala\s+Pol[ií]tico[\s-]Administrativa|Sala\s+Electoral|Sala\s+Plena)",
            clean_text,
            re.IGNORECASE
        )
        if sala_match:
            result["sala"] = re.sub(r"\s+", " ", sala_match.group(0)).strip().title().replace("De", "de")
        elif "penal" in filename.lower() or "scp" in filename.lower():
            result["sala"] = "Sala de Casación Penal"
        elif "civil" in filename.lower() or "scc" in filename.lower():
            result["sala"] = "Sala de Casación Civil"
        elif "constitucional" in filename.lower() or "scon" in filename.lower():
            result["sala"] = "Sala Constitucional"

    # 2. EXPEDIENTE
    # Formatos típicos TSJ: AA30-P-2024-000184, AA20-C-2023-000504, Exp. 2023-23-504
    exp_direct = re.search(r"([A-Z]{2}\d{2}\s*-\s*[A-Z]\s*-\s*\d{4}\s*-\s*\d+)", clean_text)
    if exp_direct:
        result["expediente"] = re.sub(r"\s+", "", exp_direct.group(1))
    else:
        exp_match = re.search(
            r"(?:Exp(?:ediente|\.)?\s*[:.]?\s*)([A-Z0-9\s\-]+(?:\d{4}|\d{3}))",
            clean_text,
            re.IGNORECASE
        )
        if exp_match:
            raw_exp = exp_match.group(1).strip()
            exp_clean = re.sub(r"\s*-\s*", "-", raw_exp)
            exp_clean = re.sub(r"\s+", " ", exp_clean).strip()
            first_tok = exp_clean.split()[0] if exp_clean else ""
            result["expediente"] = first_tok if len(first_tok) >= 6 else exp_clean[:35]

    # 3. NÚMERO DE SENTENCIA
    if "SCP-" in filename or "SCC-" in filename:
        fn_match = re.search(r"(?:SCP|SCC)-(\d+)", filename)
        if fn_match:
            result["numero_sentencia"] = fn_match.group(1)
    
    if not result["numero_sentencia"]:
        # Buscar en nombre del archivo patrones como 000709 o 000019
        fn_num = re.search(r"-(\d{6})-", filename)
        if fn_num:
            result["numero_sentencia"] = fn_num.group(1).lstrip("0") or fn_num.group(1)
    
    if not result["numero_sentencia"]:
        num_match = re.search(
            r"(?:Sentencia\s*N[°º\.]?\s*|N°\s*)(\d+[\d\-]*)",
            clean_text,
            re.IGNORECASE
        )
        if num_match:
            result["numero_sentencia"] = num_match.group(1).strip()

    # 4. MAGISTRADO PONENTE
    ponente_match = re.search(
        r"(?:Magistrad[oa]\s+Ponente\s*[:.]?\s*|ponencia\s+(?:a\s+la|al)?\s*Magistrad[oa]?\s*(?:Doctor[a]?)?\s*)([A-ZÁÉÍÓÚÑa-záéíóúñ\s\.]+?)(?:[\.,\n\r]|seg[uú]n|\(Ponente\))",
        clean_text,
        re.IGNORECASE
    )
    if ponente_match:
        pon_clean = ponente_match.group(1).strip()
        pon_clean = re.sub(r"^(?:Doctora?|Dr\.|Dra\.)\s+", "", pon_clean, flags=re.IGNORECASE).strip()
        words = pon_clean.split()
        if 2 <= len(words) <= 5:
            result["ponente"] = " ".join(words).title()
    
    if not result["ponente"]:
        firma_ponente = re.search(r"##?\s*([A-ZÁÉÍÓÚÑ\s]{6,40})\s*\n+\s*\(Ponente\)", clean_text, re.IGNORECASE)
        if firma_ponente:
            result["ponente"] = firma_ponente.group(1).strip().title()

    # 5. FECHA DE DECISIÓN (Priorizar fecha de cierre 'Dada, firmada y sellada...')
    fecha_cierre = re.search(
        r"Dada\s*,\s*firmada\s+y\s+sellada[\s\S]{10,250}?\ba\s+los\s+(\d{1,2}|[\w\(\)\s]+?)\s+d[ií]as\s+del\s+mes\s+de\s+(\w+)\s+de(?:l)?\s+(?:año\s+)?(?:dos\s+mil\s+\w+\s+)?\(?(\d{4})\)?",
        clean_text,
        re.IGNORECASE
    )
    if fecha_cierre:
        dia_raw = re.sub(r"[\(\)]", "", fecha_cierre.group(1)).strip()
        # Si tiene letras y números como "veintitrés (23)", extraer el número
        num_in_dia = re.search(r"\d+", dia_raw)
        dia_final = num_in_dia.group(0) if num_in_dia else dia_raw.split()[-1]
        mes_final = fecha_cierre.group(2).strip()
        ano_final = fecha_cierre.group(3).strip()
        result["fecha_decision"] = f"{dia_final} de {mes_final} de {ano_final}"
    else:
        fecha_gen = re.search(
            r"(\d{1,2})\s+de\s+(enero|febrero|marzo|abril|mayo|junio|julio|agosto|septiembre|octubre|noviembre|diciembre)\s+de\s+(\d{4})",
            clean_text,
            re.IGNORECASE
        )
        if fecha_gen:
            result["fecha_decision"] = f"{fecha_gen.group(1)} de {fecha_gen.group(2)} de {fecha_gen.group(3)}"
        else:
            iso_match = re.search(r"(\d{2})[-/](\d{2})[-/](\d{4})", clean_text)
            if iso_match:
                result["fecha_decision"] = f"{iso_match.group(1)}/{iso_match.group(2)}/{iso_match.group(3)}"

    # 6. MATERIA
    if "penal" in result["sala"].lower():
        result["materia"] = "Penal — Recurso de Casación"
    elif "civil" in result["sala"].lower():
        result["materia"] = "Civil y Mercantil — Recurso de Casación"
    elif "constitucional" in result["sala"].lower():
        result["materia"] = "Constitucional — Revisión / Vinculante"
    elif "social" in result["sala"].lower():
        result["materia"] = "Laboral y Protección — Recurso de Casación"
    else:
        result["materia"] = "Jurisprudencia TSJ"

    # 7. DELITO / ASUNTO
    delito_match = re.search(
        r"(?:delito\s+de|por\s+la\s+presunta\s+comisi[oó]n\s+del\s+delito\s+de)\s+([A-ZÁÉÍÓÚÑa-záéíóúñ\s,]+?)(?:,|\s+previsto|\s+sancionado|\.)",
        clean_text,
        re.IGNORECASE
    )
    if delito_match:
        result["delito_asunto"] = delito_match.group(1).strip().title()
    else:
        asunto_match = re.search(
            r"(?:juicio\s+por|en\s+el\s+juicio\s+por|en\s+materia\s+de)\s+([A-ZÁÉÍÓÚÑa-záéíóúñ\s,]+?)(?:,|\s+interpuesto|\s+seguido|\.)",
            clean_text,
            re.IGNORECASE
        )
        if asunto_match:
            result["delito_asunto"] = asunto_match.group(1).strip().title()

    # 8. PARTES
    rec_match = re.search(
        r"(?:ciudadano|apoderados\s+judiciales\s+del\s+ciudadano|demandante|formalizante|recurrente)\s+([A-ZÁÉÍÓÚÑ\s]{4,35})(?:,|\s+titular|\s+inscrito|\s+asistido)",
        clean_text,
        re.IGNORECASE
    )
    if rec_match:
        result["partes"]["recurrente_o_demandante"] = rec_match.group(1).strip().title()

    recdo_match = re.search(
        r"(?:a\s+favor\s+del\s+ciudadano|contra\s+(?:la\s+ciudadana|el\s+ciudadano)|demandad[oa]|recurrid[oa])\s+([A-ZÁÉÍÓÚÑ\s]{4,35})(?:,|\s+titular|\s+inscrito|\.)",
        clean_text,
        re.IGNORECASE
    )
    if recdo_match:
        result["partes"]["recurrido_o_demandado"] = recdo_match.group(1).strip().title()

    # 9. TIPO DE DECISIÓN (DISPOSITIVO)
    if re.search(r"DESESTIMA\s+POR\s+MANIFIESTAMENTE\s+INFUNDADO", clean_text, re.IGNORECASE):
        result["decision_tipo"] = "Desestimado por manifiestamente infundado"
    elif re.search(r"DECLARA\s+(?:CON\s+LUGAR|HA\s+LUGAR)", clean_text, re.IGNORECASE):
        result["decision_tipo"] = "Con Lugar"
    elif re.search(r"DECLARA\s+SIN\s+LUGAR", clean_text, re.IGNORECASE):
        result["decision_tipo"] = "Sin Lugar"
    elif re.search(r"DECRETA\s+(?:EL\s+)?SOBRESEIMIENTO", clean_text, re.IGNORECASE):
        result["decision_tipo"] = "Sobreseimiento decretado"
    elif re.search(r"INADMISIBLE", clean_text, re.IGNORECASE):
        result["decision_tipo"] = "Inadmisible"
    elif re.search(r"PERECIDO", clean_text, re.IGNORECASE):
        result["decision_tipo"] = "Perecido el recurso"
    else:
        result["decision_tipo"] = "Sentencia de Fondo"

    # 10. LEYES CITADAS
    leyes_encontradas = set()
    normas_patterns = [
        (r"art[ií]culo\s+(\d+(?:[,\s]+numeral\s+\d+)?)\s+(?:del\s+)?(C[oó]digo\s+Org[aá]nico\s+Procesal\s+Penal|COPP)", "COPP"),
        (r"art[ií]culo\s+(\d+)\s+(?:del\s+)?(C[oó]digo\s+Penal)", "Código Penal"),
        (r"art[ií]culo\s+(\d+(?:[,\s]+numeral\s+\d+)?)\s+(?:de\s+la\s+)?(Constituci[oó]n|CRBV)", "CRBV"),
        (r"art[ií]culo\s+(\d+)\s+(?:de\s+la\s+)?(Ley\s+Org[aá]nica\s+del\s+Tribunal\s+Supremo|LOTSJ)", "Ley Orgánica TSJ"),
        (r"art[ií]culo\s+(\d+)\s+(?:del\s+)?(C[oó]digo\s+de\s+Procedimiento\s+Civil|CPC)", "CPC"),
        (r"art[ií]culo\s+(\d+)\s+(?:del\s+)?(C[oó]digo\s+Civil)", "Código Civil"),
        (r"art[ií]culo\s+(\d+)\s+(?:de\s+la\s+)?(Ley\s+Especial\s+contra\s+los\s+Delitos\s+Inform[aá]ticos)", "Ley Delitos Informáticos"),
        (r"art[ií]culo\s+(\d+)\s+(?:de\s+la\s+)?(Ley\s+sobre\s+Mensajes\s+de\s+Datos)", "Ley Mensajes de Datos"),
    ]
    for pattern, label in normas_patterns:
        matches = re.finditer(pattern, clean_text, re.IGNORECASE)
        for m in matches:
            art_num = re.sub(r"\s+", " ", m.group(1)).strip()
            leyes_encontradas.add(f"{label} Art. {art_num}")

    result["leyes_citadas"] = sorted(leyes_encontradas)[:12]

    # 11. CARÁCTER VINCULANTE
    if "vinculante" in clean_text.lower() and ("sala constitucional" in result["sala"].lower() or "artículo 335" in clean_text.lower() or "art. 335" in clean_text.lower()):
        result["caracter_vinculante"] = True
    else:
        result["caracter_vinculante"] = False

    # 12. VOTOS SALVADOS / CONCURRENTES
    if re.search(r"voto\s+salvado|voto\s+concurrente|salva\s+el\s+voto|concurre\s+con\s+el\s+voto", clean_text, re.IGNORECASE):
        result["votos_salvados"] = True

    # 13. SÍNTESIS DE LA RATIO DECIDENDI / DISPOSITIVO
    # Buscar sección D E C I S I Ó N o DECISIÓN con espaciado flexible
    dec_match = re.search(
        r"##?\s*D\s*E\s*C\s*I\s*S\s*I\s*[OÓ]\s*N\s*\n+([\s\S]+?)(?:\n\s*Publ|\n\s*Dada|\n\s*##|$)",
        clean_text,
        re.IGNORECASE
    )
    if dec_match:
        sintesis = re.sub(r"\s+", " ", dec_match.group(1)).strip()
        result["ratio_decidendi_sintesis"] = sintesis[:500] + "..." if len(sintesis) > 500 else sintesis

    return result


def extract_from_file(filepath: str) -> dict[str, Any]:
    """Carga un archivo .md de sentencia y devuelve sus metadatos extraídos."""
    if not os.path.exists(filepath):
        raise FileNotFoundError(f"Archivo no encontrado: {filepath}")
    with open(filepath, encoding="utf-8", errors="ignore") as f:
        content = f.read()
    filename = os.path.basename(filepath)
    return extract_metadata(content, filename)


if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description="Extractor de metadatos de sentencias TSJ")
    parser.add_argument("path", help="Ruta al archivo Markdown (.md) de la sentencia")
    parser.add_argument("--pretty", action="store_true", help="Imprimir JSON formateado")
    args = parser.parse_args()

    meta = extract_from_file(args.path)
    if args.pretty:
        print(json.dumps(meta, indent=2, ensure_ascii=False))
    else:
        print(json.dumps(meta, ensure_ascii=False))
