from fastapi import FastAPI, File, UploadFile, HTTPException
from fastapi.responses import JSONResponse
import uvicorn
import logging
import os
import tempfile
from pathlib import Path

# 导入自定义模块
from utils.config import Config
from core.pdf_parser import PaperParser
from core.llm_client import ModelManager
from core.qa_chain import PaperQASystem
from core.summarizer import PaperSummarizer

# 配置日志
logging.basicConfig(
    level=getattr(logging, Config.LOG_LEVEL),
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(Config.LOG_FILE),
        logging.StreamHandler()
    ]
)

logger = logging.getLogger(__name__)


class PaperAssistantApp:
    """论文助手主应用"""

    def __init__(self):
        # 验证配置
        Config.validate()

        # 初始化组件
        self.model_manager = ModelManager()
        self.parser = PaperParser()
        self.qa_system = PaperQASystem(self.model_manager)
        self.summarizer = PaperSummarizer(self.model_manager)

        # 当前论文状态
        self.current_paper = None
        self.current_summary = None

        logger.info("论文助手应用初始化完成")

    def upload_paper(self, file_path: str) -> dict:
        """上传并处理论文"""
        try:
            logger.info(f"开始处理论文: {file_path}")

            # 解析PDF
            sections = self.parser.extract_sections(file_path)
            metadata = self.parser.extract_metadata(file_path)

            # 加载到问答系统
            paper_title = sections.get('title') or metadata.get('title') or "未知论文"
            success = self.qa_system.load_paper(sections, paper_title)

            if not success:
                raise Exception("论文加载失败")

            # 生成摘要
            summary = self.summarizer.generate_comprehensive_summary(sections)

            # 保存状态
            self.current_paper = {
                "sections": sections,
                "metadata": metadata,
                "title": paper_title
            }
            self.current_summary = summary

            logger.info(f"论文处理完成: {paper_title}")

            return {
                "success": True,
                "message": f"论文《{paper_title}》上传成功",
                "paper_info": {
                    "title": paper_title,
                    "pages": metadata.get('pages', 0),
                    "sections": list(sections.keys())
                },
                "summary": summary
            }

        except Exception as e:
            logger.error(f"论文处理失败: {e}")
            return {
                "success": False,
                "message": f"论文处理失败: {str(e)}",
                "paper_info": None,
                "summary": None
            }

    def ask_question(self, question: str) -> dict:
        """回答问题"""
        if not self.current_paper:
            return {
                "success": False,
                "message": "请先上传论文",
                "answer": None
            }

        try:
            result = self.qa_system.ask_question(question)

            return {
                "success": True,
                "message": "回答生成成功",
                "answer": result["answer"],
                "sources": result["sources"],
                "confidence": result["confidence"]
            }

        except Exception as e:
            logger.error(f"问答失败: {e}")
            return {
                "success": False,
                "message": f"问答失败: {str(e)}",
                "answer": None
            }

    def explain_term(self, term: str) -> dict:
        """解释术语"""
        if not self.current_paper:
            return {
                "success": False,
                "message": "请先上传论文",
                "explanation": None
            }

        try:
            explanation = self.qa_system.explain_term(term)

            return {
                "success": True,
                "message": "术语解释成功",
                "explanation": explanation
            }

        except Exception as e:
            logger.error(f"术语解释失败: {e}")
            return {
                "success": False,
                "message": f"术语解释失败: {str(e)}",
                "explanation": None
            }

    def get_section_keypoints(self, section_name: str) -> dict:
        """获取章节关键点"""
        if not self.current_paper:
            return {
                "success": False,
                "message": "请先上传论文",
                "keypoints": []
            }

        try:
            keypoints = self.qa_system.get_section_keypoints(section_name)

            return {
                "success": True,
                "message": "关键点提取成功",
                "keypoints": keypoints
            }

        except Exception as e:
            logger.error(f"关键点提取失败: {e}")
            return {
                "success": False,
                "message": f"关键点提取失败: {str(e)}",
                "keypoints": []
            }


# 创建FastAPI应用
app = FastAPI(title="PaperBot API", description="智能论文阅读助手API")

# 创建应用实例
paper_app = PaperAssistantApp()


@app.get("/")
async def root():
    return {"message": "PaperBot API 正在运行"}


@app.post("/upload")
async def upload_paper(file: UploadFile = File(...)):
    """上传论文"""
    if not file.filename.endswith('.pdf'):
        raise HTTPException(status_code=400, detail="只支持PDF文件")

    # 保存临时文件
    with tempfile.NamedTemporaryFile(delete=False, suffix='.pdf') as tmp_file:
        content = await file.read()
        tmp_file.write(content)
        tmp_file_path = tmp_file.name

    try:
        # 处理论文
        result = paper_app.upload_paper(tmp_file_path)
        return JSONResponse(content=result)
    finally:
        # 清理临时文件
        os.unlink(tmp_file_path)


@app.post("/ask")
async def ask_question(request: dict):
    """问答接口"""
    question = request.get("question", "")
    if not question:
        raise HTTPException(status_code=400, detail="问题不能为空")

    result = paper_app.ask_question(question)
    return JSONResponse(content=result)


@app.post("/explain")
async def explain_term(request: dict):
    """术语解释接口"""
    term = request.get("term", "")
    if not term:
        raise HTTPException(status_code=400, detail="术语不能为空")

    result = paper_app.explain_term(term)
    return JSONResponse(content=result)


@app.get("/summary")
async def get_summary():
    """获取论文摘要"""
    if not paper_app.current_summary:
        raise HTTPException(status_code=400, detail="请先上传论文")

    return JSONResponse(content={
        "success": True,
        "summary": paper_app.current_summary
    })


@app.get("/sections/{section_name}/keypoints")
async def get_keypoints(section_name: str):
    """获取章节关键点"""
    result = paper_app.get_section_keypoints(section_name)
    return JSONResponse(content=result)


@app.get("/status")
async def get_status():
    """获取应用状态"""
    return JSONResponse(content={
        "status": "running",
        "has_paper": paper_app.current_paper is not None,
        "paper_title": paper_app.current_paper.get("title") if paper_app.current_paper else None
    })


if __name__ == "__main__":
    uvicorn.run(
        "app:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="info"
    )