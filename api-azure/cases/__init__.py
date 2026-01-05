import azure.functions as func
import json
import os
import uuid
from azure.data.tables import TableServiceClient


def main(req: func.HttpRequest) -> func.HttpResponse:
    try:
        conn_str = os.environ["TABLE_CONNECTION_STRING"]
        table_name = os.environ["CASES_TABLE_NAME"]

        service = TableServiceClient.from_connection_string(conn_str)
        table = service.get_table_client(table_name)

        # ---------- GET /api/cases ----------
        if req.method == "GET":
            entities = table.list_entities()
            items = []

            for e in entities:
                items.append(dict(e))

            return func.HttpResponse(
                json.dumps({"ok": True, "items": items}, ensure_ascii=False),
                mimetype="application/json",
                status_code=200
            )

        # ---------- POST /api/cases ----------
        if req.method == "POST":
            body = req.get_json()

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
                json.dumps({"ok": True, "saved": entity}, ensure_ascii=False),
                mimetype="application/json",
                status_code=200
            )

        return func.HttpResponse("Method Not Allowed", status_code=405)

    except Exception as e:
        return func.HttpResponse(
            json.dumps({"ok": False, "error": str(e)}),
            mimetype="application/json",
            status_code=500
        )
