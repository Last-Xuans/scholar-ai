import gradio as gr
import os
import sys
import json
import tempfile
import time

# 添加项目根目录到路径
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from utils.config import Config
from core.pdf_parser import PaperParser
from core.llm_client import ModelManager
from core.qa_chain import PaperQASystem
from core.summarizer import PaperSummarizer
import logging

# 配置日志
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class PaperAssistantUI:
    """论文助手UI界面"""

    def __init__(self):
        try:
            # 验证配置
            Config.validate()

            # 初始化组件
            self.model_manager = ModelManager()
            self.parser = PaperParser()
            self.qa_system = PaperQASystem(self.model_manager)
            self.summarizer = PaperSummarizer(self.model_manager)

            # 状态变量
            self.current_paper = None
            self.current_summary = None

            logger.info("UI组件初始化完成")

        except Exception as e:
            logger.error(f"初始化失败: {e}")
            raise

    def upload_paper(self, file, progress=gr.Progress()):
        """上传论文处理 - 添加进度显示"""
        if file is None:
            return "❌ 请选择PDF文件", "", {}, []

        try:
            start_time = time.time()
            logger.info(f"开始处理论文: {file.name}")

            # 进度1: 解析PDF
            progress(0.1, desc="正在解析PDF文件...")
            sections = self.parser.extract_sections(file.name)
            metadata = self.parser.extract_metadata(file.name)

            progress(0.3, desc="PDF解析完成，准备向量化...")

            # 获取论文标题
            paper_title = sections.get('title') or metadata.get('title') or "未知论文"

            # 进度2: 加载到问答系统
            progress(0.5, desc="正在创建向量数据库...")
            success = self.qa_system.load_paper(sections, paper_title)
            if not success:
                return "❌ 论文加载失败", "", {}, []

            progress(0.7, desc="向量化完成，生成摘要...")

            # 进度3: 生成摘要
            summary = self.summarizer.generate_comprehensive_summary(sections)

            progress(0.9, desc="摘要生成完成，整理结果...")

            # 保存状态
            self.current_paper = {
                "sections": sections,
                "metadata": metadata,
                "title": paper_title
            }
            self.current_summary = summary

            # 准备显示信息
            processing_time = time.time() - start_time
            status_text = f"""✅ 论文处理成功！
📄 标题: {paper_title}
📊 页数: {metadata.get('pages', '未知')}
⏱️ 处理时间: {processing_time:.1f}秒
📦 文档块数: {self.qa_system.current_paper_info.get('total_docs', 0)}
"""

            summary_text = summary.get('overall_summary', '摘要生成失败')

            # 创新点信息
            innovations = summary.get('innovations', {})

            # 章节关键点
            section_summaries = summary.get('section_summaries', {})
            keypoints_display = []
            for section, content in section_summaries.items():
                keypoints_display.append(f"**{section.upper()}**\n{content}\n")

            progress(1.0, desc="完成！")
            logger.info(f"论文处理完成: {paper_title} (耗时: {processing_time:.1f}秒)")

            return status_text, summary_text, innovations, "\n".join(keypoints_display)

        except Exception as e:
            error_msg = f"❌ 论文处理失败: {str(e)}"
            logger.error(error_msg)
            return error_msg, "", {}, []

    def ask_question(self, question, history):
        """处理问答 - 优化响应"""
        if not question.strip():
            return history, ""

        if not self.current_paper:
            history.append([question, "❌ 请先上传论文"])
            return history, ""

        try:
            start_time = time.time()

            # 获取回答
            result = self.qa_system.ask_question(question)

            processing_time = time.time() - start_time

            # 构建回答
            answer = result["answer"]
            confidence = result.get("confidence", 0)
            sources = result.get("sources", [])

            # 优化回答格式
            full_answer = f"{answer}\n\n"
            full_answer += f"🎯 **置信度**: {confidence:.0%} | ⏱️ **响应时间**: {processing_time:.1f}秒\n\n"

            if sources:
                full_answer += "📚 **参考来源**:\n"
                for i, source in enumerate(sources[:3], 1):
                    section = source.get('section', 'unknown')
                    content = source.get('content', '')[:80]  # 缩短显示长度
                    full_answer += f"{i}. [{section}] {content}...\n"

            history.append([question, full_answer])

        except Exception as e:
            error_msg = f"❌ 回答生成失败: {str(e)}"
            history.append([question, error_msg])

        return history, ""

    def explain_term(self, term):
        """解释术语"""
        if not term.strip():
            return "请输入要解释的术语"

        if not self.current_paper:
            return "❌ 请先上传论文"

        try:
            start_time = time.time()
            explanation = self.qa_system.explain_term(term)
            processing_time = time.time() - start_time

            return f"📖 **术语**: {term}\n⏱️ **处理时间**: {processing_time:.1f}秒\n\n{explanation}"
        except Exception as e:
            return f"❌ 术语解释失败: {str(e)}"

    def get_section_analysis(self, section_name):
        """获取章节分析"""
        if not self.current_paper:
            return "❌ 请先上传论文"

        if not self.current_summary:
            return "❌ 摘要信息不可用"

        try:
            start_time = time.time()

            # 获取章节摘要
            section_summaries = self.current_summary.get('section_summaries', {})
            if section_name in section_summaries:
                summary = section_summaries[section_name]

                # 获取关键点
                keypoints = self.qa_system.get_section_keypoints(section_name)

                processing_time = time.time() - start_time

                result = f"## {section_name.upper()} 分析\n"
                result += f"⏱️ **处理时间**: {processing_time:.1f}秒\n\n"
                result += f"**章节摘要**:\n{summary}\n\n"

                if keypoints:
                    result += "**关键要点**:\n"
                    for i, point in enumerate(keypoints, 1):
                        result += f"{i}. {point}\n"

                return result
            else:
                return f"❌ 未找到 {section_name} 章节"

        except Exception as e:
            return f"❌ 章节分析失败: {str(e)}"

    def create_interface(self):
        """创建Gradio界面"""

        # 自定义CSS
        css = """
        .gradio-container {
            font-family: 'Microsoft YaHei', sans-serif;
        }
        .performance-info {
            background-color: #f0f8ff;
            padding: 10px;
            border-radius: 5px;
            margin: 5px 0;
        }
        """

        with gr.Blocks(
                title="📚 PaperBot - 智能论文阅读助手",
                theme=gr.themes.Soft(),
                css=css
        ) as demo:
            gr.Markdown(
                """
                # 📚 PaperBot - 智能论文阅读助手 (优化版)

                **🚀 性能优化**:
                - ⚡ 智能分块策略，减少处理时间
                - 🎯 改进检索算法，提高回答准确性
                - 🧹 内容过滤机制，避免测试数据污染
                - 📊 实时进度显示和性能监控

                **功能特色:**
                - 🔍 智能问答：基于论文内容精准回答
                - 📝 自动摘要：生成高质量论文总结
                - 🔖 术语解释：专业术语智能解释
                - 📊 章节分析：深度分析各章节要点

                ---
                """
            )

            with gr.Tab("📄 论文上传"):
                gr.Markdown("### 📤 上传论文文件")

                with gr.Row():
                    with gr.Column(scale=1):
                        file_input = gr.File(
                            label="选择PDF论文文件",
                            file_types=[".pdf"],
                            elem_classes=["upload-area"]
                        )
                        upload_btn = gr.Button("🚀 开始解析", variant="primary", size="lg")

                        gr.Markdown("""
                        **💡 使用提示**:
                        - 支持学术论文PDF格式
                        - 建议文件大小 < 50MB
                        - 处理时间通常 30-60秒
                        """)

                    with gr.Column(scale=1):
                        status_output = gr.Textbox(
                            label="📊 处理状态",
                            lines=6,
                            interactive=False,
                            elem_classes=["performance-info"]
                        )

                with gr.Row():
                    with gr.Column():
                        summary_output = gr.Textbox(
                            label="📝 论文摘要",
                            lines=8,
                            interactive=False
                        )

                    with gr.Column():
                        innovations_output = gr.JSON(
                            label="💡 创新点分析"
                        )

                keypoints_output = gr.Textbox(
                    label="🔑 章节要点总结",
                    lines=8,
                    interactive=False
                )

            with gr.Tab("💬 智能问答"):
                gr.Markdown("### 🤖 基于论文内容的智能问答")

                with gr.Row():
                    with gr.Column(scale=3):
                        chatbot = gr.Chatbot(
                            label="💬 对话历史",
                            height=500,
                            show_label=True
                        )

                        with gr.Row():
                            question_input = gr.Textbox(
                                label="输入问题",
                                placeholder="请输入您想了解的问题...",
                                scale=4
                            )
                            ask_btn = gr.Button("🤔 提问", variant="primary", scale=1)

                    with gr.Column(scale=1):
                        gr.Markdown("### 💡 推荐问题")

                        gr.Markdown("**🎯 论文理解类**")
                        example1_btn = gr.Button("这篇论文的主要贡献是什么？", variant="secondary", size="sm")
                        example2_btn = gr.Button("研究背景和动机是什么？", variant="secondary", size="sm")
                        example3_btn = gr.Button("解决了什么问题？", variant="secondary", size="sm")

                        gr.Markdown("**🔬 方法技术类**")
                        example4_btn = gr.Button("使用了什么研究方法？", variant="secondary", size="sm")
                        example5_btn = gr.Button("技术实现细节如何？", variant="secondary", size="sm")
                        example6_btn = gr.Button("实验设计是怎样的？", variant="secondary", size="sm")

                        gr.Markdown("**📊 结果评估类**")
                        example7_btn = gr.Button("实验结果如何？", variant="secondary", size="sm")
                        example8_btn = gr.Button("有哪些局限性？", variant="secondary", size="sm")
                        example9_btn = gr.Button("与其他工作相比有什么优势？", variant="secondary", size="sm")

            with gr.Tab("📖 术语解释"):
                gr.Markdown("### 🔍 专业术语智能解释")

                with gr.Row():
                    with gr.Column(scale=1):
                        term_input = gr.Textbox(
                            label="输入术语或概念",
                            placeholder="请输入需要解释的专业术语..."
                        )
                        explain_btn = gr.Button("🔍 解释术语", variant="primary")

                        gr.Markdown("""
                        **💡 使用说明**:
                        - 输入论文中的专业术语
                        - 支持中英文术语解释
                        - 基于论文上下文提供解释
                        """)

                    with gr.Column(scale=2):
                        term_output = gr.Textbox(
                            label="📖 术语解释结果",
                            lines=12,
                            interactive=False
                        )

            with gr.Tab("📊 章节分析"):
                gr.Markdown("### 📈 论文章节深度分析")

                with gr.Row():
                    with gr.Column(scale=1):
                        section_dropdown = gr.Dropdown(
                            choices=["abstract", "introduction", "methodology", "results", "conclusion"],
                            label="选择要分析的章节",
                            value="abstract"
                        )
                        analyze_btn = gr.Button("📈 开始分析", variant="primary")

                        gr.Markdown("""
                        **📋 分析内容**:
                        - 📝 章节内容摘要
                        - 🔑 关键要点提取
                        - 💡 重要发现总结
                        - ⏱️ 处理性能监控
                        """)

                    with gr.Column(scale=2):
                        section_analysis_output = gr.Textbox(
                            label="📊 章节分析结果",
                            lines=15,
                            interactive=False
                        )

            with gr.Tab("ℹ️ 系统信息"):
                gr.Markdown("### 📋 系统状态和使用指南")

                with gr.Row():
                    with gr.Column():
                        gr.Markdown("""
                        **🔧 技术架构**:
                        - **LLM模型**: 通义千问 (qwen-turbo/qwen-plus)
                        - **向量模型**: BGE中文向量模型 
                        - **向量数据库**: ChromaDB
                        - **文档处理**: PyPDF2 + 智能解析
                        - **前端界面**: Gradio Web UI

                        **⚡ 性能优化**:
                        - 智能分块策略 (800字符/块)
                        - 内容过滤和去重机制
                        - 多策略检索融合
                        - 实时进度显示
                        """)

                    with gr.Column():
                        gr.Markdown("""
                        **📖 使用建议**:

                        1. **论文上传**:
                           - 选择高质量PDF文件
                           - 确保文字可复制
                           - 等待处理完成

                        2. **智能问答**:
                           - 使用具体明确的问题
                           - 参考推荐问题模板
                           - 查看置信度和来源

                        3. **术语解释**:
                           - 输入论文中出现的术语
                           - 支持缩写和全称

                        4. **章节分析**:
                           - 选择感兴趣的章节
                           - 获得结构化分析结果
                        """)

            # 事件绑定
            upload_btn.click(
                fn=self.upload_paper,
                inputs=[file_input],
                outputs=[status_output, summary_output, innovations_output, keypoints_output]
            )

            ask_btn.click(
                fn=self.ask_question,
                inputs=[question_input, chatbot],
                outputs=[chatbot, question_input]
            )

            question_input.submit(
                fn=self.ask_question,
                inputs=[question_input, chatbot],
                outputs=[chatbot, question_input]
            )

            # 示例问题按钮点击事件
            example1_btn.click(lambda: "这篇论文的主要贡献是什么？", outputs=question_input)
            example2_btn.click(lambda: "研究背景和动机是什么？", outputs=question_input)
            example3_btn.click(lambda: "解决了什么问题？", outputs=question_input)
            example4_btn.click(lambda: "使用了什么研究方法？", outputs=question_input)
            example5_btn.click(lambda: "技术实现细节如何？", outputs=question_input)
            example6_btn.click(lambda: "实验设计是怎样的？", outputs=question_input)
            example7_btn.click(lambda: "实验结果如何？", outputs=question_input)
            example8_btn.click(lambda: "有哪些局限性？", outputs=question_input)
            example9_btn.click(lambda: "与其他工作相比有什么优势？", outputs=question_input)

            explain_btn.click(
                fn=self.explain_term,
                inputs=[term_input],
                outputs=[term_output]
            )

            analyze_btn.click(
                fn=self.get_section_analysis,
                inputs=[section_dropdown],
                outputs=[section_analysis_output]
            )

        return demo


def main():
    """主函数"""
    try:
        # 创建UI应用
        ui_app = PaperAssistantUI()

        # 创建界面
        demo = ui_app.create_interface()

        # 启动应用
        print("🎉 启动PaperBot优化版...")
        print("📱 访问地址: http://localhost:7860")
        print("🔧 按Ctrl+C停止服务")

        demo.launch(
            server_name="0.0.0.0",
            server_port=Config.GRADIO_PORT,
            share=Config.GRADIO_SHARE,
            debug=True,
            show_error=True
        )

    except Exception as e:
        logger.error(f"应用启动失败: {e}")
        raise


if __name__ == "__main__":
    main()