import asyncio
import subprocess
import sys
import os
from fastapi import FastAPI, Form
from fastapi.responses import HTMLResponse, StreamingResponse
from typing import Optional

# --- AUTO-INSTALLER ---
@app.on_event("startup")
async def startup_event():
    print("⚙️ SERVER STARTING...")
    try:
        import playwright
        from playwright.async_api import async_playwright
        print("⬇️ Ensuring Chromium...")
        subprocess.check_call([sys.executable, "-m", "playwright", "install", "chromium"])
        print("✅ Browser Ready!")
    except Exception as e:
        print(f"❌ Setup Error: {e}")

from playwright.async_api import async_playwright

app = FastAPI()

# --- UI TEMPLATE ---
HTML_TEMPLATE = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>FB Hunter Bot (Smart Logs)</title>
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
    <h1>🕵️ FB Hunter (Smart Diagnostics)</h1>
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
            <input type="submit" value="🔥 START & DIAGNOSE">
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
    yield """<style>body{background:#000;color:#0f0;font-family:monospace;padding:10px}.e{color:red}.s{color:cyan;font-weight:bold}.w{color:yellow}.i{color:#58a6ff}</style>"""
    yield f'<div>⚙️ Starting Smart Engine...</div>'
    
    async with async_playwright() as p:
        try:
            # Launch with specific args to imitate real browser
            browser = await p.chromium.launch(
                headless=True,
                args=['--no-sandbox', '--disable-setuid-sandbox', '--disable-gl-drawing-for-tests']
            )
            # Use a real User Agent
            context = await browser.new_context(
                user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36"
            )
            
            cookies = parse_cookies(cookie_string)
            if not cookies:
                yield f'<div class="e">❌ Error: Cookies are empty!</div>'
                return
            await context.add_cookies(cookies)
            
            page = await context.new_page()
            
            # 1. CHECK LOGIN STATUS
            yield f'<div>🌐 Opening Facebook to verify identity...</div>'
            await page.goto("https://www.facebook.com", timeout=60000)
            await page.wait_for_timeout(3000)
            
            # Try to grab username
            try:
                # Looking for profile link or aria-label in navigation
                username = await page.evaluate("""() => {
                    let el = document.querySelector('div[role="navigation"] a[href*="/me/"]'); 
                    if(!el) el = document.querySelector('svg[aria-label] ~ span'); // Mobile view sometimes
                    return el ? el.innerText : null;
                }""")
                
                if username:
                    yield f'<div class="s">✅ Logged in as: {username}</div>'
                else:
                    # Check if login failed
                    content = await page.content()
                    if "Log In" in content or "Create new account" in content:
                        yield f'<div class="e">❌ LOGIN FAILED: Cookies expired or invalid.</div>'
                        await browser.close()
                        return
                    else:
                        yield f'<div class="w">⚠️ Logged in, but Username hidden (Continuing...)</div>'
            except:
                yield f'<div class="w">⚠️ Could not detect username (Continuing...)</div>'

            # 2. OPEN CHAT
            yield f'<div>💬 Opening Chat URL...</div>'
            await page.goto(chat_url, timeout=60000)
            await page.wait_for_timeout(5000)

            # --- SMART DIAGNOSTICS FUNCTION ---
            async def diagnose_screen():
                """Checks what is blocking the bot"""
                content = await page.content()
                
                if "Enter your PIN" in content or "Secure storage" in content:
                    return "PIN_LOCK"
                elif "Connect with" in content and "Google" in content:
                    return "SYNC_POPUP"
                elif "Continue" in content or "restore messages" in content:
                    return "CONTINUE_POPUP"
                elif "Messages are end-to-end encrypted" in content:
                    return "CLEAN" # Should be fine
                else:
                    return "UNKNOWN"

            # --- POPUP BYPASS LOGIC ---
            async def hunt_popups():
                clicked = await page.evaluate("""() => {
                    let clicked = false;
                    let buttons = document.querySelectorAll('div[role="button"], span, div[aria-label], button');
                    for (let el of elements) {
                        let txt = (el.innerText || "").toLowerCase();
                        let label = (el.getAttribute('aria-label') || "").toLowerCase();
                        
                        if (txt.includes("continue") || txt.includes("restore") || label === "close") {
                             // Ensure it's not hidden
                             if (el.offsetParent !== null) { el.click(); clicked = true; }
                        }
                    }
                    return clicked;
                }""")
                if clicked: yield f'<div class="w">⚔️ Hunter: Removed a Popup!</div>'

            # --- PIN BYPASS ---
            if pin_code:
                status = await diagnose_screen()
                if status == "PIN_LOCK":
                    yield f'<div class="w">⚠️ PIN Lock Screen Detected!</div>'
                    try:
                        inputs = await page.locator("input[type='tel'], input[type='password']").all()
                        if len(inputs) >= 6:
                            yield f'<div class="i">🔢 Entering PIN {pin_code}...</div>'
                            for i in range(6):
                                await inputs[i].fill(pin_code[i])
                                await page.wait_for_timeout(100)
                            yield f'<div class="s">🔓 PIN Submitted. Waiting...</div>'
                            await page.wait_for_timeout(5000)
                    except: pass

            # --- MAIN LOOP ---
            count = 0
            running = True
            
            while running:
                # 1. Run Diagnostics
                screen_status = await diagnose_screen()
                
                # 2. Take Action based on Status
                if screen_status == "CONTINUE_POPUP":
                    yield f'<div class="w">⚠️ Stuck on "Continue" Popup. Clicking...</div>'
                    await hunt_popups()
                    await page.wait_for_timeout(2000)
                
                elif screen_status == "PIN_LOCK" and not pin_code:
                    yield f'<div class="e">❌ Stuck on PIN Screen! (Please enter PIN in settings)</div>'
                    await page.wait_for_timeout(5000) # Wait in case user is watching

                # 3. Try to Send
                box = page.locator('div[aria-label="Message"]').first
                if not await box.is_visible():
                     box = page.locator('div[contenteditable="true"]').first
                
                if await box.is_visible():
                    await box.click(force=True)
                    await box.fill(message_text)
                    await page.keyboard.press("Enter")
                    
                    count += 1
                    yield f'<div class="s">✅ Sent: {count}</div><script>window.scrollTo(0,document.body.scrollHeight);</script>'
                    
                    if not infinite: running = False
                    else: await page.wait_for_timeout(delay * 1000)
                else:
                    # Provide Detailed Error
                    yield f'<div class="e">❌ Box Not Found. Status: {screen_status} (Retrying...)</div>'
                    await page.wait_for_timeout(3000)
                    
                    # Last ditch effort: blind clicks on buttons
                    await hunt_popups()

            yield f'<div>🏁 Finished.</div>'
            await browser.close()

        except Exception as e:
            yield f'<div class="e">CRITICAL ERROR: {str(e)}</div>'

# --- ROUTES ---
@app.get("/", response_class=HTMLResponse)
def index():
    return HTML_TEMPLATE

@app.post("/run")
async def run(
    cookie_string: str = Form(...), 
    chat_url: str = Form(...), 
    message_text: str = Form(...), 
    delay: int = Form(2), 
    infinite: Optional[str] = Form(None), 
    pin_code: Optional[str] = Form(None)
):
    return StreamingResponse(
        bot_logic(cookie_string, chat_url, message_text, delay, infinite == "on", pin_code), 
        media_type="text/html"
    )

if __name__ == "__main__":
    import uvicorn
    port = int(os.environ.get("PORT", 8000))
    uvicorn.run(app, host="0.0.0.0", port=port)
            
