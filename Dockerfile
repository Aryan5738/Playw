# 1. Base Image (Python)
FROM python:3.9-slim

# 2. System dependencies aur Chromium install karein
# Chromium aur Chromedriver Debian repo se install karna sabse stable hai
RUN apt-get update && apt-get install -y \
    chromium \
    chromium-driver \
    && rm -rf /var/lib/apt/lists/*

# 3. Environment Variables set karein
ENV CHROME_BIN=/usr/bin/chromium
ENV CHROMEDRIVER_PATH=/usr/bin/chromedriver

# 4. Working Directory banaye
WORKDIR /app

# 5. Requirements copy aur install karein
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# 6. Pura code copy karein
COPY . .

# 7. Render PORT expose karein
EXPOSE 8501

# 8. Command to run app
# Streamlit ko batana padta hai ki wo specific port par chale
CMD ["streamlit", "run", "app.py", "--server.port=8501", "--server.address=0.0.0.0"]
