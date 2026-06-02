from pydantic import BaseModel


class BrokerStatusUpdate(BaseModel):
    is_active: bool
