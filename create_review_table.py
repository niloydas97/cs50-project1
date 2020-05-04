import os

from sqlalchemy import create_engine
from sqlalchemy.orm import scoped_session, sessionmaker



# Set up database
engine = create_engine(os.getenv("DATABASE_URL"))
db = scoped_session(sessionmaker(bind=engine))

def main():
    users_review= db.execute("CREATE TABLE reviews (id SERIAL  NOT NULL,user_id INTEGER PRIMARY KEY NOT NULL,book_id INTEGER NOT NULL, review VARCHAR, rating INTEGER UNIQUE NOT NULL)")
    db.commit()

if __name__ == "__main__":
    main()
