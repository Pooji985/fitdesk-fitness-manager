from pydantic import BaseModel


class HealthCheckResponse(BaseModel):
    status: str
    project: str
    database: str
    version: str = "1.0.0"
