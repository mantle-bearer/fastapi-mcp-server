"""Tests for fastapi-mcp-server inspector, tools, codegen, discovery, and cross-platform path handling."""

import json
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest
from fastapi import FastAPI
from pydantic import BaseModel

from fastapi_mcp_server.inspector import (
    extract_openapi,
    extract_pydantic_schema,
    extract_routes,
    extract_typescript,
    extract_zod,
    normalize_import_path,
    resolve_target,
)
from fastapi_mcp_server.scanner import discover_project
from fastapi_mcp_server.server import (
    discover_fastapi_project,
    get_openapi_schema,
    get_pydantic_schema,
    get_typescript_definition,
    get_zod_schema,
    list_registered_routes,
)

BASE_DIR = Path(__file__).resolve().parent.parent


def test_normalize_import_path_dot_notation():
    module, attr, sys_dir = normalize_import_path("tests.sample_app:app", str(BASE_DIR))
    assert module == "tests.sample_app"
    assert attr == "app"
    assert sys_dir == BASE_DIR


def test_normalize_import_path_file_notation():
    module, attr, sys_dir = normalize_import_path(
        "tests/sample_app.py:app", str(BASE_DIR)
    )
    assert module == "sample_app"
    assert attr == "app"
    assert sys_dir == BASE_DIR / "tests"


def test_normalize_import_path_windows_slash():
    module, attr, sys_dir = normalize_import_path(
        "tests\\sample_app.py:app", str(BASE_DIR)
    )
    assert module == "sample_app"
    assert attr == "app"
    assert sys_dir == BASE_DIR / "tests"


def test_normalize_import_path_invalid_format():
    with pytest.raises(ValueError, match="Invalid target format"):
        _ = normalize_import_path("tests.sample_app", str(BASE_DIR))


def test_normalize_import_path_nonexistent_file():
    with pytest.raises(FileNotFoundError, match="File not found"):
        _ = normalize_import_path("tests/nonexistent_file.py:app", str(BASE_DIR))


def test_resolve_target_app():
    app = resolve_target("tests.sample_app:app", str(BASE_DIR))
    assert isinstance(app, FastAPI)
    assert app.title == "Sample Test App"


def test_resolve_target_model():
    model = resolve_target("tests.sample_app:User", str(BASE_DIR))
    assert issubclass(model, BaseModel)
    assert model.__name__ == "User"


def test_resolve_target_nonexistent_attribute():
    with pytest.raises(AttributeError, match="has no attribute"):
        _ = resolve_target("tests.sample_app:NonExistent", str(BASE_DIR))


def test_resolve_target_nonexistent_module():
    with pytest.raises(ModuleNotFoundError, match="Failed to import module"):
        _ = resolve_target("completely_fake_module_name:app", str(BASE_DIR))


def test_extract_openapi():
    schema = extract_openapi("tests.sample_app:app", str(BASE_DIR))
    assert "openapi" in schema
    assert schema["info"]["title"] == "Sample Test App"
    assert "/health" in schema["paths"]
    assert "/users/" in schema["paths"]


def test_extract_openapi_from_factory():
    schema = extract_openapi("tests.sample_app:make_app", str(BASE_DIR))
    assert "openapi" in schema
    assert schema["info"]["title"] == "Factory Created App"
    assert "/factory-route" in schema["paths"]


def test_extract_openapi_from_standalone_router():
    schema = extract_openapi("tests.sample_app:router", str(BASE_DIR))
    assert "openapi" in schema
    assert "/users/" in schema["paths"]


def test_extract_openapi_invalid_target():
    res = extract_openapi("tests.sample_app:User", str(BASE_DIR))
    assert "error" in res
    assert res["error"] == "TypeError"


def test_extract_pydantic_schema():
    schema = extract_pydantic_schema("tests.sample_app:User", str(BASE_DIR))
    assert "properties" in schema
    assert "username" in schema["properties"]
    assert "email" in schema["properties"]
    assert "items" in schema["properties"]


def test_extract_pydantic_schema_invalid_target():
    res = extract_pydantic_schema("tests.sample_app:app", str(BASE_DIR))
    assert "error" in res
    assert res["error"] == "TypeError"


def test_extract_routes():
    routes = extract_routes("tests.sample_app:app", str(BASE_DIR))
    assert isinstance(routes, list)

    paths = {r["path"]: r for r in routes}
    assert "/health" in paths
    assert "GET" in paths["/health"]["methods"]
    assert paths["/health"]["summary"] == "Health check endpoint"

    assert "/users/" in paths
    get_users_route = next(
        r for r in routes if r["path"] == "/users/" and "GET" in r["methods"]
    )
    assert get_users_route["operation_id"] == "list_users"
    assert get_users_route["tags"] == ["Users"]

    assert "/ws" in paths
    assert paths["/ws"]["type"] == "WebSocket"


def test_extract_routes_from_standalone_router():
    routes = extract_routes("tests.sample_app:router", str(BASE_DIR))
    assert isinstance(routes, list)
    paths = {r["path"]: r for r in routes}
    assert "/users/" in paths


def test_extract_routes_from_factory():
    routes = extract_routes("tests.sample_app:make_app", str(BASE_DIR))
    assert isinstance(routes, list)
    paths = {r["path"]: r for r in routes}
    assert "/factory-route" in paths


def test_extract_typescript_from_model():
    ts_code = extract_typescript("tests.sample_app:User", str(BASE_DIR))
    assert isinstance(ts_code, str)
    assert "export interface User {" in ts_code
    assert "username: string;" in ts_code
    assert "email: string;" in ts_code
    assert "items" in ts_code


def test_extract_zod_from_model():
    zod_code = extract_zod("tests.sample_app:Item", str(BASE_DIR))
    assert isinstance(zod_code, str)
    assert 'import { z } from "zod";' in zod_code
    assert "export const ItemSchema = z.object({" in zod_code
    assert "name: z.string()" in zod_code
    assert "price: z.number()" in zod_code


def test_discover_fastapi_project():
    discovery = discover_project(str(BASE_DIR))
    assert "apps" in discovery
    assert "routers" in discovery
    assert "models" in discovery
    assert len(discovery["apps"]) >= 1
    assert any(m["class"] == "User" for m in discovery["models"])


def test_extract_openapi_from_remote_url():
    fake_openapi = {
        "openapi": "3.1.0",
        "info": {"title": "Remote Test API", "version": "1.0.0"},
        "paths": {
            "/remote-users": {
                "get": {
                    "operationId": "get_remote_users",
                    "summary": "Get Remote Users",
                    "tags": ["Remote"],
                }
            }
        },
    }

    mock_resp = MagicMock()
    mock_resp.read.return_value = json.dumps(fake_openapi).encode("utf-8")
    mock_resp.__enter__.return_value = mock_resp

    with patch("urllib.request.urlopen", return_value=mock_resp):
        schema = extract_openapi("https://api.example.com/openapi.json")
        assert schema["info"]["title"] == "Remote Test API"

        routes = extract_routes("https://api.example.com/openapi.json")
        assert isinstance(routes, list)
        assert len(routes) == 1
        assert routes[0]["path"] == "/remote-users"
        assert routes[0]["operation_id"] == "get_remote_users"


def test_server_tools_direct_call():
    openapi_res = get_openapi_schema("tests.sample_app:app", str(BASE_DIR))
    assert "openapi" in openapi_res

    pydantic_res = get_pydantic_schema("tests.sample_app:Item", str(BASE_DIR))
    assert "price" in pydantic_res["properties"]

    routes_res = list_registered_routes("tests.sample_app:app", str(BASE_DIR))
    assert isinstance(routes_res, list)
    assert len(routes_res) >= 3

    ts_res = get_typescript_definition("tests.sample_app:User", str(BASE_DIR))
    assert "export interface User" in ts_res

    zod_res = get_zod_schema("tests.sample_app:Item", str(BASE_DIR))
    assert "export const ItemSchema" in zod_res

    disc_res = discover_fastapi_project(str(BASE_DIR))
    assert disc_res["summary"]["total_models"] >= 1
