"""Database client for connecting to multiple database types."""
import os
import urllib.parse
from typing import Optional
from dotenv import load_dotenv

from langchain_community.utilities import SQLDatabase

class DBClient:
    def __init__(self, env_file: str = ".env") -> None:
        """Initialize database client with environment configuration.
        
        Args:
            env_file: Path to environment file (default: .env)
            
        Raises:
            ValueError: If required environment variables are missing
        """
        load_dotenv(env_file)

        self.user: Optional[str] = os.getenv("DB_USER")
        self.password: Optional[str] = os.getenv("DB_PASSWORD")
        self.host: Optional[str] = os.getenv("DB_HOST")
        self.port: Optional[str] = os.getenv("DB_PORT")
        self.database: Optional[str] = os.getenv("DB_NAME")
        self.db_type: Optional[str] = os.getenv("DB_TYPE")

        if not all([self.user, self.password, self.host, self.port, self.database, self.db_type]):
            raise ValueError("One or more required database environment variables are missing")

    def get_connection_uri(self) -> str:
        """Generate database connection URI based on database type.
        
        Returns:
            Connection URI string for SQLAlchemy
            
        Raises:
            NotImplementedError: If database type is not supported
        """
        pwd = urllib.parse.quote_plus(self.password)
        db_type = self.db_type.lower()

        if db_type == "mssql":
            return (
                f"mssql+pyodbc://{self.user}:{pwd}@{self.host},{self.port}/{self.database}"
                "?driver=ODBC+Driver+18+for+SQL+Server&encrypt=no"
            )

        elif db_type == "postgres":
            return (
                f"postgresql+psycopg2://{self.user}:{pwd}@{self.host}:{self.port}/{self.database}"
            )

        elif db_type == "mysql":
            return (
                f"mysql+pymysql://{self.user}:{pwd}@{self.host}:{self.port}/{self.database}"
            )

        elif db_type == "oracle":
            return (
                f"oracle+cx_oracle://{self.user}:{pwd}@{self.host}:{self.port}/?service_name={self.database}"
            )

        else:
            raise NotImplementedError(f"Unsupported database type: {self.db_type}")
        
    def get_db(self) -> SQLDatabase:
        """Get SQLDatabase instance with proper error handling.
        
        Returns:
            SQLDatabase instance connected to configured database
            
        Raises:
            ConnectionError: If connection fails
        """
        try:
            uri = self.get_connection_uri()
            return SQLDatabase.from_uri(uri)
        except Exception as exp:
            raise ConnectionError(f"Failed to connect to database: {exp}") from exp

# Global singleton
db_client = DBClient()
