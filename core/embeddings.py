from sentence_transformers import SentenceTransformer
from langchain.embeddings.base import Embeddings
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain.docstore.document import Document
from langchain.vectorstores import Chroma
import logging
import uuid
import shutil
import os
from typing import List, Dict
from utils.config import Config

logger = logging.getLogger(__name__)


class ChineseEmbeddings(Embeddings):
    def __init__(self, model_name: str = None):
        """初始化中文embedding模型"""
        self.model_name = model_name or Config.EMBEDDING_MODEL
        try:
            self.model = SentenceTransformer(self.model_name)
            logger.info(f"成功加载embedding模型: {self.model_name}")
        except Exception as e:
            logger.error(f"模型加载失败: {e}")
            raise

    def embed_documents(self, texts: List[str]) -> List[List[float]]:
        """文档向量化"""
        try:
            embeddings = self.model.encode(
                texts,
                normalize_embeddings=True,
                show_progress_bar=True
            )
            return embeddings.tolist()
        except Exception as e:
            logger.error(f"文档向量化失败: {e}")
            raise

    def embed_query(self, text: str) -> List[float]:
        """查询向量化"""
        try:
            embedding = self.model.encode([text], normalize_embeddings=True)
            return embedding[0].tolist()
        except Exception as e:
            logger.error(f"查询向量化失败: {e}")
            raise


class DocumentProcessor:
    def __init__(self):
        # 优化分块参数 - 减少文档块数量，提高质量
        self.text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=800,  # 增大chunk大小
            chunk_overlap=100,  # 增加重叠
            separators=["\n\n", "\n", "。", "！", "？", ".", "!", "?", " ", ""]
        )
        self.embeddings = ChineseEmbeddings()

    def process_paper_sections(self, sections: Dict[str, str]) -> List[Document]:
        """处理论文章节，转换为Document对象"""
        documents = []

        # 处理顺序：优先处理重要章节
        priority_sections = ["abstract", "introduction", "methodology", "results", "conclusion"]
        other_sections = [s for s in sections.keys() if s not in priority_sections and s != 'full_text']

        section_order = priority_sections + other_sections

        for section_name in section_order:
            if section_name not in sections or not sections[section_name] or section_name == 'full_text':
                continue

            content = sections[section_name].strip()
            if len(content) < 50:  # 跳过太短的内容
                continue

            # 清理内容
            content = self._clean_content(content)

            # 为每个章节添加元数据
            doc = Document(
                page_content=content,
                metadata={
                    'section': section_name,
                    'section_title': section_name.title(),
                    'content_length': len(content),
                    'doc_id': str(uuid.uuid4())  # 添加唯一ID
                }
            )
            documents.append(doc)

        # 对长文本进行分割
        split_docs = []
        for doc in documents:
            if len(doc.page_content) > 800:  # 使用新的chunk大小
                # 分割长文档
                chunks = self.text_splitter.split_documents([doc])
                # 为分割后的文档添加chunk信息
                for i, chunk in enumerate(chunks):
                    chunk.metadata.update({
                        'chunk_id': i,
                        'total_chunks': len(chunks),
                        'original_section': doc.metadata['section']
                    })
                split_docs.extend(chunks)
            else:
                split_docs.append(doc)

        logger.info(f"文档处理完成，共生成 {len(split_docs)} 个文档块")
        return split_docs

    def _clean_content(self, content: str) -> str:
        """清理文档内容"""
        # 移除多余的空白和特殊字符
        content = content.replace('\u2028', '\n').replace('\u2029', '\n\n')

        # 移除包含特殊Unicode字符的行（可能是公式或符号）
        lines = content.split('\n')
        cleaned_lines = []
        for line in lines:
            # 跳过主要由特殊字符组成的行
            if len(line.strip()) > 5 and not any('\ud835' in line or '\ufffd' in line for char in line):
                cleaned_lines.append(line)

        content = '\n'.join(cleaned_lines)

        # 清理多余空白
        import re
        content = re.sub(r'\n+', '\n', content)
        content = re.sub(r' +', ' ', content)

        return content.strip()

    def create_vectorstore(self, documents: List[Document], persist_directory: str = None) -> Chroma:
        """创建向量数据库 - 每次创建新的，避免污染"""
        try:
            persist_dir = persist_directory or Config.CHROMA_DB_PATH

            # 为每次新论文创建独立的collection
            collection_name = f"paper_{uuid.uuid4().hex[:8]}"

            # 清理旧的数据库目录（可选）
            if os.path.exists(persist_dir):
                try:
                    shutil.rmtree(persist_dir)
                    logger.info("清理旧的向量数据库")
                except:
                    pass

            os.makedirs(persist_dir, exist_ok=True)

            vectorstore = Chroma.from_documents(
                documents=documents,
                embedding=self.embeddings,
                persist_directory=persist_dir,
                collection_name=collection_name,
                collection_metadata={
                    "description": "Current paper documents",
                    "created_at": str(uuid.uuid4())
                }
            )

            # 持久化
            vectorstore.persist()
            logger.info(f"向量数据库创建成功，存储路径: {persist_dir}, collection: {collection_name}")

            return vectorstore
        except Exception as e:
            logger.error(f"向量数据库创建失败: {e}")
            raise

    def load_vectorstore(self, persist_directory: str = None) -> Chroma:
        """加载已存在的向量数据库"""
        try:
            persist_dir = persist_directory or Config.CHROMA_DB_PATH

            vectorstore = Chroma(
                persist_directory=persist_dir,
                embedding_function=self.embeddings
            )

            logger.info(f"向量数据库加载成功，路径: {persist_dir}")
            return vectorstore
        except Exception as e:
            logger.error(f"向量数据库加载失败: {e}")
            raise