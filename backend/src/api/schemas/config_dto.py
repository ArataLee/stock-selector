from pydantic import BaseModel

class ProviderConfigRequest(BaseModel):
    id: str
    api_base: str
    api_key: str
    model: str
    default: bool = False
    max_tokens: int = 4096

class DataSourceAccountRequest(BaseModel):
    token: str
