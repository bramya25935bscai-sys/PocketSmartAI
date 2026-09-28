import io
import sys
from pathlib import Path

import pytest
from PIL import Image

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from pocketsmart.app import create_app  # noqa: E402


@pytest.fixture()
def app():
    application = create_app()
    application.config["TESTING"] = True
    return application


@pytest.fixture()
def client(app):
    return app.test_client()


@pytest.fixture()
def png_bytes():
    buf = io.BytesIO()
    img = Image.new("RGB", (80, 120), (210, 140, 160))
    img.save(buf, format="PNG")
    return buf.getvalue()
