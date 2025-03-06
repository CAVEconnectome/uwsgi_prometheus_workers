# Use a minimal Python image
FROM python:3.9-slim

# Create a working directory
WORKDIR /app

# Install Python dependencies
COPY requirements.txt /app/
RUN pip install --no-cache-dir -r requirements.txt

# Copy the exporter script into the container
COPY uwsgi_stats_exporter.py /app/

# Expose the exporter port (optional: for clarity)
EXPOSE 9101

# Run the exporter script
CMD ["python", "uwsgi_stats_exporter.py"]