# Reference

- API endpoints
  - GET /api/health
  - GET /api/status
  - GET /api/stream (SSE)
  - POST /api/task { task, output_description? }
  - POST /api/enhance { text }
  - POST /api/shutdown

- Environment variables
  - WEB_GUI_PORT (default 8086)
  - OPEN_ROUTER_API_KEY (optional)
  - RESULTS_OUTPUT_PATH, EVENTS_OUTPUT_PATH

- CLI
  - mobile-use serve --port 8086
