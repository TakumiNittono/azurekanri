"""
RAG検索サービス（Index作成・管理）
"""
from pathlib import Path
from typing import List, Optional
from llama_index.core import Document, VectorStoreIndex, StorageContext, load_index_from_storage
from llama_index.core.node_parser import SimpleNodeParser
from llama_index.embeddings.openai import OpenAIEmbedding
from llama_index.llms.openai import OpenAI
from app.core.config import settings
from app.services.knowledge_service import knowledge_service
import os
import json
import re


class RAGService:
    """RAG検索サービス"""
    
    def __init__(self):
        self.knowledge_dir = Path(settings.knowledge_dir)
        self.index_dir = Path("./storage/index")
        self.index_dir.mkdir(parents=True, exist_ok=True)
        
        # OpenAI設定
        self.embed_model = OpenAIEmbedding(api_key=settings.openai_api_key)
        self.llm = OpenAI(api_key=settings.openai_api_key, model="gpt-4o-mini")
        
        # Index（遅延読み込み）
        self._index: Optional[VectorStoreIndex] = None
    
    def create_index(self) -> dict:
        """
        KnowledgeファイルからIndexを作成
        
        Returns:
            dict: 作成結果
                - success: 成功フラグ
                - message: メッセージ
                - indexed_files: インデックス化したファイル数
                - total_chunks: 総chunk数
        """
        try:
            # Knowledgeファイル一覧を取得
            files = knowledge_service.get_file_list()
            
            if not files:
                return {
                    "success": False,
                    "message": "No knowledge files found",
                    "indexed_files": 0,
                    "total_chunks": 0,
                }
            
            # Documentを作成
            documents = []
            for file_info in files:
                try:
                    file_content = knowledge_service.get_file_content(file_info["filename"])
                    content = file_content["content"]
                    
                    # Document作成（メタデータ付与）
                    doc = Document(
                        text=content,
                        metadata={
                            "file_name": file_info["filename"],
                            "file_type": file_info["file_type"],
                            "file_size": file_info["size"],
                            "updated_at": file_info["updated_at"],
                        }
                    )
                    documents.append(doc)
                except Exception as e:
                    print(f"Error processing file {file_info['filename']}: {e}")
                    continue
            
            if not documents:
                return {
                    "success": False,
                    "message": "No documents could be created",
                    "indexed_files": 0,
                    "total_chunks": 0,
                }
            
            # chunk分割（200-500文字、意味的なまとまりを優先）
            node_parser = SimpleNodeParser.from_defaults(
                chunk_size=400,  # 400文字を目安
                chunk_overlap=50,  # 50文字のオーバーラップ
            )
            
            # Documentをchunkに分割
            nodes = []
            for doc in documents:
                doc_nodes = node_parser.get_nodes_from_documents([doc])
                # chunk_indexをメタデータに追加
                for idx, node in enumerate(doc_nodes):
                    node.metadata["chunk_index"] = idx
                    node.metadata["file_name"] = doc.metadata["file_name"]
                    node.metadata["file_type"] = doc.metadata["file_type"]
                nodes.extend(doc_nodes)
            
            # Index作成
            index = VectorStoreIndex(
                nodes=nodes,
                embed_model=self.embed_model,
            )
            
            # Indexを保存
            self._save_index(index)
            
            # Indexをメモリに保持
            self._index = index
            
            return {
                "success": True,
                "message": "Index created successfully",
                "indexed_files": len(documents),
                "total_chunks": len(nodes),
            }
            
        except Exception as e:
            return {
                "success": False,
                "message": f"Error creating index: {str(e)}",
                "indexed_files": 0,
                "total_chunks": 0,
            }
    
    def load_index(self) -> bool:
        """
        保存されたIndexを読み込む
        
        Returns:
            bool: 読み込み成功フラグ
        """
        try:
            if not self.index_dir.exists():
                return False
            
            # Indexが保存されているか確認
            if not (self.index_dir / "docstore.json").exists():
                return False
            
            # Indexを読み込む
            storage_context = StorageContext.from_defaults(persist_dir=str(self.index_dir))
            self._index = load_index_from_storage(
                storage_context,
                embed_model=self.embed_model,
            )
            return True
        except Exception as e:
            print(f"Error loading index: {e}")
            return False
    
    def _save_index(self, index: VectorStoreIndex):
        """
        Indexを保存
        
        Args:
            index: VectorStoreIndex
        """
        index.storage_context.persist(persist_dir=str(self.index_dir))
    
    def get_index(self) -> Optional[VectorStoreIndex]:
        """
        Indexを取得（遅延読み込み）
        
        Returns:
            Optional[VectorStoreIndex]: Index（存在しない場合はNone）
        """
        if self._index is None:
            # Indexが読み込まれていない場合は読み込む
            if not self.load_index():
                # Indexが存在しない場合は作成
                result = self.create_index()
                if not result["success"]:
                    return None
        return self._index
    
    def is_index_ready(self) -> bool:
        """
        Indexが準備できているか確認
        
        Returns:
            bool: Indexが準備できている場合True
        """
        if self._index is not None:
            return True
        return self.load_index()
    
    def search(self, query: str, top_k: int = 5) -> dict:
        """
        RAG検索を実行（LLM統合なし、検索結果のみ返す）
        
        Args:
            query: 検索クエリ
            top_k: 返す検索結果の数（デフォルト: 5）
            
        Returns:
            dict: 検索結果
                - success: 成功フラグ
                - query: 検索クエリ
                - results: 検索結果のリスト
                    - text: 検索結果のテキスト
                    - score: 類似度スコア
                    - file_name: 参照ファイル名
                    - file_type: ファイル種別
                    - chunk_index: chunk番号
                - referenced_files: 参照されたファイル名の一覧（重複なし）
        """
        try:
            # Indexを取得
            index = self.get_index()
            if index is None:
                return {
                    "success": False,
                    "query": query,
                    "message": "Index not found. Please create index first.",
                    "results": [],
                    "referenced_files": [],
                }
            
            # 検索クエリを実行（Retrieverを使用して検索結果のみ取得）
            retriever = index.as_retriever(similarity_top_k=top_k)
            nodes = retriever.retrieve(query)
            
            # 検索結果を整形
            results = []
            referenced_files = set()
            
            # 検索結果からノード情報を取得
            for node_with_score in nodes:
                node = node_with_score.node if hasattr(node_with_score, "node") else node_with_score
                score = node_with_score.score if hasattr(node_with_score, "score") else 0.0
                
                # メタデータから情報を取得
                metadata = node.metadata if hasattr(node, "metadata") else {}
                file_name = metadata.get("file_name", "unknown")
                file_type = metadata.get("file_type", "unknown")
                chunk_index = metadata.get("chunk_index", -1)
                
                # テキストを取得
                text = node.text if hasattr(node, "text") else node.get_content() if hasattr(node, "get_content") else ""
                
                # ノードID（chunk_id）を取得
                chunk_id = node.node_id if hasattr(node, "node_id") else node.id_ if hasattr(node, "id_") else None
                
                results.append({
                    "chunk_id": chunk_id,
                    "text": text,
                    "score": float(score),
                    "file_name": file_name,
                    "file_type": file_type,
                    "chunk_index": chunk_index,
                })
                
                referenced_files.add(file_name)
            
            return {
                "success": True,
                "query": query,
                "results": results,
                "referenced_files": list(referenced_files),
                "total_results": len(results),
            }
            
        except Exception as e:
            return {
                "success": False,
                "query": query,
                "message": f"Search error: {str(e)}",
                "results": [],
                "referenced_files": [],
            }
    
    def generate_answer(self, query: str, case_info: Optional[dict] = None, top_k: int = 5) -> dict:
        """
        RAG検索結果を基にLLMで回答を生成
        
        Args:
            query: 検索クエリ
            case_info: 案件情報（オプション）
            top_k: 検索結果の数（デフォルト: 5）
            
        Returns:
            dict: 回答生成結果
                - success: 成功フラグ
                - query: 検索クエリ
                - answer: 生成された回答
                - reasoning: 判断理由（参照ファイル名を含む）
                - referenced_files: 参照されたファイル名の一覧
                - search_results: 検索結果（デバッグ用）
        """
        import time
        max_retries = 3
        retry_delay = 1
        
        for attempt in range(max_retries):
            try:
                # まず検索を実行
                search_result = self.search(query, top_k=top_k)
                
                if not search_result["success"] or not search_result["results"]:
                    return {
                        "success": False,
                        "query": query,
                        "answer": "",
                        "reasoning": "",
                        "referenced_files": [],
                        "message": search_result.get("message", "No search results found"),
                    }
                
                # プロンプトテンプレートを作成
                # 事例番号を抽出する関数
                def extract_case_numbers(text: str) -> List[str]:
                    """テキストから事例番号を抽出"""
                    case_numbers = []
                    # 様々な形式の事例番号パターンを検出
                    patterns = [
                        r'事例[No\.\s]*[#\s]*(\d+)',
                        r'ケース[#\s]*(\d+)',
                        r'事例番号[#\s]*(\d+)',
                        r'Case[#\s]*(\d+)',
                        r'CASE[#\s]*(\d+)',
                        r'事例\s*(\d+)',
                        r'ケース\s*(\d+)',
                    ]
                    for pattern in patterns:
                        matches = re.findall(pattern, text, re.IGNORECASE)
                        case_numbers.extend(matches)
                    return list(set(case_numbers))  # 重複を除去
                
                # プロンプトの長さを制限するため、検索結果を最大10件に制限
                max_results = min(10, len(search_result["results"]))
                context_text = "\n\n".join([
                    f"[{idx+1}] {result['text'][:1000]}\n(出典: {result['file_name']})"  # 各結果を1000文字に制限
                    for idx, result in enumerate(search_result["results"][:max_results])
                ])
                
                # 検索結果から事例番号を抽出
                all_case_numbers = []
                for result in search_result["results"]:
                    case_nums = extract_case_numbers(result.get("text", ""))
                    all_case_numbers.extend(case_nums)
                all_case_numbers = sorted(set(all_case_numbers), key=lambda x: int(x) if x.isdigit() else 0)
                
                # 検索結果から業者名と事例番号の対応を抽出
                contractor_case_mapping = {}
                for result in search_result["results"]:
                    text = result.get("text", "")
                    # 業者名を抽出
                    contractor_match = re.search(r'対応業者[：:]\s*([^\n]+)', text)
                    if contractor_match:
                        contractor_name = contractor_match.group(1).strip()
                        # この業者に関連する事例番号を抽出
                        case_nums = extract_case_numbers(text)
                        if case_nums:
                            if contractor_name not in contractor_case_mapping:
                                contractor_case_mapping[contractor_name] = []
                            contractor_case_mapping[contractor_name].extend(case_nums)
                
                referenced_files = search_result["referenced_files"]
                
                # 案件情報があれば追加
                case_context = ""
                if case_info:
                    case_context = f"""
【案件情報】
- 修理種別: {case_info.get('repair_type', '不明')}
- 緊急度: {case_info.get('urgency', '不明')}
- 現場情報: {case_info.get('location', '不明')}
"""
                
                prompt = f"""あなたはビルメンテナンス業務の専門家です。
以下の情報を基に、貯水槽修理案件の判断支援情報を提供してください。

{case_context}
【検索クエリ】
{query}

【参考情報（Knowledge）】
{context_text}

【検索結果から抽出された事例番号】（参考）
{', '.join([f'事例No.{case_num}' for case_num in all_case_numbers[:10]]) if all_case_numbers else "なし"}

【出力要件】
以下の形式で回答してください：

1. **推奨業者候補**（最大3社）
   各業者について、以下の形式で記載してください：
   - **業者名**（参照ファイル: ファイル名1.txt, ファイル名2.txt）
     - 選定理由：参照したKnowledgeファイル名と事例番号を必ず明記（例：「contractor_case_studies.txtの過去事例No.1より、深夜の緊急対応実績がある」）
     - 対応可能な緊急度（参照ファイル: ファイル名.txt）
     - 想定価格帯：金額（参照ファイル: ファイル名.txt）
     - 参照事例番号：選定理由で言及した事例番号を必ず「事例No.XX」の形式で記載すること（例：「事例No.6」「事例No.10」）。選定理由に「事例6」「事例10」「Case 6」などの形式で事例番号が含まれている場合は、必ず「事例No.6」「事例No.10」の形式に統一して記載すること。「該当なし」「情報不足」とは記載しないこと。

2. **想定価格情報**
   - 相場価格帯（最低〜最高）
   - 人件費目安
   - 材料費目安
   - 高額/低額ケースの説明

3. **判断理由**
   - 参照したKnowledgeファイル名を明記してください
   - 各ファイルから抽出した根拠情報

4. **リスク・注意事項**
   - 法令要件
   - 安全上の注意点
   - 過去事例からの教訓

5. **緊急度評価**
   - AIによる緊急度評価
   - 評価理由

【重要】
- 各業者名の横に必ず「（参照ファイル: ファイル名1.txt, ファイル名2.txt）」の形式で参照ファイル名を明記すること
- 選定理由には必ず参照したファイル名と事例番号を含めること（例：「contractor_case_studies.txtの過去事例No.1より」）
- 各業者の「参照事例番号」には、選定理由で言及した事例番号を必ず「事例No.XX」の形式で記載すること（例：「事例No.6」「事例No.10」）
- 選定理由に「事例6」「事例10」「Case 6」「事例No.6」などの形式で事例番号が含まれている場合は、必ず「事例No.XX」の形式に統一して「参照事例番号」に記載すること
- 選定理由に事例番号が含まれていない場合でも、「該当なし」「情報不足」とは記載せず、選定理由を再確認して事例番号を抽出し、「事例No.XX」の形式で記載すること
- 選定理由に事例番号が一切含まれていない場合のみ、「該当なし」と記載すること（ただし、通常は選定理由に事例番号が含まれているはずです）
- 対応可能な緊急度と想定価格帯にも参照ファイル名を明記すること
- 判断理由には必ず参照したKnowledgeファイル名と事例番号を含めること
- 不確実な情報は推測ではなく「情報不足」と明記すること（ただし、「参照事例番号」については上記のルールに従うこと）
- 最終判断はユーザーが行うことを前提に、支援情報を提供すること
"""
                
                # LLMで回答を生成
                query_engine = self.get_index().as_query_engine(
                    llm=self.llm,
                    similarity_top_k=top_k,
                )
                
                response = query_engine.query(prompt)
                answer_text = str(response) if hasattr(response, '__str__') else str(response)
                
                # 判断理由を抽出（参照ファイル名を含む）
                # 回答テキストから「3. 判断理由」セクションを抽出
                reasoning = ""
                if "判断理由" in answer_text:
                    # 「3. 判断理由」セクションを抽出
                    match = re.search(r'3\.\s*\*\*判断理由\*\*.*?(?=4\.|$)', answer_text, re.DOTALL)
                    if match:
                        reasoning = match.group(0).replace("3. **判断理由**", "").strip()
                    else:
                        # フォールバック: 「判断理由」を含む行以降を取得
                        lines = answer_text.split('\n')
                        reasoning_start = False
                        reasoning_lines = []
                        for line in lines:
                            if "判断理由" in line:
                                reasoning_start = True
                            if reasoning_start:
                                reasoning_lines.append(line)
                        reasoning = '\n'.join(reasoning_lines).strip()
                
                # 判断理由が空の場合は、参照ファイル名のみを表示
                if not reasoning:
                    reasoning = f"参照したKnowledgeファイル: {', '.join(referenced_files)}"
                
                return {
                    "success": True,
                    "query": query,
                    "answer": answer_text,
                    "reasoning": reasoning,
                    "referenced_files": referenced_files,
                    "search_results": search_result["results"],  # 全ての検索結果
                }
                
            except Exception as e:
                import traceback
                error_msg = str(e)
                error_detail = traceback.format_exc()
                print(f"Error in generate_answer: {error_detail}")
                
                # レート制限エラーの場合、リトライ
                if "rate limit" in error_msg.lower() or "429" in error_msg:
                    if attempt < max_retries - 1:
                        time.sleep(retry_delay * (attempt + 1))
                        continue
                    else:
                        return {
                            "success": False,
                            "query": query,
                            "answer": "",
                            "reasoning": "",
                            "referenced_files": [],
                            "message": "Rate limit exceeded. Please try again later.",
                        }
                else:
                    return {
                        "success": False,
                        "query": query,
                        "answer": "",
                        "reasoning": "",
                        "referenced_files": [],
                        "message": f"Error generating answer: {error_msg}",
                    }
        
        return {
            "success": False,
            "query": query,
            "answer": "",
            "reasoning": "",
            "referenced_files": [],
            "message": "Failed to generate answer after retries",
        }


# シングルトンインスタンス
rag_service = RAGService()

