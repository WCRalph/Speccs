# Use an official Python runtime as a parent image
FROM python:3.11-slim

# Set the working directory in the container
WORKDIR /app

# Copy the requirements file into the container at /app
COPY requirements.txt .

# Install any needed packages specified in requirements.txt
# --no-cache-dir reduces image size
# --upgrade pip ensures we have the latest pip
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt

# Copy the rest of the application code into the container at /app
COPY . .

# Make port 5000 available to the world outside this container (Flask default)
EXPOSE 5000

# Define environment variable (optional, can also be set in docker-compose.yml)
# ENV FLASK_APP=app.py

# Run app.py when the container launches
# Use --host=0.0.0.0 to make it accessible externally within the Docker network
CMD ["flask", "run", "--host=0.0.0.0"]
