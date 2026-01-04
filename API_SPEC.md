# API仕様書（簡易版）

## 概要

このドキュメントは、貯水槽修理案件管理システムのAPI仕様書です。

## ベースURL

```
http://localhost:8000
```

## 認証

### 管理者認証

管理者機能を使用するには、まずログインが必要です。

**エンドポイント**: `POST /api/admin/login`

**リクエストボディ**:
```json
{
  "password": "admin123"
}
```

**レスポンス**:
```json
{
  "success": true,
  "message": "Login successful"
}
```

ログイン後、セッションクッキーが設定されます。管理者APIはこのクッキーを確認します。

---

## 一般ユーザー向けAPI

### 1. Knowledgeファイル一覧取得

**エンドポイント**: `GET /api/knowledge/files`

**説明**: Knowledgeファイルの一覧を取得します。

**レスポンス**:
```json
[
  {
    "filename": "price_repair_leak.txt",
    "size": 1024,
    "updated_at": 1703123456.789,
    "file_type": "price"
  }
]
```

### 2. Knowledgeファイル内容取得

**エンドポイント**: `GET /api/knowledge/files/{filename}`

**パラメータ**:
- `filename`: ファイル名（例: `price_repair_leak.txt`）

**レスポンス**:
```json
{
  "filename": "price_repair_leak.txt",
  "content": "ファイルの内容...",
  "size": 1024,
  "updated_at": 1703123456.789
}
```

### 3. RAG検索

**エンドポイント**: `POST /api/rag/search`

**リクエストボディ**:
```json
{
  "query": "漏水の修理について",
  "top_k": 5
}
```

**レスポンス**:
```json
{
  "success": true,
  "query": "漏水の修理について",
  "results": [
    {
      "text": "検索結果のテキスト...",
      "score": 0.95,
      "file_name": "price_repair_leak.txt",
      "file_type": "price",
      "chunk_index": 0
    }
  ],
  "referenced_files": ["price_repair_leak.txt"],
  "total_results": 5
}
```

### 4. RAG回答生成

**エンドポイント**: `POST /api/rag/answer`

**リクエストボディ**:
```json
{
  "query": "漏水の修理について、緊急の案件です。",
  "case_info": {
    "case_name": "本館貯水槽漏水修理",
    "repair_type": "漏水",
    "urgency": "緊急",
    "location": "本館3階",
    "tank_size": "10トン",
    "description": "詳細説明"
  },
  "top_k": 5
}
```

**レスポンス**:
```json
{
  "success": true,
  "query": "漏水の修理について、緊急の案件です。",
  "answer": "生成された回答テキスト...",
  "reasoning": "参照したKnowledgeファイル: price_repair_leak.txt, contractor_emergency.txt",
  "referenced_files": ["price_repair_leak.txt", "contractor_emergency.txt"],
  "search_results": [...]
}
```

### 5. 見積書生成

**エンドポイント**: `POST /api/documents/estimate`

**リクエストボディ**:
```json
{
  "case_info": {
    "case_name": "本館貯水槽漏水修理",
    "repair_type": "漏水",
    "urgency": "緊急",
    "location": "本館3階",
    "tank_size": "10トン"
  },
  "rag_answer": "生成された回答テキスト..."
}
```

**レスポンス**: Word形式（.docx）のファイルがダウンロードされます。

### 6. 発注書生成

**エンドポイント**: `POST /api/documents/order`

**リクエストボディ**:
```json
{
  "case_info": {
    "case_name": "本館貯水槽漏水修理",
    "repair_type": "漏水",
    "urgency": "緊急",
    "location": "本館3階",
    "tank_size": "10トン"
  },
  "rag_answer": "生成された回答テキスト...",
  "contractor_name": "業者名",
  "order_price": 500000
}
```

**レスポンス**: Word形式（.docx）のファイルがダウンロードされます。

---

## 管理者向けAPI

### 1. Knowledgeファイル一覧取得（管理者）

**エンドポイント**: `GET /api/admin/knowledge/files`

**認証**: 管理者ログイン必須

**レスポンス**: 一般ユーザー向けAPIと同じ形式

### 2. Knowledgeファイル内容取得（管理者）

**エンドポイント**: `GET /api/admin/knowledge/files/{filename}`

**認証**: 管理者ログイン必須

**レスポンス**: 一般ユーザー向けAPIと同じ形式

### 3. Knowledgeファイル追加

**エンドポイント**: `POST /api/admin/knowledge/files`

**認証**: 管理者ログイン必須

**リクエストボディ**:
```json
{
  "filename": "new_file.txt",
  "content": "ファイルの内容..."
}
```

**レスポンス**:
```json
{
  "filename": "new_file.txt",
  "size": 1024,
  "updated_at": 1703123456.789,
  "file_type": "unknown"
}
```

### 4. Knowledgeファイル削除

**エンドポイント**: `DELETE /api/admin/knowledge/files/{filename}`

**認証**: 管理者ログイン必須

**レスポンス**:
```json
{
  "success": true,
  "message": "File deleted successfully"
}
```

### 5. RAG Index作成

**エンドポイント**: `POST /api/rag/index/create`

**認証**: 管理者ログイン必須

**レスポンス**:
```json
{
  "status": "success",
  "message": "Index created successfully",
  "indexed_files": 30,
  "total_chunks": 150
}
```

### 6. RAG Index再構築

**エンドポイント**: `POST /api/rag/index/reindex`

**認証**: 管理者ログイン必須

**レスポンス**: RAG Index作成と同じ形式

### 7. RAG Index状態確認

**エンドポイント**: `GET /api/rag/index/status`

**レスポンス**:
```json
{
  "is_ready": true,
  "indexed_files": 30,
  "total_chunks": 150,
  "last_updated": "2024-12-25T10:00:00"
}
```

### 8. ログ一覧取得

**エンドポイント**: `GET /api/admin/logs`

**認証**: 管理者ログイン必須

**クエリパラメータ**:
- `start_date`: 開始日時（YYYY-MM-DD形式、オプション）
- `end_date`: 終了日時（YYYY-MM-DD形式、オプション）
- `user_id`: ユーザーID（オプション）
- `case_id`: 案件ID（オプション）
- `limit`: 取得件数（デフォルト: 100）

**レスポンス**:
```json
{
  "logs": [
    {
      "id": 1,
      "case_id": "REP-2024-001",
      "timestamp": "2024-12-25T10:00:00",
      "processing_time": 2.5,
      "referenced_files_count": 3
    }
  ],
  "total": 100
}
```

### 9. ログ詳細取得

**エンドポイント**: `GET /api/admin/logs/{log_id}`

**認証**: 管理者ログイン必須

**レスポンス**:
```json
{
  "id": 1,
  "case_id": "REP-2024-001",
  "input_data": {...},
  "rag_queries": ["漏水の修理について"],
  "referenced_files": ["price_repair_leak.txt"],
  "generated_answer": "生成された回答...",
  "processing_time": 2.5,
  "model_name": "gpt-4o-mini",
  "timestamp": "2024-12-25T10:00:00"
}
```

---

## エラーレスポンス

すべてのAPIエンドポイントは、エラー時に以下の形式でレスポンスを返します：

```json
{
  "detail": "エラーメッセージ"
}
```

**HTTPステータスコード**:
- `400`: Bad Request（リクエストが不正）
- `401`: Unauthorized（認証が必要）
- `403`: Forbidden（権限がない）
- `404`: Not Found（リソースが見つからない）
- `500`: Internal Server Error（サーバーエラー）

---

## 補足

- 詳細なAPI仕様は、Swagger UI（`http://localhost:8000/docs`）で確認できます
- PoC版のため、認証は簡易実装です
- 本番環境では適切なセキュリティ対策が必要です

