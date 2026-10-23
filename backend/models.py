"""Pydantic request/response models for the Campus Customs API and agent."""

from __future__ import annotations

from pydantic import BaseModel, EmailStr, Field


class SignupRequest(BaseModel):
    first_name: str = Field(min_length=1, max_length=80)
    last_name: str = Field(min_length=1, max_length=80)
    email: EmailStr
    password: str = Field(min_length=6, max_length=200)
    confirm_password: str = Field(min_length=6, max_length=200)


class LoginRequest(BaseModel):
    email: EmailStr
    password: str = Field(min_length=1, max_length=200)


class UserOut(BaseModel):
    id: int
    first_name: str
    last_name: str
    name: str
    email: str


class AuthResponse(BaseModel):
    user: UserOut
    message: str


class ProductCard(BaseModel):
    """Structured product match for the front end to render as cards."""

    product_id: str
    name: str
    price: float
    garment_type: str
    short_description: str
    image_file_path: str
    colors: str = ""


class StockBySize(BaseModel):
    size: str
    quantity: int


class ProductInfo(BaseModel):
    product_id: str
    name: str
    description: str
    price: float
    garment_type: str
    colors: str
    image_file_path: str
    stock: list[StockBySize] = Field(default_factory=list)


class PageContext(BaseModel):
    path: str | None = None
    product_id: str | None = None
    product_name: str | None = None


class ChatRequest(BaseModel):
    message: str = Field(min_length=1, max_length=4000)
    user_id: int | None = None
    page: PageContext | None = None


class ChatResponse(BaseModel):
    reply: str
    products: list[ProductCard] = Field(default_factory=list)
    suggestions: list[str] = Field(default_factory=list)
    tool_events: list[dict] = Field(default_factory=list)


class ChatHistoryItem(BaseModel):
    role: str
    content: str
    products: list[ProductCard] = Field(default_factory=list)
    created_at: str | None = None
