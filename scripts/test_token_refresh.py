#!/usr/bin/env python3
"""
Test OAuth Token Refresh Flow

This script tests the token refresh endpoint to verify that
refresh tokens can be used to obtain new access tokens.
"""
import asyncio
import json
import httpx


async def test_refresh_flow():
    """Test the OAuth token refresh flow."""
    base_url = "http://localhost:8000"

    # Credentials from OAuth flow
    # TODO: Replace these with your own test credentials from completing the OAuth flow
    session_id = "your-session-id-here"
    refresh_token = "your-refresh-token-here"

    print("=" * 60)
    print("Testing OAuth Token Refresh Flow")
    print("=" * 60)
    print()

    async with httpx.AsyncClient() as client:
        # Test: Refresh access token
        print("Step 1: Refreshing access token...")
        print(f"   Session ID: {session_id}")
        print()

        refresh_request = {
            "session_id": session_id,
            "refresh_token": refresh_token
        }

        response = await client.post(
            f"{base_url}/oauth/refresh",
            json=refresh_request
        )

        if response.status_code == 200:
            result = response.json()
            print("✅ Token refreshed successfully!")
            print()
            print(f"   New Access Token: {result['access_token'][:50]}...")
            print(f"   Refresh Token: {result['refresh_token'][:50]}...")
            print(f"   Expires In: {result['expires_in']} seconds ({result['expires_in'] // 60} minutes)")
            print(f"   Token Type: {result['token_type']}")
            print()

            new_access_token = result['access_token']
            new_session_id = result['session_id']

            # Test 2: Verify new access token works with MCP tools
            print("Step 2: Testing new access token with MCP tools...")
            headers = {
                "Authorization": f"Bearer {new_session_id}",
                "Content-Type": "application/json"
            }

            # Create a test task
            create_request = {
                "name": "task_create",
                "params": {
                    "title": "Test with refreshed token",
                    "project": "OAuth Testing",
                    "priority": 3
                }
            }

            mcp_response = await client.post(
                f"{base_url}/mcp/tools/call",
                json=create_request,
                headers=headers
            )

            if mcp_response.status_code == 200:
                mcp_result = mcp_response.json()
                task_data = json.loads(mcp_result["content"][0]["text"])
                print(f"✅ MCP tool works with refreshed token!")
                print(f"   Created task: {task_data['title']} (ID: {task_data['id']})")
            else:
                print(f"❌ MCP tool failed: {mcp_response.status_code}")
                print(f"   Response: {mcp_response.text}")

        else:
            print(f"❌ Token refresh failed: {response.status_code}")
            print(f"   Response: {response.text}")
            return

        print()
        print("=" * 60)
        print("Token refresh test completed successfully!")
        print("=" * 60)


if __name__ == "__main__":
    asyncio.run(test_refresh_flow())
