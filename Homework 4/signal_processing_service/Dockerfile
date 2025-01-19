FROM python:3.9-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
RUN pip install gunicorn

COPY . .

EXPOSE 5001

#CMD ["gunicorn", "--bind", "0.0.0.0:5001", "run:app"]  # For signal service
CMD ["gunicorn", "app:app", "--bind", "0.0.0.0:5001"]
