"""
Configuration for frontend integration
"""
from pydantic import Field
from pydantic_settings import BaseSettings

NEXT_PUBLIC_BACKEND_URL="https://065270077bf7.ngrok-free.app"

class FrontendSettings(BaseSettings):
    """Frontend settings"""
    frontend_url: str = Field(default=NEXT_PUBLIC_BACKEND_URL)
    frontend_assets_path: str = Field(default="/source")

    model_config = {
        "env_prefix": "FRONTEND_"
    }


frontend_settings = FrontendSettings()
