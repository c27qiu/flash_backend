import logging
import uvicorn
from fastapi.middleware.cors import CORSMiddleware
from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from websocke.socketManager import WebSocketManager
import json
import argparse

parser = argparse.ArgumentParser()
parser.add_argument("-p", "--port", default=8000, type=int)
args = parser.parse_args()


logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("FastAPI app")

app = FastAPI()

# Adding the CORS middleware to the app
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

socket_manager = WebSocketManager()


@app.websocket("/api/v1/ws/{room_id}/{user_id}")
async def websocket_endpoint(websocket: WebSocket, room_id: str, user_id: int, user_type: str):
    await socket_manager.add_user_to_room(room_id, websocket, user_type)
    try:
        while True:
            data = await websocket.receive_text()
            message = json.loads(data)
            print('got message! ', message)
            # if message['type'] == 'change_detected' and user_type == 'cv_model':
            #     await socket_manager.broadcast_to_room(room_id, data, user_type='gym_manager')
            # elif message['type'] == 'change_approved' and user_type == 'gym_manager':
            #     await socket_manager.broadcast_to_room(room_id, data)
            # elif message['type'] == 'change_approved' and user_type == 'regular_user':
            #     await socket_manager.broadcast_to_user(user_id, data)

    except WebSocketDisconnect:
        await socket_manager.remove_user_from_room(room_id, websocket)

# @app.websocket("/api/v1/ws/{room_id}/{user_id}")
# async def websocket_endpoint(websocket: WebSocket, room_id: str, user_id: int):
#     await socket_manager.add_user_to_room(room_id, websocket)
#     # message = {
#     #     "user_id": user_id,
#     #     "room_id": room_id,
#     #     "message": f"User {user_id} connected to room - {room_id}"
#     # }
#     # await socket_manager.broadcast_to_room(room_id, json.dumps(message))
#     try:
#         while True:
#             data = await websocket.receive_text()
#             message = {
#                 "user_id": user_id,
#                 "room_id": room_id,
#                 "message": data
#             }
#             await socket_manager.broadcast_to_room(room_id, json.dumps(message))

#     except WebSocketDisconnect:
#         await socket_manager.remove_user_from_room(room_id, websocket)

#         message = {
#             "user_id": user_id,
#             "room_id": room_id,
#             "message": f"User {user_id} disconnected from room - {room_id}"
#         }
#         await socket_manager.broadcast_to_room(room_id, json.dumps(message))


if __name__ == "__main__":
    uvicorn.run("main:app", host="127.0.0.1", port=args.port, reload=True)