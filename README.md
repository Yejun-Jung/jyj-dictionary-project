# 📚 지식백과 검색기 (Knowledge Encyclopedia Search)

> 네이버 지식백과 API와 BeautifulSoup을 활용한 웹 스크래핑 기반 검색 서비스
> 
> **배포 URL:** [https://jyj-dictionary-project.vercel.app](https://jyj-dictionary-project.vercel.app)

---

## 📌 프로젝트 개요

| 항목 | 내용 |
| --- | --- |
| **프로젝트명** | 지식백과 검색기 |
| **개발 기간** | 2026.05.29 ~ 2026.05.31 |
| **배포 환경** | Vercel |
| **사용 언어** | Python |
| **프레임워크** | FastAPI |
| **데이터베이스** | MongoDB Atlas |

### 기획 의도
검색어를 입력하면 **네이버 지식백과**에서 관련 항목을 수집하여 카드 형태로 보여주고, 마음에 드는 항목을 **즐겨찾기**로 저장해 언제든 다시 확인할 수 있는 서비스입니다.

---

## 🛠 기술 스택

- **Backend:** Python, FastAPI, Uvicorn
- **Scraping:** requests, BeautifulSoup4
- **Database:** MongoDB Atlas (pymongo)
- **Frontend:** HTML, CSS (Vanilla), JavaScript
- **Template Engine:** Jinja2
- **Deployment:** Vercel (@vercel/python)
- **Environment:** python-dotenv

---

## 📁 프로젝트 구조

```text
jyj-dictionary-project/
│
├── main.py                 # FastAPI 앱 진입점, 라우터 정의
├── encyc_scraper.py        # 네이버 API 호출 + BeautifulSoup 스크래핑
├── config.py               # 환경변수 로드
├── vercel.json             # Vercel 배포 설정
├── requirements.txt        # 의존성 패키지
│
├── models/
│   ├── __init__.py
│   └── database.py         # MongoDB 연결 클래스
│
├── templates/
│   ├── index.html          # 메인 검색 화면
│   └── favorites.html      # 즐겨찾기 화면
│
└── static/
    ├── favicon.ico
    └── css/
        └── style.css
```

---

## ⚙️ 주요 기능

### 1. 웹 스크래핑
- 네이버 오픈API (`/v1/search/encyc.json`)로 검색 결과 수집
- 각 항목의 상세 페이지를 `BeautifulSoup`으로 크롤링하여 본문 설명 추출
- 썸네일 이미지를 **Base64로 변환**하여 MongoDB에 저장 (배포 환경에서 네이버 CDN 차단을 우회하기 위한 수단)

### 2. 데이터 구조
수집된 데이터는 아래 형태로 MongoDB에 저장되며, `/api/data` 엔드포인트를 통해 JSON 형태로 조회 가능합니다.
```json
{
  "title": "이순신",
  "description": "본관 덕수(德水). 자 여해(汝諧)...",
  "link": "https://terms.naver.com/...",
  "thumbnail": "data:image/jpeg;base64,..."
}
```

### 3. 즐겨찾기 기능
- 검색 결과 카드의 ☆ 버튼 클릭 → `/api/favorites` POST 요청
- 이미 저장된 항목이면 **삭제**, 없으면 **추가** (토글 방식)
- `/favorites` 페이지에서 저장된 목록 확인 및 삭제 가능
- 즐겨찾기가 없을 때 **빈 상태 안내 UI** 표시

### 4. 검색 UX 개선
- 검색 버튼 클릭 시 **"검색 중입니다..." 로딩 메시지** 및 스피너 애니메이션 표시
- 마지막 검색어를 쿠키에 저장하여 활용
- 검색 결과가 없을 때 **빈 상태 안내 메시지** 표시
- 제목(지식백과 검색기) 클릭 시 검색이 초기화된 메인 화면으로 이동

---

## 🗺 화면 구성 및 라우팅

### 메인 화면 (`/`)
- 검색 입력창 및 검색 버튼
- 즐겨찾기 목록 바로가기 버튼
- 검색 결과: 카드 형태 (썸네일, 제목, 설명, 상세보기 링크, 즐겨찾기 버튼)

### 즐겨찾기 화면 (`/favorites`)
- 저장된 항목 카드 목록
- 각 카드에서 삭제 버튼으로 즐겨찾기 해제
- 이전 화면으로 돌아가기 버튼 (`history.back()`)

### 🌐 API 엔드포인트
| Method | URL | 설명 |
| --- | --- | --- |
| `GET` | `/search?query={keyword}` | 검색 실행 |
| `POST` | `/api/favorites` | 즐겨찾기 추가/해제 |
| `GET` | `/api/data` | 검색 데이터 JSON 조회 |
| `GET` | `/api/favorites/data` | 즐겨찾기 데이터 JSON 조회 |

---

## 🔍 트러블슈팅 (문제 해결 과정)

### 1. 배포 후 썸네일 이미지 엑스박스(403 Forbidden) 문제
- **상황:** 로컬 환경에서는 썸네일 이미지가 정상적으로 출력되었으나, Vercel 배포 후 모든 이미지가 엑스박스로 깨지는 현상 발생.
- **원인 분석:** 네이버 CDN 시스템이 Vercel 서버가 위치한 **해외(미국) IP 대역의 무단 이미지 호출을 차단**하기 때문이었음 (로컬은 한국 IP라 정상 작동). 서버를 경유하는 프록시 API(`/api/image-proxy`)를 구축해 우회하려 했으나 여전히 실패함.
- **해결 방법:** 백엔드 스크래핑이 일어나는 시점에 이미지 URL을 다운로드하여 **Base64 인코딩 문자열**(`data:image/jpeg;base64,...`)로 변환함. 변환된 텍스트 형태의 이미지 데이터를 MongoDB에 함께 저장하고, 프론트엔드에서는 텍스트 데이터를 그대로 `img src`에 주입함으로써 **외부 CDN 의존성을 완전히 제거**하고 이미지 로딩 문제를 완벽히 해결함.

### 2. '뒤로 가기' 시 즐겨찾기 UI 상태 불일치 (BFCache 문제)
- **상황:** '즐겨찾기 목록' 페이지에서 항목을 삭제한 뒤, 브라우저의 '뒤로 가기' 버튼을 눌러 복귀하면 삭제했던 항목의 별표(★)가 여전히 활성화된 상태로 남아있는 버그 발견.
- **원인 분석:** 브라우저의 뒤로 가기(`history.back()`) 동작 시, 서버에 새로운 데이터를 요청하는 것이 아니라 브라우저 메모리에 캐시된 이전 페이지(BFCache)를 그대로 복원하기 때문에 UI 갱신이 일어나지 않음.
- **해결 방법:** 즐겨찾기 페이지에서 항목을 삭제할 때 `sessionStorage`에 상태 변경 플래그(`favorites_changed=1`)를 저장함. 메인 검색 페이지에 `pageshow` 이벤트 리스너를 추가하여, 뒤로 가기로 페이지가 복원될 때 플래그를 감지하도록 처리. 플래그가 확인되면 서버에서 최신 화면을 다시 받아오도록 하되, 불필요한 재스크래핑으로 인한 지연을 막기 위해 **`skip_scrape=true` 쿼리 파라미터를 백엔드 로직에 추가**하여 DB에서 최신 즐겨찾기 상태만 빠르게 동기화하도록 성능과 UX를 모두 개선함.

### 3. Vercel 배포 환경에서 TemplateResponse 500 에러
- **상황:** Vercel 배포 후 메인 페이지 접속 시 `500 Internal Server Error` 발생. Vercel 로그 확인 결과 `TemplateResponse` 관련 `TypeError` 발생.
- **원인 분석:** 로컬 환경의 FastAPI(Starlette) 버전과 Vercel Python 런타임 환경에 기본 설치되는 Starlette의 버전에 차이가 있었음. 구버전과 신버전 간에 `TemplateResponse`를 호출할 때 넘겨주는 인자 규격이 달라 호환성 충돌이 일어남.
- **해결 방법:** FastAPI의 기본 `TemplateResponse` 래퍼에 의존하는 대신, 내부 템플릿 엔진인 Jinja2 환경(`templates.env.get_template()`)을 직접 호출하는 커스텀 `render()` 함수를 구현. 템플릿을 HTML 문자열로 렌더링한 뒤 표준 `HTMLResponse` 객체로 반환하도록 구조를 변경하여 호환성 문제를 해결함.

---

## 🚀 로컬 실행 방법

1. 저장소 클론 및 패키지 설치
```bash
git clone <repository-url>
cd jyj-dictionary-project
pip install -r requirements.txt
```

2. `.env` 파일 생성 (루트 디렉토리)
```env
MONGO_URI=mongodb+srv://...
NAVER_CLIENT_ID=...
NAVER_CLIENT_SECRET=...
```

3. 애플리케이션 실행
```bash
uvicorn main:app --reload
```
- 브라우저에서 `http://127.0.0.1:8000` 접속
