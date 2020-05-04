import os

from sqlalchemy import create_engine
from sqlalchemy.orm import scoped_session, sessionmaker


# Set up database
engine = create_engine(os.getenv("DATABASE_URL"))
db = scoped_session(sessionmaker(bind=engine))

def main():
     users_table= db.execute("CREATE TABLE Books (book_id SERIAL NOT	NULL,isbn VARCHAR PRIMARY KEY NOT NULL,title VARCHAR NOT NULL,author VARCHAR NOT NULL,year INTEGER NOT NULL)")
     db.commit()

if __name__ == "__main__":
    main()
