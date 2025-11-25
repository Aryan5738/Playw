import asyncio
from fastapi import FastAPI, Form
from fastapi.responses import HTMLResponse
from playwright.async_api import async_playwright

app = FastAPI()

COOKIE_STRING_DEFAULT = ""
CHAT_URL_DEFAULT = "https://www.facebook.com/messages/t/61558458805222"
MESSAGE_TEXT_DEFAULT = "Hello from Bot!"
DELAY_DEFAULT = 2
INFINITE_DEFAULT = False

HTML_PAGE = """
<!DOCTYPE html>
<html>
<head>
    <title>FB Auto Sender</title>
</head>
<body>
<h1>Facebook Auto Sender</h1>
<form method="post">
<label>Cookie String:</label><br>
<textarea name="cookie_string" rows="4" cols="50">{cookie}</textarea><br><br>
<label>Chat URL:</label><br>
<input type="text" name="chat_url" size="50" value="{chat_url}"/><br><br>
<label>Message Text:</label><br>
<input type="text" name="message_text" size="50" value="{message_text}"/><br><br>
<label>Infinite Mode:</label>
<input type="checkbox" name="infinite" {infinite}/><br><br>
<label>Delay (seconds):</label>
<input type="number" name="delay" value="{delay}"/><br><br>
<input type="submit" value="Start Sending"/>
</form>
<h2>Log:</h2>
<pre>{log}</pre>
</body>
</html>
"""

def parse_cookies(cookie_string):
    cookies = []
    for item in cookie_string.split(";"):
        if "=" in item:
            name, value = item.strip().split("=", 1)
            cookies.append({"name": name, "value": value, "domain": ".facebook.com", "path": "/"})
    return cookies

async def run_bot(cookie_string, chat_url, message_text, delay, infinite, log_messages):
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        context = await browser.new_context()
        page = await context.new_page()

        log_messages.append("Opening Facebook...")
        await page.goto("https://www.facebook.com")
        log_messages.append("Injecting cookies...")
        await context.add_cookies(parse_cookies(cookie_string))
        log_messages.append("Opening chat...")
        await page.goto(chat_url)
        await page.wait_for_timeout(7000)

        count = 0
        running = True if infinite else False
        while True if infinite else running:
            try:
                msg_box = await page.wait_for_selector("div[aria-label='Message']", timeout=5000)
                await msg_box.click()
                await msg_box.type(message_text)
                await msg_box.press("Enter")
                count += 1
                log_messages.append(f"Sent: {count}")
                await page.wait_for_timeout(delay * 1000)
                if not infinite:
                    break
            except Exception as e:
                log_messages.append(f"Error: {e}")
                await page.wait_for_timeout(2000)
        await browser.close()
        log_messages.append("Done!")

@app.get("/", response_class=HTMLResponse)
def home():
    return HTML_PAGE.format(cookie=COOKIE_STRING_DEFAULT,
                            chat_url=CHAT_URL_DEFAULT,
                            message_text=MESSAGE_TEXT_DEFAULT,
                            infinite="",
                            delay=DELAY_DEFAULT,
                            log="")

@app.post("/", response_class=HTMLResponse)
async def send_message(cookie_string: str = Form(...),
                       chat_url: str = Form(...),
                       message_text: str = Form(...),
                       infinite: str = Form(None),
                       delay: int = Form(DELAY_DEFAULT)):
    log_messages = []
    is_infinite = True if infinite == "on" else False
    await run_bot(cookie_string, chat_url, message_text, delay, is_infinite, log_messages)
    return HTML_PAGE.format(cookie=cookie_string,
                            chat_url=chat_url,
                            message_text=message_text,
                            infinite="checked" if is_infinite else "",
                            delay=delay,
                            log="\n".join(log_messages))

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
