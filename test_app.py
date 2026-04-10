import pytest
from app import app, init_db
import os

@pytest.fixture
def client():
    app.config['TESTING'] = True
    app.config['DATABASE'] = 'test_urls.db'
    with app.test_client() as client:
        init_db()
        yield client
    if os.path.exists('test_urls.db'):
        os.remove('test_urls.db')

def test_shorten_success(client):
    res = client.post('/shorten', json={"url": "https://example.com"})
    assert res.status_code in [200, 201]
    data = res.get_json()
    assert "short_url" in data

def test_redirect_success(client):
    client.post('/shorten', json={"url": "https://redirect-test.com"})
    res_shorten = client.post('/shorten', json={"url": "https://redirect-test.com"})
    code = res_shorten.get_json()["short_url"].split("/")[-1]
    res_redirect = client.get(f'/{code}', follow_redirects=False)
    assert res_redirect.status_code == 302
    assert "https://redirect-test.com" in res_redirect.headers["Location"]

def test_invalid_input(client):
    res = client.post('/shorten', json={})
    assert res.status_code == 400
    assert "error" in res.get_json()