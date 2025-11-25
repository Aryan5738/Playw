import asyncio
import subprocess
import sys
import os
from fastapi import FastAPI, Form
from fastapi.responses import HTMLResponse, StreamingResponse
from typing import Optional

# ==========================================
# 🔥 AUTO-INSTALLER LOGIC (NO ERROR FIX) 🔥
# ==========================================
def install_playwright_browsers():
    print("⚙️ CHECKING SYSTEM REQUIREMENTS...")
    try:
        # Check if we can import playwright
        import playwright
        print("✅ Playwright Library Found.")
        
        # Force install Chromium inside the script
        # This fixes the "Executable doesn't exist" error on Render
        print("⬇️ DOWNLOADING CHROMIUM BROWSER (This may take a minute)...")
        subprocess.check_call([sys.executable, "-m", "playwright", "install", "chromium"])
        print("✅ CHROMIUM INSTALLED SUCCESSFULLY!")
        
    except ImportError:
        print("❌ Playwright not found! Installing...")
        subprocess.check_call([sys.executable, "-m", "pip", "install", "playwright"])
        subprocess.check_call([sys.executable, "-m", "playwright", "install", "chromium"])

# Run this immediately when app starts
install_playwright_browsers()

from playwright.async_api import async_playwright

app = FastAPI()

# --- HACKER UI TEMPLATE ---
HTML_TEMPLATE = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>FB Hunter Bot (Auto-Fix)</title>
    <style>
        body { background-color: #0d1117; color: #c9d1d9; font-family: 'Courier New', monospace; padding: 20px; }
        .container { max-width: 800px; margin: 0 auto; }
        h1 { color: #58a6ff; border-bottom: 2px solid #30363d; padding-bottom: 10px; }
        .card { background: #161b22; padding: 20px; border-radius: 8px; border: 1px solid #30363d; margin-bottom: 20px; }
        input, textarea { width: 100%; background: #0d1117; border: 1px solid #30363d; color: #c9d1d9; padding: 10px; margin-top: 5px; border-radius: 4px; box-sizing: border-box;}
        input[type="submit"] { background: #238636; color: white; border: none; padding: 12px; cursor: pointer; font-weight: bold; margin-top: 15px; }
        iframe { width: 100%; height: 500px; background: #000; border: 1px solid #333; margin-top: 10px; }
        label { color: #8b949e; font-weight: bold; display: block; margin-top: 10px; }
    </style>
</head>
<body>
<div class="container">
    <h1>🚀 FB Hunter Bot (Auto-Download)</h1>
    <div class="card">
        <form action="/run" method="post" target="log_frame">
            <label>🍪 Cookie String:</label>
            <textarea name="cookie_string" rows="3" required></textarea>
            
            <label>🔐 6-Digit PIN (If required):</label>
            <input type="password" name="pin_code" maxlength="6">

            <label>🔗 Chat URL:</label>
            <input type="text" name="chat_url" value="https://www.facebook.com/messages/t/61558458805222">

            <label>💬 Message:</label>
            <input type="text" name="message_text" value="Hello from Bot!">

            <div style="display: flex; gap: 10px; margin-top: 10px;">
                <div style="flex:1"><label>Delay (s):</label><input type="number" name="delay" value="2"></div>
                <div style="flex:1; display:flex; align-items:center; padding-top:25px;">
                    <input type="checkbox" name="infinite" id="inf" style="width:auto; margin-right:5px;">
                    <label for="inf" style="margin:0; cursor:pointer;">Infinite Loop</label>
                </div>
            </div>
            <input type="submit" value="🔥 START ATTACK">
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

# --- BOT LOGIC ---
async def bot_logic(cookie_string, chat_url, message_text, delay, infinite, pin_code):
    yield """<style>body{background:#000;color:#0f0;font-family:monospace;padding:10px}.e{color:red}.s{color:cyan;font-weight:bold}.w{color:yellow}</style>"""
    yield f'<div>⚙️ Starting Engine...</div>'
    
    async with async_playwright() as p:
        try:
            # Launch with specific args for Render
            browser = await p.chromium.launch(
                headless=True,
                args=['--no-sandbox', '--disable-setuid-sandbox', '--disable-gl-drawing-for-tests']
            )
            context = await browser.new_context()
            
            # Cookies
            cookies = parse_cookies(cookie_string)
            if not cookies:
                yield f'<div class="e">❌ Error: Invalid Cookies!</div>'
                return
            await context.add_cookies(cookies)
            
            page = await context.new_page()
            
            yield f'<div>🌐 Opening Facebook...</div>'
            await page.goto("https://www.facebook.com", timeout=60000)
            
            yield f'<div>💬 Loading Chat...</div>'
            await page.goto(chat_url, timeout=60000)
            await page.wait_for_timeout(5000)

            # --- HUNTER FUNCTION (JavaScript Force) ---
            async def hunt_popups():
                # This script finds ANY button with specific text and clicks it
                clicked = await page.evaluate("""() => {
                    let clicked = false;
                    
                    // 1. Find all potential buttons
                    let elements = document.querySelectorAll('div[role="button"], span, div[aria-label], button');
                    
                    for (let el of elements) {
                        let txt = el.innerText || "";
                        let label = el.getAttribute('aria-label') || "";
                        
                        // Check for targets
                        if (txt.includes("Continue") || txt.includes("restore messages") || label === "Close" || label === "Continue") {
                            // Ensure it's visible
                            if (el.offsetParent !== null) {
                                el.click();
                                clicked = true;
                            }
                        }
                    }
                    return clicked;
                }""")
                if clicked: 
                    yield f'<div class="w">⚔️ Hunter: Clicked a popup/button!</div>'
                    await page.wait_for_timeout(2000)

            # --- PIN BYPASS ---
            if pin_code:
                yield f'<div>🔐 Checking PIN status...</div>'
                try:
                    inputs = await page.locator("input[type='tel'], input[type='password']").all()
                    if len(inputs) >= 6:
                        yield f'<div class="w">⚠️ PIN Required! Entering {pin_code}...</div>'
                        for i in range(6):
                            await inputs[i].fill(pin_code[i])
                            await page.wait_for_timeout(100)
                        yield f'<div class="s">🔓 PIN Entered! Waiting...</div>'
                        await page.wait_for_timeout(5000)
                except: pass

            # --- MAIN SENDING LOOP ---
            count = 0
            running = True
            
            while running:
                # 1. Clear Path
                await hunt_popups()
                
                # 2. Find Box
                # Try multiple selectors
                box = page.locator('div[aria-label="Message"]').first
                if not await box.is_visible():
                     box = page.locator('div[contenteditable="true"]').first
                
                if await box.is_visible():
                    # 3. Send
                    await box.click(force=True) # Force click handles overlays
                    await box.fill(message_text)
                    await page.keyboard.press("Enter")
                    
                    count += 1
                    yield f'<div class="s">✅ Sent: {count}</div><script>window.scrollTo(0,document.body.scrollHeight);</script>'
                    
                    if not infinite: running = False
                    else: await page.wait_for_timeout(delay * 1000)
                else:
                    yield f'<div class="e">❌ Message Box not visible. Retrying Hunter...</div>'
                    await page.wait_for_timeout(3000)

            yield f'<div>🏁 Finished.</div>'
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
    # Render requires reading the PORT environment variable
    port = int(os.environ.get("PORT", 8000))
    uvicorn.run(app, host="0.0.0.0", port=port)
        
