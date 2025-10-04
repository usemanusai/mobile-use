## Mobile-Use Web GUI

This Web GUI provides a modern, ChatGPT-style interface for composing tasks, monitoring real-time progress, and viewing results.

- Default URL: http://localhost:8086
- Configure the port via `WEB_GUI_PORT` in your `.env` (host port is mapped 1:1).

### Launch

- Windows: `powershell.exe -ExecutionPolicy Bypass -File mobile-use.ps1`
- macOS/Linux: `bash ./mobile-use.sh` (coming soon)

The script will:
- Detect a device and set ADB connection
- Start the Docker container with ports exposed
- Launch the Web GUI in your default browser
- Initialize the agent only after you submit a task

### Using the GUI

- Enter a task in the text area
- Optionally add an Output Description (e.g., "Return a JSON with keys: sender, subject")
- Click Enhance to rewrite your task for clarity (rate-limited)
- Click Send to enqueue the task for execution
- Watch real-time status updates and agent thoughts

### Persistent loop mode

- The agent is initialized once and then waits for new tasks.
- Tasks are queued and run sequentially; the GUI shows "Waiting for next task" when idle.
- The Docker container and agent stay alive across tasks.
- Use the optional `/api/shutdown` endpoint to stop the agent gracefully.

### Real-time updates

- The GUI connects via Server-Sent Events (SSE) to stream:
  - Status changes (Initializing, Ready, Executing, Waiting, Error)
  - Task lifecycle events (queued, dequeued, start, end)
  - Agent node updates (planner, orchestrator, cortex, executor)
  - Agent thoughts and final outputs

### Security and privacy

- The server binds to 0.0.0.0 inside the container and is mapped to 127.0.0.1 on your host.
- Inputs are sanitized in the browser; avoid pasting secrets.
- The Enhance endpoint uses your configured OpenRouter key if present; otherwise it is a no-op echo.

### Troubleshooting

- If the browser opens before the server is ready, the page will connect automatically a few seconds later.
- Ensure port 8086 is free on your host, or set `WEB_GUI_PORT` in `.env` and re-run.
- If no device is found, the agent will fail to initialize when you send the first task.

