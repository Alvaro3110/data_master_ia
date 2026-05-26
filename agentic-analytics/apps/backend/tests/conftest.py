import pytest

@pytest.fixture(autouse=True)
def reset_workspace_db():
    from app.api.v1.workspaces import db
    db.reset()
