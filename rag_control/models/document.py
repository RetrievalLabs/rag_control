from pydantic import BaseModel


class DocumentPolicy(BaseModel):
    top_k: int = 5
    filter_name: str | None = None
