"""
Configuration for frontend integration
"""
from pydantic import Field
from pydantic_settings import BaseSettings
from app.core.config import settings

class FrontendSettings(BaseSettings):
    """Frontend settings"""
    frontend_url: str = Field(default=settings.NEXT_PUBLIC_BACKEND_URL)
    frontend_assets_path: str = Field(default="/source")

    model_config = {
        "env_prefix": "FRONTEND_"
    }


frontend_settings = FrontendSettings()
