import pytest

def pytest_configure(config):
    config.addinivalue_line(
        "markers", "live_openai: Mark test as requiring live OpenAI API credentials"
    )


@pytest.fixture(autouse=True)
def reset_workspace_db():
    from app.api.v1.workspaces import db
    db.reset()
