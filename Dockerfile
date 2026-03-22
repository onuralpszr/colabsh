FROM python:3.13-slim AS base

# Install system deps for Playwright Chromium
RUN apt-get update && apt-get install -y --no-install-recommends \
    libnss3 libatk1.0-0 libatk-bridge2.0-0 libcups2 libdrm2 \
    libxkbcommon0 libxcomposite1 libxdamage1 libxrandr2 libgbm1 \
    libpango-1.0-0 libcairo2 libasound2t64 libxshmfence1 \
    libx11-xcb1 libxcb-dri3-0 libxfixes3 \
    && rm -rf /var/lib/apt/lists/*

# Install colabsh with auto (Playwright) support
RUN pip install --no-cache-dir "colabsh[auto]" \
    && playwright install chromium

# Config and browser profile persist via volume
VOLUME ["/root/.config/colabsh"]

ENTRYPOINT ["colabsh"]
CMD ["start", "--auto"]

# ---- Usage ----
#
# Build:
#   docker build -t colabsh .
#
# First-time login (interactive, mount profile volume):
#   docker run -it -v colabsh-data:/root/.config/colabsh colabsh login
#
# Run with auto-connect:
#   docker run -d -v colabsh-data:/root/.config/colabsh -p 45000:45000 colabsh start --auto
#
# Reuse host Chrome profile (skip login):
#   docker run -d \
#     -v ~/.config/google-chrome:/chrome-profile:ro \
#     -v colabsh-data:/root/.config/colabsh \
#     colabsh start --auto --browser-profile /chrome-profile
#
# Execute code (connect to running container):
#   docker exec <container> colabsh exec "print('hello')"
