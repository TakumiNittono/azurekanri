"""
Knowledgeファイル管理サービス
"""
from pathlib import Path
from typing import List, Dict, Optional
from app.core.config import settings
import os


class KnowledgeService:
    """Knowledgeファイル管理サービス"""
    
    def __init__(self):
        self.knowledge_dir = Path(settings.knowledge_dir)
        if not self.knowledge_dir.exists():
            raise FileNotFoundError(f"Knowledge directory not found: {self.knowledge_dir}")
    
    def get_file_list(self) -> List[Dict[str, any]]:
        """
        Knowledgeファイル一覧を取得
        
        Returns:
            List[Dict]: ファイル情報のリスト
                - filename: ファイル名
                - size: ファイルサイズ（バイト）
                - updated_at: 最終更新日時（ISO形式）
                - file_type: ファイル種別（price_*, contractor_*, repair_*など）
        """
        files = []
        
        if not self.knowledge_dir.exists():
            return files
        
        for file_path in sorted(self.knowledge_dir.glob("*.txt")):
            if file_path.is_file():
                stat = file_path.stat()
                filename = file_path.name
                
                # ファイル種別を判定
                file_type = self._get_file_type(filename)
                
                files.append({
                    "filename": filename,
                    "size": stat.st_size,
                    "updated_at": stat.st_mtime,  # Unix timestamp
                    "file_type": file_type,
                })
        
        return files
    
    def get_file_content(self, filename: str) -> Dict[str, any]:
        """
        ファイル内容を取得
        
        Args:
            filename: ファイル名
            
        Returns:
            Dict: ファイル情報と内容
                - filename: ファイル名
                - content: ファイル内容
                - size: ファイルサイズ
                - updated_at: 最終更新日時
                
        Raises:
            FileNotFoundError: ファイルが存在しない場合
        """
        # セキュリティ対策：パストラバーサル攻撃を防ぐ
        if ".." in filename or "/" in filename or "\\" in filename:
            raise ValueError("Invalid filename")
        
        file_path = self.knowledge_dir / filename
        
        if not file_path.exists():
            raise FileNotFoundError(f"File not found: {filename}")
        
        if not file_path.is_file():
            raise ValueError(f"Not a file: {filename}")
        
        # ファイル内容を読み込み（UTF-8）
        try:
            content = file_path.read_text(encoding="utf-8")
        except UnicodeDecodeError:
            # UTF-8で読めない場合はエラー
            raise ValueError(f"File encoding error: {filename}")
        
        stat = file_path.stat()
        
        return {
            "filename": filename,
            "content": content,
            "size": stat.st_size,
            "updated_at": stat.st_mtime,
        }
    
    def _get_file_type(self, filename: str) -> str:
        """
        ファイル名からファイル種別を判定
        
        Args:
            filename: ファイル名
            
        Returns:
            str: ファイル種別
        """
        if filename.startswith("price_"):
            return "price"
        elif filename.startswith("contractor_"):
            return "contractor"
        elif filename.startswith("repair_"):
            return "repair"
        elif filename.startswith("legal_") or filename.startswith("safety_"):
            return "legal_safety"
        elif filename.startswith("risk_"):
            return "risk"
        elif filename.startswith("estimate_") or filename.startswith("order_"):
            return "document"
        elif filename.startswith("judgement_") or filename.startswith("decision_"):
            return "judgement"
        elif filename.startswith("urgency_") or filename.startswith("water_supply_"):
            return "urgency"
        elif filename.startswith("material_") or filename.startswith("part_"):
            return "material"
        elif filename.startswith("construction_") or filename.startswith("difficulty_"):
            return "construction"
        elif filename.startswith("warranty_") or filename.startswith("seasonal_") or filename.startswith("building_") or filename.startswith("communication_"):
            return "other"
        elif filename == "past_case_study.txt":
            return "case_study"
        elif filename == "common_mistakes_lessons.txt":
            return "lessons"
        else:
            return "unknown"


# シングルトンインスタンス
knowledge_service = KnowledgeService()

