"""
Fuente única de verdad para la versión de JullEditor.

SemVer 2.0.0 (https://semver.org/):
    MAJOR.MINOR.PATCH[-PRERELEASE][+BUILD]
    - MAJOR: cambios incompatibles en la API / arquitectura
    - MINOR: funcionalidad nueva retrocompatible
    - PATCH: correcciones de errores retrocompatibles

GitHub toma la versión desde las Tags/Releases del repositorio, por lo que
esta constante debe mantenerse sincronizada con el tag etiquetado (v{VERSION}).
"""

# Componentes individuales según SemVer 2.0.0
MAJOR = 3
MINOR = 3
PATCH = 1
PRERELEASE = None  # p.ej. "rc.1"
BUILD_META = None  # p.ej. "build.20261025"

def get_version() -> str:
    """Devuelve la versión canónica en formato SemVer."""
    base = f"{MAJOR}.{MINOR}.{PATCH}"
    if PRERELEASE:
        base += f"-{PRERELEASE}"
    if BUILD_META:
        base += f"+{BUILD_META}"
    return base

def get_tag() -> str:
    """Devuelve la etiqueta Git correspondiente (convención GitHub: v + SemVer)."""
    return f"v{get_version()}"

__version__ = get_version()
