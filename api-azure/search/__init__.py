import json
import azure.functions as func

def main(req: func.HttpRequest) -> func.HttpResponse:
    try:
        body = req.get_json()
        query = body.get("query", "")

        return func.HttpResponse(
            json.dumps({
                "answer": f"あなたの質問は『{query}』ですね（仮回答）",
                "sources": []
            }),
            mimetype="application/json",
            status_code=200
        )
    except Exception as e:
        return func.HttpResponse(
            json.dumps({"error": str(e)}),
            status_code=500
        )
