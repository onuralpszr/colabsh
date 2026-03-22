---
tags:
  - Guide
  - Setup
---

# Installation

## Requirements

- Python 3.10 or later
- A web browser (for the Google Colab connection)

## Install

=== "pip"

    ```bash
    pip install colabsh
    ```

=== "uv"

    ```bash
    uv add colabsh
    ```

=== "uvx (no install)"

    ```bash
    uvx colabsh exec "print('hello')"
    ```

=== "From source"

    ```bash
    git clone https://github.com/onuralpszr/colabsh.git
    cd colabsh
    uv sync
    ```

## Optional dependencies

???+ info "QR code support"

    For QR code display in headless mode:

    === "pip"

        ```bash
        pip install colabsh[qr]
        ```

    === "uv"

        ```bash
        uv add colabsh[qr]
        ```

## Verify installation

```bash
colabsh --help
```

!!! success "Expected output"

    You should see the help text listing all available commands: `start`, `stop`, `status`, `exec`, `repl`, `download`, `tools`, and `history`.
