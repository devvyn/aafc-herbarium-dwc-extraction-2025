from __future__ import annotations

from functools import lru_cache
from pathlib import Path
from typing import Dict
import tomllib

# Base directory for rule files
_RULES_DIR = Path(__file__).resolve().parent.parent / "config" / "rules"


@lru_cache(maxsize=None)
def _load_rules(name: str) -> Dict[str, Dict[str, str]]:
    """Load a TOML rule file from the configuration directory.

    Parameters
    ----------
    name: str
        Name of the rule file without extension.
    """

    path = _RULES_DIR / f"{name}.toml"
    if not path.exists():
        return {}
    with path.open("rb") as fh:
        return tomllib.load(fh)


def normalize_institution(value: str) -> str:
    """Return the normalised institution code for ``value``.

    The function consults ``config/rules/institutions.toml`` which is
    expected to contain a simple mapping of aliases to canonical codes.
    If no rule matches, the original ``value`` is returned unchanged.
    """

    if not value:
        return value
    rules = _load_rules("institutions")
    mapping = {k.lower(): v for k, v in rules.items()}
    return mapping.get(value.lower(), value)


def normalize_vocab(value: str, vocab: str) -> str:
    """Normalise ``value`` based on the vocabulary ``vocab``.

    The ``config/rules/vocab.toml`` file can contain nested tables where the
    top-level keys correspond to vocabulary names (e.g. ``basisOfRecord``)
    and the nested key/value pairs map observed values to controlled
    vocabulary terms.
    """

    if not value:
        return value
    rules = _load_rules("vocab")
    section = rules.get(vocab, {})
    mapping = {k.lower(): v for k, v in section.items()}
    return mapping.get(value.lower(), value)
