# Use Python 3.11 slim base image for a lightweight container
FROM python:3.11-slim

# Set working directory inside the container
WORKDIR /app

# Copy requirements file and install dependencies
COPY requirements.txt .
# Install dependencies without caching to reduce image size
RUN pip install --no-cache-dir -r requirements.txt

# Copy the entire application code
COPY . .

# Expose port 5000 for the Flask application
EXPOSE 5000

# Command to run the application
CMD ["python", "pubsub_ws.py"]