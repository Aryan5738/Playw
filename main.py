import asyncio
import subprocess
import sys
import os
from fastapi import FastAPI, Form
from fastapi.responses import HTMLResponse, StreamingResponse
from typing import Optional

# ==========================================
# 1. APP DEFINITION
# ==========================================
app = FastAPI()

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

# ==========================================
# 2. UI TEMPLATE
# ==========================================
HTML_TEMPLATE = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>FB Hunter (Desktop Mode)</title>
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
    <h1>🖥️ FB Hunter (Desktop Force)</h1>
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
            <input type="submit" value="🔥 START DESKTOP MODE">
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

# ==========================================
# 3. BOT LOGIC (DESKTOP MODE)
# ==========================================
async def bot_logic(cookie_string, chat_url, message_text, delay, infinite, pin_code):
    yield """<style>body{background:#000;color:#0f0;font-family:monospace;padding:10px}.e{color:red}.s{color:cyan;font-weight:bold}.w{color:yellow}.i{color:#58a6ff}</style>"""
    yield f'<div>⚙️ Starting Desktop Engine...</div>'
    
    async with async_playwright() as p:
        try:
            # 1. Launch Browser
            browser = await p.chromium.launch(
                headless=True,
                args=['--no-sandbox', '--disable-setuid-sandbox', '--disable-gl-drawing-for-tests']
            )
            
            # 2. FORCE DESKTOP CONTEXT (This fixes Mobile View)
            context = await browser.new_context(
                viewport={"width": 1920, "height": 1080}, # Full HD Resolution
                user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
                device_scale_factor=1,
                is_mobile=False,
                has_touch=False
            )
            
            # Cookies
            cookies = parse_cookies(cookie_string)
            if not cookies:
                yield f'<div class="e">❌ Error: Cookies are empty!</div>'
                return
            await context.add_cookies(cookies)
            
            page = await context.new_page()
            
            # --- IDENTITY CHECK ---
            yield f'<div>🌐 Opening Facebook Desktop...</div>'
            try:
                await page.goto("https://www.facebook.com", timeout=60000, wait_until='domcontentloaded')
            except:
                yield f'<div class="w">⚠️ Loading slow, forcing entry...</div>'

            await page.wait_for_timeout(3000)

            # Check Username (Desktop Selectors)
            try:
                name = await page.evaluate("""() => {
                    // Method 1: Left Sidebar Profile
                    let el = document.querySelector('div[role="navigation"] a[href*="/me/"] span');
                    // Method 2: Top Right Profile
                    if(!el) el = document.querySelector('svg[aria-label] + span'); 
                    return el ? el.innerText : null;
                }""")
                if name:
                    yield f'<div class="s">✅ Logged in as: {name}</div>'
                else:
                    yield f'<div class="w">⚠️ Identity Verified (Name Hidden)</div>'
            except:
                pass

            # --- OPEN CHAT ---
            yield f'<div>💬 Navigating to Chat...</div>'
            try:
                await page.goto(chat_url, timeout=90000, wait_until='domcontentloaded')
            except:
                yield f'<div class="w">⚠️ Chat load timeout (Ignoring)...</div>'

            await page.wait_for_timeout(5000)

            # --- MAIN LOOP ---
            count = 0
            running = True
            
            while running:
                # -----------------------------
                # BLOCK 1: HUNTER (POPUP KILLER)
                # -----------------------------
                try:
                    clicked = await page.evaluate("""() => {
                        let clicked = false;
                        // Find all clickable buttons
                        let elements = document.querySelectorAll('div[role="button"], span, div[aria-label], button');
                        for (let el of elements) {
                            let txt = (el.innerText || "").toLowerCase();
                            let label = (el.getAttribute('aria-label') || "").toLowerCase();
                            
                            // Target Blockers
                            if (txt.includes("continue") || txt.includes("restore") || label === "close" || txt.includes("not now") || txt.includes("allow cookies")) {
                                 if (el.offsetParent !== null) { el.click(); clicked = true; }
                            }
                        }
                        return clicked;
                    }""")
                    if clicked:
                        yield f'<div class="w">⚔️ Hunter: Removed a Popup!</div>'
                        await page.wait_for_timeout(1000)
                except:
                    pass

                # -----------------------------
                # BLOCK 2: PIN ENTRY
                # -----------------------------
                if pin_code:
                    try:
                        content = await page.content()
                        if "Enter your PIN" in content or "Secure storage" in content:
                            yield f'<div class="w">🔐 PIN Screen Detected! Entering...</div>'
                            inputs = await page.locator("input[type='tel'], input[type='password']").all()
                            for i in range(min(len(inputs), 6)):
                                await inputs[i].fill(pin_code[i])
                                await page.wait_for_timeout(100)
                            yield f'<div class="s">🔓 PIN Submitted.</div>'
                            await page.wait_for_timeout(4000)
                    except:
                        pass

                # -----------------------------
                # BLOCK 3: SEND MESSAGE
                # -----------------------------
                # Find Box (Desktop Selectors)
                box = page.locator('div[aria-label="Message"]').first
                
                # Check Visibility
                if await box.is_visible():
                    try:
                        # Focus and Type
                        await box.click(force=True)
                        await box.fill(message_text)
                        await page.keyboard.press("Enter")
                        
                        count += 1
                        yield f'<div class="s">✅ Sent: {count}</div><script>window.scrollTo(0,document.body.scrollHeight);</script>'
                        
                        if not infinite: running = False
                        else: await page.wait_for_timeout(delay * 1000)
                    except Exception as e:
                        yield f'<div class="e">❌ Send Error: {str(e)}</div>'
                else:
                    # Detailed Error if hidden
                    yield f'<div class="e">❌ Box Hidden. Trying to clear blockers...</div>'
                    await page.wait_for_timeout(2000)
                    # Scroll to bottom just in case
                    await page.evaluate("window.scrollTo(0, document.body.scrollHeight)")

            yield f'<div>🏁 Finished.</div>'
            await browser.close()

        except Exception as e:
            yield f'<div class="e">CRITICAL ERROR: {str(e)}</div>'

# ==========================================
# 4. ROUTES
# ==========================================
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
            
