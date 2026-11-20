from sqlalchemy import create_engine, Column, Integer, String, Float
from sqlalchemy.orm import declarative_base
from config import Config

# 创建数据库连接引擎
DATABASE_URL = (
    f"postgresql://{Config.POSTGRES_USER}:{Config.POSTGRES_PASSWORD}"
    f"@{Config.POSTGRES_HOST}:{Config.POSTGRES_PORT}/{Config.POSTGRES_DB}"
)
engine = create_engine(DATABASE_URL)

Base = declarative_base()

class SubwayPosition(Base):
    __tablename__ = "subway_positions"

    id = Column(Integer, primary_key=True, autoincrement=True)
    trip_id = Column(String)
    route_id = Column(String)
    direction_id = Column(Integer)
    stop_id = Column(String)
    latitude = Column(Float)
    longitude = Column(Float)
    bearing = Column(Float)
    current_status = Column(String)
    timestamp = Column(Integer)

if __name__ == "__main__":
    Base.metadata.create_all(engine)
    print("Database and table created successfully!")