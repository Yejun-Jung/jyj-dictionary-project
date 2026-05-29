import os
from dotenv import load_dotenv

load_dotenv()

MONGO_URI = os.environ.get("MONGO_URI")
NAVER_CLIENT_ID = os.environ.get("NAVER_CLIENT_ID")
NAVER_CLIENT_SECRET = os.environ.get("NAVER_CLIENT_SECRET")

if not MONGO_URI:
    raise ValueError(
        ".env 파일을 찾지 못했거나 내용이 비어있습니다. 파일명을 다시 확인하세요."
    )
