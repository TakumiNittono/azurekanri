import azure.functions as func
import json

def main(req: func.HttpRequest) -> func.HttpResponse:
    return func.HttpResponse(
        json.dumps({"ok": True, "msg": "cases booted"}),
        mimetype="application/json",
        status_code=200
    )
