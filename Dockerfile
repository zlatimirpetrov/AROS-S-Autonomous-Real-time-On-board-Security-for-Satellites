#lightweight Python image
FROM python:3.11-slim

#making non-privileged user for the sat app
RUN useradd -m -u 10001 satellite_user

WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY . .

#security: change ownership of the app dir to our non root user
RUN mkdir -p /app/logs && chown -R satellite_user:satellite_user /app

#switch to the non-privileged user
USER satellite_user

ENV PYTHONUNBUFFERED=1

ENTRYPOINT ["python", "-m", "src.main"]
CMD []