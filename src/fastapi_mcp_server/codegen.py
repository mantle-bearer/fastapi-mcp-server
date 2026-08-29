"""Code generation utilities for converting JSON Schema and Pydantic models to TypeScript and Zod."""

import json
from typing import Any


def _resolve_type_name(ref: str) -> str:
    """Extract type name from a JSON Schema $ref string (e.g. '#/$defs/User' -> 'User')."""
    return ref.split("/")[-1]


def _format_jsdoc(description: str | None, indent: str = "") -> str:
    """Format an optional description into a JSDoc comment block."""
    if not description:
        return ""
    clean_desc = description.strip().replace("*/", "* /")
    return f"{indent}/** {clean_desc} */\n"


def _json_type_to_ts(prop_schema: dict[str, Any], defs: dict[str, Any]) -> str:
    """Convert a single JSON Schema property definition to a TypeScript type string."""
    if "$ref" in prop_schema:
        return _resolve_type_name(str(prop_schema["$ref"]))

    if "enum" in prop_schema:
        enum_vals = prop_schema["enum"]
        return " | ".join(json.dumps(val) for val in enum_vals)

    if "anyOf" in prop_schema or "oneOf" in prop_schema:
        union_list = prop_schema.get("anyOf") or prop_schema.get("oneOf") or []
        types: list[str] = []
        for sub in union_list:
            if isinstance(sub, dict):
                if sub.get("type") == "null":
                    types.append("null")
                else:
                    types.append(_json_type_to_ts(sub, defs))
        return " | ".join(dict.fromkeys(types)) if types else "any"

    prop_type = prop_schema.get("type")

    if prop_type == "string":
        return "string"
    elif prop_type in ("integer", "number"):
        return "number"
    elif prop_type == "boolean":
        return "boolean"
    elif prop_type == "null":
        return "null"
    elif prop_type == "array":
        items = prop_schema.get("items")
        if isinstance(items, dict):
            item_ts = _json_type_to_ts(items, defs)
            if " | " in item_ts and not item_ts.startswith("("):
                return f"({item_ts})[]"
            return f"{item_ts}[]"
        return "any[]"
    elif prop_type == "object":
        if "properties" in prop_schema:
            inner_props = prop_schema.get("properties", {})
            required_set = set(prop_schema.get("required", []))
            lines: list[str] = ["{"]
            for k, v in inner_props.items():
                if isinstance(v, dict):
                    opt = "" if k in required_set else "?"
                    lines.append(f"  {k}{opt}: {_json_type_to_ts(v, defs)};")
            lines.append("}")
            return " ".join(lines)
        if "additionalProperties" in prop_schema:
            add_props = prop_schema.get("additionalProperties")
            if isinstance(add_props, dict):
                val_type = _json_type_to_ts(add_props, defs)
                return f"Record<string, {val_type}>"
            return "Record<string, any>"
        return "Record<string, any>"

    return "any"


def json_schema_to_typescript(
    schema: dict[str, Any], root_name: str | None = None
) -> str:
    """
    Convert a JSON Schema (or Pydantic JSON Schema) into idiomatic TypeScript interface definitions.
    Recursively renders nested $defs and components.
    """
    if "error" in schema:
        return (
            f"// Error generating TypeScript: {schema.get('detail', 'Unknown error')}"
        )

    name = root_name or schema.get("title", "GeneratedModel")
    defs = schema.get("$defs") or schema.get("definitions") or {}
    rendered_types: list[str] = []

    # Render $defs / nested models first
    for def_name, def_schema in defs.items():
        if isinstance(def_schema, dict) and def_name != name:
            rendered_types.append(
                _render_single_ts_interface(def_name, def_schema, defs)
            )

    # Render root model
    rendered_types.append(_render_single_ts_interface(name, schema, defs))

    return "\n\n".join(filter(None, rendered_types))


def _render_single_ts_interface(
    name: str, schema: dict[str, Any], defs: dict[str, Any]
) -> str:
    """Render a single TypeScript interface or type alias."""
    desc = schema.get("description")
    jsdoc = _format_jsdoc(desc)

    if "enum" in schema:
        enum_vals = schema["enum"]
        type_def = " | ".join(json.dumps(val) for val in enum_vals)
        return f"{jsdoc}export type {name} = {type_def};"

    props = schema.get("properties", {})
    required_set = set(schema.get("required", []))

    lines: list[str] = []
    lines.append(f"{jsdoc}export interface {name} {{")

    if not props:
        lines.append("  [key: string]: any;")
    else:
        for prop_name, prop_data in props.items():
            if isinstance(prop_data, dict):
                prop_desc = prop_data.get("description")
                prop_jsdoc = _format_jsdoc(prop_desc, indent="  ")
                is_req = prop_name in required_set
                opt_mark = "" if is_req else "?"
                ts_type = _json_type_to_ts(prop_data, defs)
                if prop_jsdoc:
                    lines.append(prop_jsdoc.rstrip())
                lines.append(f"  {prop_name}{opt_mark}: {ts_type};")

    lines.append("}")
    return "\n".join(lines)


def _json_type_to_zod(prop_schema: dict[str, Any], defs: dict[str, Any]) -> str:
    """Convert a single JSON Schema property definition to a Zod schema call string."""
    if "$ref" in prop_schema:
        ref_name = _resolve_type_name(str(prop_schema["$ref"]))
        return f"{ref_name}Schema"

    if "enum" in prop_schema:
        enum_vals = [json.dumps(v) for v in prop_schema["enum"]]
        return f"z.enum([{', '.join(enum_vals)}])"

    if "anyOf" in prop_schema or "oneOf" in prop_schema:
        union_list = prop_schema.get("anyOf") or prop_schema.get("oneOf") or []
        zod_types: list[str] = []
        is_nullable = False
        for sub in union_list:
            if isinstance(sub, dict):
                if sub.get("type") == "null":
                    is_nullable = True
                else:
                    zod_types.append(_json_type_to_zod(sub, defs))

        base = (
            zod_types[0]
            if len(zod_types) == 1
            else f"z.union([{', '.join(zod_types)}])"
            if zod_types
            else "z.any()"
        )
        return f"{base}.nullable()" if is_nullable else base

    prop_type = prop_schema.get("type")

    if prop_type == "string":
        zod = "z.string()"
        if "minLength" in prop_schema:
            zod += f".min({prop_schema['minLength']})"
        if "maxLength" in prop_schema:
            zod += f".max({prop_schema['maxLength']})"
        if prop_schema.get("format") == "email":
            zod += ".email()"
        return zod
    elif prop_type == "integer":
        zod = "z.number().int()"
        if "minimum" in prop_schema:
            zod += f".min({prop_schema['minimum']})"
        if "maximum" in prop_schema:
            zod += f".max({prop_schema['maximum']})"
        return zod
    elif prop_type == "number":
        zod = "z.number()"
        if "minimum" in prop_schema:
            zod += f".min({prop_schema['minimum']})"
        if "maximum" in prop_schema:
            zod += f".max({prop_schema['maximum']})"
        return zod
    elif prop_type == "boolean":
        return "z.boolean()"
    elif prop_type == "array":
        items = prop_schema.get("items")
        item_zod = (
            _json_type_to_zod(items, defs) if isinstance(items, dict) else "z.any()"
        )
        return f"z.array({item_zod})"
    elif prop_type == "object":
        if "properties" in prop_schema:
            inner_props = prop_schema.get("properties", {})
            required_set = set(prop_schema.get("required", []))
            lines: list[str] = ["z.object({"]
            for k, v in inner_props.items():
                if isinstance(v, dict):
                    inner_zod = _json_type_to_zod(v, defs)
                    if k not in required_set:
                        inner_zod += ".optional()"
                    lines.append(f"  {k}: {inner_zod},")
            lines.append("})")
            return "\n".join(lines)
        return "z.record(z.string(), z.any())"

    return "z.any()"


def json_schema_to_zod(schema: dict[str, Any], root_name: str | None = None) -> str:
    """
    Convert a JSON Schema (or Pydantic JSON Schema) into Zod schema definitions with imports.
    """
    if "error" in schema:
        return (
            f"// Error generating Zod schema: {schema.get('detail', 'Unknown error')}"
        )

    name = root_name or schema.get("title", "GeneratedModel")
    defs = schema.get("$defs") or schema.get("definitions") or {}
    rendered_schemas: list[str] = []

    # Render $defs / nested schemas first
    for def_name, def_schema in defs.items():
        if isinstance(def_schema, dict) and def_name != name:
            rendered_schemas.append(
                _render_single_zod_schema(def_name, def_schema, defs)
            )

    # Render root schema
    rendered_schemas.append(_render_single_zod_schema(name, schema, defs))

    header = 'import { z } from "zod";\n\n'
    return header + "\n\n".join(filter(None, rendered_schemas))


def _render_single_zod_schema(
    name: str, schema: dict[str, Any], defs: dict[str, Any]
) -> str:
    """Render a single Zod schema and its TypeScript inferred type."""
    schema_var = f"{name}Schema"
    props = schema.get("properties", {})
    required_set = set(schema.get("required", []))

    lines: list[str] = []
    lines.append(f"export const {schema_var} = z.object({{")

    for prop_name, prop_data in props.items():
        if isinstance(prop_data, dict):
            zod_type = _json_type_to_zod(prop_data, defs)
            if prop_name not in required_set:
                zod_type += ".optional()"
            desc = prop_data.get("description")
            if desc:
                clean_desc = json.dumps(desc.strip())
                zod_type += f".describe({clean_desc})"
            lines.append(f"  {prop_name}: {zod_type},")

    lines.append("});")
    lines.append(f"\nexport type {name} = z.infer<typeof {schema_var}>;")

    return "\n".join(lines)
