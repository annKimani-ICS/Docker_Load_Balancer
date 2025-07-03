FROM python:3.9-slim
WORKDIR /app
COPY server.py .
RUN pip install flask
RUN PIP install requirements.txt
CMD ["python", "server.py"]
