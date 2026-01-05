import azure.functions as func
import json

def main(req: func.HttpRequest) -> func.HttpResponse:
    try:
        data = req.get_json()
        query = data.get("query", "")

        return func.HttpResponse(
            json.dumps({
                "query": query,
                "result": "dummy search result"
            }),
            mimetype="application/json",
            status_code=200
        )

    except Exception as e:
        return func.HttpResponse(
            json.dumps({"error": str(e)}),
            mimetype="application/json",
            status_code=400
        )
