from sqlalchemy import Boolean, Integer, String
from sqlalchemy.orm import Mapped, mapped_column

from app.db import Base
from app.models.base import TimestampMixin


class CompanySettings(TimestampMixin, Base):
    """Single-row table of company settings (spec section 5.1)."""

    __tablename__ = "company_settings"

    company_name: Mapped[str] = mapped_column(String(200), nullable=False)
    address: Mapped[str] = mapped_column(String(500), default="", nullable=False)
    cr_number: Mapped[str] = mapped_column(String(50), default="", nullable=False)
    vat_number: Mapped[str] = mapped_column(String(50), default="", nullable=False)
    vat_enabled: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    currency: Mapped[str] = mapped_column(String(3), default="OMR", nullable=False)
    currency_decimals: Mapped[int] = mapped_column(Integer, default=3, nullable=False)
    financial_year_start_month: Mapped[int] = mapped_column(Integer, default=1, nullable=False)
