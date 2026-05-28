# Doc Agent

[![Python](https://img.shields.io/badge/python-3.8%2B-blue)](https://www.python.org/)
[![License](https://img.shields.io/badge/license-MIT-green.svg)](LICENSE)
[![Code style: black](https://img.shields.io/badge/code%20style-black-000000.svg)](https://github.com/psf/black)

Automate la génération de documentation pour vos projets Python avec l'IA. **Doc Agent** crée des docstrings, README et CHANGELOG de qualité professionnelle en quelques secondes.

## ✨ Fonctionnalités

- 🤖 **Génération automatique de docstrings** - Injecte intelligemment des docstrings dans vos fonctions et classes
- 📖 **Génération de README** - Crée un README structuré à partir de votre code
- 📝 **Génération de CHANGELOG** - Extrait l'historique Git et le formate automatiquement
- 📊 **Analyse statistique** - Affiche des métriques sur votre codebase
- 🔍 **Support multi-providers** - Anthropic Claude et Ollama
- 🏃 **Mode dry-run** - Prévisualisez les changements sans modifier le code
- ⏭️ **Skip existants** - Ignore les docstrings déjà présentes

## 📦 Installation

### Avec pip

```bash
pip install doc-agent
```

### Depuis les sources

```bash
git clone https://github.com/yourusername/doc-agent.git
cd doc-agent
pip install -e .
```

### Dépendances

- Python 3.8+
- anthropic (pour utiliser Anthropic Claude)
- ollama (pour utiliser Ollama en local)
- gitpython (pour la génération de CHANGELOG)

## 🚀 Utilisation

### En tant que CLI

#### Générer des docstrings

```bash
# Générer des docstrings pour tous les fichiers
doc-agent docstring ./src

# Mode dry-run (aperçu sans modification)
doc-agent docstring ./src --dry-run

# Ignorer les docstrings existants
doc-agent docstring ./src --skip-existing

# Utiliser Ollama au lieu d'Anthropic
doc-agent docstring ./src --provider ollama
```

#### Générer un README

```bash
# Générer un README automatique
doc-agent readme ./src --name "Mon Projet"

# Aperçu avant d'écrire
doc-agent readme ./src --name "Mon Projet" --dry-run

# Avec un provider spécifique
doc-agent readme ./src --name "Mon Projet" --provider ollama
```

#### Générer un CHANGELOG

```bash
# Générer un CHANGELOG à partir de l'historique Git
doc-agent changelog ./src --name "Mon Projet"

# Mode dry-run
doc-agent changelog ./src --name "Mon Projet" --dry-run
```

#### Afficher les statistiques

```bash
# Analyser la couverture de documentation
doc-agent stats ./src
```

### Exemples pratiques

**Flux complet de documentation d'un projet :**

```bash
# 1. Analyser le projet
doc-agent stats ./src

# 2. Générer les docstrings en aperçu
doc-agent docstring ./src --dry-run --skip-existing

# 3. Appliquer les docstrings
doc-agent docstring ./src --skip-existing

# 4. Générer le README
doc-agent readme ./src --name "Doc Agent" --dry-run

# 5. Générer le CHANGELOG
doc-agent changelog ./src --name "Doc Agent"
```

## 📁 Structure du projet

```
doc-agent/
├── src/doc_agent/
│   ├── __init__.py
│   ├── parser.py           # Extraction d'AST et parsing
│   ├── generator.py        # Génération IA des docstrings
│   ├── inj