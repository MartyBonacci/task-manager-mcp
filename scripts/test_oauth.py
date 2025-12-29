#!/usr/bin/env python3
"""
OAuth 2.1 Flow Test Script

This script tests the complete OAuth flow with real Google credentials.
"""
import httpx
import asyncio


async def test_oauth_flow():
    """Test the OAuth authorization flow."""
    base_url = "http://localhost:8000"

    print("=" * 60)
    print("OAuth 2.1 Flow Test with Real Google Credentials")
    print("=" * 60)
    print()

    # Step 1: Get authorization URL
    print("Step 1: Getting authorization URL...")
    async with httpx.AsyncClient(follow_redirects=False) as client:
        response = await client.get(f"{base_url}/oauth/authorize")

        # Handle redirect (307/302) - the endpoint redirects directly to Google
        if response.status_code in [307, 302]:
            auth_url = response.headers.get("Location")
            if not auth_url:
                print(f"❌ No redirect location found in response")
                return
            print(f"✅ Authorization URL retrieved successfully (via redirect)")
        elif response.status_code == 200:
            data = response.json()
            auth_url = data.get("authorization_url")
            if not auth_url:
                print(f"❌ No authorization URL in response: {data}")
                return
            print(f"✅ Authorization URL retrieved successfully")
        else:
            print(f"❌ Failed to get authorization URL: {response.status_code}")
            print(f"Response: {response.text}")
            return
        print()
        print("=" * 60)
        print("NEXT STEPS:")
        print("=" * 60)
        print()
        print("1. Open this URL in your browser:")
        print()
        print(f"   {auth_url}")
        print()
        print("2. Log in with your Google account")
        print("   (Use the email you added as a test user)")
        print()
        print("3. Click 'Continue' to authorize the app")
        print()
        print("4. You'll be redirected to:")
        print(f"   {base_url}/oauth/callback?code=...")
        print()
        print("5. Look for the success message on that page!")
        print()
        print("=" * 60)
        print()
        print("After completing the OAuth flow, you can test MCP tools")
        print("with your authenticated session.")
        print()


if __name__ == "__main__":
    asyncio.run(test_oauth_flow())
