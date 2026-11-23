"""Visits the demo site in a real browser so Streamlit Community Cloud counts a visitor.

Community Cloud puts an app to sleep after 12 hours without traffic. A plain web request does not
count as a visit, so this opens the page in headless Chromium, presses the wake button if the app
is asleep, and waits until the app has drawn its banner. It exits with an error if the app never
appears, so a failed run shows up in the repository's Actions tab.
"""
from playwright.sync_api import sync_playwright

URL = "https://where-to-live-demo.streamlit.app/"

with sync_playwright() as p:
    browser = p.chromium.launch()
    page = browser.new_page()
    page.goto(URL, wait_until="domcontentloaded", timeout=120_000)
    page.wait_for_timeout(8_000)
    wake = page.get_by_role("button", name="Yes, get this app back up!")
    if wake.count() > 0:
        print("The app was asleep. Pressing the wake button.")
        wake.first.click()
    app = page.frame_locator('iframe[title="streamlitApp"]')
    app.get_by_text("THE GRADUATE TRAIL").first.wait_for(timeout=300_000)
    page.wait_for_timeout(15_000)
    print("The app is awake.")
    browser.close()
