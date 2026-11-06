#!/usr/bin/env python3
"""Sincroniza todos los artículos de astro_ready/ hacia el blog Astro.

Uso:  python3 scripts/sync_articles.py [--dry-run]

Reutiliza backend.astro_publisher (misma validación de contrato que el
endpoint POST /api/export/publish).
"""
from __future__ import annotations

import argparse
import os
import sys

REPO_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, REPO_ROOT)

from backend.astro_publisher import (  # noqa: E402
    get_publication_status,
    publish_article,
)


def main() -> int:
    parser = argparse.ArgumentParser(description="Publicar artículos astro_ready en el blog Astro")
    parser.add_argument("--dry-run", action="store_true", help="Solo listar estados, no copiar")
    args = parser.parse_args()

    statuses = get_publication_status()
    if not statuses:
        print("[sync] No hay artículos en data/articles_generated/astro_ready/.")
        return 0

    print(f"[sync] {len(statuses)} artículo(s) en astro_ready/:")
    for item in statuses:
        slug = item["slug"]
        state = item["state"]
        if args.dry_run or state == "synced":
            print(f"  - {slug}: {state}")
            continue
        if state == "draft":
            print(f"  [skip] {slug}: borrador (draft=true)")
            continue
        result = publish_article(slug)
        action = result.get("action") or result.get("status", "error")
        ok = result.get("status") == "success"
        message = result.get("message") or result.get("error") or ""
        print(f"  [{'OK ' if ok else 'ERR'}] {slug}: {action} {message}".rstrip())

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
