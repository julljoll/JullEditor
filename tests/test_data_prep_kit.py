"""
Pruebas exhaustivas para la integración de IBM Data Prep Kit (DPK) en JullEditor.
Verifica transformaciones Apache Arrow, anonimización PII venezolana, control de calidad,
desduplicación, chunking semántico, persistencia Parquet y endpoints FastAPI.
"""

import json
from pathlib import Path
import pyarrow as pa
import pytest
from fastapi.testclient import TestClient

from backend.app import app
from backend.data_prep.base import BaseDPKTableTransform
from backend.data_prep.parquet_store import ParquetDatasetManager
from backend.data_prep.pipeline import (
    DataPrepPipeline,
    create_rag_indexing_pipeline,
    create_source_prep_pipeline,
)
from backend.data_prep.transforms.chunker_transform import SemanticLegalChunkTransform
from backend.data_prep.transforms.cleaner_transform import HeaderCleanerTransform
from backend.data_prep.transforms.dedup_transform import ExactDedupTransform, FuzzyDedupTransform
from backend.data_prep.transforms.docling_transform import DoclingIngestTransform
from backend.data_prep.transforms.pii_transform import PIIRedactorTransform
from backend.data_prep.transforms.quality_transform import DocQualityTransform
from backend.data_prep import preprocess_source_dpk
from backend.rag.vector_store import LegalVectorStore


client = TestClient(app)


# ==============================================================================
# 1. PRUEBAS DE TRANSFORMACIONES ATÓMICAS (DPK TRANSFORMS)
# ==============================================================================

def test_docling_ingest_transform():
    """Valida la ingesta de Markdown y JSON estructurados hacia Apache Arrow."""
    transform = DoclingIngestTransform({"default_category": "Ciberseguridad"})
    input_records = [
        {
            "text": "---\ntitle: Ley de Infogobierno\n---\n# Ley de Infogobierno\n\nEl Estado promoverá el uso de tecnologías libres.",
            "filename": "infogobierno.md",
            "category": "Infogobierno",
        },
        {
            "text": json.dumps({"title": "Dictamen Forense", "markdown": "Contenido pericial sobre evidencia digital."}),
            "filename": "dictamen.json",
        },
    ]
    in_table = BaseDPKTableTransform.records_to_table(input_records)
    out_tables, stats = transform.transform(in_table)

    assert len(out_tables) == 1
    table = out_tables[0]
    assert isinstance(table, pa.Table)
    assert table.num_rows == 2
    assert "doc_id" in table.column_names
    assert "title" in table.column_names
    assert "word_count" in table.column_names
    assert stats["ingested_docs"] == 2


def test_header_cleaner_transform():
    """Valida la eliminación de cookies, navegación, paginación OCR y corrección de mojibake."""
    transform = HeaderCleanerTransform()
    noisy_text = (
        "Accept all cookies to continue reading.\n"
        "Página 1 de 12\n"
        "Análisis de ciberseguridad con carÃ¡cter urgente.\n"
        "Subscribe to our newsletter!\n"
        "Todos los derechos reservados 2026."
    )
    in_table = BaseDPKTableTransform.records_to_table([{"text": noisy_text, "doc_id": "test_clean"}])
    out_tables, stats = transform.transform(in_table)

    cleaned = out_tables[0].to_pylist()[0]["text"]
    assert "Accept all cookies" not in cleaned
    assert "Página 1 de 12" not in cleaned
    assert "Subscribe to our newsletter" not in cleaned
    # Mojibake corregido
    assert "carácter" in cleaned
    assert stats["boilerplate_hits_removed"] >= 2


def test_pii_redactor_transform():
    """Valida la detección y ofuscación de PII sensible venezolana conforme a la ley."""
    transform = PIIRedactorTransform()
    sensitive_text = (
        "El perito Juan Pérez, titular de la C.I. V-18.765.432 y RIF J-31234567-0, "
        "envió el informe desde jperez@tribunal.gob.ve y teléfono 0414-1234567. "
        "Cuenta bancaria de depósito: 01020123456789012345."
    )
    in_table = BaseDPKTableTransform.records_to_table([{"text": sensitive_text, "doc_id": "doc_pii"}])
    out_tables, stats = transform.transform(in_table)

    record = out_tables[0].to_pylist()[0]
    redacted = record["text"]

    assert "[CÉDULA_PROTEGIDA]" in redacted
    assert "V-18.765.432" not in redacted
    assert "[EMAIL_PROTEGIDO]" in redacted
    assert "jperez@tribunal.gob.ve" not in redacted
    assert "[TELÉFONO_PROTEGIDO]" in redacted
    assert "0414-1234567" not in redacted
    assert "[CUENTA_BANCARIA_PROTEGIDA]" in redacted

    audit = record["pii_audit"]
    assert len(audit) >= 4
    assert stats["total_pii_entities_redacted"] >= 4


def test_doc_quality_transform():
    """Valida el cálculo de métricas de calidad y preparación para IBM Granite."""
    transform = DocQualityTransform({"min_words": 15})
    records = [
        {"text": "Texto muy corto.", "doc_id": "short_doc"},
        {
            "text": "La evidencia digital recolectada en auditorías forenses debe cumplir con la cadena de custodia estipulada en las normas técnicas para garantizar su validez jurídica en tribunales competentes de la República.",
            "doc_id": "good_doc",
        },
    ]
    in_table = BaseDPKTableTransform.records_to_table(records)
    out_tables, stats = transform.transform(in_table)

    results = out_tables[0].to_pylist()
    assert len(results) == 2
    assert results[0]["is_ready_for_granite"] is False
    assert results[1]["is_ready_for_granite"] is True
    assert results[1]["quality_score"] > results[0]["quality_score"]


def test_dedup_transforms():
    """Valida la eliminación de duplicados exactos (SHA-256) y casi duplicados (MinHash/Jaccard)."""
    text_a = "El principio de intervención mínima rige el derecho penal informático."
    text_b = "El principio de intervención mínima rige el derecho penal informático."
    text_c = "Diferente contenido sobre criptografía y firmas electrónicas."

    records = [
        {"text": text_a, "doc_id": "1"},
        {"text": text_b, "doc_id": "2"},
        {"text": text_c, "doc_id": "3"},
    ]
    in_table = BaseDPKTableTransform.records_to_table(records)

    exact_dedup = ExactDedupTransform()
    out_tables, stats = exact_dedup.transform(in_table)
    assert out_tables[0].num_rows == 2
    assert stats["exact_duplicates_removed"] == 1

    fuzzy_dedup = FuzzyDedupTransform({"similarity_threshold": 0.85})
    fuzzy_tables, f_stats = fuzzy_dedup.transform(in_table)
    assert fuzzy_tables[0].num_rows == 2


def test_semantic_legal_chunk_transform():
    """Valida la partición de normativas legales preservando el número de artículo."""
    legal_law = """
    # Ley de Firmas Electrónicas
    
    Artículo 28
    Los proveedores de servicios de certificación deben mantener auditoría permanente sobre los certificados emitidos.
    
    Artículo 29
    La revocatoria de un certificado electrónico producirá efectos desde el momento de su publicación en la lista oficial.
    """
    in_table = BaseDPKTableTransform.records_to_table([{
        "text": legal_law,
        "doc_id": "ley_firmas",
        "title": "Ley de Firmas",
        "category": "Telecomunicaciones",
    }])
    chunker = SemanticLegalChunkTransform({"min_chunk_words": 5})
    out_tables, stats = chunker.transform(in_table)

    chunks = out_tables[0].to_pylist()
    assert len(chunks) == 2
    assert chunks[0]["article_number"] == "28"
    assert chunks[1]["article_number"] == "29"
    assert stats["generated_chunks"] == 2
    assert chunks[0]["token_count_est"] > 0


# ==============================================================================
# 2. PRUEBAS DE PIPELINE Y PARQUET DATASET MANAGER
# ==============================================================================

def test_data_prep_pipeline_end_to_end():
    """Valida la ejecución de un pipeline encadenado completo con DPK."""
    pipeline = create_source_prep_pipeline(min_words=10, redact_pii=True)
    raw_text = (
        "---nauthor: Perito Informáticon---n"
        "# Auditoría de Seguridad Digitaln"
        "Informe elaborado por C.I. V-12.345.678. "
        "Se detectó vulnerabilidad en la pasarela de pagos electrónicos. "
        "Subscribe to our newsletter! "
        "Las medidas correctivas deben aplicarse de inmediato bajo estándares ISO/IEC 27001."
    )
    table, stats = pipeline.run(raw_text, file_name="auditoria.md")

    assert table.num_rows == 1
    assert stats["total_transforms"] == 5
    assert "3_PIIRedactorTransform" in stats["step_statistics"]
    assert table.to_pylist()[0]["pii_redacted"] is True


def test_parquet_store_manager(tmp_path):
    """Valida el guardado y lectura de tablas Apache Parquet con compresión Snappy."""
    manager = ParquetDatasetManager(tmp_path)
    records = [{"doc_id": f"id_{i}", "text": f"Contenido legal número {i}"} for i in range(10)]
    table = BaseDPKTableTransform.records_to_table(records)

    saved_path = manager.save_table(table, "test_corpus")
    assert saved_path.exists()
    assert manager.table_exists("test_corpus")

    loaded_table = manager.load_table("test_corpus")
    assert loaded_table is not None
    assert loaded_table.num_rows == 10

    stats = manager.get_dataset_stats("test_corpus")
    assert stats is not None
    assert stats["num_rows"] == 10
    assert stats["num_columns"] == 2
    assert "doc_id" in stats["column_names"]


def test_vector_store_dpk_indexing(tmp_path):
    """Valida la indexación DPK directamente en LegalVectorStore con persistencia Parquet."""
    doc_dir = tmp_path / "docs"
    doc_dir.mkdir()
    law_file = doc_dir / "ley_prueba.md"
    law_file.write_text(
        "# Ley Modelo de Ciberseguridad\n\n"
        "Artículo 10\nTodo incidente crítico debe notificarse en menos de 24 horas.\n\n"
        "Artículo 11\nLa cadena de custodia de la evidencia digital no podrá ser alterada.",
        encoding="utf-8",
    )

    store = LegalVectorStore(persist_dir=tmp_path / "store")
    result = store.index_corpus_dpk(corpus_dir=doc_dir, save_parquet=True)

    assert result["status"] == "success"
    assert result["chunks_count"] >= 2
    assert result["parquet_path"] is not None

    stats = store.get_dpk_parquet_stats()
    assert stats is not None
    assert stats["num_rows"] >= 2

    # Probar que la búsqueda BM25/Híbrida funciona con los chunks generados por DPK
    hits = store.search("cadena de custodia evidencia digital", top_k=2)
    assert len(hits) >= 1
    assert "cadena de custodia" in hits[0]["text"].lower()


# ==============================================================================
# 3. PRUEBAS DE ENDPOINTS FASTAPI PARA IBM DATA PREP KIT
# ==============================================================================

def test_api_dpk_preprocess_endpoint():
    """Valida el endpoint POST /api/data-prep/preprocess."""
    payload = {
        "text": "Informe de vulnerabilidad preparado por analista con C.I. V-15.999.888. Detectada intrusión en servidor.",
        "filename": "informe_sec.md",
        "redact_pii": True,
        "min_words": 10,
    }
    response = client.post("/api/data-prep/preprocess", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "success"
    assert "[CÉDULA_PROTEGIDA]" in data["cleaned_text"]
    assert data["pii_redacted"] is True
    assert "pipeline_stats" in data


def test_api_dpk_redact_pii_endpoint():
    """Valida el endpoint POST /api/data-prep/redact-pii."""
    payload = {
        "text": "Contacto del fiscal: fiscal.general@mp.gob.ve o al teléfono 0212-5551234 con C.I. V-10.123.456.",
    }
    response = client.post("/api/data-prep/redact-pii", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "success"
    assert "[EMAIL_PROTEGIDO]" in data["redacted_text"]
    assert "[TELÉFONO_PROTEGIDO]" in data["redacted_text"]
    assert "[CÉDULA_PROTEGIDA]" in data["redacted_text"]
    assert len(data["pii_audit"]) >= 3


def test_api_dpk_corpus_stats_and_index_endpoint(tmp_path, monkeypatch):
    """Valida los endpoints GET /api/data-prep/corpus-stats y POST /api/data-prep/index-corpus."""
    # Probar endpoint stats cuando aún no está indexado o ya indexado
    stats_res = client.get("/api/data-prep/corpus-stats")
    assert stats_res.status_code == 200
    assert "status" in stats_res.json()

    # Probar endpoint index con max_files=2 para ejecución rápida
    index_res = client.post("/api/data-prep/index-corpus", json={"max_files": 2})
    assert index_res.status_code == 200
    data = index_res.json()
    assert data["status"] in ("success", "warning")

