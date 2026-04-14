"""
输出验证器

提供统一的 Pydantic 验证和 JSON 提取功能。
"""

from __future__ import annotations

import json
from typing import Any

from pydantic import BaseModel, ValidationError


class OutputValidationError(Exception):
    """输出验证错误"""

    def __init__(self, message: str, retry_count: int = 0) -> None:
        self.retry_count = retry_count
        super().__init__(message)


class OutputValidator:
    """统一的输出验证器"""

    def __init__(self, schema: type[BaseModel], max_retries: int = 3) -> None:
        self.schema = schema
        self.max_retries = max_retries

    async def validate_output(
        self,
        raw_output: str,
        model_client: Any,
        temperature: float = 0.7,
    ) -> BaseModel:
        """验证输出并在失败时尝试自我修正。"""
        for attempt in range(self.max_retries):
            try:
                parsed = self._extract_json(raw_output)
                return self.schema.model_validate(parsed)
            except (json.JSONDecodeError, ValidationError, ValueError) as exc:
                if attempt >= self.max_retries - 1:
                    raise OutputValidationError(
                        f"Failed to validate after {self.max_retries} attempts: {exc}",
                        retry_count=self.max_retries,
                    ) from exc

                raw_output = await self._self_correction(
                    invalid_output=raw_output,
                    error_message=str(exc),
                    model_client=model_client,
                    temperature=max(0.0, temperature - 0.1 * attempt),
                )

        raise OutputValidationError(
            "Validation loop exited unexpectedly",
            retry_count=self.max_retries,
        )

    async def _self_correction(
        self,
        invalid_output: str,
        error_message: str,
        model_client: Any,
        temperature: float,
    ) -> str:
        """请求模型客户端修正无效输出。"""
        correction_prompt = f"""
The previous output was invalid due to: {error_message}

Invalid output:
{invalid_output}

Please correct the output to match the required JSON schema.
Ensure:
1. Valid JSON format
2. All required fields are present
3. Values match the expected types

Corrected output:
"""

        response = await model_client.create(
            messages=[{"role": "user", "content": correction_prompt}],
            temperature=temperature,
            top_p=0.9,
        )

        return response.choices[0].message.content

    def _extract_json(self, text: str) -> dict[str, Any]:
        """从纯 JSON 或混合文本中提取第一个可解析的 JSON 对象。"""
        try:
            return json.loads(text)
        except json.JSONDecodeError:
            pass

        decoder = json.JSONDecoder()
        for index, char in enumerate(text):
            if char != "{":
                continue

            try:
                parsed, _ = decoder.raw_decode(text[index:])
            except json.JSONDecodeError:
                continue

            if isinstance(parsed, dict):
                return parsed

        raise json.JSONDecodeError("No valid JSON object found", text, 0)
