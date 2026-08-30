"""
hr_server.py — Domain 4, Concept 5: A second, independent MCP server, for
testing multi-server client aggregation and tool-name collision handling.

DELIBERATE COLLISION: this server exposes a tool literally named
`get_status`, same as order_server.py's `get_status` — but scoped to
employee PTO status, completely different meaning and arguments. This
simulates a very real production scenario: two independently-developed
MCP servers, neither aware of the other, happening to choose the same
generic tool name for their own domain.
"""

from mcp.server.fastmcp import FastMCP

mcp = FastMCP("HRService")

EMPLOYEES = {
    "EMP-1001": {"name": "Alex Chen", "pto_balance_days": 12, "pending_request": True},
    "EMP-2002": {"name": "Priya Patel", "pto_balance_days": 3, "pending_request": False},
}


@mcp.tool()
def get_pto_balance(employee_id: str) -> str:
    """Get an employee's remaining PTO balance in days."""
    emp = EMPLOYEES.get(employee_id)
    if not emp:
        return f"No employee found with ID {employee_id}."
    return f"{employee_id} ({emp['name']}): {emp['pto_balance_days']} PTO days remaining."


@mcp.tool()
def get_status(employee_id: str) -> str:
    """Get the status of an employee's pending PTO request (generic name, employee-scoped).
    NOTE: deliberately named identically to order_server.py's get_status —
    this is the collision this exercise is designed to test."""
    emp = EMPLOYEES.get(employee_id)
    if not emp:
        return f"No employee found with ID {employee_id}."
    status = "pending approval" if emp["pending_request"] else "no pending request"
    return f"[HR STATUS] {employee_id}: {status}"


@mcp.resource("employees://all")
def all_employees() -> str:
    """A read-only snapshot of all employees, as context."""
    lines = [f"{eid}: {data['name']}, {data['pto_balance_days']} PTO days" for eid, data in EMPLOYEES.items()]
    return "\n".join(lines)


if __name__ == "__main__":
    mcp.run()
