import pytest
from playwright.sync_api import sync_playwright

def test_otp_detection():
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page()
        page.goto("http://mock_site:8002/with-otp")
        
        from app.detection import BlockerDetector
        detector = BlockerDetector(page)
        assert detector.detect_blockers() == "OTP_REQUIRED"
        browser.close()

def test_captcha_detection():
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page()
        page.goto("http://mock_site:8002/with-captcha")
        
        from app.detection import BlockerDetector
        detector = BlockerDetector(page)
        assert detector.detect_blockers() == "CAPTCHA_REQUIRED"
        browser.close()
