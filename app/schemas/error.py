from pydantic import BaseModel


class ErrorResponse(BaseModel):
    status_code: int
    error: str
    message: str
    path: str
