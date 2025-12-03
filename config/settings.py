# Stub settings for config import

class Settings:
    def __init__(self):
        self.debug = True
        self.env = "development"
        self.database_url = "postgresql://postgres:postgres@localhost:5432/opendiscourse"

settings = Settings()
