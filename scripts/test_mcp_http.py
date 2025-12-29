#!/usr/bin/env python3
"""
Test MCP Tools via HTTP with OAuth Session

This script tests MCP tool calls through the HTTP API using a valid session_id from OAuth.
"""
import asyncio
import json
import httpx


async def test_mcp_tools():
    """Test MCP tools with authenticated session."""
    base_url = "http://localhost:8000"

    # Session ID from OAuth flow
    session_id = "7iil97Nj4jMe0u-LyEmj2bC_HprR4XIc9k1ahD_Ehxo"

    # Headers with session authentication
    headers = {
        "Authorization": f"Bearer {session_id}",
        "Content-Type": "application/json"
    }

    print("=" * 60)
    print("Testing MCP Tools with Authenticated Session")
    print("=" * 60)
    print()

    async with httpx.AsyncClient() as client:
        # Test 1: Create a task
        print("Test 1: Creating a task...")
        create_request = {
            "name": "task_create",
            "params": {
                "title": "Test OAuth integration",
                "project": "Task Manager MCP",
                "priority": 4,
                "energy": "medium",
                "time_estimate": "30min"
            }
        }

        response = await client.post(
            f"{base_url}/mcp/tools/call",
            json=create_request,
            headers=headers
        )

        if response.status_code == 200:
            result = response.json()
            task_data = json.loads(result["content"][0]["text"])
            print(f"✅ Task created successfully!")
            print(f"   Task ID: {task_data['id']}")
            print(f"   Title: {task_data['title']}")
            print(f"   Project: {task_data['project']}")
            task_id = task_data['id']
        else:
            print(f"❌ Failed to create task: {response.status_code}")
            print(f"   Response: {response.text}")
            return

        print()

        # Test 2: List tasks
        print("Test 2: Listing tasks...")
        list_request = {
            "name": "task_list",
            "params": {
                "show_completed": False,
                "limit": 10
            }
        }

        response = await client.post(
            f"{base_url}/mcp/tools/call",
            json=list_request,
            headers=headers
        )

        if response.status_code == 200:
            result = response.json()
            tasks = json.loads(result["content"][0]["text"])
            print(f"✅ Listed {len(tasks)} task(s)")
            for task in tasks:
                print(f"   - {task['title']} (ID: {task['id']})")
        else:
            print(f"❌ Failed to list tasks: {response.status_code}")
            print(f"   Response: {response.text}")

        print()

        # Test 3: Get specific task
        print(f"Test 3: Getting task {task_id}...")
        get_request = {
            "name": "task_get",
            "params": {
                "task_id": task_id
            }
        }

        response = await client.post(
            f"{base_url}/mcp/tools/call",
            json=get_request,
            headers=headers
        )

        if response.status_code == 200:
            result = response.json()
            task = json.loads(result["content"][0]["text"])
            print(f"✅ Retrieved task successfully")
            print(f"   Title: {task['title']}")
            print(f"   Status: {'Completed' if task['completed'] else 'Pending'}")
        else:
            print(f"❌ Failed to get task: {response.status_code}")
            print(f"   Response: {response.text}")

        print()

        # Test 4: Update task
        print(f"Test 4: Updating task {task_id}...")
        update_request = {
            "name": "task_update",
            "params": {
                "task_id": task_id,
                "priority": 5,
                "notes": "Updated via MCP tools test"
            }
        }

        response = await client.post(
            f"{base_url}/mcp/tools/call",
            json=update_request,
            headers=headers
        )

        if response.status_code == 200:
            result = response.json()
            task = json.loads(result["content"][0]["text"])
            print(f"✅ Task updated successfully")
            print(f"   Priority: {task['priority']} (changed to Critical)")
            print(f"   Notes: {task['notes']}")
        else:
            print(f"❌ Failed to update task: {response.status_code}")
            print(f"   Response: {response.text}")

        print()

        # Test 5: Get task stats
        print("Test 5: Getting task statistics...")
        stats_request = {
            "name": "task_stats",
            "params": {}
        }

        response = await client.post(
            f"{base_url}/mcp/tools/call",
            json=stats_request,
            headers=headers
        )

        if response.status_code == 200:
            result = response.json()
            stats = json.loads(result["content"][0]["text"])
            print(f"✅ Statistics retrieved")
            print(f"   Total tasks: {stats['total_tasks']}")
            print(f"   Completed: {stats['completed_tasks']}")
            print(f"   Incomplete: {stats['incomplete_tasks']}")
            print(f"   Completion rate: {stats['completion_rate']:.1f}%")
        else:
            print(f"❌ Failed to get stats: {response.status_code}")
            print(f"   Response: {response.text}")

        print()

        # Test 6: Complete task
        print(f"Test 6: Completing task {task_id}...")
        complete_request = {
            "name": "task_complete",
            "params": {
                "task_id": task_id
            }
        }

        response = await client.post(
            f"{base_url}/mcp/tools/call",
            json=complete_request,
            headers=headers
        )

        if response.status_code == 200:
            result = response.json()
            task = json.loads(result["content"][0]["text"])
            print(f"✅ Task completed successfully")
            print(f"   Completed: {task['completed']}")
            print(f"   Completed at: {task['completed_at']}")
        else:
            print(f"❌ Failed to complete task: {response.status_code}")
            print(f"   Response: {response.text}")

        print()
        print("=" * 60)
        print("All MCP tool tests completed!")
        print("=" * 60)


if __name__ == "__main__":
    asyncio.run(test_mcp_tools())
