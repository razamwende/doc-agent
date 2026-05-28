from pathlib import Path
from dataclasses import dataclass
from .parser import ModuleInfo, FunctionInfo, ClassInfo

@dataclass
class InjectionResult:
    """
    Conteneur pour les résultats d'une injection de dépendance.

    Attributes:
        success (bool): Indique si l'injection a réussi.
        value (Any): La valeur injectée ou None en cas d'échec.
        error (Exception): L'exception levée lors de l'injection, ou None si réussie.
    """
    path: Path
    injected_count: int
    skipped_count: int  # déjà documentés
    changes: list[str]  # descriptions des changements

def _indent_docstring(docstring: str, indent: int) -> str:
    """
    Formate une docstring avec l'indentation correcte.
    
    Args:
        docstring: Contenu de la docstring (sans guillemets triples)
        indent: Nombre d'espaces d'indentation
        
    Returns:
        Docstring complète avec guillemets triples et indentation
    """
    prefix = " " * indent
    lines = docstring.splitlines()
    
    if len(lines) == 1:
        # Docstring sur une ligne
        return f'{prefix}    \"\"\"{docstring}\"\"\"\n'
    else:
        # Docstring multi-lignes
        formatted_lines = [f'{prefix}    \"\"\"']
        for line in lines:
            formatted_lines.append(f'{prefix}    {line}' if line.strip() else "")
        formatted_lines.append(f'{prefix}    \"\"\"')
        return "\n".join(formatted_lines) + "\n"


def inject_docstrings(
    module: ModuleInfo,
    docstrings: dict[str, str],
    dry_run: bool = True,
) -> InjectionResult:
    """
    Injecte les docstrings générées dans un fichier Python.
    
    Stratégie : insertion ligne par ligne en partant de la fin du fichier
    pour ne pas décaler les numéros de ligne.
    
    Args:
        module: Module analysé par le parser AST
        docstrings: dict {"ClassName.method" ou "function_name": "docstring"}
        dry_run: Si True, affiche les changements sans modifier le fichier
        
    Returns:
        InjectionResult avec le compte des injections
    """
    source_lines = module.path.read_text(encoding="utf-8").splitlines(keepends=True)
    
    # Construire la liste d'insertions (lineno → docstring_text)
    # On travaille de la fin vers le début pour ne pas décaler les indices
    insertions: list[tuple[int, str]] = []  # (line_index_after_def, content)
    injected = 0
    skipped = 0
    changes = []
    
    def _process_func(func: FunctionInfo, prefix: str = "") -> None:
        nonlocal injected, skipped
        key = f"{prefix}{func.name}" if prefix else func.name
        
        if func.has_docstring:
            skipped += 1
            return
        if key not in docstrings:
            return
        
        # Trouver la ligne du 'def' et calculer l'indentation
        def_line = source_lines[func.lineno - 1]
        indent = len(def_line) - len(def_line.lstrip())
        
        # Trouver la première ligne du corps (après le ':' de def)
        # La ligne d'insertion est func.lineno (0-indexed)
        insert_at = func.lineno  # après la ligne 'def'
        
        # Gérer les def multi-lignes (arguments sur plusieurs lignes)
        # On cherche le ':' final
        for i in range(func.lineno - 1, min(func.lineno + 10, len(source_lines))):
            if source_lines[i].rstrip().endswith(":"):
                insert_at = i + 1
                break
        
        doc_content = _indent_docstring(docstrings[key], indent)
        insertions.append((insert_at, doc_content))
        injected += 1
        changes.append(f"+ docstring → {key}() (ligne {func.lineno})")
    
    # Traiter fonctions de haut niveau
    for func in module.functions:
        _process_func(func)
    
    # Traiter classes et méthodes
    for cls in module.classes:
        if not cls.has_docstring and cls.name in docstrings:
            def_line = source_lines[cls.lineno - 1]
            indent = len(def_line) - len(def_line.lstrip())
            doc_content = _indent_docstring(docstrings[cls.name], indent)
            insertions.append((cls.lineno, doc_content))
            injected += 1
            changes.append(f"+ docstring → class {cls.name} (ligne {cls.lineno})")
        
        for method in cls.methods:
            _process_func(method, prefix=f"{cls.name}.")
    
    if dry_run or not insertions:
        return InjectionResult(
            path=module.path,
            injected_count=injected,
            skipped_count=skipped,
            changes=changes,
        )
    
    # Appliquer les insertions en ordre inverse (fin → début)
    insertions.sort(key=lambda x: x[0], reverse=True)
    for insert_at, content in insertions:
        source_lines.insert(insert_at, content)
    
    module.path.write_text("".join(source_lines), encoding="utf-8")
    
    return InjectionResult(
        path=module.path,
        injected_count=injected,
        skipped_count=skipped,
        changes=changes,
    )