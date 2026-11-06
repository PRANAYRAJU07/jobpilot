import pytest
from playwright.sync_api import sync_playwright

def test_simple_submission():
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page()
        page.goto("http://mock_site:8002/simple")
        
        page.fill("input[name='first_name']", "Test")
        page.fill("input[name='last_name']", "User")
        page.fill("input[name='email']", "test@test.com")
        page.click("button[type='submit']")
        
        assert "Application Submitted" in page.content()
        browser.close()
