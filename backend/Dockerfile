# Dockerfile

# Use the official Python image from the Docker Hub
FROM python:3.9-slim

# Set environment variables to avoid writing .pyc files
ENV PYTHONDONTWRITEBYTECODE 1
ENV PYTHONUNBUFFERED 1

# Set the working directory to /code
WORKDIR /code

# Copy the requirements.txt file into the container
COPY requirements.txt /code/

# Install any dependencies specified in requirements.txt
RUN pip install --no-cache-dir -r requirements.txt

# Copy the rest of the code into the container
COPY . /code/