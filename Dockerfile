FROM gcr.io/kaggle-images/python:latest
# gpu image: gcr.io/kaggle-gpu-images/python

WORKDIR /workspace

ENV UV_PROJECT_ENVIRONMENT=/usr/local/
ENV PYTHONPATH=/workspace:${PYTHONPATH}

COPY pyproject.toml ./
RUN uv pip install -r pyproject.toml --system

COPY src/ src/
