import os
import logging
import pathlib
import json
import hashlib
import shutil
import sqlite3
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

@app.get("/items")
async def getItem():
    # with open('items.json', "r", encoding="utf-8") as f:
    #     return json.load(f)
    # except json.decoder.JSONDecodeError: #json形式でない場合
    #dbへのアクセス
    con = sqlite3.connect("../db/mercari.sqlite3")
    cur = con.cursor()
    items = await get_items(cur)
    return items
    #sqlite3のerror

async def get_items(cur):
    cur.execute("SELECT id,name,category,image_name FROM items")
    items = cur.fetchall()
    #print(items)
    return items

@app.get("/search")
async def read_items(keyword: str = None):
    con = sqlite3.connect("../db/mercari.sqlite3")
    cur = con.cursor()
    items = await search_items(cur, keyword)
    return items

async def search_items(cur, keyword):
    print(keyword)
    cur.execute("""SELECT id, name, category, image_name FROM items WHERE name=(?);""",(keyword,))
    items = cur.fetchall()
    #print(items)
    return items


@app.get("/items/{item_id}")
def read_item(item_id):
    with open('items.json') as f:
        json_data = json.load(f)
        item = json_data["items"][int(item_id)-1]
        print(item)
    #dbの場合
    return {f"{item}"}

@app.post("/items")
async def add_item(name: str = Form(...), category:str = Form(...), image:UploadFile = File(...)):
    logger.info(f"Receive item: {name}, category: {category}")

    #画像の処理
    hash256_image = hashlib.sha256(repr(image).encode()).hexdigest()
    image_name = hash256_image + ".png"
    if image:
        fileobj = image.file
        upload_dir = open(os.path.join('images', image_name),'wb+')
        # shutil.copyfileobj(fileobj, upload_dir)
        # upload_dir.close()
        #return {"アップロードファイル名": image_name}

    #new_data = {"name": name, "category": category, "image_filename": image_name}

    #dbへのアクセス
    con = sqlite3.connect("../db/mercari.sqlite3")
    cur = con.cursor()

    #取得したcategoryをcategory_idに変換
    category_id = await get_category_id(cur, category)
    
    #idの取得
    id = await get_id(cur)
    cur.execute("""INSERT INTO items(id, name, category_id, image_name) VALUES(?,?,?,?);""",(int(id[0][0])+1, name, category_id, image_name,))
    con.commit()

    # if os.path.exists('items.json'):
    #     with open('items.json', "r", encoding="utf-8") as f:
    #         json_data = json.load(f)
    #         f.close()
    # with open('items.json', "w", encoding="utf-8") as f:
    #     json_data["items"].append(new_data)
    #     json.dump(json_data, f, ensure_ascii=False , sort_keys=False)
    return {"message": f"item received: {name}"}

async def get_id(cur):
    cur.execute("SELECT count(*) FROM items")
    id = cur.fetchall()
    return id

async def get_category_id(cur, category):
    category_id = cur.execute("""SERECT id FROM category WHERE name=(?);""",(category,))
    return category_id


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