from sqlalchemy import String
from sqlalchemy.orm import Mapped, mapped_column
from app.core.database import Base

class Market(Base):
    __tablename__ = "markets"
    country_code: Mapped[str] = mapped_column(String(2), primary_key=True)
    country_name_zh: Mapped[str]
    country_name_en: Mapped[str]
    default_currency: Mapped[str] = mapped_column(String(3))
    is_enabled: Mapped[bool]
    rules_status: Mapped[str]
