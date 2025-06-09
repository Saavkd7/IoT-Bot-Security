FROM postgres:13

RUN apt-get update && \
    apt-get install -y iproute2 iputils-arping && \
    rm -rf /var/lib/apt/lists/*
RUN apt-get update && apt-get install -y nano
COPY init.sql /docker-entrypoint-initdb.d/init.sql
COPY enable-remote.sh /docker-entrypoint-initdb.d/enable-remote.sh
#RUN chmod +x enable-remote.sh
EXPOSE 5432
