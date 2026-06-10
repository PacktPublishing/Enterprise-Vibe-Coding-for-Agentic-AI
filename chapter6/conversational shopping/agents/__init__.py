"""
Agent Registry — single import point for app.py.
"""

from .client import (                       # noqa: F401
    AZURE_OPENAI_ENDPOINT,
    DEPLOYMENT_NAME,
    IMAGE_DEPLOYMENT,
    IMAGES_DIR,
    credential,
    client,
    image_client,
    _loop,
    generate_product_image,
)

from . import shopping_assistant            # noqa: F401
