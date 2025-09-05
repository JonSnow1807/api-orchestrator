#!/usr/bin/env python3
"""
WebSocket Test Client for API Orchestrator
Tests real-time communication with the server
"""

import pytest
import asyncio
import websockets
import json
from datetime import datetime

@pytest.mark.integration
@pytest.mark.asyncio
async def test_websocket():
    """Test WebSocket connection and messaging"""
    
    uri = "ws://localhost:8000/ws"
    
    print("🔌 Connecting to WebSocket...")
    print(f"   URI: {uri}")
    print("-" * 50)
    
    try:
        async with websockets.connect(uri) as websocket:
            print("✅ Connected successfully!")
            
            # Listen for initial connection message
            message = await websocket.recv()
            data = json.loads(message)
            print(f"\n📨 Received: {json.dumps(data, indent=2)}")
            
            # Test 1: Send ping
            print("\n🏓 Sending ping...")
            await websocket.send(json.dumps({"type": "ping"}))
            
            # Wait for pong
            response = await websocket.recv()
            data = json.loads(response)
            print(f"📨 Received: {data}")
            
            # Test 2: Get status
            print("\n📊 Requesting status...")
            await websocket.send(json.dumps({"type": "get_status"}))
            
            # Wait for status
            response = await websocket.recv()
            data = json.loads(response)
            print(f"📨 Received: {json.dumps(data, indent=2)}")
            
            # Keep connection open for a bit to see any broadcasts
            print("\n👂 Listening for broadcasts (10 seconds)...")
            
            # Listen with timeout
            try:
                for i in range(10):
                    response = await asyncio.wait_for(websocket.recv(), timeout=1.0)
                    data = json.loads(response)
                    print(f"📨 Broadcast received: {json.dumps(data, indent=2)}")
            except asyncio.TimeoutError:
                print("⏱️  No more messages (timeout)")
            
            print("\n✨ WebSocket test completed successfully!")
            
    except Exception as e:
        print(f"❌ Error: {e}")
        return False
    
    return True

async def test_orchestration_with_websocket():
    """Test orchestration while monitoring WebSocket"""
    
    import aiohttp
    
    print("\n" + "=" * 50)
    print("🚀 Testing Orchestration with WebSocket Monitoring")
    print("=" * 50)
    
    # Connect to WebSocket first
    uri = "ws://localhost:8000/ws"
    
    async with websockets.connect(uri) as websocket:
        print("✅ WebSocket connected")
        
        # Clear initial message
        await websocket.recv()
        
        # Create a task to listen for messages
        async def listen_for_messages():
            try:
                while True:
                    message = await websocket.recv()
                    data = json.loads(message)
                    timestamp = datetime.now().strftime("%H:%M:%S")
                    print(f"[{timestamp}] 📨 {data.get('type', 'unknown')}: {data.get('message', json.dumps(data))}")
            except:
                pass
        
        # Start listening in background
        listen_task = asyncio.create_task(listen_for_messages())
        
        # Trigger orchestration via HTTP
        print("\n🎯 Triggering orchestration via API...")
        
        async with aiohttp.ClientSession() as session:
            payload = {
                "source_type": "directory",
                "source_path": "src"
            }
            
            async with session.post(
                "http://localhost:8000/api/orchestrate",
                json=payload
            ) as response:
                result = await response.json()
                print(f"✅ Orchestration started: {result}")
        
        # Wait to see WebSocket messages
        print("\n👂 Monitoring progress via WebSocket...")
        await asyncio.sleep(5)
        
        # Cancel listener
        listen_task.cancel()
        
    print("\n✨ Test completed!")

async def main():
    """Run all tests"""
    
    print("🧪 API Orchestrator WebSocket Test Suite")
    print("=" * 50)
    
    # Test 1: Basic WebSocket
    success = await test_websocket()
    
    if success:
        # Test 2: Orchestration with monitoring
        await test_orchestration_with_websocket()
    
    print("\n🎉 All tests completed!")

if __name__ == "__main__":
    # Install required package if needed
    try:
        import websockets
        import aiohttp
    except ImportError:
        print("Installing required packages...")
        import subprocess
        subprocess.check_call(["pip", "install", "websockets", "aiohttp"])
        print("Packages installed. Please run the script again.")
        exit(0)
    
    asyncio.run(main())
