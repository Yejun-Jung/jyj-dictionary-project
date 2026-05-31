from contextlib import asynccontextmanager
from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse, Response, FileResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from pydantic import BaseModel
import uvicorn
import requests as http_requests
from urllib.parse import quote, unquote, quote as url_quote

from encyc_scraper import search_naver_encyc
from models.database import mongodb


@asynccontextmanager
async def lifespan(app: FastAPI):
    mongodb.connect()
    yield
    mongodb.close()


app = FastAPI(lifespan=lifespan)
app.mount("/static", StaticFiles(directory="static"), name="static")
templates = Jinja2Templates(directory="templates")
templates.env.filters["url_quote"] = lambda s: url_quote(str(s), safe="")


def render(template_name: str, request: Request, **context) -> HTMLResponse:
    """Starlette 버전에 무관하게 동작하는 템플릿 렌더 함수"""
    template = templates.env.get_template(template_name)
    html = template.render(request=request, url_for=request.url_for, **context)
    return HTMLResponse(content=html)


class FavoriteItem(BaseModel):
    title: str
    description: str = ""
    link: str
    thumbnail: str = ""


@app.get("/favicon.ico", include_in_schema=False)
async def favicon():
    return FileResponse("static/favicon.ico")


@app.get("/", response_class=HTMLResponse)
async def index(request: Request):
    return render("index.html", request, items=[], query="", fav_links=[])


@app.get("/search", response_class=HTMLResponse)
async def search(request: Request, query: str = None):
    db = mongodb.get_db()
    if query:
        search_naver_encyc(query)
        items = list(db.encyclopedia.find({}, {"_id": False}))
    else:
        items = []

    favorites = list(db.favorites.find({}, {"_id": False}))
    fav_links = [fav["link"] for fav in favorites]

    response = render("index.html", request, items=items, query=query, fav_links=fav_links)

    if query:
        response.set_cookie(key="last_query", value=quote(query))

    return response


@app.post("/api/favorites")
async def toggle_favorite(item: FavoriteItem):
    db = mongodb.get_db()
    data = item.model_dump()
    link = data.get("link")

    existing = db.favorites.find_one({"link": link})
    if existing:
        db.favorites.delete_one({"link": link})
        action = "removed"
    else:
        db.favorites.insert_one(data)
        action = "added"

    return {"status": "success", "action": action}


@app.get("/api/data")
async def get_data():
    """수집한 백과사전 데이터를 JSON 형태로 반환"""
    db = mongodb.get_db()
    items = list(db.encyclopedia.find({}, {"_id": False}))
    return items


@app.get("/api/favorites/data")
async def get_favorites_data():
    """즐겨찾기 데이터를 JSON 형태로 반환"""
    db = mongodb.get_db()
    items = list(db.favorites.find({}, {"_id": False}))
    return items


@app.get("/api/image-proxy")
async def image_proxy(url: str):
    try:
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
            "Referer": "https://naver.com",
        }
        resp = http_requests.get(url, headers=headers, timeout=5)
        content_type = resp.headers.get("content-type", "image/jpeg")
        return Response(content=resp.content, media_type=content_type)
    except Exception:
        return Response(status_code=404)


@app.get("/favorites", response_class=HTMLResponse)
async def favorites_page(request: Request):
    db = mongodb.get_db()
    favorites = list(db.favorites.find({}, {"_id": False}))
    last_query = unquote(request.cookies.get("last_query", ""))
    return render("favorites.html", request, items=favorites, last_query=last_query)


if __name__ == "__main__":
    uvicorn.run("main:app", host="127.0.0.1", port=8000, reload=True)
