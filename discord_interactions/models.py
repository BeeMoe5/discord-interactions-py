from pydantic import BaseModel
from enum import Enum
from typing import Optional
import datetime


class InteractionType(Enum):
    PING = PONG = 1
    APPLICATION_COMMAND = 2
    MESSAGE_COMMAND = 3
    APPLICATION_COMMAND_AUTOCOMPLETE = 4
    MODAL_SUBMIT = 5


class AuthorEmbedModel(BaseModel):
    name: str
    icon_url: Optional[str] = None


class FooterEmbedModel(BaseModel):
    text: str
    icon_url: Optional[str] = None


class FieldEmbedModel(BaseModel):
    name: str
    value: str
    inline: Optional[bool] = False


class ThumbnailEmbedModel(BaseModel):
    url: str


class EmbedModel(BaseModel):
    type: str = "rich"
    title: Optional[str] = None
    timestamp: Optional[datetime.datetime] = None
    color: Optional[int] = None
    description: Optional[str] = None
    url: Optional[str] = None
    author: Optional[AuthorEmbedModel] = None
    footer: Optional[FooterEmbedModel] = None
    fields: Optional[list[FieldEmbedModel]] = None
    thumbnail: Optional[ThumbnailEmbedModel] = None


class ContentModel(BaseModel):
    content: str
