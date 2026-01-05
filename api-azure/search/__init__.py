import azure.functions as func
import json

def main(req: func.HttpRequest) -> func.HttpResponse:
    try:
        body = req.get_body()
        body_str = body.decode("utf-8") if body else "{}"
        data = json.loads(body_str)

        query = data.get("query", "")

        return func.HttpResponse(
            json.dumps({
                "ok": True,
                "query": query,
                "message": "search endpoint works"
            }),
            mimetype="application/json",
            status_code=200
        )

    except Exception as e:
        return func.HttpResponse(
            json.dumps({
                "ok": False,
                "error": str(e)
            }),
            mimetype="application/json",
            status_code=500
        )
