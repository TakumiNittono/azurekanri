"""
管理者認証APIルート
"""
from fastapi import APIRouter, HTTPException, Request, Response
from fastapi.responses import JSONResponse
from app.core.auth import verify_admin_password, create_admin_session, delete_admin_session
from app.core.config import settings
from pydantic import BaseModel

router = APIRouter(prefix="/api/admin", tags=["admin"])


class LoginRequest(BaseModel):
    """ログインリクエスト"""
    password: str


class LoginResponse(BaseModel):
    """ログインレスポンス"""
    status: str
    message: str


@router.post("/login", response_model=LoginResponse)
async def admin_login(request: LoginRequest, response: Response):
    """
    管理者ログイン
    
    Args:
        request: ログインリクエスト（パスワード）
        response: FastAPI Responseオブジェクト
        
    Returns:
        LoginResponse: ログイン結果
    """
    if not verify_admin_password(request.password):
        raise HTTPException(status_code=401, detail="Invalid password")
    
    # セッションを作成
    token = create_admin_session()
    
    # Cookieにセッショントークンを設定
    response.set_cookie(
        key="admin_session",
        value=token,
        httponly=True,
        secure=False,  # PoCではFalse、本番ではTrue
        samesite="lax",
    )
    
    return LoginResponse(
        status="success",
        message="Login successful",
    )


@router.post("/logout")
async def admin_logout(request: Request, response: Response):
    """
    管理者ログアウト
    
    Args:
        request: FastAPI Requestオブジェクト
        response: FastAPI Responseオブジェクト
        
    Returns:
        dict: ログアウト結果
    """
    token = request.cookies.get("admin_session")
    if token:
        delete_admin_session(token)
    
    # Cookieを削除
    response.delete_cookie(key="admin_session")
    
    return {"status": "success", "message": "Logout successful"}


@router.get("/check")
async def check_admin(request: Request):
    """
    管理者認証状態を確認
    
    Args:
        request: FastAPI Requestオブジェクト
        
    Returns:
        dict: 認証状態
    """
    from app.core.auth import verify_admin_session
    
    token = request.cookies.get("admin_session")
    is_authenticated = verify_admin_session(token)
    
    return {
        "authenticated": is_authenticated,
        "message": "Authenticated" if is_authenticated else "Not authenticated",
    }

