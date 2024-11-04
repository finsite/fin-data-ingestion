import os

# Define the project name and GitHub repository details
project_name = "fin-data-ingestion"
docker_repo = "mobious999/my-docker-repo"  # Change to your GitHub repo
github_token = "your_github_token"  # Store your GitHub token securely

# Create the main project directory structure
os.makedirs(os.path.join(project_name, ".github", "workflows"), exist_ok=True)
os.makedirs(os.path.join(project_name, "app"), exist_ok=True)
os.makedirs(os.path.join(project_name, "tests"), exist_ok=True)

# Create Dockerfile
with open(os.path.join(project_name, "Dockerfile"), "w") as f:
    f.write("""# Use the official Python image from the Docker Hub
FROM python:3.10-slim

# Set the working directory
WORKDIR /app

# Copy requirements and install them
COPY app/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy the application code
COPY app/ .

# Command to run the application
CMD ["python", "main.py"]
""")

# Create .dockerignore
with open(os.path.join(project_name, ".dockerignore"), "w") as f:
    f.write("""__pycache__
*.pyc
*.pyo
*.pyd
*.db
*.log
*.env
tests/
""")

# Create requirements.txt
with open(os.path.join(project_name, "app", "requirements.txt"), "w") as f:
    f.write("# Add your Python dependencies here\n")

# Create main.py
with open(os.path.join(project_name, "app", "main.py"), "w") as f:
    f.write("""def main():
    print("Hello, Docker!")

if __name__ == "__main__":
    main()
""")

# Create a sample test
with open(os.path.join(project_name, "tests", "test_main.py"), "w") as f:
    f.write("""import pytest
from app.main import main

def test_main():
    assert main() is None  # Adjust this as per your actual function return
""")

# Create GitHub Actions workflow file
with open(os.path.join(project_name, ".github", "workflows", "ci.yml"), "w") as f:
    f.write(f"""name: CI

on:
  push:
    branches:
      - main
  pull_request:

jobs:
  build:
    runs-on: ubuntu-latest

    services:
      docker:
        image: docker:20.10.7
        options: >-
          --privileged
          --userns=host

    steps:
    - name: Checkout code
      uses: actions/checkout@v2

    - name: Set up Python
      uses: actions/setup-python@v2
      with:
        python-version: '3.10'

    - name: Install dependencies
      run: |
        pip install -r app/requirements.txt
        pip install pytest

    - name: Run tests
      run: |
        pytest tests/

    - name: Build Docker image
      run: |
        docker build -t {docker_repo}:latest .

    - name: Log in to GitHub Container Registry
      env:
        GITHUB_TOKEN: {github_token}
      run: echo "$GITHUB_TOKEN" | docker login ghcr.io -u ${{{{ github.actor }}}} --password-stdin

    - name: Push Docker image to GitHub Container Registry
      run: |
        docker push {docker_repo}:latest
""")

print(f"Project structure for {project_name} created successfully!")
