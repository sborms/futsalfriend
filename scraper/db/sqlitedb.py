import typing as tp
from contextlib import contextmanager

import pandas as pd
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from scraper.db.tables import Base


class SQLiteDB:
    def __init__(self, path2db: str, table_classes: tp.Type[Base] = Base):
        """Sets up a connection to a SQLite database."""
        self.path2db = path2db
        self.table_classes = table_classes
        self.engine = create_engine(f"sqlite:///{self.path2db}")
        self.session = sessionmaker(bind=self.engine)()

    @contextmanager
    def session_scope(self):
        """Provides a transactional scope around a series of operations."""
        session = self.session
        try:
            yield session
            session.commit()
        except Exception:
            session.rollback()
            raise

    @contextmanager
    def cursor(self):
        """Provides a cursor to execute commands in the database."""
        connection = self.engine.raw_connection()
        cursor = connection.cursor()
        try:
            yield cursor
            connection.commit()
        except Exception:
            raise

    def create_db(self):
        """Creates the database and tables based on self.table_classes."""
        self.table_classes.metadata.create_all(self.engine, checkfirst=True)

    def drop_tables(self):
        """Drops all tables in the database based on self.table_classes."""
        self.table_classes.metadata.drop_all(self.engine)

    def insert_table(self, df: pd.DataFrame, table_class: tp.Type[Base]):
        """Inserts a table from a pandas DataFrame row-by-row into the database."""
        rows = [row.to_dict() for _, row in df.iterrows()]
        with self.session_scope() as session:
            for row in rows:
                db_row = table_class(**row)
                session.add(db_row)

    def get_table(self, table_class: tp.Type[Base]):
        """Gets a raw table from the database."""
        with self.session_scope() as session:
            return session.query(table_class).all()

    def query(self, query_str: str):
        """Executes a query and returns the results as a pandas DataFrame."""
        with self.cursor() as cursor:
            cursor.execute(query_str)
            df = pd.DataFrame(cursor.fetchall())
        return df  # TODO: extract and add headers

    def get_table_classes(self):
        """Gets the tables from the database."""
        return self.table_classes.metadata.sorted_tables

    def close(self):
        """Shuts down database connection."""
        self.session.close()
        self.engine.dispose()
