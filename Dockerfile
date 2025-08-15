# AnonSuite Docker Container
# Multi-stage build for optimized production image

FROM python:3.11-slim as builder

# Set build arguments
ARG BUILD_DATE
ARG VCS_REF
ARG VERSION=2.0.0

# Add metadata
LABEL org.opencontainers.image.title="AnonSuite"
LABEL org.opencontainers.image.description="Unified Security Toolkit for Privacy Professionals"
LABEL org.opencontainers.image.version="${VERSION}"
LABEL org.opencontainers.image.created="${BUILD_DATE}"
LABEL org.opencontainers.image.revision="${VCS_REF}"
LABEL org.opencontainers.image.source="https://github.com/morningstarxcdcode/AnonSuite"
LABEL org.opencontainers.image.url="https://github.com/morningstarxcdcode/AnonSuite"
LABEL org.opencontainers.image.documentation="https://github.com/morningstarxcdcode/AnonSuite/docs"
LABEL org.opencontainers.image.licenses="MIT"
LABEL maintainer="morningstarxcdcode"

# Install system dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    git \
    curl \
    wget \
    && rm -rf /var/lib/apt/lists/*

# Set up Python environment
WORKDIR /app
COPY requirements.txt requirements-dev.txt ./

# Install Python dependencies
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt

# Production stage
FROM python:3.11-slim as production

# Install runtime system dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    tor \
    privoxy \
    wireless-tools \
    net-tools \
    iproute2 \
    procps \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Create non-root user for security
RUN groupadd -r anonsuite && useradd -r -g anonsuite -d /app -s /bin/bash anonsuite

# Set up application directory
WORKDIR /app

# Copy Python dependencies from builder
COPY --from=builder /usr/local/lib/python3.11/site-packages /usr/local/lib/python3.11/site-packages
COPY --from=builder /usr/local/bin /usr/local/bin

# Copy application code
COPY --chown=anonsuite:anonsuite . .

# Create necessary directories
RUN mkdir -p /app/config /app/run /app/log /app/plugins /tmp/anonsuite && \
    chown -R anonsuite:anonsuite /app /tmp/anonsuite

# Set up configuration
RUN chmod +x install.sh && \
    chmod +x src/anonymity/multitor/multitor && \
    chmod +x src/anonymity/multitor/__init__ && \
    chmod +x src/anonymity/multitor/CreateTorProcess && \
    chmod +x src/anonymity/multitor/CreateProxyProcess

# Configure Tor for container environment
RUN echo "SocksPort 0.0.0.0:9000" >> /etc/tor/torrc && \
    echo "ControlPort 0.0.0.0:9001" >> /etc/tor/torrc && \
    echo "CookieAuthentication 1" >> /etc/tor/torrc && \
    echo "DataDirectory /tmp/tor" >> /etc/tor/torrc

# Configure Privoxy for container environment
RUN echo "listen-address 0.0.0.0:8119" >> /etc/privoxy/config && \
    echo "forward-socks5 / 127.0.0.1:9000 ." >> /etc/privoxy/config

# Switch to non-root user
USER anonsuite

# Set environment variables
ENV PYTHONPATH=/app/src
ENV ANONSUITE_CONFIG_DIR=/app/config
ENV ANONSUITE_DATA_DIR=/app/run
ENV ANONSUITE_LOG_DIR=/app/log

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD python src/anonsuite.py --health-check || exit 1

# Expose ports
EXPOSE 9000 9001 8119

# Default command
CMD ["python", "src/anonsuite.py"]

# Development stage
FROM production as development

USER root

# Install development dependencies
COPY requirements-dev.txt .
RUN pip install --no-cache-dir -r requirements-dev.txt

# Install additional development tools
RUN apt-get update && apt-get install -y --no-install-recommends \
    vim \
    nano \
    htop \
    tcpdump \
    nmap \
    && rm -rf /var/lib/apt/lists/*

USER anonsuite

# Development command
CMD ["python", "src/anonsuite.py", "--demo"]
