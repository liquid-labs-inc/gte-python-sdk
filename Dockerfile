FROM python:3.10-slim AS builder

WORKDIR /app

COPY . /app

RUN pip install .

FROM python:3.10-slim

COPY --from=builder /app/dist /dist
RUN pip install /dist/*.whl && rm -rf /dist

CMD ["/usr/local/bin/gte-py"]