# Vercelデプロイガイド

## ⚠️ 重要な注意事項

このアプリケーションをVercelにデプロイする場合、以下の制約があります：

### 1. ファイルシステムの制約

Vercelは**サーバーレス環境**のため、以下の制約があります：

- **読み取り専用ファイルシステム**: `/tmp`ディレクトリ以外への書き込みはできません
- **一時的なストレージ**: ファイルは一時的なもので、リクエスト間で保持されません

### 2. 現在のアプリケーションの課題

#### ❌ SQLiteデータベース (`rag_kanri.db`)
- 現在はローカルファイルシステムに書き込んでいます
- Vercelでは永続化されません

#### ❌ Vector Store Index (`storage/index/`)
- 現在はローカルファイルシステムに保存しています
- Vercelでは永続化されません

#### ⚠️ Knowledgeファイル
- 現在はローカルパスから読み込んでいます
- Vercelでは、Knowledgeファイルをリポジトリに含める必要があります

## 🔧 対応策

### オプション1: 最小限の変更でデプロイ（制限あり）

この方法では、以下の機能が制限されます：

- **ログ機能**: SQLiteへの書き込みができないため、ログは保存されません
- **Index再構築**: 毎回Indexを再構築する必要があります（起動時に自動生成）

#### 必要な変更

1. **Knowledgeファイルをリポジトリに含める**
   ```bash
   # Knowledgeファイルをプロジェクトにコピー
   mkdir -p knowledge
   cp -r /path/to/knowledge/* knowledge/
   ```

2. **設定ファイルの変更** (`app/core/config.py`)
   - Knowledgeディレクトリを相対パスに変更
   - データベースを`/tmp`に保存（一時的）

3. **Indexを事前にビルド**
   - デプロイ前にIndexをビルドしてリポジトリに含める

### オプション2: 外部ストレージを使用（推奨）

より実用的な方法として、以下の外部サービスを使用します：

#### データベース
- **PostgreSQL** (Vercel Postgres、Supabase、Neonなど)
- **MongoDB Atlas** (MongoDB)

#### Vector Store
- **Pinecone** (ベクトルデータベース)
- **Weaviate** (ベクトルデータベース)
- **Qdrant** (ベクトルデータベース)

#### Knowledgeファイル
- **GitHubリポジトリ**に含める
- **S3/Cloud Storage**から読み込む

### オプション3: 代替プラットフォームを使用

Vercelの制約を回避するため、以下のプラットフォームを検討してください：

#### Railway
- ✅ ファイルシステムへの書き込み可能
- ✅ SQLiteサポート
- ✅ 簡単なデプロイ
- ✅ 無料プランあり

#### Render
- ✅ ファイルシステムへの書き込み可能
- ✅ SQLiteサポート
- ✅ 無料プランあり

#### Fly.io
- ✅ ファイルシステムへの書き込み可能
- ✅ Dockerサポート
- ✅ グローバルデプロイ

## 📋 Vercelデプロイ手順（オプション1: 最小限の変更）

### 1. 前提条件

- Vercelアカウント
- GitHubリポジトリ（推奨）

### 2. Knowledgeファイルの準備

```bash
# Knowledgeファイルをプロジェクトにコピー
mkdir -p knowledge
cp -r /path/to/knowledge/* knowledge/
```

### 3. 設定ファイルの変更

`app/core/config.py`を以下のように変更：

```python
# Knowledgeディレクトリを相対パスに変更
knowledge_dir: str = "./knowledge"

# データベースを/tmpに保存（一時的）
database_url: str = "sqlite:////tmp/rag_kanri.db"
```

### 4. Indexの事前ビルド

```bash
# ローカルでIndexをビルド
python -c "from app.services.rag_service import rag_service; rag_service.create_index()"

# storage/index/をリポジトリに含める
git add storage/index/
```

### 5. 環境変数の設定

Vercelダッシュボードで以下の環境変数を設定：

```
OPENAI_API_KEY=your_api_key
KNOWLEDGE_DIR=./knowledge
DATABASE_URL=sqlite:////tmp/rag_kanri.db
ADMIN_PASSWORD=your_password
```

### 6. デプロイ

```bash
# Vercel CLIを使用
vercel

# またはGitHubと連携して自動デプロイ
```

## 🚀 推奨: Railwayでのデプロイ

Vercelの制約を回避するため、**Railway**でのデプロイを推奨します。

### Railwayデプロイ手順

1. **Railwayアカウント作成**
   - https://railway.app/ にアクセス

2. **プロジェクト作成**
   - "New Project" → "Deploy from GitHub repo"

3. **環境変数の設定**
   ```
   OPENAI_API_KEY=your_api_key
   KNOWLEDGE_DIR=/app/knowledge
   DATABASE_URL=sqlite:////app/rag_kanri.db
   ADMIN_PASSWORD=your_password
   ```

4. **Knowledgeファイルのアップロード**
   - RailwayのファイルシステムにKnowledgeファイルをアップロード
   - または、GitHubリポジトリに含める

5. **デプロイ**
   - Railwayが自動的にデプロイします

### Railwayの利点

- ✅ ファイルシステムへの書き込み可能
- ✅ SQLiteサポート
- ✅ 永続的なストレージ
- ✅ 簡単なデプロイ
- ✅ 無料プランあり（$5/月のクレジット）

## 📝 まとめ

### Vercelデプロイの可否

**技術的には可能ですが、以下の制約があります：**

- ❌ ログ機能が動作しない（SQLiteが永続化されない）
- ❌ Index再構築が毎回必要（起動時に自動生成）
- ⚠️ Knowledgeファイルをリポジトリに含める必要がある

### 推奨事項

**本番環境では、以下のいずれかを推奨します：**

1. **Railway** - 最も簡単で制約が少ない
2. **Render** - 無料プランあり、簡単なデプロイ
3. **Fly.io** - Dockerサポート、グローバルデプロイ
4. **外部ストレージを使用したVercel** - PostgreSQL + Pineconeなど

現在のアプリケーション構成では、**Railway**が最も適しています。









