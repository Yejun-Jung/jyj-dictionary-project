import requests
import re
from bs4 import BeautifulSoup
from config import NAVER_CLIENT_ID, NAVER_CLIENT_SECRET
from models.database import mongodb


def search_naver_encyc(keyword):
    url = "https://openapi.naver.com/v1/search/encyc.json"
    headers = {
        "X-Naver-Client-Id": NAVER_CLIENT_ID,
        "X-Naver-Client-Secret": NAVER_CLIENT_SECRET,
    }
    params = {"query": keyword, "display": 5}
    response = requests.get(url, headers=headers, params=params)
    data = response.json()

    encyc_items = []

    session_headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
    }

    for item in data.get("items", []):
        title = re.sub(r'<[^>]+>', '', item["title"])
        api_desc = re.sub(r'<[^>]+>', '', item["description"])
        link = item["link"]
        thumbnail = item.get("thumbnail", "")
        if thumbnail.startswith("http://"):
            thumbnail = thumbnail.replace("http://", "https://", 1)

        detail_desc = api_desc
        if link:
            try:
                detail_resp = requests.get(link, headers=session_headers, timeout=5)
                detail_resp.encoding = 'utf-8'
                if detail_resp.status_code == 200:
                    soup = BeautifulSoup(detail_resp.text, "html.parser")

                    content_div = soup.select_one("#size_ct")
                    if not content_div:
                        content_div = soup.select_one(".size_ct_prt")
                        
                    if content_div:
                        text_content = content_div.get_text().strip()
                        text_content = re.sub(r'\s+', ' ', text_content)
                        if text_content:
                            detail_desc = text_content[:350] + "..." if len(text_content) > 350 else text_content
            except Exception as e:
                print(f"Detail crawling failed for {link}: {e}")

        encyc_items.append(
            {
                "title": title,
                "description": detail_desc,
                "link": link,
                "thumbnail": thumbnail,
            }
        )

    mongodb.db.encyclopedia.drop()
    if encyc_items:
        mongodb.db.encyclopedia.insert_many(encyc_items)

