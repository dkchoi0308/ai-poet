import os
import json
from typing import List, Dict, Any
from PyPDF2 import PdfReader
from langchain_community.vectorstores import FAISS
from langchain_openai import OpenAIEmbeddings
from langchain_core.documents import Document

class PDFFeatureLoader:
    """PDF 파일에서 피처 정보를 로드하고 FAISS 인덱스를 구축하는 클래스 (JSON 캐싱 지원)"""

    def __init__(self, pdf_path: str = "featurelist.pdf", json_path: str = "featurelist.json"):
        self.pdf_path = pdf_path
        self.json_path = json_path
        self.vector_store = None

        # API Key 확인 (환경변수 또는 Streamlit Secrets)
        api_key = os.getenv("OPENAI_API_KEY")

        # 런타임에 st.secrets 확인 (Streamlit 환경인 경우)
        try:
            import streamlit as st
            if not api_key and "OPENAI_API_KEY" in st.secrets:
                api_key = st.secrets["OPENAI_API_KEY"]
        except ImportError:
            pass

        if not api_key:
            # 로컬 실행 시 .env가 있으면 여기서 에러가 안 나겠지만, 
            # Cloud 배포 시 Secrets 설정이 안 되어있으면 나중에 에러가 납니다.
            self.embeddings = OpenAIEmbeddings(model="text-embedding-3-small")
        else:
            self.embeddings = OpenAIEmbeddings(model="text-embedding-3-small", openai_api_key=api_key)

    def _get_file_mtime(self, filepath: str) -> float:
        """파일의 마지막 수정 시간을 반환합니다."""
        if os.path.exists(filepath):
            return os.path.getmtime(filepath)
        return 0.0

    def _load_from_json(self) -> List[Document]:
        """JSON 파일에서 Document 리스트를 로드합니다."""
        try:
            with open(self.json_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
                documents = []
                for item in data:
                    doc = Document(
                        page_content=item.get("page_content", ""),
                        metadata=item.get("metadata", {})
                    )
                    documents.append(doc)
                print(f"Loaded {len(documents)} features from JSON cache.")
                return documents
        except Exception as e:
            print(f"Error loading JSON cache: {e}")
            return []

    def _save_to_json(self, documents: List[Document]):
        """Document 리스트를 JSON 파일로 저장합니다."""
        try:
            data = []
            for doc in documents:
                data.append({
                    "page_content": doc.page_content,
                    "metadata": doc.metadata
                })
            with open(self.json_path, 'w', encoding='utf-8') as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
            print(f"Saved {len(documents)} features to JSON cache.")
        except Exception as e:
            print(f"Error saving JSON cache: {e}")

    def load_and_index(self):
        """PDF/JSON을 로드하여 FAISS 인덱스를 생성합니다."""
        pdf_mtime = self._get_file_mtime(self.pdf_path)
        json_mtime = self._get_file_mtime(self.json_path)

        documents = []

        # 1. JSON 캐시가 유효한지 확인 (PDF가 존재하고, JSON이 PDF보다 최신이거나 같을 때)
        # 단, PDF 파일이 아예 없으면 로드 불가
        if os.path.exists(self.pdf_path) and os.path.exists(self.json_path) and json_mtime >= pdf_mtime:
            print("Checking JSON cache... valid.")
            documents = self._load_from_json()
        
        # 2. 캐시가 없거나 만료되었으면 PDF 파싱 수행
        if not documents:
            if not os.path.exists(self.pdf_path):
                print(f"PDF file not found: {self.pdf_path}. Cannot build index.")
                return

            print("Parsing PDF (Cache outdated or missing)...")
            reader = PdfReader(self.pdf_path)
            
            # PDF 파싱 (단순 텍스트 추출 방식)
            raw_text = ""
            for page in reader.pages:
                raw_text += page.extract_text() + "\n"
            
            lines = raw_text.split('\n')
            for line in lines:
                if "ID: " in line and " | " in line:
                    try:
                        # 예시: ID: feat_name | CAT: category | DESC: description | VAL: 45
                        parts = line.split(" | ")
                        meta = {}
                        for p in parts:
                            if ":" in p:
                                key, val = p.split(":", 1)
                                meta[key.strip()] = val.strip()
                        
                        # 전체 텍스트도 검색을 위해 남겨둠
                        doc = Document(
                            page_content=line,
                            metadata={
                                "source": self.pdf_path,
                                "feature_name": meta.get("ID", "Unknown"),
                                "category": meta.get("CAT", ""),
                                "description": meta.get("DESC", ""),
                                "value": meta.get("VAL", "0")
                            }
                        )
                        documents.append(doc)
                    except Exception:
                        continue
            
            if documents:
                self._save_to_json(documents)
            else:
                print("No content parsed from PDF.")

        # 3. FAISS 인덱스 구축
        if documents:
            self.vector_store = FAISS.from_documents(documents, self.embeddings)
            print(f"Successfully built FAISS index with {len(documents)} items.")
        else:
            print("No documents to index.")

    def search_similar_features(self, query: str, k: int = 10) -> List[Dict[str, Any]]:
        """유사한 피처 검색"""
        if not self.vector_store:
            self.load_and_index()
        
        if not self.vector_store:
            return []

        docs = self.vector_store.similarity_search_with_score(query, k=k)
        results = []
        for doc, score in docs:
            content = doc.page_content
            results.append({
                "raw_text": content,
                "metadata": doc.metadata,
                "similarity_score": float(score)
            })
        return results
