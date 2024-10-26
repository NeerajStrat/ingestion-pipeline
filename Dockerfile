FROM python:3.12-slim

# Install necessary system packages (if needed)
# Step 2: Update apt-get and install dependencies
RUN apt-get update && apt-get install -y \
    wkhtmltopdf

# Create a non-root user with a home directory
RUN useradd -m finaillm-user

# Set the working directory
WORKDIR /app

# Copy the requirements file first for better caching
COPY ./requirements.txt .

# Create a virtual environment as the root user
RUN python -m venv venv

# Install Python packages as root
RUN ./venv/bin/pip install --no-cache-dir -r requirements.txt

# Create the /app/data directory and make finaillm-user the owner of the entire folder
RUN mkdir -p /app/data/sec-edgar-filings && chown -R finaillm-user:finaillm-user /app/data/sec-edgar-filings && chmod -R 777 /app/data/sec-edgar-filings


# Switch to the non-root user
USER finaillm-user

# Copy the rest of the application code
COPY . .

EXPOSE 8000

# Specify the command to run your application
CMD ["./venv/bin/python", "server.py"]  # Replace with your actual script
