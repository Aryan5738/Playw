import asyncio
import subprocess
import sys
import os
from fastapi import FastAPI, Form
from fastapi.responses import HTMLResponse, StreamingResponse
from typing import Optional

# --- AUTO-INSTALL PLAYWRIGHT (Backup Logic) ---
# Waise hum Render Build Command me isse install karenge, par safety ke liye yahan bhi rakha hai
def install_playwright_internal():
    try:
        from playwright.async_api import async_playwright
    except ImportError:
        print("Installing Playwright internally...")
        subprocess.check_call([sys.executable, "-m", "pip", "install", "playwright"])
        subprocess.check_call([sys.executable, "-m", "playwright", "install", "chromium"])

install_playwright_internal()

from playwright.async_api import async_playwright

app = FastAPI()

# --- HACKER UI TEMPLATE ---
HTML_TEMPLATE = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>FB Hunter Bot</title>
    <style>
        body { background-color: #0d1117; color: #c9d1d9; font-family: 'Courier New', monospace; padding: 20px; }
        .container { max-width: 800px; margin: 0 auto; }
        h1 { color: #58a6ff; border-bottom: 2px solid #30363d; padding-bottom: 10px; }
        .card { background: #161b22; padding: 20px; border-radius: 8px; border: 1px solid #30363d; margin-bottom: 20px; }
        input[type="text"], input[type="number"], textarea, input[type="password"] {
            width: 100%; background: #0d1117; border: 1px solid #30363d; color: #c9d1d9; padding: 10px; border-radius: 4px; margin-top: 5px; 
        }
        input[type="submit"] {
            background: #238636; color: white; border: none; padding: 12px; border-radius: 6px; cursor: pointer; width: 100%; margin-top: 15px; font-weight: bold;
        }
        iframe { width: 100%; height: 500px; background: #000; border: 1px solid #333; margin-top: 10px; }
    </style>
</head>
<body>
<div class="container">
    <h1>🚀 FB Hunter Bot (Render Edition)</h1>
    <div class="card">
        <form action="/run" method="post" target="log_frame">
            <label>🍪 Cookie String:</label>
            <textarea name="cookie_string" rows="3" required></textarea>
            
            <label>🔐 PIN (Optional):</label>
            <input type="password" name="pin_code" maxlength="6">

            <label>🔗 Chat URL:</label>
            <input type="text" name="chat_url" value="https://www.facebook.com/messages/t/61558458805222">

            <label>💬 Message:</label>
            <input type="text" name="message_text" value="Hello from Bot!">

            <div style="display: flex; gap: 10px; margin-top: 10px;">
                <input type="number" name="delay" value="2" placeholder="Delay">
                <div style="display: flex; align-items: center;">
                    <input type="checkbox" name="infinite" id="inf">
                    <label for="inf" style="margin-left: 5px;">Infinite</label>
                </div>
            </div>
            <input type="submit" value="START ATTACK">
        </form>
    </div>
    <div class="card">
        <h3>📟 Live Logs</h3>
        <iframe name="log_frame"></iframe>
    </div>
</div>
</body>
</html>
"""

def parse_cookies(cookie_string):
    cookies = []
    try:
        parts = cookie_string.split(';')
        for part in parts:
            if '=' in part:
                name, value = part.strip().split('=', 1)
                cookies.append({'name': name, 'value': value, 'domain': '.facebook.com', 'path': '/'})
    except: pass
    return cookies

# --- BOT GENERATOR LOGIC ---
async def bot_logic(cookie_string, chat_url, message_text, delay, infinite, pin_code):
    yield """<style>body{background:#000;color:#0f0;font-family:monospace;padding:10px}.e{color:red}.s{color:cyan;font-weight:bold}.w{color:yellow}</style>"""
    yield f'<div>🚀 Initializing Render Engine...</div>'
    
    async with async_playwright() as p:
        try:
            # Render needs specific args
            browser = await p.chromium.launch(headless=True, args=['--no-sandbox', '--disable-setuid-sandbox'])
            context = await browser.new_context()
            
            cookies = parse_cookies(cookie_string)
            if not cookies:
                yield f'<div class="e">❌ Invalid Cookies!</div>'
                return
            await context.add_cookies(cookies)
            yield f'<div>🍪 Cookies Injected.</div>'

            page = await context.new_page()
            
            yield f'<div>🌐 Opening Facebook...</div>'
            await page.goto("https://www.facebook.com", timeout=60000)
            
            yield f'<div>💬 Navigating to Chat...</div>'
            await page.goto(chat_url, timeout=60000)
            await page.wait_for_timeout(5000)

            # --- POPUP BYPASS LOGIC (Javascript) ---
            async def kill_popups():
                clicked = await page.evaluate("""() => {
                    let found = false;
                    let buttons = document.querySelectorAll('div[role="button"], span, div[aria-label]');
                    for (let b of buttons) {
                        let t = b.innerText || "";
                        if (t.includes("Continue") || t.includes("restore messages") || b.getAttribute('aria-label') === 'Close') {
                            b.click();
                            found = true;
                        }
                    }
                    return found;
                }""")
                if clicked: yield f'<div class="w">⚔️ Hunter: Smashed a Popup!</div>'

            # --- PIN ENTRY ---
            if pin_code:
                yield f'<div>🔐 Checking for PIN...</div>'
                try:
                    inputs = await page.locator("input[type='tel'], input[type='password']").all()
                    if len(inputs) >= 6:
                        yield f'<div class="w">⚠️ PIN Locked! Entering code...</div>'
                        for i in range(6):
                            await inputs[i].fill(pin_code[i])
                            await page.wait_for_timeout(100)
                        await page.wait_for_timeout(4000)
                except: pass

            # --- SENDING LOOP ---
            count = 0
            running = True
            
            while running:
                await kill_popups()
                
                box = page.locator('div[aria-label="Message"]').first
                if not await box.is_visible():
                    box = page.locator('div[contenteditable="true"]').first
                
                if await box.is_visible():
                    await box.click(force=True)
                    await box.fill(message_text)
                    await page.keyboard.press("Enter")
                    count += 1
                    yield f'<div class="s">✅ Message Sent: {count}</div><script>window.scrollTo(0,document.body.scrollHeight);</script>'
                    
                    if not infinite: running = False
                    else: await page.wait_for_timeout(delay * 1000)
                else:
                    yield f'<div class="e">❌ Message Box Hidden (Retrying...)</div>'
                    await page.wait_for_timeout(3000)

            yield f'<div>🏁 Task Done.</div>'
            await browser.close()
            
        except Exception as e:
            yield f'<div class="e">CRITICAL ERROR: {str(e)}</div>'

@app.get("/", response_class=HTMLResponse)
def index():
    return HTML_TEMPLATE

@app.post("/run")
async def run(cookie_string: str = Form(...), chat_url: str = Form(...), message_text: str = Form(...), 
              delay: int = Form(2), infinite: Optional[str] = Form(None), pin_code: Optional[str] = Form(None)):
    return StreamingResponse(bot_logic(cookie_string, chat_url, message_text, delay, infinite == "on", pin_code), media_type="text/html")

if __name__ == "__main__":
    import uvicorn
    # Render PORT variable ko handle karna zaroori hai
    port = int(os.environ.get("PORT", 8000))
    uvicorn.run(app, host="0.0.0.0", port=port)
            
