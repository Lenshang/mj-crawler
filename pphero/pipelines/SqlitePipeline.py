from pphero.model.DbPPHero import DbPPHero
from sqlalchemy import create_engine
from sqlalchemy.engine.mock import MockConnection
from sqlalchemy.orm import sessionmaker,Session
class SqlitePipeline(object):
    def __init__(self) -> None:
        engine=create_engine("sqlite:///pphero.db",pool_recycle=7200,connect_args={'check_same_thread': False})
        SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False)
        DbPPHero.metadata.create_all(engine)
        self.db=SessionLocal()

    def process_item(self, item, spider):
        dbItem=DbPPHero(**item)
        self.db.merge(dbItem)
        self.db.commit()