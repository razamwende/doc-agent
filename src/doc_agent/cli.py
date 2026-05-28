import os
from pathlib import Path
from dotenv import load_dotenv
import click
from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from rich.progress import Progress, SpinnerColumn, TextColumn

from .parser import scan_python_files, parse_file, extract_class_attributes
from .generator import generate_function_docstring, generate_class_docstring, generate_module_docstring
from .injector import inject_docstrings
from .readme_builder import generate_readme, save_readme
from .changelog import generate_changelog, save_changelog

load_dotenv()
console = Console()


@click.group()
def main():
    """🤖 Doc Agent — Documentation automatique par LLM."""
    pass


@main.command()
@click.argument("path", type=click.Path(exists=True, path_type=Path))
@click.option("--provider", default="anthropic", type=click.Choice(["anthropic", "ollama"]), show_default=True)
@click.option("--dry-run/--apply", default=True, show_default=True, help="Simuler sans modifier les fichiers")
@click.option("--skip-existing/--force", default=True, show_default=True, help="Ignorer les fonctions déjà documentées")
def docstring(path: Path, provider: str, dry_run: bool, skip_existing: bool):
    """Génère et injecte des docstrings pour un fichier ou répertoire Python."""
    console.print(Panel(f"[bold blue]🔍 Analyse de {path}[/bold blue]"))
    
    # Charger les modules
    if path.is_file():
        modules = [parse_file(path)]
    else:
        modules = scan_python_files(path)
    
    console.print(f"📦 {len(modules)} fichier(s) Python trouvé(s)")
    
    total_injected = 0
    total_skipped = 0
    
    with Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        console=console,
    ) as progress:
        for module in modules:
            # Compter les éléments sans docstring
            items_to_doc = []
            for func in module.functions:
                if not func.has_docstring or not skip_existing:
                    items_to_doc.append(("function", func, ""))
            for cls in module.classes:
                if not cls.has_docstring or not skip_existing:
                    items_to_doc.append(("class", cls, ""))
                for method in cls.methods:
                    if not method.has_docstring or not skip_existing:
                        items_to_doc.append(("method", method, f"{cls.name}."))
            
            if not items_to_doc:
                continue
            
            task = progress.add_task(
                f"[cyan]Génération pour {module.path.name}[/cyan]",
                total=len(items_to_doc),
            )
            
            class_attrs = extract_class_attributes(module.path)
            docstrings = {}
            for kind, item, prefix in items_to_doc:
                progress.advance(task)
                key = f"{prefix}{item.name}"
                try:
                    if kind in ("function", "method"):
                        docstrings[key] = generate_function_docstring(item, provider, prefix)
                    else:
                        docstrings[key] = generate_class_docstring(item, provider, class_attrs.get(item.name))
                except Exception as e:
                    console.print(f"[red]Erreur pour {key}: {e}[/red]")
            
            result = inject_docstrings(module, docstrings, dry_run=dry_run)
            total_injected += result.injected_count
            total_skipped += result.skipped_count
            
            if result.changes:
                for change in result.changes:
                    console.print(f"  {'[dim][DRY-RUN][/dim] ' if dry_run else ''}[green]{change}[/green]")
    
    mode = "[yellow][DRY-RUN][/yellow]" if dry_run else "[green][APPLIQUÉ][/green]"
    console.print(f"\n{mode} {total_injected} docstrings générées, {total_skipped} ignorées (déjà documentées)")
    if dry_run:
        console.print("💡 Relancez avec [bold]--apply[/bold] pour appliquer les changements")


@main.command()
@click.argument("path", type=click.Path(exists=True, path_type=Path))
@click.option("--provider", default="anthropic", type=click.Choice(["anthropic", "ollama"]), show_default=True)
@click.option("--dry-run/--save", default=True, show_default=True)
@click.option("--name", default=None, help="Nom du projet")
def readme(path: Path, provider: str, dry_run: bool, name: str | None):
    """Génère un README.md pour le projet."""
    console.print(Panel("[bold blue]📖 Génération README[/bold blue]"))
    
    with Progress(SpinnerColumn(), TextColumn("{task.description}"), console=console) as p:
        task = p.add_task("Analyse du code...", total=None)
        modules = scan_python_files(path)
        p.update(task, description=f"Génération via {provider}...")
        content = generate_readme(path, modules, name, provider)
    
    if dry_run:
        console.print(Panel(content, title="README.md (preview)", border_style="blue"))
        console.print("💡 Relancez avec [bold]--save[/bold] pour sauvegarder")
    else:
        readme_path = save_readme(path, content, dry_run=False)
        console.print(f"[green]✅ README sauvegardé : {readme_path}[/green]")


@main.command()
@click.argument("path", type=click.Path(exists=True, path_type=Path))
@click.option("--provider", default="anthropic", type=click.Choice(["anthropic", "ollama"]), show_default=True)
@click.option("--dry-run/--save", default=True, show_default=True)
@click.option("--name", default=None, help="Nom du projet")
def changelog(path: Path, provider: str, dry_run: bool, name: str | None):
    """Génère un CHANGELOG.md depuis l'historique git."""
    console.print(Panel("[bold blue]📋 Génération CHANGELOG[/bold blue]"))
    
    with Progress(SpinnerColumn(), TextColumn("{task.description}"), console=console) as p:
        p.add_task(f"Génération via {provider}...", total=None)
        content = generate_changelog(path, name, provider)
    
    if dry_run:
        console.print(Panel(content, title="CHANGELOG.md (preview)", border_style="blue"))
        console.print("💡 Relancez avec [bold]--save[/bold] pour sauvegarder")
    else:
        cl_path = save_changelog(path, content, dry_run=False)
        console.print(f"[green]✅ CHANGELOG sauvegardé : {cl_path}[/green]")


@main.command()
@click.argument("path", type=click.Path(exists=True, path_type=Path))
def stats(path: Path):
    """Affiche les statistiques de documentation du projet."""
    modules = scan_python_files(path)
    
    table = Table(title="📊 Couverture de documentation", show_header=True)
    table.add_column("Fichier", style="cyan")
    table.add_column("Fonctions", justify="right")
    table.add_column("Documentées", justify="right")
    table.add_column("Couverture", justify="right")
    
    total_funcs = total_documented = 0
    
    for module in modules:
        all_funcs = list(module.functions)
        for cls in module.classes:
            all_funcs.extend(cls.methods)
        
        documented = sum(1 for f in all_funcs if f.has_docstring)
        total = len(all_funcs)
        coverage = (documented / total * 100) if total > 0 else 100.0
        
        total_funcs += total
        total_documented += documented
        
        color = "green" if coverage >= 80 else "yellow" if coverage >= 50 else "red"
        table.add_row(
            str(module.path.name),
            str(total),
            str(documented),
            f"[{color}]{coverage:.0f}%[/{color}]",
        )
    
    console.print(table)
    overall = (total_documented / total_funcs * 100) if total_funcs > 0 else 100.0
    console.print(f"\n[bold]Total : {total_documented}/{total_funcs} fonctions documentées ({overall:.0f}%)[/bold]")