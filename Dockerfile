FROM python:3.12-slim AS build
WORKDIR /src
COPY pyproject.toml README.md ./
COPY reachq/ ./reachq/
RUN pip install --no-cache-dir build && \
    python -m build && \
    pip install --no-cache-dir dist/*.whl

FROM python:3.12-slim
WORKDIR /app
RUN useradd -m -u 1000 reachq
COPY --from=build /usr/local/lib/python3.12/site-packages /usr/local/lib/python3.12/site-packages
COPY --from=build /usr/local/bin /usr/local/bin
COPY --from=build /src/reachq /app/reachq
USER reachq

HEALTHCHECK CMD ["python", "-c", "import reachq; print('ok')"]
ENTRYPOINT ["python"]
CMD ["-m", "reachq"]
