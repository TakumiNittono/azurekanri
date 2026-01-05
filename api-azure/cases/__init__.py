import azure.functions as func
import json
import os
import uuid
from azure.data.tables import TableServiceClient


def main(req: func.HttpRequest) -> func.HttpResponse:
    try:
        body = req.get_json()

        # 環境変数
        conn_str = os.environ["TABLE_CONNECTION_STRING"]
        table_name = os.environ["CASES_TABLE_NAME"]

        service = TableServiceClient.from_connection_string(conn_str)
        table = service.get_table_client(table_name)

        entity = {
            "PartitionKey": "CASE",
            "RowKey": str(uuid.uuid4()),
            "title": body.get("title"),
            "type": body.get("type"),
            "priority": body.get("priority"),
            "location": body.get("location"),
            "tank": body.get("tank"),
            "detail": body.get("detail"),
        }

        table.create_entity(entity)

        return func.HttpResponse(
            json.dumps({"ok": True, "saved": entity}),
            mimetype="application/json",
            status_code=200
        )

    except Exception as e:
        return func.HttpResponse(
            json.dumps({"ok": False, "error": str(e)}),
            mimetype="application/json",
            status_code=500
        )
