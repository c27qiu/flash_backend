from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.responses import HTMLResponse
from websocke.socketManager import WebSocketManager
import json
from fastapi.middleware.cors import CORSMiddleware
import boto3
from botocore.credentials import Credentials
import base64

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # You might want to restrict this to specific origins in a production environment
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

s3 = boto3.client('s3')

socket_manager = WebSocketManager()

html = """
<!DOCTYPE html>
<html>
    <head>
        <title>Chat</title>
    </head>
    <body>
        <h1>WebSocket Chat</h1>
        <h2>Your ID: <span id="ws-id"></span></h2>
        <form action="" onsubmit="sendMessage(event)">
            <input type="text" id="messageText" autocomplete="off"/>
            <button>Send</button>
        </form>
        <ul id='messages'>
        </ul>
        <script>
            var client_id = Date.now()
            document.querySelector("#ws-id").textContent = client_id;
            var ws = new WebSocket(`ws://localhost:8000/ws/${client_id}`);
            ws.onmessage = function(event) {
                var messages = document.getElementById('messages')
                var message = document.createElement('li')
                var content = document.createTextNode(event.data)
                message.appendChild(content)
                messages.appendChild(message)
            };
            function sendMessage(event) {
                var input = document.getElementById("messageText")
                ws.send(input.value)
                input.value = ''
                event.preventDefault()
            }
        </script>
    </body>
</html>
"""


class ConnectionManager:
    def __init__(self):
        self.active_connections: list[WebSocket] = []

    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        self.active_connections.append(websocket)

    def disconnect(self, websocket: WebSocket):
        self.active_connections.remove(websocket)

    async def send_personal_message(self, message: str, websocket: WebSocket):
        await websocket.send_text(message)

    async def broadcast(self, message: str):
        for connection in self.active_connections:
            await connection.send_text(message)


manager = ConnectionManager()


@app.get("/")
async def get():
    return HTMLResponse(html)

@app.websocket("/wse/{client_id}")
async def websocket_endpoint(websocket: WebSocket, client_id: int):
    await manager.connect(websocket)
    try:
        while True:
            data = await websocket.receive_text()
            await manager.send_personal_message(f"You wrote: {data}", websocket)
            await manager.broadcast(f"Client #{client_id} says: {data}")
            
            # s3_url = json.loads(data)
            # wall_name = s3_url["wall_name"]
            # image_path = s3_url["image_path"]
            
            # try:
            #     bucket, key = "fydp-photos", image_path
            #     print('bucket, key from sara ', bucket, key)
            #     # Retrieve image data from S3
            #     response = s3.get_object(Bucket=bucket, Key=key)
            #     # print("response from sara ", response)
            #     image_data = response['Body'].read()
            #     base64_image = base64.b64encode(image_data).decode('utf-8')
            #     await websocket.send_text(base64_image)
            #     # print("image_data from sara ", image_data)
            #     # Send image data to the client
            #     # await websocket.send_bytes(image_data)
            #     await websocket.send_text("You sent an image data!")
            # except Exception as e:
            #     print(f"Error retrieving image from S3: {e}")
    except WebSocketDisconnect:
        manager.disconnect(websocket)
        await manager.broadcast(f"Client #{client_id} left the chat")


@app.websocket("/ws/{client_id}")
async def websocket_endpoint(websocket: WebSocket, client_id: int):
    await socket_manager.add_user_to_room(client_id, websocket)
    # await manager.connect(websocket)
    message = {
        "user_id": client_id,
        "message": f"User {client_id} connected"
    }
    await websocket.send_text(f"You wrote: {json.dumps(message)}")
    await socket_manager.broadcast_to_room(client_id, json.dumps(message))
    
    try:
        while True:
            data = await websocket.receive_text()
            await websocket.send_text(f'You sent an image data!{data}')

            s3_url = data
            
            try:
                bucket, key = s3_url.split("//")[1].split("/", 1)
                # Retrieve image data from S3
                response = s3.get_object(Bucket=bucket, Key=key)
                image_data = response['Body'].read()
                # Send image data to the client
                await websocket.send_bytes(image_data)
                await websocket.send_text("You sent an image data!")
            except Exception as e:
                print(f"Error retrieving image from S3: {e}")
                
            # message = json.loads(data)
            # await socket_manager.broadcast_to_room(client_id, data)
            # print('got message! ', message)
            # await manager.send_personal_message(f"You wrote: {data}", websocket)
            # await manager.broadcast(f"Client #{client_id} says: {data}")
    except WebSocketDisconnect:
        manager.disconnect(websocket)
        await manager.broadcast(f"Client #{client_id} left the chat")
        
if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)