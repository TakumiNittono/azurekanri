# トラブルシューティングガイド

## よくある問題と解決方法

### 1. サーバーが起動しない

#### 症状
```bash
$ uvicorn app.main:app --reload
Error: ...
```

#### 原因と解決方法

**原因1: ポートが既に使用されている**
```bash
# ポート8000が使用中か確認
lsof -i :8000

# プロセスを終了
kill -9 <PID>

# または別のポートを使用
uvicorn app.main:app --reload --port 8001
```

**原因2: 仮想環境が有効化されていない**
```bash
# 仮想環境を有効化
source venv/bin/activate

# パッケージがインストールされているか確認
pip list
```

**原因3: 環境変数が設定されていない**
```bash
# .envファイルが存在するか確認
ls -la .env

# 環境変数が正しく読み込まれているか確認
python -c "from app.core.config import settings; print(settings.openai_api_key[:10])"
```

---

### 2. OpenAI APIエラー

#### 症状
```
OpenAI API error: Invalid API key
```

#### 原因と解決方法

**原因1: APIキーが設定されていない**
```bash
# .envファイルを確認
cat .env | grep OPENAI_API_KEY

# 正しいAPIキーを設定
# .envファイルを編集
```

**原因2: APIキーが無効**
- OpenAIのダッシュボードでAPIキーを確認
- 新しいAPIキーを生成して設定

**原因3: APIレート制限に達した**
- しばらく待ってから再試行
- OpenAIのダッシュボードで使用状況を確認

---

### 3. RAG Indexが作成できない

#### 症状
```
Error creating index: ...
```

#### 原因と解決方法

**原因1: Knowledgeディレクトリが存在しない**
```bash
# ディレクトリの存在確認
ls -la /path/to/knowledge/

# .envファイルでパスを確認
cat .env | grep KNOWLEDGE_DIR
```

**原因2: Knowledgeファイルが存在しない**
```bash
# ファイルの存在確認
ls -la /path/to/knowledge/*.txt

# ファイルが存在しない場合は、Knowledgeファイルを配置
```

**原因3: ディスク容量不足**
```bash
# ディスク容量を確認
df -h

# 必要に応じて古いファイルを削除
```

**原因4: 権限の問題**
```bash
# ディレクトリの権限を確認
ls -ld /path/to/knowledge/

# 権限を修正（必要に応じて）
chmod 755 /path/to/knowledge/
```

---

### 4. データベースエラー

#### 症状
```
Database error: ...
```

#### 原因と解決方法

**原因1: データベースファイルの権限問題**
```bash
# データベースファイルの権限を確認
ls -la rag_kanri.db

# 権限を修正
chmod 644 rag_kanri.db
```

**原因2: データベースファイルが破損**
```bash
# データベースの整合性を確認
sqlite3 rag_kanri.db "PRAGMA integrity_check;"

# 破損している場合は、バックアップから復元
# または、データベースを再作成
rm rag_kanri.db
# アプリケーションを再起動（自動的に再作成されます）
```

---

### 5. 管理者ログインできない

#### 症状
```
Login failed
```

#### 原因と解決方法

**原因1: パスワードが間違っている**
```bash
# .envファイルでパスワードを確認
cat .env | grep ADMIN_PASSWORD

# 正しいパスワードを入力
```

**原因2: セッションクッキーが無効**
- ブラウザのクッキーをクリア
- 再度ログインを試行

**原因3: セッション管理の問題**
```bash
# サーバーを再起動
sudo systemctl restart rag-kanri
```

---

### 6. 見積書・発注書が生成できない

#### 症状
```
Error generating document
```

#### 原因と解決方法

**原因1: 日本語フォントがインストールされていない**
```bash
# macOSの場合（通常は問題なし）
# Linuxの場合、日本語フォントをインストール
sudo apt-get install fonts-noto-cjk  # Ubuntu/Debian
```

**原因2: ファイル名に不正な文字が含まれている**
- 案件名に特殊文字が含まれていないか確認
- 英数字とハイフン、アンダースコアのみを使用

**原因3: ディスク容量不足**
```bash
# ディスク容量を確認
df -h
```

---

### 7. ログが表示されない

#### 症状
```
No logs found
```

#### 原因と解決方法

**原因1: データベースにログが保存されていない**
```bash
# データベースを確認
sqlite3 rag_kanri.db "SELECT COUNT(*) FROM rag_logs;"

# RAG検索を実行してログが生成されるか確認
```

**原因2: フィルタ条件が厳しすぎる**
- フィルタ条件を緩和して再検索

---

### 8. パフォーマンスが遅い

#### 症状
- RAG検索に時間がかかる
- ページの読み込みが遅い

#### 原因と解決方法

**原因1: RAG Indexが大きすぎる**
- Knowledgeファイルの数を減らす
- chunkサイズを調整（`rag_service.py`の`chunk_size`を変更）

**原因2: サーバーリソース不足**
```bash
# CPU・メモリ使用状況を確認
top
htop

# 必要に応じてサーバーリソースを増やす
```

**原因3: ネットワーク遅延**
- OpenAI APIへの接続が遅い場合、リトライロジックが動作している可能性
- しばらく待ってから再試行

---

### 9. CORSエラー

#### 症状
```
CORS error: ...
```

#### 原因と解決方法

**原因1: フロントエンドとバックエンドのオリジンが異なる**
- `app/main.py`のCORS設定を確認
- PoCでは`allow_origins=["*"]`で全許可されているが、本番では適切に設定

---

### 10. モジュールが見つからない

#### 症状
```
ModuleNotFoundError: No module named 'app'
```

#### 原因と解決方法

**原因1: 仮想環境が有効化されていない**
```bash
source venv/bin/activate
```

**原因2: パッケージがインストールされていない**
```bash
pip install -r requirements.txt
```

**原因3: PYTHONPATHが設定されていない**
```bash
# プロジェクトディレクトリに移動
cd /path/to/rag-kanri

# または、PYTHONPATHを設定
export PYTHONPATH=/path/to/rag-kanri:$PYTHONPATH
```

---

## デバッグ方法

### ログの確認

```bash
# アプリケーションログ（systemdの場合）
sudo journalctl -u rag-kanri -f

# エラーログのみ
sudo journalctl -u rag-kanri -p err

# 最新の100行
sudo journalctl -u rag-kanri -n 100
```

### デバッグモードの有効化

`.env`ファイルで`DEBUG=True`に設定：

```env
DEBUG=True
```

### Pythonデバッガーの使用

```python
# コードにブレークポイントを設定
import pdb; pdb.set_trace()
```

---

## サポート

問題が解決しない場合は、以下を確認してください：

1. `PROGRESS.md`で実装状況を確認
2. `REQUIREMENTS.md`で要件を確認
3. `API_SPEC.md`でAPI仕様を確認
4. エラーメッセージの全文を確認
5. ログファイルを確認

---

## よくある質問（FAQ）

### Q: Knowledgeファイルを追加した後、どうすればいいですか？

A: 管理者画面から「RAG Index再構築」を実行してください。

### Q: パスワードを忘れました

A: `.env`ファイルの`ADMIN_PASSWORD`を確認または変更してください。

### Q: データベースをリセットしたい

A: `rag_kanri.db`ファイルを削除して、アプリケーションを再起動してください。

### Q: 複数のユーザーが同時に使用できますか？

A: はい、PoC版では複数のユーザーが同時に使用できます。ただし、RAG Index再構築中は検索が遅くなる可能性があります。

