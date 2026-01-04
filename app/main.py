"""
FastAPIアプリケーション
"""
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, HTMLResponse
from fastapi.templating import Jinja2Templates
from fastapi.staticfiles import StaticFiles
from app.core.config import settings
from app.core.database import init_db
from app.api.routes import knowledge, rag_index, rag_search, admin_auth, admin_knowledge, admin_logs, documents
import uvicorn

# データベース初期化
init_db()

# FastAPIアプリケーション初期化
app = FastAPI(
    title=settings.app_name,
    description="RAGを活用した貯水槽修理案件の判断支援Webアプリケーション",
    version="0.1.0",
    debug=settings.debug,
)

# テンプレートと静的ファイルの設定
templates = Jinja2Templates(directory="templates")
app.mount("/static", StaticFiles(directory="static"), name="static")

# CORS設定
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # PoCでは全許可、本番では適切に設定
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ルーター登録
app.include_router(knowledge.router)
app.include_router(rag_index.router)
app.include_router(rag_search.router)
app.include_router(admin_auth.router)
app.include_router(admin_knowledge.router)
app.include_router(admin_logs.router)
app.include_router(documents.router)


# エラーハンドリング
@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    """グローバル例外ハンドラー"""
    return JSONResponse(
        status_code=500,
        content={
            "error": "Internal Server Error",
            "message": str(exc) if settings.debug else "An error occurred",
            "path": str(request.url),
        },
    )


# ヘルスチェックエンドポイント
@app.get("/health")
async def health_check():
    """ヘルスチェック"""
    return {
        "status": "ok",
        "app_name": settings.app_name,
        "version": "0.1.0",
    }


# ルートエンドポイント（HTMLページ）
@app.get("/", response_class=HTMLResponse)
async def root(request: Request):
    """ルートエンドポイント（案件入力画面）"""
    return templates.TemplateResponse("index.html", {"request": request})


# 回答表示画面
@app.get("/answer", response_class=HTMLResponse)
async def answer_page(request: Request):
    """回答表示画面"""
    return templates.TemplateResponse("answer.html", {"request": request})


# 管理者ログイン画面
@app.get("/admin/login", response_class=HTMLResponse)
async def admin_login_page(request: Request):
    """管理者ログイン画面"""
    return templates.TemplateResponse("admin_login.html", {"request": request})


# 管理者画面
@app.get("/admin", response_class=HTMLResponse)
async def admin_page(request: Request):
    """管理者画面"""
    from app.core.auth import require_admin
    require_admin(request)
    return templates.TemplateResponse("admin.html", {"request": request})


if __name__ == "__main__":
    uvicorn.run(
        "app.main:app",
        host=settings.host,
        port=settings.port,
        reload=settings.debug,
    )

