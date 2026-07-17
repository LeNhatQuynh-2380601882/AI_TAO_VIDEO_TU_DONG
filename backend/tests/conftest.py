import os
import sys
import shutil
import pytest
from fastapi.testclient import TestClient

# Thêm thư mục backend vào PYTHONPATH để pytest có thể import app
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Thiết lập biến môi trường test trước khi import app.config
os.environ["GEMINI_API_KEY"] = "mock_gemini_api_key"
os.environ["OPENAI_API_KEY"] = "mock_openai_api_key"

from app.config import settings
from app.main import app

# Định nghĩa thư mục tạm cho kiểm thử
TEST_TEMP_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "temp_test")

@pytest.fixture(scope="session", autouse=True)
def setup_test_environment():
    """Thiết lập môi trường kiểm thử: ghi đè TEMP_DIR và tạo thư mục tạm test."""
    original_temp_dir = settings.TEMP_DIR
    settings.TEMP_DIR = TEST_TEMP_DIR
    os.makedirs(TEST_TEMP_DIR, exist_ok=True)
    
    # Tạo thư mục uploads ảo trong temp_test
    os.makedirs(os.path.join(TEST_TEMP_DIR, "uploads"), exist_ok=True)
    
    yield
    
    # Dọn dẹp sau khi chạy xong tất cả các bài test
    settings.TEMP_DIR = original_temp_dir
    if os.path.exists(TEST_TEMP_DIR):
        shutil.rmtree(TEST_TEMP_DIR)

@pytest.fixture
def client():
    """Fixture cung cấp TestClient của FastAPI."""
    with TestClient(app) as test_client:
        yield test_client
