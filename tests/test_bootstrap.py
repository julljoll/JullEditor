"""Tests del auto-arranque (backend/bootstrap.py): análisis de PC, deps, Ollama y modelo Granite."""
from unittest import mock

import pytest

from backend import bootstrap as b


class TestAnalyzeComputer:
    def test_profile_keys(self):
        p = b.analyze_computer()
        for key in ("os", "arch", "cpu_count", "ram_gb", "tier", "recommended_model"):
            assert key in p

    def test_model_follows_ram(self):
        with mock.patch("backend.bootstrap.detect_system_resources",
                        return_value={"os": "Windows", "arch": "AMD64", "cpu_count": 8,
                                      "ram_gb": 16.0, "tier": "high",
                                      "recommended_model": "granite3.3:8b",
                                      "recommended_ctx": 8192, "recommended_threads": 8}):
            p = b.analyze_computer()
        assert p["recommended_model"] == "granite3.3:8b"


class TestRequirementsParser:
    @pytest.mark.parametrize("spec,name", [
        ("fastapi>=0.115.0,<1.0.0", "fastapi"),
        ("uvicorn[standard]>=0.30.6", "uvicorn"),
        ("# comentario", None),
        ("-r otros.txt", None),
        ("", None),
    ])
    def test_requirement_name(self, spec, name):
        assert b._requirement_name(spec) == name

    def test_missing_detects_absent_package(self):
        with mock.patch.object(b, "REQUIREMENTS_FILE") as f:
            f.exists.return_value = True
            f.read_text.return_value = "paquete-inexistente-zz>=1.0\n"
            assert "paquete-inexistente-zz" in b.missing_python_packages()


class TestOllama:
    def test_is_installed_uses_which(self):
        with mock.patch.object(b.shutil, "which", return_value=None), \
             mock.patch.object(b, "_candidate_ollama_paths", return_value=[]):
            assert b.is_ollama_installed() is False
        with mock.patch.object(b.shutil, "which", return_value="/usr/bin/ollama"):
            assert b.is_ollama_installed() is True

    def test_no_autoinstall_when_disabled(self):
        with mock.patch.object(b, "is_ollama_installed", return_value=False):
            assert b.ensure_ollama_installed(auto_install=False) is False

    def test_windows_fallback_to_official_installer(self):
        calls = []

        def fake_run(cmd, **kw):
            calls.append(cmd)
            return type("R", (), {"returncode": 0})()

        # Secuencia real de llamadas a is_ollama_installed():
        #   1) ensure_ollama_installed() -> False (falta Ollama)
        #   2) install_ollama_windows(): chequeo post-winget -> False
        #   3) install_ollama_windows(): chequeo post-instalador oficial -> True
        with mock.patch.object(b, "is_ollama_installed", side_effect=[False, True]), \
             mock.patch.object(b, "_run_quiet", side_effect=fake_run), \
             mock.patch("urllib.request.urlretrieve", return_value=None), \
             mock.patch.object(b.platform, "system", return_value="Windows"), \
             mock.patch.object(b, "refresh_ollama_path"):
            ok = b.install_ollama_windows()
        assert ok is True
        assert any("winget" in str(c) for c in calls)
        assert any("OllamaSetup.exe" in str(c) for c in calls)


class TestDownloadGranite:
    def test_skips_pull_if_already_present(self):
        with mock.patch.object(b, "installed_ollama_models",
                               return_value=["granite3.3:8b:latest"]), \
             mock.patch.object(b.subprocess, "run") as mrun:
            assert b.download_granite_model("granite3.3:8b", base_url="http://x") is True
            mrun.assert_not_called()

    def test_pulls_recommended_model(self):
        with mock.patch.object(b, "installed_ollama_models", return_value=[]), \
             mock.patch.object(b.subprocess, "run", return_value=type("R", (), {"returncode": 0})()) as mrun:
            assert b.download_granite_model("granite3.3:2b") is True
            mrun.assert_called_once()
            assert mrun.call_args[0][0] == ["ollama", "pull", "granite3.3:2b"]


class TestRunBootstrap:
    def test_full_environment_makes_no_installs(self):
        with mock.patch.object(b, "ensure_python_dependencies", return_value=True), \
             mock.patch.object(b, "is_ollama_installed", return_value=True), \
             mock.patch.object(b, "ensure_ollama_service_running", return_value=True), \
             mock.patch.object(b, "installed_ollama_models", return_value=["granite3.3:2b"]), \
             mock.patch.object(b.subprocess, "run") as mrun:
            p = b.run_bootstrap(auto_install=True)
        assert p["deps_ok"] and p["ollama_ok"] and p["model_ready"]
        mrun.assert_not_called()

    def test_degrades_without_ollama(self):
        with mock.patch.object(b, "ensure_python_dependencies", return_value=True), \
             mock.patch.object(b, "is_ollama_installed", return_value=False), \
             mock.patch.object(b, "ensure_ollama_installed", return_value=False):
            p = b.run_bootstrap(auto_install=False)
        assert p["ollama_ok"] is False and p["model_ready"] is False
