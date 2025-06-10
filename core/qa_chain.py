from langchain.vectorstores import Chroma
from core.llm_client import ModelManager
from core.embeddings import DocumentProcessor
from utils.prompts import (
    PAPER_QA_PROMPT,
    TERM_EXPLANATION_PROMPT,
    KEYPOINTS_EXTRACTION_PROMPT
)
import logging
from typing import Dict, List, Any

logger = logging.getLogger(__name__)


class PaperQASystem:
    """论文问答系统"""

    def __init__(self, model_manager: ModelManager):
        self.model_manager = model_manager
        self.vectorstore = None
        self.current_paper_info = {}

    def load_paper(self, sections: Dict[str, str], paper_title: str = ""):
        """加载论文到问答系统"""
        try:
            # 处理文档
            processor = DocumentProcessor()
            documents = processor.process_paper_sections(sections)

            # 创建新的向量数据库（避免污染）
            self.vectorstore = processor.create_vectorstore(documents)

            # 保存论文信息
            self.current_paper_info = {
                "title": paper_title or sections.get("title", ""),
                "sections": sections,
                "total_docs": len(documents)
            }

            logger.info(f"论文加载成功: {self.current_paper_info['title']}")
            return True

        except Exception as e:
            logger.error(f"论文加载失败: {e}")
            return False

    def ask_question(self, question: str) -> Dict[str, Any]:
        """回答问题 - 改进检索策略"""
        if not self.vectorstore:
            return {
                "answer": "请先上传论文",
                "sources": [],
                "confidence": 0
            }

        try:
            # 改进的检索策略
            relevant_docs = self._smart_retrieve(question)

            if not relevant_docs:
                return {
                    "answer": "抱歉，我在论文中没有找到与您问题相关的内容。",
                    "sources": [],
                    "confidence": 0
                }

            # 过滤检索结果，确保相关性
            filtered_docs = self._filter_relevant_docs(question, relevant_docs)

            if not filtered_docs:
                return {
                    "answer": "抱歉，检索到的内容与您的问题相关性较低，请尝试重新表述问题。",
                    "sources": [],
                    "confidence": 0
                }

            # 构建高质量上下文
            context = self._build_context(filtered_docs)

            # 改进的prompt
            improved_prompt = f"""
            请基于以下论文内容回答用户问题。注意：

            1. 只基于提供的论文内容回答，不要添加论文中没有的信息
            2. 如果论文内容不足以回答问题，请明确说明
            3. 引用具体的章节来源
            4. 使用专业但易懂的语言

            论文内容：
            {context}

            用户问题：{question}

            回答：
            """

            # 生成回答
            qwen_model = self.model_manager.get_model("qa")
            answer = qwen_model(improved_prompt)

            # 格式化来源信息
            sources = self._format_sources(filtered_docs)

            # 评估置信度
            confidence = self._estimate_confidence(question, filtered_docs)

            return {
                "answer": answer,
                "sources": sources,
                "confidence": confidence,
                "question": question
            }

        except Exception as e:
            logger.error(f"问答失败: {e}")
            return {
                "answer": f"回答生成时出现错误: {str(e)}",
                "sources": [],
                "confidence": 0
            }

    def _smart_retrieve(self, question: str) -> List:
        """智能检索策略"""
        try:
            # 多种检索策略结合
            results = []

            # 1. 基本相似性检索
            similarity_results = self.vectorstore.similarity_search(
                question,
                k=6,
                filter=None  # 确保不使用过时的filter
            )
            results.extend(similarity_results)

            # 2. MMR检索（最大边际相关性）
            try:
                mmr_results = self.vectorstore.max_marginal_relevance_search(
                    question,
                    k=4,
                    fetch_k=10
                )
                results.extend(mmr_results)
            except:
                logger.warning("MMR检索失败，使用基本检索")

            # 去重
            seen_content = set()
            unique_results = []
            for doc in results:
                content_hash = hash(doc.page_content[:100])
                if content_hash not in seen_content:
                    seen_content.add(content_hash)
                    unique_results.append(doc)

            return unique_results[:8]  # 限制结果数量

        except Exception as e:
            logger.error(f"检索失败: {e}")
            return []

    def _filter_relevant_docs(self, question: str, docs: List) -> List:
        """过滤相关文档"""
        if not docs:
            return []

        # 简单的相关性过滤
        filtered = []
        question_lower = question.lower()

        for doc in docs:
            content_lower = doc.page_content.lower()

            # 排除明显不相关的测试内容
            test_keywords = [
                "智能论文阅读助手", "paperbot", "基于大语言模型和检索增强生成技术",
                "本文提出了一种", "随着学术论文数量的快速增长"
            ]

            # 如果包含测试关键词，跳过
            if any(keyword in content_lower for keyword in test_keywords):
                logger.warning(f"过滤掉测试内容: {doc.page_content[:50]}...")
                continue

            # 检查基本相关性
            if len(doc.page_content.strip()) > 20:  # 内容不能太短
                filtered.append(doc)

        return filtered[:6]  # 限制数量

    def explain_term(self, term: str) -> str:
        """解释术语"""
        if not self.vectorstore:
            return "请先上传论文"

        try:
            # 搜索术语相关内容
            relevant_docs = self.vectorstore.similarity_search(term, k=3)

            # 过滤相关文档
            filtered_docs = self._filter_relevant_docs(term, relevant_docs)

            if not filtered_docs:
                return f"在论文中没有找到关于'{term}'的相关内容。"

            # 构建上下文
            context = self._build_context(filtered_docs)

            # 生成解释
            qwen_model = self.model_manager.get_model("explanation")
            prompt = TERM_EXPLANATION_PROMPT.format(term=term, context=context)

            explanation = qwen_model(prompt)
            return explanation

        except Exception as e:
            logger.error(f"术语解释失败: {e}")
            return f"术语解释时出现错误: {str(e)}"

    def get_section_keypoints(self, section_name: str) -> List[str]:
        """提取章节关键点"""
        if section_name not in self.current_paper_info.get("sections", {}):
            return []

        try:
            section_content = self.current_paper_info["sections"][section_name]
            if not section_content:
                return []

            # 生成关键点
            qwen_model = self.model_manager.get_model("analysis")
            prompt = KEYPOINTS_EXTRACTION_PROMPT.format(
                section_name=section_name,
                content=section_content[:2000]  # 限制长度
            )

            response = qwen_model(prompt)

            # 解析关键点
            keypoints = []
            for line in response.split('\n'):
                line = line.strip()
                if line and (line.startswith('-') or line.startswith('•') or line.startswith('*')):
                    keypoints.append(line[1:].strip())
                elif line and not line.startswith(('1.', '2.', '3.', '4.', '5.')):
                    keypoints.append(line)

            return keypoints[:10]  # 最多返回10个关键点

        except Exception as e:
            logger.error(f"关键点提取失败: {e}")
            return []

    def get_paper_summary(self) -> str:
        """获取论文摘要"""
        if not self.current_paper_info:
            return "请先上传论文"

        try:
            # 构建摘要内容
            sections = self.current_paper_info["sections"]
            summary_content = ""

            for section in ["title", "abstract", "introduction", "conclusion"]:
                if section in sections and sections[section]:
                    summary_content += f"{section}: {sections[section][:500]}\n\n"

            if not summary_content:
                summary_content = sections.get("full_text", "")[:1500]

            # 生成摘要
            from utils.prompts import PAPER_SUMMARY_PROMPT
            qwen_model = self.model_manager.get_model("summary")
            prompt = PAPER_SUMMARY_PROMPT.format(
                title=self.current_paper_info["title"],
                content=summary_content
            )

            summary = qwen_model(prompt)
            return summary

        except Exception as e:
            logger.error(f"摘要生成失败: {e}")
            return f"摘要生成时出现错误: {str(e)}"

    def _build_context(self, documents) -> str:
        """构建上下文"""
        context_parts = []
        for i, doc in enumerate(documents):
            section = doc.metadata.get('section', 'unknown')
            content = doc.page_content.strip()
            context_parts.append(f"[章节:{section}] {content}")

        return "\n\n".join(context_parts)

    def _format_sources(self, documents) -> List[Dict[str, str]]:
        """格式化来源信息"""
        sources = []
        for doc in documents:
            sources.append({
                "section": doc.metadata.get('section', 'unknown'),
                "content": doc.page_content[:100] + "..." if len(doc.page_content) > 100 else doc.page_content,
                "chunk_id": doc.metadata.get('chunk_id', 0)
            })
        return sources

    def _estimate_confidence(self, question: str, documents) -> float:
        """估算回答置信度"""
        if not documents:
            return 0.0

        # 基于检索到的文档质量评估置信度
        doc_count_score = min(len(documents) / 4.0, 1.0)

        # 基于文档内容长度和质量
        total_content_length = sum(len(doc.page_content) for doc in documents)
        content_score = min(total_content_length / 1500.0, 1.0)

        # 检查内容相关性
        question_words = set(question.lower().split())
        relevance_scores = []
        for doc in documents:
            doc_words = set(doc.page_content.lower().split())
            intersection = len(question_words & doc_words)
            relevance = intersection / max(len(question_words), 1)
            relevance_scores.append(relevance)

        avg_relevance = sum(relevance_scores) / len(relevance_scores) if relevance_scores else 0

        # 综合得分
        confidence = (doc_count_score + content_score + avg_relevance) / 3.0
        return round(min(confidence, 0.95), 2)  # 最高95%