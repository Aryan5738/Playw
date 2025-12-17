# 1. Base Image Change: "slim" hata diya (ye zyada stable hai)
FROM python:3.9

# 2. Install Chromium & Git
# Humne faltu packages hata diye jo error 100 de rahe the
RUN apt-get update && apt-get install -y \
    chromium \
    chromium-driver \
    git \
    && rm -rf /var/lib/apt/lists/*

# 3. Environment Variables
ENV CHROME_BIN=/usr/bin/chromium
ENV CHROMEDRIVER_PATH=/usr/bin/chromedriver

# 4. Working Directory
WORKDIR /app

# 5. Git Permission Fix
RUN git config --global --add safe.directory '*'

# 6. Install Python Libraries
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# 7. Copy Code
COPY . .

# 8. Start Command
# "app.py" ka naam check kar lena (Case Sensitive hai!)
CMD sh -c "streamlit run app.py --server.port=$PORT --server.address=0.0.0.0"
