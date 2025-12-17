# 1. Base Image
FROM python:3.9-slim

# 2. System dependencies (Git zaroori hai error 128 hatane ke liye)
RUN apt-get update && apt-get install -y \
    build-essential \
    curl \
    software-properties-common \
    git \
    chromium \
    chromium-driver \
    && rm -rf /var/lib/apt/lists/*

# 3. Environment Variables
ENV CHROME_BIN=/usr/bin/chromium
ENV CHROMEDRIVER_PATH=/usr/bin/chromedriver

# 4. Working Directory
WORKDIR /app

# 5. Git "Safe Directory" Error Fix (Yeh hai Error 128 ka ilaaj)
RUN git config --global --add safe.directory '*'

# 6. Install Requirements
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# 7. Copy Code
COPY . .

# 8. Start Command (Isme PORT variable dynamic rakha hai)
# Render khud PORT environment variable deta hai, hum wahi use karenge
CMD sh -c "streamlit run app.py --server.port=$PORT --server.address=0.0.0.0"
