import os
import datetime
import sqlite3
from pathlib import Path
from pydantic import BaseModel, field_validator
from contextlib import contextmanager

class Newsletter(BaseModel):
    content: str
    start_date: str
    end_date: str
    date_sent: str
    

class Paper(BaseModel):
    title: str
    abstract: str
    date: str
    date_run: str
    score: float | int
    rationale: str
    related: bool
    cosine_similarity: float
    url: str
    embedding_model: str

    @field_validator('score')
    @classmethod
    def score_range(cls, v):
        if not 0 <= v <= 10:
            raise ValueError('Score must be between 0 and 10')
        return v

class PaperDatabase:
    """
    PaperDatabase class for handling paper data storage and retrieval.

    This class provides methods to interact with a SQLite database for storing
    and retrieving paper information. It includes functionality to insert new
    papers, retrieve papers based on various criteria, and manage the database
    connection.

    Attributes:
        db_path (Path): The path to the SQLite database file.
        conn (sqlite3.Connection): The database connection object.

    Methods:
        __init__(db_path: str = "papers.db"):
            Initialize the PaperDatabase instance.
        
        _ensure_path_exists():
            Ensure the database directory exists.
        
        get_cursor():
            Context manager that yields a database cursor and handles transactions.
        
        _create_table():
            Create the papers table if it doesn't exist.
        
        _create_connection():
            Creates a connection to the papers database.

        insert_paper(paper: Paper):
            Insert a new paper into the database.
        
    """
    def __init__(self, db_path: str = "papers.db"):
        self.db_path = Path(db_path)
        self._ensure_path_exists()
        self.conn = self._create_connection()
        self._create_table()

    def _create_connection(self):
        return sqlite3.connect(str(self.db_path))
    
    def _ensure_path_exists(self):
        self.db_path.parent.mkdir(parents=True, exist_ok=True)

    @contextmanager
    def get_cursor(self):
        with self._create_connection() as conn:
            yield conn.cursor()

    def _create_table(self):
        with self.get_cursor() as cursor:
            cursor.execute('''CREATE TABLE IF NOT EXISTS papers
                              (id INTEGER PRIMARY KEY AUTOINCREMENT,
                               title TEXT NOT NULL,
                               abstract TEXT NOT NULL,
                               date TEXT NOT NULL,
                               date_run TEXT NOT NULL,
                               score REAL NOT NULL,
                               rationale TEXT NOT NULL,
                               related BOOLEAN NOT NULL,
                               cosine_similarity REAL NOT NULL,
                               url TEXT NOT NULL,
                               embedding_model TEXT NOT NULL
                            )''')
            cursor.execute('''CREATE TABLE IF NOT EXISTS newsletters
                              (id INTEGER PRIMARY KEY AUTOINCREMENT,
                               content TEXT NOT NULL,
                               start_date TEXT NOT NULL,
                               end_date TEXT NOT NULL,
                               date_sent TEXT NOT NULL
                            )''')
    
    def insert_paper(self, paper: Paper):
        """
        Insert a new paper into the database.

        Args:
            paper (Paper): A Paper object containing the paper's information.

        Raises:
            ValueError: If any required field in the Paper object is missing or invalid.

        Note:
            This method uses a context manager to handle database transactions,
            ensuring that the connection is properly committed or rolled back
            in case of an error.
        """

        # Validate required fields
        required_fields = ['title', 'abstract', 'date', 'date_run', 
                           'score', 'rationale', 'related', 'cosine_similarity', 'url', 'embedding_model']
        for field in required_fields:
            if not hasattr(paper, field) or getattr(paper, field) is None:
                raise ValueError(f"Paper object is missing required field: {field}")

        # Validate data types
        if not isinstance(paper.score, (int, float)):
            raise ValueError("Score must be a number")
        if not isinstance(paper.related, bool):
            raise ValueError("Related must be a boolean")
        if not isinstance(paper.cosine_similarity, float):
            raise ValueError("Cosine similarity must be a float")

        # Validate date formats
        try:
            datetime.datetime.strptime(paper.date, '%Y-%m-%d')
            datetime.datetime.strptime(paper.date_run, '%Y-%m-%d')
        except ValueError:
            raise ValueError("Dates must be in 'YYYY-MM-DD' format")
        with self.get_cursor() as cursor:
            cursor.execute('''INSERT INTO papers (title, abstract, date, date_run, score, rationale, related, cosine_similarity, url, embedding_model)
                              VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)''',
                           (paper.title, paper.abstract, paper.date, paper.date_run, 
                            paper.score, paper.rationale, paper.related, paper.cosine_similarity, 
                            paper.url, paper.embedding_model))
    
    def insert_newsletter(self, newsletter: Newsletter):
        """
        Insert a new newsletter into the database.

        Args:
            newsletter (Newsletter): A Newsletter object containing the newsletter's information.

        Raises:
            ValueError: If any required field in the Newsletter object is missing or invalid.

        Note:
            This method uses a context manager to handle database transactions,
            ensuring that the connection is properly committed or rolled back
            in case of an error.
        """

        # Validate required fields
        required_fields = ['content', 'start_date', 'end_date', 'date_sent']
        for field in required_fields:
            if not hasattr(newsletter, field) or getattr(newsletter, field) is None:
                raise ValueError(f"Newsletter object is missing required field: {field}")

        # Validate date formats
        try:
            datetime.datetime.strptime(newsletter.start_date, '%Y-%m-%d')
            datetime.datetime.strptime(newsletter.end_date, '%Y-%m-%d')
            datetime.datetime.strptime(newsletter.date_sent, '%Y-%m-%d')
        except ValueError:
            raise ValueError("Dates must be in 'YYYY-MM-DD' format")

        # Validate that start_date is not after end_date
        if newsletter.start_date > newsletter.end_date:
            raise ValueError("start_date cannot be after end_date")
        with self.get_cursor() as cursor:
            cursor.execute('''INSERT INTO newsletters (content, start_date, end_date, date_sent)
                              VALUES (?, ?, ?, ?)''',
                           (newsletter.content, newsletter.start_date, newsletter.end_date, newsletter.date_sent))

