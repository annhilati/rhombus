---
title: Frontend Reference
icon: lucide/ethernet-port
---

<h6>Last updated: 02.07.2026</h6>

# Preview Endpoints Architecture

The Rhombus Preview Frontend is designed to be completely decoupled from the specific backend generating the Minecraft resources. While the Rhombus Python package provides a default ASGI backend, anyone can build a custom backend (e.g., in Node.js, Go, or Rust) to serve data to the frontend, as long as it adheres to the following endpoint contracts.

All API interactions between the frontend and the backend are initiated by the frontend. The backend must expose a base URL (e.g., `http://127.0.0.1:8000`), and the frontend will append specific endpoint paths to fetch data and receive updates.

---

## 1. Data Snapshot Endpoint
**`GET /data`**

This is the primary endpoint for retrieving the generated Minecraft resources. The frontend fetches this endpoint whenever it connects or receives an update event.

### Request Details
- **Method:** `GET`
- **Headers:** `Accept: application/json`
- **Query Parameters:** `t` (Timestamp for cache-busting, e.g., `?t=1690000000000`)

### Response Format
The endpoint must return a `200 OK` status with a JSON object matching this schema:

```json
{
  "latest_data": [
    {
      "registry": "worldgen/density_function",
      "id": "namespace:example/id",
      "content": { ... },
      "language": "json"
    }
  ]
}
```

#### Fields:
- `latest_data` (Array, required): A list of files/resources available for preview.
  - `registry` (String, required): The namespace folder / registry path (e.g., `worldgen/noise_settings`).
  - `id` (String, required): The resource location / identifier (e.g., `minecraft:overworld`).
  - `content` (Any, required): The content of the file. If `language` is `"json"`, this can be a pre-parsed JSON object or a JSON string.
  - `language` (String, required): The language/format of the content (usually `"json"`).

---

## 2. Server-Sent Events (SSE) Endpoint
**`GET /events`**

To avoid constant polling, the frontend connects to an SSE stream to listen for file modifications. When the backend finishes regenerating resources, it should push an event to this stream, instructing the frontend to re-fetch `/data`.

### Request Details
- **Method:** `GET`
- **Headers:** Expects a persistent HTTP connection.

### Response Format
The endpoint must respond with the `text/event-stream` media type and keep the connection alive. 

When the backend data updates, it should emit the following payload to the stream:

```text
data: update\n\n
```

*Note: The frontend explicitly checks for the `data: update` message. Once received, it will automatically trigger a new request to `/data`.*

---

## 3. Addon Scripts Endpoint (Optional)
**`GET /addons/scripts`**

The frontend supports loading dynamic frontend scripts (Javascript or Typescript) injected by the backend. This is particularly useful for loading specific UI extensions, such as `deepslate.ts` for advanced 3D rendering or custom noise logic.

If your backend does not support addons, you can safely return a `404 Not Found` or an empty array `[]`. The frontend will gracefully ignore it.

### Request Details
- **Method:** `GET`

### Response Format
Returns a JSON array of script objects.

```json
[
  {
    "name": "deepslate.ts",
    "url": "/addons/scripts/0"
  },
  {
    "name": "custom-addon.js",
    "url": "/addons/scripts/custom"
  }
]
```

- `name` (String): The name of the script. If it ends with `.ts`, the frontend will transpile it using `sucrase` on the fly before execution.
- `url` (String): The path relative to the backend's base URL from which the frontend can download the raw script content.

---

## 4. Addon Script Content Endpoint (Optional)
**`GET {script.url}`**

If the `/addons/scripts` endpoint returned scripts, the frontend will subsequently request the raw content of each script using the provided `url`.

### Request Details
- **Method:** `GET`
- **Query Parameters:** `t` (Cache-busting timestamp)

### Response Format
Return the raw source code of the script. 
- Ensure the `Content-Type` header is set appropriately (e.g., `text/typescript` for `.ts` files or `application/javascript` for `.js` files).

## Summary Workflow

1. The frontend boots up and requests `GET /addons/scripts` to load any injected plugins.
2. It fetches `GET /data` to get the initial state of the resources.
3. It opens an SSE connection to `GET /events`.
4. When the backend regenerates files, it sends `data: update\n\n` through the `/events` stream.
5. The frontend responds by re-fetching `GET /data` and updating the UI instantly.
