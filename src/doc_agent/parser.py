# src/doc_agent/parser.py
import ast
from dataclasses import dataclass, field
from pathlib import Path


@dataclass
class FunctionInfo:
    name: str
    args: list[str]
    returns: str | None
    has_docstring: bool
    lineno: int
    end_lineno: int
    source: str
    decorators: list[str] = field(default_factory=list)


@dataclass
class ClassInfo:
    name: str
    bases: list[str]
    has_docstring: bool
    lineno: int
    end_lineno: int
    methods: list[FunctionInfo] = field(default_factory=list)


@dataclass
class ModuleInfo:
    path: Path
    has_docstring: bool
    functions: list[FunctionInfo] = field(default_factory=list)
    classes: list[ClassInfo] = field(default_factory=list)
    imports: list[str] = field(default_factory=list)


def _get_docstring(node: ast.AST) -> bool:
    """Vérifie si un nœud AST possède déjà une docstring."""
    if not (node.body and isinstance(node.body[0], ast.Expr)):
        return False
    val = node.body[0].value
    return isinstance(val, ast.Constant) and isinstance(val.value, str)


def _extract_args(node: ast.FunctionDef | ast.AsyncFunctionDef) -> list[str]:
    """Extrait les noms des arguments (hors self/cls)."""
    args = []
    for arg in node.args.args:
        if arg.arg not in ("self", "cls"):
            args.append(arg.arg)
    return args


def _get_return_annotation(node: ast.FunctionDef | ast.AsyncFunctionDef) -> str | None:
    """Récupère l'annotation de retour si présente."""
    if node.returns is None:
        return None
    return ast.unparse(node.returns)


def _extract_decorators(node: ast.FunctionDef | ast.AsyncFunctionDef) -> list[str]:
    """Récupère les noms des décorateurs."""
    return [ast.unparse(d) for d in node.decorator_list]


def parse_file(path: Path) -> ModuleInfo:
    """
    Parse un fichier Python avec le module ast.
    
    Args:
        path: Chemin vers le fichier .py à analyser
        
    Returns:
        ModuleInfo avec toutes les fonctions, classes et imports extraits
    """
    source = path.read_text(encoding="utf-8")
    tree = ast.parse(source, filename=str(path))
    
    module = ModuleInfo(
        path=path,
        has_docstring=_get_docstring(tree),
    )
    
    # Extraire les imports
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                module.imports.append(alias.name)
        elif isinstance(node, ast.ImportFrom):
            module.imports.append(f"{node.module}")
    
    # Extraire fonctions de haut niveau
    for node in tree.body:
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            func_source = ast.get_source_segment(source, node) or ""
            module.functions.append(FunctionInfo(
                name=node.name,
                args=_extract_args(node),
                returns=_get_return_annotation(node),
                has_docstring=_get_docstring(node),
                lineno=node.lineno,
                end_lineno=node.end_lineno,
                source=func_source,
                decorators=_extract_decorators(node),
            ))
        elif isinstance(node, ast.ClassDef):
            bases = [ast.unparse(b) for b in node.bases]
            class_info = ClassInfo(
                name=node.name,
                bases=bases,
                has_docstring=_get_docstring(node),
                lineno=node.lineno,
                end_lineno=node.end_lineno,
            )
            # Méthodes de la classe
            for item in node.body:
                if isinstance(item, (ast.FunctionDef, ast.AsyncFunctionDef)):
                    method_source = ast.get_source_segment(source, item) or ""
                    class_info.methods.append(FunctionInfo(
                        name=item.name,
                        args=_extract_args(item),
                        returns=_get_return_annotation(item),
                        has_docstring=_get_docstring(item),
                        lineno=item.lineno,
                        end_lineno=item.end_lineno,
                        source=method_source,
                        decorators=_extract_decorators(item),
                    ))
            module.classes.append(class_info)
    
    return module


def scan_python_files(root: Path) -> list[ModuleInfo]:
    """
    Scanne récursivement un répertoire et parse tous les fichiers .py.
    
    Ignore : tests/, __pycache__/, migrations/, venv/
    """
    IGNORED_DIRS = {"__pycache__", ".git", "venv", ".venv", "node_modules", 
                    "migrations", ".tox", "build", "dist"}
    
    modules = []
    for py_file in root.rglob("*.py"):
        # Ignorer les répertoires exclus
        if any(part in IGNORED_DIRS for part in py_file.parts):
            continue
        # Ignorer les fichiers trop volumineux (> 200 Ko)
        if py_file.stat().st_size > 200_000:
            continue
        try:
            modules.append(parse_file(py_file))
        except SyntaxError:
            pass  # Fichier avec erreur de syntaxe → ignorer
    
    return modules