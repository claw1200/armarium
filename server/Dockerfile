FROM python:3.12-slim AS estimator

RUN apt-get update \
    && apt-get install -y --no-install-recommends cmake g++ make git wget ca-certificates \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /src
COPY estimator /src/estimator
RUN cmake -S /src/estimator -B /build -DCMAKE_BUILD_TYPE=Release \
    && cmake --build /build --target armarium-loop-tempo \
    && cmake --install /build --prefix /out

FROM python:3.12-slim

WORKDIR /app
COPY pyproject.toml ./
COPY app ./app
RUN pip install --no-cache-dir .

COPY --from=estimator /out/bin/armarium-loop-tempo /usr/local/bin/armarium-loop-tempo

ENV LIBRARY_ROOT=/library
ENV DATABASE_PATH=/data/catalog.sqlite
RUN mkdir -p /data /library

EXPOSE 8000
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
