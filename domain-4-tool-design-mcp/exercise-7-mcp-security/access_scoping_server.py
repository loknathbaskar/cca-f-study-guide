"""
access_scoping_server.py — Domain 4, Concept 7: access scoping. A tool
meant to read files from within one sandboxed directory, but with two
implementations: a naive one vulnerable to path traversal, and a
hardened one that properly enforces containment.

SETUP: a `sandbox/` directory contains files the tool is MEANT to
expose. A `secret.txt` file OUTSIDE the sandbox directory represents
something the tool should never be able to reach.
"""

import os
from mcp.server.fastmcp import FastMCP

mcp = FastMCP("AccessScopingDemo")

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
SANDBOX_DIR = os.path.join(BASE_DIR, "sandbox")


@mcp.tool()
def read_file_naive(filename: str) -> str:
    """Read a file from the sandbox directory. (VULNERABLE: no path containment check.)"""
    # THE BUG: naive string concatenation. "../secret.txt" escapes the
    # sandbox directory entirely, and os.path.join happily allows it —
    # join() does NOT sanitize ".." components.
    path = os.path.join(SANDBOX_DIR, filename)
    try:
        with open(path) as f:
            return f.read()
    except FileNotFoundError:
        return f"File not found: {filename}"
    except Exception as e:
        return f"Error: {e}"


@mcp.tool()
def read_file_hardened(filename: str) -> str:
    """Read a file from the sandbox directory. (HARDENED: enforces real containment.)"""
    # THE FIX: resolve the ACTUAL final path (following any ".." segments)
    # and verify it's still inside SANDBOX_DIR before opening anything.
    requested_path = os.path.realpath(os.path.join(SANDBOX_DIR, filename))
    sandbox_real = os.path.realpath(SANDBOX_DIR)
    if not requested_path.startswith(sandbox_real + os.sep) and requested_path != sandbox_real:
        return f"BLOCKED: '{filename}' resolves outside the sandboxed directory. Access denied."
    try:
        with open(requested_path) as f:
            return f.read()
    except FileNotFoundError:
        return f"File not found: {filename}"
    except Exception as e:
        return f"Error: {e}"


if __name__ == "__main__":
    mcp.run()
