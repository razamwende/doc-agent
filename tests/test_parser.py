import pytest
from pathlib import Path
from doc_agent.parser import parse_file, scan_python_files

FIXTURES = Path(__file__).parent / "fixtures"


def test_parse_file_basic():
    module = parse_file(FIXTURES / "sample_module.py")
    assert module.has_docstring is True
    assert len(module.functions) == 2
    assert len(module.classes) == 1


def test_function_with_docstring():
    module = parse_file(FIXTURES / "sample_module.py")
    add_func = next(f for f in module.functions if f.name == "add")
    assert add_func.has_docstring is True
    assert add_func.args == ["a", "b"]
    assert add_func.returns == "int"


def test_function_without_docstring():
    module = parse_file(FIXTURES / "sample_module.py")
    undoc = next(f for f in module.functions if f.name == "undocumented_function")
    assert undoc.has_docstring is False
    assert len(undoc.args) == 3


def test_class_parsing():
    module = parse_file(FIXTURES / "sample_module.py")
    calc = module.classes[0]
    assert calc.name == "Calculator"
    assert calc.has_docstring is True
    assert len(calc.methods) == 3  # __init__, multiply, undocumented_method


def test_scan_ignores_pycache(tmp_path):
    # Créer une structure avec __pycache__
    (tmp_path / "__pycache__").mkdir()
    (tmp_path / "__pycache__" / "test.py").write_text("x = 1")
    (tmp_path / "main.py").write_text("def foo(): pass")
    
    modules = scan_python_files(tmp_path)
    paths = [str(m.path) for m in modules]
    assert all("__pycache__" not in p for p in paths)
    assert any("main.py" in p for p in paths)