"""Settings com pydantic-settings — carrega .env automaticamente."""
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    # App
    APP_ENV: str = "development"
    LOG_LEVEL: str = "INFO"
    SECRET_KEY: str = "dev-secret-key"

    # LLM
    OLLAMA_HOST: str = "http://localhost:11434"
    OLLAMA_MODEL: str = "llama3.2:1b"
    OPENAI_API_KEY: str = ""
    ANTHROPIC_API_KEY: str = ""

    # Embeddings
    JINA_API_KEY: str = ""
    JINA_MODEL: str = "jina-embeddings-v3"

    # OpenSearch
    OPENSEARCH_HOST: str = "http://localhost:9200"
    OPENSEARCH_INDEX_RULES: str = "pricing-rules"

    # PostgreSQL
    POSTGRES_URL: str = "postgresql+psycopg2://app:app@localhost:5432/app"

    # DuckDB
    DUCKDB_PATH: str = "./data/pricing.duckdb"

    # Guardrail (Week7 pattern)
    GUARDRAIL_THRESHOLD: int = 60
    MAX_RETRIEVAL_ATTEMPTS: int = 2

    # Security
    SQL_MAX_ROWS: int = 1000
    SQL_TIMEOUT_SECONDS: int = 30
    COST_BUDGET_ROWS: int = 100_000

    @property
    def has_jina_key(self) -> bool:
        return bool(self.JINA_API_KEY)

    @property
    def has_openai_key(self) -> bool:
        return bool(self.OPENAI_API_KEY)

    @property
    def has_anthropic_key(self) -> bool:
        return bool(self.ANTHROPIC_API_KEY)


settings = Settings()
