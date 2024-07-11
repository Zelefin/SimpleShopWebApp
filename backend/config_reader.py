from pydantic_settings import BaseSettings
from sqlalchemy.engine.url import URL


class Web(BaseSettings):
    domain: str
    host: str
    port: int


class Bot(BaseSettings):
    token: str
    use_webhook: bool
    use_redis: bool
    webhook_path: str
    webhook_url: str
    webhook_secret: str


class Admin(BaseSettings):
    id: int


class Postgres(BaseSettings):
    host: str
    port: int
    database: str
    user: str
    password: str

    def construct_sqlalchemy_url(self) -> str:
        """
        Constructs and returns a SQLAlchemy URL for this database configuration.
        """
        uri = URL.create(
            drivername=f"postgresql+asyncpg",
            username=self.user,
            password=self.password,
            host=self.host,
            port=self.port,
            database=self.database,
        )
        return uri.render_as_string(hide_password=False)


class Redis(BaseSettings):
    host: str
    port: int
    db: int

    def make_connection_string(self) -> str:
        return f"redis://{self.host}:{self.port}/{self.db}"


class Config(BaseSettings):
    web: Web
    bot: Bot
    admin: Admin
    postgres: Postgres
    redis: Redis

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        env_nested_delimiter = "__"


def load_config(env_file="../.env") -> Config:
    config = Config(_env_file=env_file)
    return config
