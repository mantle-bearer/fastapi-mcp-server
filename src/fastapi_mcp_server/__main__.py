"""CLI entrypoint for running the fastapi-mcp-server over standard input/output (stdio)."""

import sys

from fastapi_mcp_server.server import mcp


def main() -> None:
    """Main execution function for the MCP server."""
    # Ensure UTF-8 standard stream encoding across platforms (especially on Windows)
    if sys.platform == "win32":
        reconfigure_stdin = getattr(sys.stdin, "reconfigure", None)
        if callable(reconfigure_stdin):
            reconfigure_stdin(encoding="utf-8")
        reconfigure_stdout = getattr(sys.stdout, "reconfigure", None)
        if callable(reconfigure_stdout):
            reconfigure_stdout(encoding="utf-8")
        reconfigure_stderr = getattr(sys.stderr, "reconfigure", None)
        if callable(reconfigure_stderr):
            reconfigure_stderr(encoding="utf-8")

    # Run the FastMCP server with stdio transport
    mcp.run(transport="stdio")


if __name__ == "__main__":
    main()
