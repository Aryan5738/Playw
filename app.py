import os
import time
import threading
import uuid
import datetime
import streamlit as st
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.common.action_chains import ActionChains

# --- PAGE CONFIG ---
st.set_page_config(page_title="FB Pro Sender", layout="centered")
st.title("FB Sender (Anti-Detect Mode 🛡️)")

# --- GLOBAL TASK MANAGER ---
@st.cache_resource
class TaskManager:
    def __init__(self):
        self.tasks = {} 

    def create_task(self):
        task_id = str(uuid.uuid4())[:8]
        self.tasks[task_id] = {
            "status": "Running",
            "logs": [],
            "count": 0,
            "stop": False,
            "screenshot": None
        }
        return task_id

    def get_task(self, task_id):
        return self.tasks.get(task_id)

    def log_update(self, task_id, message):
        if task_id in self.tasks:
            timestamp = datetime.datetime.now().strftime("%H:%M:%S")
            self.tasks[task_id]["logs"].append(f"[{timestamp}] {message}")

    def update_screenshot(self, task_id, driver):
        if task_id in self.tasks:
            filename = f"screen_{task_id}.png"
            driver.save_screenshot(filename)
            self.tasks[task_id]["screenshot"] = filename

    def stop_task(self, task_id):
        if task_id in self.tasks:
            self.tasks[task_id]["stop"] = True
            self.tasks[task_id]["status"] = "Stopped by User"

manager = TaskManager()

# --- COOKIE PARSER ---
def parse_cookies(cookie_string):
    cookies = []
    try:
        lines = cookie_string.split('\n')
        for line in lines:
            parts = line.split('\t')
            if len(parts) >= 7: # Netscape format
                cookies.append({
                    'name': parts[5], 
                    'value': parts[6].strip(), 
                    'domain': parts[0]
                })
        
        if not cookies: # Try simple format key=value;
            items = cookie_string.split(';')
            for item in items:
                if '=' in item:
                    name, value = item.strip().split('=', 1)
                    cookies.append({'name': name, 'value': value, 'domain': '.facebook.com'})
        return cookies
    except:
        return []

# --- DRIVER SETUP ---
def get_driver():
    chrome_options = Options()
    
    # User Agent & Window Size
    user_agent = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
    chrome_options.add_argument(f'user-agent={user_agent}')
    chrome_options.add_argument("--window-size=1920,1080")
    
    # Anti-Detection
    chrome_options.add_argument("--disable-blink-features=AutomationControlled")
    chrome_options.add_experimental_option("excludeSwitches", ["enable-automation"])
    chrome_options.add_experimental_option('useAutomationExtension', False)

    # Server Flags
    chrome_options.add_argument("--headless=new") 
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--disable-dev-shm-usage")
    chrome_options.add_argument("--disable-gpu")
    
    chromium_path = os.environ.get("CHROME_BIN", "/usr/bin/chromium")
    chromedriver_path = os.environ.get("CHROMEDRIVER_PATH", "/usr/bin/chromedriver")

    service = Service(chromedriver_path)
    try:
        driver = webdriver.Chrome(service=service, options=chrome_options)
        return driver
    except Exception as e:
        return None

# --- ACTION LOGIC ---
def send_message_safely(driver, text):
    # Updated Selectors
    selectors = [
        'div[aria-label="Message"]', 
        'div[role="textbox"]', 
        'div[contenteditable="true"]',
        'p[class*="xdj266r"]'
    ]
    msg_box = None
    for selector in selectors:
        try:
            msg_box = driver.find_element(By.CSS_SELECTOR, selector)
            if msg_box: break
        except:
            continue
            
    if msg_box:
        try:
            driver.execute_script("arguments[0].focus();", msg_box)
            actions = ActionChains(driver)
            actions.send_keys(text)
            time.sleep(1)
            actions.send_keys(Keys.RETURN)
            actions.perform()
            return True
        except:
            return False
    return False

# --- BACKGROUND WORKER ---
def run_background_task(task_id, cookie_str, url, msg, delay, is_infinite):
    manager.log_update(task_id, "Starting Driver...")
    driver = get_driver()
    
    if not driver:
        manager.tasks[task_id]["status"] = "Driver Failed"
        return

    try:
        driver.get("https://www.facebook.com/")
        
        cookies = parse_cookies(cookie_str)
        if not cookies:
            manager.log_update(task_id, "Invalid Cookie Format!")
            return
            
        for c in cookies:
            try: driver.add_cookie(c)
            except: pass
        
        manager.log_update(task_id, "Loading URL...")
        driver.get(url)
        time.sleep(10) 
        
        # Take Screenshot 1 (Load Check)
        manager.update_screenshot(task_id, driver)
        
        keep_running = True
        while keep_running:
            if manager.tasks[task_id]["stop"]:
                break

            # Popup Closer
            try:
                popups = driver.find_elements(By.XPATH, "//div[@aria-label='Close' or text()='Got it']")
                for p in popups: p.click()
            except: pass

            success = send_message_safely(driver, msg)
            
            if success:
                manager.tasks[task_id]["count"] += 1
                cnt = manager.tasks[task_id]["count"]
                manager.log_update(task_id, f"Sent Message #{cnt}")
                
                if not is_infinite:
                    keep_running = False
                    manager.tasks[task_id]["status"] = "Completed"
                else:
                    time.sleep(delay)
            else:
                manager.log_update(task_id, "Element Not Found (See Screenshot)")
                manager.update_screenshot(task_id, driver) 
                time.sleep(5)

    except Exception as e:
        manager.log_update(task_id, f"Error: {str(e)}")
        manager.tasks[task_id]["status"] = "Error"
    finally:
        driver.quit()
        if manager.tasks[task_id]["status"] == "Running":
            manager.tasks[task_id]["status"] = "Finished"

# --- UI ---
tab1, tab2 = st.tabs(["🚀 Launch", "👀 Monitor"])

with tab1:
    st.subheader("New Automation Task")
    cookie_input = st.text_area("Paste Cookies Here", height=100)
    target_url = st.text_input("Facebook Chat/Group URL")
    message_text = st.text_input("Message to Send")
    c1, c2 = st.columns(2)
    enable_infinite = c1.checkbox("Infinite Loop", False)
    delay_time = c2.number_input("Delay (Seconds)", 5, 120, 10)

    if st.button("Start Task"):
        if not cookie_input or not target_url:
            st.error("Please fill required fields")
        else:
            new_id = manager.create_task()
            t = threading.Thread(
                target=run_background_task, 
                args=(new_id, cookie_input, target_url, message_text, delay_time, enable_infinite)
            )
            t.start()
            st.success(f"Started! ID: {new_id}")

with tab2:
    st.subheader("Live Status")
    check_id = st.text_input("Task ID")
    
    if st.button("Refresh") or check_id:
        task = manager.get_task(check_id)
        if task:
            st.info(f"Status: {task['status']} | Sent: {task['count']}")
            
            # --- FIX IS HERE ---
            if task['screenshot'] and os.path.exists(task['screenshot']):
                # use_column_width hatakar use_container_width kar diya
                st.image(task['screenshot'], caption="Bot's View (Server)", use_container_width=True)
            else:
                st.warning("No screenshot yet (Wait 10-15s)")
                
            st.code("\n".join(task['logs'][-8:]))
            
            if task['status'] == "Running":
                if st.button("Stop"):
                    manager.stop_task(check_id)
                    st.rerun()
            
