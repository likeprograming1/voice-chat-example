from fastapi import FastAPI, WebSocket
from fastapi.responses import HTMLResponse

app = FastAPI()

# 클라이언트들을 저장할 WebSocket 연결 리스트
clients = []

@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    await websocket.accept()
    clients.append(websocket)
    try:
        while True:
            # 클라이언트로부터 메시지를 받음
            data = await websocket.receive_text()
            # 다른 모든 클라이언트에 메시지 브로드캐스트
            for client in clients:
                if client != websocket:
                    await client.send_text(data)
    except Exception as e:
        print(f"Connection error: {e}")
    finally:
        # 연결 종료 시 클라이언트 제거
        clients.remove(websocket)
