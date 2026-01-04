"""
認証機能（簡易版）
"""
from fastapi import HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from app.core.config import settings
from typing import Optional

# セッション管理（簡易版、メモリ）
admin_sessions: set[str] = set()

security = HTTPBearer()


def verify_admin_password(password: str) -> bool:
    """
    管理者パスワードを検証
    
    Args:
        password: 入力されたパスワード
        
    Returns:
        bool: パスワードが正しい場合True
    """
    return password == settings.admin_password


def create_admin_session() -> str:
    """
    管理者セッションを作成
    
    Returns:
        str: セッショントークン
    """
    import secrets
    token = secrets.token_urlsafe(32)
    admin_sessions.add(token)
    return token


def verify_admin_session(token: Optional[str]) -> bool:
    """
    管理者セッションを検証
    
    Args:
        token: セッショントークン
        
    Returns:
        bool: セッションが有効な場合True
    """
    if token is None:
        return False
    return token in admin_sessions


def delete_admin_session(token: str):
    """
    管理者セッションを削除
    
    Args:
        token: セッショントークン
    """
    admin_sessions.discard(token)


def require_admin(request):
    """
    管理者認証が必要なエンドポイント用の依存関数
    
    Args:
        request: FastAPI Requestオブジェクト
        
    Raises:
        HTTPException: 認証に失敗した場合
    """
    # Cookieからセッショントークンを取得
    token = request.cookies.get("admin_session")
    
    if not verify_admin_session(token):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Admin authentication required",
        )

