"""
アプリケーション設定管理
"""
from pathlib import Path
from pydantic_settings import BaseSettings
from typing import Optional


class Settings(BaseSettings):
    """アプリケーション設定"""
    
    # OpenAI API設定
    openai_api_key: str
    
    # Knowledgeディレクトリパス
    knowledge_dir: str = "/Users/takuminittono/Desktop/ragstudy/ラグルール/knowledge"
    
    # データベース設定
    database_url: str = "sqlite:///./rag_kanri.db"
    
    # 管理者認証（PoC簡易版）
    admin_password: str = "admin123"
    
    # アプリケーション設定
    app_name: str = "貯水槽修理案件管理システム"
    debug: bool = True
    secret_key: str = "change-me-in-production"
    
    # サーバー設定
    host: str = "0.0.0.0"
    port: int = 8000
    
    class Config:
        env_file = [".env.local", ".env"]  # .env.localを優先的に読み込む
        env_file_encoding = "utf-8"
        case_sensitive = False


# グローバル設定インスタンス
settings = Settings()

