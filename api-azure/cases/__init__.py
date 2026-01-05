import azure.functions as func
import json
import os
import uuid
from datetime import datetime, timezone
from azure.data.tables import TableServiceClient


def main(req: func.HttpRequest) -> func.HttpResponse:
    try:
        # GET: 一覧取得
        if req.method == "GET":
            conn_str = os.environ["TABLE_CONNECTION_STRING"]
            table_name = os.environ["CASES_TABLE_NAME"]

            service = TableServiceClient.from_connection_string(conn_str)
            table = service.get_table_client(table_name)

            entities = list(table.list_entities())

            # createdAt 降順ソート
            entities.sort(
                key=lambda x: x.get("createdAt", ""),
                reverse=True
            )

            return func.HttpResponse(
                json.dumps({"ok": True, "items": entities}, ensure_ascii=False),
                mimetype="application/json",
                status_code=200
            )

        # POST: 新規作成
        body = req.get_json()

        conn_str = os.environ["TABLE_CONNECTION_STRING"]
        table_name = os.environ["CASES_TABLE_NAME"]

        service = TableServiceClient.from_connection_string(conn_str)
        table = service.get_table_client(table_name)

        now = datetime.now(timezone.utc).isoformat()

        entity = {
            "PartitionKey": "CASE",
            "RowKey": str(uuid.uuid4()),
            "title": body.get("title"),
            "type": body.get("type"),
            "priority": body.get("priority"),
            "location": body.get("location"),
            "tank": body.get("tank"),
            "detail": body.get("detail"),
            "createdAt": now
        }

        table.create_entity(entity)

        return func.HttpResponse(
            json.dumps({"ok": True, "saved": entity}, ensure_ascii=False),
            mimetype="application/json",
            status_code=200
        )

    except Exception as e:
        return func.HttpResponse(
            json.dumps({"ok": False, "error": str(e)}, ensure_ascii=False),
            mimetype="application/json",
            status_code=500
        )