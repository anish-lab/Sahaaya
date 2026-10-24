"""
Tests for project setup (directory creation).
"""
import sys
from pathlib import Path
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))


class TestSetupProject:
    """Test that setup_project.py creates all required directories."""

    def test_setup_creates_directories(self, tmp_path, monkeypatch):
        """Verify all directories are created in a temp location."""
        from src.setup_project import DIRECTORIES

        # Patch ROOT to use tmp_path
        import src.setup_project as setup_mod
        monkeypatch.setattr(setup_mod, "ROOT", tmp_path)

        setup_mod.setup()

        for d in DIRECTORIES:
            assert (tmp_path / d).exists(), f"Directory {d} was not created"

    def test_setup_is_idempotent(self, tmp_path, monkeypatch):
        """Verify running setup twice does not error or delete files."""
        import src.setup_project as setup_mod
        monkeypatch.setattr(setup_mod, "ROOT", tmp_path)

        setup_mod.setup()
        # Place a file in one of the created dirs
        marker = tmp_path / "data" / "raw" / "udise" / "test_marker.txt"
        marker.write_text("keep me")

        setup_mod.setup()  # Second run
        assert marker.exists(), "Setup deleted an existing file on re-run"

    def test_init_files_created(self, tmp_path, monkeypatch):
        """Verify __init__.py files are created for Python packages."""
        from src.setup_project import INIT_PACKAGES
        import src.setup_project as setup_mod
        monkeypatch.setattr(setup_mod, "ROOT", tmp_path)

        setup_mod.setup()

        for pkg in INIT_PACKAGES:
            init_path = tmp_path / pkg / "__init__.py"
            assert init_path.exists(), f"__init__.py missing for {pkg}"
