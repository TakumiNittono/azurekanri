# Azure移行 クイックスタートガイド

## 📋 このドキュメントについて

このドキュメントは、Azure.mdの要件定義書に基づいて、PoC版システムをAzureサーバーレス構成に移行するための**超詳しい手順**をまとめたものです。

## 📚 関連ドキュメント

1. **`Azure.md`** - 要件定義書（移行の全体像と設計）
2. **`AZURE_MIGRATION_GUIDE.md`** - 詳細な移行手順書
3. **`MIGRATION_CODE_EXAMPLES.md`** - コード変更例集
4. **`MIGRATION_SUMMARY.md`** - このドキュメント（クイックスタート）

---

## 🎯 移行の全体像

### 現在の構成 → 移行後の構成

```
【現在（PoC版）】
FastAPI (ローカル実行)
  ├─ SQLite (ローカルDB)
  ├─ ローカルファイルシステム
  └─ 簡易認証

【移行後（Azureサーバーレス）】
Azure Static Web Apps (フロントエンド)
  ├─ Azure Functions (API)
  ├─ Azure Table Storage (ログ)
  ├─ Azure Blob Storage (Knowledge/RAG Index)
  └─ Azure Entra ID (認証)
```

### 主な変更点

| 項目 | 現在 | 移行後 |
|------|------|--------|
| **Webサーバー** | FastAPI (uvicorn) | Azure Functions |
| **データベース** | SQLite | Azure Table Storage |
| **ファイルストレージ** | ローカルファイルシステム | Azure Blob Storage |
| **認証** | 簡易認証 | Azure Entra ID |
| **フロントエンド** | FastAPI Templates | Azure Static Web Apps |
| **コスト** | ローカル（無料） | 月額1,000〜5,000円（従量課金） |

---

## 🚀 移行手順の全体フロー

### フェーズ1: 事前準備（1日）

- [ ] Azureアカウント作成
- [ ] Azure CLIインストール・ログイン
- [ ] GitHubアカウント準備
- [ ] 必要なツールのインストール

### フェーズ2: Azureリソース作成（1日）

- [ ] リソースグループ作成
- [ ] ストレージアカウント作成
- [ ] Blob Storageコンテナ作成
- [ ] Azure Functionsアプリ作成
- [ ] Azure Static Web Apps作成
- [ ] Azure Entra IDアプリ登録

### フェーズ3: コード修正（2-3日）

- [ ] `app/core/config.py` をAzure対応に修正
- [ ] `app/services/knowledge_service.py` をBlob Storage対応に修正
- [ ] `app/services/log_service.py` をTable Storage対応に修正
- [ ] `app/services/rag_service.py` をBlob Storage対応に修正
- [ ] `app/core/auth.py` をAzure Entra ID対応に修正
- [ ] Azure Functions用のコード作成

### フェーズ4: データ移行（1日）

- [ ] KnowledgeファイルをBlob Storageに移行
- [ ] SQLiteログをTable Storageに移行（オプション）
- [ ] RAG Indexを再構築

### フェーズ5: デプロイ（1日）

- [ ] Azure Functionsにデプロイ
- [ ] Static Web Appsにデプロイ
- [ ] 動作確認

### フェーズ6: テスト・調整（1-2日）

- [ ] 機能テスト
- [ ] パフォーマンステスト
- [ ] コスト確認
- [ ] ドキュメント更新

**合計: 約1週間**

---

## 📝 詳細手順へのリンク

### 1. 事前準備

詳細は `AZURE_MIGRATION_GUIDE.md` の「2. 事前準備」を参照：

- Azure CLIのインストール
- Pythonパッケージの追加
- プロジェクト構造の準備

### 2. Azureリソース作成

詳細は `AZURE_MIGRATION_GUIDE.md` の「3. フェーズ1: Azureリソースの作成」を参照：

```bash
# リソースグループ作成
az group create --name rg-ragkanri --location japaneast

# ストレージアカウント作成
STORAGE_ACCOUNT_NAME="stragkanri$(date +%s | cut -c1-10)"
az storage account create \
  --name $STORAGE_ACCOUNT_NAME \
  --resource-group rg-ragkanri \
  --location japaneast \
  --sku Standard_LRS

# Azure Functions作成
FUNCTION_APP_NAME="func-ragkanri-$(date +%s | cut -c1-10)"
az functionapp create \
  --name $FUNCTION_APP_NAME \
  --resource-group rg-ragkanri \
  --storage-account $STORAGE_ACCOUNT_NAME \
  --consumption-plan-location japaneast \
  --runtime python \
  --runtime-version 3.11
```

### 3. コード修正

詳細は `MIGRATION_CODE_EXAMPLES.md` を参照：

#### 3.1 設定ファイルの修正

`app/core/config.py` をAzure対応に変更（`MIGRATION_CODE_EXAMPLES.md` の「1. 設定ファイルの変更」参照）

#### 3.2 Knowledge Serviceの修正

`app/services/knowledge_service.py` をBlob Storage対応に変更（`MIGRATION_CODE_EXAMPLES.md` の「2. Knowledge Serviceの変更」参照）

#### 3.3 Log Serviceの修正

`app/services/log_service.py` をTable Storage対応に変更（`MIGRATION_CODE_EXAMPLES.md` の「3. Log Serviceの変更」参照）

#### 3.4 RAG Serviceの修正

`app/services/rag_service.py` をBlob Storage対応に変更（`MIGRATION_CODE_EXAMPLES.md` の「4. RAG Serviceの変更」参照）

#### 3.5 認証の修正

`app/core/auth.py` をAzure Entra ID対応に変更（`MIGRATION_CODE_EXAMPLES.md` の「5. 認証の変更」参照）

#### 3.6 Azure Functionsの作成

`api/` ディレクトリにAzure Functions用のコードを作成（`MIGRATION_CODE_EXAMPLES.md` の「6. Azure Functions実装例」参照）

### 4. データ移行

詳細は `AZURE_MIGRATION_GUIDE.md` の「5. フェーズ3: データ移行」を参照：

```bash
# Knowledgeファイル移行
export BLOB_STORAGE_CONNECTION_STRING="<接続文字列>"
python scripts/migrate_knowledge_to_blob.py
```

### 5. デプロイ

詳細は `AZURE_MIGRATION_GUIDE.md` の「6. フェーズ4: Azure Functionsへのデプロイ」と「7. フェーズ5: Static Web Appsへのデプロイ」を参照：

- GitHub Actionsで自動デプロイ設定
- 手動デプロイも可能

---

## 🔧 よくある質問（FAQ）

### Q1: 移行にどのくらい時間がかかりますか？

**A**: 約1週間です。詳細は上記の「移行手順の全体フロー」を参照してください。

### Q2: 既存のデータはどうなりますか？

**A**: 
- Knowledgeファイル: Blob Storageに移行（既存ファイルは保持）
- SQLiteログ: Table Storageに移行可能（オプション）
- RAG Index: 再構築を推奨（既存ファイルのコピーも可能）

### Q3: ローカル環境でも動作しますか？

**A**: はい。`local.settings.json` を設定すれば、Azure Functions Core Toolsでローカル実行可能です。

### Q4: コストはどのくらいかかりますか？

**A**: 月額1,000〜5,000円程度（利用量次第）。固定費はありません。詳細は `Azure.md` の「10. コスト設計」を参照してください。

### Q5: 移行中にサービスを停止する必要がありますか？

**A**: いいえ。並行運用が可能です。本番切り替え時のみ数分のダウンタイムが発生します。

### Q6: エラーが発生した場合はどうすればよいですか？

**A**: `AZURE_MIGRATION_GUIDE.md` の「9. トラブルシューティング」を参照してください。

---

## 📖 次のステップ

1. **`AZURE_MIGRATION_GUIDE.md`** を読んで、詳細な移行手順を理解する
2. **`MIGRATION_CODE_EXAMPLES.md`** を参照して、コード変更例を確認する
3. **フェーズ1（事前準備）** から順番に実行する
4. 各フェーズで動作確認を行う
5. 問題があれば、トラブルシューティングセクションを参照する

---

## 🎉 移行完了後のチェックリスト

- [ ] Static Web Appsにアクセスできる
- [ ] Azure Entra IDでログインできる
- [ ] RAG検索APIが動作する
- [ ] Knowledgeファイル一覧が取得できる
- [ ] RAG Indexが作成できる
- [ ] ログがTable Storageに保存される
- [ ] ドキュメント生成が動作する
- [ ] コストが予想範囲内である
- [ ] パフォーマンスが問題ない

---

## 📞 サポート

移行中に問題が発生した場合：

1. `AZURE_MIGRATION_GUIDE.md` の「9. トラブルシューティング」を確認
2. Azure Portalのログを確認
3. GitHub Issuesで質問（プロジェクトがGitHubで管理されている場合）

---

**移行の成功をお祈りしています！** 🚀

