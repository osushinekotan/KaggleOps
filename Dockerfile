FROM gcr.io/kaggle-images/python:latest
# gpu image: gcr.io/kaggle-gpu-images/python

ENV UV_PROJECT_ENVIRONMENT=/usr/local/

COPY . .

RUN uv pip install -r pyproject.toml --system
