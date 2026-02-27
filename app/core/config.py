from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8")

    # 공공 API
    public_api_key: str
    public_api_base_url: str = "https://apis.data.go.kr/1140100"

    # LLM
    # CPU 로컬 테스트: Qwen/Qwen2.5-1.5B-Instruct (약 3GB)
    # GPU 프로덕션:   Qwen/Qwen2.5-7B-Instruct  (약 14GB bfloat16)
    llm_model_name: str = "Qwen/Qwen2.5-1.5B-Instruct"
    llm_temperature: float = 0.1
    llm_max_new_tokens: int = 512


settings = Settings()