# fastapi-mcp-server

A Model Context Protocol (MCP) server that connects AI coding assistants directly to your FastAPI applications, APIRouters, and Pydantic models.

Functions as a **Full-Stack Context Bridge**—allowing AI in your IDE to inspect local Python files or live backend deployments, generate 100% accurate TypeScript interfaces and Zod schemas, scaffold typed API clients, and discover backend routes without hallucinations or stale documentation.

---

## Why this exists

When AI assistants write frontend hooks, API clients, or backend tests, they often guess request shapes, parameter names, and route paths based on incomplete file views or outdated training data.

`fastapi-mcp-server` solves this by giving AI assistants native inspection tools:

1. **Dual-Mode Introspection:** Inspects local `.py` files directly from disk (no running `uvicorn` required) **or** fetches live schemas from deployed staging/production URLs (`https://api.example.com/openapi.json` or `http://localhost:8000/docs`).
2. **Instant TypeScript & Zod Generation:** Converts Pydantic models and OpenAPI schemas into strict, copy-paste ready TypeScript `interface`s and Zod validation schemas with full typing, nullability, and JSDoc comments.
3. **Standalone Router & Sub-Module Support:** Introspects full applications (`main:app`) as well as standalone `APIRouter` files (`routers.users:router`) and factory functions.
4. **Project Auto-Discovery:** Scans backend repositories using AST analysis to catalog every FastAPI app, router, and Pydantic model automatically.
5. **Cross-Repository Context:** Frontend developers working in a separate repository (e.g. Next.js/React) can point their IDE's MCP client to the backend project directory to inspect backend types while writing frontend code.

---

## Installation & Quickstart

### Using `uvx` (Recommended — no installation needed)

```bash
uvx fastapi-mcp-server
```

### Using `pip`

```bash
pip install fastapi-mcp-server
```

### Running from source

```bash
git clone https://github.com/username/fastapi-mcp-server.git
cd fastapi-mcp-server
uv sync
uv run fastapi-mcp-server
```

---

## Editor & Client Configuration

### Zed IDE

Add to your Zed `settings.json` (`Ctrl + ,` or `Cmd + ,`):

```json
{
  "context_servers": {
    "fastapi-mcp-server": {
      "command": {
        "path": "uvx",
        "args": ["fastapi-mcp-server"]
      }
    }
  }
}
```

_For local workspace development without publishing:_

```json
{
  "context_servers": {
    "fastapi-mcp-server": {
      "command": {
        "path": "uv",
        "args": [
          "run",
          "--directory",
          "/path/to/fastapi-mcp-server",
          "fastapi-mcp-server"
        ]
      }
    }
  }
}
```

### Cursor

Go to **Cursor Settings** > **Features** > **MCP Servers** > **+ Add New MCP Server**:

- **Name:** `fastapi-mcp-server`
- **Type:** `command`
- **Command:** `uvx fastapi-mcp-server`

### VS Code (with MCP / Copilot)

Add to your VS Code user or workspace settings (`settings.json`):

```json
{
  "mcp": {
    "servers": {
      "fastapi-mcp-server": {
        "command": "uvx",
        "args": ["fastapi-mcp-server"]
      }
    }
  }
}
```

### Claude Desktop

Add to your `claude_desktop_config.json`:

- **macOS:** `~/Library/Application Support/Claude/claude_desktop_config.json`
- **Windows:** `%APPDATA%\Claude\claude_desktop_config.json`

```json
{
  "mcpServers": {
    "fastapi-mcp-server": {
      "command": "uvx",
      "args": ["fastapi-mcp-server"]
    }
  }
}
```

---

## Available MCP Tools

### 1. `get_openapi_schema`

Extracts the complete OpenAPI JSON schema from a local FastAPI app, standalone `APIRouter`, factory function, or live deployed HTTP URL.

- `app_path` _(str, required)_: Import target (e.g. `"main:app"`, `"routers.users:router"`, `"src/api.py:app"`) or live URL (`"https://api.example.com/openapi.json"`, `"http://localhost:8000/docs"`).
- `project_dir` _(str, optional)_: Path to the backend project root.

### 2. `get_pydantic_schema`

Extracts the JSON Schema from any Pydantic `BaseModel` class (supporting both Pydantic v2 and v1).

- `model_path` _(str, required)_: Import target (e.g. `"models.user:UserProfile"`, `"src/schemas.py:Item"`).
- `project_dir` _(str, optional)_: Path to the backend project root.

### 3. `list_registered_routes`

Returns a structured catalog of registered routes, HTTP methods, operation IDs, summaries, and tags from an app, standalone router, or live URL.

- `app_path` _(str, required)_: Target app, router, or URL.
- `project_dir` _(str, optional)_: Path to the backend project root.

### 4. `get_typescript_definition`

Directly generates strict TypeScript interfaces and types from a Pydantic model, local app, or remote OpenAPI URL.

- `target` _(str, required)_: Model target (e.g. `"models.user:UserProfile"`), app target (`"main:app"`), or live URL.
- `project_dir` _(str, optional)_: Path to the backend project root.

### 5. `get_zod_schema`

Generates client-side Zod validation schemas (`z.object({...})`) and inferred TypeScript types from a Pydantic model or OpenAPI target.

- `target` _(str, required)_: Model target, app target, or live URL.
- `project_dir` _(str, optional)_: Path to the backend project root.

### 6. `discover_fastapi_project`

Scans a backend project directory using zero-execution AST parsing to catalog all FastAPI instances, APIRouters, and Pydantic models.

- `project_dir` _(str, optional)_: Path to the project directory to scan.

---

## Error Handling

All tools return clean structured JSON dictionaries rather than raising unhandled exceptions or crashing the MCP connection:

```json
{
  "error": "ModuleNotFoundError",
  "detail": "Failed to import module 'src.main'. Searched in sys.path: [...]"
}
```

---

## Development & Testing

```bash
# Clone the repository
git clone https://github.com/username/fastapi-mcp-server.git
cd fastapi-mcp-server

# Install dependencies
uv sync

# Run tests
uv run pytest

# Run type checker and linter
uv run basedpyright
uv run ruff check src tests
```

---

## License

MIT License. See [LICENSE](LICENSE) for details.
