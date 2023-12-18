
from fastapi import FastAPI, Form, HTTPException, Request, Query
from fastapi.responses import JSONResponse
from fastapi.templating import Jinja2Templates
import requests

app = FastAPI()

no_embed = 'https://noembed.com/embed?url='
url = "https://noembed.com/embed?url=https://www.youtube.com/watch?v=fTPi6hKmULU"

@app.get('/get_info')
async def get_info(request: Request, video_url: str = Query(...)):
    full_url = no_embed + video_url
    response = requests.get(full_url)

    if response.status_code != 200:
        raise HTTPException(status_code=response.status_code, detail="Error fetching data from YouTube")

    data = response.json()

    youtube = {
    "author": None,
    "vid_title": None,
}

    youtube['author'] = data['author_name']
    youtube['vid_title'] = data['title']


    # Print the results to the console
    print(JSONResponse(content=youtube))
    return JSONResponse(content=youtube)