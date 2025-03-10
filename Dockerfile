# Use the official Python image from the Docker Hub
FROM python:3.12-slim

# Set the working directory in the container
WORKDIR /app

# Copy the uv.lock file into the container
COPY uv.lock .

# Install uv using pip
RUN pip install --no-cache-dir uv

# Install the dependencies using uv
RUN uv --no-cache-dir sync uv.lock

# Copy the rest of the application code into the container
COPY . .

EXPOSE 8501

# Command to run the Streamlit app
CMD ["streamlit", "run", "main.py"]