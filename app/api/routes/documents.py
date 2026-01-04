"""
見積書・発注書生成APIルート
"""
from fastapi import APIRouter, HTTPException
from fastapi.responses import Response
from pydantic import BaseModel
from typing import Optional
from urllib.parse import quote
from app.services.document_service import document_service

router = APIRouter(prefix="/api/documents", tags=["documents"])


class GenerateEstimateRequest(BaseModel):
    """見積書生成リクエスト"""
    case_info: dict
    rag_answer: str


class GenerateOrderRequest(BaseModel):
    """発注書生成リクエスト"""
    case_info: dict
    rag_answer: str
    selected_contractor: str
    price: float
    contractor_info: Optional[dict] = None
    notes: Optional[str] = None


@router.post("/estimate")
async def generate_estimate(request: GenerateEstimateRequest):
    """
    見積書ドラフトを生成（Word形式）
    
    Args:
        request: 見積書生成リクエスト
        
    Returns:
        Response: DOCXファイル
    """
    try:
        docx_bytes = document_service.generate_estimate_draft_docx(
            case_info=request.case_info,
            rag_answer=request.rag_answer,
        )
        
        # ファイル名をASCII文字のみに変換（日本語対応）
        case_name = request.case_info.get('case_name', 'case')
        # 日本語をASCIIに変換（英数字とハイフン、アンダースコアのみ使用、スペースは削除）
        safe_filename = "".join(c if c.isalnum() or c in ('-', '_') else '_' for c in str(case_name))
        safe_filename = safe_filename[:50].strip() or "case"  # 長さ制限、空の場合は"case"
        # ファイル名がASCII文字のみであることを確認
        filename = f"estimate_{safe_filename}.docx"
        # ASCII文字のみであることを確認
        try:
            filename.encode('ascii')
        except UnicodeEncodeError:
            filename = "estimate_case.docx"
        
        # HTTPヘッダーはASCII文字のみ（RFC 5987準拠）
        return Response(
            content=docx_bytes,
            media_type="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
            headers={
                "Content-Disposition": f"attachment; filename={filename}"
            }
        )
    except Exception as e:
        import traceback
        error_detail = traceback.format_exc()
        print(f"Error generating estimate: {error_detail}")
        raise HTTPException(status_code=500, detail=f"Error generating estimate: {str(e)}")


@router.post("/order")
async def generate_order(request: GenerateOrderRequest):
    """
    発注書ドラフトを生成（Word形式）
    
    Args:
        request: 発注書生成リクエスト
        
    Returns:
        Response: DOCXファイル
    """
    try:
        import traceback
        docx_bytes = document_service.generate_order_draft_docx(
            case_info=request.case_info,
            rag_answer=request.rag_answer,
            selected_contractor=request.selected_contractor,
            price=request.price,
            contractor_info=request.contractor_info,
            notes=request.notes,
        )
        
        # ファイル名をASCII文字のみに変換（日本語対応）
        case_name = request.case_info.get('case_name', 'case')
        # 日本語をASCIIに変換（英数字とハイフン、アンダースコアのみ使用、スペースは削除）
        safe_filename = "".join(c if c.isalnum() or c in ('-', '_') else '_' for c in str(case_name))
        safe_filename = safe_filename[:50].strip() or "case"  # 長さ制限、空の場合は"case"
        # ファイル名がASCII文字のみであることを確認
        filename = f"order_{safe_filename}.docx"
        # ASCII文字のみであることを確認
        try:
            filename.encode('ascii')
        except UnicodeEncodeError:
            filename = "order_case.docx"
        
        # HTTPヘッダーはASCII文字のみ（RFC 5987準拠）
        return Response(
            content=docx_bytes,
            media_type="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
            headers={
                "Content-Disposition": f"attachment; filename={filename}"
            }
        )
    except Exception as e:
        import traceback
        error_detail = traceback.format_exc()
        print(f"Error generating order: {error_detail}")
        print(f"Request data: case_info={request.case_info}, contractor={request.selected_contractor}, price={request.price}")
        raise HTTPException(status_code=500, detail=f"Error generating order: {str(e)}\n{error_detail}")

