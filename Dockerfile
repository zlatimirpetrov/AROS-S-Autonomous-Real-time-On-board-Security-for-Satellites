#lightweight Python image
FROM python:3.11-slim

#making non-privileged user for the sat app
RUN useradd -m satellite_user

WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY . .

#security: change ownership of the app dir to our non root user
RUN chown -R satellite_user:satellite_user /app

#switch to the no privileged user
USER satellite_user

CMD ["python", "src/live_detector.py"]