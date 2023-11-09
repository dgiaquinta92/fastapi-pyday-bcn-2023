from typing import Optional

from fastapi import FastAPI, HTTPException

app = FastAPI()


@app.get("/")
async def root():
    return {"message": "Hello World"}

@app.get("/items/{item_id}")
def read_item(item_id: int, q: Optional[str] = None):
    return {"item_id": item_id, "q": q}



# Lista de clientes inversos permitidos
allowed_clients = {
    "client1": "192.168.1.2",
    "client2": "192.168.1.3"
}

@app.post("/send_command/{client_id}")
async def send_command_to_client(client_id: str, command: str):
    if client_id not in allowed_clients:
        raise HTTPException(status_code=403, detail="Cliente no permitido")
    
    client_ip = allowed_clients[client_id]
    response = send_command_to_inverse_client(client_ip, command)
    return response

def send_command_to_inverse_client(client_ip, command):
    # Aquí usar la biblioteca adecuada para enviar comandos a clientes inversos
    # Por ejemplo, la librería 'socket' o 'httpx' (dependiendo de la implementación)
    # y manejar la comunicación con el cliente inverso
    pass
