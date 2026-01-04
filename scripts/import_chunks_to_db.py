"""
チャンクデータをSQLiteデータベースにインポートするスクリプト
"""
import json
import sys
from pathlib import Path
from datetime import datetime
from sqlalchemy import create_engine, Column, Integer, String, Text, DateTime, Float, text
from sqlalchemy.orm import declarative_base, sessionmaker

# プロジェクトルートをパスに追加
sys.path.insert(0, str(Path(__file__).parent.parent))

from app.core.config import settings
from app.services.knowledge_service import knowledge_service

Base = declarative_base()


class Chunk(Base):
    """チャンクテーブル"""
    __tablename__ = "chunks"
    
    id = Column(Integer, primary_key=True, index=True)
    chunk_id = Column(String, unique=True, index=True, nullable=False)  # UUID
    file_name = Column(String, index=True, nullable=False)
    file_type = Column(String, index=True, nullable=True)
    chunk_index = Column(Integer, nullable=True)  # ファイル内でのチャンク番号
    text_content = Column(Text, nullable=True)  # チャンクのテキスト内容
    text_preview = Column(String, nullable=True)  # テキストのプレビュー（最初の200文字）
    text_length = Column(Integer, nullable=True)  # テキストの長さ
    document_id = Column(String, nullable=True)
    ref_doc_id = Column(String, nullable=True)  # 参照ドキュメントID
    file_size = Column(Integer, nullable=True)  # 元ファイルのサイズ
    file_updated_at = Column(DateTime, nullable=True)  # 元ファイルの更新日時
    embedding_json = Column(Text, nullable=True)  # エンベディングベクトル（JSON形式）
    embedding_dimension = Column(Integer, nullable=True)  # エンベディングの次元数
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    metadata_json = Column(Text, nullable=True)  # メタデータ全体をJSON文字列で保存


def import_chunks_to_db():
    """チャンクデータをデータベースにインポート"""
    
    # データベース接続
    engine = create_engine(settings.database_url, connect_args={"check_same_thread": False})
    Base.metadata.create_all(bind=engine)
    SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    db = SessionLocal()
    
    try:
        # 既存のチャンクを削除（再インポート用）
        db.execute(text("DELETE FROM chunks"))
        db.commit()
        print("既存のチャンクデータを削除しました。")
        
        # ベクトルストアファイルを読み込み
        vector_store_path = Path("./storage/index/default__vector_store.json")
        if not vector_store_path.exists():
            print(f"エラー: {vector_store_path} が見つかりません。")
            return
        
        print(f"ベクトルストアファイルを読み込み中: {vector_store_path}")
        with open(vector_store_path, 'r', encoding='utf-8') as f:
            vector_store = json.load(f)
        
        # docstoreファイルを読み込み（テキスト内容を取得するため）
        docstore_path = Path("./storage/index/docstore.json")
        docstore_data = {}
        if docstore_path.exists():
            with open(docstore_path, 'r', encoding='utf-8') as f:
                docstore_json = json.load(f)
                # docstoreの構造に応じてデータを取得
                if 'docstore' in docstore_json and 'data' in docstore_json['docstore']:
                    docstore_data = docstore_json['docstore']['data']
        
        # エンベディングとメタデータを取得
        embedding_dict = vector_store.get('embedding_dict', {})
        metadata_dict = vector_store.get('metadata_dict', {})
        text_id_to_ref_doc_id = vector_store.get('text_id_to_ref_doc_id', {})
        
        print(f"総チャンク数: {len(embedding_dict)}")
        
        # Knowledgeファイルからテキストを取得するためのキャッシュ
        file_content_cache = {}
        
        # チャンクをデータベースにインポート
        imported_count = 0
        for chunk_id, embedding in embedding_dict.items():
            metadata = metadata_dict.get(chunk_id, {})
            
            # docstoreからテキスト内容を取得（可能な場合）
            text_content = None
            if chunk_id in docstore_data:
                chunk_data = docstore_data[chunk_id]
                if isinstance(chunk_data, dict) and 'text' in chunk_data:
                    text_content = chunk_data['text']
            
            # docstoreから取得できない場合、Knowledgeファイルから再構築を試みる
            if not text_content:
                file_name = metadata.get('file_name', '')
                chunk_index = metadata.get('chunk_index', None)
                
                if file_name and chunk_index is not None:
                    try:
                        # ファイル内容をキャッシュから取得、または読み込む
                        if file_name not in file_content_cache:
                            file_content = knowledge_service.get_file_content(file_name)
                            file_content_cache[file_name] = file_content['content']
                        
                        file_text = file_content_cache[file_name]
                        
                        # チャンクサイズ400文字、オーバーラップ50文字で分割
                        chunk_size = 400
                        overlap = 50
                        start = chunk_index * (chunk_size - overlap)
                        end = start + chunk_size
                        text_content = file_text[start:end] if start < len(file_text) else None
                    except Exception as e:
                        print(f"Warning: Could not get text for {file_name} chunk {chunk_index}: {e}")
                        text_content = None
            
            # ref_doc_idを取得
            ref_doc_id = text_id_to_ref_doc_id.get(chunk_id)
            
            # メタデータから情報を取得
            file_name = metadata.get('file_name', 'unknown')
            file_type = metadata.get('file_type', 'unknown')
            chunk_index = metadata.get('chunk_index', None)
            document_id = metadata.get('document_id') or metadata.get('doc_id') or ref_doc_id
            file_size = metadata.get('file_size', None)
            updated_at = metadata.get('updated_at', None)
            
            # updated_atをDateTimeに変換
            file_updated_at = None
            if updated_at:
                try:
                    file_updated_at = datetime.fromtimestamp(updated_at)
                except (ValueError, TypeError):
                    pass
            
            # テキストプレビューを作成（最初の200文字）
            text_preview = None
            if text_content:
                text_preview = text_content[:200] + "..." if len(text_content) > 200 else text_content
            
            # エンベディングベクトルを取得
            embedding_vector = embedding_dict.get(chunk_id)
            embedding_json = None
            embedding_dimension = None
            if embedding_vector:
                embedding_json = json.dumps(embedding_vector)
                embedding_dimension = len(embedding_vector) if isinstance(embedding_vector, list) else None
            
            # チャンクレコードを作成
            chunk = Chunk(
                chunk_id=chunk_id,
                file_name=file_name,
                file_type=file_type,
                chunk_index=chunk_index,
                text_content=text_content,
                text_preview=text_preview,
                text_length=len(text_content) if text_content else None,
                document_id=document_id,
                ref_doc_id=ref_doc_id,
                file_size=file_size,
                file_updated_at=file_updated_at,
                embedding_json=embedding_json,
                embedding_dimension=embedding_dimension,
                metadata_json=json.dumps(metadata, ensure_ascii=False)
            )
            
            db.add(chunk)
            imported_count += 1
            
            if imported_count % 10 == 0:
                print(f"  インポート中: {imported_count}/{len(embedding_dict)}")
        
        db.commit()
        print(f"\n✅ 完了: {imported_count}個のチャンクをデータベースにインポートしました。")
        
        # 統計情報を表示
        result = db.execute(text("""
            SELECT 
                file_name,
                COUNT(*) as chunk_count,
                AVG(text_length) as avg_length
            FROM chunks
            GROUP BY file_name
            ORDER BY file_name
        """))
        
        print("\n📊 ファイルごとのチャンク統計:")
        print("-" * 60)
        for row in result:
            avg_len = row.avg_length if row.avg_length else 0
            print(f"  {row.file_name}: {row.chunk_count}チャンク (平均長: {avg_len:.0f}文字)")
        
    except Exception as e:
        db.rollback()
        print(f"❌ エラーが発生しました: {e}")
        import traceback
        traceback.print_exc()
    finally:
        db.close()


if __name__ == "__main__":
    import_chunks_to_db()

