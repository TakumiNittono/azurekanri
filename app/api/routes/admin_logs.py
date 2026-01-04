"""
管理者用ログ閲覧APIルート
"""
from fastapi import APIRouter, HTTPException, Request, Query
from typing import Optional, List
from datetime import datetime
from app.core.auth import require_admin
from app.core.database import SessionLocal, RAGLog
from sqlalchemy import desc
from pydantic import BaseModel

router = APIRouter(prefix="/api/admin/logs", tags=["admin"])


class LogInfo(BaseModel):
    """ログ情報（一覧用）"""
    id: int
    timestamp: str
    user_id: Optional[str]
    case_id: Optional[str]
    status: str
    referenced_files_count: int
    processing_time: Optional[float]
    model_name: Optional[str]


class LogDetail(BaseModel):
    """ログ詳細"""
    id: int
    timestamp: str
    user_id: Optional[str]
    case_id: Optional[str]
    status: str
    error_message: Optional[str]
    input_data: Optional[dict]
    rag_queries: Optional[List[str]]
    referenced_files: Optional[List[str]]
    search_results: Optional[List[dict]]
    generated_answer: Optional[str]
    reasoning: Optional[str]
    processing_time: Optional[float]
    model_name: Optional[str]
    top_k: Optional[int]


@router.get("", response_model=List[LogInfo])
async def get_logs(
    request: Request,
    start_date: Optional[str] = Query(None, description="開始日時 (YYYY-MM-DD)"),
    end_date: Optional[str] = Query(None, description="終了日時 (YYYY-MM-DD)"),
    user_id: Optional[str] = Query(None, description="ユーザーID"),
    case_id: Optional[str] = Query(None, description="案件ID"),
    limit: int = Query(100, description="取得件数"),
):
    """
    管理者用：ログ一覧を取得
    
    Args:
        request: FastAPI Requestオブジェクト
        start_date: 開始日時
        end_date: 終了日時
        user_id: ユーザーID（フィルタ）
        case_id: 案件ID（フィルタ）
        limit: 取得件数
        
    Returns:
        List[LogInfo]: ログ情報のリスト
    """
    require_admin(request)
    
    db = SessionLocal()
    try:
        query = db.query(RAGLog)
        
        # フィルタリング
        if start_date:
            try:
                start_dt = datetime.fromisoformat(start_date)
                query = query.filter(RAGLog.timestamp >= start_dt)
            except ValueError:
                raise HTTPException(status_code=400, detail="Invalid start_date format")
        
        if end_date:
            try:
                end_dt = datetime.fromisoformat(end_date)
                query = query.filter(RAGLog.timestamp <= end_dt)
            except ValueError:
                raise HTTPException(status_code=400, detail="Invalid end_date format")
        
        if user_id:
            query = query.filter(RAGLog.user_id == user_id)
        
        if case_id:
            query = query.filter(RAGLog.case_id == case_id)
        
        # ソート（新しい順）
        query = query.order_by(desc(RAGLog.timestamp))
        
        # 件数制限
        logs = query.limit(limit).all()
        
        # レスポンス形式に変換
        result = []
        for log in logs:
            referenced_files = log.referenced_files if isinstance(log.referenced_files, list) else []
            result.append(LogInfo(
                id=log.id,
                timestamp=log.timestamp.isoformat(),
                user_id=log.user_id,
                case_id=log.case_id,
                status=getattr(log, 'status', 'success'),
                referenced_files_count=len(referenced_files) if referenced_files else 0,
                processing_time=log.processing_time,
                model_name=log.model_name,
            ))
        
        return result
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error getting logs: {str(e)}")
    finally:
        db.close()


@router.get("/{log_id}", response_model=LogDetail)
async def get_log_detail(
    log_id: int,
    request: Request,
):
    """
    管理者用：ログ詳細を取得
    
    Args:
        log_id: ログID
        request: FastAPI Requestオブジェクト
        
    Returns:
        LogDetail: ログ詳細
    """
    require_admin(request)
    
    db = SessionLocal()
    try:
        log = db.query(RAGLog).filter(RAGLog.id == log_id).first()
        
        if not log:
            raise HTTPException(status_code=404, detail=f"Log not found: {log_id}")
        
        return LogDetail(
            id=log.id,
            timestamp=log.timestamp.isoformat(),
            user_id=log.user_id,
            case_id=log.case_id,
            status=getattr(log, 'status', 'success'),
            error_message=getattr(log, 'error_message', None),
            input_data=log.input_data,
            rag_queries=log.rag_queries,
            referenced_files=log.referenced_files,
            search_results=getattr(log, 'search_results', None),
            generated_answer=log.generated_answer,
            reasoning=getattr(log, 'reasoning', None),
            processing_time=log.processing_time,
            model_name=log.model_name,
            top_k=getattr(log, 'top_k', None),
        )
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error getting log detail: {str(e)}")
    finally:
        db.close()

