#!/usr/bin/env python3
"""
一键启动脚本 - 自动检查环境并启动应用
"""

import os
import sys
import subprocess
import time
from pathlib import Path


def check_python_version():
    """检查Python版本"""
    version = sys.version_info
    if version.major < 3 or (version.major == 3 and version.minor < 8):
        print("❌ 需要Python 3.8或更高版本")
        return False
    print(f"✅ Python版本: {version.major}.{version.minor}.{version.micro}")
    return True


def check_env_file():
    """检查环境文件"""
    env_file = Path(".env")
    if not env_file.exists():
        print("❌ 未找到.env文件")
        print("📝 正在创建示例.env文件...")

        env_content = """# 通义千问API密钥 - 请替换为你的实际密钥
DASHSCOPE_API_KEY=your_actual_api_key_here

# 模型配置
EMBEDDING_MODEL=BAAI/bge-small-zh-v1.5
LLM_MODEL=qwen-turbo

# 应用配置
GRADIO_PORT=7860
GRADIO_SHARE=false

# 日志配置
LOG_LEVEL=INFO
"""
        with open(".env", "w", encoding="utf-8") as f:
            f.write(env_content)

        print("✅ 已创建.env文件")
        print("⚠️  请编辑.env文件，设置你的DASHSCOPE_API_KEY")
        return False

    # 检查API密钥是否设置
    with open(".env", "r", encoding="utf-8") as f:
        content = f.read()
        if "your_actual_api_key_here" in content:
            print("⚠️  请在.env文件中设置正确的DASHSCOPE_API_KEY")
            return False

    print("✅ .env文件检查通过")
    return True


def install_dependencies():
    """安装依赖"""
    print("📦 检查依赖...")

    try:
        import gradio
        import langchain
        import chromadb
        import sentence_transformers
        import dashscope
        print("✅ 主要依赖已安装")
        return True
    except ImportError as e:
        print(f"❌ 缺少依赖: {e}")
        print("📦 正在安装依赖...")

        try:
            subprocess.run([
                sys.executable, "-m", "pip", "install", "-r", "requirements.txt"
            ], check=True)
            print("✅ 依赖安装完成")
            return True
        except subprocess.CalledProcessError:
            print("❌ 依赖安装失败")
            return False


def create_directories():
    """创建必要目录"""
    dirs = ["logs", "chroma_db", "data"]
    for dir_name in dirs:
        Path(dir_name).mkdir(exist_ok=True)
    print("✅ 目录创建完成")


def test_basic_functionality():
    """测试基础功能"""
    print("🧪 测试基础功能...")

    try:
        from utils.config import Config
        Config.validate()
        print("✅ 配置验证通过")

        from core.embeddings import DocumentProcessor
        processor = DocumentProcessor()
        print("✅ 向量处理器初始化成功")

        from core.llm_client import ModelManager
        model_manager = ModelManager()
        print("✅ 模型管理器初始化成功")

        return True
    except Exception as e:
        print(f"❌ 基础功能测试失败: {e}")
        return False


def start_gradio_app():
    """启动Gradio应用"""
    print("🚀 启动Gradio界面...")

    try:
        from frontend.gradio_app import main
        main()
    except KeyboardInterrupt:
        print("\n👋 应用已停止")
    except Exception as e:
        print(f"❌ 应用启动失败: {e}")


def main():
    """主函数"""
    print("🚀 PaperBot 一键启动")
    print("=" * 50)

    # 1. 检查Python版本
    if not check_python_version():
        return

    # 2. 检查环境文件
    if not check_env_file():
        print("\n📋 下一步操作:")
        print("1. 获取通义千问API密钥: https://dashscope.aliyun.com/")
        print("2. 编辑.env文件，设置DASHSCOPE_API_KEY")
        print("3. 重新运行此脚本")
        return

    # 3. 创建目录
    create_directories()

    # 4. 安装依赖
    if not install_dependencies():
        return

    # 5. 测试基础功能
    if not test_basic_functionality():
        print("\n💡 可能的解决方案:")
        print("1. 检查网络连接")
        print("2. 确认API密钥正确")
        print("3. 重新安装依赖: pip install -r requirements.txt")
        return

    print("\n🎉 所有检查通过！")
    print("📋 功能说明:")
    print("- 📄 论文上传: 支持PDF文件解析")
    print("- 💬 智能问答: 基于论文内容回答问题")
    print("- 📖 术语解释: 解释专业术语")
    print("- 📊 章节分析: 分析各章节要点")

    print("\n" + "=" * 50)
    input("按回车键启动应用...")

    # 6. 启动应用
    start_gradio_app()


if __name__ == "__main__":
    main()