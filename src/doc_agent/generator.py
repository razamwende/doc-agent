import os
import json
from anthropic import Anthropic
import requests
from .parser import FunctionInfo, ClassInfo, ModuleInfo

ANTHROPIC_MODEL = "claude-haiku-4-5-20251001"
OLLAMA_MODEL = "qwen2.5-coder:1.5b"

def _call_anthropic(prompt: str, system: str) -> str:
    """
    Appelle l'API Anthropic avec le prompt et le système fournis pour générer une réponse textuelle.

    Args:
        prompt: Le texte de la requête à envoyer à Anthropic.
        system: Le message système définissant le comportement et le contexte du modèle.

    Returns:
        La réponse textuelle générée par Anthropic.
    """
    client = Anthropic(api_key=os.environ["ANTHROPIC_API_KEY"])
    msg = client.messages.create(
        model=ANTHROPIC_MODEL,
        max_tokens=1024,
        system=system,
        messages=[{"role": "user", "content": prompt}],
    )
    return msg.content[0].text

def _call_ollama(prompt: str, system: str) -> str:
    """
    Envoie un prompt à Ollama et retourne la réponse générée.

    Args:
        prompt (str): Le texte de la requête à traiter.
        system (str): Les instructions système pour guider la génération.

    Returns:
        str: La réponse générée par Ollama.
    """
    ollama_url = os.getenv("OLLAMA_URL", "http://localhost:11434")
    payload = {
        "model": OLLAMA_MODEL,
        "prompt": f"{system}\n\n{prompt}",
        "stream": False,
    }
    resp = requests.post(f"{ollama_url}/api/generate", json=payload, timeout=120)
    resp.raise_for_status()
    return resp.json()["response"]

SYSTEM_DOCSTRING = """Tu es un expert Python qui génère des docstrings claires et précises.
Réponds UNIQUEMENT avec la docstring, sans guillemets triples et sans autre texte.
Utilise le format Google Style. Sois concis mais complet.
Si la fonction est simple et évidente, une phrase suffit."""
def generate_function_docstring(
    func: FunctionInfo,
    provider: str = "anthropic",
    context: str = "",
) -> str:
    """
    Génère une docstring Google Style pour une fonction.
    
    Args:
        func: Informations sur la fonction (nom, args, source)
        provider: "anthropic" ou "ollama"
        context: Contexte supplémentaire (nom du module, classe parente...)
        
    Returns:
        Docstring générée (sans les guillemets triples)
    """
    args_str = ", ".join(func.args) if func.args else "(aucun argument)"
    returns_str = f"-> {func.returns}" if func.returns else "(non annoté)"
    
    prompt = f"""Génère une docstring Google Style pour cette fonction Python.

Contexte : {context or 'Module standalone'}
Nom : {func.name}
Arguments : {args_str}
Retour : {returns_str}

Code source :

Docstring (sans guillemets triples) :"""
    
    call_fn = _call_anthropic if provider == "anthropic" else _call_ollama
    result = call_fn(prompt, SYSTEM_DOCSTRING)
    # Nettoyer les guillemets triples si le LLM en a quand même ajouté
    result = result.strip().strip('"').strip("'")
    if result.startswith("\"\"\"") or result.startswith("'''"):
        result = result[3:]
    if result.endswith("\"\"\"") or result.endswith("'''"):
        result = result[:-3]
    return result.strip()


def generate_class_docstring(
    cls: ClassInfo,
    provider: str = "anthropic",
    attributes: list[str] | None = None,
) -> str:
    """Génère une docstring pour une classe Python."""
    methods_str = ", ".join(m.name for m in cls.methods[:10])
    bases_str = ", ".join(cls.bases) if cls.bases else "object"
    attrs_str = "\n".join(f"    {a}" for a in attributes) if attributes else "    (aucun)"

    prompt = f"""Génère une docstring Google Style pour cette classe Python.
Liste UNIQUEMENT les attributs fournis ci-dessous. Ne suppose rien d'autre.

Nom : {cls.name}
Hérite de : {bases_str}
Attributs :
{attrs_str}
Méthodes principales : {methods_str or '(aucune)'}

Docstring (sans guillemets triples) :"""
    
    call_fn = _call_anthropic if provider == "anthropic" else _call_ollama
    result = call_fn(prompt, SYSTEM_DOCSTRING)
    result = result.strip().strip('"').strip("'")
    return result.strip()


def generate_module_docstring(
    module: ModuleInfo,
    provider: str = "anthropic",
) -> str:
    """Génère la docstring de module (premier commentaire du fichier)."""
    funcs = ", ".join(f.name for f in module.functions[:8])
    classes = ", ".join(c.name for c in module.classes[:5])
    
    prompt = f"""Génère une docstring de module Python (une ou deux phrases maximum).

Fichier : {module.path.name}
Fonctions : {funcs or '(aucune)'}
Classes : {classes or '(aucune)'}

Docstring (sans guillemets triples) :"""
    
    call_fn = _call_anthropic if provider == "anthropic" else _call_ollama
    result = call_fn(prompt, SYSTEM_DOCSTRING)
    return result.strip().strip('"').strip("'")