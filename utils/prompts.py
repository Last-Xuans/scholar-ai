from langchain.prompts import PromptTemplate

# 论文问答Prompt
PAPER_QA_PROMPT = PromptTemplate(
    template="""你是一个专业的学术论文阅读助手。基于以下论文内容回答用户问题。

论文相关内容：
{context}

用户问题：{question}

回答要求：
1. 基于给定的论文内容进行回答
2. 如果内容中没有相关信息，请明确说明
3. 回答要准确、专业，使用中文
4. 可以适当引用原文，但要标明出处
5. 如果涉及技术术语，请简要解释

回答：""",
    input_variables=["context", "question"]
)

# 论文摘要生成Prompt
PAPER_SUMMARY_PROMPT = PromptTemplate(
    template="""请为以下论文内容生成一个详细的中文摘要。

论文标题：{title}

论文内容：
{content}

请生成包含以下部分的摘要：
1. 研究背景和问题
2. 主要方法和技术
3. 核心贡献和创新点
4. 实验结果或主要发现
5. 局限性和未来工作方向

摘要长度：200-300字
语言：中文，学术风格

摘要：""",
    input_variables=["title", "content"]
)

# 术语解释Prompt
TERM_EXPLANATION_PROMPT = PromptTemplate(
    template="""作为学术专家，请解释以下术语在给定论文上下文中的含义。

术语：{term}

论文上下文：
{context}

请提供：
1. 术语的基本定义
2. 在该论文中的具体含义
3. 相关的技术背景
4. 如果有的话，提供简单的例子

解释语言：中文
解释风格：准确但易懂

解释：""",
    input_variables=["term", "context"]
)

# 关键点提取Prompt
KEYPOINTS_EXTRACTION_PROMPT = PromptTemplate(
    template="""请从以下论文章节中提取关键要点。

章节名称：{section_name}
章节内容：
{content}

请提取：
1. 主要观点（3-5个）
2. 重要数据或结果
3. 关键方法或技术
4. 值得注意的发现

输出格式：
- 每个要点一行
- 使用简洁的中文表述
- 按重要性排序

关键要点：""",
    input_variables=["section_name", "content"]
)

# 创新点分析Prompt
INNOVATION_ANALYSIS_PROMPT = PromptTemplate(
    template="""请分析以下论文的创新点和贡献。

论文标题：{title}
论文内容：
{content}

请分析以下方面：
1. 技术创新点
2. 方法论贡献
3. 理论贡献
4. 实践应用价值
5. 与现有工作的差异

输出格式：JSON格式，包含以下字段：
- technical_innovations: 技术创新点列表
- methodological_contributions: 方法论贡献列表
- theoretical_contributions: 理论贡献列表
- practical_value: 实践应用价值
- differences_from_existing_work: 与现有工作的主要差异

分析：""",
    input_variables=["title", "content"]
)

# 论文比较Prompt
PAPER_COMPARISON_PROMPT = PromptTemplate(
    template="""请比较以下两篇论文的异同点。

论文1标题：{title1}
论文1内容：{content1}

论文2标题：{title2}
论文2内容：{content2}

请从以下维度进行比较：
1. 研究问题和目标
2. 采用的方法和技术
3. 实验设计和数据
4. 主要结果和结论
5. 贡献和创新点

比较结果：""",
    input_variables=["title1", "content1", "title2", "content2"]
)

# 文献综述生成Prompt
LITERATURE_REVIEW_PROMPT = PromptTemplate(
    template="""基于以下多篇论文，生成一个主题相关的文献综述。

研究主题：{topic}

论文列表：
{papers_info}

请生成包含以下部分的文献综述：
1. 研究背景和现状
2. 主要研究方法分类
3. 重要发现和结论总结
4. 存在的问题和挑战
5. 未来研究方向

综述长度：500-800字
语言：中文学术风格

文献综述：""",
    input_variables=["topic", "papers_info"]
)