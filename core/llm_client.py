import dashscope
from dashscope import Generation
from typing import Optional, List, Any, Dict
import logging
import json
from utils.config import Config

logger = logging.getLogger(__name__)


class QwenLLM:
    """通义千问LLM封装 - 简化版本，避免LangChain兼容性问题"""

    def __init__(
            self,
            api_key: str = None,
            model_name: str = None,
            temperature: float = 0.1,
            max_tokens: int = 2000,
            **kwargs
    ):
        self.api_key = api_key or Config.DASHSCOPE_API_KEY
        self.model_name = model_name or Config.LLM_MODEL
        self.temperature = temperature
        self.max_tokens = max_tokens

        # 设置API密钥
        dashscope.api_key = self.api_key

        if not self.api_key:
            raise ValueError("请设置DASHSCOPE_API_KEY环境变量")

        logger.info(f"QwenLLM初始化完成，模型: {self.model_name}")

    def __call__(self, prompt: str, stop: Optional[List[str]] = None) -> str:
        """直接调用方法"""
        return self._call(prompt, stop)

    def _call(self, prompt: str, stop: Optional[List[str]] = None) -> str:
        """调用通义千问API"""
        try:
            response = Generation.call(
                model=self.model_name,
                prompt=prompt,
                temperature=self.temperature,
                max_tokens=self.max_tokens,
                stop=stop
            )

            if response.status_code == 200:
                return response.output.text.strip()
            else:
                error_msg = f"API调用失败: {response.message}"
                logger.error(error_msg)
                raise Exception(error_msg)

        except Exception as e:
            logger.error(f"LLM调用异常: {e}")
            raise

    @property
    def _llm_type(self) -> str:
        return "qwen"

    @property
    def _identifying_params(self) -> Dict[str, Any]:
        return {
            "model_name": self.model_name,
            "temperature": self.temperature,
            "max_tokens": self.max_tokens
        }


class ModelManager:
    """模型管理器"""

    def __init__(self, api_key: str = None):
        self.api_key = api_key or Config.DASHSCOPE_API_KEY

        # 不同任务使用不同配置的模型
        self.models = {}
        self._init_models()

        logger.info("模型管理器初始化完成")

    def _init_models(self):
        """初始化模型"""
        try:
            self.models = {
                "fast": QwenLLM(
                    api_key=self.api_key,
                    model_name="qwen-turbo",
                    temperature=0.1,
                    max_tokens=1500
                ),
                "smart": QwenLLM(
                    api_key=self.api_key,
                    model_name="qwen-plus",
                    temperature=0.1,
                    max_tokens=2000
                ),
                "creative": QwenLLM(
                    api_key=self.api_key,
                    model_name="qwen-turbo",
                    temperature=0.7,
                    max_tokens=2000
                )
            }
            logger.info("所有模型初始化成功")
        except Exception as e:
            logger.error(f"模型初始化失败: {e}")
            raise

    def get_model(self, task_type: str = "fast") -> QwenLLM:
        """根据任务类型获取合适的模型"""
        task_model_mapping = {
            # 快速任务
            "qa": "fast",
            "explanation": "fast",
            "translation": "fast",

            # 复杂任务
            "summary": "smart",
            "analysis": "smart",
            "comparison": "smart",

            # 创意任务
            "review": "creative",
            "writing": "creative"
        }

        model_type = task_model_mapping.get(task_type, "fast")
        return self.models[model_type]

    def call_with_retry(
            self,
            task_type: str,
            prompt: str,
            max_retries: int = 3
    ) -> str:
        """带重试的模型调用"""
        model = self.get_model(task_type)

        for attempt in range(max_retries):
            try:
                return model(prompt)
            except Exception as e:
                logger.warning(f"模型调用失败 (尝试 {attempt + 1}/{max_retries}): {e}")
                if attempt == max_retries - 1:
                    raise

        raise Exception("模型调用失败，已达到最大重试次数")

    def parse_json_response(self, response: str) -> Dict:
        """解析JSON格式的响应"""
        try:
            # 尝试直接解析
            return json.loads(response)
        except json.JSONDecodeError:
            # 如果直接解析失败，尝试提取JSON部分
            import re
            json_match = re.search(r'\{.*\}', response, re.DOTALL)
            if json_match:
                try:
                    return json.loads(json_match.group())
                except json.JSONDecodeError:
                    pass

            # 如果还是失败，返回错误信息
            logger.error(f"JSON解析失败: {response}")
            return {"error": "JSON解析失败", "raw_response": response}


# 为了兼容LangChain，创建一个适配器
from langchain.llms.base import LLM


class QwenLangChainLLM(LLM):
    """LangChain兼容的QwenLLM包装器"""

    def __init__(self, qwen_llm: QwenLLM, **kwargs):
        super().__init__(**kwargs)
        self.qwen_llm = qwen_llm

    def _call(self, prompt: str, stop: Optional[List[str]] = None, run_manager=None) -> str:
        return self.qwen_llm._call(prompt, stop)

    @property
    def _llm_type(self) -> str:
        return "qwen"

    @property
    def _identifying_params(self) -> Dict[str, Any]:
        return self.qwen_llm._identifying_params