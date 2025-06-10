from core.llm_client import ModelManager
from utils.prompts import (
    PAPER_SUMMARY_PROMPT,
    INNOVATION_ANALYSIS_PROMPT,
    KEYPOINTS_EXTRACTION_PROMPT
)
import logging
import json
from typing import Dict, List, Any

logger = logging.getLogger(__name__)


class PaperSummarizer:
    """论文摘要生成器"""

    def __init__(self, model_manager: ModelManager):
        self.model_manager = model_manager

    def generate_comprehensive_summary(self, sections: Dict[str, str]) -> Dict[str, Any]:
        """生成全面的论文摘要"""
        title = sections.get('title', '未知标题')

        try:
            # 1. 生成整体摘要
            overall_summary = self._generate_overall_summary(sections, title)

            # 2. 提取各章节关键点
            section_summaries = self._extract_section_summaries(sections)

            # 3. 分析创新点
            innovations = self._analyze_innovations(sections, title)

            # 4. 生成研究方法总结
            methodology_summary = self._summarize_methodology(sections)

            # 5. 提取主要结论
            main_findings = self._extract_main_findings(sections)

            return {
                "overall_summary": overall_summary,
                "section_summaries": section_summaries,
                "innovations": innovations,
                "methodology": methodology_summary,
                "main_findings": main_findings,
                "paper_title": title
            }

        except Exception as e:
            logger.error(f"摘要生成失败: {e}")
            return {
                "overall_summary": f"摘要生成失败: {str(e)}",
                "section_summaries": {},
                "innovations": {},
                "methodology": "",
                "main_findings": [],
                "paper_title": title
            }

    def _generate_overall_summary(self, sections: Dict[str, str], title: str) -> str:
        """生成整体摘要"""
        # 构建摘要内容
        content_parts = []

        for section_name in ["abstract", "introduction", "methodology", "results", "conclusion"]:
            if section_name in sections and sections[section_name]:
                content_parts.append(f"{section_name.upper()}:\n{sections[section_name][:800]}")

        if not content_parts:
            # 如果没有标准章节，使用全文
            full_text = sections.get("full_text", "")
            content_parts = [full_text[:2000]]

        content = "\n\n".join(content_parts)

        try:
            qwen_model = self.model_manager.get_model("summary")
            prompt = PAPER_SUMMARY_PROMPT.format(title=title, content=content)
            return qwen_model(prompt)
        except Exception as e:
            logger.error(f"整体摘要生成失败: {e}")
            return f"摘要生成失败: {str(e)}"

    def _extract_section_summaries(self, sections: Dict[str, str]) -> Dict[str, str]:
        """提取各章节摘要"""
        section_summaries = {}

        important_sections = [
            "abstract", "introduction", "methodology",
            "results", "conclusion", "discussion"
        ]

        for section_name in important_sections:
            if section_name in sections and sections[section_name]:
                try:
                    summary = self._summarize_section(section_name, sections[section_name])
                    if summary:
                        section_summaries[section_name] = summary
                except Exception as e:
                    logger.warning(f"章节 {section_name} 摘要失败: {e}")
                    continue

        return section_summaries

    def _summarize_section(self, section_name: str, content: str) -> str:
        """总结单个章节"""
        if len(content) < 100:  # 内容太短不需要总结
            return content

        prompt = f"""
        请总结以下论文章节的主要内容：

        章节：{section_name}
        内容：{content[:1500]}

        要求：
        1. 用中文总结
        2. 保留关键信息
        3. 长度控制在100字以内
        4. 突出重点

        总结：
        """

        try:
            qwen_model = self.model_manager.get_model("summary")
            return qwen_model(prompt)
        except Exception as e:
            logger.error(f"章节总结失败: {e}")
            return ""

    def _analyze_innovations(self, sections: Dict[str, str], title: str) -> Dict[str, Any]:
        """分析创新点"""
        # 构建分析内容
        analysis_content = ""

        for section_name in ["abstract", "introduction", "methodology", "conclusion"]:
            if section_name in sections and sections[section_name]:
                analysis_content += f"{section_name.upper()}:\n{sections[section_name][:600]}\n\n"

        if not analysis_content:
            analysis_content = sections.get("full_text", "")[:2000]

        try:
            qwen_model = self.model_manager.get_model("analysis")
            prompt = INNOVATION_ANALYSIS_PROMPT.format(
                title=title,
                content=analysis_content
            )

            response = qwen_model(prompt)

            # 尝试解析JSON响应
            innovations = self.model_manager.parse_json_response(response)

            # 如果解析失败，返回默认格式
            if "error" in innovations:
                return self._parse_innovations_from_text(response)

            return innovations

        except Exception as e:
            logger.error(f"创新点分析失败: {e}")
            return {
                "technical_innovations": [],
                "methodological_contributions": [],
                "theoretical_contributions": [],
                "practical_value": "分析失败",
                "differences_from_existing_work": []
            }

    def _parse_innovations_from_text(self, text: str) -> Dict[str, Any]:
        """从文本中解析创新点"""
        lines = text.split('\n')
        innovations = {
            "technical_innovations": [],
            "methodological_contributions": [],
            "theoretical_contributions": [],
            "practical_value": "",
            "differences_from_existing_work": []
        }

        current_category = None
        for line in lines:
            line = line.strip()
            if not line:
                continue

            # 识别类别
            if "技术创新" in line or "technical" in line.lower():
                current_category = "technical_innovations"
            elif "方法" in line or "methodological" in line.lower():
                current_category = "methodological_contributions"
            elif "理论" in line or "theoretical" in line.lower():
                current_category = "theoretical_contributions"
            elif "实践" in line or "practical" in line.lower():
                current_category = "practical_value"
            elif "差异" in line or "differences" in line.lower():
                current_category = "differences_from_existing_work"
            elif line.startswith(('-', '•', '*')) and current_category:
                # 添加到当前类别
                item = line[1:].strip()
                if isinstance(innovations[current_category], list):
                    innovations[current_category].append(item)
                else:
                    innovations[current_category] = item

        return innovations

    def _summarize_methodology(self, sections: Dict[str, str]) -> str:
        """总结研究方法"""
        methodology_content = sections.get("methodology", "")

        # 如果没有专门的方法章节，尝试从其他章节提取
        if not methodology_content:
            for section_name, content in sections.items():
                if any(keyword in section_name.lower() for keyword in ["method", "approach", "technique"]):
                    methodology_content = content
                    break

        if not methodology_content:
            return "未找到明确的方法论描述"

        prompt = f"""
        请总结以下研究方法的核心要点：

        {methodology_content[:1200]}

        请包含：
        1. 主要方法或技术
        2. 实验设计
        3. 数据来源和处理
        4. 评估标准

        总结：
        """

        try:
            qwen_model = self.model_manager.get_model("summary")
            return qwen_model(prompt)
        except Exception as e:
            logger.error(f"方法论总结失败: {e}")
            return f"方法论总结失败: {str(e)}"

    def _extract_main_findings(self, sections: Dict[str, str]) -> List[str]:
        """提取主要发现"""
        findings_content = ""

        # 从结果和结论章节提取
        for section_name in ["results", "conclusion", "discussion", "findings"]:
            if section_name in sections and sections[section_name]:
                findings_content += sections[section_name][:800] + "\n\n"

        if not findings_content:
            # 如果没有专门章节，从摘要中提取
            findings_content = sections.get("abstract", "")[:500]

        if not findings_content:
            return ["未找到明确的研究发现"]

        prompt = f"""
        请从以下内容中提取主要研究发现和结论：

        {findings_content}

        要求：
        1. 提取3-5个主要发现
        2. 每个发现用一句话表述
        3. 按重要性排序
        4. 使用中文

        格式：
        - 发现1
        - 发现2
        - 发现3

        主要发现：
        """

        try:
            qwen_model = self.model_manager.get_model("summary")
            response = qwen_model(prompt)

            # 解析发现列表
            findings = []
            for line in response.split('\n'):
                line = line.strip()
                if line.startswith(('-', '•', '*')):
                    findings.append(line[1:].strip())
                elif line and not line.startswith(('主要发现', '发现', '结论')):
                    findings.append(line)

            return findings[:5]  # 最多返回5个发现

        except Exception as e:
            logger.error(f"主要发现提取失败: {e}")
            return [f"发现提取失败: {str(e)}"]