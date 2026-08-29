# Technical Specification: fastapi-mcp-server

**Project Name:** `fastapi-mcp-server`  
**Version:** `0.1.0`  
**Core Purpose:** Model Context Protocol (MCP) server functioning as a Full-Stack Context Bridge for FastAPI, APIRouters, live OpenAPI endpoints, and Pydantic models.

---

## 1. Architecture Overview

```
┌────────────────────────────────────────────────────────┐
│                   AI Assistant / MCP Client            │
│          (Zed, Cursor, VS Code, Claude Desktop)       │
└───────────────────────────┬────────────────────────────┘
                            │ stdio (JSON-RPC)
┌───────────────────────────▼────────────────────────────┐
│                  fastapi-mcp-server                    │
│                                                        │
│  ┌───────────────────────┐  ┌───────────────────────┐  │
│  │   inspector.py        │  │   codegen.py          │  │
│  │   • dynamic import    │  │   • JSON -> TypeScript│  │
│  │   • router wrapper    │  │   • JSON -> Zod       │  │
│  │   • remote URL fetch  │  └───────────────────────┘  │
│  └───────────────────────┘  ┌───────────────────────┐  │
│                             │   scanner.py          │  │
│                             │   • AST auto-discovery│  │
│                             └───────────────────────┘  │
└───────────────────────────┬────────────────────────────┘
                            │
       ┌────────────────────┴────────────────────┐
       ▼                                         ▼
┌───────────────────────────┐         ┌───────────────────────────┐
│ Local Python Files (.py)  │         │ Live / Deployed OpenAPI   │
│ • FastAPI instances       │         │ • http://localhost:8000   │
│ • APIRouters              │         │ • https://staging/api     │
│ • Pydantic BaseModels     │         │ • /docs & /openapi.json   │
└───────────────────────────┘         └───────────────────────────┘
```

---

## 2. Implemented Tools

1. **`get_openapi_schema`**: Extracts complete OpenAPI 3.1.0/3.0.x schema from FastAPI apps, standalone APIRouters, factories, or remote HTTP/HTTPS URLs.
2. **`get_pydantic_schema`**: Extracts JSON Schema from Pydantic v1 & v2 `BaseModel` classes.
3. **`list_registered_routes`**: Recursively parses route trees, methods, operation IDs, summaries, tags, WebSockets, and mounts from local apps/routers or remote URLs.
4. **`get_typescript_definition`**: Converts Pydantic models or OpenAPI schemas into typed TypeScript interfaces and type aliases with JSDoc comments.
5. **`get_zod_schema`**: Converts Pydantic models or OpenAPI schemas into client-side Zod validation schemas.
6. **`discover_fastapi_project`**: Performs AST-based static scanning of a project directory to discover all apps, routers, and models without executing code.

---

## 3. Supported Platforms & Environments

- **Operating Systems:** Windows 10/11, macOS, Linux.
- **Python Compatibility:** Python >= 3.10.
- **Package Manager:** `uv` with `hatchling` build backend.
- **Protocol:** MCP SDK (JSON-RPC over stdio with UTF-8 encoding).
