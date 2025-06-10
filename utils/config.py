import os
from dotenv import load_dotenv

# 加载环境变量
load_dotenv()


class Config:
    # API配置
    DASHSCOPE_API_KEY = os.getenv("DASHSCOPE_API_KEY", "")

    # 模型配置
    EMBEDDING_MODEL = "BAAI/bge-small-zh-v1.5"  # 轻量级中文embedding模型
    LLM_MODEL = "qwen-turbo"  # 通义千问模型

    # 向量数据库配置
    CHROMA_DB_PATH = "./chroma_db"

    # 文本分割配置
    CHUNK_SIZE = 500
    CHUNK_OVERLAP = 50

    # 检索配置
    RETRIEVE_K = 4  # 检索top-k文档

    # 界面配置
    GRADIO_PORT = 7860
    GRADIO_SHARE = False

    # 日志配置
    LOG_LEVEL = "INFO"
    LOG_FILE = "./logs/app.log"

    @classmethod
    def validate(cls):
        """验证配置"""
        if not cls.DASHSCOPE_API_KEY:
            raise ValueError("请设置DASHSCOPE_API_KEY环境变量")

        # 创建必要目录
        os.makedirs("./logs", exist_ok=True)
        os.makedirs("./chroma_db", exist_ok=True)
        os.makedirs("./data", exist_ok=True)