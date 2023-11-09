from fastapi import FastAPI, Depends, Request, HTTPException
from fastapi.responses import FileResponse, HTMLResponse, StreamingResponse, JSONResponse, RedirectResponse
from starlette.responses import JSONResponse, Response
from fastapi.encoders import jsonable_encoder
from fastapi.security import HTTPBasicCredentials
from fastapi.middleware.cors import CORSMiddleware

import pandas as pd
import io
import requests
import urllib3
urllib3.disable_warnings()

from security import security
from procedures import procedures
from models import models as md
from routers import routers_v1
from logs import logs_middleware


app = FastAPI()


tags_metadata = [
    {
        "name": "DRINKS",
        "description": "Request de Obtención de CSV DRINKS",
        "externalDocs": {
            "description": "Link",
            "url": "https://fastapi.tiangolo.com/",
        },
    },
    {
        "name": "TEST",
        "description": "Request de prueba",
        "externalDocs": {
            "description": "Link a Dashboard o algo",
            "url": "https://fastapi.tiangolo.com/",
        },
    }    
]
description = "API de Prueba"



app = FastAPI(title="API - PyDay2023", version="1.0", 
              description = description, openapi_tags=tags_metadata)

app.include_router(routers_v1.router, prefix="/api/v1")

app.add_middleware(CORSMiddleware, allow_origins=["*"], 
                   allow_credentials=True, allow_methods=["*"], 
                   allow_headers=["*"])
app.add_middleware(logs_middleware.RequestLoggingMiddleware)




@app.get("/drinks", response_class=FileResponse, tags=["DRINKS"])
async def get_drinks(Alcoholic: bool):
    """
    Obtener las bebidas con/sin **Alcohol**:
    
    **Alcoholic:** True si quiere las bebidas con Alcohol
    """
    if Alcoholic:
        url = "https://www.thecocktaildb.com/api/json/v1/1/filter.php?a=Alcoholic"
    else:
        url = "https://www.thecocktaildb.com/api/json/v1/1/filter.php?a=Non_Alcoholic"
    r = requests.get(url)
    response = {}
    for drink in r.json()["drinks"]:
        response[drink["strDrink"]] = {}
        response[drink["strDrink"]]["name"] = drink["strDrink"]
        response[drink["strDrink"]]["id"] = drink["idDrink"]

    # Convertir el JSON a DataFrame
    df = pd.DataFrame(response.values())
    file_name = 'drinks.csv'
    # Guardar el DataFrame como CSV
    df.to_csv(file_name, index=False)

    return FileResponse(file_name, filename=file_name)


@app.get("/drinks_json", response_class=JSONResponse, tags=["DRINKS"])
async def get_drinks(Alcoholic: bool):
    """
    Obtener las bebidas con/sin **Alcohol**:
    
    **Alcoholic:** True si quiere las bebidas con Alcohol
    """
    if Alcoholic:
        url = "https://www.thecocktaildb.com/api/json/v1/1/filter.php?a=Alcoholic"
    else:
        url = "https://www.thecocktaildb.com/api/json/v1/1/filter.php?a=Non_Alcoholic"
    r = requests.get(url)
    response = {}
    for drink in r.json()["drinks"]:
        response[drink["strDrink"]] = {}
        response[drink["strDrink"]]["name"] = drink["strDrink"]
        response[drink["strDrink"]]["id"] = drink["idDrink"]
        

    return response
    

@app.get("/get-test", response_class=JSONResponse, tags=["TEST"])
async def get_test(name: md.Names):
    response = {}
    response["result"] = "Hello " + name
    return response


@app.get("/get/{name}/saludo", response_class=JSONResponse, tags=["TEST"])
async def get_test(name: md.Names):
    response = {}
    response["result"] = "Hello " + name
    return response


@app.get("/error_response", response_class=JSONResponse, tags=["Error"])
async def error_response(name: str):
    if name != "Diego":
        raise HTTPException(status_code=401, detail="Este usuario no tiene permiso")
    else:
        response = {}
        response["result"] = "Hello " + name
        return response


@app.get("/html_response", response_class=HTMLResponse, tags=["HTML"])
async def html_response(name: md.Names):

    html_file_path = "content/template.html"
    # Abre el html y lo guarda en html_content
    with open(html_file_path, "r") as html_file:
        html_content = html_file.read()
    html_content = html_content.format(name=name.value)
    return HTMLResponse(content=html_content, status_code=200)


@app.get("/video_response", response_class=StreamingResponse, tags=["VIDEO"])
async def video_response():
    video_path = "content/video.mp4"

    # Abre el archivo de video en modo de lectura binaria
    video_file = open(video_path, "rb")

    # Lee los datos del video en un búfer
    video_data = video_file.read()

    # Cierra el archivo de video
    video_file.close()

    # Utiliza StreamingResponse para transmitir los datos del video como respuesta
    return StreamingResponse(io.BytesIO(video_data), media_type="video/mp4")


@app.get("/redirect_response/hello_lucas", response_class=RedirectResponse, tags=["Redirect"])
async def redirect_response():  
    return RedirectResponse("/html_response?name=Lucas")




@app.post("/admin/users/create_api_user", tags=["ADMIN"])
async def create_api_user(request: Request, response: Response, user: md.UserApi, credentials: HTTPBasicCredentials = Depends(security.security_basic)):
    security.verify_credentials_basic(credentials)
    access_token = security.create_access_token_login(data={"sub": credentials.username}, expires_delta=security.ACCESS_TOKEN_EXPIRE_MINUTES_TIME)
    token = jsonable_encoder(access_token)
    response.set_cookie(key="Authorization", value=f"Bearer {token}")
    response.set_cookie(key="detail", value=f"Creacion de API-USER {user.username}")
    respuesta = procedures.add_user_to_db(user)
    if not respuesta:
        raise HTTPException(status_code=400, detail="Ha ocurrido un error")
    return respuesta


@app.delete("/admin/users/delete_user", tags=["ADMIN"])
async def get_users(response: Response, username: str, credentials: HTTPBasicCredentials = Depends(security.security_basic)):
    security.verify_credentials_basic(credentials)
    access_token = security.create_access_token_login(data={"sub": credentials.username}, expires_delta=security.ACCESS_TOKEN_EXPIRE_MINUTES_TIME)
    token = jsonable_encoder(access_token)
    response.set_cookie(key="Authorization", value=f"Bearer {token}")
    response.set_cookie(key="detail", value=f"Se ha borrado el usuario {username}")
    respuesta = procedures.delete_api_user(username)
    if not respuesta:
        response.set_cookie(key="detail", value=f"Se intentó borrar el usuario {username}, pero hubo un error")
        raise HTTPException(status_code=400, detail="Ha ocurrido un error")
    else:
        response.set_cookie(key="detail", value=f"Se ha borrado el usuario {username}")
    return respuesta



@app.get("/admin/users/get_users", tags=["ADMIN"])
async def get_users(response: Response, credentials: HTTPBasicCredentials = Depends(security.security_basic)):
    security.verify_credentials_basic(credentials)
    access_token = security.create_access_token_login(data={"sub": credentials.username}, expires_delta=security.ACCESS_TOKEN_EXPIRE_MINUTES_TIME)
    token = jsonable_encoder(access_token)
    response.set_cookie(key="Authorization", value=f"Bearer {token}")
    response.set_cookie(key="detail", value=f"Se ha consultado el listado de usuarios")
    respuesta = procedures.get_users()
    if not respuesta:
        raise HTTPException(status_code=400, detail="Ha ocurrido un error")
    return respuesta



@app.get("/wordcloud", response_class=HTMLResponse, tags=["HTML"])
async def html_response():
    html_file_path = "content/wordcloud.html"
    # Abre el html y lo guarda en html_content
    with open(html_file_path, "r") as html_file:
        html_content = html_file.read()
    return HTMLResponse(content=html_content, status_code=200)


#if __name__ == "__main__":
#    uvicorn.run(app, host="0.0.0.0", port=8000)
