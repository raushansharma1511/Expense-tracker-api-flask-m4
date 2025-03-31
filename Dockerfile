# FROM python:3.12.0-slim

# # Install system dependencies for cairo and weasyprint
# RUN apt-get update && apt-get install -y \
#     libcairo2 \
#     libpango-1.0-0 \
#     libpangocairo-1.0-0 \
#     libgdk-pixbuf-2.0-0 \
#     libffi-dev \
#     && apt-get clean \
#     && rm -rf /var/lib/apt/lists/*

# # Set the working directory in the container
# WORKDIR /app

# # Copy requirements file and install Python dependencies
# COPY requirements.txt .
# RUN pip install --no-cache-dir -r requirements.txt

# # Copy the rest of the application files
# COPY . .

# # Expose port 5000 for Flask
# EXPOSE 5000

# # Set environment variables (optional if using .env)
# # ENV FLASK_APP=app
# ENV FLASK_ENV=production  
# ENV FLASK_DEBUG=False 

# # # Run the Flask application
# CMD ["flask", "run", "--host=0.0.0.0", "--port=5000"]

# **Stage 1: Builder**
FROM python:3.12.0-slim AS builder

# Install system dependencies for WeasyPrint and Cairo
RUN apt-get update && apt-get install -y --no-install-recommends \
    libcairo2 \
    libpango-1.0-0 \
    libpangocairo-1.0-0 \
    libgdk-pixbuf-2.0-0 \
    libffi-dev \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*


# Set working directory
WORKDIR /app

# Copy requirements file and install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir --prefix=/install -r requirements.txt

# **Stage 2: Final Image**
FROM python:3.12.0-slim

# Set working directory
WORKDIR /app
COPY --from=builder /usr/lib /usr/lib
COPY --from=builder /usr/include /usr/include

# Copy runtime dependencies from the builder stage
COPY --from=builder /install /usr/local

# Copy application code
COPY . .

# Expose port 5000
EXPOSE 5000

# Set environment variables
ENV FLASK_ENV=production  
ENV FLASK_DEBUG=False 

# Start Flask application
CMD ["flask", "run", "--host=0.0.0.0", "--port=5000"]
