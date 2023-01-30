# coding: utf-8
"""
Created on January 20th, 2023
@title: Balth App
@version: 2.0.1
@author: Balthazar Méhus
@society: CentraleSupélec
@abstract: Python PDF extraction and storage - Database model.
"""
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from sqlalchemy import create_engine, Column, String, DateTime
from sqlalchemy.sql import func

# Config SQLAlchemy to store in a database
__DB_NAME = 'storage/db/pdf_infos.db'
engine = create_engine('sqlite:///' + __DB_NAME, echo=True)
Session = sessionmaker(bind=engine)
session = Session()
Base = declarative_base()

default_value: str = 'default'


class PdfData(Base):
    # Create the pdf metadata model
    __tablename__ = 'metadata'
    id = Column(String(255), primary_key=True)
    data = Column(String(), default=default_value, nullable=False)
    name = Column(String(255), default=default_value, nullable=False)
    link = Column(String(), default=default_value, nullable=False)
    task_id = Column(String(255), default=default_value, nullable=False)
    task_state = Column(String(255), default='PENDING', nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())


Base.metadata.create_all(engine)
