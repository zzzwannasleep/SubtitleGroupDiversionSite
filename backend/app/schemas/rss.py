from pydantic import BaseModel


class RssFeedLink(BaseModel):
    name: str
    url: str

