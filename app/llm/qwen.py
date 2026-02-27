"""Qwen2.5 Instruct 모델 래퍼.

앱 시작 시 qwen_model.load()를 1회 호출해 모델을 메모리에 올립니다.
이후 generate()로 추론합니다.

디바이스 우선순위: CUDA → MPS (Apple Silicon) → CPU
"""

import torch
from transformers import AutoModelForCausalLM, AutoTokenizer

from app.core.config import settings


def _select_device() -> torch.device:
    if torch.cuda.is_available():
        return torch.device("cuda")
    if torch.backends.mps.is_available():
        return torch.device("mps")
    return torch.device("cpu")


def _select_dtype(device: torch.device) -> torch.dtype:
    if device.type == "cpu":
        return torch.float32
    return torch.bfloat16


class QwenModel:
    def __init__(self) -> None:
        self.tokenizer: AutoTokenizer | None = None
        self.model: AutoModelForCausalLM | None = None
        self.device: torch.device = _select_device()

    def load(self) -> None:
        dtype = _select_dtype(self.device)
        self.tokenizer = AutoTokenizer.from_pretrained(settings.llm_model_name)
        self.model = AutoModelForCausalLM.from_pretrained(
            settings.llm_model_name,
            torch_dtype=dtype,
            device_map=str(self.device),
        )
        self.model.eval()

    def generate(self, messages: list[dict]) -> str:
        if self.model is None or self.tokenizer is None:
            raise RuntimeError("모델이 로드되지 않았습니다. load()를 먼저 호출하세요.")

        text = self.tokenizer.apply_chat_template(
            messages,
            tokenize=False,
            add_generation_prompt=True,
        )
        inputs = self.tokenizer([text], return_tensors="pt").to(self.device)

        with torch.no_grad():
            output_ids = self.model.generate(
                **inputs,
                max_new_tokens=settings.llm_max_new_tokens,
                temperature=settings.llm_temperature,
                do_sample=settings.llm_temperature > 0,
            )

        # 입력 토큰 제거, 생성된 부분만 디코딩
        new_ids = output_ids[0][len(inputs.input_ids[0]):]
        return self.tokenizer.decode(new_ids, skip_special_tokens=True)


qwen_model = QwenModel()
