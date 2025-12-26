import asyncio
from playwright.async_api import async_playwright

MF_URL_LOGIN = "https://moneyforward.com/sign_in"
AUTH_FILE = "mf_auth.json"


async def main():
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=False)
        context = await browser.new_context()
        page = await context.new_page()

        await page.goto(MF_URL_LOGIN)

        input("Press Enter continue...")

        await context.storage_state(path=AUTH_FILE)

        await browser.close()


if __name__ == "__main__":
    asyncio.run(main())
