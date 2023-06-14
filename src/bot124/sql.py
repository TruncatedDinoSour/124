#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""sql wrapper for sqlalchemy"""

import typing
from dataclasses import dataclass

import sqlalchemy  # type: ignore
from sqlalchemy.orm import Session, declarative_base  # type: ignore

__all__: tuple[str] = ("SQLiteDB",)


@dataclass
class SQLiteDB:
    engine: sqlalchemy.engine.base.Engine
    base: typing.Any
    session: Session

    __slots__: tuple[str, ...] = (
        "engine",
        "base",
        "session",
    )

    def __init__(self, url: str) -> None:
        self.engine = sqlalchemy.create_engine(url)
        self.base = declarative_base()
        self.session = sqlalchemy.orm.Session(self.engine)  # type: ignore

    def table(self, cls: typing.Any) -> typing.Any:
        cls.__tablename__ = cls.__name__
        return type(cls.__name__, (dataclass(cls), self.base), {})  # type: ignore

    def init(self) -> None:
        self.base.metadata.create_all(self.engine)
        self.commit()

    def commit(self) -> None:
        self.session.commit()

    def add(self, what: typing.Any) -> None:
        try:
            self.session.add(what)
            self.commit()
        except Exception as e:
            self.session.rollback()
            raise e
