import json
import requests
import io
import base64
from PIL import Image, PngImagePlugin


import os
import time
import serverHelper
import prompt_shortcut
def txt2ImgRequest(payload):
    url = "http://127.0.0.1:7860"

    # payload = { 
    #     "prompt": "cute cat, kitten",
    #     "steps": 10
    # }
    print("payload: ",payload)
    
    if(payload['use_prompt_shortcut']): # use edit prompt
        #edit prompt, replaceShortcut(prompt)
        payload['prompt'] = prompt_shortcut.replaceShortcut(payload['prompt'])
        # edit negative prompt, replaceShortcut(negative_prompt)
        payload['negative_prompt'] = prompt_shortcut.replaceShortcut(payload['negative_prompt'])
        
    
    #request the images to be generated
    request_path = "/sdapi/v1/txt2img"
    
    
    response = requests.post(url=f'{url}{request_path}', json=payload)

    r = response.json()

    #create a directory to store the images at
    # dirName = f'{time.time()}'
    dir_fullpath,dirName = serverHelper.makeDirPathName()
    serverHelper.createFolder(dir_fullpath)
    image_paths = []
    #for each image store the prompt and settings in the meta data
    for i in r['images']:
        image = Image.open(io.BytesIO(base64.b64decode(i.split(",",1)[0])))

        png_payload = {
            "image": "data:image/png;base64," + i
        }
        response2 = requests.post(url=f'{url}/sdapi/v1/png-info', json=png_payload)
        pnginfo = PngImagePlugin.PngInfo()
        pnginfo.add_text("parameters", response2.json().get("info"))
        image_name = f'output- {time.time()}.png'
        
        image_path = f'output/{dirName}/{image_name}'
        image_paths.append(image_path)
        image.save(f'./{image_path}', pnginfo=pnginfo)   
        
    return dirName,image_paths

import base64
from io import BytesIO


def img_2_b64(image):
    buff = BytesIO()
    image.save(buff, format="PNG")
    img_byte = base64.b64encode(buff.getvalue())
    img_str = img_byte.decode("utf-8")
    return img_str


from typing import Union

from fastapi import FastAPI

app = FastAPI()


@app.get("/")
def read_root():
    return {"Hello": "World"}


# @app.get("/items/{item_id}")
# def read_item(item_id: int, q: Union[str, None] = None):
#     return {"item_id": item_id, "q": q}





# @app.post("/txt2img/")
# async def txt2ImgHandle(payload:Payload):
#     print("txt2ImgHandle: \n")
#     txt2ImgRequest(payload)
#     return {"prompt":payload.prompt,"images": ""}


from fastapi import Request
import img2imgapi
@app.post("/txt2img/")
async def txt2ImgHandle(request:Request):
    print("txt2ImgHandle: \n")
    payload = await request.json() 
    dir_name,image_paths = txt2ImgRequest(payload)
    # return {"prompt":payload.prompt,"images": ""}
    return {"payload": payload,"dir_name": dir_name,"image_paths":image_paths}

@app.post("/img2img/")
async def img2ImgHandle(request:Request):
    print("img2ImgHandle: \n")
    payload = await request.json() 
    dir_name,image_paths = img2imgapi.img2ImgRequest(payload)
    # return {"prompt":payload.prompt,"images": ""}
    return {"payload": payload,"dir_name": dir_name,"image_paths":image_paths}






@app.post("/getInitImage/")
async def getInitImageHandle(request:Request):
    print("getInitImageHandle: \n")
    payload = await request.json() 
    print("payload:",payload)
    init_img_dir = "./init_images"
    init_img_name = payload["init_image_name"]# change this to "image_name"
    
    numOfAttempts = 3
    init_img_str = ""
    for i in range(numOfAttempts):
        try:
            image_path = f"{init_img_dir}/{init_img_name}"
            init_img = Image.open(image_path)
            init_img_str = img_2_b64(init_img)

            
            # # If file exists, delete it.
            # if os.path.isfile(image_path):
            #     os.remove(image_path)
        except:
            print(f"exception:fail to read an image file {image_path}, will try again {i} of {numOfAttempts}")
            #sleep for one second every time you try to read an image and fail
            time.sleep(1)
            continue;
    
    
    
    return {"payload": payload,"init_image_str":init_img_str}



@app.post("/swapModel")
async def swapModel(request:Request):
    url = "http://127.0.0.1:7860"
    print("swapModel: \n")
    payload = await request.json()
    print("payload:",payload)
    model_title = payload.title
    option_payload = {
        # "sd_model_checkpoint": "Anything-V3.0-pruned.ckpt [2700c435]"
        "sd_model_checkpoint": model_title

    }
    response = requests.post(url=f'{url}/sdapi/v1/options', json=option_payload)