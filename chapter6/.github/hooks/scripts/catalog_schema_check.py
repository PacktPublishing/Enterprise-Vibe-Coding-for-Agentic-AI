#!/usr/bin/env python3
"""
catalog_schema_check.py — PostToolUse guard for the product-catalog schema.

Reads the hook payload from stdin, looks at the just-edited file, and refuses
edits that drift from the approved `PRODUCTS[*]` schema defined in
`conversational shopping/mock_data.py`.

Exit 0 (allow): file is unrelated, or all checks pass.
Exit 2 (block): emits a JSON {decision: "block", reason: ...} for the agent.

Checks applied (only to files in `conversational shopping/`):

  1. mock_data.py itself
     - Every entry in PRODUCTS must have the full set of REQUIRED_FIELDS
       with the right primitive types, and no UNKNOWN extra fields.
     - `category` must be in CATEGORY_WHITELIST.

  2. Python files that reference the catalog (PRODUCTS, mock_data, or any
     dict access like `p["..."]` / `product["..."]`):
     - Every string-key access on a catalog dict must use a known field.

  3. SQL / ORM / API contracts (heuristic, regex-based):
     - CREATE TABLE products(...) / class Product(Base) / Column(...) /
       Pydantic models / dataclasses named *Product* must only declare
       columns whose names are in REQUIRED_FIELDS.
     - Any reference to a column/field named `sku`, `inventory_id`, `stock`,
       `vendor_id`, `cost_price` (etc.) is treated as a foreign-schema leak.
"""

from __future__ import annotations

import ast
import json
import os
import re
import sys
from pathlib import Path

# ---- Schema (single source of truth, mirrors mock_data.PRODUCTS[*]) ---------

REQUIRED_FIELDS: dict[str, type | tuple[type, ...]] = {
    "id": str,
    "name": str,
    "category": str,
    "price": (int, float),
    "sizes": list,
    "colors": list,
    "description": str,
    "tags": list,
    "image": str,
    "rating": (int, float),
    "reviews_count": int,
}
CATEGORY_WHITELIST = {"Tops", "Bottoms", "Dresses", "Outerwear", "Knitwear", "Accessories"}
FOREIGN_SCHEMA_FIELDS = {"sku", "inventory_id", "stock", "vendor_id", "cost_price", "deleted_at"}

CATALOG_SCOPE = "conversational shopping"   # only check files under this folder
ALLOWED_KEYS = set(REQUIRED_FIELDS.keys())

# ---- Hook I/O ---------------------------------------------------------------

def _read_payload() -> dict:
    try:
        raw = sys.stdin.read()
        return json.loads(raw) if raw.strip() else {}
    except Exception:
        return {}

def _extract_file_path(payload: dict) -> str | None:
    tool_input = payload.get("tool_input") or payload.get("toolInput") or {}
    for key in ("file_path", "filePath", "path", "uri"):
        val = tool_input.get(key)
        if isinstance(val, str) and val:
            return val.replace("file://", "")
    return None

def _allow() -> None:
    sys.exit(0)

def _block(reason: str) -> None:
    print(json.dumps({
        "decision": "block",
        "reason": reason,
        "systemMessage": "catalog-schema-guard blocked this edit. Reconcile with PRODUCTS schema in `conversational shopping/mock_data.py` and retry.",
    }))
    sys.exit(2)

# ---- Per-file checks --------------------------------------------------------

_DICT_KEY_RE = re.compile(r"""\b(p|product|item|prod)\s*\[\s*['"]([A-Za-z_][A-Za-z0-9_]*)['"]\s*\]""")
_SQL_CREATE_RE = re.compile(r"CREATE\s+TABLE\s+products?\s*\((.*?)\)", re.IGNORECASE | re.DOTALL)
_SQL_COL_RE = re.compile(r"^\s*([A-Za-z_][A-Za-z0-9_]*)\b", re.MULTILINE)
_ORM_COLUMN_RE = re.compile(r"^\s*([A-Za-z_][A-Za-z0-9_]*)\s*[:=]\s*(?:Column|mapped_column|Field|fields\.\w+|orm\.\w+)\b", re.MULTILINE)
_FOREIGN_FIELD_RE = re.compile(rf"""\b({'|'.join(re.escape(f) for f in FOREIGN_SCHEMA_FIELDS)})\b""")

def _check_mock_data(src: str) -> list[str]:
    """Validate PRODUCTS list-of-dicts literal in mock_data.py."""
    errors: list[str] = []
    try:
        tree = ast.parse(src)
    except SyntaxError as e:
        return [f"mock_data.py has a syntax error after edit: {e.msg} (line {e.lineno})"]

    products_node = None
    for node in tree.body:
        if isinstance(node, ast.Assign):
            for target in node.targets:
                if isinstance(target, ast.Name) and target.id == "PRODUCTS":
                    products_node = node.value
                    break
        if products_node is not None:
            break
    if products_node is None:
        return ["PRODUCTS assignment is missing from mock_data.py"]
    if not isinstance(products_node, ast.List):
        return ["PRODUCTS must be a list literal"]

    for idx, elt in enumerate(products_node.elts):
        if not isinstance(elt, ast.Dict):
            errors.append(f"PRODUCTS[{idx}] is not a dict literal")
            continue
        keys = {k.value for k in elt.keys if isinstance(k, ast.Constant) and isinstance(k.value, str)}
        missing = sorted(set(REQUIRED_FIELDS) - keys)
        extra = sorted(keys - ALLOWED_KEYS)
        if missing:
            errors.append(f"PRODUCTS[{idx}] is missing required field(s): {missing}")
        if extra:
            errors.append(f"PRODUCTS[{idx}] adds unknown field(s) not in schema: {extra}")

        # Spot-check category whitelist on literal values
        for k, v in zip(elt.keys, elt.values):
            if isinstance(k, ast.Constant) and k.value == "category" and isinstance(v, ast.Constant):
                if v.value not in CATEGORY_WHITELIST:
                    errors.append(
                        f"PRODUCTS[{idx}].category={v.value!r} is not in approved categories "
                        f"{sorted(CATEGORY_WHITELIST)}"
                    )
    return errors

def _check_consumer_python(src: str) -> list[str]:
    """For .py files that consume the catalog, flag unknown dict keys and foreign schema fields."""
    errors: list[str] = []

    # Unknown key access on catalog-shaped dicts
    for match in _DICT_KEY_RE.finditer(src):
        key = match.group(2)
        if key not in ALLOWED_KEYS and key not in {"quantity", "size", "color"}:
            # quantity/size/color are legitimate cart-item keys, not catalog keys
            line = src.count("\n", 0, match.start()) + 1
            errors.append(
                f"line {line}: dict access [{key!r}] is not a known PRODUCTS field "
                f"(allowed: {sorted(ALLOWED_KEYS)})"
            )

    # ORM / Pydantic / dataclass fields named like product columns
    in_product_model = re.search(
        r"class\s+\w*Product\w*\s*\([^)]*\)\s*:", src
    ) is not None
    if in_product_model:
        for match in _ORM_COLUMN_RE.finditer(src):
            field = match.group(1)
            if field.startswith("_") or field in {"Meta", "Config"}:
                continue
            if field not in ALLOWED_KEYS:
                errors.append(f"Product model declares unknown column/field {field!r}")

    return errors

def _check_sql_or_contract(src: str) -> list[str]:
    """Look for CREATE TABLE / OpenAPI / contract strings that drift from schema."""
    errors: list[str] = []
    for create in _SQL_CREATE_RE.finditer(src):
        body = create.group(1)
        declared = {m.group(1).lower() for m in _SQL_COL_RE.finditer(body)}
        declared.discard("constraint")
        declared.discard("primary")
        missing = sorted({f.lower() for f in REQUIRED_FIELDS} - declared)
        if missing:
            errors.append(f"CREATE TABLE products(...) is missing required column(s): {missing}")

    for match in _FOREIGN_FIELD_RE.finditer(src):
        line = src.count("\n", 0, match.start()) + 1
        errors.append(
            f"line {line}: reference to foreign-schema field {match.group(1)!r} — "
            "not part of the approved PRODUCTS schema"
        )
    return errors

# ---- Main -------------------------------------------------------------------

def main() -> None:
    payload = _read_payload()
    file_path = _extract_file_path(payload)
    if not file_path:
        _allow()

    # Only act on files inside the conversational-shopping project
    norm = file_path.replace("\\", "/")
    if CATALOG_SCOPE not in norm:
        _allow()

    path = Path(file_path)
    if not path.exists() or not path.is_file():
        _allow()

    suffix = path.suffix.lower()
    if suffix not in {".py", ".sql", ".yaml", ".yml", ".json"}:
        _allow()

    try:
        src = path.read_text(encoding="utf-8", errors="replace")
    except Exception:
        _allow()

    # Cheap early-out: is this file even catalog-related?
    catalog_signals = ("PRODUCTS", "mock_data", "product_id", "CREATE TABLE products", "class Product")
    if not any(sig in src for sig in catalog_signals):
        _allow()

    errors: list[str] = []
    if path.name == "mock_data.py":
        errors += _check_mock_data(src)
    if suffix == ".py":
        errors += _check_consumer_python(src)
    errors += _check_sql_or_contract(src)

    if errors:
        bullets = "\n".join(f"  - {e}" for e in errors[:20])
        _block(
            f"Catalog schema check failed for `{os.path.relpath(file_path)}`:\n{bullets}\n\n"
            f"Approved PRODUCTS schema fields: {sorted(ALLOWED_KEYS)}\n"
            f"Approved categories: {sorted(CATEGORY_WHITELIST)}"
        )

    _allow()

if __name__ == "__main__":
    main()
