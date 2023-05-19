import os
import logging
import pathlib
import json
import hashlib
import shutil
from typing import Union
from fastapi import FastAPI, Query, Form, File, UploadFile, HTTPException
from fastapi.responses import FileResponse
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI()
logger = logging.getLogger("uvicorn")
logger.level = logging.INFO
images = pathlib.Path(__file__).parent.resolve() / "images"
origins = [ os.environ.get('FRONT_URL', 'http://localhost:3000') ]
app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=False,
    allow_methods=["GET","POST","PUT","DELETE"],
    allow_headers=["*"],
)

@app.get("/")
def root():
    return {"message": "Hello, world!"}

@app.get("/items/")
def getItem():
    with open('items.json') as f:
        message = json.load(f)
    return {f"{message}"}

@app.get("/items/{item_id}")
def read_item(item_id):
    with open('items.json') as f:
        json_data = json.load(f)
        item = json_data["items"][int(item_id)-1]
        print(item)
    return {f"{item}"}
    

# @app.get("/items/<items_id>")
# def getItem():
#     with open('items.json') as f:
#         message = json.load(f)
#     return {f"{message}"}

@app.post("/items")
def add_item(name: str = Form(...), category:str = Form(...), image:UploadFile = File(...)):
    logger.info(f"Receive item: {name}, category: {category}")

    #画像の処理
    hash256_image = hashlib.sha256(repr(image).encode()).hexdigest()
    image_name = hash256_image + ".png"
    if image:
        fileobj = image.file
        upload_dir = open(os.path.join('images', image_name),'wb+')
        shutil.copyfileobj(fileobj, upload_dir)
        upload_dir.close()
        return {"アップロードファイル名": image_name}

    new_data = {"name": name, "category": category, "image_filename": image_name}

    if os.path.exists('items.json'):
        with open('items.json', "r", encoding="utf-8") as f:
            json_data = json.load(f)
            f.close()
    with open('items.json', "w", encoding="utf-8") as f:
        json_data["items"].append(new_data)
        json.dump(json_data, f, ensure_ascii=False , sort_keys=False)
    return {"message": f"item received: {name}"}

@app.get("/image/{image_filename}")
async def get_image(image_filename):
    # Create image path
    image = images / image_filename

    if not image_filename.endswith(".jpg"):
        raise HTTPException(status_code=400, detail="Image path does not end with .jpg")

    if not image.exists():
        logger.debug(f"Image not found: {image}")
        image = images / "default.jpg"

    return FileResponse(image)