# デプロイ手順書（PoC用）

## 概要

このドキュメントは、貯水槽修理案件管理システムのPoC環境へのデプロイ手順を説明します。

## 前提条件

- Python 3.11または3.12がインストールされていること
- サーバーへのSSHアクセス権限があること
- 必要なポート（8000など）が開放されていること

## デプロイ手順

### 1. サーバーへの接続

```bash
ssh user@your-server.com
```

### 2. プロジェクトディレクトリの作成

```bash
mkdir -p /opt/rag-kanri
cd /opt/rag-kanri
```

### 3. プロジェクトファイルの配置

Gitリポジトリからクローンする場合：

```bash
git clone <repository-url> .
```

または、ファイルを直接アップロード：

```bash
# ローカルから
scp -r rag-kanri/* user@your-server.com:/opt/rag-kanri/
```

### 4. Python仮想環境の作成

```bash
python3.12 -m venv venv
source venv/bin/activate
```

### 5. 依存パッケージのインストール

```bash
pip install --upgrade pip
pip install -r requirements.txt
```

### 6. 環境変数の設定

`.env`ファイルを作成：

```bash
nano .env
```

以下の内容を設定：

```env
# OpenAI API設定
OPENAI_API_KEY=your_openai_api_key_here

# Knowledgeディレクトリパス
KNOWLEDGE_DIR=/opt/rag-kanri/knowledge

# データベース設定
DATABASE_URL=sqlite:///./rag_kanri.db

# 管理者認証（本番では強力なパスワードに変更）
ADMIN_PASSWORD=your_strong_password_here

# アプリケーション設定
APP_NAME=貯水槽修理案件管理システム
DEBUG=False
SECRET_KEY=your_secret_key_here_change_in_production

# サーバー設定
HOST=0.0.0.0
PORT=8000
```

**重要**:
- `OPENAI_API_KEY`: 実際のOpenAI APIキーに置き換える
- `ADMIN_PASSWORD`: 強力なパスワードに変更する
- `SECRET_KEY`: ランダムな文字列に変更する
- `DEBUG`: 本番環境では`False`に設定する

### 7. Knowledgeディレクトリの配置

Knowledgeファイルを配置：

```bash
mkdir -p knowledge
# Knowledgeファイルを配置
# cp /path/to/knowledge/*.txt knowledge/
```

### 8. RAG Indexの初期構築

```bash
# 仮想環境を有効化
source venv/bin/activate

# PythonスクリプトでIndexを作成（または管理者画面から実行）
python -c "
from app.services.rag_service import rag_service
result = rag_service.create_index()
print(result)
"
```

### 9. アプリケーションの起動

#### 開発環境（手動起動）

```bash
source venv/bin/activate
uvicorn app.main:app --host 0.0.0.0 --port 8000
```

#### 本番環境（systemdサービス）

`/etc/systemd/system/rag-kanri.service`を作成：

```ini
[Unit]
Description=RAG Kanri Application
After=network.target

[Service]
Type=simple
User=your-user
WorkingDirectory=/opt/rag-kanri
Environment="PATH=/opt/rag-kanri/venv/bin"
ExecStart=/opt/rag-kanri/venv/bin/uvicorn app.main:app --host 0.0.0.0 --port 8000
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
```

サービスを有効化・起動：

```bash
sudo systemctl daemon-reload
sudo systemctl enable rag-kanri
sudo systemctl start rag-kanri
sudo systemctl status rag-kanri
```

### 10. リバースプロキシの設定（Nginx例）

`/etc/nginx/sites-available/rag-kanri`を作成：

```nginx
server {
    listen 80;
    server_name your-domain.com;

    location / {
        proxy_pass http://127.0.0.1:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
}
```

シンボリックリンクを作成：

```bash
sudo ln -s /etc/nginx/sites-available/rag-kanri /etc/nginx/sites-enabled/
sudo nginx -t
sudo systemctl reload nginx
```

### 11. 動作確認

```bash
# ヘルスチェック
curl http://localhost:8000/health

# ブラウザでアクセス
# http://your-domain.com
```

## ログの確認

### アプリケーションログ

```bash
# systemdサービスの場合
sudo journalctl -u rag-kanri -f

# 手動起動の場合
# コンソールに出力されます
```

### データベースログ

SQLiteデータベースは`/opt/rag-kanri/rag_kanri.db`に保存されます。

## バックアップ

### Knowledgeファイルのバックアップ

```bash
# バックアップスクリプト例
#!/bin/bash
BACKUP_DIR="/backup/rag-kanri"
DATE=$(date +%Y%m%d_%H%M%S)
mkdir -p $BACKUP_DIR
tar -czf $BACKUP_DIR/knowledge_$DATE.tar.gz /opt/rag-kanri/knowledge
```

### データベースのバックアップ

```bash
#!/bin/bash
BACKUP_DIR="/backup/rag-kanri"
DATE=$(date +%Y%m%d_%H%M%S)
mkdir -p $BACKUP_DIR
cp /opt/rag-kanri/rag_kanri.db $BACKUP_DIR/rag_kanri_$DATE.db
```

## 更新手順

### 1. アプリケーションの停止

```bash
sudo systemctl stop rag-kanri
```

### 2. コードの更新

```bash
cd /opt/rag-kanri
git pull  # またはファイルをアップロード
```

### 3. 依存パッケージの更新

```bash
source venv/bin/activate
pip install -r requirements.txt
```

### 4. RAG Indexの再構築（必要に応じて）

管理者画面から「RAG Index再構築」を実行

### 5. アプリケーションの起動

```bash
sudo systemctl start rag-kanri
```

## トラブルシューティング

詳細は`TROUBLESHOOTING.md`を参照してください。

## セキュリティ注意事項

- `.env`ファイルの権限を適切に設定（`chmod 600 .env`）
- 管理者パスワードを強力なものに変更
- HTTPSの使用を推奨（Let's Encryptなど）
- ファイアウォールで必要なポートのみ開放
- 定期的なバックアップの実施

## パフォーマンス最適化

- RAG Indexは`storage/index/`に保存されるため、SSDの使用を推奨
- 大量のKnowledgeファイルがある場合は、chunkサイズの調整を検討
- 本番環境では、GunicornなどのWSGIサーバーの使用を検討

