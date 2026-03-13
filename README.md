# Wrangler-Desktop

A simple PySide6 GUI for Cloudflare's Wrangler CLI.

## Prerequisites

1.  **Node.js and npm**: You must have Node.js and npm installed.
2.  **Wrangler**: Install Wrangler CLI globally.
    ```bash
    npm install -g wrangler
    ```

## How to Run

1.  **Clone the repository**
    ```bash
    git clone <repository-url>
    cd Wrangler-Desktop
    ```

2.  **Install Python dependencies**
    ```bash
    pip install -r requirements.txt
    ```

3.  **Run the application**
    ```bash
    python main.py
    ```

## Features (MVP)

*   GUI wrapper for `wrangler` commands.
*   Real-time output from the CLI.
*   Buttons for `wrangler login`, `wrangler dev`, and `wrangler deploy`.
*   Cloudflare-inspired UI theme.
