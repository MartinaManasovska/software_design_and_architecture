# Use an official Python runtime as a base image
FROM python:3.9-slim

# Set the working directory inside the container
WORKDIR /app

# Copy the current directory contents into the container at /app
COPY . /app

# Install any needed packages specified in requirements.txt
RUN pip install --no-cache-dir -r requirements.txt
RUN pip install gunicorn

# Set the PYTHONPATH environment variable to include the app directory
#ENV PYTHONPATH=/app:$PYTHONPATH
ENV PYTHONPATH=/app

# Run the Python application
#CMD ["gunicorn", "--bind", "0.0.0.0:5000", "run:app"]  # For main app
CMD ["gunicorn", "app:app", "--bind", "0.0.0.0:5000"]

