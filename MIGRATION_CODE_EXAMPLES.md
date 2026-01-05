# Azure移行用コード例集

このドキュメントは、Azure.mdの要件定義書に基づいて、実際のコード変更例を提供します。

## 📋 目次

1. [設定ファイルの変更](#1-設定ファイルの変更)
2. [Knowledge Serviceの変更](#2-knowledge-serviceの変更)
3. [Log Serviceの変更](#3-log-serviceの変更)
4. [RAG Serviceの変更](#4-rag-serviceの変更)
5. [認証の変更](#5-認証の変更)
6. [Azure Functions実装例](#6-azure-functions実装例)

---

## 1. 設定ファイルの変更

### 1.1 `app/core/config.py` の完全版

```python
"""
アプリケーション設定管理（Azure対応版）
"""
from pydantic_settings import BaseSettings
from typing import Optional
import os


class Settings(BaseSettings):
    """アプリケーション設定"""
    
    # OpenAI API設定
    openai_api_key: str = os.getenv("OPENAI_API_KEY", "")
    
    # Azure Storage設定
    blob_storage_connection_string: Optional[str] = os.getenv("BLOB_STORAGE_CONNECTION_STRING")
    table_storage_connection_string: Optional[str] = os.getenv("TABLE_STORAGE_CONNECTION_STRING")
    blob_storage_account_name: Optional[str] = os.getenv("BLOB_STORAGE_ACCOUNT_NAME")
    
    # コンテナ名・テーブル名
    knowledge_container_name: str = os.getenv("KNOWLEDGE_CONTAINER_NAME", "knowledge-files")
    index_container_name: str = os.getenv("INDEX_CONTAINER_NAME", "rag-index")
    documents_container_name: str = os.getenv("DOCUMENTS_CONTAINER_NAME", "generated-documents")
    log_table_name: str = os.getenv("LOG_TABLE_NAME", "raglogs")
    
    # アプリケーション設定
    app_name: str = "貯水槽修理案件管理システム"
    app_env: str = os.getenv("APP_ENV", "development")
    debug: bool = app_env != "production"
    
    # Azure Functions設定
    function_app_name: Optional[str] = os.getenv("FUNCTION_APP_NAME")
    
    # Blob Storage URL（Managed Identity使用時）
    @property
    def blob_storage_url(self) -> str:
        """Blob StorageのURLを生成"""
        if self.blob_storage_account_name:
            return f"https://{self.blob_storage_account_name}.blob.core.windows.net"
        return ""
    
    # Table Storage URL（Managed Identity使用時）
    @property
    def table_storage_url(self) -> str:
        """Table StorageのURLを生成"""
        if self.blob_storage_account_name:
            return f"https://{self.blob_storage_account_name}.table.core.windows.net"
        return ""
    
    class Config:
        env_file = [".env.local", ".env"]
        env_file_encoding = "utf-8"
        case_sensitive = False


# グローバル設定インスタンス
settings = Settings()
```

---

## 2. Knowledge Serviceの変更

### 2.1 完全な実装例

```python
"""
Knowledgeファイル管理サービス（Azure Blob Storage対応版）
"""
from azure.storage.blob import BlobServiceClient
from azure.identity import DefaultAzureCredential
from typing import List, Dict, Optional
from app.core.config import settings
import logging

logger = logging.getLogger(__name__)


class KnowledgeService:
    """Knowledgeファイル管理サービス"""
    
    def __init__(self):
        self.container_name = settings.knowledge_container_name
        
        # 接続方法の選択（接続文字列 or Managed Identity）
        try:
            if settings.blob_storage_connection_string:
                self.blob_service_client = BlobServiceClient.from_connection_string(
                    settings.blob_storage_connection_string
                )
                logger.info("Blob Storage接続: 接続文字列を使用")
            elif settings.blob_storage_url:
                credential = DefaultAzureCredential()
                self.blob_service_client = BlobServiceClient(
                    account_url=settings.blob_storage_url,
                    credential=credential
                )
                logger.info("Blob Storage接続: Managed Identityを使用")
            else:
                raise ValueError("Blob Storage接続設定がありません")
            
            self.container_client = self.blob_service_client.get_container_client(
                self.container_name
            )
            
            # コンテナが存在しない場合は作成
            if not self.container_client.exists():
                self.container_client.create_container()
                logger.info(f"コンテナ作成: {self.container_name}")
        except Exception as e:
            logger.error(f"Blob Storage接続エラー: {e}")
            raise
    
    def get_file_list(self) -> List[Dict[str, any]]:
        """
        Knowledgeファイル一覧を取得
        
        Returns:
            List[Dict]: ファイル情報のリスト
        """
        files = []
        
        try:
            blobs = self.container_client.list_blobs()
            
            for blob in blobs:
                if not blob.name.endswith(".txt"):
                    continue
                
                file_type = self._get_file_type(blob.name)
                
                files.append({
                    "filename": blob.name,
                    "size": blob.size,
                    "updated_at": blob.last_modified.timestamp() if blob.last_modified else 0,
                    "file_type": file_type,
                })
        except Exception as e:
            logger.error(f"ファイル一覧取得エラー: {e}")
            return []
        
        files.sort(key=lambda x: x["filename"])
        return files
    
    def get_file_content(self, filename: str) -> Dict[str, any]:
        """
        ファイル内容を取得
        
        Args:
            filename: ファイル名
            
        Returns:
            Dict: ファイル情報と内容
        """
        # セキュリティ対策
        if ".." in filename or "/" in filename or "\\" in filename:
            raise ValueError("Invalid filename")
        
        blob_client = self.container_client.get_blob_client(filename)
        
        if not blob_client.exists():
            raise FileNotFoundError(f"File not found: {filename}")
        
        try:
            content = blob_client.download_blob().readall().decode('utf-8')
        except UnicodeDecodeError:
            raise ValueError(f"File encoding error: {filename}")
        
        properties = blob_client.get_blob_properties()
        
        return {
            "filename": filename,
            "content": content,
            "size": properties.size,
            "updated_at": properties.last_modified.timestamp() if properties.last_modified else 0,
        }
    
    def create_file(self, filename: str, content: str) -> Dict[str, str]:
        """新規Knowledgeファイルを作成"""
        if ".." in filename or "/" in filename or "\\" in filename:
            raise ValueError("Invalid filename")
        
        if not filename.endswith(".txt"):
            filename = f"{filename}.txt"
        
        blob_client = self.container_client.get_blob_client(filename)
        if blob_client.exists():
            raise ValueError(f"File already exists: {filename}")
        
        blob_client.upload_blob(
            content.encode('utf-8'),
            overwrite=False,
            content_settings={"content_type": "text/plain; charset=utf-8"}
        )
        
        logger.info(f"ファイル作成: {filename}")
        
        return {
            "status": "success",
            "message": f"File created: {filename}",
            "filename": filename,
        }
    
    def delete_file(self, filename: str) -> Dict[str, str]:
        """Knowledgeファイルを削除"""
        if ".." in filename or "/" in filename or "\\" in filename:
            raise ValueError("Invalid filename")
        
        if not filename.endswith(".txt"):
            filename = f"{filename}.txt"
        
        blob_client = self.container_client.get_blob_client(filename)
        
        if not blob_client.exists():
            raise FileNotFoundError(f"File not found: {filename}")
        
        blob_client.delete_blob()
        
        logger.info(f"ファイル削除: {filename}")
        
        return {
            "status": "success",
            "message": f"File deleted: {filename}",
            "filename": filename,
        }
    
    def _get_file_type(self, filename: str) -> str:
        """ファイル名からファイル種別を判定"""
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
```

---

## 3. Log Serviceの変更

### 3.1 完全な実装例

```python
"""
ログ保存サービス（Azure Table Storage対応版）
"""
from azure.data.tables import TableServiceClient, TableClient
from azure.identity import DefaultAzureCredential
from datetime import datetime, timedelta
from typing import Optional, Dict, List
from app.core.config import settings
import json
import uuid
import logging

logger = logging.getLogger(__name__)


class LogService:
    """ログ保存サービス"""
    
    def __init__(self):
        self.table_name = settings.log_table_name
        
        # 接続方法の選択
        try:
            if settings.table_storage_connection_string:
                self.table_service_client = TableServiceClient.from_connection_string(
                    settings.table_storage_connection_string
                )
                logger.info("Table Storage接続: 接続文字列を使用")
            elif settings.table_storage_url:
                credential = DefaultAzureCredential()
                self.table_service_client = TableServiceClient(
                    endpoint=settings.table_storage_url,
                    credential=credential
                )
                logger.info("Table Storage接続: Managed Identityを使用")
            else:
                raise ValueError("Table Storage接続設定がありません")
            
            self.table_client = self.table_service_client.get_table_client(self.table_name)
            
            # テーブルが存在しない場合は作成
            try:
                self.table_client.create_table()
                logger.info(f"テーブル作成: {self.table_name}")
            except Exception:
                pass  # 既に存在する場合はスキップ
        except Exception as e:
            logger.error(f"Table Storage接続エラー: {e}")
            raise
    
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
    ) -> str:
        """
        RAG検索ログをTable Storageに保存
        
        Returns:
            str: RowKey（ログIDとして使用）
        """
        now = datetime.utcnow()
        partition_key = now.strftime("%Y-%m-%d")
        row_key = f"{now.strftime('%Y%m%dT%H%M%S')}_{uuid.uuid4().hex[:8]}"
        
        # エンティティ作成
        entity = {
            "PartitionKey": partition_key,
            "RowKey": row_key,
            "timestamp": now.isoformat(),
            "user_id": user_id or "",
            "case_id": case_id or "",
            "status": status,
            "error_message": error_message or "",
            "input_data": json.dumps(input_data, ensure_ascii=False) if input_data else "",
            "rag_queries": json.dumps(rag_queries, ensure_ascii=False) if rag_queries else "",
            "referenced_files": json.dumps(referenced_files, ensure_ascii=False) if referenced_files else "",
            "search_results": json.dumps(search_results, ensure_ascii=False) if search_results else "",
            "generated_answer": generated_answer or "",
            "reasoning": reasoning or "",
            "processing_time": processing_time or 0.0,
            "model_name": model_name or "",
            "top_k": top_k or 0,
        }
        
        # エンティティサイズ制限（1MB）を考慮
        entity_size = sum(len(str(v)) for v in entity.values())
        if entity_size > 900000:  # 900KB以下に制限
            if generated_answer:
                max_answer_length = 900000 - (entity_size - len(generated_answer))
                entity["generated_answer"] = generated_answer[:max_answer_length] + "...(truncated)"
        
        try:
            self.table_client.upsert_entity(entity)
            logger.info(f"ログ保存成功: {row_key}")
            return row_key
        except Exception as e:
            logger.error(f"ログ保存エラー: {e}")
            raise
    
    def get_logs(
        self,
        start_date: Optional[str] = None,
        end_date: Optional[str] = None,
        user_id: Optional[str] = None,
        case_id: Optional[str] = None,
        limit: int = 100,
    ) -> List[dict]:
        """
        ログを取得（日付範囲、ユーザーID、案件IDでフィルタリング）
        
        Args:
            start_date: 開始日（YYYY-MM-DD形式）
            end_date: 終了日（YYYY-MM-DD形式）
            user_id: ユーザーID（フィルタ）
            case_id: 案件ID（フィルタ）
            limit: 取得件数上限
            
        Returns:
            List[dict]: ログエンティティのリスト
        """
        logs = []
        
        # 日付範囲のデフォルト値
        if not start_date:
            start_date = (datetime.utcnow() - timedelta(days=30)).strftime("%Y-%m-%d")
        if not end_date:
            end_date = datetime.utcnow().strftime("%Y-%m-%d")
        
        # パーティションキー範囲を生成
        start_dt = datetime.strptime(start_date, "%Y-%m-%d")
        end_dt = datetime.strptime(end_date, "%Y-%m-%d")
        
        current_date = start_dt
        while current_date <= end_dt:
            partition_key = current_date.strftime("%Y-%m-%d")
            
            # フィルタークエリを構築
            filter_parts = []
            if user_id:
                filter_parts.append(f"user_id eq '{user_id}'")
            if case_id:
                filter_parts.append(f"case_id eq '{case_id}'")
            
            filter_query = " and ".join(filter_parts) if filter_parts else None
            
            # クエリ実行
            try:
                entities = self.table_client.query_entities(
                    query_filter=filter_query,
                    results_per_page=limit
                )
                
                for entity in entities:
                    # JSON文字列をパース
                    if entity.get("input_data"):
                        try:
                            entity["input_data"] = json.loads(entity["input_data"])
                        except:
                            pass
                    if entity.get("rag_queries"):
                        try:
                            entity["rag_queries"] = json.loads(entity["rag_queries"])
                        except:
                            pass
                    if entity.get("referenced_files"):
                        try:
                            entity["referenced_files"] = json.loads(entity["referenced_files"])
                        except:
                            pass
                    if entity.get("search_results"):
                        try:
                            entity["search_results"] = json.loads(entity["search_results"])
                        except:
                            pass
                    
                    logs.append(entity)
                    
                    if len(logs) >= limit:
                        break
            except Exception as e:
                logger.error(f"ログ取得エラー (partition: {partition_key}): {e}")
                continue
            
            if len(logs) >= limit:
                break
            
            current_date += timedelta(days=1)
        
        # タイムスタンプでソート（新しい順）
        logs.sort(key=lambda x: x.get("timestamp", ""), reverse=True)
        
        return logs[:limit]
    
    def get_log_detail(self, log_id: str) -> Optional[dict]:
        """
        ログID（RowKey）からログ詳細を取得
        
        Args:
            log_id: RowKey（ログID）
            
        Returns:
            Optional[dict]: ログエンティティ（存在しない場合はNone）
        """
        # RowKeyから日付を抽出（YYYYMMDDTHHMMSS_xxxx形式）
        try:
            partition_key = log_id[:10].replace("T", "-")[:10]  # YYYY-MM-DD形式に変換
            
            try:
                entity = self.table_client.get_entity(
                    partition_key=partition_key,
                    row_key=log_id
                )
                
                # JSON文字列をパース
                if entity.get("input_data"):
                    try:
                        entity["input_data"] = json.loads(entity["input_data"])
                    except:
                        pass
                if entity.get("rag_queries"):
                    try:
                        entity["rag_queries"] = json.loads(entity["rag_queries"])
                    except:
                        pass
                if entity.get("referenced_files"):
                    try:
                        entity["referenced_files"] = json.loads(entity["referenced_files"])
                    except:
                        pass
                if entity.get("search_results"):
                    try:
                        entity["search_results"] = json.loads(entity["search_results"])
                    except:
                        pass
                
                return entity
            except Exception as e:
                logger.error(f"ログ詳細取得エラー: {e}")
                return None
        except Exception as e:
            logger.error(f"ログID解析エラー: {e}")
            return None


# シングルトンインスタンス
log_service = LogService()
```

---

## 4. RAG Serviceの変更

### 4.1 Blob Storage対応の主要部分

RAG Serviceの変更は複雑なため、主要な変更点のみ示します：

```python
"""
RAG検索サービス（Azure Blob Storage対応版）
"""
from pathlib import Path
from typing import List, Optional
from llama_index.core import Document, VectorStoreIndex, StorageContext, load_index_from_storage
from llama_index.core.node_parser import SimpleNodeParser
from llama_index.embeddings.openai import OpenAIEmbedding
from llama_index.llms.openai import OpenAI
from app.core.config import settings
from app.services.knowledge_service import knowledge_service
from azure.storage.blob import BlobServiceClient
from azure.identity import DefaultAzureCredential
import os
import json
import tempfile
import shutil


class RAGService:
    """RAG検索サービス"""
    
    def __init__(self):
        self.index_container = settings.index_container_name
        
        # Blob Storage接続
        if settings.blob_storage_connection_string:
            self.blob_service_client = BlobServiceClient.from_connection_string(
                settings.blob_storage_connection_string
            )
        elif settings.blob_storage_url:
            credential = DefaultAzureCredential()
            self.blob_service_client = BlobServiceClient(
                account_url=settings.blob_storage_url,
                credential=credential
            )
        else:
            raise ValueError("Blob Storage接続設定がありません")
        
        self.index_container_client = self.blob_service_client.get_container_client(
            self.index_container
        )
        
        # OpenAI設定
        self.embed_model = OpenAIEmbedding(api_key=settings.openai_api_key)
        self.llm = OpenAI(api_key=settings.openai_api_key, model="gpt-4o-mini")
        
        # Index（遅延読み込み）
        self._index: Optional[VectorStoreIndex] = None
        self._index_version: Optional[int] = None
    
    def load_index(self) -> bool:
        """
        保存されたIndexをBlob Storageから読み込む
        
        Returns:
            bool: 読み込み成功フラグ
        """
        try:
            # 最新バージョンのインデックスを検索
            latest_version = self._get_latest_index_version()
            if latest_version is None:
                return False
            
            # 一時ディレクトリを作成
            temp_dir = Path(tempfile.mkdtemp())
            
            try:
                # インデックスファイルをダウンロード
                index_files = [
                    "default__vector_store.json",
                    "docstore.json",
                    "graph_store.json",
                    "index_store.json",
                ]
                
                for filename in index_files:
                    blob_name = f"index_v{latest_version}/{filename}"
                    blob_client = self.index_container_client.get_blob_client(blob_name)
                    
                    if blob_client.exists():
                        content = blob_client.download_blob().readall().decode('utf-8')
                        file_path = temp_dir / filename
                        file_path.write_text(content, encoding='utf-8')
                
                # LlamaIndexで読み込み
                storage_context = StorageContext.from_defaults(persist_dir=str(temp_dir))
                self._index = load_index_from_storage(
                    storage_context,
                    embed_model=self.embed_model,
                )
                self._index_version = latest_version
                return True
            finally:
                # 一時ディレクトリを削除
                shutil.rmtree(temp_dir, ignore_errors=True)
                
        except Exception as e:
            print(f"Error loading index: {e}")
            return False
    
    def _save_index(self, index: VectorStoreIndex, version: int):
        """
        IndexをBlob Storageに保存
        
        Args:
            index: VectorStoreIndex
            version: インデックスバージョン
        """
        # 一時ディレクトリに保存
        temp_dir = Path(tempfile.mkdtemp())
        
        try:
            index.storage_context.persist(persist_dir=str(temp_dir))
            
            # Blob Storageにアップロード
            for file_path in temp_dir.glob("*.json"):
                blob_name = f"index_v{version}/{file_path.name}"
                blob_client = self.index_container_client.get_blob_client(blob_name)
                
                content = file_path.read_text(encoding='utf-8')
                blob_client.upload_blob(
                    content.encode('utf-8'),
                    overwrite=True,
                    content_settings={"content_type": "application/json"}
                )
        finally:
            # 一時ディレクトリを削除
            shutil.rmtree(temp_dir, ignore_errors=True)
    
    def _get_latest_index_version(self) -> Optional[int]:
        """最新のインデックスバージョンを取得"""
        versions = []
        blobs = self.index_container_client.list_blobs(name_starts_with="index_v")
        
        for blob in blobs:
            # index_v{version}/filename 形式からバージョンを抽出
            parts = blob.name.split("/")
            if len(parts) >= 2 and parts[0].startswith("index_v"):
                version = int(parts[0].replace("index_v", ""))
                if version not in versions:
                    versions.append(version)
        
        return max(versions) if versions else None
    
    # 以下、既存のcreate_index()、search_and_generate_answer()メソッドは
    # 基本的に変更なし（Knowledge ServiceがBlob Storageから読み込むため）
```

---

## 5. 認証の変更

### 5.1 Azure Entra ID対応版

```python
"""
認証機能（Azure Entra ID対応版）
"""
from fastapi import Request, HTTPException, status
import json
import base64
from typing import Optional, Dict
import logging

logger = logging.getLogger(__name__)


def get_current_user(request: Request) -> dict:
    """
    Static Web Appsから渡される認証情報を取得
    
    Returns:
        dict: ユーザー情報
            - user_id: ユーザーID
            - email: メールアドレス
            - name: 表示名
            - roles: ロールリスト
    """
    # Static Web Appsから渡される認証ヘッダー
    auth_header = request.headers.get("x-ms-client-principal")
    if not auth_header:
        logger.warning("認証ヘッダーが見つかりません")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Not authenticated"
        )
    
    # Base64デコード
    try:
        decoded = base64.b64decode(auth_header)
        principal = json.loads(decoded)
    except Exception as e:
        logger.error(f"認証ヘッダーのデコードエラー: {e}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=f"Invalid authentication header: {e}"
        )
    
    user_info = {
        "user_id": principal.get("userId", ""),
        "email": principal.get("userDetails", ""),
        "name": principal.get("userDetails", ""),
        "roles": principal.get("userRoles", []),
    }
    
    logger.info(f"ユーザー認証成功: {user_info['email']}")
    return user_info


def require_admin(request: Request) -> dict:
    """
    管理者権限チェック
    
    Returns:
        dict: ユーザー情報
    
    Raises:
        HTTPException: 認証に失敗した場合
    """
    user = get_current_user(request)
    
    # ロール確認（Static Web Appsのロール設定に依存）
    # または、Table Storageからユーザー情報を取得してロール確認
    if "admin" not in user.get("roles", []):
        logger.warning(f"管理者権限なし: {user['email']}")
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin access required"
        )
    
    return user


# Azure Functions用の認証ヘルパー
def get_user_from_request(req) -> Optional[Dict]:
    """
    Azure Functionsのリクエストからユーザー情報を取得
    
    Args:
        req: Azure FunctionsのHttpRequest
        
    Returns:
        Optional[Dict]: ユーザー情報（認証されていない場合はNone）
    """
    auth_header = req.headers.get("x-ms-client-principal")
    if not auth_header:
        return None
    
    try:
        decoded = base64.b64decode(auth_header)
        principal = json.loads(decoded)
        return {
            "user_id": principal.get("userId", ""),
            "email": principal.get("userDetails", ""),
            "name": principal.get("userDetails", ""),
            "roles": principal.get("userRoles", []),
        }
    except Exception as e:
        logger.error(f"認証ヘッダーのデコードエラー: {e}")
        return None
```

---

## 6. Azure Functions実装例

### 6.1 RAG検索関数の完全版

```python
"""
RAG検索API（Azure Functions版）
"""
import azure.functions as func
import json
import logging
import time
from app.services.rag_service import rag_service
from app.services.log_service import log_service
from app.core.auth import get_user_from_request

logger = logging.getLogger(__name__)

app = func.FunctionApp()

@app.route(route="rag_search", methods=["POST"], auth_level=func.AuthLevel.FUNCTION)
def rag_search(req: func.HttpRequest) -> func.HttpResponse:
    """RAG検索・回答生成"""
    logger.info('RAG検索リクエストを受信')
    
    try:
        # 認証チェック
        user = get_user_from_request(req)
        user_id = user.get("email", "anonymous") if user else "anonymous"
        
        # リクエストボディを取得
        try:
            req_body = req.get_json()
        except ValueError:
            return func.HttpResponse(
                json.dumps({"error": "Invalid JSON"}, ensure_ascii=False),
                mimetype="application/json",
                status_code=400
            )
        
        # 案件情報を取得
        case_info = req_body.get("case_info", {})
        case_id = req_body.get("case_id", "")
        top_k = req_body.get("top_k", 5)
        
        if not case_info:
            return func.HttpResponse(
                json.dumps({"error": "case_info is required"}, ensure_ascii=False),
                mimetype="application/json",
                status_code=400
            )
        
        start_time = time.time()
        
        # RAG検索実行
        result = rag_service.search_and_generate_answer(
            case_info=case_info,
            top_k=top_k
        )
        
        processing_time = time.time() - start_time
        
        # ログ保存
        try:
            log_service.save_rag_log(
                user_id=user_id,
                case_id=case_id,
                input_data=case_info,
                rag_queries=result.get("queries", []),
                referenced_files=result.get("referenced_files", []),
                search_results=result.get("search_results", []),
                generated_answer=result.get("answer", ""),
                reasoning=result.get("reasoning", ""),
                processing_time=processing_time,
                model_name="gpt-4o-mini",
                top_k=top_k,
                status="success"
            )
        except Exception as log_error:
            logger.error(f"ログ保存エラー: {log_error}")
            # ログエラーは続行
        
        return func.HttpResponse(
            json.dumps(result, ensure_ascii=False),
            mimetype="application/json",
            status_code=200
        )
        
    except Exception as e:
        logger.error(f"RAG検索エラー: {e}", exc_info=True)
        
        # エラーログ保存
        try:
            user = get_user_from_request(req)
            user_id = user.get("email", "anonymous") if user else "anonymous"
            req_body = req.get_json() if req else {}
            
            log_service.save_rag_log(
                user_id=user_id,
                case_id=req_body.get("case_id", ""),
                input_data=req_body.get("case_info", {}),
                status="failed",
                error_message=str(e)
            )
        except:
            pass
        
        return func.HttpResponse(
            json.dumps({"error": str(e)}, ensure_ascii=False),
            mimetype="application/json",
            status_code=500
        )
```

### 6.2 Knowledge管理関数の例

```python
"""
Knowledge管理API（Azure Functions版）
"""
import azure.functions as func
import json
import logging
from app.services.knowledge_service import knowledge_service
from app.core.auth import require_admin_function

logger = logging.getLogger(__name__)

app = func.FunctionApp()

@app.route(route="knowledge/list", methods=["GET"], auth_level=func.AuthLevel.FUNCTION)
def knowledge_list(req: func.HttpRequest) -> func.HttpResponse:
    """Knowledgeファイル一覧取得"""
    try:
        files = knowledge_service.get_file_list()
        
        return func.HttpResponse(
            json.dumps({"files": files}, ensure_ascii=False),
            mimetype="application/json",
            status_code=200
        )
    except Exception as e:
        logger.error(f"Knowledge一覧取得エラー: {e}")
        return func.HttpResponse(
            json.dumps({"error": str(e)}, ensure_ascii=False),
            mimetype="application/json",
            status_code=500
        )

@app.route(route="knowledge/{filename}", methods=["GET"], auth_level=func.AuthLevel.FUNCTION)
def knowledge_get(req: func.HttpRequest) -> func.HttpResponse:
    """Knowledgeファイル内容取得"""
    try:
        filename = req.route_params.get("filename")
        if not filename:
            return func.HttpResponse(
                json.dumps({"error": "filename is required"}, ensure_ascii=False),
                mimetype="application/json",
                status_code=400
            )
        
        file_content = knowledge_service.get_file_content(filename)
        
        return func.HttpResponse(
            json.dumps(file_content, ensure_ascii=False),
            mimetype="application/json",
            status_code=200
        )
    except FileNotFoundError:
        return func.HttpResponse(
            json.dumps({"error": "File not found"}, ensure_ascii=False),
            mimetype="application/json",
            status_code=404
        )
    except Exception as e:
        logger.error(f"Knowledge取得エラー: {e}")
        return func.HttpResponse(
            json.dumps({"error": str(e)}, ensure_ascii=False),
            mimetype="application/json",
            status_code=500
        )
```

### 6.3 RAG Index更新関数（Blob Trigger）

```python
"""
RAG Index更新関数（Blob Trigger）
"""
import azure.functions as func
import logging
from app.services.rag_service import rag_service

logger = logging.getLogger(__name__)

app = func.FunctionApp()

@app.blob_trigger(
    arg_name="myblob",
    path="knowledge-files/{name}",
    connection="BLOB_STORAGE_CONNECTION_STRING"
)
def update_rag_index(myblob: func.InputStream) -> None:
    """
    Knowledgeファイルが更新されたときにRAG Indexを自動更新
    
    Args:
        myblob: Blob Storageの入力ストリーム
    """
    logger.info(f'RAG Index更新トリガー: {myblob.name}')
    
    try:
        # RAG Indexを再構築
        result = rag_service.create_index()
        
        if result.get("success"):
            logger.info(f'RAG Index更新成功: {result.get("indexed_files")}ファイル, {result.get("total_chunks")}チャンク')
        else:
            logger.error(f'RAG Index更新失敗: {result.get("message")}')
    except Exception as e:
        logger.error(f'RAG Index更新エラー: {e}', exc_info=True)
```

---

## 7. 移行スクリプト例

### 7.1 Knowledgeファイル移行スクリプト

```python
"""
KnowledgeファイルをBlob Storageに移行
"""
from pathlib import Path
from azure.storage.blob import BlobServiceClient
from azure.identity import DefaultAzureCredential
from app.core.config import settings
import os
import sys

def migrate_knowledge_files():
    """KnowledgeファイルをBlob Storageに移行"""
    # ローカルファイルシステムから読み込み
    knowledge_dir = Path("/Users/takuminittono/Desktop/ragstudy/ラグルール/knowledge")
    
    if not knowledge_dir.exists():
        print(f"Knowledge directory not found: {knowledge_dir}")
        return False
    
    # Blob Storage接続
    try:
        if settings.blob_storage_connection_string:
            blob_service_client = BlobServiceClient.from_connection_string(
                settings.blob_storage_connection_string
            )
        elif settings.blob_storage_url:
            credential = DefaultAzureCredential()
            blob_service_client = BlobServiceClient(
                account_url=settings.blob_storage_url,
                credential=credential
            )
        else:
            print("Blob Storage接続設定がありません")
            return False
    except Exception as e:
        print(f"Blob Storage接続エラー: {e}")
        return False
    
    container_client = blob_service_client.get_container_client("knowledge-files")
    
    # コンテナが存在しない場合は作成
    if not container_client.exists():
        container_client.create_container()
        print("コンテナ作成: knowledge-files")
    
    # ファイルをアップロード
    txt_files = list(knowledge_dir.glob("*.txt"))
    print(f"Found {len(txt_files)} files to migrate")
    
    success_count = 0
    error_count = 0
    
    for file_path in txt_files:
        try:
            blob_client = container_client.get_blob_client(file_path.name)
            
            # ファイル内容を読み込み
            content = file_path.read_text(encoding='utf-8')
            
            # Blob Storageにアップロード
            blob_client.upload_blob(
                content.encode('utf-8'),
                overwrite=True,
                content_settings={"content_type": "text/plain; charset=utf-8"}
            )
            
            print(f"✓ Uploaded: {file_path.name}")
            success_count += 1
        except Exception as e:
            print(f"✗ Error uploading {file_path.name}: {e}")
            error_count += 1
    
    print(f"\nMigration completed!")
    print(f"  Successfully migrated: {success_count} files")
    print(f"  Errors: {error_count} files")
    
    return error_count == 0

if __name__ == "__main__":
    success = migrate_knowledge_files()
    sys.exit(0 if success else 1)
```

---

これらのコード例を参考に、段階的に移行を進めてください。詳細は`AZURE_MIGRATION_GUIDE.md`を参照してください。



