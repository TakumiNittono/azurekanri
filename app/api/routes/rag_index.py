"""
RAG Index管理APIルート
"""
from fastapi import APIRouter, HTTPException, Request
from app.services.rag_service import rag_service
from app.core.auth import require_admin
from app.models.schemas import ErrorResponse

router = APIRouter(prefix="/api/rag", tags=["rag"])


@router.post("/index/create")
async def create_index(request: Request):
    """
    RAG Indexを作成（管理者用）
    
    Returns:
        dict: 作成結果
    """
    require_admin(request)
    
    try:
        result = rag_service.create_index()
        
        if result["success"]:
            return {
                "status": "success",
                "message": result["message"],
                "indexed_files": result["indexed_files"],
                "total_chunks": result["total_chunks"],
            }
        else:
            raise HTTPException(status_code=500, detail=result["message"])
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error creating index: {str(e)}")


@router.post("/index/reindex")
async def reindex(request: Request):
    """
    RAG Indexを再構築（管理者用）
    
    Returns:
        dict: 再構築結果
    """
    require_admin(request)
    
    try:
        # 既存のIndexをクリア
        rag_service._index = None
        
        # 新しいIndexを作成
        result = rag_service.create_index()
        
        if result["success"]:
            return {
                "status": "success",
                "message": "Index recreated successfully",
                "indexed_files": result["indexed_files"],
                "total_chunks": result["total_chunks"],
            }
        else:
            raise HTTPException(status_code=500, detail=result["message"])
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error reindexing: {str(e)}")


@router.get("/index/status")
async def get_index_status():
    """
    Indexの状態を取得
    
    Returns:
        dict: Index状態
    """
    try:
        is_ready = rag_service.is_index_ready()
        
        return {
            "index_ready": is_ready,
            "message": "Index is ready" if is_ready else "Index not found. Please create index first.",
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error checking index status: {str(e)}")

