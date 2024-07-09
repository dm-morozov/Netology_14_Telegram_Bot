import psycopg2
from sqlalchemy import create_engine, Column, Integer, String, Text, Date, ForeignKey
from sqlalchemy.orm import declarative_base, relationship, sessionmaker
from models import Base, create_tables, drop_tables, fill_words


DSN = 'postgresql://postgres:20145@localhost:5432/learning_English'
engine = create_engine(DSN)

if __name__ == '__main__':

    drop_tables(engine)

    create_tables(engine)

    Session = sessionmaker(bind=engine)
    session = Session()

    # fill_words(session)

    session.close()

