FROM pgvector/pgvector:0.6.2-pg16

RUN mkdir -p /docker-entrypoint-initdb.d
COPY initdb-extensions.sh /docker-entrypoint-initdb.d/initdb-extensions.sh