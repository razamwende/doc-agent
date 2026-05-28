import pytest
from pathlib import Path
from doc_agent.parser import parse_file
from doc_agent.injector import inject_docstrings


def test_dry_run_does_not_modify(tmp_path):
    py_file = tmp_path / "test.py"
    py_file.write_text("def foo(x):\n    return x * 2\n")
    original_content = py_file.read_text()
    
    module = parse_file(py_file)
    result = inject_docstrings(module, {"foo": "Multiplie x par 2."}, dry_run=True)
    
    assert py_file.read_text() == original_content
    assert result.injected_count == 1


def test_apply_injects_docstring(tmp_path):
    py_file = tmp_path / "test.py"
    py_file.write_text("def foo(x: int) -> int:\n    return x * 2\n")
    
    module = parse_file(py_file)
    result = inject_docstrings(
        module, {"foo": "Multiplie x par 2."}, dry_run=False
    )
    
    content = py_file.read_text()
    assert '"""Multiplie x par 2."""' in content
    assert result.injected_count == 1


def test_skip_existing_docstring(tmp_path):
    py_file = tmp_path / "test.py"
    py_file.write_text('def foo():\n    """Déjà documenté."""\n    pass\n')
    
    module = parse_file(py_file)
    result = inject_docstrings(module, {"foo": "Nouvelle docstring"}, dry_run=False)
    
    content = py_file.read_text()
    assert "Déjà documenté." in content  # non modifié
    assert result.skipped_count == 1
    assert result.injected_count == 0