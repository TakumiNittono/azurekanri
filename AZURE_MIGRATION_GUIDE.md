# Azureサーバーレス構成への移行ガイド

## 📋 目次

1. [移行概要](#1-移行概要)
2. [事前準備](#2-事前準備)
3. [フェーズ1: Azureリソースの作成](#3-フェーズ1-azureリソースの作成)
4. [フェーズ2: コード修正](#4-フェーズ2-コード修正)
5. [フェーズ3: データ移行](#5-フェーズ3-データ移行)
6. [フェーズ4: Azure Functionsへのデプロイ](#6-フェーズ4-azure-functionsへのデプロイ)
7. [フェーズ5: Static Web Appsへのデプロイ](#7-フェーズ5-static-web-appsへのデプロイ)
8. [フェーズ6: 動作確認とテスト](#8-フェーズ6-動作確認とテスト)
9. [トラブルシューティング](#9-トラブルシューティング)

---

## 1. 移行概要

### 1.1 移行の全体像

現在のPoC版システム（FastAPI + SQLite + ローカルファイルシステム）を、Azureサーバーレス構成に移行します。

```
【現在の構成】
FastAPI (ローカル)
  ├─ SQLite (ローカルDB)
  ├─ ローカルファイルシステム (Knowledge/RAG Index)
  └─ 簡易認証

【移行後の構成】
Azure Static Web Apps (フロントエンド)
  ├─ Azure Functions (API)
  ├─ Azure Table Storage (ログ)
  ├─ Azure Blob Storage (Knowledge/RAG Index)
  └─ Azure Entra ID (認証)
```

### 1.2 移行の主な変更点

| 項目 | 現在 | 移行後 |
|------|------|--------|
| **Webサーバー** | FastAPI (uvicorn) | Azure Functions (HTTP Trigger) |
| **データベース** | SQLite | Azure Table Storage |
| **ファイルストレージ** | ローカルファイルシステム | Azure Blob Storage |
| **認証** | 簡易認証（パスワード） | Azure Entra ID |
| **フロントエンド** | FastAPI Templates | Azure Static Web Apps |
| **デプロイ** | ローカル実行 | GitHub Actions + Azure |

---

## 2. 事前準備

### 2.1 必要なアカウント・ツール

- [ ] **Azureアカウント**: [Azure Portal](https://portal.azure.com/)でアカウント作成
- [ ] **Azure CLI**: ローカル環境にインストール
- [ ] **GitHubアカウント**: コードリポジトリ用
- [ ] **Python 3.11**: 開発環境
- [ ] **Visual Studio Code**: 推奨エディタ（Azure拡張機能付き）

### 2.2 Azure CLIのインストールとログイン

```bash
# macOSの場合
brew install azure-cli

# Azureにログイン
az login

# サブスクリプション確認
az account list --output table

# デフォルトサブスクリプション設定
az account set --subscription "サブスクリプション名"
```

### 2.3 必要なPythonパッケージの追加

`requirements.txt`に以下を追加：

```txt
# Azure関連
azure-functions>=1.18.0
azure-storage-blob>=12.19.0
azure-data-tables>=12.4.0
azure-identity>=1.15.0
azure-functions-worker>=0.0.0
```

### 2.4 プロジェクト構造の準備

移行後のプロジェクト構造：

```
rag-kanri/
├── .github/
│   └── workflows/
│       └── deploy.yml              # GitHub Actions デプロイ設定
├── api/                            # Azure Functions (API)
│   ├── __init__.py
│   ├── function_app.py            # Azure Functions アプリケーション
│   ├── rag_search/                # RAG検索関数
│   │   ├── __init__.py
│   │   └── function.json
│   ├── generate_document/         # ドキュメント生成関数
│   │   ├── __init__.py
│   │   └── function.json
│   ├── knowledge_management/      # Knowledge管理関数
│   │   ├── __init__.py
│   │   └── function.json
│   ├── update_rag_index/          # RAG Index更新関数（Blob Trigger）
│   │   ├── __init__.py
│   │   └── function.json
│   └── admin_logs/                # ログ閲覧関数
│       ├── __init__.py
│       └── function.json
├── app/                            # 共通モジュール（既存）
│   ├── core/
│   │   ├── config.py              # 設定（Azure対応版）
│   │   └── auth.py                # 認証（Azure Entra ID対応版）
│   └── services/
│       ├── knowledge_service.py   # Blob Storage対応版
│       ├── rag_service.py         # Blob Storage対応版
│       └── log_service.py         # Table Storage対応版
├── static/                         # 静的ファイル（Static Web Apps用）
│   ├── css/
│   ├── js/
│   └── ...
├── templates/                      # HTMLテンプレート（Static Web Apps用）
│   ├── index.html
│   ├── answer.html
│   └── ...
├── scripts/                        # 移行スクリプト
│   ├── migrate_knowledge_to_blob.py
│   ├── migrate_logs_to_table.py
│   └── migrate_index_to_blob.py
├── host.json                       # Azure Functions設定
├── local.settings.json            # ローカル開発用設定
├── requirements.txt                # Python依存パッケージ
└── staticwebapp.config.json        # Static Web Apps設定
```

---

## 3. フェーズ1: Azureリソースの作成

### 3.1 リソースグループの作成

```bash
# リソースグループ作成
az group create \
  --name rg-ragkanri \
  --location japaneast

# 確認
az group show --name rg-ragkanri
```

### 3.2 ストレージアカウントの作成

```bash
# ストレージアカウント作成（Blob + Table Storage）
STORAGE_ACCOUNT_NAME="stragkanri$(date +%s | cut -c1-10)"

az storage account create \
  --name $STORAGE_ACCOUNT_NAME \
  --resource-group rg-ragkanri \
  --location japaneast \
  --sku Standard_LRS \
  --kind StorageV2

# 接続文字列を取得（後で使用）
az storage account show-connection-string \
  --name $STORAGE_ACCOUNT_NAME \
  --resource-group rg-ragkanri \
  --query connectionString \
  --output tsv
```

**重要**: 接続文字列をメモしておいてください。後で使用します。

### 3.3 Blob Storageコンテナの作成

```bash
# 接続文字列を環境変数に設定
export STORAGE_CONNECTION_STRING="<上記で取得した接続文字列>"

# コンテナ作成
az storage container create \
  --name knowledge-files \
  --connection-string $STORAGE_CONNECTION_STRING \
  --public-access off

az storage container create \
  --name rag-index \
  --connection-string $STORAGE_CONNECTION_STRING \
  --public-access off

az storage container create \
  --name generated-documents \
  --connection-string $STORAGE_CONNECTION_STRING \
  --public-access off
```

### 3.4 Azure Functionsアプリの作成

```bash
# Functionsアプリ作成
FUNCTION_APP_NAME="func-ragkanri-$(date +%s | cut -c1-10)"

az functionapp create \
  --name $FUNCTION_APP_NAME \
  --resource-group rg-ragkanri \
  --storage-account $STORAGE_ACCOUNT_NAME \
  --consumption-plan-location japaneast \
  --runtime python \
  --runtime-version 3.11 \
  --functions-version 4 \
  --os-type Linux

# アプリケーション設定（後で詳細設定）
az functionapp config appsettings set \
  --name $FUNCTION_APP_NAME \
  --resource-group rg-ragkanri \
  --settings \
    OPENAI_API_KEY="<OpenAI APIキー>" \
    BLOB_STORAGE_CONNECTION_STRING="<ストレージ接続文字列>" \
    TABLE_STORAGE_CONNECTION_STRING="<ストレージ接続文字列>" \
    KNOWLEDGE_CONTAINER_NAME="knowledge-files" \
    INDEX_CONTAINER_NAME="rag-index" \
    DOCUMENTS_CONTAINER_NAME="generated-documents" \
    LOG_TABLE_NAME="raglogs" \
    APP_ENV="production"
```

### 3.5 Azure Static Web Appsの作成

```bash
# Static Web Apps作成
STATIC_WEB_APP_NAME="swa-ragkanri-$(date +%s | cut -c1-10)"

az staticwebapp create \
  --name $STATIC_WEB_APP_NAME \
  --resource-group rg-ragkanri \
  --location japaneast \
  --sku Free

# デプロイトークンを取得（GitHub Actions用）
az staticwebapp secrets list \
  --name $STATIC_WEB_APP_NAME \
  --resource-group rg-ragkanri \
  --query properties.apiKey \
  --output tsv
```

**重要**: デプロイトークンをメモしておいてください。GitHub Secretsに設定します。

### 3.6 Azure Entra IDアプリ登録

```bash
# アプリ登録（Azure Portalで手動実行推奨）
# または Azure CLIで実行

# アプリ登録作成
az ad app create \
  --display-name "RAG案件管理システム" \
  --web-redirect-uris "https://$STATIC_WEB_APP_NAME.azurestaticapps.net/.auth/login/aad/callback"

# アプリIDを取得
APP_ID=$(az ad app list --display-name "RAG案件管理システム" --query [0].appId --output tsv)
TENANT_ID=$(az account show --query tenantId --output tsv)

echo "APP_ID: $APP_ID"
echo "TENANT_ID: $TENANT_ID"
```

**重要**: APP_IDとTENANT_IDをメモしておいてください。

---

## 4. フェーズ2: コード修正

### 4.1 設定ファイルの修正

#### 4.1.1 `app/core/config.py` の修正

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
    
    # コンテナ名
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

### 4.2 Knowledge Serviceの修正

#### 4.2.1 `app/services/knowledge_service.py` の修正

Azure Blob Storage対応版に書き換えます：

```python
"""
Knowledgeファイル管理サービス（Azure Blob Storage対応版）
"""
from azure.storage.blob import BlobServiceClient
from azure.identity import DefaultAzureCredential
from typing import List, Dict, Optional
from app.core.config import settings
import os


class KnowledgeService:
    """Knowledgeファイル管理サービス"""
    
    def __init__(self):
        self.container_name = settings.knowledge_container_name
        
        # 接続方法の選択（接続文字列 or Managed Identity）
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
        
        self.container_client = self.blob_service_client.get_container_client(
            self.container_name
        )
    
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
            print(f"Error listing blobs: {e}")
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

### 4.3 Log Serviceの修正

#### 4.3.1 `app/services/log_service.py` の修正

Azure Table Storage対応版に書き換えます：

```python
"""
ログ保存サービス（Azure Table Storage対応版）
"""
from azure.data.tables import TableServiceClient, TableClient
from azure.identity import DefaultAzureCredential
from datetime import datetime
from typing import Optional, Dict, List
from app.core.config import settings
import json
import uuid


class LogService:
    """ログ保存サービス"""
    
    def __init__(self):
        self.table_name = settings.log_table_name
        
        # 接続方法の選択
        if settings.table_storage_connection_string:
            self.table_service_client = TableServiceClient.from_connection_string(
                settings.table_storage_connection_string
            )
        elif settings.table_storage_url:
            credential = DefaultAzureCredential()
            self.table_service_client = TableServiceClient(
                endpoint=settings.table_storage_url,
                credential=credential
            )
        else:
            raise ValueError("Table Storage接続設定がありません")
        
        self.table_client = self.table_service_client.get_table_client(self.table_name)
        
        # テーブルが存在しない場合は作成
        try:
            self.table_client.create_table()
        except Exception:
            pass  # 既に存在する場合はスキップ
    
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
        
        self.table_client.upsert_entity(entity)
        return row_key


# シングルトンインスタンス
log_service = LogService()
```

### 4.4 RAG Serviceの修正

#### 4.4.1 `app/services/rag_service.py` の修正

Blob Storage対応版に修正します。主な変更点：

1. `self.index_dir` を Blob Storage に変更
2. Index保存・読み込み処理を Blob Storage 対応に変更
3. 一時ディレクトリを使用してLlamaIndexで読み込み

詳細な実装は、Azure.mdの「6.3.3 RAGインデックス管理（Azure版）」を参照してください。

### 4.5 Azure Functionsの作成

#### 4.5.1 `host.json` の作成

```json
{
  "version": "2.0",
  "logging": {
    "applicationInsights": {
      "samplingSettings": {
        "isEnabled": true,
        "maxTelemetryItemsPerSecond": 20
      }
    }
  },
  "extensionBundle": {
    "id": "Microsoft.Azure.Functions.ExtensionBundle",
    "version": "[4.*, 5.0.0)"
  },
  "functionTimeout": "00:10:00"
}
```

#### 4.5.2 `api/function_app.py` の作成

```python
"""
Azure Functions アプリケーション
"""
import azure.functions as func
import logging

app = func.FunctionApp()

# ルーター登録（各関数は個別のフォルダに配置）
# 例: rag_search関数は api/rag_search/__init__.py に実装
```

#### 4.5.3 `api/rag_search/__init__.py` の作成

```python
"""
RAG検索API（Azure Functions版）
"""
import azure.functions as func
import json
import logging
from app.services.rag_service import rag_service
from app.services.log_service import log_service
import time

app = func.FunctionApp()

@app.route(route="rag_search", methods=["POST"], auth_level=func.AuthLevel.FUNCTION)
def rag_search(req: func.HttpRequest) -> func.HttpResponse:
    """RAG検索・回答生成"""
    logging.info('RAG検索リクエストを受信')
    
    try:
        # リクエストボディを取得
        req_body = req.get_json()
        
        # 案件情報を取得
        case_info = req_body.get("case_info", {})
        user_id = req_body.get("user_id", "anonymous")
        case_id = req_body.get("case_id", "")
        
        start_time = time.time()
        
        # RAG検索実行
        result = rag_service.search_and_generate_answer(
            case_info=case_info,
            top_k=5
        )
        
        processing_time = time.time() - start_time
        
        # ログ保存
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
            top_k=5,
            status="success"
        )
        
        return func.HttpResponse(
            json.dumps(result, ensure_ascii=False),
            mimetype="application/json",
            status_code=200
        )
        
    except Exception as e:
        logging.error(f"RAG検索エラー: {e}", exc_info=True)
        
        # エラーログ保存
        try:
            log_service.save_rag_log(
                user_id=req_body.get("user_id", "anonymous"),
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

同様に、他の関数も作成します：
- `api/generate_document/__init__.py`
- `api/knowledge_management/__init__.py`
- `api/update_rag_index/__init__.py` (Blob Trigger)
- `api/admin_logs/__init__.py`

### 4.6 認証の修正

#### 4.6.1 `app/core/auth.py` の修正

Azure Entra ID対応版に書き換えます：

```python
"""
認証機能（Azure Entra ID対応版）
"""
from fastapi import Request, HTTPException, status
import json
import base64
from typing import Optional


def get_current_user(request: Request) -> dict:
    """
    Static Web Appsから渡される認証情報を取得
    
    Returns:
        dict: ユーザー情報
    """
    # Static Web Appsから渡される認証ヘッダー
    auth_header = request.headers.get("x-ms-client-principal")
    if not auth_header:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Not authenticated"
        )
    
    # Base64デコード
    try:
        decoded = base64.b64decode(auth_header)
        principal = json.loads(decoded)
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=f"Invalid authentication header: {e}"
        )
    
    return {
        "user_id": principal.get("userId", ""),
        "email": principal.get("userDetails", ""),
        "name": principal.get("userDetails", ""),
        "roles": principal.get("userRoles", []),
    }


def require_admin(request: Request):
    """
    管理者権限チェック
    
    Raises:
        HTTPException: 認証に失敗した場合
    """
    user = get_current_user(request)
    
    # Table Storageからユーザー情報を取得してロール確認
    # （実装は省略、必要に応じて追加）
    
    if "admin" not in user.get("roles", []):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin access required"
        )
    
    return user
```

---

## 5. フェーズ3: データ移行

### 5.1 Knowledgeファイルの移行

#### 5.1.1 移行スクリプトの作成

`scripts/migrate_knowledge_to_blob.py` を作成：

```python
"""
KnowledgeファイルをBlob Storageに移行
"""
from pathlib import Path
from azure.storage.blob import BlobServiceClient
from azure.identity import DefaultAzureCredential
from app.core.config import settings
import os

def migrate_knowledge_files():
    """KnowledgeファイルをBlob Storageに移行"""
    # ローカルファイルシステムから読み込み
    knowledge_dir = Path("/Users/takuminittono/Desktop/ragstudy/ラグルール/knowledge")
    
    if not knowledge_dir.exists():
        print(f"Knowledge directory not found: {knowledge_dir}")
        return
    
    # Blob Storage接続
    if settings.blob_storage_connection_string:
        blob_service_client = BlobServiceClient.from_connection_string(
            settings.blob_storage_connection_string
        )
    else:
        credential = DefaultAzureCredential()
        blob_service_client = BlobServiceClient(
            account_url=settings.blob_storage_url,
            credential=credential
        )
    
    container_client = blob_service_client.get_container_client("knowledge-files")
    
    # コンテナが存在しない場合は作成
    if not container_client.exists():
        container_client.create_container()
    
    # ファイルをアップロード
    txt_files = list(knowledge_dir.glob("*.txt"))
    print(f"Found {len(txt_files)} files to migrate")
    
    for file_path in txt_files:
        blob_client = container_client.get_blob_client(file_path.name)
        
        # ファイル内容を読み込み
        content = file_path.read_text(encoding='utf-8')
        
        # Blob Storageにアップロード
        blob_client.upload_blob(
            content.encode('utf-8'),
            overwrite=True,
            content_settings={"content_type": "text/plain; charset=utf-8"}
        )
        
        print(f"Uploaded: {file_path.name}")
    
    print("Migration completed!")

if __name__ == "__main__":
    migrate_knowledge_files()
```

#### 5.1.2 実行方法

```bash
# 環境変数を設定
export BLOB_STORAGE_CONNECTION_STRING="<接続文字列>"
export KNOWLEDGE_CONTAINER_NAME="knowledge-files"

# スクリプト実行
python scripts/migrate_knowledge_to_blob.py
```

### 5.2 SQLiteログの移行

#### 5.2.1 移行スクリプトの作成

`scripts/migrate_logs_to_table.py` を作成（Azure.mdの12.2.2を参照）

### 5.3 RAGインデックスの移行

#### 5.3.1 移行方法

RAGインデックスは、既存ファイルをコピーするよりも、**再構築を推奨**します。

理由：
- LlamaIndexのバージョン依存性
- エンベディングモデルの互換性
- Azure環境での動作確認

再構築手順：

1. KnowledgeファイルをBlob Storageに移行（完了）
2. Azure FunctionsでRAG Index更新関数を実行
3. 新しいインデックスがBlob Storageに保存される

---

## 6. フェーズ4: Azure Functionsへのデプロイ

### 6.1 ローカル開発環境の準備

#### 6.1.1 Azure Functions Core Toolsのインストール

```bash
# macOS
brew tap azure/functions
brew install azure-functions-core-tools@4

# 確認
func --version
```

#### 6.1.2 ローカル設定ファイルの作成

`local.settings.json` を作成：

```json
{
  "IsEncrypted": false,
  "Values": {
    "AzureWebJobsStorage": "<ストレージ接続文字列>",
    "FUNCTIONS_WORKER_RUNTIME": "python",
    "OPENAI_API_KEY": "<OpenAI APIキー>",
    "BLOB_STORAGE_CONNECTION_STRING": "<Blob Storage接続文字列>",
    "TABLE_STORAGE_CONNECTION_STRING": "<Table Storage接続文字列>",
    "KNOWLEDGE_CONTAINER_NAME": "knowledge-files",
    "INDEX_CONTAINER_NAME": "rag-index",
    "DOCUMENTS_CONTAINER_NAME": "generated-documents",
    "LOG_TABLE_NAME": "raglogs",
    "APP_ENV": "development"
  }
}
```

**重要**: `.gitignore`に`local.settings.json`を追加してください。

### 6.2 ローカルでのテスト

```bash
# Azure Functionsをローカルで起動
func start

# 別ターミナルでテスト
curl -X POST http://localhost:7071/api/rag_search \
  -H "Content-Type: application/json" \
  -d '{"case_info": {"repair_type": "漏水", "urgency": "緊急"}}'
```

### 6.3 GitHub Actionsでのデプロイ

#### 6.3.1 `.github/workflows/deploy.yml` の作成

```yaml
name: Deploy to Azure

on:
  push:
    branches:
      - main
  workflow_dispatch:

jobs:
  deploy-functions:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      
      - name: Set up Python
        uses: actions/setup-python@v4
        with:
          python-version: '3.11'
      
      - name: Install dependencies
        run: |
          pip install -r requirements.txt
          pip install azure-functions
      
      - name: Deploy to Azure Functions
        uses: Azure/functions-action@v1
        with:
          app-name: 'func-ragkanri-xxxxx'  # 実際の関数アプリ名に変更
          package: '.'
          publish-profile: ${{ secrets.AZURE_FUNCTIONAPP_PUBLISH_PROFILE }}
```

#### 6.3.2 GitHub Secretsの設定

GitHubリポジトリの Settings > Secrets and variables > Actions で以下を設定：

- `AZURE_FUNCTIONAPP_PUBLISH_PROFILE`: Functionsアプリの公開プロファイル

公開プロファイルの取得方法：

```bash
az functionapp deployment list-publishing-profiles \
  --name $FUNCTION_APP_NAME \
  --resource-group rg-ragkanri \
  --xml
```

---

## 7. フェーズ5: Static Web Appsへのデプロイ

### 7.1 フロントエンドファイルの準備

#### 7.1.1 `staticwebapp.config.json` の作成

```json
{
  "routes": [
    {
      "route": "/api/*",
      "allowedRoles": ["authenticated"]
    }
  ],
  "navigationFallback": {
    "rewrite": "/index.html"
  },
  "auth": {
    "identityProviders": {
      "azureActiveDirectory": {
        "userDetailsClaim": "http://schemas.xmlsoap.org/ws/2005/05/identity/claims/name"
      }
    }
  }
}
```

### 7.2 GitHub Actionsでのデプロイ

#### 7.2.1 `.github/workflows/deploy.yml` に追加

```yaml
  deploy-static-web-app:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      
      - name: Deploy to Azure Static Web Apps
        uses: Azure/static-web-apps-deploy@v1
        with:
          azure_static_web_apps_api_token: ${{ secrets.AZURE_STATIC_WEB_APPS_API_TOKEN }}
          repo_token: ${{ secrets.GITHUB_TOKEN }}
          action: "upload"
          app_location: "/"
          api_location: "api"
```

#### 7.2.2 GitHub Secretsの設定

- `AZURE_STATIC_WEB_APPS_API_TOKEN`: Static Web Appsのデプロイトークン（3.5で取得）

---

## 8. フェーズ6: 動作確認とテスト

### 8.1 動作確認チェックリスト

- [ ] Static Web Appsにアクセスできる
- [ ] Azure Entra IDでログインできる
- [ ] RAG検索APIが動作する
- [ ] Knowledgeファイル一覧が取得できる
- [ ] RAG Indexが作成できる
- [ ] ログがTable Storageに保存される
- [ ] ドキュメント生成が動作する

### 8.2 トラブルシューティング

#### 8.2.1 よくある問題

1. **認証エラー**
   - Static Web Appsの認証設定を確認
   - Azure Entra IDアプリ登録を確認

2. **Blob Storage接続エラー**
   - 接続文字列を確認
   - Managed Identityの権限を確認

3. **Functions実行エラー**
   - ログを確認: `az functionapp log tail --name <関数名> --resource-group rg-ragkanri`
   - アプリケーション設定を確認

---

## 9. トラブルシューティング

### 9.1 ログの確認方法

```bash
# Functionsログをリアルタイムで確認
az functionapp log tail \
  --name $FUNCTION_APP_NAME \
  --resource-group rg-ragkanri

# Static Web Appsログ
az staticwebapp logs show \
  --name $STATIC_WEB_APP_NAME \
  --resource-group rg-ragkanri
```

### 9.2 よくあるエラーと対処法

| エラー | 原因 | 対処法 |
|--------|------|--------|
| `ModuleNotFoundError` | 依存パッケージが不足 | `requirements.txt`を確認し、再デプロイ |
| `ConnectionError` | ストレージ接続エラー | 接続文字列を確認 |
| `AuthenticationError` | 認証エラー | Azure Entra ID設定を確認 |
| `TimeoutError` | タイムアウト | `host.json`の`functionTimeout`を延長 |

---

## 10. 次のステップ

移行が完了したら：

1. **コスト監視**: Azure Portalでコストを確認
2. **パフォーマンス監視**: Functionsのメトリックを確認
3. **セキュリティ確認**: アクセスログを確認
4. **ドキュメント更新**: README.mdを更新

---

**移行完了おめでとうございます！** 🎉

質問や問題があれば、Azure.mdの要件定義書を参照するか、Azure Portalのドキュメントを確認してください。

