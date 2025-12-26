#!/usr/bin/env python3
"""
MCP Tools Test CLI

Interactive CLI for testing MCP tools during development.

Usage:
    python scripts/test_mcp_tools.py

This script allows you to interactively test all 8 MCP tools
without running the full server.
"""

import asyncio
import json
import sys
from pathlib import Path

# Add project root to Python path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from sqlalchemy.ext.asyncio import AsyncSession

from app.config.auth import AuthService
from app.db.session import AsyncSessionLocal, init_db
from app.mcp.handlers import TOOL_HANDLERS
from app.mcp.tools import list_tool_names


async def test_tool_interactive() -> None:
    """
    Interactive tool testing session.
    """
    # Initialize database
    await init_db()
    print("✓ Database initialized\n")

    # Get current user
    user_id = AuthService.get_current_user_id()
    print(f"Current User: {user_id}\n")

    # List available tools
    print("Available Tools:")
    tools = list_tool_names()
    for i, tool_name in enumerate(tools, 1):
        print(f"  {i}. {tool_name}")
    print()

    # Interactive loop
    async with AsyncSessionLocal() as session:
        while True:
            print("\nEnter tool name (or 'quit' to exit):")
            tool_name = input("> ").strip()

            if tool_name.lower() in ("quit", "exit", "q"):
                break

            if tool_name not in tools:
                print(f"❌ Unknown tool: {tool_name}")
                continue

            # Get tool handler
            handler = TOOL_HANDLERS.get(tool_name)
            if not handler:
                print(f"❌ Handler not found for: {tool_name}")
                continue

            # Get parameters
            print(f"\nEnter parameters for {tool_name} (JSON format):")
            print("Example: {\"title\": \"Test task\", \"priority\": 4}")
            params_str = input("> ").strip()

            if not params_str:
                params = {}
            else:
                try:
                    params = json.loads(params_str)
                except json.JSONDecodeError as e:
                    print(f"❌ Invalid JSON: {e}")
                    continue

            # Execute tool
            try:
                print(f"\n⏳ Executing {tool_name}...")
                response = await handler(session, user_id, params)

                # Display response
                print(f"\n✓ Response:")
                response_data = json.loads(response.content[0].text)
                print(json.dumps(response_data, indent=2))

            except Exception as e:
                print(f"❌ Error: {e}")


async def quick_test() -> None:
    """
    Quick automated test of common operations.
    """
    # Initialize database
    await init_db()
    print("✓ Database initialized\n")

    user_id = AuthService.get_current_user_id()
    print(f"Testing with user: {user_id}\n")

    async with AsyncSessionLocal() as session:
        # Test 1: Create task
        print("Test 1: Creating task...")
        create_handler = TOOL_HANDLERS["task_create"]
        response = await create_handler(
            session,
            user_id,
            {"title": "Test Task", "priority": 4, "project": "Test Project"},
        )
        task_data = json.loads(response.content[0].text)
        task_id = task_data["id"]
        print(f"✓ Created task ID: {task_id}\n")

        # Test 2: List tasks
        print("Test 2: Listing tasks...")
        list_handler = TOOL_HANDLERS["task_list"]
        response = await list_handler(session, user_id, {})
        tasks = json.loads(response.content[0].text)
        print(f"✓ Found {len(tasks)} tasks\n")

        # Test 3: Get task
        print(f"Test 3: Getting task {task_id}...")
        get_handler = TOOL_HANDLERS["task_get"]
        response = await get_handler(session, user_id, {"task_id": task_id})
        task = json.loads(response.content[0].text)
        print(f"✓ Retrieved: {task['title']}\n")

        # Test 4: Update task
        print(f"Test 4: Updating task {task_id}...")
        update_handler = TOOL_HANDLERS["task_update"]
        response = await update_handler(
            session, user_id, {"task_id": task_id, "priority": 5, "notes": "Updated notes"}
        )
        updated_task = json.loads(response.content[0].text)
        print(f"✓ Updated priority to: {updated_task['priority']}\n")

        # Test 5: Search tasks
        print("Test 5: Searching tasks...")
        search_handler = TOOL_HANDLERS["task_search"]
        response = await search_handler(session, user_id, {"query": "Test"})
        results = json.loads(response.content[0].text)
        print(f"✓ Found {len(results)} matching tasks\n")

        # Test 6: Get stats
        print("Test 6: Getting statistics...")
        stats_handler = TOOL_HANDLERS["task_stats"]
        response = await stats_handler(session, user_id, {})
        stats = json.loads(response.content[0].text)
        print(f"✓ Total tasks: {stats['total_tasks']}")
        print(f"  Completed: {stats['completed_tasks']}")
        print(f"  Completion rate: {stats['completion_rate']}%\n")

        # Test 7: Complete task
        print(f"Test 7: Completing task {task_id}...")
        complete_handler = TOOL_HANDLERS["task_complete"]
        response = await complete_handler(session, user_id, {"task_id": task_id})
        completed_task = json.loads(response.content[0].text)
        print(f"✓ Task completed at: {completed_task['completed_at']}\n")

        # Test 8: Delete task
        print(f"Test 8: Deleting task {task_id}...")
        delete_handler = TOOL_HANDLERS["task_delete"]
        response = await delete_handler(session, user_id, {"task_id": task_id})
        delete_result = json.loads(response.content[0].text)
        print(f"✓ {delete_result['message']}\n")

    print("All tests completed successfully! ✓")


async def main() -> None:
    """
    Main entry point - choose test mode.
    """
    print("Task Manager MCP - Tool Testing CLI")
    print("=" * 40)
    print()
    print("Select mode:")
    print("  1. Quick automated test")
    print("  2. Interactive tool testing")
    print()

    choice = input("Enter choice (1 or 2): ").strip()

    if choice == "1":
        await quick_test()
    elif choice == "2":
        await test_tool_interactive()
    else:
        print("Invalid choice. Exiting.")


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n\nInterrupted by user. Exiting...")
        sys.exit(0)
