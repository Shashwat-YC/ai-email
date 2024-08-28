import datetime
from enum import Enum

from fastapi import UploadFile
from pydantic import BaseModel


class BaseRequest(BaseModel):
    # may define additional fields or config shared across requests
    pass


class Products(BaseModel):
    product_name: str
    product_url: str
    product_price: str
    product_image_url: str


class CampaignCreate(BaseModel):
    company_name: str
    company_url: str
    products: list[Products]
    campaign_timeline: datetime.datetime
    threshold: int

    class Config:
        from_attributes = True
        extra = "ignore"
