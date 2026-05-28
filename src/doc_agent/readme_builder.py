from pathlib import Path
from .parser import ModuleInfo
from .generator import _call_anthropic, _call_ollama

def _build_api_summary(modules: list[ModuleInfo]) -> str:
    """Construit un résumé de l'API publique pour le prompt."""
    lines = []
    for module in modules:
        rel_path = str(module.path)
        if module.functions:
            func_names = [f"{f.name}({', '.join(f.args)})" for f in module.functions[:5]]
            lines.append(f"**{rel_path}** : {', '.join(func_names)}")
        for cls in module.classes[:3]:
            method_names = [m.name for m in cls.methods[:5]]
            lines.append(f"  └─ class {cls.name} : {', '.join(method_names)}")
    return "\n".join(lines[:50])  # Limiter pour le prompt

SYSTEM_README = """Tu es un expert en documentation technique. 
Génère un README.md complet, professionnel et attrayant en Markdown.
Inclus : titre, badges (Python version, license), description, features, 
installation, usage avec exemples de code, structure du projet, contributing.
Sois concis et pratique. Ne génère pas de contenu fictif."""

def generate_readme(
    root: Path,
    modules: list[ModuleInfo],
    project_name: str | None = None,
    provider: str = "anthropic",
) -> str:
    """
    Génère un README.md complet pour le projet.
    
    Args:
        root: Répertoire racine du projet
        modules: Liste des modules parsés
        project_name: Nom du projet (déduit du dossier si non fourni)
        provider: "anthropic" ou "ollama"
        
    Returns:
        Contenu du README.md en Markdown
    """
    name = project_name or root.name
    api_summary = _build_api_summary(modules)
    
    total_funcs = sum(len(m.functions) for m in modules)
    total_classes = sum(len(m.classes) for m in modules)
    total_files = len(modules)
    
    # Détecter le type de projet
    has_cli = any(
        any("click" in imp or "argparse" in imp for imp in m.imports)
        for m in modules
    )
    has_fastapi = any(
        any("fastapi" in imp for imp in m.imports)
        for m in modules
    )
    
    project_type = "API FastAPI" if has_fastapi else "CLI" if has_cli else "Library Python"
    
    prompt = f"""Génère un README.md complet pour ce projet Python.

Nom du projet : {name}
Type : {project_type}
Fichiers Python : {total_files}
Fonctions : {total_funcs}
Classes : {total_classes}

API publique principale :
{api_summary}

Crée un README.md professionnel avec installation, usage et exemples."""
    
    call_fn = _call_anthropic if provider == "anthropic" else _call_ollama
    return call_fn(prompt, SYSTEM_README)


def save_readme(root: Path, content: str, dry_run: bool = True) -> Path:
    """Sauvegarde ou affiche le README généré."""
    readme_path = root / "README.md"
    if dry_run:
        return readme_path
    readme_path.write_text(content, encoding="utf-8")
    return readme_path