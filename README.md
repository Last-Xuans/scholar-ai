<<<<<<< HEAD
# 📚 PaperBot - 智能论文阅读助手

一个基于大语言模型和RAG技术的智能论文阅读助手，帮助研究人员快速理解和分析学术论文。

![Python](https://img.shields.io/badge/Python-3.8+-blue)
![License](https://img.shields.io/badge/License-MIT-green)
![Status](https://img.shields.io/badge/Status-Ready-success)

## ✨ 功能特色

- 🔍 **智能问答**: 基于论文内容回答问题，支持多轮对话
- 📝 **自动摘要**: 生成论文总结和关键点提取
- 🔖 **术语解释**: 智能解释专业术语和概念
- 📊 **章节分析**: 分析各章节要点和贡献
- 💡 **创新点识别**: 自动识别论文的技术创新
- 📈 **置信度评估**: 为回答提供可信度评分

## 🚀 快速开始

### 方法一：一键启动（推荐）

```bash
# 1. 克隆项目
git clone <your-repo-url>
cd paper-assistant

# 2. 一键启动
python quick_start.py
```

### 方法二：手动安装

```bash
# 1. 安装依赖
pip install -r requirements.txt

# 2. 配置API密钥
cp .env.example .env
# 编辑.env文件，设置DASHSCOPE_API_KEY

# 3. 启动Gradio界面
python frontend/gradio_app.py

# 或启动API服务
python app.py
```

## 🔑 API密钥配置

1. 访问 [阿里云DashScope](https://dashscope.aliyun.com/)
2. 注册账号并获取API密钥
3. 在`.env`文件中设置：
   ```bash
   DASHSCOPE_API_KEY=your_actual_api_key_here
   ```

详细步骤请查看 [API密钥获取指南](API_KEY_GUIDE.md)

## 📖 使用方法

### 1. 上传论文
- 支持PDF格式的学术论文
- 自动解析论文结构（摘要、引言、方法、结果、结论）
- 生成论文元信息和摘要

### 2. 智能问答
```
问：这篇论文的主要贡献是什么？
答：本文的主要贡献包括：1. 提出了xxx方法... 2. 在xxx数据集上达到了...

问：实验结果如何？
答：实验结果显示...（附带置信度和参考来源）
```

### 3. 术语解释
输入专业术语，获得基于论文上下文的详细解释。

### 4. 章节分析
选择特定章节，获得该章节的关键要点和分析。

## 🏗️ 技术架构

```
📁 项目结构
├── core/                # 核心功能模块
│   ├── pdf_parser.py   # PDF解析
│   ├── embeddings.py   # 向量化处理
│   ├── llm_client.py   # LLM客户端
│   ├── qa_chain.py     # 问答系统
│   └── summarizer.py   # 摘要生成
├── frontend/           # 前端界面
│   └── gradio_app.py  # Gradio界面
├── utils/             # 工具模块
│   ├── config.py      # 配置管理
│   └── prompts.py     # Prompt模板
└── app.py            # FastAPI服务
```

### 核心技术

- **LLM**: 通义千问 (qwen-turbo/qwen-plus)
- **Embedding**: BGE中文向量模型
- **向量数据库**: ChromaDB
- **文档处理**: PyPDF2 + 智能章节识别
- **前端**: Gradio Web界面
- **后端**: FastAPI RESTful API

## 🧪 测试

```bash
# 运行基础测试
python test_basic.py

# 运行完整测试
python test_complete.py
```

测试需要：
- 在项目根目录放置测试PDF文件 `test_paper.pdf`
- 正确配置API密钥

## 📊 性能指标

- **PDF解析**: 支持37页+论文，秒级解析
- **向量化**: BGE模型，准确率85%+
- **问答响应**: 平均2-3秒
- **支持格式**: PDF学术论文
- **语言支持**: 中英文混合

## 🛠️ 开发

### 添加新功能

1. **新增问答类型**: 在 `utils/prompts.py` 添加Prompt模板
2. **扩展解析能力**: 修改 `core/pdf_parser.py`
3. **优化检索策略**: 调整 `core/qa_chain.py` 检索参数
4. **界面定制**: 修改 `frontend/gradio_app.py`

### API接口

启动FastAPI服务后，访问 `http://localhost:8000/docs` 查看API文档。

主要接口：
- `POST /upload` - 上传论文
- `POST /ask` - 问答
- `POST /explain` - 术语解释
- `GET /summary` - 获取摘要

## 🐛 常见问题

### 1. API调用失败
- 检查网络连接
- 确认API密钥正确
- 查看余额是否充足

### 2. PDF解析失败
- 确认文件是有效的PDF
- 检查文件大小（建议<50MB）
- 尝试不同的PDF文件

### 3. 向量化慢
- 首次运行会下载模型（约2GB）
- 确认网络稳定
- 考虑使用GPU加速

### 4. 依赖安装失败
```bash
# 升级pip
pip install --upgrade pip

# 使用国内镜像
pip install -r requirements.txt -i https://pypi.tuna.tsinghua.edu.cn/simple/
```

## 📈 性能优化

- **缓存机制**: 相同问题缓存回答
- **批量处理**: 支持多文档批量分析
- **模型选择**: 根据任务复杂度选择不同模型
- **参数调优**: 可调整chunk大小、检索数量等

## 🤝 贡献

欢迎提交Issue和Pull Request！

1. Fork项目
2. 创建特性分支
3. 提交更改
4. 推送到分支
5. 创建Pull Request

## 📄 许可证

本项目基于 MIT 许可证开源 - 查看 [LICENSE](LICENSE) 文件了解详情。

## 🙏 致谢

- [LangChain](https://github.com/langchain-ai/langchain) - LLM应用框架
- [ChromaDB](https://github.com/chroma-core/chroma) - 向量数据库
- [Gradio](https://github.com/gradio-app/gradio) - 快速构建ML界面
- [阿里云DashScope](https://dashscope.aliyun.com/) - 大语言模型服务

## 📞 联系

如有问题或建议，请提交Issue或联系开发者。

---

⭐ 如果这个项目对你有帮助，请给个Star！
=======
# scholar-ai
论文阅读助手 - 基于RAG和大语言模型
>>>>>>> 17470e66a5ab1daf186843b4e2205d1871ffdec7
