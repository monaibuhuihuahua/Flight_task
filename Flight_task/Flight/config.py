class Config:
    username = "root"
    password = "123456"
    host = "localhost"
    port = "3306"
    database = "db_flight"
    db_url = f"mysql+pymysql://{username}:{password}@{host}:{port}/{database}?charset=utf8mb4"
    SQLALCHEMY_DATABASE_URI = db_url
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    SQLALCHEMY_ECHO = True
