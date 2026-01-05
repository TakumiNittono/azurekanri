import azure.functions as func
import json

def main(req: func.HttpRequest) -> func.HttpResponse:
    try:
        body = req.get_json()
        return func.HttpResponse(
            json.dumps({
                "ok": True,
                "received": body
            }),
            status_code=200,
            mimetype="application/json"
        )
    except Exception as e:
        return func.HttpResponse(
            json.dumps({"ok": False, "error": str(e)}),
            status_code=400,
            mimetype="application/json"
        )
