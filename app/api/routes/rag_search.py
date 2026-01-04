"""
RAG検索APIルート
"""
import time
from fastapi import APIRouter, HTTPException
from app.services.rag_service import rag_service
from app.services.log_service import log_service
from app.models.schemas import (
    RAGSearchRequest, RAGSearchResponse,
    RAGAnswerRequest, RAGAnswerResponse
)

router = APIRouter(prefix="/api/rag", tags=["rag"])


@router.post("/search", response_model=RAGSearchResponse)
async def search_rag(request: RAGSearchRequest):
    """
    RAG検索を実行（検索結果のみ、LLM統合なし）
    
    Args:
        request: 検索リクエスト
            - query: 検索クエリ
            - top_k: 返す検索結果の数（デフォルト: 5）
            
    Returns:
        RAGSearchResponse: 検索結果
    """
    try:
        # バリデーション
        if not request.query or not request.query.strip():
            raise HTTPException(status_code=400, detail="Query is required")
        
        # 検索を実行
        result = rag_service.search(
            query=request.query.strip(),
            top_k=request.top_k or 5,
        )
        
        if not result["success"]:
            raise HTTPException(status_code=500, detail=result.get("message", "Search failed"))
        
        return RAGSearchResponse(**result)
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")


@router.post("/answer", response_model=RAGAnswerResponse)
async def generate_answer(request: RAGAnswerRequest):
    """
    RAG検索結果を基にLLMで回答を生成
    
    Args:
        request: 回答生成リクエスト
            - query: 検索クエリ
            - case_info: 案件情報（オプション）
            - top_k: 検索結果の数（デフォルト: 5）
            
    Returns:
        RAGAnswerResponse: 生成された回答
    """
    start_time = time.time()
    try:
        # バリデーション
        if not request.query or not request.query.strip():
            raise HTTPException(status_code=400, detail="Query is required")
        
        # 回答を生成
        result = rag_service.generate_answer(
            query=request.query.strip(),
            case_info=request.case_info,
            top_k=request.top_k or 5,
        )
        
        if not result["success"]:
            raise HTTPException(status_code=500, detail=result.get("message", "Answer generation failed"))
        
        # 処理時間を計算
        processing_time = time.time() - start_time
        
        # ログを保存
        try:
            case_id = request.case_info.get("case_id") if request.case_info else None
            # 検索結果の詳細を取得（チャンクID、スコアなど）
            search_results_detail = []
            if result.get("search_results"):
                for sr in result["search_results"][:5]:  # 上位5件を保存
                    search_results_detail.append({
                        "chunk_id": sr.get("chunk_id"),
                        "file_name": sr.get("file_name"),
                        "file_type": sr.get("file_type"),
                        "chunk_index": sr.get("chunk_index"),
                        "score": sr.get("score"),
                        "text_preview": sr.get("text", "")[:200] if sr.get("text") else None,
                    })
            
            log_service.save_rag_log(
                case_id=case_id,
                input_data=request.case_info,
                rag_queries=[request.query],
                referenced_files=result.get("referenced_files", []),
                search_results=search_results_detail,
                generated_answer=result.get("answer", ""),
                reasoning=result.get("reasoning", ""),
                processing_time=processing_time,
                model_name="gpt-4o-mini",
                top_k=request.top_k or 5,
                status="success",
            )
        except Exception as log_error:
            # ログ保存エラーは無視（本番ではログに記録）
            print(f"Log save error: {log_error}")
        
        return RAGAnswerResponse(**result)
        
    except HTTPException:
        raise
    except Exception as e:
        # エラーログを保存
        try:
            error_msg = str(e)
            log_service.save_rag_log(
                case_id=request.case_info.get("case_id") if request.case_info else None,
                input_data=request.case_info,
                rag_queries=[request.query] if request.query else [],
                status="failed",
                error_message=error_msg,
                processing_time=time.time() - start_time,
            )
        except:
            pass  # ログ保存エラーは無視
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")

