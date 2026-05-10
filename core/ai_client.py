"""
OpenAI-compatible API client wrapper for resume optimization.
"""

import openai
from typing import Optional

from .config import Config
from .logger import get_logger, LoggerMixin


class AIClient(LoggerMixin):
    """OpenAI-compatible API client with error handling and retry logic."""

    def __init__(
        self,
        api_key: Optional[str] = None,
        model: Optional[str] = None,
        provider: Optional[str] = None,
        base_url: Optional[str] = None,
    ):
        """
        Initialize AI client.

        Args:
            api_key: LLM API key. If None, loads from config/env.
            model: Model name. If None, uses config default.
            provider: Provider name for display/config defaults.
            base_url: OpenAI-compatible base URL.
        """
        self.config = Config()
        self.provider = provider or self.config.llm_provider
        self.api_key = api_key or self.config.llm_api_key
        self.model = model or self.config.llm_model
        self.base_url = base_url or self.config.llm_base_url
        self._client = None

    @property
    def client(self) -> openai.OpenAI:
        """Lazy-load OpenAI-compatible client."""
        if self._client is None:
            if not self.api_key:
                raise ValueError(f"LLM API key not configured for provider: {self.provider}")
            kwargs = {"api_key": self.api_key}
            if self.base_url:
                kwargs["base_url"] = self.base_url.rstrip("/")
            self._client = openai.OpenAI(**kwargs)
        return self._client

    def is_available(self) -> bool:
        """Check if API key is configured."""
        return bool(self.api_key)

    def optimize_resume(self, content: str, jd: str = "") -> str:
        """
        Optimize resume content using AI.

        Args:
            content: Original resume markdown content.
            jd: Job description for context (optional).

        Returns:
            Optimized resume content in markdown.
        """
        prompt = f"""
请优化以下简历内容，使其更专业、更有竞争力，突出亮点和成果，使用量化数据，符合招聘要求。
{'招聘JD参考：' + jd if jd else ''}

简历内容：
{content}

要求：
1. 保持原有信息真实，不编造内容
2. 优化表述，使用专业术语，突出成果和贡献
3. 适当增加量化数据，提升说服力
4. 结构清晰，重点突出
5. 输出格式保持markdown不变
"""

        return self._call_chat(prompt)

    def analyze_jd_match(self, jd_text: str, resume_text: str) -> tuple[str, str]:
        """
        Analyze JD and resume match, return suggestions and optimized resume.

        Args:
            jd_text: Job description text.
            resume_text: Original resume text.

        Returns:
            Tuple of (suggestions, optimized_resume).
        """
        prompt = f"""
你是专业的简历优化专家，请根据以下招聘JD，分析用户简历的匹配度，然后生成优化后的完整简历内容。

招聘JD：
{jd_text}

用户原始简历内容：
{resume_text}

要求：
1. 先给出匹配度评分（0-100分）和3条核心优化建议
2. 然后生成优化后的完整简历内容，要求：
   - 保持用户所有真实经历不变，不编造信息
   - 优化表述，匹配JD中的关键词和技能要求
   - 突出和JD相关的项目经验和技能
   - 使用量化成果，提升说服力
   - 结构保持：个人信息 → 教育背景 → 工作经验 → 项目经验 → 技能栈
   - 输出格式为纯markdown，不要其他解释内容
3. 优化后的简历内容要完全适配招聘JD的要求，最大化通过ATS筛选的概率
"""

        result = self._call_chat(prompt)

        # Parse result - expect format: "suggestions # optimized_resume"
        if '# ' in result:
            parts = result.split('# ', 1)
            suggestions = parts[0]
            optimized = '# ' + parts[1]
        else:
            suggestions = result
            optimized = result

        return suggestions, optimized

    def ats_score(self, resume_text: str, jd_text: str) -> dict:
        """
        Calculate ATS (Applicant Tracking System) score.

        Args:
            resume_text: Resume text.
            jd_text: Job description text.

        Returns:
            Dict with score, keywords_found, keywords_missing.
        """
        prompt = f"""
你是ATS系统模拟器，请分析以下简历与JD的匹配度。

简历：
{resume_text}

JD：
{jd_text}

请分析并返回JSON格式的评分：
{{
    "ats_score": 0-100的分数,
    "keywords_found": ["找到的关键词列表"],
    "keywords_missing": ["缺失的重要关键词"],
    "format_score": 0-100的格式分数,
    "suggestions": ["改进建议列表"]
}}

只返回JSON，不要其他内容。
"""

        result = self._call_chat(prompt)

        # Parse JSON from response
        import json
        import re

        json_match = re.search(r'\{[^}]+\}', result, re.DOTALL)
        if json_match:
            try:
                return json.loads(json_match.group())
            except json.JSONDecodeError:
                pass

        return {
            'ats_score': 0,
            'keywords_found': [],
            'keywords_missing': [],
            'format_score': 0,
            'suggestions': ['Unable to parse ATS analysis']
        }

    def _call_chat(self, prompt: str, max_retries: int = 3) -> str:
        """
        Call OpenAI-compatible chat API with retry logic.

        Args:
            prompt: The prompt to send.
            max_retries: Maximum number of retries.

        Returns:
            Response content.

        Raises:
            Exception: If all retries fail.
        """
        if not self.is_available():
            raise ValueError(f"LLM API key not configured for provider: {self.provider}")

        for attempt in range(max_retries):
            try:
                response = self.client.chat.completions.create(
                    model=self.model,
                    messages=[{"role": "user", "content": prompt}]
                )
                return response.choices[0].message.content

            except Exception as e:
                self.logger.warning(f"API call attempt {attempt + 1} failed: {e}")
                if attempt == max_retries - 1:
                    raise

        return ""
