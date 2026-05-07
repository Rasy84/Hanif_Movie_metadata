"""Capture UI screenshots for documentation (requires: pip install playwright && playwright install chromium)."""
from __future__ import annotations

from pathlib import Path

from playwright.sync_api import sync_playwright

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "screenshots"


def main() -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    base = "http://127.0.0.1:5005"
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page(viewport={"width": 1280, "height": 900})
        page.goto(base, wait_until="load", timeout=120_000)
        page.screenshot(path=str(OUT / "01_home.png"), full_page=True)

        page.fill("#question", "Best comedy movie")
        page.get_by_role("button", name="Search & Ask").click()
        page.wait_for_selector("text=Retrieved movies", timeout=120_000)
        page.wait_for_timeout(500)
        page.screenshot(path=str(OUT / "02_search_best_comedy.png"), full_page=True)

        browser.close()


if __name__ == "__main__":
    main()
