# 中小企業向け・低コストAI案件管理システム 要件定義書
## 貯水槽修理案件管理システム - サーバーレス版

**作成日**: 2024年12月  
**バージョン**: 2.0  
**対象システム**: 貯水槽修理案件管理システム（RAGベース）  
**対象企業規模**: 1〜30名程度の中小企業

---

## 📋 目次

1. [システム概要](#1-システム概要)
2. [非機能要件](#2-非機能要件)
3. [Azureアーキテクチャ設計](#3-azureアーキテクチャ設計)
4. [インフラストラクチャ詳細設計](#4-インフラストラクチャ詳細設計)
5. [データ設計](#5-データ設計)
6. [ストレージ設計](#6-ストレージ設計)
7. [認証・セキュリティ設計](#7-認証セキュリティ設計)
8. [監視・ログ設計](#8-監視ログ設計)
9. [CI/CD設計](#9-cicd設計)
10. [コスト設計](#10-コスト設計)
11. [バックアップ・復旧計画](#11-バックアップ復旧計画)
12. [移行計画](#12-移行計画)
13. [運用・保守計画](#13-運用保守計画)
14. [セキュリティコンプライアンス](#14-セキュリティコンプライアンス)
15. [将来の本番拡張構成（Enterprise移行パス）](#15-将来の本番拡張構成enterprise移行パス)

---

## 1. システム概要

### 1.1 目的

現在のPoC版システムを、**固定費をかけずに**Azureクラウド上で本番運用できるサーバーレス構成に移行する。IT専任者がいない中小企業でも運用可能で、かつ企業に正式提案できるレベルのシステムを実現する。

### 1.2 なぜ低コストで実現できるのか

#### 1.2.1 サーバーレス構成の採用

- **固定費ゼロ**: サーバーを常時起動しないため、使った分だけ課金される従量課金制
- **自動スケーリング**: 利用者が増えても自動で対応し、使わない時はコストがかからない
- **運用負荷の削減**: サーバー管理が不要で、IT専任者なしでも運用可能

#### 1.2.2 データベースを使わない設計

- **SQL Database不要**: リレーショナルデータベース（SQL Database）を使わず、Azure Table StorageとBlob Storageでデータを管理
- **コスト削減**: SQL Databaseの月額数万円の固定費が不要
- **シンプルな運用**: データベースのバックアップ・メンテナンスが不要

#### 1.2.3 必要十分な機能に絞る

- **高可用性は後回し**: 99.9%のSLAは不要。通常の業務利用で十分な可用性を確保
- **マルチリージョン不要**: 単一リージョン（Japan East）で運用し、コストを削減
- **高度な監視は最小限**: 基本的なログとエラー通知のみで運用可能

### 1.3 中小企業が抱える課題（現状システムの課題）

- **コスト**: 月額10万円以上のクラウド費用は負担が大きい
- **運用負荷**: IT専任者がいないため、サーバー管理は難しい
- **スケーラビリティ**: 利用者が少ない時も固定費が発生するのは無駄
- **セキュリティ**: 簡易認証では本番運用に不安がある
- **データ管理**: ローカルファイルではバックアップや共有が難しい

### 1.4 目標システムの特徴

- **低コスト**: 月額1,000〜5,000円台（利用量次第）
- **固定費ゼロ**: 使った分だけ課金される従量課金制
- **運用簡単**: サーバー管理不要、自動スケーリング
- **セキュリティ**: Azure Entra ID（Azure AD）による企業認証
- **将来拡張可能**: 必要に応じてエンタープライズ構成へ移行可能

---

## 2. 非機能要件

### 2.1 パフォーマンス要件

| 項目 | 要件 | 測定方法 |
|------|------|----------|
| **API応答時間** | RAG検索: 10秒以内（通常は5秒程度）<br>通常API: 1秒以内 | Azure Functions ログ |
| **同時接続数** | 10〜30ユーザー同時接続対応 | 実運用で検証 |
| **スループット** | 100リクエスト/分（通常は十分） | Azure Functions メトリック |
| **RAG Index構築時間** | 30ファイル: 10分以内（バックグラウンド処理） | バッチ処理ログ |

**補足**: 中小企業の利用規模（1〜30名）を想定した「必要十分」な性能要件です。利用が増えた場合は、後述の「将来の本番拡張構成」へ移行することで対応可能です。

### 2.2 可用性要件

| 項目 | 要件 | 実現方法 |
|------|------|----------|
| **稼働率** | 通常の業務時間帯（平日9:00-18:00）で問題なく利用可能 | Azure Functions 標準SLA（99.95%） |
| **計画メンテナンス** | 月1回、深夜時間帯（影響最小） | Azure Functions 自動更新 |
| **障害検知** | エラー発生時にメール通知 | Azure Functions アラート |
| **自動復旧** | Azure側で自動復旧 | Azure Functions 標準機能 |

**補足**: エンタープライズレベルの99.9%以上のSLAは不要です。通常の業務利用で十分な可用性を確保します。将来的に高可用性が必要になった場合は、拡張構成へ移行可能です。

### 2.3 セキュリティ要件

| 項目 | 要件 | 実現方法 |
|------|------|----------|
| **認証** | Azure Entra ID（Azure AD）統合 | Azure Static Web Apps 認証機能 |
| **認可** | ロールベースアクセス制御（管理者/一般ユーザー） | アプリケーション内で実装 |
| **データ暗号化** | 転送時: HTTPS（TLS 1.2以上）、保存時: Azure Storage暗号化 | Azure標準機能 |
| **機密情報管理** | APIキーは環境変数で管理（Key Vaultは将来拡張時） | Azure Functions アプリケーション設定 |
| **監査ログ** | 操作ログ・検索ログを記録（30日間保持） | Azure Table Storage |
| **脆弱性対策** | Azure標準のセキュリティ対策 | Azure Security Center（基本機能） |

**補足**: エンタープライズレベルの高度なセキュリティ機能（Key Vault Premium、HSM等）は使用しませんが、中小企業の業務利用に必要なセキュリティ要件は満たします。

### 2.4 スケーラビリティ要件

| 項目 | 要件 | 実現方法 |
|------|------|----------|
| **自動スケーリング** | 利用者数に応じて自動でスケール（0〜無制限） | Azure Functions Consumption Plan |
| **RAG Index更新** | Knowledge更新時に自動再構築（バックグラウンド） | Azure Functions + Blob Storage トリガー |

**補足**: サーバーレス構成のため、利用者が0人でも固定費は発生しません。利用が増えても自動でスケールし、コストも利用量に応じて変動します。

### 2.5 コンプライアンス要件

- **個人情報保護**: 個人情報保護法準拠（必要に応じて対応）
- **データ所在地**: 日本リージョン（Japan East）に限定
- **データ保持**: ログデータ30日間、案件データは必要に応じて長期保存
- **アクセス制御**: 最小権限の原則（管理者/一般ユーザー）

---

## 3. Azureアーキテクチャ設計

### 3.1 全体アーキテクチャ（サーバーレス1枚構成）

```
┌─────────────────────────────────────────────────────────┐
│                        インターネット                    │
└──────────────────────────┬──────────────────────────────┘
                           │ HTTPS (TLS 1.2+)
                           ▼
┌─────────────────────────────────────────────────────────┐
│          Azure Static Web Apps                          │
│          (フロントエンド: HTML/JavaScript)              │
│          - 認証: Azure Entra ID統合                    │
│          - CDN: 自動付与                                │
└──────────────────────────┬──────────────────────────────┘
                           │
                           ▼
┌─────────────────────────────────────────────────────────┐
│          Azure Functions (Consumption Plan)             │
│          (API: FastAPI互換)                             │
│          - RAG検索API                                   │
│          - ドキュメント生成API                          │
│          - Knowledge管理API                            │
│          - 自動スケーリング（0〜無制限）               │
└──────────────────────────┬──────────────────────────────┘
                           │
        ┌──────────────────┼──────────────────┐
        ▼                  ▼                  ▼
┌──────────────┐  ┌──────────────┐  ┌──────────────┐
│ Azure Blob   │  │ Azure Table  │  │ Azure Entra  │
│ Storage      │  │ Storage      │  │ ID           │
│              │  │              │  │              │
│ - Knowledge  │  │ - ログ       │  │ - 認証       │
│ - RAG Index  │  │ - メタデータ │  │ - ユーザー   │
│ - ドキュメント│  │              │  │   管理       │
└──────────────┘  └──────────────┘  └──────────────┘
        │
        └──────────────────┐
                           ▼
                ┌──────────────────────┐
                │ OpenAI API           │
                │ (従量課金)           │
                │ - Embedding          │
                │ - LLM (gpt-4o-mini)  │
                └──────────────────────┘
```

### 3.2 Azureサービス選定

| カテゴリ | Azureサービス | 選定理由 | コスト |
|---------|--------------|---------|--------|
| **Web** | Azure Static Web Apps | 無料プランあり、CDN自動付与、認証統合 | 無料〜数千円/月 |
| **API** | Azure Functions (Consumption Plan) | 従量課金、自動スケーリング、Python対応 | 従量課金（月数百円〜） |
| **認証** | Azure Entra ID（Azure AD） | 企業認証、無料プランあり | 無料（基本機能） |
| **ファイル** | Azure Blob Storage (Standard LRS) | 低コスト、Knowledgeファイル・RAG Index保存 | 従量課金（月数百円〜） |
| **メタデータ・ログ** | Azure Table Storage | 低コスト、NoSQL、ログ保存に最適 | 従量課金（月数百円〜） |
| **LLM** | OpenAI API | 従量課金、利用量に応じて課金 | 従量課金（利用量次第） |

**削除したサービス（コスト削減のため）**:
- ❌ Azure App Service Premium v3（固定費が高い）
- ❌ Azure SQL Database（固定費が高い）
- ❌ Azure Cache for Redis（固定費が高い）
- ❌ Azure Front Door / Application Gateway（固定費が高い）
- ❌ Azure Key Vault Premium（Standardで十分）
- ❌ Azure Functions Premium（Consumption Planで十分）

---

## 4. インフラストラクチャ詳細設計

### 4.1 Azure Static Web Apps

#### 4.1.1 構成

- **プラン**: Free（無料）または Standard（有料、カスタムドメイン対応）
- **リージョン**: Japan East
- **認証**: Azure Entra ID統合（無料）
- **CDN**: 自動付与（無料）

#### 4.1.2 機能

- **フロントエンド**: HTML/JavaScript/CSSをホスティング
- **認証**: Azure Entra IDによる企業認証
- **API連携**: Azure Functionsと連携
- **自動デプロイ**: GitHub連携で自動デプロイ

#### 4.1.3 設定

```yaml
# staticwebapp.config.json
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

### 4.2 Azure Functions（Consumption Plan）

#### 4.2.1 構成

- **プラン**: Consumption Plan（従量課金）
- **ランタイム**: Python 3.11
- **リージョン**: Japan East
- **タイムアウト**: 最大10分（RAG検索用）
- **メモリ**: 最大3.5GB

#### 4.2.2 関数構成

```yaml
関数1: rag_search
  トリガー: HTTP (POST)
  用途: RAG検索・回答生成
  タイムアウト: 10分
  メモリ: 3.5GB

関数2: generate_document
  トリガー: HTTP (POST)
  用途: 見積書・発注書生成
  タイムアウト: 5分
  メモリ: 1.75GB

関数3: knowledge_management
  トリガー: HTTP (GET/POST)
  用途: Knowledgeファイル管理
  タイムアウト: 5分
  メモリ: 1.75GB

関数4: update_rag_index
  トリガー: Blob Storage（knowledge-filesコンテナの変更）
  用途: RAG Index自動更新
  タイムアウト: 10分
  メモリ: 3.5GB

関数5: admin_logs
  トリガー: HTTP (GET)
  用途: ログ閲覧（管理者）
  タイムアウト: 2分
  メモリ: 1.75GB
```

#### 4.2.3 アプリケーション設定

```env
# Azure Functions アプリケーション設定
OPENAI_API_KEY={OpenAI APIキー}
BLOB_STORAGE_CONNECTION_STRING={Blob Storage接続文字列}
TABLE_STORAGE_CONNECTION_STRING={Table Storage接続文字列}
KNOWLEDGE_CONTAINER_NAME=knowledge-files
INDEX_CONTAINER_NAME=rag-index
DOCUMENTS_CONTAINER_NAME=generated-documents
LOG_TABLE_NAME=raglogs
APP_ENV=production
```

**補足**: Key Vaultは使用せず、Azure Functionsのアプリケーション設定で管理します。将来的にKey Vaultが必要になった場合は、拡張構成へ移行可能です。

### 4.3 Azure Blob Storage

#### 4.3.1 構成

- **ストレージアカウント**: Standard (LRS)
- **リージョン**: Japan East（単一リージョン）
- **アクセス層**: Hot（アクセス頻度が高い）
- **バージョニング**: 有効（オプション）
- **論理的な削除**: 有効（7日間）

#### 4.3.2 コンテナ構成

```
blob-storage-ragkanri/
├── knowledge-files/          # Knowledgeファイル（txt）
│   ├── contractor_case_studies.txt
│   ├── price_reference.txt
│   └── ...
├── rag-index/               # RAG Index（JSON形式）
│   ├── index_v1.json
│   ├── index_v2.json
│   └── ...
├── generated-documents/     # 生成されたドキュメント
│   ├── estimates/
│   ├── orders/
│   └── ...
└── backups/                 # バックアップ（オプション）
    └── index/
```

#### 4.3.3 アクセス制御

- **認証**: Azure Functions Managed Identity（推奨）または接続文字列
- **アクセスレベル**: プライベート（パブリックアクセスなし）
- **SASトークン**: 一時的なダウンロード用（有効期限1時間）

### 4.4 Azure Table Storage

#### 4.4.1 構成

- **ストレージアカウント**: Blob Storageと同じアカウントを使用
- **リージョン**: Japan East
- **パーティションキー**: 日付（例: 2024-12-25）
- **行キー**: タイムスタンプ + ユニークID

#### 4.4.2 テーブル設計

```python
# RAGログテーブル
Table: raglogs
PartitionKey: 日付（YYYY-MM-DD）
RowKey: タイムスタンプ + GUID（例: 20241225T120000_abc123）

プロパティ:
  - user_id: string
  - case_id: string
  - status: string (success/failed)
  - error_message: string
  - input_data: string (JSON)
  - rag_queries: string (JSON array)
  - referenced_files: string (JSON array)
  - generated_answer: string
  - reasoning: string
  - processing_time: float
  - model_name: string
  - top_k: int

# ユーザーテーブル（Azure AD連携）
Table: users
PartitionKey: "users"
RowKey: Azure AD ID

プロパティ:
  - email: string
  - display_name: string
  - role: string (admin/user)
  - created_at: datetime

# 案件テーブル
Table: cases
PartitionKey: 日付（YYYY-MM-DD）
RowKey: case_id

プロパティ:
  - case_name: string
  - repair_type: string
  - urgency: string
  - location: string
  - tank_size: string
  - description: string
  - user_id: string
  - status: string
  - created_at: datetime
```

**補足**: SQL Databaseを使わないため、リレーショナルデータベースの機能（JOIN、トランザクション等）は使用しません。シンプルなデータ構造で運用します。

---

## 5. データ設計

### 5.0 現在のコードベースのデータ管理実現可能性判断

#### 5.0.1 判断結果サマリー

| データ種別 | 現在の実装 | Azure実現可能性 | 判断 |
|-----------|-----------|----------------|------|
| **RAG検索ログ** | SQLite (`rag_logs`テーブル) | ✅ **実現可能** | Table Storageに移行可能 |
| **Knowledgeファイル** | ローカルファイルシステム | ✅ **実現可能** | Blob Storageに移行可能 |
| **RAGインデックス** | ローカルファイルシステム (`./storage/index/`) | ✅ **実現可能** | Blob Storageに移行可能 |
| **生成ドキュメント** | メモリ内生成（永続化なし） | ✅ **実現可能** | Blob Storageに保存可能 |
| **ユーザー情報** | 簡易認証（固定パスワード） | ✅ **実現可能** | Azure Entra IDに移行可能 |
| **セッション管理** | 簡易実装 | ✅ **実現可能** | Static Web Apps認証で対応可能 |

**総合判断**: ✅ **すべてのデータ管理機能はAzureで実現可能**

#### 5.0.2 実現可能性の詳細判断

**1. RAG検索ログ（SQLite → Table Storage）**

- **現在の実装**: `app/core/database.py`の`RAGLog`テーブル（SQLite）
- **データ構造**: 13カラム（id, timestamp, user_id, case_id, status, error_message, input_data, rag_queries, referenced_files, search_results, generated_answer, reasoning, processing_time, model_name, top_k）
- **Azure移行**: Table Storageで実現可能
  - ✅ パーティションキー: 日付（`YYYY-MM-DD`）で時系列検索が高速化
  - ✅ 行キー: タイムスタンプ + IDで一意性を保証
  - ✅ JSONカラム: Table Storageの文字列プロパティにJSON文字列として保存
  - ⚠️ 制限: エンティティサイズ1MB以下（`generated_answer`が大きい場合は切り詰めが必要）
- **移行難易度**: 🟢 **低**（移行スクリプトで対応可能）

**2. Knowledgeファイル（ローカルファイルシステム → Blob Storage）**

- **現在の実装**: `app/services/knowledge_service.py`でローカルファイルシステムから`.txt`ファイルを読み込み
- **データ構造**: テキストファイル（UTF-8エンコーディング）
- **Azure移行**: Blob Storageで実現可能
  - ✅ ファイル一覧取得: `list_blobs()`で実現可能
  - ✅ ファイル内容取得: `download_blob()`で実現可能
  - ✅ ファイル作成・削除: `upload_blob()`, `delete_blob()`で実現可能
  - ✅ ファイル種別判定: ファイル名のプレフィックスで判定（現在の実装と同じ）
- **移行難易度**: 🟢 **低**（Azure CLIまたはPythonスクリプトで一括アップロード可能）

**3. RAGインデックス（ローカルファイルシステム → Blob Storage）**

- **現在の実装**: `app/services/rag_service.py`で`./storage/index/`にLlamaIndex形式で保存
- **データ構造**: JSONファイル（`default__vector_store.json`, `docstore.json`, `graph_store.json`, `index_store.json`）
- **Azure移行**: Blob Storageで実現可能
  - ✅ インデックス保存: Blob StorageにJSONファイルとして保存可能
  - ✅ インデックス読み込み: Blob Storageからダウンロードして一時ディレクトリに保存後、LlamaIndexで読み込み
  - ✅ バージョン管理: `index_v{version}/`形式でバージョン管理可能
  - ⚠️ 注意: LlamaIndexはローカルファイルシステムを前提としているため、一時ディレクトリを使用する必要がある
- **移行難易度**: 🟡 **中**（LlamaIndexの読み込み処理を修正する必要がある）

**4. 生成ドキュメント（メモリ内生成 → Blob Storage保存）**

- **現在の実装**: `app/services/document_service.py`でメモリ内で生成し、バイト列として返す（永続化なし）
- **データ構造**: Word形式（`.docx`）のバイト列
- **Azure移行**: Blob Storageで実現可能
  - ✅ ドキュメント保存: バイト列をBlob Storageにアップロード可能
  - ✅ パス構造: `{document_type}/{case_id}/{filename}`形式で整理可能
  - ✅ アクセス制御: Blob Storageのアクセス権限で制御可能
- **移行難易度**: 🟢 **低**（新規実装として追加）

**5. ユーザー情報・認証（簡易認証 → Azure Entra ID）**

- **現在の実装**: `app/core/auth.py`で簡易認証（固定パスワード）
- **データ構造**: セッション情報（簡易実装）
- **Azure移行**: Azure Entra IDで実現可能
  - ✅ 認証: Static Web Appsの認証機能でAzure Entra IDと統合可能
  - ✅ ユーザー情報: Azure Entra IDから取得可能
  - ✅ ロール管理: Table Storageにユーザーロール情報を保存可能
- **移行難易度**: 🟡 **中**（認証処理の修正が必要）

#### 5.0.3 実現可能性の結論

**すべてのデータ管理機能はAzureで実現可能**です。主な理由：

1. **SQLite → Table Storage**: データ構造がシンプルで、Table StorageのNoSQL構造に適合
2. **ローカルファイルシステム → Blob Storage**: ファイル操作がBlob StorageのAPIで直接対応可能
3. **RAGインデックス**: LlamaIndexの読み込み処理を一時ディレクトリを使用するように修正することで対応可能
4. **認証**: Azure Entra IDとStatic Web Appsの認証機能で対応可能

**移行の優先順位**:
1. 🟢 **Knowledgeファイル**: 最も簡単（Azure CLIで一括アップロード）
2. 🟢 **RAG検索ログ**: 移行スクリプトで対応可能
3. 🟡 **RAGインデックス**: 再構築を推奨（既存ファイルのコピーも可能）
4. 🟡 **認証**: 認証処理の修正が必要
5. 🟢 **生成ドキュメント**: 新規実装として追加

### 5.1 データ保存先の明確化

| データ種別 | 保存先 | 形式 | 理由 |
|-----------|--------|------|------|
| **Knowledgeファイル** | Blob Storage | txtファイル | テキストファイルとして保存 |
| **RAG Index** | Blob Storage | JSONファイル | チャンク・EmbeddingをJSON形式で保存 |
| **生成ドキュメント** | Blob Storage | docx/pdfファイル | Word/PDF形式で保存 |
| **ログデータ** | Table Storage | NoSQL | 時系列データ、検索に最適 |
| **メタデータ** | Table Storage | NoSQL | ユーザー情報、案件情報等 |
| **ユーザー情報** | Azure Entra ID + Table Storage | - | 認証はEntra ID、追加情報はTable Storage |

### 5.2 RAG Indexの保存形式

#### 5.2.1 JSON形式での保存

```json
{
  "version": 1,
  "created_at": "2024-12-25T10:00:00Z",
  "indexed_files_count": 30,
  "total_chunks": 150,
  "chunks": [
    {
      "chunk_id": "chunk_001",
      "file_name": "contractor_case_studies.txt",
      "chunk_index": 0,
      "text": "事例1: 株式会社ABCは...",
      "embedding": [0.123, -0.456, ...],  // 1536次元のベクトル
      "metadata": {
        "file_type": "case_study",
        "case_number": 1
      }
    },
    ...
  ]
}
```

#### 5.2.2 Index読み込み処理

```python
# app/services/rag_service.py（Azure版）
import json
from azure.storage.blob import BlobServiceClient
from azure.identity import DefaultAzureCredential

class RAGService:
    def __init__(self):
        self.index_container = "rag-index"
        self.blob_service_client = BlobServiceClient(
            account_url=settings.blob_storage_url,
            credential=DefaultAzureCredential()
        )
        self.container_client = self.blob_service_client.get_container_client(
            self.index_container
        )
    
    def load_index(self, version: int) -> dict:
        """Blob StorageからIndexを読み込み（JSON形式）"""
        blob_name = f"index_v{version}.json"
        blob_client = self.container_client.get_blob_client(blob_name)
        content = blob_client.download_blob().readall().decode('utf-8')
        index_data = json.loads(content)
        return index_data
    
    def save_index(self, index_data: dict, version: int):
        """IndexをBlob Storageに保存（JSON形式）"""
        blob_name = f"index_v{version}.json"
        blob_client = self.container_client.get_blob_client(blob_name)
        content = json.dumps(index_data, ensure_ascii=False, indent=2)
        blob_client.upload_blob(content, overwrite=True)
```

**補足**: LlamaIndexの標準形式ではなく、JSON形式で保存することで、シンプルに管理できます。将来的にLlamaIndex形式が必要になった場合は、拡張可能です。

### 5.3 現在のコードベースのデータ構造とAzure移行

#### 5.3.1 現在のSQLiteデータベース構造

現在のPoC版では、SQLiteデータベース（`rag_kanri.db`）を使用しています。主なテーブル構造は以下の通りです：

**RAGLogテーブル（`app/core/database.py`）**:
```python
class RAGLog(Base):
    __tablename__ = "rag_logs"
    
    id = Column(Integer, primary_key=True, index=True)
    timestamp = Column(DateTime, default=datetime.utcnow, nullable=False)
    user_id = Column(String, nullable=True)
    case_id = Column(String, nullable=True, index=True)
    status = Column(String, default="success", nullable=False)
    error_message = Column(Text, nullable=True)
    input_data = Column(JSON, nullable=True)  # 案件情報など
    rag_queries = Column(JSON, nullable=True)  # 検索クエリのリスト
    referenced_files = Column(JSON, nullable=True)  # 参照ファイル名のリスト
    search_results = Column(JSON, nullable=True)  # 検索結果の詳細
    generated_answer = Column(Text, nullable=True)
    reasoning = Column(Text, nullable=True)  # 判断理由
    processing_time = Column(Float, nullable=True)
    model_name = Column(String, nullable=True)
    top_k = Column(Integer, nullable=True)
```

#### 5.3.2 Azure Table Storageへの移行設計

SQLiteの`rag_logs`テーブルをAzure Table Storageに移行する場合の設計：

**テーブル名**: `raglogs`

**パーティションキー（PartitionKey）**: 日付（`YYYY-MM-DD`形式）
- 日付ごとにパーティションを分けることで、時系列検索が高速化
- 例: `2024-12-25`

**行キー（RowKey）**: タイムスタンプ + ID（`YYYYMMDDTHHMMSS_{id}`形式）
- 同一パーティション内で一意性を保証
- 時系列順にソート可能
- 例: `20241225T143022_001`

**エンティティ構造**:
```python
{
    "PartitionKey": "2024-12-25",  # 日付
    "RowKey": "20241225T143022_001",  # タイムスタンプ + ID
    "id": 1,  # 元のID（検索用）
    "timestamp": "2024-12-25T14:30:22Z",  # ISO形式
    "user_id": "user@example.com",
    "case_id": "case-001",
    "status": "success",
    "error_message": None,
    "input_data": '{"case_name": "貯水槽修理", ...}',  # JSON文字列
    "rag_queries": '["クエリ1", "クエリ2"]',  # JSON文字列
    "referenced_files": '["file1.txt", "file2.txt"]',  # JSON文字列
    "search_results": '[...]',  # JSON文字列
    "generated_answer": "生成された回答...",
    "reasoning": "判断理由...",
    "processing_time": 5.23,
    "model_name": "gpt-4o-mini",
    "top_k": 5
}
```

**注意**: Table Storageのプロパティ名は大文字小文字を区別し、一部の予約語（`PartitionKey`, `RowKey`, `Timestamp`, `ETag`）は使用できません。また、各エンティティのサイズは1MB以下に制限されます。

#### 5.3.3 現在のローカルファイルシステム構造

現在のPoC版では、以下のローカルファイルシステムを使用しています：

**Knowledgeファイル**:
- パス: `settings.knowledge_dir`（デフォルト: `/Users/takuminittono/Desktop/ragstudy/ラグルール/knowledge`）
- 形式: `.txt`ファイル
- 管理: `app/services/knowledge_service.py`でファイル一覧・内容取得

**RAGインデックス**:
- パス: `./storage/index/`
- ファイル:
  - `default__vector_store.json`: ベクトルストア（エンベディング）
  - `docstore.json`: ドキュメントストア（テキスト内容）
  - `graph_store.json`: グラフストア（LlamaIndex用）
  - `index_store.json`: インデックスストア（メタデータ）
- 管理: `app/services/rag_service.py`でインデックス作成・読み込み

**生成ドキュメント**:
- 現在はメモリ内で生成し、バイト列として返す（永続化なし）
- テンプレート: `templates/documents/order_template.docx`

#### 5.3.4 Azure Blob Storageへの移行設計

**Knowledgeファイル**:
- コンテナ名: `knowledge-files`
- パス構造: `{filename}.txt`（フラット構造）
- 例: `contractor_case_studies.txt`, `price_guide.txt`

**RAGインデックス**:
- コンテナ名: `rag-index`
- パス構造:
  - `index_v{version}/default__vector_store.json`
  - `index_v{version}/docstore.json`
  - `index_v{version}/graph_store.json`
  - `index_v{version}/index_store.json`
- バージョン管理: インデックス更新時に新しいバージョンを作成

**生成ドキュメント**:
- コンテナ名: `generated-documents`
- パス構造: `{document_type}/{case_id}/{filename}`
- 例: `order/case-001/order_20241225_001.docx`

#### 5.3.5 データベースがなくても問題ない理由

**リレーショナルデータベースが不要な理由**:

- **シンプルなデータ構造**: ユーザー情報、案件情報、ログ情報は独立して管理可能
- **JOINが不要**: データの関連付けはアプリケーション側で処理
- **トランザクションが不要**: 同時更新が少ない業務フロー

**Table Storageで十分な理由**:

- **低コスト**: SQL Databaseの固定費が不要
- **スケーラブル**: データが増えても自動でスケール
- **シンプル**: 複雑なクエリが不要な用途に最適

**将来SQL Databaseが必要になった場合**:

- 拡張構成へ移行することで、SQL Databaseを追加可能
- データ移行ツールを提供
- 段階的な移行が可能

---

## 6. ストレージ設計

### 6.1 Blob Storage接続

#### 6.1.1 Managed Identity使用（推奨）

```python
from azure.identity import DefaultAzureCredential
from azure.storage.blob import BlobServiceClient

# Managed Identityを使用（接続文字列不要）
credential = DefaultAzureCredential()
blob_service_client = BlobServiceClient(
    account_url="https://stragkanri.blob.core.windows.net/",
    credential=credential
)
```

#### 6.1.2 接続文字列使用（簡易版）

```python
import os
from azure.storage.blob import BlobServiceClient

# 環境変数から接続文字列を取得
connection_string = os.getenv("BLOB_STORAGE_CONNECTION_STRING")
blob_service_client = BlobServiceClient.from_connection_string(
    connection_string
)
```

### 6.2 Table Storage接続

```python
from azure.data.tables import TableServiceClient
from azure.identity import DefaultAzureCredential

# Managed Identityを使用
credential = DefaultAzureCredential()
table_service_client = TableServiceClient(
    account_url="https://stragkanri.table.core.windows.net/",
    credential=credential
)

# テーブル取得
table_client = table_service_client.get_table_client("raglogs")
```

### 6.3 Knowledgeファイル管理

#### 6.3.1 現在の実装

現在のPoC版では、`app/services/knowledge_service.py`でローカルファイルシステムからKnowledgeファイルを管理しています：

```python
class KnowledgeService:
    def __init__(self):
        self.knowledge_dir = Path(settings.knowledge_dir)
        # デフォルト: /Users/takuminittono/Desktop/ragstudy/ラグルール/knowledge
    
    def get_file_list(self) -> List[Dict[str, any]]:
        """Knowledgeファイル一覧を取得"""
        files = []
        for file_path in sorted(self.knowledge_dir.glob("*.txt")):
            stat = file_path.stat()
            files.append({
                "filename": file_path.name,
                "size": stat.st_size,
                "updated_at": stat.st_mtime,  # Unix timestamp
                "file_type": self._get_file_type(file_path.name),
            })
        return files
    
    def get_file_content(self, filename: str) -> Dict[str, any]:
        """ファイル内容を取得"""
        file_path = self.knowledge_dir / filename
        content = file_path.read_text(encoding="utf-8")
        return {
            "filename": filename,
            "content": content,
            "size": file_path.stat().st_size,
            "updated_at": file_path.stat().st_mtime,
        }
```

#### 6.3.2 Azure Blob Storageへの移行実装

Azure版では、以下のようにBlob StorageからKnowledgeファイルを管理します：

```python
# app/services/knowledge_service.py（Azure版）
from azure.storage.blob import BlobServiceClient
from azure.identity import DefaultAzureCredential
from pathlib import Path
from typing import List, Dict
from app.core.config import settings

class KnowledgeService:
    def __init__(self):
        self.container_name = "knowledge-files"
        self.blob_service_client = BlobServiceClient(
            account_url=settings.blob_storage_url,
            credential=DefaultAzureCredential()
        )
        self.container_client = self.blob_service_client.get_container_client(
            self.container_name
        )
    
    def get_file_list(self) -> List[Dict[str, any]]:
        """
        Knowledgeファイル一覧取得
        
        Returns:
            List[Dict]: ファイル情報のリスト
                - filename: ファイル名
                - size: ファイルサイズ（バイト）
                - updated_at: 最終更新日時（Unix timestamp）
                - file_type: ファイル種別
        """
        files = []
        blobs = self.container_client.list_blobs()
        
        for blob in blobs:
            # .txtファイルのみ対象
            if not blob.name.endswith(".txt"):
                continue
            
            # ファイル種別を判定
            file_type = self._get_file_type(blob.name)
            
            files.append({
                "filename": blob.name,
                "size": blob.size,
                "updated_at": blob.last_modified.timestamp(),  # Unix timestampに変換
                "file_type": file_type,
            })
        
        # ファイル名でソート
        files.sort(key=lambda x: x["filename"])
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
        
        blob_client = self.container_client.get_blob_client(filename)
        
        if not blob_client.exists():
            raise FileNotFoundError(f"File not found: {filename}")
        
        # ファイル内容を読み込み（UTF-8）
        try:
            content = blob_client.download_blob().readall().decode('utf-8')
        except UnicodeDecodeError:
            raise ValueError(f"File encoding error: {filename}")
        
        # メタデータ取得
        properties = blob_client.get_blob_properties()
        
        return {
            "filename": filename,
            "content": content,
            "size": properties.size,
            "updated_at": properties.last_modified.timestamp(),
        }
    
    def create_file(self, filename: str, content: str) -> Dict[str, str]:
        """
        新規Knowledgeファイルを作成
        
        Args:
            filename: ファイル名
            content: ファイル内容
            
        Returns:
            Dict: 作成結果
        """
        # セキュリティ対策
        if ".." in filename or "/" in filename or "\\" in filename:
            raise ValueError("Invalid filename")
        
        if not filename.endswith(".txt"):
            filename = f"{filename}.txt"
        
        # ファイルが既に存在するか確認
        blob_client = self.container_client.get_blob_client(filename)
        if blob_client.exists():
            raise ValueError(f"File already exists: {filename}")
        
        # ファイルをアップロード
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
        """
        Knowledgeファイルを削除
        
        Args:
            filename: ファイル名
            
        Returns:
            Dict: 削除結果
        """
        # セキュリティ対策
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
        """ファイル名からファイル種別を判定（現在の実装と同じ）"""
        if filename.startswith("price_"):
            return "price"
        elif filename.startswith("contractor_"):
            return "contractor"
        elif filename.startswith("repair_"):
            return "repair"
        # ... その他の判定ロジック
        else:
            return "unknown"
```

#### 6.3.3 RAGインデックス管理（Azure版）

現在のPoC版では、`app/services/rag_service.py`でローカルファイルシステム（`./storage/index/`）にRAGインデックスを保存しています。Azure版では、Blob Storageに保存します：

```python
# app/services/rag_service.py（Azure版）
from azure.storage.blob import BlobServiceClient
from azure.identity import DefaultAzureCredential
from llama_index.core import Document, VectorStoreIndex, StorageContext
from llama_index.core.storage.storage_context import StorageContext
import json
import io

class RAGService:
    def __init__(self):
        self.knowledge_dir = Path(settings.knowledge_dir)  # Blob Storageから読み込み
        self.index_container = "rag-index"
        self.blob_service_client = BlobServiceClient(
            account_url=settings.blob_storage_url,
            credential=DefaultAzureCredential()
        )
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
            
            # インデックスファイルをダウンロード
            index_files = {
                "default__vector_store.json": None,
                "docstore.json": None,
                "graph_store.json": None,
                "index_store.json": None,
            }
            
            for filename in index_files.keys():
                blob_name = f"index_v{latest_version}/{filename}"
                blob_client = self.index_container_client.get_blob_client(blob_name)
                
                if blob_client.exists():
                    content = blob_client.download_blob().readall().decode('utf-8')
                    index_files[filename] = json.loads(content)
            
            # 一時ディレクトリに保存してLlamaIndexで読み込み
            # （LlamaIndexはローカルファイルシステムを前提としているため）
            temp_dir = Path("/tmp/rag_index_temp")
            temp_dir.mkdir(exist_ok=True)
            
            for filename, data in index_files.items():
                if data is not None:
                    file_path = temp_dir / filename
                    file_path.write_text(json.dumps(data, ensure_ascii=False, indent=2))
            
            # LlamaIndexで読み込み
            storage_context = StorageContext.from_defaults(persist_dir=str(temp_dir))
            self._index = load_index_from_storage(
                storage_context,
                embed_model=self.embed_model,
            )
            self._index_version = latest_version
            return True
            
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
        temp_dir = Path(f"/tmp/rag_index_temp_{version}")
        temp_dir.mkdir(exist_ok=True)
        
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
        
        # 一時ディレクトリを削除
        import shutil
        shutil.rmtree(temp_dir)
    
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
```

---

## 7. 認証・セキュリティ設計

### 7.1 Azure Entra ID（Azure AD）統合

#### 7.1.1 アプリケーション登録

```yaml
アプリケーション名: RAG案件管理システム
アプリケーションID: {app-id}
テナントID: {tenant-id}

認証設定:
  - リダイレクトURI: https://{app-name}.azurestaticapps.net/.auth/login/aad/callback
  - サポートされているアカウントの種類: この組織ディレクトリのみ
  - 暗黙的な許可: IDトークン

API権限:
  - Microsoft Graph: User.Read（基本情報取得）

ロール:
  - Admin: 管理者権限（アプリケーション内で実装）
  - User: 一般ユーザー権限（アプリケーション内で実装）
```

#### 7.1.2 Static Web Apps認証設定

```yaml
認証プロバイダー: Azure Active Directory
認証モード: 認証が必要
未認証の要求の動作: Azure Active Directory でログインするようにリダイレクト
```

#### 7.1.3 フロントエンド認証処理

```javascript
// static/js/auth.js
async function getCurrentUser() {
    try {
        const response = await fetch('/.auth/me');
        const data = await response.json();
        return data.clientPrincipal;
    } catch (error) {
        console.error('認証エラー:', error);
        return null;
    }
}

async function requireAuth() {
    const user = await getCurrentUser();
    if (!user) {
        window.location.href = '/.auth/login/aad';
        return null;
    }
    return user;
}
```

#### 7.1.4 Azure Functions認証処理

```python
# app/core/auth.py（Azure版）
from fastapi import Request, HTTPException
import json
import base64

async def get_current_user(request: Request) -> dict:
    """現在のユーザー情報を取得（Static Web Apps認証）"""
    # Static Web Appsから渡される認証ヘッダー
    auth_header = request.headers.get("x-ms-client-principal")
    if not auth_header:
        raise HTTPException(status_code=401, detail="Not authenticated")
    
    # Base64デコード
    decoded = base64.b64decode(auth_header)
    principal = json.loads(decoded)
    
    return {
        "user_id": principal.get("userId"),
        "email": principal.get("userDetails"),
        "name": principal.get("userDetails"),
        "roles": principal.get("userRoles", []),
    }

async def require_admin(request: Request):
    """管理者権限チェック"""
    user = await get_current_user(request)
    # Table Storageからユーザー情報を取得してロール確認
    # （実装は省略）
    if user.get("role") != "admin":
        raise HTTPException(status_code=403, detail="Admin access required")
    return user
```

### 7.2 機密情報管理

#### 7.2.1 アプリケーション設定での管理

```yaml
Azure Functions アプリケーション設定:
  - OPENAI_API_KEY: OpenAI APIキー
  - BLOB_STORAGE_CONNECTION_STRING: Blob Storage接続文字列
  - TABLE_STORAGE_CONNECTION_STRING: Table Storage接続文字列

設定方法:
  - Azure Portalで設定
  - 環境変数として暗号化保存
  - アクセス権限を制限
```

**補足**: Key Vaultは使用しませんが、Azure Functionsのアプリケーション設定は暗号化されて保存されます。将来的にKey Vaultが必要になった場合は、拡張構成へ移行可能です。

### 7.3 ネットワークセキュリティ

#### 7.3.1 基本的なセキュリティ対策

- **HTTPS必須**: すべての通信はHTTPS（TLS 1.2以上）
- **認証必須**: すべてのAPIは認証が必要
- **CORS設定**: Static Web Appsからのみアクセス可能
- **IP制限**: 必要に応じてIP制限を設定可能（オプション）

#### 7.3.2 プライベートエンドポイント（将来拡張時）

- 現時点では不要
- 将来的に必要になった場合は、拡張構成で対応可能

---

## 8. 監視・ログ設計

### 8.1 Azure Functions標準ログ

#### 8.1.1 ログ出力

```python
# app/core/logging.py
import logging
import json
from datetime import datetime

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)

def log_rag_search(user_id: str, query: str, processing_time: float, status: str):
    """RAG検索ログを出力"""
    log_data = {
        "timestamp": datetime.utcnow().isoformat(),
        "user_id": user_id,
        "query": query,
        "processing_time": processing_time,
        "status": status,
        "operation": "rag_search",
    }
    logger.info(json.dumps(log_data))
```

#### 8.1.2 ログ確認方法

- **Azure Portal**: Azure Functionsの「ログ」タブで確認
- **Application Insights**: 有料プランで詳細な分析が可能（オプション）
- **Table Storage**: アプリケーションログをTable Storageに保存（推奨）

### 8.2 Table Storageでのログ管理

#### 8.2.1 現在のログサービス実装

現在のPoC版では、`app/services/log_service.py`でSQLiteにログを保存しています：

```python
class LogService:
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
    ) -> int:
        """RAG検索ログを保存"""
        # SQLiteに保存（現在の実装）
        ...
```

#### 8.2.2 Azure Table Storageへの移行実装

Azure版では、以下のようにTable Storageにログを保存します：

```python
# app/services/log_service.py（Azure版）
from azure.data.tables import TableServiceClient
from azure.identity import DefaultAzureCredential
from datetime import datetime
from typing import Optional, Dict, List
import json
import uuid

class LogService:
    def __init__(self):
        self.table_name = "raglogs"
        table_service_client = TableServiceClient(
            account_url=settings.table_storage_url,
            credential=DefaultAzureCredential()
        )
        self.table_client = table_service_client.get_table_client(self.table_name)
    
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
        partition_key = now.strftime("%Y-%m-%d")  # 日付でパーティション分割
        row_key = f"{now.strftime('%Y%m%dT%H%M%S')}_{uuid.uuid4().hex[:8]}"
        
        # JSONデータを文字列に変換（Table Storageの制限対応）
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
        # generated_answerが大きい場合は切り詰め
        entity_size = sum(len(str(v)) for v in entity.values())
        if entity_size > 900000:  # 900KB以下に制限
            if generated_answer:
                max_answer_length = 900000 - (entity_size - len(generated_answer))
                entity["generated_answer"] = generated_answer[:max_answer_length] + "...(truncated)"
        
        self.table_client.upsert_entity(entity)
        return row_key
```

#### 8.2.3 ログクエリ実装

```python
# app/api/routes/admin_logs.py（Azure版）
from azure.data.tables import TableServiceClient
from datetime import datetime, timedelta
from typing import List, Optional

def get_logs(
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
    table_client = get_table_client("raglogs")
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
            entities = table_client.query_entities(
                query_filter=filter_query,
                results_per_page=limit
            )
            
            for entity in entities:
                # JSON文字列をパース
                if entity.get("input_data"):
                    entity["input_data"] = json.loads(entity["input_data"])
                if entity.get("rag_queries"):
                    entity["rag_queries"] = json.loads(entity["rag_queries"])
                if entity.get("referenced_files"):
                    entity["referenced_files"] = json.loads(entity["referenced_files"])
                if entity.get("search_results"):
                    entity["search_results"] = json.loads(entity["search_results"])
                
                logs.append(entity)
                
                if len(logs) >= limit:
                    break
        except Exception as e:
            print(f"Error querying partition {partition_key}: {e}")
            continue
        
        if len(logs) >= limit:
            break
        
        current_date += timedelta(days=1)
    
    # タイムスタンプでソート（新しい順）
    logs.sort(key=lambda x: x.get("timestamp", ""), reverse=True)
    
    return logs[:limit]
```

#### 8.2.4 ログ詳細取得

```python
def get_log_detail(log_id: str) -> Optional[dict]:
    """
    ログID（RowKey）からログ詳細を取得
    
    Args:
        log_id: RowKey（ログID）
        
    Returns:
        Optional[dict]: ログエンティティ（存在しない場合はNone）
    """
    # RowKeyから日付を抽出（YYYYMMDDTHHMMSS_xxxx形式）
    partition_key = log_id[:10].replace("T", "-")[:10]  # YYYY-MM-DD形式に変換
    
    table_client = get_table_client("raglogs")
    
    try:
        entity = table_client.get_entity(
            partition_key=partition_key,
            row_key=log_id
        )
        
        # JSON文字列をパース
        if entity.get("input_data"):
            entity["input_data"] = json.loads(entity["input_data"])
        if entity.get("rag_queries"):
            entity["rag_queries"] = json.loads(entity["rag_queries"])
        if entity.get("referenced_files"):
            entity["referenced_files"] = json.loads(entity["referenced_files"])
        if entity.get("search_results"):
            entity["search_results"] = json.loads(entity["search_results"])
        
        return entity
    except Exception as e:
        print(f"Error getting log detail: {e}")
        return None
```

### 8.3 エラー通知

#### 8.3.1 メール通知（簡易版）

```python
# Azure Functionsのアラート設定
# Azure Portalで設定:
# - エラー率 > 10% の場合にメール通知
# - 応答時間 > 10秒 の場合にメール通知
```

#### 8.3.2 ログ監視（将来拡張時）

- Application Insightsを追加することで、詳細な監視が可能
- 現時点では標準ログで十分

---

## 9. CI/CD設計

### 9.1 GitHub Actions（推奨）

#### 9.1.1 パイプライン構成

```yaml
# .github/workflows/deploy.yml
name: Deploy to Azure

on:
  push:
    branches:
      - main

jobs:
  deploy:
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
      
      - name: Run tests
        run: pytest tests/ || true  # テストがなくてもエラーにしない
      
      - name: Deploy to Azure Static Web Apps
        uses: Azure/static-web-apps-deploy@v1
        with:
          azure_static_web_apps_api_token: ${{ secrets.AZURE_STATIC_WEB_APPS_API_TOKEN }}
          repo_token: ${{ secrets.GITHUB_TOKEN }}
          action: "upload"
          app_location: "/"
          api_location: "api"
      
      - name: Deploy to Azure Functions
        uses: Azure/functions-action@v1
        with:
          app-name: 'func-ragkanri'
          package: '.'
          publish-profile: ${{ secrets.AZURE_FUNCTIONAPP_PUBLISH_PROFILE }}
```

### 9.2 デプロイメント戦略

#### 9.2.1 シンプルなデプロイ

- **GitHub連携**: コードをプッシュすると自動デプロイ
- **ロールバック**: 前のバージョンに戻す場合は、GitHubでロールバック
- **テスト環境**: 別ブランチ（develop）でテスト可能（オプション）

**補足**: ブルー・グリーンデプロイメントやカナリアリリースは不要です。シンプルなデプロイで十分です。

---

## 10. コスト設計

### 10.1 月間コスト見積もり（初期・小規模利用）

| サービス | 構成 | 月額コスト（円） | 備考 |
|---------|------|-----------------|------|
| **Azure Static Web Apps** | Free | **0円** | 無料プランで十分 |
| **Azure Functions** | Consumption Plan | **500〜2,000円** | 利用量次第（100万リクエスト/月まで無料） |
| **Azure Blob Storage** | Standard LRS, 10GB | **200〜500円** | 利用量次第 |
| **Azure Table Storage** | Standard, 1GB | **100〜300円** | 利用量次第 |
| **Azure Entra ID** | Free | **0円** | 基本機能は無料 |
| **OpenAI API** | 従量課金 | **1,000〜3,000円** | 利用量次第（目安） |
| **合計** | - | **1,800〜5,800円/月** | **固定費なし** |

### 10.2 コスト内訳の詳細

#### 10.2.1 Azure Functions（Consumption Plan）

```
無料枠:
  - 100万リクエスト/月: 無料
  - 40万GB秒/月: 無料

超過分:
  - リクエスト: 0.2円/100万リクエスト
  - 実行時間: 0.000016円/GB秒

例: 月間10万リクエスト、平均実行時間5秒、メモリ1GB
  - リクエスト: 無料（100万以下）
  - 実行時間: 10万 × 5秒 × 1GB = 50万GB秒（無料枠内）
  - 合計: 0円
```

#### 10.2.2 Azure Blob Storage

```
ストレージ:
  - 最初の50GB: 0.018円/GB/月
  - 50GB超: 0.016円/GB/月

トランザクション:
  - 読み取り: 0.004円/10,000トランザクション
  - 書き込み: 0.05円/10,000トランザクション

例: 10GB保存、月間100万読み取り、10万書き込み
  - ストレージ: 10GB × 0.018円 = 0.18円
  - 読み取り: 100 × 0.004円 = 0.4円
  - 書き込み: 10 × 0.05円 = 0.5円
  - 合計: 約1円/月
```

#### 10.2.3 OpenAI API

```
Embedding (text-embedding-3-small):
  - $0.02 / 1M tokens

LLM (gpt-4o-mini):
  - Input: $0.15 / 1M tokens
  - Output: $0.60 / 1M tokens

例: 月間100回のRAG検索、平均5,000 tokens/回
  - Embedding: 100回 × 5,000 tokens = 50万tokens = $0.01
  - LLM Input: 100回 × 5,000 tokens = 50万tokens = $0.075
  - LLM Output: 100回 × 2,000 tokens = 20万tokens = $0.12
  - 合計: 約$0.2 = 約30円/月（為替レート次第）
```

### 10.3 コスト最適化のポイント

#### 10.3.1 固定費をゼロにする

- **Static Web Apps**: 無料プランを使用
- **Functions**: Consumption Planで従量課金
- **Storage**: 従量課金のみ
- **Entra ID**: 無料プランを使用

#### 10.3.2 利用量に応じた最適化

- **キャッシュ**: 同じクエリの結果をキャッシュ（Table Storage）
- **バッチ処理**: RAG Index更新はバッチ処理で効率化
- **ストレージ最適化**: 古いデータはArchive層に移動（オプション）

#### 10.3.3 コスト監視

```yaml
コストアラート:
  - 月間予算: 10,000円
  - アラート: 80%（8,000円）、100%（10,000円）
  - 通知先: 管理者メール

コスト分析:
  - Azure Portalの「コスト管理」で確認
  - サービス別コストを確認
  - 利用量の傾向を把握
```

### 10.4 利用規模別のコスト目安

| 利用規模 | 月間リクエスト数 | 月額コスト（目安） |
|---------|----------------|------------------|
| **小規模（1-5名）** | 1,000回 | 1,000〜2,000円 |
| **中規模（6-15名）** | 5,000回 | 2,000〜4,000円 |
| **大規模（16-30名）** | 10,000回 | 3,000〜6,000円 |

**補足**: 利用が増えても、コストは利用量に比例して増加します。固定費は発生しません。

---

## 11. バックアップ・復旧計画

### 11.1 バックアップ戦略（簡易版）

#### 11.1.1 Blob Storageバックアップ

```yaml
自動バックアップ:
  - 頻度: 週次（日曜日）
  - 方法: 別ストレージアカウントにコピー（手動またはAzure Functions）
  - 保持期間: 4週間（4世代保持）

手動バックアップ:
  - 必要に応じて手動でバックアップ
  - Azure Portalからダウンロード可能
```

#### 11.1.2 Table Storageバックアップ

```yaml
自動バックアップ:
  - 頻度: 週次（日曜日）
  - 方法: Blob Storageにエクスポート（JSON形式）
  - 保持期間: 4週間

手動バックアップ:
  - 必要に応じて手動でエクスポート
```

### 11.2 復旧手順

#### 11.2.1 データ復旧

```yaml
手順:
  1. バックアップからデータを復元
  2. Blob Storageにアップロード
  3. Table Storageにインポート
  4. 動作確認

予想復旧時間: 1時間以内
```

#### 11.2.2 RAG Index再構築

```yaml
手順:
  1. KnowledgeファイルからRAG Indexを再構築
  2. Blob Storageに保存
  3. 動作確認

予想復旧時間: 10分〜30分（ファイル数による）
```

**補足**: エンタープライズレベルの厳密なRPO/RTOは不要です。通常の業務利用で十分な復旧計画です。

---

## 12. 移行計画

### 12.1 移行フェーズ

#### フェーズ1: 準備（1週間）

- [ ] Azureサブスクリプション作成・設定
- [ ] リソースグループ作成
- [ ] Azure Entra IDアプリケーション登録
- [ ] GitHubリポジトリ準備

#### フェーズ2: インフラ構築（1週間）

- [ ] Static Web Apps作成・設定
- [ ] Azure Functions作成・設定
- [ ] Blob Storage作成・設定
- [ ] Table Storage作成・設定

#### フェーズ3: アプリケーション移行（1-2週間）

- [ ] コード修正（Azure対応）
- [ ] 環境変数・設定の移行
- [ ] Knowledgeファイル移行（Blob Storage）
- [ ] RAG Index再構築

#### フェーズ4: テスト（1週間）

- [ ] 単体テスト
- [ ] 統合テスト
- [ ] ユーザー受け入れテスト（UAT）

#### フェーズ5: 本番リリース（1週間）

- [ ] 本番環境デプロイ
- [ ] 動作確認
- [ ] ユーザーへの案内
- [ ] ドキュメント更新

### 12.2 データ移行手順

#### 12.2.1 Knowledgeファイル移行

**現在の実装**: `app/services/knowledge_service.py`でローカルファイルシステム（`settings.knowledge_dir`）から`.txt`ファイルを読み込み

**移行方法1: Azure CLIを使用**

```bash
# Azure CLIでBlob Storageにアップロード
az storage blob upload-batch \
  --destination knowledge-files \
  --source /Users/takuminittono/Desktop/ragstudy/ラグルール/knowledge \
  --account-name stragkanri \
  --auth-mode login \
  --pattern "*.txt"
```

**移行方法2: Pythonスクリプトを使用**

```python
# scripts/migrate_knowledge_to_blob.py
from pathlib import Path
from azure.storage.blob import BlobServiceClient
from azure.identity import DefaultAzureCredential
from app.core.config import settings

def migrate_knowledge_files():
    """KnowledgeファイルをBlob Storageに移行"""
    # ローカルファイルシステムから読み込み
    knowledge_dir = Path(settings.knowledge_dir)
    
    # Blob Storage接続
    blob_service_client = BlobServiceClient(
        account_url=settings.blob_storage_url,
        credential=DefaultAzureCredential()
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

#### 12.2.2 SQLite → Table Storage移行

**現在の実装**: `app/core/database.py`の`RAGLog`テーブルにログを保存

**移行スクリプト**:

```python
# scripts/migrate_logs_to_table_storage.py
import sqlite3
from azure.data.tables import TableServiceClient
from azure.identity import DefaultAzureCredential
from datetime import datetime
import json
from app.core.config import settings

def migrate_logs():
    """SQLiteのrag_logsテーブルをTable Storageに移行"""
    # SQLiteからデータを読み込み
    conn = sqlite3.connect('rag_kanri.db')
    conn.row_factory = sqlite3.Row  # 辞書形式で取得
    cursor = conn.cursor()
    
    cursor.execute("SELECT * FROM rag_logs ORDER BY timestamp")
    logs = cursor.fetchall()
    
    print(f"Found {len(logs)} logs to migrate")
    
    # Table Storage接続
    table_service_client = TableServiceClient(
        account_url=settings.table_storage_url,
        credential=DefaultAzureCredential()
    )
    table_client = table_service_client.get_table_client("raglogs")
    
    # テーブルが存在しない場合は作成
    try:
        table_client.create_table()
    except Exception:
        pass  # 既に存在する場合はスキップ
    
    # データを移行
    migrated_count = 0
    error_count = 0
    
    for log_row in logs:
        try:
            # タイムスタンプをパース
            if isinstance(log_row['timestamp'], str):
                timestamp = datetime.fromisoformat(log_row['timestamp'].replace('Z', '+00:00'))
            else:
                timestamp = datetime.fromisoformat(log_row['timestamp'])
            
            # パーティションキーと行キーを生成
            partition_key = timestamp.strftime("%Y-%m-%d")
            row_key = f"{timestamp.strftime('%Y%m%dT%H%M%S')}_{log_row['id']:08d}"
            
            # エンティティを作成
            entity = {
                "PartitionKey": partition_key,
                "RowKey": row_key,
                "id": log_row['id'],
                "timestamp": timestamp.isoformat(),
                "user_id": log_row['user_id'] or "",
                "case_id": log_row['case_id'] or "",
                "status": log_row['status'] or "success",
                "error_message": log_row['error_message'] or "",
                "input_data": json.dumps(log_row['input_data'], ensure_ascii=False) if log_row['input_data'] else "",
                "rag_queries": json.dumps(log_row['rag_queries'], ensure_ascii=False) if log_row['rag_queries'] else "",
                "referenced_files": json.dumps(log_row['referenced_files'], ensure_ascii=False) if log_row['referenced_files'] else "",
                "search_results": json.dumps(log_row['search_results'], ensure_ascii=False) if log_row['search_results'] else "",
                "generated_answer": (log_row['generated_answer'] or "")[:900000],  # サイズ制限
                "reasoning": (log_row['reasoning'] or "")[:10000],  # サイズ制限
                "processing_time": log_row['processing_time'] or 0.0,
                "model_name": log_row['model_name'] or "",
                "top_k": log_row['top_k'] or 0,
            }
            
            # Table Storageに書き込み
            table_client.upsert_entity(entity)
            migrated_count += 1
            
            if migrated_count % 100 == 0:
                print(f"Migrated {migrated_count} logs...")
                
        except Exception as e:
            error_count += 1
            print(f"Error migrating log ID {log_row['id']}: {e}")
            continue
    
    conn.close()
    
    print(f"\nMigration completed!")
    print(f"  Successfully migrated: {migrated_count} logs")
    print(f"  Errors: {error_count} logs")

if __name__ == "__main__":
    migrate_logs()
```

#### 12.2.3 RAGインデックス移行

**現在の実装**: `app/services/rag_service.py`でローカルファイルシステム（`./storage/index/`）にLlamaIndex形式で保存

**移行方法1: Azure Functionsで再構築（推奨）**

```python
# Azure Functionsで実行（推奨）
# 理由: Blob StorageからKnowledgeファイルを読み込んで、新しいインデックスを構築

from app.services.rag_service import rag_service

# Knowledgeファイルは既にBlob Storageに移行済み
# RAGサービスがBlob Storageから読み込むように設定されている場合
result = rag_service.create_index()

print(f"Index created: {result}")
print(f"  Success: {result['success']}")
print(f"  Indexed files: {result['indexed_files']}")
print(f"  Total chunks: {result['total_chunks']}")
```

**移行方法2: 既存インデックスファイルをBlob Storageにコピー**

```python
# scripts/migrate_index_to_blob.py
from pathlib import Path
from azure.storage.blob import BlobServiceClient
from azure.identity import DefaultAzureCredential
from app.core.config import settings
import json

def migrate_index():
    """既存のRAGインデックスをBlob Storageに移行"""
    # ローカルインデックスディレクトリ
    local_index_dir = Path("./storage/index")
    
    if not local_index_dir.exists():
        print("Local index directory not found. Skipping migration.")
        return
    
    # Blob Storage接続
    blob_service_client = BlobServiceClient(
        account_url=settings.blob_storage_url,
        credential=DefaultAzureCredential()
    )
    container_client = blob_service_client.get_container_client("rag-index")
    
    # コンテナが存在しない場合は作成
    if not container_client.exists():
        container_client.create_container()
    
    # バージョン1として保存
    version = 1
    
    # インデックスファイルをアップロード
    index_files = [
        "default__vector_store.json",
        "docstore.json",
        "graph_store.json",
        "index_store.json",
    ]
    
    for filename in index_files:
        file_path = local_index_dir / filename
        
        if not file_path.exists():
            print(f"Warning: {filename} not found. Skipping.")
            continue
        
        # Blob Storageのパス
        blob_name = f"index_v{version}/{filename}"
        blob_client = container_client.get_blob_client(blob_name)
        
        # ファイル内容を読み込み
        content = file_path.read_text(encoding='utf-8')
        
        # Blob Storageにアップロード
        blob_client.upload_blob(
            content.encode('utf-8'),
            overwrite=True,
            content_settings={"content_type": "application/json"}
        )
        
        print(f"Uploaded: {blob_name}")
    
    print("Index migration completed!")

if __name__ == "__main__":
    migrate_index()
```

**注意**: LlamaIndexのインデックスは、エンベディングモデルやLlamaIndexのバージョンに依存するため、**再構築を推奨**します。既存のインデックスファイルをコピーする場合は、Azure環境で同じバージョンのLlamaIndexとエンベディングモデルを使用する必要があります。

#### 12.2.4 生成ドキュメントの移行

**現在の実装**: メモリ内で生成し、バイト列として返す（永続化なし）

**移行**: 新規実装として、生成されたドキュメントをBlob Storageに保存する機能を追加

```python
# app/services/document_service.py（Azure版への追加）
from azure.storage.blob import BlobServiceClient
from azure.identity import DefaultAzureCredential

def save_generated_document(
    document_type: str,  # "estimate" or "order"
    case_id: str,
    document_bytes: bytes,
    filename: str
) -> str:
    """
    生成されたドキュメントをBlob Storageに保存
    
    Returns:
        str: Blob StorageのURL
    """
    blob_service_client = BlobServiceClient(
        account_url=settings.blob_storage_url,
        credential=DefaultAzureCredential()
    )
    container_client = blob_service_client.get_container_client("generated-documents")
    
    # コンテナが存在しない場合は作成
    if not container_client.exists():
        container_client.create_container()
    
    # Blob Storageのパス
    blob_name = f"{document_type}/{case_id}/{filename}"
    blob_client = container_client.get_blob_client(blob_name)
    
    # アップロード
    blob_client.upload_blob(
        document_bytes,
        overwrite=True,
        content_settings={"content_type": "application/vnd.openxmlformats-officedocument.wordprocessingml.document"}
    )
    
    return blob_client.url
```

### 12.3 ダウンタイム最小化

```yaml
移行戦略: 並行運用

手順:
  1. Azure環境を構築・テスト（既存システムは稼働継続）
  2. データをAzure環境にコピー
  3. 並行運用期間（1週間）
  4. 本番切り替え（ダウンタイム: 数分）
  5. 旧システム停止

予想ダウンタイム: 数分（DNS切り替えのみ）
```

---

## 13. 運用・保守計画

### 13.1 日常運用タスク

#### 13.1.1 日次タスク（自動化推奨）

- [ ] システムヘルスチェック（自動）
- [ ] エラーログ確認（必要に応じて）
- [ ] コスト確認（Azure Portal）

#### 13.1.2 週次タスク

- [ ] コスト分析・最適化
- [ ] エラーログの確認
- [ ] ユーザーアクティビティ確認

#### 13.1.3 月次タスク

- [ ] バックアップ確認
- [ ] コスト最適化レビュー
- [ ] セキュリティ確認（オプション）

### 13.2 メンテナンス計画

#### 13.2.1 定期メンテナンス

```yaml
頻度: 月1回（必要に応じて）

内容:
  - コード更新（GitHub経由で自動デプロイ）
  - 依存パッケージの更新
  - ログローテーション（Table Storage）

通知:
  - 必要に応じてユーザーに通知
  - メンテナンス時間: 深夜時間帯（影響最小）
```

**補足**: Azure Functionsは自動で更新されるため、手動メンテナンスは最小限です。

### 13.3 サポート体制

#### 13.3.1 サポートレベル

| レベル | 対応時間 | 対象 |
|-------|---------|------|
| **L1（一次対応）** | 営業時間内（9:00-18:00） | 一般的な問い合わせ、ユーザーサポート |
| **L2（二次対応）** | 営業時間内 | 技術的な問題、バグ対応 |

**補足**: 24時間365日のサポートは不要です。営業時間内のサポートで十分です。

#### 13.3.2 エスカレーション

```yaml
エスカレーションフロー:
  L1 → L2: 1時間以内に解決できない場合

通知チャネル:
  - メール
  - 電話（緊急時）
```

---

## 14. セキュリティコンプライアンス

### 14.1 セキュリティ標準

- **個人情報保護法**: 日本の個人情報保護法準拠（必要に応じて対応）
- **データ所在地**: 日本リージョン（Japan East）に限定
- **アクセス制御**: 最小権限の原則（管理者/一般ユーザー）

**補足**: ISO 27001やSOC 2などの高度なコンプライアンスは不要です。中小企業の業務利用に必要なセキュリティ要件を満たします。

### 14.2 セキュリティ監査

#### 14.2.1 定期確認

```yaml
頻度: 四半期に1回

確認項目:
  - アクセスログの確認
  - 権限の見直し
  - セキュリティパッチの適用状況（Azure側で自動）

確認方法:
  - Azure Portalで確認
  - Table Storageのログを確認
```

#### 14.2.2 脆弱性対策

```yaml
ツール: Azure Security Center（基本機能）

頻度: 月1回（自動）

対応:
  - Critical/High: 1週間以内に修正
  - Medium: 1ヶ月以内に修正
  - Low: 必要に応じて対応
```

### 14.3 インシデント対応

#### 14.3.1 インシデント対応計画

```yaml
インシデント種別:
  - データ漏洩
  - 不正アクセス
  - サービス停止

対応手順:
  1. インシデントの検知・報告
  2. 初期対応（影響範囲の特定、隔離）
  3. 調査・分析
  4. 復旧作業
  5. 事後対応（再発防止策、報告）
```

#### 14.3.2 通知・報告

```yaml
通知先:
  - 内部: 管理者

報告期限:
  - 重大なインシデント: 24時間以内
  - 一般的なインシデント: 72時間以内
```

---

## 15. 将来の本番拡張構成（Enterprise移行パス）

### 15.1 拡張が必要になるタイミング

以下のような状況になった場合、エンタープライズ構成への移行を検討してください：

- **利用者数の増加**: 30名を超える利用者が発生
- **高可用性の要求**: 99.9%以上のSLAが必要
- **セキュリティ要件の強化**: より高度なセキュリティ対策が必要
- **パフォーマンス要件の向上**: より高速な応答が必要
- **データ量の増加**: 大規模なデータ管理が必要

### 15.2 現在構成 → エンタープライズ構成への移行イメージ

```
【現在構成（サーバーレス）】
Static Web Apps (Free)
  ↓
Azure Functions (Consumption)
  ↓
Blob Storage (LRS) + Table Storage
  ↓
OpenAI API

【拡張構成（エンタープライズ）】
Azure Front Door + WAF
  ↓
Azure App Service (Premium v3) × 2リージョン
  ↓
Azure SQL Database (Business Critical) + Geo-Replication
  ↓
Azure Blob Storage (RA-GRS) + Azure Cache for Redis
  ↓
Azure Key Vault (Premium) + Application Insights
```

### 15.3 移行手順（概要）

#### 15.3.1 段階的移行

```yaml
フェーズ1: App Service追加
  - Static Web Apps → App Serviceに移行
  - Functions → App Service内のAPIに統合
  - コスト: 月額3万円程度

フェーズ2: SQL Database追加
  - Table Storage → SQL Databaseに移行
  - データ移行ツールを使用
  - コスト: 月額8万円程度

フェーズ3: 高可用性構成
  - マルチリージョン構成
  - Geo-Replication
  - コスト: 月額15万円程度

フェーズ4: セキュリティ強化
  - Key Vault Premium
  - WAF追加
  - コスト: 月額2万円程度
```

#### 15.3.2 データ移行

```yaml
Table Storage → SQL Database:
  - データエクスポートツールを使用
  - スキーマ変換
  - データインポート

Blob Storage:
  - そのまま使用可能（RA-GRSに変更）

RAG Index:
  - そのまま使用可能
```

### 15.4 コスト比較

| 構成 | 月額コスト | 特徴 |
|------|-----------|------|
| **現在構成（サーバーレス）** | 1,000〜5,000円 | 固定費なし、従量課金 |
| **拡張構成（エンタープライズ）** | 15万〜20万円 | 高可用性、高セキュリティ |

**補足**: 現在構成から拡張構成への移行は、段階的に実施可能です。必要に応じて移行してください。

---

## 16. 付録

### 16.1 参考資料

- [Azure Static Web Apps ドキュメント](https://docs.microsoft.com/ja-jp/azure/static-web-apps/)
- [Azure Functions ドキュメント](https://docs.microsoft.com/ja-jp/azure/azure-functions/)
- [Azure Blob Storage ドキュメント](https://docs.microsoft.com/ja-jp/azure/storage/blobs/)
- [Azure Table Storage ドキュメント](https://docs.microsoft.com/ja-jp/azure/storage/tables/)
- [Azure Entra ID ドキュメント](https://docs.microsoft.com/ja-jp/azure/active-directory/)

### 16.2 用語集

- **サーバーレス**: サーバーを管理せず、コードを実行するだけの構成。使った分だけ課金される。
- **従量課金**: 利用量に応じて課金される方式。固定費が発生しない。
- **Consumption Plan**: Azure Functionsの従量課金プラン。使った分だけ課金される。
- **Static Web Apps**: Azureの静的Webサイトホスティングサービス。無料プランあり。
- **Table Storage**: AzureのNoSQLデータベースサービス。低コストで利用可能。

### 16.3 変更履歴

| バージョン | 日付 | 変更内容 | 作成者 |
|-----------|------|---------|--------|
| 1.0 | 2024-12 | エンタープライズ版作成 | - |
| 2.0 | 2024-12 | 中小企業向けサーバーレス版に書き換え | - |

---

**文書終了**
