# 貯水槽修理案件管理システム

RAG（Retrieval-Augmented Generation）を活用した、貯水槽修理案件の判断支援Webアプリケーション。

## 📋 プロジェクト概要

- **目的**：貯水槽の修理案件を下請け業者に回す際の判断支援
- **技術スタック**：FastAPI + LlamaIndex + OpenAI API + SQLite
- **Knowledge**：既存30個のtxtファイルを使用

## 🚀 セットアップ手順

### 1. 前提条件

- **Python 3.10以上、3.13以下を推奨**（Python 3.14は一部パッケージが未対応の可能性があります）
- pip（Pythonパッケージマネージャー）

**注意**：Python 3.14を使用している場合、一部のパッケージ（特に`pydantic-core`）がビルドできない可能性があります。その場合は、Python 3.11または3.12を使用することを推奨します。

### 2. 仮想環境の作成と有効化

```bash
# 仮想環境を作成
python3 -m venv venv

# 仮想環境を有効化
# macOS/Linux:
source venv/bin/activate

# Windows:
# venv\Scripts\activate
```

### 3. 依存パッケージのインストール

```bash
pip install -r requirements.txt
```

### 4. 環境変数の設定

`.env`ファイルを手動で作成し、以下の内容を設定してください。

```bash
# .envファイルを作成
touch .env
```

`.env`ファイルに以下の内容を記述してください：

```env
# OpenAI API設定
OPENAI_API_KEY=your_openai_api_key_here

# Knowledgeディレクトリパス
KNOWLEDGE_DIR=/Users/takuminittono/Desktop/ragstudy/ラグルール/knowledge

# データベース設定
DATABASE_URL=sqlite:///./rag_kanri.db

# 管理者認証（PoC簡易版）
ADMIN_PASSWORD=admin123

# アプリケーション設定
APP_NAME=貯水槽修理案件管理システム
DEBUG=True
SECRET_KEY=your_secret_key_here_change_in_production

# サーバー設定
HOST=0.0.0.0
PORT=8000
```

**重要**：
- `OPENAI_API_KEY`: 実際のOpenAI APIキーに置き換えてください
- `KNOWLEDGE_DIR`: 既存のKnowledgeディレクトリパスをそのまま使用可能です
- `ADMIN_PASSWORD`: PoCでは簡易パスワードでOKですが、本番では変更してください

### 5. アプリケーションの起動

```bash
# 仮想環境を有効化（まだの場合）
source venv/bin/activate

# 開発サーバー起動
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

ブラウザで以下のURLにアクセスしてください：

- **API**: `http://localhost:8000`
- **APIドキュメント（Swagger UI）**: `http://localhost:8000/docs`
- **ヘルスチェック**: `http://localhost:8000/health`

### 6. 動作確認

サーバーが起動したら、以下のエンドポイントを確認してください：

```bash
# ヘルスチェック
curl http://localhost:8000/health

# ルートエンドポイント
curl http://localhost:8000/
```

## 📁 プロジェクト構造

```
rag-kanri/
├── app/
│   ├── __init__.py
│   ├── main.py                    # FastAPIアプリケーション
│   ├── api/
│   │   ├── __init__.py
│   │   └── routes/                # APIルート
│   │       ├── knowledge.py       # KnowledgeファイルAPI（一般ユーザー）
│   │       ├── rag_index.py       # RAG Index管理API
│   │       ├── rag_search.py      # RAG検索・回答生成API
│   │       ├── documents.py       # 見積書・発注書生成API
│   │       ├── admin_auth.py      # 管理者認証API
│   │       ├── admin_knowledge.py  # Knowledge管理API（管理者）
│   │       └── admin_logs.py      # ログ閲覧API（管理者）
│   ├── core/
│   │   ├── config.py              # 設定管理
│   │   ├── database.py            # DB接続
│   │   └── auth.py                # 認証機能
│   ├── models/
│   │   └── schemas.py             # Pydanticスキーマ
│   ├── services/
│   │   ├── rag_service.py         # RAG検索サービス
│   │   ├── knowledge_service.py   # Knowledge管理サービス
│   │   ├── log_service.py         # ログ管理サービス
│   │   └── document_service.py    # ドキュメント生成サービス
│   └── utils/
│       └── __init__.py
├── static/                        # 静的ファイル（CSS、JS等）
├── templates/                     # HTMLテンプレート
│   ├── index.html                 # 案件入力画面
│   ├── answer.html                # 回答表示画面
│   ├── admin_login.html           # 管理者ログイン画面
│   └── admin.html                 # 管理者画面
├── storage/                       # ストレージ（RAG Index保存先）
│   └── index/
├── .env                           # 環境変数（gitignore対象）
├── .env.local                     # ローカル環境変数（gitignore対象）
├── requirements.txt               # Python依存パッケージ
├── README.md                      # このファイル
├── REQUIREMENTS.md                # 要件定義書
├── PROGRESS.md                    # 進捗管理ファイル
└── rag_kanri.db                   # SQLiteデータベース（自動生成）
```

## 💻 使い方

### 一般ユーザー向け機能

1. **案件入力**
   - ブラウザで `http://localhost:8000` にアクセス
   - 案件名、修理種別、緊急度、現場情報、貯水槽規模、詳細説明を入力
   - 「RAG検索を実行」ボタンをクリック

2. **RAG回答の確認**
   - 検索結果が表示されます
   - 推奨業者候補、想定価格情報、判断理由、リスク・注意事項、緊急度評価が表示されます
   - 参照したKnowledgeファイル名も確認できます

3. **見積書・発注書の生成**
   - 回答画面から「見積書生成」または「発注書生成」ボタンをクリック
   - Word形式（.docx）のファイルがダウンロードされます

### 管理者向け機能

1. **ログイン**
   - `http://localhost:8000/admin/login` にアクセス
   - 管理者パスワードを入力（デフォルト: `.env`ファイルで設定した`ADMIN_PASSWORD`）

2. **Knowledge管理**
   - Knowledgeファイルの一覧表示、内容確認、追加、削除が可能
   - ファイル追加後は「RAG Index再構築」を実行してください

3. **ログ閲覧**
   - RAG検索のログを確認できます
   - 日付、ユーザーID、案件IDでフィルタリング可能

4. **RAG Index再構築**
   - Knowledgeファイルを追加・更新・削除した後、必ず再構築を実行してください
   - 再構築には数分かかる場合があります

## 🔧 開発フェーズ

このプロジェクトは段階的に実装されています。詳細は `PROGRESS.md` を参照してください。

- **Phase 0-12**: 実装完了 ✅
- **Phase 13**: UI改善・バグ修正 ✅
- **Phase 14**: ドキュメント整備 🔵 進行中

## 📚 参考資料

- **要件定義書**：`REQUIREMENTS.md`
- **進捗管理**：`PROGRESS.md`
- **API仕様書**：`API_SPEC.md`
- **デプロイ手順書**：`DEPLOYMENT.md`
- **トラブルシューティングガイド**：`TROUBLESHOOTING.md`
- **Knowledge索引**：`/Users/takuminittono/Desktop/ragstudy/ラグルール/knowledge_index.md`

## ⚠️ 注意事項

- PoC（概念実証）版のため、認証は簡易実装です
- 本番環境では適切なセキュリティ対策が必要です
- Knowledgeファイルは既存のディレクトリを参照します

## 📝 ライセンス

このプロジェクトは内部使用を目的としています。

