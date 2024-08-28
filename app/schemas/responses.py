import datetime

from pydantic import BaseModel, ConfigDict


class BaseResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)


# class BoxResponse(BaseResponse):
#     token_type: str
#     access_token: str
#     expires_at: int
#     issued_at: int
#     refresh_token: str
#     refresh_token_expires_at: int
#     refresh_token_issued_at: int


class BoxResponse(BaseModel):
    id: int
    floor: int
    room: int
    rack: int
    shelf: int
    machine_id: int

    class Config:
        from_attributes = True


class PacketResponse(BaseModel):
    id: int
    rfid: str
    packet_type: str
    quantity: int
    product_id: str
    box_id: int

    class Config:
        from_attributes = True


class ProductModel(BaseModel):
    id: str
    material_desc: str
    maker_desc: str
    part_no: str

    class Config:
        from_attributes = True


class JobResponse(BaseModel):
    due: datetime.datetime
    interval: int
    id: str
    description: str
    status: str
    pic: int

    class Config:
        from_attributes = True


class ProductResponse(BaseModel):
    rob: int
    product: ProductModel
    rfid: str

    class Config:
        from_attributes = True
