# Use a lightweight Python image to save RAM on your server
FROM python:3.10-slim

# Tell Docker where to work inside the container
WORKDIR /app

# Copy the requirements file first to cache the installations
COPY requirements.txt .

# Install the Python libraries without saving the messy cache files
RUN pip install --no-cache-dir -r requirements.txt

# Copy all your actual code (api.py, main.py, database.py, etc.) into the container
COPY . .

# Expose the port that FastAPI is listening on
EXPOSE 8080

# The command that boots up your API
CMD ["python", "api.py"]