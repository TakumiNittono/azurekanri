import azure.functions as func
import json
import os
from azure.storage.blob import BlobServiceClient

# ---- 設定 ----
BLOB_CONN = os.environ["BLOB_CONNECTION_STRING"]
CONTAINER = os.environ["BLOB_CONTAINER_NAME"]

blob_service = BlobServiceClient.from_connection_string(BLOB_CONN)
container_client = blob_service.get_container_client(CONTAINER)


def build_query(case: dict) -> str:
    return " ".join([
        case.get("type", ""),
        case.get("priority", ""),
        case.get("location", ""),
        case.get("tank", ""),
        case.get("detail", "")
    ])


def retrieve_evidence(query: str, max_docs=3):
    """
    Blob全文検索（超安定RAG）
    """
    results = []
    keywords = query.split()

    for blob in container_client.list_blobs():
        blob_client = container_client.get_blob_client(blob.name)
        text = blob_client.download_blob().readall().decode("utf-8")

        score = sum(1 for k in keywords if k in text)

        if score > 0:
            results.append({
                "source": blob.name,
                "snippet": text[:300],
                "score": score
            })

    results.sort(key=lambda x: x["score"], reverse=True)
    return results[:max_docs]


def generate_answer(case: dict, evidences: list):
    reasons = "\n".join(
        [f"- {e['snippet']}" for e in evidences]
    )

    return f"""【結論】
本案件は対応が必要です。

【理由】
{reasons}

【推奨対応】
・現地確認
・応急処置
・必要に応じて部品交換
"""


def main(req: func.HttpRequest) -> func.HttpResponse:
    try:
        case = req.get_json()

        query = build_query(case)
        evidences = retrieve_evidence(query)
        answer = generate_answer(case, evidences)

        return func.HttpResponse(
            json.dumps({
                "answer": answer,
                "sources": evidences
            }, ensure_ascii=False),
            mimetype="application/json"
        )

    except Exception as e:
        return func.HttpResponse(
            json.dumps({"error": str(e)}),
            mimetype="application/json",
            status_code=500
        )
