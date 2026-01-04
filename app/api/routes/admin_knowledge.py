"""
管理者用Knowledge管理APIルート
"""
from fastapi import APIRouter, HTTPException, Request, Depends
from typing import List
from app.core.auth import require_admin
from app.services.knowledge_service import knowledge_service
from app.models.schemas import KnowledgeFileInfo, KnowledgeFileContent
from pydantic import BaseModel
import os
from pathlib import Path

router = APIRouter(prefix="/api/admin/knowledge", tags=["admin"])


class CreateFileRequest(BaseModel):
    """ファイル作成リクエスト"""
    filename: str
    content: str


@router.get("/files", response_model=List[KnowledgeFileInfo])
async def get_knowledge_files(request: Request):
    """
    管理者用：Knowledgeファイル一覧を取得
    
    Returns:
        List[KnowledgeFileInfo]: ファイル情報のリスト
    """
    require_admin(request)
    
    try:
        files = knowledge_service.get_file_list()
        # スキーマに合わせて変換
        return [
            KnowledgeFileInfo(
                filename=f["filename"],
                size=f["size"],
                updated_at=f["updated_at"],
                file_type=f["file_type"],
            )
            for f in files
        ]
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error getting files: {str(e)}")


@router.get("/files/{filename}", response_model=KnowledgeFileContent)
async def get_knowledge_file_content(
    filename: str,
    request: Request,
):
    """
    管理者用：Knowledgeファイルの内容を取得
    
    Args:
        filename: ファイル名
        request: FastAPI Requestオブジェクト
        
    Returns:
        KnowledgeFileContent: ファイル内容
    """
    require_admin(request)
    
    try:
        if not filename.endswith(".txt"):
            filename = f"{filename}.txt"
        
        content = knowledge_service.get_file_content(filename)
        # スキーマに合わせて変換
        return KnowledgeFileContent(
            filename=content["filename"],
            content=content["content"],
            size=content["size"],
            updated_at=content["updated_at"],
        )
    except FileNotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error getting file content: {str(e)}")


@router.post("/files")
async def create_knowledge_file(
    request_data: CreateFileRequest,
    request: Request,
):
    """
    管理者用：新規Knowledgeファイルを作成
    
    Args:
        request_data: ファイル作成リクエスト
        request: FastAPI Requestオブジェクト
        
    Returns:
        dict: 作成結果
    """
    require_admin(request)
    
    try:
        # バリデーション
        if not request_data.filename or not request_data.filename.strip():
            raise HTTPException(status_code=400, detail="Filename is required")
        
        filename = request_data.filename.strip()
        if not filename.endswith(".txt"):
            filename = f"{filename}.txt"
        
        # ファイル名のセキュリティチェック
        if ".." in filename or "/" in filename or "\\" in filename:
            raise HTTPException(status_code=400, detail="Invalid filename")
        
        # ファイルが既に存在するか確認
        knowledge_dir = Path(knowledge_service.knowledge_dir)
        file_path = knowledge_dir / filename
        
        if file_path.exists():
            raise HTTPException(status_code=400, detail=f"File already exists: {filename}")
        
        # ファイルを作成
        file_path.write_text(request_data.content, encoding="utf-8")
        
        return {
            "status": "success",
            "message": f"File created: {filename}",
            "filename": filename,
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error creating file: {str(e)}")


@router.delete("/files/{filename}")
async def delete_knowledge_file(
    filename: str,
    request: Request,
):
    """
    管理者用：Knowledgeファイルを削除
    
    Args:
        filename: ファイル名
        request: FastAPI Requestオブジェクト
        
    Returns:
        dict: 削除結果
    """
    require_admin(request)
    
    try:
        # バリデーション
        if not filename or not filename.strip():
            raise HTTPException(status_code=400, detail="Filename is required")
        
        filename = filename.strip()
        if not filename.endswith(".txt"):
            filename = f"{filename}.txt"
        
        # ファイル名のセキュリティチェック
        if ".." in filename or "/" in filename or "\\" in filename:
            raise HTTPException(status_code=400, detail="Invalid filename")
        
        # ファイルを削除
        knowledge_dir = Path(knowledge_service.knowledge_dir)
        file_path = knowledge_dir / filename
        
        if not file_path.exists():
            raise HTTPException(status_code=404, detail=f"File not found: {filename}")
        
        file_path.unlink()
        
        return {
            "status": "success",
            "message": f"File deleted: {filename}",
            "filename": filename,
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error deleting file: {str(e)}")

