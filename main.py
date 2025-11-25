import asyncio
import subprocess
import sys
import time
from fastapi import FastAPI, Form, Request
from fastapi.responses import HTMLResponse, StreamingResponse
from typing import Optional

# --- 1. AUTO-INSTALL PLAYWRIGHT (Server Setup) ---
def install_playwright():
    try:
        import playwright
    except ImportError:
        print("Installing Playwright Library...")
        subprocess.check_call([sys.executable, "-m", "pip", "install", "playwright"])
        subprocess.check_call([sys.executable, "-m", "playwright", "install", "chromium"])

install_playwright()

from playwright.async_api import async_playwright

app = FastAPI()

# --- 2. HTML UI (Hacker Style) ---
HTML_TEMPLATE = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>FB Hunter Bot (Playwright)</title>
    <style>
        body { background-color: #0d1117; color: #c9d1d9; font-family: 'Courier New', monospace; padding: 20px; }
        .container { max-width: 800px; margin: 0 auto; }
        h1 { color: #58a6ff; border-bottom: 2px solid #30363d; padding-bottom: 10px; }
        .card { background: #161b22; padding: 20px; border-radius: 8px; border: 1px solid #30363d; margin-bottom: 20px; }
        label { display: block; margin-top: 10px; color: #8b949e; font-weight: bold; }
        input[type="text"], input[type="number"], textarea, input[type="password"] {
            width: 100%; background: #0d1117; border: 1px solid #30363d; color: #c9d1d9; padding: 10px; border-radius: 4px; margin-top: 5px; font-family: inherit;
        }
        input[type="submit"] {
            background: #238636; color: white; border: none; padding: 12px 24px; border-radius: 6px; cursor: pointer; font-size: 16px; margin-top: 20px; width: 100%;
        }
        input[type="submit"]:hover { background: #2ea043; }
        .log-box { background: #000; color: #0f0; padding: 15px; border-radius: 5px; height: 400px; overflow-y: auto; border: 1px solid #333; font-size: 14px; line-height: 1.5; }
        .log-entry { margin: 5px 0; border-bottom: 1px solid #111; padding-bottom: 2px; }
        .error { color: #ff5555; }
        .warn { color: #f1e05a; }
        .success { color: #0f0; font-weight: bold; }
        .info { color: #58a6ff; }
    </style>
</head>
<body>
<div class="container">
    <h1>🎯 FB Hunter Bot (Advanced)</h1>
    
    <div class="card">
        <form action="/run" method="post" target="log_frame">
            <label>🍪 Cookie String (Paste Full Header):</label>
            <textarea name="cookie_string" rows="3" placeholder="sb=...; c_user=..."></textarea>
            
            <label>🔐 6-Digit PIN (Optional):</label>
            <input type="password" name="pin_code" placeholder="888888" maxlength="6">

            <label>🔗 Chat URL:</label>
            <input type="text" name="chat_url" value="https://www.facebook.com/messages/t/61558458805222">

            <label>💬 Message:</label>
            <input type="text" name="message_text" value="Hello from Bot!">

            <div style="display: flex; gap: 20px; margin-top: 10px;">
                <div style="flex: 1;">
                    <label>⏱️ Delay (Seconds):</label>
                    <input type="number" name="delay" value="2">
                </div>
                <div style="flex: 1; display: flex; align-items: center; margin-top: 30px;">
                    <input type="checkbox" name="infinite" id="inf" style="width: auto; margin-right: 10px;">
                    <label for="inf" style="margin: 0; cursor: pointer;">Infinite Loop ♾️</label>
                </div>
            </div>

            <input type="submit" value="🚀 START ATTACK">
        </form>
    </div>

    <div class="card">
        <h3>📟 Live Console Logs</h3>
        <!-- iframe use kar rahe hain taaki main page refresh na ho -->
        <iframe name="log_frame" style="width: 100%; height: 450px; background: #000; border: none;"></iframe>
    </div>
</div>
</body>
</html>
"""

# --- 3. HELPER LOGIC ---
def parse_cookies(cookie_string):
    cookies = []
    try:
        parts = cookie_string.split(';')
        for part in parts:
            if '=' in part:
                name, value = part.strip().split('=', 1)
                cookies.append({
                    'name': name,
                    'value': value,
                    'domain': '.facebook.com',
                    'path': '/'
                })
    except:
        pass
    return cookies

# --- 4. THE CORE BOT LOGIC (Generator) ---
async def bot_logic_generator(cookie_string, chat_url, message_text, delay, infinite, pin_code):
    # CSS for the Iframe Logs
    yield """<style>
        body { background: #000; color: #0f0; font-family: monospace; padding: 10px; }
        .l { margin: 2px 0; } .e { color: red; } .s { color: cyan; font-weight: bold; } .w { color: yellow; }
    </style>"""
    
    yield f'<div class="l">🚀 Initializing Playwright Engine...</div>'
    
    async with async_playwright() as p:
        # Launch Browser (Headless=True for Server)
        browser = await p.chromium.launch(headless=True, args=['--no-sandbox', '--disable-setuid-sandbox'])
        context = await browser.new_context(
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/110.0.0.0 Safari/537.36"
        )
        
        # Add Cookies
        cookies = parse_cookies(cookie_string)
        if cookies:
            await context.add_cookies(cookies)
            yield f'<div class="l">🍪 {len(cookies)} Cookies Injected successfully.</div>'
        else:
            yield f'<div class="l e">❌ No Valid Cookies Found!</div>'
            return

        page = await context.new_page()
        
        # 1. Open Facebook
        yield f'<div class="l">🌐 Connecting to Facebook...</div>'
        try:
            await page.goto("https://www.facebook.com", timeout=60000)
        except Exception as e:
            yield f'<div class="l e">❌ Network Error: {e}</div>'

        # 2. Open Chat
        yield f'<div class="l">💬 Opening Chat URL...</div>'
        await page.goto(chat_url, timeout=60000)
        await page.wait_for_timeout(5000)

        # --- HUNTER FUNCTION (POPUP BYPASS) ---
        async def hunt_and_kill():
            # Try 1: Continue Button (Blue)
            # Use 'evaluate' for Force Click (JavaScript)
            clicked = await page.evaluate("""() => {
                let found = false;
                // Target: Continue Button
                let btns = document.querySelectorAll('div[role="button"] span');
                for (let b of btns) {
                    if (b.innerText.includes("Continue") || b.innerText.includes("restore")) {
                        b.closest('div[role="button"]').click();
                        found = true;
                    }
                }
                // Target: X Button
                let close = document.querySelector('div[aria-label="Close"]');
                if (close) { close.click(); found = true; }
                
                return found;
            }""")
            if clicked:
                yield f'<div class="l w">⚔️ Hunter: Smashed a Popup/Button!</div>'
                await page.wait_for_timeout(2000)

        # --- PIN FUNCTION ---
        if pin_code:
            yield f'<div class="l">🔐 Checking for PIN Screen...</div>'
            try:
                # Check for PIN inputs
                inputs = await page.locator("input[type='tel']").all()
                if not inputs:
                    inputs = await page.locator("input[type='password']").all()
                
                if len(inputs) >= 6:
                    yield f'<div class="l w">⚠️ PIN Lock Detected! Entering {pin_code}...</div>'
                    for i in range(6):
                        await inputs[i].fill(pin_code[i])
                        await page.wait_for_timeout(200)
                    yield f'<div class="l s">🔓 PIN Entered. Waiting for unlock...</div>'
                    await page.wait_for_timeout(5000)
            except Exception as e:
                yield f'<div class="l e">PIN Error: {str(e)}</div>'

        # --- MAIN LOOP ---
        count = 0
        keep_running = True
        
        while keep_running:
            # 1. Run Hunter (Clear Path)
            await hunt_and_kill()
            
            # 2. Find Message Box (Aggressive)
            box = None
            try:
                # Playwright selectors are powerful
                box = page.locator('div[aria-label="Message"]').first
                if not await box.is_visible():
                     box = page.locator('div[contenteditable="true"]').first
                
                if await box.is_visible():
                    # Focus and Type
                    await box.click(force=True) # Force click bypasses overlays
                    await box.fill(message_text)
                    await page.keyboard.press("Enter")
                    
                    count += 1
                    yield f'<div class="l s">✅ Message Sent: {count}</div><script>window.scrollTo(0,document.body.scrollHeight);</script>'
                    
                    if not infinite:
                        keep_running = False
                    else:
                        await page.wait_for_timeout(delay * 1000)
                else:
                    yield f'<div class="l e">❌ Message Box Not Found (Retrying...)</div>'
                    await page.screenshot(path="debug.png") # Optional debug
                    await page.wait_for_timeout(3000)
                    
            except Exception as e:
                yield f'<div class="l e">⚠️ Error: {str(e)}</div>'
                await page.wait_for_timeout(2000)

        yield f'<div class="l">🏁 Task Completed. Closing Browser.</div>'
        await browser.close()

# --- 5. ROUTES ---

@app.get("/", response_class=HTMLResponse)
def index():
    return HTML_TEMPLATE

@app.post("/run")
async def run_bot_route(
    cookie_string: str = Form(...),
    chat_url: str = Form(...),
    message_text: str = Form(...),
    delay: int = Form(2),
    infinite: Optional[str] = Form(None),
    pin_code: Optional[str] = Form(None)
):
    is_infinite = True if infinite == "on" else False
    
    # StreamingResponse wapis karte hain taaki LIVE logs dikhein
    return StreamingResponse(
        bot_logic_generator(cookie_string, chat_url, message_text, delay, is_infinite, pin_code),
        media_type="text/html"
    )

if __name__ == "__main__":
    import uvicorn
    # 0.0.0.0 is important for Render/Heroku/Cloud deployment
    uvicorn.run(app, host="0.0.0.0", port=8000)
        
