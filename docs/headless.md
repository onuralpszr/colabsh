---
tags:
  - Guide
  - SSH
  - CLI
---

# Headless mode

For SSH sessions, containers, or remote machines where there's no desktop
browser.

## Usage

```bash
colabsh start --headless
```

This prints the connection URL instead of opening a browser. Open the URL on the
same machine in any browser.

## SSH port forwarding

To use colabsh on a remote server:

!!! example "Step-by-step"

    === "1. Remote server"

        Start colabsh in headless mode:

        ```bash
        colabsh start --headless
        ```

        Output:
        ```
        https://colab.research.google.com/notebooks/empty.ipynb#mcpProxyToken=...&mcpProxyPort=45123
        ```

    === "2. Local machine"

        Forward the port:

        ```bash
        ssh -L 45123:localhost:45123 remote-server
        ```

        Then open the printed URL in your local browser.

    === "3. Run commands"

        Back on the remote server, run commands as usual:

        ```bash
        colabsh exec "print('running on remote')"
        ```

## QR code

For easier URL transfer, use the `--qr` flag:

```bash
colabsh start --qr
```

This prints an ASCII QR code alongside the URL.

!!! note "Requires optional dependency"

    ```bash
    pip install colabsh[qr]
    ```

## Why not LAN or phone access?

!!! warning "localhost only"

    Google Colab's frontend JavaScript **always connects WebSocket to `localhost`** this is hardcoded in Google's code. When you open the URL on a different device (phone, another computer), the browser tries to connect to `localhost` on *that* device, which doesn't have the colabsh server.

    The only way to use colabsh from a different machine is **SSH port forwarding**, which makes the remote port appear as `localhost` on your local machine.
