---
tags:
  - Reference
  - Security
---

# Security

## What colabsh does

!!! success "Security measures"

    - Runs a **localhost-only** WebSocket server not accessible from the network
    - Uses a random **authentication token** for every session
    - Communicates with Google Colab via Google's MCP proxy protocol
    - Stores data locally in your [config directory](configuration.md) -nothing is sent to third parties

## What to be aware of

!!! warning "Important considerations"

    - The connection URL contains a secret token treat it like a password
    - Anyone with the URL can execute code in your Google's Colab session
    - The background server runs until you stop it (`colabsh stop`)
    - Code execution happens on Google's Colab VMs, subject to Google's terms of service
    - The Google Colab session has your Google account's permissions

## Token lifecycle

| Event           | Behavior                                                            |
| --------------- | ------------------------------------------------------------------- |
| `colabsh start` | A new random token is generated (16-byte URL-safe)                  |
| While running   | Token stored in config directory `server.json` (user-readable only) |
| `colabsh stop`  | Token is deleted                                                    |

## Authentication

The server validates incoming WebSocket connections using one of two methods:

!!! info "Authentication methods"

    === "URL query parameter"

        The token is embedded in the connection URL:

        ```
        wss://localhost:PORT?access_token=<token>
        ```

    === "Bearer token header"

        Standard HTTP authorization header:

        ```
        Authorization: Bearer <token>
        ```

    Connections without a valid token are rejected with **HTTP 403**.
