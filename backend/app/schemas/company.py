"""
Component: Backend -> API Layer -> Pydantic schema
Belongs to: the response_model for GET /api/companies and GET /api/companies/{symbol}
(app/api/routes/companies.py).
Purpose: the public JSON shape of a Company row — decouples the API's response
contract from the ORM model (via from_attributes) so DB columns can change without
automatically changing the API surface.
"""

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
