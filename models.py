from sqlalchemy import create_engine, Column, Integer, String
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import scoped_session, sessionmaker

DB_URI = 'sqlite:///test.db'

Session = sessionmaker(autocommit=False,
                       autoflush=False,
                       bind=create_engine(DB_URI))
session = scoped_session(Session)
Base = declarative_base()


# Note Model
class Ad(Base):
    __tablename__ = 'advertisements'
    id = Column(Integer, primary_key=True)
    title = Column(String(50))
    description = Column(String(50))
    created_at = Column(String(50))
    author = Column(String(50))

    def __init__(self, title, description, created_at, author):
        self.title = title
        self.description = description
        self.created_at = created_at
        self.author = author

    @classmethod
    def from_json(cls, data):
        return cls(**data)

    def to_json(self):
        to_serialize = ['id', 'title', 'description', 'created_at', 'author']
        d = {}
        for attr_name in to_serialize:
            d[attr_name] = getattr(self, attr_name)
        return d


# creates database
if __name__ == "__main__":
    engine = create_engine(DB_URI)
    Base.metadata.drop_all(engine)
    Base.metadata.create_all(engine)
