from sqlalchemy import Column, String, TIMESTAMP, text,func
from sqlalchemy.dialects.mysql import INTEGER
from sqlalchemy.ext.declarative import declarative_base

Base = declarative_base()
metadata = Base.metadata

class DbPPHero(Base):
    __tablename__ = 'prompt_hero'
    __table_args__ = {'comment': 'prompt_hero'}

    url = Column(String(255), primary_key=True)
    img_url = Column(String(255), nullable=False, server_default=text("''"))
    prompt_text = Column(String(255), nullable=False, server_default=text("''"))
    file_path = Column(String(255), nullable=False, server_default=text("''"))
    update_time = Column(TIMESTAMP, nullable=False, server_default=func.now(), onupdate=func.now())

