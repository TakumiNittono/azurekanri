# 貯水槽修理案件管理システム - アーキテクチャ概要

## 📋 プロジェクト概要

RAG（Retrieval-Augmented Generation）を活用した、貯水槽修理案件の判断支援Webアプリケーション。過去の事例や知識ベースから最適な業者を推薦し、見積書・発注書を自動生成します。

## 🏗️ システムアーキテクチャ

### 全体構成

```
┌─────────────────┐
│   フロントエンド │  (HTML + JavaScript + Bootstrap)
│  (ブラウザ)      │
└────────┬────────┘
         │ HTTP/HTTPS
         ▼
┌─────────────────┐
│   FastAPI        │  (Python Web Framework)
│   (バックエンド)  │
└────────┬────────┘
         │
    ┌────┴────┬──────────────┬─────────────┐
    ▼         ▼              ▼             ▼
┌────────┐ ┌──────────┐ ┌──────────┐ ┌──────────┐
│ Llama  │ │ OpenAI   │ │ SQLite   │ │ Knowledge│
│ Index  │ │ API      │ │ Database │ │ Files    │
│ (RAG)  │ │ (LLM)    │ │ (Logs)   │ │ (30txt)  │
└────────┘ └──────────┘ └──────────┘ └──────────┘
```

## 🛠️ 技術スタック

### バックエンド

#### Webフレームワーク
- **FastAPI** (0.104.1)
  - モダンなPython Webフレームワーク
  - 自動APIドキュメント生成（Swagger UI）
  - 非同期処理対応
  - Pydanticによる型安全なデータバリデーション

#### RAG・LLM関連
- **LlamaIndex** (>=0.10.0, <0.15.0)
  - RAG（Retrieval-Augmented Generation）フレームワーク
  - ベクトル検索とLLM統合
  - Document管理とchunk分割
  - Vector Store Index管理

- **OpenAI API**
  - **Embeddingモデル**: `text-embedding-3-small` (デフォルト)
  - **LLMモデル**: `gpt-4o-mini`
  - テキスト埋め込み生成
  - 回答生成とプロンプトエンジニアリング

#### データベース
- **SQLite** (aiosqlite 0.19.0)
  - 軽量なリレーショナルデータベース
  - RAG検索ログの保存
  - SQLAlchemy ORM使用

#### ドキュメント生成
- **python-docx** (1.1.0)
  - Word形式（.docx）ファイル生成
  - テンプレートベースの文書作成
  - 見積書・発注書の自動生成

- **reportlab** (4.0.7)
  - PDF生成（将来拡張用）

### フロントエンド

- **HTML5 + JavaScript (ES6+)**
  - バニラJavaScript（フレームワーク不使用）
  - セッションストレージによる状態管理
  - 動的なUI更新

- **Bootstrap 5**
  - レスポンシブデザイン
  - モーダルダイアログ
  - フォームコンポーネント

### 開発・運用ツール

- **Uvicorn** (0.24.0)
  - ASGIサーバー
  - ホットリロード対応
  - 本番環境対応

- **Pydantic** (>=2.8.0)
  - データバリデーション
  - 設定管理
  - 型安全性の確保

## 📂 プロジェクト構造

```
rag-kanri/
├── app/                          # アプリケーション本体
│   ├── main.py                   # FastAPIアプリケーションエントリーポイント
│   ├── api/routes/               # APIルート定義
│   │   ├── rag_search.py        # RAG検索・回答生成API
│   │   ├── rag_index.py         # RAG Index管理API
│   │   ├── knowledge.py         # Knowledgeファイル閲覧API
│   │   ├── documents.py         # 見積書・発注書生成API
│   │   ├── admin_auth.py        # 管理者認証API
│   │   ├── admin_knowledge.py   # Knowledge管理API（管理者）
│   │   └── admin_logs.py        # ログ閲覧API（管理者）
│   ├── services/                 # ビジネスロジック層
│   │   ├── rag_service.py       # RAG検索・回答生成サービス
│   │   ├── knowledge_service.py # Knowledgeファイル管理サービス
│   │   ├── log_service.py       # ログ管理サービス
│   │   └── document_service.py  # ドキュメント生成サービス
│   ├── core/                     # コア機能
│   │   ├── config.py            # 設定管理（環境変数読み込み）
│   │   ├── database.py           # データベース接続・モデル定義
│   │   └── auth.py               # 認証機能
│   └── models/                   # データモデル
│       └── schemas.py            # Pydanticスキーマ定義
├── templates/                    # HTMLテンプレート
│   ├── index.html                # 案件入力画面
│   ├── answer.html               # RAG回答表示画面
│   ├── admin_login.html          # 管理者ログイン画面
│   ├── admin.html                # 管理者画面
│   └── documents/                # ドキュメントテンプレート
│       └── order_template.docx   # 発注書テンプレート
├── static/                       # 静的ファイル（CSS、JS等）
├── storage/                      # ストレージ
│   └── index/                    # RAG Index保存先
├── scripts/                      # ユーティリティスクリプト
│   ├── create_order_template.py  # 発注書テンプレート生成
│   └── import_chunks_to_db.py    # チャンクデータインポート
└── requirements.txt              # Python依存パッケージ一覧
```

## 🔄 データフロー

### RAG検索・回答生成の流れ

```
1. ユーザー入力
   └─> 案件情報（修理種別、緊急度、場所など）

2. RAG検索
   ├─> クエリ生成（案件情報から検索クエリを作成）
   ├─> ベクトル検索（LlamaIndex Vector Store）
   ├─> 類似度計算（OpenAI Embedding）
   └─> トップK件の検索結果取得

3. LLM回答生成
   ├─> プロンプト構築（検索結果 + 案件情報）
   ├─> OpenAI API呼び出し（gpt-4o-mini）
   ├─> 回答生成（推奨業者候補、価格情報、判断理由など）
   └─> 事例番号抽出・フォーマット整形

4. 結果表示
   ├─> フロントエンドで表示
   ├─> ログ保存（SQLite）
   └─> 見積書・発注書生成（オプション）
```

### ドキュメント生成の流れ

```
1. ユーザー選択
   └─> 推奨業者候補から選択

2. テンプレート読み込み
   ├─> order_template.docx読み込み
   └─> プレースホルダー検出

3. データ置換
   ├─> 案件情報の置換
   ├─> 業者情報の置換
   ├─> 価格情報の置換
   └─> 日付・備考の置換

4. ファイル生成
   └─> Word形式（.docx）でダウンロード
```

## 🔑 主要コンポーネント

### 1. RAG Service (`app/services/rag_service.py`)

**役割**: RAG検索とLLM回答生成の中核

**主要機能**:
- KnowledgeファイルからVector Store Index作成
- セマンティック検索（ベクトル類似度検索）
- LLMによる回答生成
- 事例番号の抽出とフォーマット

**使用技術**:
- LlamaIndex (Vector Store Index)
- OpenAI Embedding API
- OpenAI GPT-4o-mini API

### 2. Document Service (`app/services/document_service.py`)

**役割**: 見積書・発注書の自動生成

**主要機能**:
- Word形式（.docx）ファイル生成
- テンプレートベースの文書作成
- プレースホルダー置換

**使用技術**:
- python-docx
- カスタムWordテンプレート

### 3. Knowledge Service (`app/services/knowledge_service.py`)

**役割**: Knowledgeファイルの管理

**主要機能**:
- Knowledgeファイル一覧取得
- ファイル内容の読み込み
- ファイル種別の判定

### 4. Log Service (`app/services/log_service.py`)

**役割**: RAG検索ログの保存・管理

**主要機能**:
- 検索クエリのログ保存
- 参照ファイルの記録
- 処理時間の記録

**使用技術**:
- SQLite
- SQLAlchemy ORM

## 🎯 主要機能

### 1. RAG検索・回答生成

- **入力**: 案件情報（修理種別、緊急度、場所など）
- **処理**: 
  - ベクトル検索で関連Knowledgeを取得
  - LLMで構造化された回答を生成
- **出力**: 
  - 推奨業者候補（最大3社）
  - 想定価格情報
  - 判断理由
  - リスク・注意事項
  - 緊急度評価

### 2. 業者推薦

- **特徴**:
  - 過去事例に基づく推薦
  - 事例番号の明示
  - 選定理由の説明
  - 価格帯の提示

### 3. ドキュメント生成

- **見積書生成**: RAG回答から見積書を自動生成
- **発注書生成**: 
  - 推奨業者候補から選択
  - テンプレートベースで生成
  - Word形式（.docx）で出力

### 4. Knowledge管理（管理者機能）

- Knowledgeファイルの追加・削除
- RAG Indexの再構築
- ログ閲覧・分析

## 🔐 認証・セキュリティ

### 認証方式

- **管理者認証**: 簡易パスワード認証（PoC版）
- **セッション管理**: Cookieベース（JWT未使用）

### セキュリティ考慮事項

- CORS設定（開発環境では全許可）
- 環境変数による機密情報管理
- SQLインジェクション対策（SQLAlchemy ORM使用）

## 📊 データモデル

### RAGLog (SQLite)

```python
- id: 主キー
- timestamp: 検索実行日時
- user_id: ユーザーID（オプション）
- case_id: 案件ID（オプション）
- query: 検索クエリ
- referenced_files: 参照ファイル名リスト
- generated_answer: 生成された回答
- reasoning: 判断理由
- processing_time: 処理時間（秒）
- status: ステータス（success/failed）
```

### Vector Store Index (LlamaIndex)

- **保存形式**: JSONファイル
- **保存先**: `storage/index/`
- **内容**:
  - ベクトル埋め込み
  - メタデータ（ファイル名、chunk_index等）
  - テキストコンテンツ

## 🚀 デプロイメント

### 開発環境

```bash
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

### 本番環境

- Uvicorn + Gunicorn（推奨）
- 環境変数の適切な設定
- HTTPS化
- セキュリティ設定の強化

## 📝 設定ファイル

### 環境変数 (.env)

```env
OPENAI_API_KEY=your_api_key
KNOWLEDGE_DIR=/path/to/knowledge
DATABASE_URL=sqlite:///./rag_kanri.db
ADMIN_PASSWORD=your_password
HOST=0.0.0.0
PORT=8000
```

## 🔧 カスタマイズポイント

### Embeddingモデルの変更

`app/services/rag_service.py`の26行目:
```python
self.embed_model = OpenAIEmbedding(
    api_key=settings.openai_api_key,
    model="text-embedding-3-small"  # モデル名を指定
)
```

### LLMモデルの変更

`app/services/rag_service.py`の27行目:
```python
self.llm = OpenAI(
    api_key=settings.openai_api_key,
    model="gpt-4o-mini"  # モデル名を変更可能
)
```

### Chunkサイズの調整

`app/services/rag_service.py`の86-89行目:
```python
node_parser = SimpleNodeParser.from_defaults(
    chunk_size=400,      # チャンクサイズ（文字数）
    chunk_overlap=50,    # オーバーラップ（文字数）
)
```

## 📚 参考資料

- **LlamaIndex公式ドキュメント**: https://docs.llamaindex.ai/
- **FastAPI公式ドキュメント**: https://fastapi.tiangolo.com/
- **OpenAI APIドキュメント**: https://platform.openai.com/docs

## 🎓 学習ポイント

このプロジェクトで学べる技術:

1. **RAG（Retrieval-Augmented Generation）**
   - ベクトル検索の実装
   - LLMと検索結果の統合
   - プロンプトエンジニアリング

2. **FastAPI**
   - RESTful API設計
   - 非同期処理
   - 自動APIドキュメント生成

3. **LlamaIndex**
   - Document管理
   - Vector Store Index
   - Query Engine

4. **OpenAI API**
   - Embedding生成
   - LLM回答生成
   - エラーハンドリング

5. **ドキュメント生成**
   - テンプレートベースの文書作成
   - Word形式ファイル生成

