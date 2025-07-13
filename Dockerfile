FROM python:3.10-slim

# Install OS dependencies for MediaPipe + Git
RUN apt-get update && apt-get install -y \
    git \
    ffmpeg \
    libglib2.0-0 \
    libsm6 \
    libxext6 \
    libxrender-dev \
    && rm -rf /var/lib/apt/lists/*

# Set working directory
WORKDIR /app

# Copy all project files into the container
COPY . .

# Install Python dependencies
RUN pip install --upgrade pip
RUN pip install git+https://github.com/google/mediapipe.git flask

# Run the app
CMD ["python", "app.py"]
