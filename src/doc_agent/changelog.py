import subprocess
from pathlib import Path
from datetime import date
from .generator import _call_anthropic, _call_ollama


def _get_git_log(root: Path, max_commits: int = 50) -> str:
    """
    Récupère l'historique git formaté.
    
    Format : hash court | date | auteur | message
    """
    try:
        result = subprocess.run(
            [
                "git", "log",
                f"--max-count={max_commits}",
                "--pretty=format:%h | %ad | %an | %s",
                "--date=short",
                "--no-merges",
            ],
            cwd=root,
            capture_output=True,
            text=True,
            timeout=10,
        )
        if result.returncode != 0:
            return ""
        return result.stdout.strip()
    except (subprocess.TimeoutExpired, FileNotFoundError):
        return ""


def _get_git_tags(root: Path) -> list[str]:
    """Récupère les tags git pour structurer le changelog par version."""
    try:
        result = subprocess.run(
            ["git", "tag", "--sort=-version:refname"],
            cwd=root,
            capture_output=True,
            text=True,
            timeout=5,
        )
        return result.stdout.strip().splitlines()[:10]
    except (subprocess.TimeoutExpired, FileNotFoundError):
        return []


SYSTEM_CHANGELOG = """Tu es un expert en rédaction de changelogs techniques.
Génère un CHANGELOG.md au format Keep a Changelog (https://keepachangelog.com).
Regrouper les commits par catégorie : Added, Changed, Fixed, Removed.
Utilise les versions git si disponibles, sinon crée une section Unreleased.
Sois précis et orienté utilisateur (pas de messages de commit trop techniques)."""


def generate_changelog(
    root: Path,
    project_name: str | None = None,
    provider: str = "anthropic",
) -> str:
    """
    Génère un CHANGELOG.md à partir de l'historique git.
    
    Args:
        root: Répertoire racine du dépôt git
        project_name: Nom du projet
        provider: "anthropic" ou "ollama"
        
    Returns:
        Contenu du CHANGELOG.md
    """
    git_log = _get_git_log(root)
    if not git_log:
        return f"# Changelog\n\n## [Unreleased]\n\nAucun historique git disponible.\n"
    
    tags = _get_git_tags(root)
    tags_str = ", ".join(tags) if tags else "(aucun tag)"
    
    prompt = f"""Génère un CHANGELOG.md au format Keep a Changelog.

Projet : {project_name or root.name}
Tags git (versions) : {tags_str}
Date du jour : {date.today().isoformat()}

Historique des commits :
{git_log}

Crée le CHANGELOG.md complet."""
    
    call_fn = _call_anthropic if provider == "anthropic" else _call_ollama
    return call_fn(prompt, SYSTEM_CHANGELOG)


def save_changelog(root: Path, content: str, dry_run: bool = True) -> Path:
    """Sauvegarde ou affiche le CHANGELOG généré."""
    changelog_path = root / "CHANGELOG.md"
    if dry_run:
        return changelog_path
    changelog_path.write_text(content, encoding="utf-8")
    return changelog_path