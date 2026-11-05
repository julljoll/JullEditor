"""
Perfiles de voz de abogado (Venezuela / Colombia), glosarios jurídicos,
listas anti-calco y normas autorizadas por jurisdicción.

Los datos son declarativos para poder ampliarse sin tocar la lógica.
"""

import re
from typing import Any

# ------------------------------------------------------------------------------
# JURISDICCIONES
# ------------------------------------------------------------------------------

JURISDICTION_LABELS: dict[str, str] = {
    "ve": "República Bolivariana de Venezuela 🇻🇪",
    "co": "República de Colombia 🇨🇴",
    "intl": "Internacional / Estándares Globales 🌐",
}

LOCALE_BY_JURISDICTION = {"ve": "es-VE", "co": "es-CO", "intl": "es"}

_VE_HINTS = ("venezuela", "venezolan", "gaceta oficial", "tsj", "crbv", "inpreabogado")
_CO_HINTS = ("colombia", "colombian", "diario oficial", "corte constitucional", "acción de tutela",
             "accion de tutela", "habeas data", "superintendencia de industria")


def resolve_jurisdiction(jurisdiction: str = "auto", text: str = "", theme: str = "",
                         persona: str = "", has_ve_rag: bool = False) -> str:
    """Devuelve 've' | 'co' | 'intl'. Prioridad: selección explícita > perfil > texto > tema."""
    j = (jurisdiction or "auto").lower()
    if j in ("venezuela", "ve"):
        return "ve"
    if j in ("colombia", "co"):
        return "co"
    if j in ("international", "intl"):
        return "intl"

    persona_def = PERSONAS.get(persona)
    if persona_def and persona_def.get("jurisdiction") in ("ve", "co"):
        return persona_def["jurisdiction"]

    low = (text or "").lower()
    ve_score = sum(low.count(h) for h in _VE_HINTS)
    co_score = sum(low.count(h) for h in _CO_HINTS)
    if co_score > ve_score:
        return "co"
    if ve_score > 0 or theme == "legal_tech" or has_ve_rag:
        return "ve"
    return "intl"


# ------------------------------------------------------------------------------
# NORMAS AUTORIZADAS (únicas citables sin RAG). Verificar contra fuente oficial.
# ------------------------------------------------------------------------------

AUTHORIZED_NORMS: dict[str, list[str]] = {
    "ve": [
        "Constitución de la República Bolivariana de Venezuela (CRBV, 1999)",
        "Ley Especial contra los Delitos Informáticos (G.O. Nº 37.313, 2001)",
        "Decreto con Rango, Valor y Fuerza de Ley sobre Mensajes de Datos y Firmas Electrónicas (G.O. Nº 37.148, 2001)",
        "Código Orgánico Procesal Penal (COPP)",
        "Código de Procedimiento Civil (CPC)",
        "Código Civil venezolano",
        "Ley de Infogobierno",
    ],
    "co": [
        "Constitución Política de Colombia de 1991",
        "Decreto 2591 de 1991 (acción de tutela)",
        "Ley 1273 de 2009 (delitos informáticos; protección de la información y de los datos)",
        "Ley 1581 de 2012 (régimen general de protección de datos personales)",
        "Ley 1266 de 2008 (habeas data financiero)",
        "Ley 527 de 1999 (mensajes de datos, comercio electrónico y firmas digitales)",
        "Ley 599 de 2000 (Código Penal)",
        "Ley 906 de 2004 (Código de Procedimiento Penal)",
        "Ley 1564 de 2012 (Código General del Proceso)",
        "Ley 1437 de 2011 (CPACA)",
        "Ley 1755 de 2015 (derecho de petición)",
        "Ley 1123 de 2007 (Código Disciplinario del Abogado)",
        "Ley 1712 de 2014 (transparencia y acceso a la información pública)",
    ],
}

# ------------------------------------------------------------------------------
# GLOSARIOS (semilla ampliable). tags: palabras de consulta que activan el término.
# ------------------------------------------------------------------------------

def _t(term: str, use: str, tags: str, avoid: str = "") -> dict[str, Any]:
    return {"term": term, "use": use, "tags": tags.split(), "avoid": avoid}


GLOSSARY: dict[str, list[dict[str, Any]]] = {
    "ve": [
        _t("amparo constitucional", "Acción para el restablecimiento inmediato de derechos y garantías constitucionales lesionados.", "amparo derechos garantías constitucional", "No llamarlo 'tutela': en Venezuela la tutela es una institución de guarda de menores."),
        _t("recurso de casación", "Medio extraordinario ante el Tribunal Supremo de Justicia por infracción de ley o quebrantamiento de formas procesales.", "casación recurso sentencia apelación"),
        _t("medida cautelar innominada", "Medida que el juez acuerda para evitar lesiones graves o de difícil reparación mientras se decide el juicio.", "cautelar medida urgencia riesgo"),
        _t("caducidad", "Extinción del derecho a accionar por el vencimiento de un lapso fijado por la ley; no admite interrupción.", "caducidad lapso plazo demanda"),
        _t("prescripción", "Modo de extinguir la acción por el transcurso del tiempo; puede interrumpirse.", "prescripción acción tiempo delito"),
        _t("cosa juzgada", "Efecto de la sentencia firme que impide un nuevo juicio sobre el mismo asunto.", "sentencia firme juicio"),
        _t("libelo de la demanda", "Escrito que contiene la pretensión del demandante.", "demanda libelo juicio civil"),
        _t("promoción de pruebas", "Lapso y acto en que las partes proponen sus medios probatorios.", "pruebas evidencia promoción probatorio"),
        _t("prueba electrónica / mensaje de datos", "Información en formato electrónico con eficacia probatoria equivalente a la de los documentos escritos.", "prueba electrónica digital mensaje datos evidencia firma"),
        _t("cadena de custodia", "Procedimiento que garantiza la integridad y trazabilidad de la evidencia desde su colección hasta el juicio.", "cadena custodia evidencia forense pericia"),
        _t("experticia informática", "Prueba pericial practicada sobre equipos o datos digitales.", "experticia pericia forense informática"),
        _t("acceso indebido", "Conducta tipificada en la Ley Especial contra los Delitos Informáticos.", "acceso indebido hacking delito informático sistema"),
        _t("sabotaje o daño a sistemas", "Conducta tipificada en la Ley Especial contra los Delitos Informáticos.", "sabotaje daño sistemas malware ransomware"),
        _t("espionaje informático", "Obtención indebida de datos o información reservada mediante medios informáticos.", "espionaje datos información confidencial"),
        _t("Gaceta Oficial", "Órgano de publicación oficial de las normas; se cita con número y fecha.", "ley decreto norma publicación gaceta"),
        _t("Sala Constitucional del Tribunal Supremo de Justicia", "Intérprete máximo de la Constitución; sus interpretaciones son vinculantes.", "constitucional tsj sala interpretación vinculante"),
        _t("Ministerio Público", "Titular de la acción penal; dirige la investigación.", "fiscal fiscalía investigación penal denuncia"),
        _t("CICPC", "Cuerpo de Investigaciones Científicas, Penales y Criminalísticas.", "cicpc investigación penal denuncia"),
        _t("nulidad", "Sanción procesal o sustantiva que priva de efectos a un acto viciado.", "nulidad acto vicio"),
        _t("debido proceso", "Garantía constitucional de defensa, juez natural y procedimiento legal.", "debido proceso defensa garantía"),
        _t("notificación / citación", "Actos de comunicación procesal; la citación emplaza al demandado, la notificación informa actuaciones.", "notificación citación demandado proceso"),
        _t("SAREN", "Servicio Autónomo de Registros y Notarías.", "registro notaría documento autenticación"),
        _t("SENIAT", "Servicio Nacional Integrado de Administración Aduanera y Tributaria.", "tributo impuesto seniat fiscal"),
        _t("INPREABOGADO", "Instituto de Previsión Social del Abogado, cuyo número identifica al profesional.", "abogado matrícula inpreabogado ejercicio"),
        _t("fraude procesal", "Maquinación o artificio para engañar al juez y perjudicar a un tercero.", "fraude proceso engaño"),
        _t("mismidad de la evidencia digital", "Principio pericial que exige demostrar que la prueba electrónica presentada en juicio es idéntica e inalterada respecto a la colectada en el sitio del suceso.", "mismidad evidencia digital forense integridad autenticidad hash"),
        _t("hash criptográfico / algoritmo de integridad", "Función matemática unidireccional (SHA-256 / SHA-3) que genera una huella digital única para garantizar la indemnidad del archivo o imagen forense.", "hash sha256 sha3 md5 integridad firma digital huella forense"),
        _t("imagen forense bit a bit", "Copia idéntica física y lógica del soporte de almacenamiento digital realizada sin alterar la fuente original.", "imagen forense bit clonación adquisición evidencia soporte"),
        _t("Manual Único de Cadena de Custodia (2017)", "Instrumento normativo obligatorio dictado por el Ministerio Público y el CICPC para fijar, colectar, embalar y trasladar evidencias físicas y digitales.", "manual cadena custodia evidencia cicpc ministerio público resolución"),
        _t("CENIF (Centro Nacional de Informática Forense)", "Órgano oficial pericial creado en Gaceta Oficial Nº 39.847 para experticias digitales de alta complejidad en Venezuela.", "cenif forense peritaje informático centro nacional gaceta 39847"),
        _t("SUSCERTE", "Superintendencia de Servicios de Certificación Electrónica, autoridad nacional en materia de firmas electrónicas y seguridad informática.", "suscerte certificación electrónica firma digital vencert seguridad"),
        _t("equivalencia funcional", "Principio de la Ley sobre Mensajes de Datos que confiere al documento electrónico el mismo valor probatorio que al soporte en papel.", "equivalencia funcional mensaje datos firma electrónica valor probatorio"),
        _t("ISO/IEC 27037", "Estándar internacional de referencia para la identificación, recolección, adquisición y preservación de evidencia digital.", "iso 27037 estándar evidencia digital preservación adquisición"),
        _t("ponencia / magistrado ponente", "Magistrado encargado de redactar el proyecto de sentencia sometido a consideración de la Sala del TSJ.", "ponencia ponente magistrado sala redactar proyecto"),
        _t("ratio decidendi", "Razón jurídica determinante y fundamento directo que resuelve el dispositivo de la sentencia con fuerza de precedente.", "ratio decidendi precedente fundamento doctrina jurisprudencia fallo"),
        _t("obiter dictum", "Argumento o consideración incidental expresada por el tribunal que no constituye el fundamento vinculante del fallo.", "obiter dictum incidental argumento consideración"),
        _t("voto salvado", "Opinión razonada y disidente de un magistrado que discrepa de la decisión mayoritaria del tribunal.", "voto salvado disidente discrepancia minoría"),
        _t("voto concurrente", "Opinión de un magistrado que coincide con el dispositivo final pero difiere de la motivación o añade fundamentos adicionales.", "voto concurrente motivación coincidencia fundamentos"),
        _t("carácter vinculante", "Efecto obligatorio y erga omnes de las interpretaciones constitucionales del TSJ (art. 335 CRBV) para todos los tribunales de la República.", "carácter vinculante obligatorio erga omnes precedente 335 crbv"),
        _t("revisión constitucional", "Facultad extraordinaria de la Sala Constitucional para revisar sentencias definitivamente firmes de amparo o de otras Salas que violen la Constitución.", "revisión constitucional amparo sala extraordinaria"),
        _t("control difuso de la constitucionalidad", "Facultad y deber de todo juez de la República de desaplicar una norma que colida con la Constitución (art. 334 CRBV).", "control difuso desaplicar norma juez 334 crbv inconstitucional"),
        _t("control concentrado de la constitucionalidad", "Competencia exclusiva de la Sala Constitucional del TSJ para declarar la nulidad total o parcial de leyes y normas con rango de ley (art. 334 y 336 CRBV).", "control concentrado nulidad ley sala constitucional 336 crbv"),
    ],
    "co": [
        _t("acción de tutela", "Mecanismo preferente y sumario para la protección inmediata de derechos fundamentales (art. 86 C.P.).", "tutela derechos fundamentales amparo", "No llamarla 'recurso de amparo': es el término de otros países."),
        _t("derecho de petición", "Derecho a presentar solicitudes respetuosas a las autoridades y obtener respuesta de fondo, clara y oportuna.", "petición solicitud autoridad respuesta"),
        _t("habeas data", "Derecho a conocer, actualizar y rectificar la información personal en bases de datos.", "habeas data datos personales información titular"),
        _t("responsable y encargado del tratamiento", "Roles definidos en la Ley 1581 de 2012: quien decide y quien trata datos por cuenta de otro.", "tratamiento datos personales responsable encargado ley 1581"),
        _t("autorización del titular", "Consentimiento previo, expreso e informado para el tratamiento de datos personales.", "autorización consentimiento titular datos"),
        _t("Superintendencia de Industria y Comercio (SIC)", "Autoridad de protección de datos personales y de la competencia y consumo.", "sic superintendencia datos consumidor competencia"),
        _t("radicado", "Número que identifica el expediente o la solicitud ante la autoridad.", "radicado expediente proceso trámite"),
        _t("providencia", "Decisión judicial; comprende autos y sentencias.", "providencia auto sentencia decisión"),
        _t("ratio decidendi", "Razón de la decisión que constituye precedente.", "precedente sentencia jurisprudencia corte"),
        _t("obiter dictum", "Argumento incidental de una sentencia, sin fuerza vinculante.", "sentencia jurisprudencia corte"),
        _t("sentencia de unificación (SU)", "Providencia de la Corte Constitucional que unifica su jurisprudencia.", "unificación sentencia corte constitucional su"),
        _t("cosa juzgada", "Efecto de la providencia ejecutoriada que impide reabrir el mismo debate.", "sentencia ejecutoriada juicio"),
        _t("caducidad", "Pérdida de la oportunidad de ejercer la acción por el paso del término legal.", "caducidad término demanda plazo"),
        _t("prescripción", "Extinción de la acción o del derecho por el transcurso del tiempo.", "prescripción tiempo acción"),
        _t("debido proceso", "Garantía del art. 29 de la Constitución.", "debido proceso defensa garantía"),
        _t("Código General del Proceso (CGP)", "Ley 1564 de 2012, estatuto procesal civil, comercial, agrario y de familia.", "proceso civil demanda cgp comercial"),
        _t("medios de control", "Acciones ante la jurisdicción de lo contencioso administrativo (CPACA).", "contencioso administrativo nulidad restablecimiento estado"),
        _t("medidas cautelares", "Instrumentos para asegurar la efectividad de la decisión final.", "cautelar medida protección urgencia"),
        _t("recurso de apelación", "Medio de impugnación para que el superior revise la decisión.", "apelación recurso impugnación"),
        _t("delitos informáticos", "Conductas tipificadas por la Ley 1273 de 2009 que protegen la información y los datos.", "delito informático ciberseguridad acceso abusivo datos"),
        _t("acceso abusivo a un sistema informático", "Delito de la Ley 1273 de 2009 (art. 269A del Código Penal).", "acceso abusivo sistema hacking"),
        _t("Fiscalía General de la Nación", "Entidad que investiga y ejerce la acción penal.", "fiscalía denuncia investigación penal"),
        _t("cadena de custodia", "Procedimiento para garantizar la autenticidad e integridad de los elementos materiales probatorios.", "cadena custodia evidencia forense prueba"),
        _t("mensaje de datos", "Información generada, enviada o archivada por medios electrónicos, con valor probatorio (Ley 527 de 1999).", "mensaje datos electrónico firma digital prueba"),
        _t("Tarjeta Profesional", "Documento que habilita el ejercicio de la abogacía (T.P.).", "abogado tarjeta profesional ejercicio"),
        _t("Cámara de Comercio y RUES", "Registro mercantil y Registro Único Empresarial y Social.", "registro mercantil empresa rues cámara comercio"),
        _t("conciliación extrajudicial en derecho", "Requisito de procedibilidad en varias materias.", "conciliación requisito procedibilidad"),
    ],
}

# Calcos y errores frecuentes (aplican a ambos países)
ANTI_CALCO: list[dict[str, str]] = [
    {"bad": r"aplicar para", "good": "solicitar / postularse a"},
    {"bad": r"realizar una demanda", "good": "interponer o presentar una demanda"},
    {"bad": r"hacer una denuncia", "good": "presentar una denuncia / denunciar"},
    {"bad": r"en orden a", "good": "con el fin de / para"},
    {"bad": r"es el caso de que", "good": "ocurre que / sucede que"},
    {"bad": r"basado en que", "good": "con base en que / debido a que"},
    {"bad": r"ley de protección de datos\b(?! personales)", "good": "identificar la norma concreta (p. ej. Ley 1581 de 2012 en Colombia)"},
    {"bad": r"\bde acuerdo a\b", "good": "de acuerdo con"},
]

# Frases de promesa de resultado (ética publicitaria del abogado)
PROMISE_PATTERNS: list[str] = [
    r"garantiz(?:amos|ado|ada)\b",
    r"100\s?%\s?(?:efectiv|seguro|garantiz)",
    r"gane (?:su|tu) caso",
    r"resultado asegurado",
    r"sin riesgo alguno",
    r"éxito (?:total|asegurado|garantizado)",
]

# Términos de la otra jurisdicción (alerta de contaminación)
FOREIGN_MARKERS: dict[str, list[str]] = {
    "co": [r"Gaceta Oficial", r"Tribunal Supremo de Justicia", r"\bCRBV\b", r"INPREABOGADO", r"\bSENIAT\b", r"\bCICPC\b"],
    "ve": [r"acción de tutela", r"Corte Constitucional de Colombia", r"Ley 1581", r"\bSIC\b", r"Fiscalía General de la Nación", r"Tarjeta Profesional"],
}

DISCLAIMER_TEXT = (
    "Este contenido es informativo y no constituye asesoría legal ni crea una relación "
    "abogado-cliente. Cada caso requiere análisis particular por un profesional del derecho."
)

DISCLAIMER_PATTERN = re.compile(r"no constituye (?:asesor[ií]a|consejo) (?:legal|jur[ií]dic)", re.IGNORECASE)

# ------------------------------------------------------------------------------
# PERFILES DE VOZ
# ------------------------------------------------------------------------------

PERSONAS: dict[str, dict[str, Any]] = {
    "revista_cientifica_law_tech": {
        "jurisdiction": "ve",
        "label": "Revista Científica Arbitrada (Derecho & Computación Forense — Nivel Universidad)",
        "register": (
            "Académico-forense, doctoral y de máxima precisión dogmática. "
            "Español formal venezolano culto con terminología científica e informática bilingüe. "
            "Uso de tercera persona o plural de modestia ('concluimos en este estudio'). "
            "Cero modismos coloquiales ni lenguaje de marketing."
        ),
        "formulas": [
            "a tenor de lo previsto en la legislación venezolana",
            "de conformidad con el estándar internacional ISO/IEC 27037",
            "en observancia del Manual Único de Cadena de Custodia de Evidencias Físicas",
            "a la luz de la doctrina pacífica de la Sala Constitucional del Tribunal Supremo de Justicia",
            "desde la perspectiva dogmática y pericial forense",
            "el mensaje de datos analizado ostenta plena eficacia probatoria a tenor de la ley",
            "preservando el principio de mismidad y cotejo de hash criptográfico SHA-256",
        ],
        "structure": "academic_law_tech_review",
    },
    "analista_tsj_revista": {
        "jurisdiction": "ve",
        "label": "📰 Analista Jurisprudencial TSJ — Revista Digital Educativa",
        "register": (
            "Profesional-educativo de revista digital: español venezolano culto, pedagógico y accesible. "
            "Combina rigurosidad doctrinal con claridad explicativa para juristas, estudiantes de derecho y público profesional interesado. "
            "Uso de segunda persona del plural ('analizamos', 'observamos') para generar cercanía académica. "
            "Evita la solemnidad forense pura: busca el equilibrio entre el análisis técnico-jurídico y la divulgación didáctica de alto nivel."
        ),
        "formulas": [
            "la Sala estableció con carácter vinculante que",
            "el criterio sostenido por la ponencia razona",
            "en la parte motiva de la decisión se advierte",
            "el dispositivo del fallo resuelve",
            "la ratio decidendi de esta sentencia radica en",
            "el voto salvado/concurrente del Magistrado X plantea",
            "a la luz de la doctrina pacífica de esta Sala",
            "el precedente fijado por la Sala Constitucional en sentencia vinculante",
            "resulta de particular interés pedagógico destacar",
            "el Tribunal Supremo de Justicia interpretó el alcance de",
            "desde la perspectiva del principio de progresividad",
            "en atención al principio de intervención mínima del derecho penal",
        ],
        "structure": "analisis_sentencia_tsj",
    },
    "abogado_ve_doctrinal": {
        "jurisdiction": "ve",
        "label": "Abogado Venezolano — Doctrinal",
        "register": "Forense, solemne y preciso. Español venezolano culto, tercera persona o plural de modestia ('en nuestro criterio'). Sin modismos coloquiales.",
        "formulas": ["a tenor de lo previsto en", "de conformidad con", "sin perjuicio de", "en criterio de la Sala Constitucional del Tribunal Supremo de Justicia", "resulta oportuno precisar que"],
        "structure": "ird",
    },
    "abogado_ve_litigante": {
        "jurisdiction": "ve",
        "label": "Abogado Venezolano — Litigante",
        "register": "Práctico y orientado a la actuación: pasos, lapsos, escritos y riesgos procesales. Español venezolano culto, directo y firme.",
        "formulas": ["el lapso para", "lo procedente es", "se recomienda consignar", "so pena de caducidad", "a los fines de"],
        "structure": "ruta",
    },
    "abogado_ve_explicativo": {
        "jurisdiction": "ve",
        "label": "Abogado Venezolano — Explicativo",
        "register": "Claro y cercano para público general, pero con terminología jurídica correcta explicada entre paréntesis. Español venezolano culto.",
        "formulas": ["en términos sencillos", "dicho de otra manera", "lo que esto significa en la práctica es", "conviene tener presente"],
        "structure": "divulgacion",
    },
    "abogado_co_doctrinal": {
        "jurisdiction": "co",
        "label": "Abogado Colombiano — Doctrinal",
        "register": "Académico y técnico-jurídico. Español colombiano profesional, trato de 'usted' cuando se interpela al lector. Análisis de precedente (ratio decidendi).",
        "formulas": ["de acuerdo con el artículo", "la Corte Constitucional ha sostenido", "en virtud de", "so pena de", "sin perjuicio de", "resulta pertinente señalar"],
        "structure": "ird",
    },
    "abogado_co_litigante": {
        "jurisdiction": "co",
        "label": "Abogado Colombiano — Litigante",
        "register": "Operativo: acción procedente, términos, requisitos y pruebas. Español colombiano profesional, directo y preciso.",
        "formulas": ["el término para", "procede la acción de", "deberá acreditar", "se radica ante", "so pena de"],
        "structure": "ruta",
    },
    "abogado_co_explicativo": {
        "jurisdiction": "co",
        "label": "Abogado Colombiano — Explicativo",
        "register": "Cercano y formal ('usted'); explica los tecnicismos para ciudadanos y empresas sin perder precisión.",
        "formulas": ["en palabras sencillas", "esto quiere decir que", "tenga presente que", "en la práctica"],
        "structure": "divulgacion",
    },
    "consultor_corporativo": {
        "jurisdiction": "auto",
        "label": "Consultor Jurídico Corporativo",
        "register": "Ejecutivo: riesgo, cumplimiento (compliance), impacto y decisiones. Frases breves, matriz riesgo/acción.",
        "formulas": ["el riesgo principal es", "se recomienda priorizar", "impacto estimado", "plan de mitigación"],
        "structure": "ejecutivo",
    },
}

_STRUCTURES = {
    "academic_law_tech_review": (
        "Estructura formal de Revista Científica Arbitrada (Law & Tech Review): "
        "1) Título formal bilingüe (Español / Inglés); "
        "2) Abstract estructurado bilingüe (Problema, Metodología, Hallazgos, Conclusiones) + Descriptores/Keywords; "
        "3) Párrafo Answer-First (40-60 palabras) para motores de IA; "
        "4) Cajas ejecutivas de síntesis pericial y de la fuente original; "
        "5) Introducción y Estado del Arte; "
        "6) Marco Normativo Positivo Venezolano (CRBV, Delitos Informáticos, Mensajes de Datos, Infogobierno); "
        "7) Discusión Técnico-Forense e Informática (RFC 3227, ISO/IEC 27037, hash SHA-256, Cadena de Custodia MP/CICPC); "
        "8) Análisis Jurisprudencial del TSJ o Contratación Electrónica; "
        "9) Compatibilidad y Viabilidad Tecnológica en Venezuela (CNTI, SUSCERTE); "
        "10) Conclusiones y Dictamen Deontológico; "
        "11) FAQ Jurídico-Técnico de 3 preguntas; "
        "12) Referencias Bibliográficas y Normativas en Normas APA 7ª Edición / ISO 690; "
        "13) Doble bloque Schema.org (ScholarlyArticle + FAQPage)."
    ),
    "analisis_sentencia_tsj": (
        "Estructura de Revista Digital Educativa para Análisis de Sentencias TSJ: "
        "1) Titular H1 impactante tipo revista (8-12 palabras) con la doctrina o principio central; "
        "2) Meta Descripción (145-160 caracteres) optimizada para búsqueda; "
        "3) Ficha Técnica de la Sentencia (tabla con: Sala, Expediente, Ponente, Fecha, Partes, Materia, Decisión); "
        "4) Párrafo Answer-First GEO 2026 (40-60 palabras) con la conclusión jurídica central; "
        "5) Caja 📌 Resumen Práctico: síntesis de la ratio decidendi y el dispositivo en lenguaje accesible; "
        "6) Caja ⚡ 30 Segundos: 3 viñetas con los puntos clave de la decisión; "
        "7) Sección '¿Qué resolvió el TSJ?' — Contexto fáctico y procesal (antecedentes del caso); "
        "8) Sección '¿Cuál es la doctrina establecida?' — Análisis de la ratio decidendi y obiter dicta relevantes; "
        "9) Sección '¿Qué normas aplicó la Sala?' — Marco normativo citado en la sentencia con artículos exactos; "
        "10) Sección '¿Cómo impacta esta decisión en la práctica?' — Consecuencias prácticas para litigantes, jueces y ciudadanos; "
        "11) Caja 💡 En Palabras Simples con analogía educativa; "
        "12) Sección de Votos Salvados/Concurrentes (si los hay); "
        "13) FAQ Jurídico con 3 preguntas naturales; "
        "14) Descargo ético obligatorio; "
        "15) Ficha de Derechos de Autor y enlace a la fuente TSJ; "
        "16) Doble bloque Schema.org (TechArticle tipo 'LegalCommentary' + FAQPage)."
    ),
    "ird": (
        "Razona como un abogado (IRAC en español): 1) Cuestión jurídica en una frase; "
        "2) Marco normativo (norma + artículo + vigencia); 3) Criterio jurisprudencial SOLO si consta en el contexto; "
        "4) Aplicación al caso típico; 5) Conclusión práctica y riesgos."
    ),
    "ruta": (
        "Organiza como guía de actuación: respuesta directa; pasos numerados; plazos/términos (solo los que consten en la norma citada); "
        "documentos necesarios; riesgos y errores frecuentes; cuándo acudir a un abogado."
    ),
    "divulgacion": (
        "Organiza para público general: respuesta directa; conceptos clave explicados; ejemplo cotidiano; normas aplicables; qué hacer."
    ),
    "ejecutivo": (
        "Organiza para directivos: resumen de riesgo; obligaciones aplicables; impacto; matriz riesgo-acción; recomendaciones priorizadas."
    ),
}


def is_legal_persona(persona_id: str) -> bool:
    return persona_id in PERSONAS


def select_glossary_terms(query: str, jurisdiction: str, k: int = 10) -> list[dict[str, Any]]:
    """Selecciona los k términos más relevantes del glosario para la consulta."""
    entries = GLOSSARY.get(jurisdiction, [])
    low = (query or "").lower()
    scored = []
    for idx, e in enumerate(entries):
        score = sum(1 for tag in e["tags"] if tag in low)
        if e["term"].lower() in low:
            score += 3
        scored.append((score, -idx, e))
    scored.sort(key=lambda s: (s[0], s[1]), reverse=True)
    picked = [e for score, _, e in scored[:k]]
    return picked


def build_persona_block(persona_id: str, jurisdiction: str, query: str = "") -> str:
    """Bloque de prompt con voz, léxico, normas autorizadas y reglas éticas."""
    persona = PERSONAS.get(persona_id)
    if not persona:
        return ""

    j = jurisdiction if jurisdiction in ("ve", "co") else (persona["jurisdiction"] if persona["jurisdiction"] in ("ve", "co") else "intl")
    lines = [
        f"PERFIL DE VOZ PROFESIONAL: {persona['label']} — {JURISDICTION_LABELS.get(j, '')}",
        f"- Registro: {persona['register']}",
        f"- Fórmulas propias que puedes usar con naturalidad (sin abusar): {'; '.join(persona['formulas'])}.",
        f"- Estructura argumentativa: {_STRUCTURES[persona['structure']]}",
    ]

    terms = select_glossary_terms(query, j, k=10) if j in GLOSSARY else []
    if terms:
        lines.append("- LÉXICO JURÍDICO A EMPLEAR CON PRECISIÓN (usa al menos 8 cuando sean pertinentes al tema):")
        for e in terms:
            note = f" ATENCIÓN: {e['avoid']}" if e["avoid"] else ""
            lines.append(f"  • {e['term']}: {e['use']}{note}")

    lines.append("- EVITA estos calcos y errores: " + "; ".join(f"«{c['bad'].replace(chr(92), '')}» → {c['good']}" for c in ANTI_CALCO[:6]) + ".")

    norms = AUTHORIZED_NORMS.get(j)
    if norms:
        lines.append("- NORMAS QUE PUEDES CITAR (únicas permitidas salvo que el contexto o la fuente aporten otras):")
        lines.extend(f"  • {n}" for n in norms)
        lines.append("  Si necesitas un artículo o una sentencia que NO consta en el contexto, NO inventes número: usa 'la normativa aplicable' o 'la jurisprudencia constitucional'.")

    if j in FOREIGN_MARKERS:
        other = "Colombia" if j == "ve" else "Venezuela"
        lines.append(f"- Jurisdicción pura: no mezcles instituciones de {other}; solo compara si el usuario lo pide.")

    lines.extend([
        "- ÉTICA PUBLICITARIA: prohibido prometer resultados ('garantizamos', 'gane su caso', '100% efectivo') o captar clientes de forma indebida.",
        f"- DESCARGO OBLIGATORIO al final antes del Schema: «{DISCLAIMER_TEXT}»",
        "- BLOQUE DE RESPUESTA DIRECTA: tras el H1, responde la pregunta principal en 40 a 60 palabras autocontenidas, citables por motores de IA.",
        "- Formula al menos la mitad de los H2 como pregunta real que un usuario escribiría en el buscador, y responde en 2-4 frases antes de profundizar.",
        "- Cita entidad completa (norma + artículo + órgano), nunca pronombres ambiguos. Enlaza fuentes oficiales cuando existan.",
    ])
    return "\n".join(lines)
