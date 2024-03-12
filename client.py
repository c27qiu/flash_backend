import asyncio
import websockets
import json

async def connect_to_server(room_id, user_id):
    uri = f"ws://127.0.0.1/api/v1/ws/{room_id}/{user_id}"
    async with websockets.connect(uri) as websocket:
        # Send a message to the server
        message = {"type": "change_detected"}
        await websocket.send(json.dumps(message))

        # Receive a message from the server
        response = await websocket.recv()
        print(response)

asyncio.run(connect_to_server(1, 1))