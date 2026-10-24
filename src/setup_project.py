"""
SAHAAYA Project Setup Script
─────────────────────────────
Creates the complete directory structure required by the project.
Safe to run repeatedly — never deletes or overwrites existing files.

Usage:
    python src/setup_project.py
"""
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

DIRECTORIES = [
    # Raw data (user downloads go here)
    "data/raw/udise",
    "data/raw/nfhs",
    "data/raw/mgnrega",
    "data/raw/boundaries",
    "data/raw/additional",
    # Pipeline outputs
    "data/interim",
    "data/processed",
    "data/metadata",
    # ML model artifacts
    "models",
    # Generated reports
    "reports",
    # Documentation
    "docs",
    # Source code
    "src/ingestion",
    "src/preprocessing",
    "src/features",
    "src/models",
    "src/evaluation",
    # Tests
    "tests",
    # Streamlit app
    "app/pages",
]

# Python packages need __init__.py
INIT_PACKAGES = [
    "src",
    "src/ingestion",
    "src/preprocessing",
    "src/features",
    "src/models",
    "src/evaluation",
    "tests",
]

# Empty .gitkeep files so git tracks empty dirs
GITKEEP_DIRS = [
    "data/raw/udise",
    "data/raw/nfhs",
    "data/raw/mgnrega",
    "data/raw/boundaries",
    "data/raw/additional",
    "data/interim",
    "data/metadata",
    "models",
    "reports",
]


def setup():
    """Create all required directories and placeholder files."""
    print("=" * 60)
    print("  SAHAAYA — Project Setup")
    print("=" * 60)
    print(f"\nProject root: {ROOT}\n")

    created_dirs = []
    created_files = []
    skipped = []

    # ── Directories ──────────────────────────────────────────
    for d in DIRECTORIES:
        path = ROOT / d
        if not path.exists():
            path.mkdir(parents=True, exist_ok=True)
            created_dirs.append(d)
        else:
            skipped.append(d)

    # ── __init__.py files ────────────────────────────────────
    for pkg in INIT_PACKAGES:
        init = ROOT / pkg / "__init__.py"
        if not init.exists():
            init.touch()
            created_files.append(str(init.relative_to(ROOT)))

    # ── .gitkeep placeholders ────────────────────────────────
    for d in GITKEEP_DIRS:
        gk = ROOT / d / ".gitkeep"
        if not gk.exists():
            gk.touch()
            created_files.append(str(gk.relative_to(ROOT)))

    # ── Summary ──────────────────────────────────────────────
    if created_dirs:
        print(f"[DIR] Created {len(created_dirs)} directories:")
        for d in created_dirs:
            print(f"   + {d}/")
    if created_files:
        print(f"\n[FILE] Created {len(created_files)} files:")
        for f in created_files:
            print(f"   + {f}")
    if skipped:
        print(f"\n[OK] {len(skipped)} directories already existed (untouched)")

    print("\n" + "=" * 60)
    print("  Setup complete.")
    print("=" * 60)


if __name__ == "__main__":
    setup()
