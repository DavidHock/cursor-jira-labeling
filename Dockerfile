FROM python:3.9
WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY . .
RUN mkdir -p /shared
ENV PYTHONUNBUFFERED=1
CMD ["python", "jira_app.py"]
