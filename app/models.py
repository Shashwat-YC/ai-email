"""
SQL Alchemy models declaration.
https://docs.sqlalchemy.org/en/14/orm/declarative_styles.html#example-two-dataclasses-with-declarative-table
Dataclass style for powerful autocompletion support.

https://alembic.sqlalchemy.org/en/latest/tutorial.html
Note, it is used by alembic migrations logic, see `alembic/env.py`

Alembic shortcuts:
# create migration
alembic revision --autogenerate -m "migration_name"

# apply all migrations
alembic upgrade head
"""

import datetime

from sqlalchemy import ForeignKey
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship


class Base(DeclarativeBase):
    pass


class Campaign(Base):
    __tablename__ = "campaign"
    campaign_id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    campaign_threshold: Mapped[int]
    company_name: Mapped[str]
    company_url: Mapped[str]
    products: Mapped[str] = mapped_column(nullable=True)
    campaign_timeline: Mapped[datetime.datetime]
    completed: Mapped[bool]


class User(Base):
    __tablename__ = "user"

    user_id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)  # id
    name: Mapped[str]
    email: Mapped[str]
    age: Mapped[str]
    gender: Mapped[str]
    industry: Mapped[str]
    company: Mapped[str]
    division: Mapped[str]
    other_details: Mapped[str]


class CampaignUser(Base):
    __tablename__ = "campaign_user"

    unique_id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("user.user_id"))
    campaign_id: Mapped[int] = mapped_column(ForeignKey("campaign.campaign_id"))
    sent: Mapped[str] = mapped_column(nullable=True)


# class Link(Base):
#     __tablename__ = "link_tracking"
#
#     link_id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
#     redirect_url: Mapped[str]


class LinkLog(Base):
    __tablename__ = "link_log"

    click_id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    click_time: Mapped[datetime.datetime]
    campaign_id: Mapped[int] = mapped_column(ForeignKey("campaign.campaign_id"))
    user_id: Mapped[int] = mapped_column(ForeignKey("user.user_id"))


class OpenLog(Base):
    __tablename__ = "open_log"

    open_id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    open_time: Mapped[datetime.datetime]
    campaign_user_id: Mapped[int] = mapped_column(ForeignKey("campaign_user.unique_id"))
    # campaign_id: Mapped[int] = mapped_column(ForeignKey("campaign.campaign_id"))
