import PyPDF2
import re
import logging
from typing import Dict, List
from pathlib import Path

logger = logging.getLogger(__name__)


class PaperParser:
    def __init__(self):
        # 章节识别模式
        self.section_patterns = {
            'abstract': re.compile(r'(abstract|摘要)', re.IGNORECASE),
            'introduction': re.compile(r'(introduction|引言|1\.\s*introduction)', re.IGNORECASE),
            'methodology': re.compile(r'(method|methodology|approach|方法)', re.IGNORECASE),
            'results': re.compile(r'(result|experiment|实验|结果)', re.IGNORECASE),
            'conclusion': re.compile(r'(conclusion|discussion|结论|讨论)', re.IGNORECASE),
            'references': re.compile(r'(reference|bibliography|参考文献)', re.IGNORECASE)
        }

    def extract_text_from_pdf(self, pdf_path: str) -> str:
        """从PDF提取文本"""
        try:
            with open(pdf_path, 'rb') as file:
                pdf_reader = PyPDF2.PdfReader(file)
                text = ""

                for page_num, page in enumerate(pdf_reader.pages):
                    try:
                        page_text = page.extract_text()
                        text += f"\n--- Page {page_num + 1} ---\n"
                        text += page_text
                    except Exception as e:
                        logger.warning(f"第{page_num + 1}页提取失败: {e}")
                        continue

                return text
        except Exception as e:
            logger.error(f"PDF解析失败: {e}")
            raise

    def extract_sections(self, pdf_path: str) -> Dict[str, str]:
        """提取论文章节"""
        text = self.extract_text_from_pdf(pdf_path)

        sections = {
            'title': '',
            'abstract': '',
            'introduction': '',
            'methodology': '',
            'results': '',
            'conclusion': '',
            'references': '',
            'full_text': text
        }

        # 简单的章节分割（可以优化）
        lines = text.split('\n')
        current_section = 'introduction'  # 默认放到introduction

        for line in lines:
            line = line.strip()
            if not line:
                continue

            # 检查是否是标题（第一行且较短）
            if not sections['title'] and len(line) < 200 and len(line) > 10:
                sections['title'] = line
                continue

            # 识别章节
            section_found = False
            for section_name, pattern in self.section_patterns.items():
                if pattern.search(line):
                    current_section = section_name
                    section_found = True
                    break

            # 如果不是章节标题，则添加到当前章节
            if not section_found:
                sections[current_section] += line + '\n'

        # 清理空白
        for key in sections:
            sections[key] = sections[key].strip()

        logger.info(f"成功解析论文，提取到 {len([s for s in sections.values() if s])} 个非空章节")
        return sections

    def extract_metadata(self, pdf_path: str) -> Dict[str, str]:
        """提取论文元信息"""
        try:
            with open(pdf_path, 'rb') as file:
                pdf_reader = PyPDF2.PdfReader(file)
                metadata = pdf_reader.metadata or {}

                return {
                    'title': metadata.get('/Title', ''),
                    'author': metadata.get('/Author', ''),
                    'subject': metadata.get('/Subject', ''),
                    'creator': metadata.get('/Creator', ''),
                    'pages': len(pdf_reader.pages),
                    'file_size': Path(pdf_path).stat().st_size
                }
        except Exception as e:
            logger.error(f"元信息提取失败: {e}")
            return {}

    def clean_text(self, text: str) -> str:
        """清理文本"""
        # 去除多余空白
        text = re.sub(r'\n+', '\n', text)
        text = re.sub(r' +', ' ', text)

        # 去除页码等干扰信息
        text = re.sub(r'--- Page \d+ ---', '', text)

        return text.strip()