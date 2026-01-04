"""
データベース接続管理
"""
from sqlalchemy import create_engine, Column, Integer, String, Text, Float, DateTime, JSON
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from app.core.config import settings
from datetime import datetime
import json

# SQLiteデータベースエンジン作成
engine = create_engine(
    settings.database_url,
    connect_args={"check_same_thread": False}  # SQLite用
)

# セッション作成
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Baseクラス
Base = declarative_base()


class RAGLog(Base):
    """RAG検索ログテーブル"""
    __tablename__ = "rag_logs"
    
    id = Column(Integer, primary_key=True, index=True)
    timestamp = Column(DateTime, default=datetime.utcnow, nullable=False)
    user_id = Column(String, nullable=True)  # PoCでは任意
    case_id = Column(String, nullable=True, index=True)
    status = Column(String, default="success", nullable=False)  # success, failed
    error_message = Column(Text, nullable=True)  # エラーメッセージ
    input_data = Column(JSON, nullable=True)  # 案件情報など
    rag_queries = Column(JSON, nullable=True)  # 検索クエリのリスト
    referenced_files = Column(JSON, nullable=True)  # 参照ファイル名のリスト
    search_results = Column(JSON, nullable=True)  # 検索結果の詳細（チャンクID、スコアなど）
    generated_answer = Column(Text, nullable=True)
    reasoning = Column(Text, nullable=True)  # 判断理由
    processing_time = Column(Float, nullable=True)  # 処理時間（秒）
    model_name = Column(String, nullable=True)
    top_k = Column(Integer, nullable=True)  # 検索結果の数


# データベース初期化
def init_db():
    """データベースとテーブルを作成"""
    Base.metadata.create_all(bind=engine)


# データベースセッション取得
def get_db():
    """データベースセッションを取得"""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

