# Use the official Python image from the Docker Hub
FROM python:3.12-slim-bookworm
COPY --from=ghcr.io/astral-sh/uv:latest /uv /uvx /bin/

# Set the working directory in the container
WORKDIR /app

COPY . .

# Install the dependencies using uv
RUN uv sync --frozen


EXPOSE 8501

# Command to run the Streamlit app
CMD ["streamlit", "run", "main.py"]