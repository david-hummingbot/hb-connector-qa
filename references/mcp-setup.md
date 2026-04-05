# hummingbot-mcp-docker Setup

Instruct the user to add the following entry to their MCP server configuration (e.g. `~/.gemini/settings.json` under `mcpServers`):
```json
"hummingbot-mcp-docker": {
  "command": "docker",
  "args": [
    "run",
    "--rm",
    "-i",
    "--network",
    "host",
    "-v",
    "hummingbot_mcp:/root/.hummingbot_mcp",
    "hummingbot/hummingbot-mcp:latest"
  ]
}
```
After adding it, ask the user to reload/restart their MCP client and then re-run this skill.
