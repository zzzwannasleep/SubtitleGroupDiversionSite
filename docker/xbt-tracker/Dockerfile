FROM debian:bookworm-slim

ENV DEBIAN_FRONTEND=noninteractive

RUN apt-get update \
    && apt-get install -y --no-install-recommends \
        build-essential \
        ca-certificates \
        cmake \
        gettext-base \
        git \
        libboost-all-dev \
        libmariadb-dev \
        libmariadb-dev-compat \
        libsystemd-dev \
        netcat-openbsd \
        pkg-config \
        zlib1g-dev \
    && rm -rf /var/lib/apt/lists/*

RUN git clone --depth 1 https://github.com/OlafvdSpek/xbt.git /src/xbt

WORKDIR /src/xbt/Tracker
RUN cmake -S . -B build -DCMAKE_BUILD_TYPE=Release \
    && cmake --build build --config Release -- -j"$(nproc)"

COPY entrypoint.sh /usr/local/bin/xbt-entrypoint.sh
COPY xbt_tracker.conf.template /etc/xbt/xbt_tracker.conf.template

RUN chmod +x /usr/local/bin/xbt-entrypoint.sh

EXPOSE 2710 6881/udp

ENTRYPOINT ["/usr/local/bin/xbt-entrypoint.sh"]
