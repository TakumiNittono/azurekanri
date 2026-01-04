"""
Pydanticスキーマ定義
"""
from pydantic import BaseModel
from typing import Optional, List


# Knowledgeファイル関連のスキーマ
class KnowledgeFileInfo(BaseModel):
    """Knowledgeファイル情報"""
    filename: str
    size: int
    updated_at: float  # Unix timestamp
    file_type: str


class KnowledgeFileContent(BaseModel):
    """Knowledgeファイル内容"""
    filename: str
    content: str
    size: int
    updated_at: float  # Unix timestamp


# RAG検索関連のスキーマ
class RAGSearchRequest(BaseModel):
    """RAG検索リクエスト"""
    query: str
    top_k: Optional[int] = 5


class RAGSearchResult(BaseModel):
    """RAG検索結果（1件）"""
    text: str
    score: float
    file_name: str
    file_type: str
    chunk_index: int


class RAGSearchResponse(BaseModel):
    """RAG検索レスポンス"""
    success: bool
    query: str
    results: List[RAGSearchResult]
    referenced_files: List[str]
    total_results: int
    message: Optional[str] = None


class RAGAnswerRequest(BaseModel):
    """RAG回答生成リクエスト"""
    query: str
    case_info: Optional[dict] = None
    top_k: Optional[int] = 5


class RAGAnswerResponse(BaseModel):
    """RAG回答生成レスポンス"""
    success: bool
    query: str
    answer: str
    reasoning: str
    referenced_files: List[str]
    search_results: Optional[List[RAGSearchResult]] = None
    message: Optional[str] = None


# エラーレスポンス
class ErrorResponse(BaseModel):
    """エラーレスポンス"""
    error: str
    message: str
    path: Optional[str] = None

