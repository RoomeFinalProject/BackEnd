from fastapi import FastAPI, Form, HTTPException, Request
from fastapi.responses import JSONResponse
from fastapi.templating import Jinja2Templates
import requests

app = FastAPI()
templates = Jinja2Templates(directory="templates")

youtube = {
    "author": None,
    "vid_title": None,
}

no_embed = 'https://noembed.com/embed?url='


@app.get('/')
async def read_root(request: Request):
    return templates.TemplateResponse("index2.html", {"request": request})


@app.post('/get_info')
async def get_info(request: Request, video_url: str = Form(...)):
    full_url = no_embed + video_url
    response = requests.get(full_url)

    if response.status_code != 200:
        raise HTTPException(status_code=response.status_code, detail="Error fetching data from YouTube")

    data = response.json()
    set_info(data)

    # Print the results to the console
    print_results()

    return JSONResponse(content=youtube)


def set_info(data):
    youtube['author'] = data['author_name']
    youtube['vid_title'] = data['title']


def print_results():
    print("YouTube Video Information:")
    print(f"Author: {youtube['author']}")
    print(f"Video Title: {youtube['vid_title']}")