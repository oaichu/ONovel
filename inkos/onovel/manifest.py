"""Per-book manifest <book>/onovel.yaml, validated by JSON schema whenever a book is opened.
No name guessing: genre_id must be a key in genre-kit/genres.yaml and skill_set a key in its skill_sets."""
import os, json, yaml, jsonschema
from . import GENRE_KIT
SCHEMA = {
  "type": "object", "additionalProperties": False,
  "required": ["schema_version", "id", "title", "genre_id", "subgenre", "audience", "register", "style_profile", "xung_ho", "layout"],
  "properties": {
    "schema_version": {"const": 1},
    "id": {"type": "string", "pattern": "^[a-z0-9][a-z0-9-]*$"},
    "title": {"type": "string", "minLength": 1},
    "genre_id": {"type": "string"},
    "skill_set": {"type": "string"},
    "subgenre": {"type": "string"},
    "audience": {"type": "string", "enum": ["nam", "nu", "chung"]},
    "language": {"type": "string", "default": "vi"},
    "register": {"type": "string"},
    "style_profile": {"type": "string", "description": "path of the locked style bible, relative to the book dir"},
    "narration": {"type": "string"},
    "xung_ho": {"type": "object", "additionalProperties": False, "required": ["rules"],
      "properties": {"rules": {"type": "array", "items": {"type": "string"}, "minItems": 1},
                     "forbidden_for": {"type": "object", "additionalProperties": {"type": "array", "items": {"type": "string"}}}}},
    "layout": {"type": "object", "additionalProperties": False, "required": ["heading_style", "blocking"],
      "properties": {"heading_style": {"enum": ["colon", "dot"]},
                     "blocking": {"type": "array", "items": {"enum": ["heading", "length"]}},
                     "target_words": {"type": "integer", "minimum": 500},
                     "min_words": {"type": "integer", "minimum": 300},
                     "max_words": {"type": "integer", "minimum": 1000}}},
    "soft_max": {"type": "integer", "minimum": 0},
    "max_attempts": {"type": "integer", "minimum": 1},
    "state_domains": {"type": "array", "items": {"enum": ["realms", "secrets", "treasures", "promises", "foreshadowing", "relationships", "factions"]}},
    "publish": {"type": "object", "properties": {"site_book_id": {"type": "string"}}, "additionalProperties": False},
  }}
class ManifestError(Exception): pass
def genres():
    return yaml.safe_load(open(os.path.join(GENRE_KIT, "genres.yaml"), encoding="utf-8")) or {}
def load(book):
    p = os.path.join(book, "onovel.yaml")
    if not os.path.exists(p): raise ManifestError(f"missing manifest {p} (create with: onovel manifest-init or onovel new)")
    m = yaml.safe_load(open(p, encoding="utf-8")) or {}
    validate(m, book); return m
def validate(m, book=None):
    try: jsonschema.validate(m, SCHEMA)
    except jsonschema.ValidationError as e: raise ManifestError(f"onovel.yaml invalid at {'/'.join(map(str, e.path)) or '<root>'}: {e.message}")
    g = genres()
    if m["genre_id"] not in g or m["genre_id"] == "skill_sets" or m["genre_id"] == "books": raise ManifestError(f"genre_id {m['genre_id']!r} not in genres.yaml")
    ss = m.get("skill_set", m["genre_id"])
    if ss not in (g.get("skill_sets") or {}): raise ManifestError(f"skill_set {ss!r} not in genres.yaml skill_sets")
    if book and not os.path.exists(os.path.join(book, m["style_profile"])): raise ManifestError(f"style_profile {m['style_profile']} missing")
    if book and os.path.basename(os.path.normpath(book)) != m["id"]: raise ManifestError(f"id {m['id']!r} != book dir name")
    return True
def get(m, key, default=None):
    d = {"soft_max": 3, "max_attempts": 3}; return m.get(key, d.get(key, default))
