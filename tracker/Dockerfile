FROM debian:bookworm-slim

ARG XBT_REF=master

ENV DEBIAN_FRONTEND=noninteractive \
    XBT_CONFIG_FILE=/etc/xbt/xbt_tracker.conf

RUN apt-get update \
    && apt-get install -y --no-install-recommends \
        ca-certificates \
        cmake \
        default-libmysqlclient-dev \
        g++ \
        git \
        libboost-dev \
        libsystemd-dev \
        make \
        zlib1g-dev \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /opt

RUN git clone --depth 1 --branch "${XBT_REF}" https://github.com/OlafvdSpek/xbt.git /opt/xbt \
    && cd /opt/xbt/Tracker \
    && cmake . \
    && make \
    && mkdir -p /usr/local/bin /usr/local/share/xbt /etc/xbt \
    && cp /opt/xbt/Tracker/xbt_tracker /usr/local/bin/xbt_tracker \
    && cp /opt/xbt/Tracker/xbt_tracker.sql /usr/local/share/xbt/xbt_tracker.sql \
    && cp /opt/xbt/Tracker/xbt_tracker.conf.default /etc/xbt/xbt_tracker.conf

COPY tracker/entrypoint.sh /entrypoint.sh
RUN chmod +x /entrypoint.sh

EXPOSE 2710

ENTRYPOINT ["/entrypoint.sh"]
