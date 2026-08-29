"""Tests for fastapi-mcp-server inspector, tools, and cross-platform path handling."""

from pathlib import Path

import pytest
from fastapi import FastAPI
from pydantic import BaseModel

from fastapi_mcp_server.inspector import (
    extract_openapi,
    extract_pydantic_schema,
    extract_routes,
    normalize_import_path,
    resolve_target,
)
from fastapi_mcp_server.server import (
    get_openapi_schema,
    get_pydantic_schema,
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
        normalize_import_path("tests.sample_app", str(BASE_DIR))


def test_normalize_import_path_nonexistent_file():
    with pytest.raises(FileNotFoundError, match="File not found"):
        normalize_import_path("tests/nonexistent_file.py:app", str(BASE_DIR))


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
        resolve_target("tests.sample_app:NonExistent", str(BASE_DIR))


def test_resolve_target_nonexistent_module():
    with pytest.raises(ModuleNotFoundError, match="Failed to import module"):
        resolve_target("completely_fake_module_name:app", str(BASE_DIR))


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
    # Verify GET /users/
    get_users_route = next(
        r for r in routes if r["path"] == "/users/" and "GET" in r["methods"]
    )
    assert get_users_route["operation_id"] == "list_users"
    assert get_users_route["tags"] == ["Users"]

    # Verify WebSocket route
    assert "/ws" in paths
    assert paths["/ws"]["type"] == "WebSocket"


def test_extract_routes_from_factory():
    routes = extract_routes("tests.sample_app:make_app", str(BASE_DIR))
    assert isinstance(routes, list)
    paths = {r["path"]: r for r in routes}
    assert "/factory-route" in paths


def test_server_tools_direct_call():
    openapi_res = get_openapi_schema("tests.sample_app:app", str(BASE_DIR))
    assert "openapi" in openapi_res

    pydantic_res = get_pydantic_schema("tests.sample_app:Item", str(BASE_DIR))
    assert "price" in pydantic_res["properties"]

    routes_res = list_registered_routes("tests.sample_app:app", str(BASE_DIR))
    assert isinstance(routes_res, list)
    assert len(routes_res) >= 3
