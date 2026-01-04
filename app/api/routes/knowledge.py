"""
Knowledgeファイル関連のAPIルート
"""
from fastapi import APIRouter, HTTPException, Path as PathParam
from typing import List
from app.services.knowledge_service import knowledge_service
from app.models.schemas import KnowledgeFileInfo, KnowledgeFileContent

router = APIRouter(prefix="/api/knowledge", tags=["knowledge"])


@router.get("/files", response_model=List[KnowledgeFileInfo])
async def get_knowledge_files():
    """
    Knowledgeファイル一覧を取得
    
    Returns:
        List[KnowledgeFileInfo]: ファイル情報のリスト
    """
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
    except FileNotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")


@router.get("/files/{filename}", response_model=KnowledgeFileContent)
async def get_knowledge_file_content(
    filename: str = PathParam(..., description="Knowledgeファイル名")
):
    """
    Knowledgeファイルの内容を取得
    
    Args:
        filename: ファイル名（.txtファイル）
        
    Returns:
        KnowledgeFileContent: ファイル内容
        
    Raises:
        HTTPException: ファイルが存在しない場合
    """
    try:
        # .txt拡張子がない場合は追加
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
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")

