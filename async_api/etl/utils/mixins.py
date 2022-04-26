from datetime import datetime

from pydantic import BaseModel


class UUIDMixin(BaseModel):
    id: str


class ModifiedMixin(BaseModel):
    modified: datetime
