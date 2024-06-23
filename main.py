from fastapi import FastAPI, Request, Response, status
from fastapi.middleware.cors import CORSMiddleware
import uvicorn
import requests, json
from base64 import b64decode
from dotenv import dotenv_values
config = dotenv_values(".env")

app = FastAPI()
app.add_middleware(CORSMiddleware, allow_origins=[config.get("VERCEL_URL")], allow_credentials=True, allow_methods=["GET", "POST", "OPTIONS"], allow_headers=["*"])

passwd = "aaa"

async def get_ips():
    url = config.get("PFSENSE_URL") + "/list/gamuxers"
    r = requests.get(url, verify=False, auth=(config.get("PFSENSE_KEY"), config.get("PFSENSE_SECRET")))

    if r.status_code == 200:
        response = json.loads(r.text)

        ips = [row.get("ip") for row in response.get("rows")]
        return ips
    else:
        raise ConnectionError("Failed to connect to pfSense!")
    
@app.get("/gamux/api", status_code=200)
async def is_allowed(request: Request, response: Response):
    try:
        ips = await get_ips()
        if request.client.host in ips:
            response.status_code = status.HTTP_200_OK
            return {"status": "Authorized!"}
        else:
            response.status_code = status.HTTP_401_UNAUTHORIZED
            return {"status": "Unauthorized!"}
    except ConnectionError as e:
        response.status_code = status.HTTP_500_INTERNAL_SERVER_ERROR
        return {"status": e.strerror}

        
@app.post("/gamux/api")
async def add_allowed(request: Request, response: Response):
    try:
        auth = request.headers.get("Authorization").split()[1]
    except:
        response.status_code = status.HTTP_401_UNAUTHORIZED
        return {"status": "Invalid Credentials!"}
    
    if passwd != auth:
        response.status_code = status.HTTP_401_UNAUTHORIZED
        return {"status": "Invalid Credentials!"}
    
    try:
        url = config.get("PFSENSE_URL") + "/add/gamuxers"
        body = {"address": request.client.host}
        r = requests.post(url, verify=False, auth=(config.get("PFSENSE_KEY"), config.get("PFSENSE_SECRET")), data=body)

        if r.status_code == 200:
            response.status_code = status.HTTP_201_CREATED
            return {"status": "Added Successfully!"}
        
        response.status_code = status.HTTP_500_INTERNAL_SERVER_ERROR
        return {"status": "Failed to add IP!"}
    except ConnectionError as e:
        response.status_code = status.HTTP_500_INTERNAL_SERVER_ERROR
        return {"status": e.strerror}

if __name__ == "__main__":
    uvicorn.run("main:app", host="127.0.0.1", port=8443, reload=True, ssl_keyfile="key.pem", ssl_certfile="cert.pem")