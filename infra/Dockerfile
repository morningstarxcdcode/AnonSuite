FROM kalilinux/kali-rolling:latest

LABEL maintainer="morningstarxcdcode"
LABEL description="AnonSuite - Unified Security Toolkit"
LABEL version="2.0"

# Install system dependencies
RUN apt-get update && apt-get install -y \
    python3 \
    python3-pip \
    python3-venv \
    tor \
    privoxy \
    haproxy \
    polipo \
    wireless-tools \
    aircrack-ng \
    hostapd \
    dnsmasq \
    iptables \
    net-tools \
    iproute2 \
    sudo \
    make \
    gcc \
    libc6-dev \
    libssl-dev \
    && rm -rf /var/lib/apt/lists/*

# Create application user
RUN useradd -m -s /bin/bash anonsuite && \
    echo "anonsuite ALL=(ALL) NOPASSWD: ALL" >> /etc/sudoers

# Set working directory
WORKDIR /app

# Copy application files
COPY src/ /app/src/
COPY etc/ /app/etc/
COPY scripts/ /app/scripts/
COPY Makefile /app/

# Install Python dependencies
RUN pip3 install --no-cache-dir \
    click \
    colorama \
    psutil \
    pyyaml \
    requests

# Create necessary directories
RUN mkdir -p /var/log/anonsuite /tmp/anonsuite /etc/anonsuite && \
    chown -R anonsuite:anonsuite /var/log/anonsuite /tmp/anonsuite /etc/anonsuite

# Copy configuration templates
COPY etc/templates/ /etc/anonsuite/templates/

# Make scripts executable
RUN chmod +x /app/src/anonymity/multitor/multitor && \
    chmod +x /app/src/anonymity/anonsuite && \
    chmod +x /app/src/wifi/*.sh && \
    chmod +x /app/scripts/*.sh

# Switch to application user
USER anonsuite

# Set environment variables
ENV ANONSUITE_ENV=production
ENV ANONSUITE_LOG_LEVEL=info
ENV ANONSUITE_CONFIG_PATH=/etc/anonsuite
ENV PATH="/app/src:$PATH"

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD python3 /app/src/anonsuite.py --health-check || exit 1

# Default command
CMD ["python3", "/app/src/anonsuite.py"]
