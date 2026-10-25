---
name: blog-legal-enrichment
description: >-
  Enriquece y fundamenta los artículos de blog con el corpus jurídico y normativo de Venezuela almacenado localmente en Informacion_docling_rag/. Permite cruzar avances tecnológicos internacionales con la legislación venezolana (CRBV, Delitos Informáticos, Infogobierno, Mensajes de Datos) y estándares ISO/NIST autorizados.
---

# Blog Legal Enrichment (Enriquecimiento Legal Venezolano)

Este skill define la doctrina de citación taxativa y las directrices para redactar la sección obligatoria de compatibilidad tecnológica nacional.

## 1. Corpus Jurídico Autorizado (Informacion_docling_rag/)

Todo fundamento de derecho debe provenir **exclusivamente** de las fuentes locales verificadas:

```text
Informacion_docling_rag/
├── Constitucion/          # CRBV (Arts. 28, 60, 110)
├── Penal/                 # Ley Delitos Informáticos (G.O. 37.313), Código Penal, COPP
├── Mercantil/             # Ley de Mensajes de Datos y Firmas Electrónicas (G.O. 37.148)
├── Informatica/           # Ley de Infogobierno (G.O. 40.274), Normas SUSCERTE, CNTI
├── Jurisprudencias/       # Sentencias de las Salas del TSJ (Casación, Constitucional)
├── Civil/                 # Código Civil y Código de Procedimiento Civil
├── Tributario/            # COT y providencias SENIAT
├── Agrario/               # Ley de Tierras
└── Diplomados/            # Manuales de Cadena de Custodia (MP / CICPC)
```

Consulta el índice completo de leyes y artículos en [legal_corpus_index.md](./references/legal_corpus_index.md).

---

## 2. Estructura Obligatoria de Compatibilidad Tecnológica

Todo artículo debe contener la siguiente sección antes del FAQ:

```markdown
## 🔬 Análisis de Compatibilidad y Prospectiva Tecnológica en Venezuela {#compatibilidad}
- **Infraestructura y Conectividad:** [Análisis sobre redes de fibra óptica, estabilidad de telecomunicaciones, centros de datos locales y contingencia energética].
- **Interoperabilidad y Gobernanza Digital:** [Alineación con la Ley de Infogobierno, plataformas del CNTI, directrices de SUSCERTE/VenCERT y sector bancario Sudeban].
- **Viabilidad Económica y Adopción Práctica:** [Desafíos y oportunidades de despliegue para empresas, peritos y profesionales en Venezuela].
- **Dictamen Prospectivo:** [Conclusión estratégica sobre la madurez tecnológica nacional para adoptar esta solución en el mediano plazo].
```

---

## 3. Principio de Cero Invención Normativa

- **Prohibido**: Citar reglamentos o leyes no existentes en la Gaceta Oficial o de otras jurisdicciones no pertinentes (como GDPR o HIPAA) a menos que se haga a título meramente comparativo con la legislación patria.
- **Obligatorio**: Referenciar el número de artículo o gaceta oficial en cada mención legal principal.
