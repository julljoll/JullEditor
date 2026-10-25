"""
JullEditor — TUI Textual (Interfaz Canónica v3.3.0 · PLAN_OPTIMIZACION Fase 1)

Interfaz de terminal rica (100% Python) espejo 1:1 del flujo de frontend/index.html:
especialidad → estilo → tono VE → jurisdicción → ajustes avanzados → streaming
en vivo con auto-guardado y auditoría SEO/jurídica. Reemplaza funcionalmente a
la GUI JS como interfaz principal; los .bat siguen siendo el puente de entrada.

Uso:
    python -m backend.tui_app
    python run.py --tui          (o crear_articulo.bat → opción [T])
"""

import json
import sys
from pathlib import Path
from typing import Any

import httpx
from textual.app import App, ComposeResult
from textual.containers import Horizontal, VerticalScroll
from textual.reactive import reactive
from textual.widgets import (
    Button,
    DirectoryTree,
    Footer,
    Header,
    Input,
    RadioButton,
    RadioSet,
    RichLog,
    Select,
    Static,
)

from backend import editorial_catalog as cat
from backend.cli_generator import (
    OLLAMA_BASE_URL,
    check_and_start_ollama,
    save_preloaded_session,
)
from backend.docling_parser import parse_docling_markdown
from backend.legal_validator import audit_legal_quality
from backend.prompts import build_generation_prompt, build_sentencia_tsj_prompt
from backend.rag_manager import retrieve_legal_context, save_final_article
from backend.sentencia_extractor import extract_sentencia_metadata, is_sentencia_text
from backend.seo_validator import audit_article_seo

INFER_PAYLOAD_OPTIONS = {
    "num_predict": 4096,
    "num_ctx": 8192,
    "num_thread": 4,
    "repeat_penalty": 1.1,
    "top_p": 0.9,
}


class ConfigSummary(Static):
    """Resumen vivo de la configuración editorial seleccionada."""

    config: reactive[dict[str, Any]] = reactive(dict)

    def render_summary(self) -> str:
        c = self.config
        tone_label = dict(cat.TONES).get(c.get("tone", ""), "?")
        jur_label = dict(cat.JURISDICTIONS).get(c.get("jurisdiction", ""), "?")
        theme_label = {code: label for code, _i, label in cat.THEMES}.get(c.get("theme", ""), "?")
        mode_label = dict(cat.EDITORIAL_MODES).get(c.get("editorial_mode", ""), "?")
        return (
            f"[bold cyan]Tema:[/bold cyan] {theme_label}\n"
            f"[bold cyan]Estilo:[/bold cyan] {mode_label}\n"
            f"[bold cyan]Voz:[/bold cyan] {tone_label}\n"
            f"[bold cyan]Jurisdicción:[/bold cyan] {jur_label}\n"
            f"[bold cyan]Temp:[/bold cyan] {c.get('temperature', 0.0)} · "
            f"[bold cyan]Modelo:[/bold cyan] {c.get('model', cat.DEFAULT_MODEL)} · "
            f"[bold cyan]Palabras:[/bold cyan] ~{c.get('target_words', 1000)}"
        )


class JullEditorTUI(App):
    """Estación editorial jurídica Venezuela — TUI oficial."""

    CSS = """
    #left-pane { width: 1fr; }
    #right-pane { width: 1fr; border-left: solid #1e293b; }
    RichLog { height: 1fr; }
    #summary { height: auto; padding: 1 2; background: #0f172a; }
    .section-title { color: #22d3ee; text-style: bold; padding-top: 1; }
    #actionBar { align-horizontal: center; height: auto; }
    Select { margin-bottom: 1; }
    """

    BINDINGS = [
        ("ctrl+q", "quit", "Salir"),
        ("ctrl+s", "generate", "Generar Artículo"),
        ("ctrl+b", "open_web", "Modo Web"),
    ]

    def __init__(self, source_file: Path | None = None):
        super().__init__()
        self.source_file: Path | None = source_file
        self.parsed_doc: dict[str, Any] = {}
        self.is_generating = False

    # ------------------------------------------------------------------ UI
    def compose(self) -> ComposeResult:
        yield Header(show_clock=True)
        with Horizontal(id="main"):
            with VerticalScroll(id="left-pane"):
                yield Static("📁 1. FUENTE (sentencia / documento .md)", classes="section-title")
                yield DirectoryTree(str(Path.cwd()), id="fileTree")
                yield Static("🎯 2. ESPECIALIDAD TEMÁTICA", classes="section-title")
                yield RadioSet(
                    *[RadioButton(label, value=(code == cat.theme_codes()[0]), id=f"th_{code}")
                      for code, _icon, label in cat.THEMES],
                    id="themeSet",
                )
                yield Static("📰 3. ESTILO EDITORIAL", classes="section-title")
                yield RadioSet(
                    RadioButton("Revista Digital (3 Col.)", value=True, id="em_magazine"),
                    RadioButton("Resumen Clásico Fiel", id="em_classic"),
                    id="modeSet",
                )
            with VerticalScroll(id="right-pane"):
                yield Static("🎙️ 4. PERFIL DE VOZ / TONO (VE)", classes="section-title")
                yield Select(
                    [(label, code) for code, label in cat.TONES],
                    value=cat.DEFAULT_TONE,
                    id="toneSelect",
                    allow_blank=False,
                )
                yield Static("⚖️ 5. JURISDICCIÓN", classes="section-title")
                yield Select(
                    [(label, code) for code, label in cat.JURISDICTIONS],
                    value=cat.DEFAULT_JURISDICTION,
                    id="jurSelect",
                    allow_blank=False,
                )
                yield Static("⚙️ 6. AJUSTES AVANZADOS", classes="section-title")
                yield Select(
                    [(f"Temperatura {t}", t) for t in (0.0, 0.15, 0.3, 0.5, 0.7)],
                    value=cat.DEFAULT_TEMPERATURE,
                    id="tempSelect",
                    allow_blank=False,
                )
                yield Select(
                    [(label, code) for code, label in cat.MODELS],
                    value=cat.DEFAULT_MODEL,
                    id="modelSelect",
                    allow_blank=False,
                )
                yield Select(
                    [(label, w) for w, label in cat.WORD_COUNT_TARGETS],
                    value=cat.DEFAULT_WORD_COUNT,
                    id="wordsSelect",
                    allow_blank=False,
                )
                yield Input(placeholder="Instrucciones personalizadas (opcional)…", id="customInstr")
                yield ConfigSummary(id="summary")
                with Horizontal(id="actionBar"):
                    yield Button("⚡ Generar Artículo", variant="primary", id="btnGenerate")
                    yield Button("🌐 Precargar en Web", variant="default", id="btnWeb")
        yield Footer()

    # ------------------------------------------------------------ helpers
    def on_directory_tree_file_selected(self, event: DirectoryTree.FileSelected) -> None:
        self.source_file = Path(event.path)
        raw = self.source_file.read_text(encoding="utf-8", errors="replace")
        self.parsed_doc = parse_docling_markdown(raw, self.source_file.name)
        title = self.parsed_doc.get("clean_title") or self.source_file.stem
        tsj = is_sentencia_text(self.parsed_doc.get("cleaned_content", ""))
        badge = "🏛️ SENTENCIA TSJ DETECTADA" if tsj else "📄 Documento cargado"
        self.query_one("#summary", ConfigSummary).update(
            f"[bold green]{badge}[/bold green]: {title}\n" + self._current_config_preview()
        )

    def _selected_theme(self) -> str:
        rs = self.query_one("#themeSet", RadioSet)
        for btn in rs.children:
            if isinstance(btn, RadioButton) and btn.value:
                return btn.id.replace("th_", "")  # type: ignore[union-attr]
        return cat.theme_codes()[0]

    def _collect_config(self) -> dict[str, Any]:
        mode_set = self.query_one("#modeSet", RadioSet)
        editorial_mode = "magazine"
        for btn in mode_set.children:
            if isinstance(btn, RadioButton) and btn.value and btn.id == "em_classic":
                editorial_mode = "classic"
        cfg = {
            "theme": self._selected_theme(),
            "editorial_mode": editorial_mode,
            "tone": self.query_one("#toneSelect", Select).value,
            "jurisdiction": self.query_one("#jurSelect", Select).value,
            "temperature": self.query_one("#tempSelect", Select).value,
            "model": self.query_one("#modelSelect", Select).value,
            "target_words": self.query_one("#wordsSelect", Select).value,
            "custom_instructions": self.query_one("#customInstr", Input).value.strip(),
        }
        return cfg

    def _current_config_preview(self) -> str:
        try:
            cfg = self._collect_config()
        except Exception:
            return ""
        summary = ConfigSummary()
        summary.config = cfg
        return summary.render_summary()

    def on_select_changed(self, event: Select.Changed) -> None:
        self.refresh_summary()

    def on_radio_set_changed(self, event: RadioSet.Changed) -> None:
        self.refresh_summary()

    def refresh_summary(self) -> None:
        self.query_one("#summary", ConfigSummary).update(self._current_config_preview())

    # ------------------------------------------------------------ actions
    async def on_button_pressed(self, event: Button.Pressed) -> None:
        if event.button.id == "btnGenerate":
            await self.action_generate()
        elif event.button.id == "btnWeb":
            self.action_open_web()

    def action_open_web(self) -> None:
        """Guarda sesión precargada e indica cómo abrir el modo web."""
        log = self.query_one(RichLog)
        if not self.source_file:
            log.write("[red]⚠ Selecciona primero un archivo fuente.[/red]")
            return
        cfg = self._collect_config()
        save_preloaded_session(self.source_file, cfg, self.parsed_doc)
        log.write("[green]✔ Sesión precargada. Ejecuta:[/green] python run.py  (abre la web con este archivo)")

    async def action_generate(self) -> None:
        if self.is_generating:
            return
        log = self.query_one(RichLog)
        if not self.source_file:
            log.write("[red]⚠ Selecciona primero un archivo fuente del árbol de la izquierda.[/red]")
            return

        cfg = self._collect_config()
        errors = cat.validate_config(cfg)
        if errors:
            for e in errors:
                log.write(f"[red]✘ {e}[/red]")
            return

        content_text = self.parsed_doc.get("cleaned_content", "")
        article_title = (
            self.parsed_doc.get("clean_title")
            or self.source_file.stem.replace("_", " ").title()
        )
        is_tsj = is_sentencia_text(content_text)
        tsj_meta = extract_sentencia_metadata(content_text, self.source_file.name) if is_tsj else None

        log.write(f"[bold cyan]▶ Configuración:[/bold cyan] tono={cfg['tone']} · jur={cfg['jurisdiction']} · "
                  f"T={cfg['temperature']} · {cfg['model']} · ~{cfg['target_words']} palabras")

        if not check_and_start_ollama():
            log.write("[red]✘ Ollama no está disponible (puerto 11434). Inícialo con: ollama serve[/red]")
            return

        # RAG legal Venezuela (misma lógica que CLI clásico y app.py)
        rag_context = ""
        if cfg["jurisdiction"] in ("venezuela", "auto"):
            try:
                rag_context = retrieve_legal_context(
                    query_text=f"{article_title} {content_text[:2000]}",
                    theme=cfg["theme"],
                    top_k=3,
                    jurisdiction="ve",
                )
            except Exception:
                rag_context = ""

        custom_instr = cfg.get("custom_instructions", "")
        if is_tsj or cfg["theme"] == "sentencia_tsj" or cfg["tone"] == "analista_tsj_revista":
            prompt = build_sentencia_tsj_prompt(
                article_source_text=content_text,
                source_title=article_title,
                source_url=f"Archivo local: {self.source_file.name}",
                sentencia_metadata=tsj_meta,
                legal_rag_context=rag_context,
                custom_instructions=custom_instr,
                target_words=cfg["target_words"],
            )
        else:
            prompt = build_generation_prompt(
                article_source_text=content_text,
                source_title=article_title,
                source_url=f"Archivo local: {self.source_file.name}",
                theme=cfg["theme"],
                tone=cfg["tone"],
                target_words=cfg["target_words"],
                custom_instructions=custom_instr,
                legal_rag_context=rag_context,
                jurisdiction=cfg["jurisdiction"],
                editorial_mode=cfg["editorial_mode"],
            )

        self.is_generating = True
        btn = self.query_one("#btnGenerate", Button)
        btn.disabled = True
        btn.label = "⏳ Redactando…"
        log.write("[bold magenta]═══ REDACCIÓN EDITORIAL EN TIEMPO REAL (IBM GRANITE 3.3) ═══[/bold magenta]")

        generated = await self._stream_inference(prompt, cfg, log)

        btn.disabled = False
        btn.label = "⚡ Generar Artículo"
        self.is_generating = False

        if not generated:
            log.write("[red]✘ El modelo no retornó contenido.[/red]")
            return

        save_res = save_final_article(
            title=article_title,
            markdown_content=generated,
            metadata={
                "theme": cfg["theme"], "model": cfg["model"], "tone": cfg["tone"],
                "temperature": cfg["temperature"], "source_file": self.source_file.name,
                "jurisdiction": cfg["jurisdiction"], "editorial_mode": cfg["editorial_mode"],
                "interface": "tui_textual",
            },
        )
        try:
            seo_report = audit_article_seo(generated)
            legal_report = audit_legal_quality(
                generated, jurisdiction="ve" if cfg["jurisdiction"] != "international" else "auto"
            )
            combined = round(seo_report.get("score", 0) * 0.6 + legal_report.get("score", 0) * 0.4)
        except Exception:
            seo_report = legal_report = {"score": 0}
            combined = 0

        log.write("[bold magenta]══════════════════════════════════════════════[/bold magenta]")
        log.write(f"📊 [bold]Auditoría:[/bold] Global {combined}/100 · SEO {seo_report.get('score', 0)}/100 · "
                  f"Jurídico {legal_report.get('score', 0)}/100 · {len(generated.split())} palabras")
        if save_res.get("status") == "success":
            log.write(f"[green]✔ Artículo guardado:[/green] {save_res.get('path')}")

    async def _stream_inference(self, prompt: str, cfg: dict[str, Any], log: RichLog) -> str:
        payload = {
            "model": cfg["model"],
            "prompt": prompt,
            "stream": True,
            "options": {
                "temperature": cfg["temperature"],
                **INFER_PAYLOAD_OPTIONS,
            },
        }
        chunks: list = []
        buf = ""
        timeout_cfg = httpx.Timeout(timeout=600.0, connect=15.0, read=300.0, write=30.0)
        try:
            async with httpx.AsyncClient(timeout=timeout_cfg) as client:
                async with client.stream(
                    "POST", f"{OLLAMA_BASE_URL}/api/generate", json=payload
                ) as response:
                    if response.status_code != 200:
                        log.write(f"[red]✘ Ollama HTTP {response.status_code}[/red]")
                        return ""
                    async for line in response.aiter_lines():
                        if not line:
                            continue
                        try:
                            data = json.loads(line)
                        except json.JSONDecodeError:
                            continue
                        tok = data.get("response", "")
                        if tok:
                            chunks.append(tok)
                            buf += tok
                            while "\n" in buf:
                                out, buf = buf.split("\n", 1)
                                log.write(out)
                        if data.get("done", False):
                            break
        except httpx.HTTPError as exc:
            log.write(f"[red]✘ Error de conexión con Ollama: {exc}[/red]")
        if buf:
            log.write(buf)
        return "".join(chunks)


def main(argv: list | None = None) -> int:
    args = argv if argv is not None else sys.argv[1:]
    src = Path(args[0]) if args and Path(args[0]).is_file() else None
    app = JullEditorTUI(source_file=src)
    app.run()
    return 0


if __name__ == "__main__":
    sys.exit(main())
