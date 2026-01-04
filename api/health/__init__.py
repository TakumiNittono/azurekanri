"""
Health check endpoint for Azure Functions
"""
import azure.functions as func
import json


def main(req: func.HttpRequest) -> func.HttpResponse:
    """
    Health check endpoint
    
    Returns:
        func.HttpResponse: {"status": "ok"} with 200 OK
    """
    return func.HttpResponse(
        json.dumps({"status": "ok"}),
        mimetype="application/json",
        status_code=200
    )

