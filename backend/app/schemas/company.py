from pydantic import BaseModel, ConfigDict


class CompanyOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    symbol: str
    name: str
    sector: str | None = None
    industry: str | None = None
    market_cap: int | None = None
    exchange: str
    currency: str | None = None
    current_price: float | None = None
