"""
Pruebas unitarias para el generador CLI y el endpoint de precarga de archivos.
Valida la selección de archivos, el endpoint /api/preloaded-file y el flujo de configuración TSJ con temp=0.0.
"""

import os
import json
import pytest
from pathlib import Path
from fastapi.testclient import TestClient

from backend.app import app, PRELOADED_FILE_PATH
from backend.cli_generator import find_available_md_files, save_preloaded_session, prompt_editorial_config

client = TestClient(app)


def test_get_preloaded_file_empty():
    """Valida que /api/preloaded-file retorne has_file=False cuando no hay sesión guardada."""
    if os.path.exists(PRELOADED_FILE_PATH):
        os.remove(PRELOADED_FILE_PATH)

    response = client.get("/api/preloaded-file")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "success"
    assert data["has_file"] is False
    assert data["data"] is None


def test_save_and_get_preloaded_file(tmp_path):
    """Valida el guardado y consumo del archivo precargado."""
    dummy_file = tmp_path / "sentencia_prueba.md"
    dummy_file.write_text("# Sentencia TSJ Sala Constitucional Nº 123\nTexto de prueba.", encoding="utf-8")

    config = {
        "theme": "sentencia_tsj",
        "editorial_mode": "magazine",
        "tone": "analista_tsj_revista",
        "jurisdiction": "venezuela",
        "temperature": 0.0,
        "model": "granite3.3:8b",
        "target_words": 1000,
    }
    parsed = {
        "clean_title": "Sentencia TSJ Sala Constitucional Nº 123",
        "cleaned_content": "Texto de prueba de la sentencia",
    }

    save_preloaded_session(dummy_file, config, parsed)
    assert os.path.exists(PRELOADED_FILE_PATH)

    # El endpoint debe leer y consumir (eliminar) el archivo
    response = client.get("/api/preloaded-file")
    assert response.status_code == 200
    res_data = response.json()
    assert res_data["status"] == "success"
    assert res_data["has_file"] is True
    assert res_data["data"]["title"] == "Sentencia TSJ Sala Constitucional Nº 123"
    assert res_data["data"]["temperature"] == 0.0
    assert res_data["data"]["tone"] == "analista_tsj_revista"
    assert res_data["data"]["theme"] == "sentencia_tsj"

    # Segunda lectura debe dar has_file=False (consumido)
    second_resp = client.get("/api/preloaded-file")
    assert second_resp.json()["has_file"] is False


def test_find_available_md_files():
    """Verifica que la función de escaneo localice archivos .md existentes en el proyecto."""
    files = find_available_md_files()
    assert isinstance(files, list)
    if len(files) > 0:
        assert all(isinstance(f, Path) for f in files)
        assert all(f.suffix.lower() == ".md" for f in files)


def test_scan_docling_rag_structure():
    """Verifica que el escaneador dinámico retorne las categorías y archivos reales de Informacion_docling_rag."""
    from backend.cli_generator import scan_docling_rag_structure

    scan = scan_docling_rag_structure()
    assert isinstance(scan, dict)
    assert "categories" in scan
    assert "category_list" in scan
    assert "all_files" in scan
    assert scan["total_categories"] >= 10
    assert scan["total_files"] >= 80

    # Verificar categorías canónicas
    assert "Jurisprudencias" in scan["category_list"]
    assert "Informatica" in scan["category_list"]
    assert "Civil" in scan["category_list"]
    assert len(scan["categories"]["Jurisprudencias"]) > 0


def test_scan_docling_rag_auto_refresh_on_new_file(tmp_path):
    """
    Verifica que al agregar dinámicamente un archivo nuevo en Informacion_docling_rag,
    el escaneo lo detecte inmediatamente (0ms latencia, sin caché estática),
    y que al eliminarlo desaparezca automáticamente.
    """
    from backend.cli_generator import scan_docling_rag_structure, WORKSPACE_ROOT

    target_category_dir = WORKSPACE_ROOT / "Informacion_docling_rag" / "Jurisprudencias"
    assert target_category_dir.exists(), "La carpeta Jurisprudencias debe existir"

    test_doc = target_category_dir / "test_auto_refresh_sentencia_tsj_temporal.md"
    try:
        # Estado inicial
        scan1 = scan_docling_rag_structure()
        assert test_doc not in scan1["all_files"]

        # 1. Simular que el usuario agrega un nuevo archivo a Informacion_docling_rag
        test_doc.write_text("# Sentencia TSJ Temporal de Prueba\nContenido dinámico.", encoding="utf-8")

        # 2. Re-escanear inmediatamente
        scan2 = scan_docling_rag_structure()
        assert test_doc in scan2["all_files"], "El nuevo archivo debe ser detectado automáticamente"
        assert test_doc in scan2["categories"]["Jurisprudencias"], "Debe aparecer en la categoría Jurisprudencias"

    finally:
        # 3. Limpieza: eliminar el archivo temporal
        if test_doc.exists():
            test_doc.unlink()

    # 4. Verificar que tras eliminarse tampoco aparezca
    scan3 = scan_docling_rag_structure()
    assert test_doc not in scan3["all_files"], "El archivo eliminado no debe permanecer en el listado"


def test_select_input_file_with_arg(tmp_path):
    """Verifica que select_input_file cargue directamente un archivo si se pasa por argumento."""
    from backend.cli_generator import select_input_file

    dummy = tmp_path / "doc_argumento.md"
    dummy.write_text("Prueba argumento", encoding="utf-8")

    res = select_input_file(str(dummy))
    assert res == dummy

