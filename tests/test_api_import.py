def test_api_imports():
    from api.main import app
    assert app is not None