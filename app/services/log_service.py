"""
ログ保存サービス
"""
from sqlalchemy.orm import Session
from app.core.database import SessionLocal, RAGLog
from datetime import datetime
from typing import Optional, Dict, List
import time


class LogService:
    """ログ保存サービス"""
    
    def save_rag_log(
        self,
        user_id: Optional[str] = None,
        case_id: Optional[str] = None,
        input_data: Optional[Dict] = None,
        rag_queries: Optional[List[str]] = None,
        referenced_files: Optional[List[str]] = None,
        search_results: Optional[List[Dict]] = None,
        generated_answer: Optional[str] = None,
        reasoning: Optional[str] = None,
        processing_time: Optional[float] = None,
        model_name: Optional[str] = None,
        top_k: Optional[int] = None,
        status: str = "success",
        error_message: Optional[str] = None,
    ) -> int:
        """
        RAG検索ログを保存
        
        Args:
            user_id: ユーザーID
            case_id: 案件ID
            input_data: 入力データ（案件情報など）
            rag_queries: RAG検索クエリのリスト
            referenced_files: 参照ファイル名のリスト
            search_results: 検索結果の詳細（チャンクID、スコアなど）
            generated_answer: 生成された回答
            reasoning: 判断理由
            processing_time: 処理時間（秒）
            model_name: 使用したLLMモデル名
            top_k: 検索結果の数
            status: ステータス（success/failed）
            error_message: エラーメッセージ
            
        Returns:
            int: 保存されたログのID
        """
        db = SessionLocal()
        try:
            log = RAGLog(
                timestamp=datetime.utcnow(),
                user_id=user_id,
                case_id=case_id,
                status=status,
                error_message=error_message,
                input_data=input_data,
                rag_queries=rag_queries,
                referenced_files=referenced_files,
                search_results=search_results,
                generated_answer=generated_answer,
                reasoning=reasoning,
                processing_time=processing_time,
                model_name=model_name,
                top_k=top_k,
            )
            db.add(log)
            db.commit()
            db.refresh(log)
            return log.id
        except Exception as e:
            db.rollback()
            print(f"Error saving log: {e}")
            raise
        finally:
            db.close()


# シングルトンインスタンス
log_service = LogService()

