# 次のステップ実装ガイド

## 📋 目次

1. [ステップ1: RAG検索API統合](#ステップ1-rag検索api統合)
2. [ステップ2: Knowledge管理API（Blob Storage対応）](#ステップ2-knowledge管理apiblob-storage対応)
3. [ステップ3: ログ管理API（Table Storage対応）](#ステップ3-ログ管理apitable-storage対応)
4. [ステップ4: Azure Entra ID認証統合](#ステップ4-azure-entra-id認証統合)
5. [ステップ5: Azure Static Web Appsデプロイ](#ステップ5-azure-static-web-appsデプロイ)

---

## ステップ1: RAG検索API統合

### 目的
`/api/search`エンドポイントにRAG検索機能を統合する

### 現在の状況
- ✅ `api-azure/search/__init__.py` - スタブ実装済み
- ✅ `app/services/rag_service.py` - PoC版のRAGサービス実装済み
- ⚠️ Azure Functions用にRAGサービスを修正する必要がある

### 実装手順

#### 1.1 依存パッケージの追加

`api-azure/requirements.txt`に以下を追加：

```txt
azure-functions
azure-data-tables
llama-index>=0.10.0,<0.15.0
openai>=1.0.0
tiktoken>=0.5.0
```

#### 1.2 RAGサービスをAzure Functions用に修正

**注意**: Azure Functionsでは、ローカルファイルシステムへのアクセスが制限されるため、Blob StorageからKnowledgeファイルを読み込む必要があります。

**オプションA: 簡易版（既存RAGサービスをそのまま使用）**

1. KnowledgeファイルをBlob Storageにアップロード（手動またはスクリプト）
2. Azure Functionsの一時ディレクトリにダウンロード
3. 既存のRAGサービスを使用

**オプションB: 完全版（Blob Storage対応RAGサービスを作成）**

`MIGRATION_CODE_EXAMPLES.md`の「4. RAG Serviceの変更」を参照して実装

#### 1.3 `/api/search`エンドポイントの実装

`api-azure/search/__init__.py`を以下のように実装：

```python
import azure.functions as func
import json
import os
from app.services.rag_service import RAGService

def main(req: func.HttpRequest) -> func.HttpResponse:
    try:
        # リクエストボディを取得
        body = req.get_json()
        case_info = body.get("case_info", {})
        
        # RAGサービス初期化
        rag_service = RAGService()
        
        # Indexが読み込まれていない場合は読み込む
        if rag_service._index is None:
            rag_service.load_index()
        
        # RAG検索・回答生成
        result = rag_service.search_and_generate_answer(
            case_info=case_info,
            top_k=5
        )
        
        return func.HttpResponse(
            json.dumps({
                "ok": True,
                "answer": result.get("answer", ""),
                "reasoning": result.get("reasoning", ""),
                "referenced_files": result.get("referenced_files", []),
                "queries": result.get("queries", [])
            }, ensure_ascii=False),
            mimetype="application/json",
            status_code=200
        )
        
    except Exception as e:
        return func.HttpResponse(
            json.dumps({
                "ok": False,
                "error": str(e)
            }, ensure_ascii=False),
            mimetype="application/json",
            status_code=500
        )
```

#### 1.4 環境変数の設定

Azure Functionsのアプリケーション設定に以下を追加：

```bash
OPENAI_API_KEY=<OpenAI APIキー>
KNOWLEDGE_DIR=/tmp/knowledge  # 一時ディレクトリ
```

### 動作確認

```bash
# ローカルでテスト
curl -X POST http://localhost:7071/api/search \
  -H "Content-Type: application/json" \
  -d '{"case_info": {"repair_type": "漏水", "urgency": "緊急"}}'
```

---

## ステップ2: Knowledge管理API（Blob Storage対応）

### 目的
KnowledgeファイルをAzure Blob Storageで管理するAPIを実装する

### 現在の状況
- ✅ `app/services/knowledge_service.py` - PoC版（ローカルファイルシステム）実装済み
- ⚪ Azure Blob Storage対応版は未実装

### 実装手順

#### 2.1 新しいAzure Functionsエンドポイントの作成

`api-azure/knowledge/`ディレクトリを作成：

```bash
mkdir -p api-azure/knowledge
```

#### 2.2 `api-azure/knowledge/function.json`の作成

```json
{
  "scriptFile": "__init__.py",
  "bindings": [
    {
      "authLevel": "anonymous",
      "type": "httpTrigger",
      "direction": "in",
      "name": "req",
      "methods": ["get", "post", "delete"],
      "route": "knowledge"
    },
    {
      "type": "http",
      "direction": "out",
      "name": "$return"
    }
  ]
}
```

#### 2.3 `api-azure/knowledge/__init__.py`の実装

`MIGRATION_CODE_EXAMPLES.md`の「2. Knowledge Serviceの変更」を参照して実装

主要なエンドポイント：
- `GET /api/knowledge` - ファイル一覧取得
- `GET /api/knowledge/{filename}` - ファイル内容取得
- `POST /api/knowledge` - 新規ファイル作成
- `DELETE /api/knowledge/{filename}` - ファイル削除

#### 2.4 環境変数の設定

```bash
BLOB_STORAGE_CONNECTION_STRING=<Blob Storage接続文字列>
KNOWLEDGE_CONTAINER_NAME=knowledge-files
```

### 動作確認

```bash
# ファイル一覧取得
curl http://localhost:7071/api/knowledge

# ファイル内容取得
curl http://localhost:7071/api/knowledge/contractor_case_studies.txt
```

---

## ステップ3: ログ管理API（Table Storage対応）

### 目的
RAG検索ログをAzure Table Storageで管理するAPIを実装する

### 現在の状況
- ✅ `app/services/log_service.py` - PoC版（SQLite）実装済み
- ✅ `api-azure/cases/__init__.py` - Table Storageの使用例あり
- ⚪ ログ管理APIは未実装

### 実装手順

#### 3.1 新しいAzure Functionsエンドポイントの作成

```bash
mkdir -p api-azure/logs
```

#### 3.2 `api-azure/logs/function.json`の作成

```json
{
  "scriptFile": "__init__.py",
  "bindings": [
    {
      "authLevel": "function",
      "type": "httpTrigger",
      "direction": "in",
      "name": "req",
      "methods": ["get"],
      "route": "logs"
    },
    {
      "type": "http",
      "direction": "out",
      "name": "$return"
    }
  ]
}
```

#### 3.3 `api-azure/logs/__init__.py`の実装

`MIGRATION_CODE_EXAMPLES.md`の「3. Log Serviceの変更」を参照して実装

主要なエンドポイント：
- `GET /api/logs` - ログ一覧取得（日付範囲、ユーザーID、案件IDでフィルタリング）
- `GET /api/logs/{log_id}` - ログ詳細取得

#### 3.4 RAG検索APIにログ保存を統合

`api-azure/search/__init__.py`を修正して、検索実行時にログを保存：

```python
from app.services.log_service import log_service

# RAG検索実行後
log_service.save_rag_log(
    user_id=user_id,
    case_id=case_id,
    input_data=case_info,
    rag_queries=result.get("queries", []),
    referenced_files=result.get("referenced_files", []),
    generated_answer=result.get("answer", ""),
    reasoning=result.get("reasoning", ""),
    processing_time=processing_time,
    model_name="gpt-4o-mini",
    top_k=5,
    status="success"
)
```

#### 3.5 環境変数の設定

```bash
TABLE_STORAGE_CONNECTION_STRING=<Table Storage接続文字列>
LOG_TABLE_NAME=raglogs
```

### 動作確認

```bash
# ログ一覧取得
curl http://localhost:7071/api/logs

# ログ詳細取得
curl http://localhost:7071/api/logs/{log_id}
```

---

## ステップ4: Azure Entra ID認証統合

### 目的
Azure Static Web Appsの認証機能とAzure Functionsを統合する

### 現在の状況
- ⚪ 認証機能は未実装
- ✅ Azure Static Web Appsは認証機能をサポート

### 実装手順

#### 4.1 Azure Entra IDアプリ登録

Azure Portalで以下を実行：

1. **Azure Active Directory** → **アプリの登録** → **新規登録**
2. アプリ名: `RAG案件管理システム`
3. リダイレクトURI: `https://<static-web-app-name>.azurestaticapps.net/.auth/login/aad/callback`
4. **APIの公開** → スコープ追加: `user_impersonation`

#### 4.2 Static Web Appsの認証設定

`staticwebapp.config.json`を作成（プロジェクトルート）：

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
        "userDetailsClaim": "http://schemas.xmlsoap.org/ws/2005/05/identity/claims/name",
        "registration": {
          "openIdIssuer": "https://login.microsoftonline.com/{tenantId}/v2.0",
          "clientIdSettingName": "AZURE_CLIENT_ID",
          "clientSecretSettingName": "AZURE_CLIENT_SECRET"
        }
      }
    }
  }
}
```

#### 4.3 Azure Functionsで認証情報を取得

`api-azure/search/__init__.py`を修正：

```python
import base64
import json

def get_user_from_request(req: func.HttpRequest):
    """Static Web Appsから渡される認証情報を取得"""
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
            "roles": principal.get("userRoles", [])
        }
    except:
        return None

def main(req: func.HttpRequest) -> func.HttpResponse:
    # 認証チェック
    user = get_user_from_request(req)
    if not user:
        return func.HttpResponse(
            json.dumps({"ok": False, "error": "Not authenticated"}),
            mimetype="application/json",
            status_code=401
        )
    
    # 以降の処理...
```

#### 4.4 フロントエンドで認証状態を確認

`frontend-azure/index.html`に認証チェックを追加：

```javascript
// 認証状態を確認
async function checkAuth() {
    try {
        const response = await fetch('/.auth/me');
        const data = await response.json();
        if (data.clientPrincipal) {
            console.log('認証済み:', data.clientPrincipal);
            return data.clientPrincipal;
        } else {
            // 未認証の場合はログインページにリダイレクト
            window.location.href = '/.auth/login/aad';
            return null;
        }
    } catch (error) {
        console.error('認証エラー:', error);
        return null;
    }
}

// ページ読み込み時に認証チェック
document.addEventListener('DOMContentLoaded', async () => {
    await checkAuth();
});
```

### 動作確認

1. Static Web Appsにデプロイ
2. ブラウザでアクセス
3. Azure Entra IDでログイン
4. 認証後にAPIが呼び出せることを確認

---

## ステップ5: Azure Static Web Appsデプロイ

### 目的
Azure Static Web AppsにフロントエンドとAzure Functionsをデプロイする

### 現在の状況
- ✅ `frontend-azure/` - フロントエンド準備済み
- ✅ `api-azure/` - Azure Functions準備済み
- ⚪ デプロイ設定は未完了

### 実装手順

#### 5.1 GitHub Actionsワークフローの作成

`.github/workflows/azure-static-web-apps.yml`を作成：

```yaml
name: Azure Static Web Apps CI/CD

on:
  push:
    branches:
      - main
  pull_request:
    types: [opened, synchronize, reopened, closed]
    branches:
      - main

jobs:
  build_and_deploy_job:
    if: github.event_name == 'push' || (github.event_name == 'pull_request' && github.event.action != 'closed')
    runs-on: ubuntu-latest
    name: Build and Deploy Job
    steps:
      - uses: actions/checkout@v3
        with:
          submodules: true
          lfs: false
      
      - name: Build And Deploy
        id: builddeploy
        uses: Azure/static-web-apps-deploy@v1
        with:
          azure_static_web_apps_api_token: ${{ secrets.AZURE_STATIC_WEB_APPS_API_TOKEN }}
          repo_token: ${{ secrets.GITHUB_TOKEN }}
          action: "upload"
          app_location: "frontend-azure"
          api_location: "api-azure"
          output_location: ""

  close_pull_request_job:
    if: github.event_name == 'pull_request' && github.event.action == 'closed'
    runs-on: ubuntu-latest
    name: Close Pull Request Job
    steps:
      - name: Close Pull Request
        id: closepullrequest
        uses: Azure/static-web-apps-deploy@v1
        with:
          azure_static_web_apps_api_token: ${{ secrets.AZURE_STATIC_WEB_APPS_API_TOKEN }}
          action: "close"
```

#### 5.2 Azure Static Web Appsの作成

Azure PortalまたはAzure CLIで作成：

```bash
# Static Web Apps作成
az staticwebapp create \
  --name swa-ragkanri \
  --resource-group rg-ragkanri \
  --location japaneast \
  --sku Free

# デプロイトークンを取得
az staticwebapp secrets list \
  --name swa-ragkanri \
  --resource-group rg-ragkanri \
  --query properties.apiKey \
  --output tsv
```

#### 5.3 GitHub Secretsの設定

GitHubリポジトリのSettings → Secrets and variables → Actionsで以下を設定：

- `AZURE_STATIC_WEB_APPS_API_TOKEN`: 上記で取得したデプロイトークン

#### 5.4 Azure Functionsのアプリケーション設定

Azure PortalでAzure Functionsのアプリケーション設定に以下を追加：

```bash
OPENAI_API_KEY=<OpenAI APIキー>
BLOB_STORAGE_CONNECTION_STRING=<Blob Storage接続文字列>
TABLE_STORAGE_CONNECTION_STRING=<Table Storage接続文字列>
KNOWLEDGE_CONTAINER_NAME=knowledge-files
INDEX_CONTAINER_NAME=rag-index
LOG_TABLE_NAME=raglogs
CASES_TABLE_NAME=cases
```

#### 5.5 デプロイ実行

```bash
# コードをコミット・プッシュ
git add .
git commit -m "Azure Static Web Appsデプロイ準備"
git push origin main
```

GitHub Actionsが自動的にデプロイを実行します。

### 動作確認

1. Azure PortalでStatic Web AppsのURLを確認
2. ブラウザでアクセス
3. 各APIエンドポイントが動作することを確認

---

## 📝 実装の優先順位

1. **ステップ1: RAG検索API統合** ⭐⭐⭐（最重要）
   - コア機能のため最優先

2. **ステップ2: Knowledge管理API** ⭐⭐
   - Knowledgeファイルの管理に必要

3. **ステップ3: ログ管理API** ⭐⭐
   - 運用・監視に必要

4. **ステップ4: Azure Entra ID認証** ⭐
   - セキュリティ向上

5. **ステップ5: Azure Static Web Appsデプロイ** ⭐⭐⭐
   - 本番環境へのデプロイ

---

## 🔧 トラブルシューティング

### よくある問題

1. **Azure Functionsでローカルファイルにアクセスできない**
   - → Blob Storageを使用するか、一時ディレクトリ（`/tmp`）を使用

2. **認証エラーが発生する**
   - → Static Web Appsの認証設定を確認
   - → Azure Entra IDアプリ登録を確認

3. **デプロイが失敗する**
   - → GitHub Actionsのログを確認
   - → Azure Functionsのアプリケーション設定を確認

---

## 📚 参考資料

- **`AZURE_MIGRATION_GUIDE.md`** - 詳細な移行手順書
- **`MIGRATION_CODE_EXAMPLES.md`** - コード変更例集
- **`Azure.md`** - Azure要件定義書

---

**次のアクション**: ステップ1（RAG検索API統合）から開始してください。

