import os
import urllib.parse
from dotenv import load_dotenv

class DBClient:
    def __init__(self, env_file: str = ".env"):
        # Load env variables
        load_dotenv(env_file)

        self.user = os.getenv("DB_USER")
        self.password = os.getenv("DB_PASSWORD")
        self.host = os.getenv("DB_HOST")
        self.port = os.getenv("DB_PORT")
        self.database = os.getenv("DB_NAME")
        self.db_type = os.getenv("DB_TYPE")

        if not all([self.user, self.password, self.host, self.port, self.database, self.db_type]):
            raise ValueError("One or more required database environment variables are missing")

    def get_connection_uri(self) -> str:
        pwd = urllib.parse.quote_plus(self.password)

        if self.db_type.lower() == "mssql":
            return (
                f"mssql+pyodbc://{self.user}:{pwd}@{self.host},{self.port}/{self.database}"
                "?driver=ODBC+Driver+18+for+SQL+Server&encrypt=no"
            )

        raise NotImplementedError(f"Database type '{self.db_type}' is not supported yet.")
__all__ = ["DBClient"]
