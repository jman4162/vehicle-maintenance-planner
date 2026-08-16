import json
import os
import sys
from pathlib import Path

import pytest
from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client


@pytest.fixture
def anyio_backend():
    return "asyncio"


@pytest.mark.anyio
async def test_stdio_mcp_contract_and_guarded_preview(tmp_path):
    root = Path(__file__).parents[1]
    parameters = StdioServerParameters(
        command=sys.executable,
        args=["-m", "vehicle_maintenance", "mcp"],
        cwd=str(root),
        env={
            **os.environ,
            "PYTHONPATH": str(root / "src"),
            "VEHICLE_MAINT_DATA_DIR": str(tmp_path / "private"),
        },
    )
    async with stdio_client(parameters) as (read_stream, write_stream):
        async with ClientSession(read_stream, write_stream) as session:
            await session.initialize()
            listed = await session.list_tools()
            tools = {tool.name: tool for tool in listed.tools}
            assert {
                "vehicle_status",
                "explain_code",
                "local_service_history",
                "invoice_audit",
                "inspect_plan",
                "compare_plan_quotes",
                "break_even",
                "add_reading",
                "import_reviewed_document",
                "record_quote",
                "record_authorization",
                "complete_service_event",
            } <= set(tools)
            assert not {"send_message", "book_service", "contact_provider", "authorize_work"} & set(tools)
            assert tools["break_even"].annotations.readOnlyHint
            assert tools["add_reading"].annotations.readOnlyHint is False
            assert tools["add_reading"].annotations.openWorldHint is False

            calculation = await session.call_tool("break_even", {"dealer_cents": 32801, "alternative_cents": 16000})
            assert not calculation.isError
            value = calculation.structuredContent or json.loads(calculation.content[0].text)
            assert value["savings_cents"] == 16801

            preview = await session.call_tool(
                "add_reading",
                {"payload": {"odometer_miles": 8462, "minder_code": "A67"}},
            )
            assert not preview.isError
            value = preview.structuredContent or json.loads(preview.content[0].text)
            assert not value["commit"]
            assert value["confirmation_token"]
