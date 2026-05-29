from contextlib import asynccontextmanager
from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from pydantic import BaseModel
import uvicorn
from urllib.parse import quote, unquote

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


class FavoriteItem(BaseModel):
    title: str
    description: str = ""
    link: str
    thumbnail: str = ""


@app.get("/", response_class=HTMLResponse)
async def index(request: Request):
    return templates.TemplateResponse(
        "index.html",
        {"request": request, "items": [], "query": "", "fav_links": []},
    )


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

    response = templates.TemplateResponse(
        "index.html",
        {"request": request, "items": items, "query": query, "fav_links": fav_links},
    )

    if query:
        encoded_query = quote(query)
        response.set_cookie(key="last_query", value=encoded_query)

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


@app.get("/favorites", response_class=HTMLResponse)
async def favorites_page(request: Request):
    db = mongodb.get_db()
    favorites = list(db.favorites.find({}, {"_id": False}))
    raw_cookie = request.cookies.get("last_query", "")
    last_query = unquote(raw_cookie)
    return templates.TemplateResponse(
        "favorites.html",
        {"request": request, "items": favorites, "last_query": last_query},
    )


if __name__ == "__main__":
    uvicorn.run("main:app", host="127.0.0.1", port=8000, reload=True)
