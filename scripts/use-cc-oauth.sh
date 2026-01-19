#!/usr/bin/env bash
# Script to borrow OAuth credentials from Claude Code
# Usage: ! use-cc-oauth [server-name]

CC_CREDS="$HOME/.claude/.credentials.json"
FACTORY_MCP="$HOME/.factory/mcp.json"

# check if Claude Code credentials exist
if [[ ! -f "$CC_CREDS" ]]; then
    echo "❌ Claude Code credentials not found at: $CC_CREDS"
    echo "Make sure Claude Code is installed and you've authenticated at least one MCP server with OAuth."
    exit 1
fi

# parse Claude Code's OAuth servers
get_oauth_servers() {
    python3 - "$CC_CREDS" <<'PYTHON'
import json, sys
from datetime import datetime

with open(sys.argv[1]) as f:
    data = json.load(f)

mcp_oauth = data.get("mcpOAuth", {})
if not mcp_oauth:
    print(json.dumps([]))
else:
    servers = []
    now = datetime.now().timestamp() * 1000

    for key, server_data in mcp_oauth.items():
        servers.append({
            "name": server_data.get("serverName", "unknown"),
            "url": server_data.get("serverUrl", ""),
            "token": server_data.get("accessToken", ""),
            "expired": server_data.get("expiresAt", 0) < now if server_data.get("expiresAt", 0) > 0 else False,
            "expires_at": server_data.get("expiresAt", 0)
        })
    
    print(json.dumps(servers))
PYTHON
}

SERVER_ARG="${1:-}"

# get OAuth servers
SERVERS_JSON=$(get_oauth_servers)

if [[ -z "$SERVERS_JSON" ]]; then
    echo "❌ Failed to parse OAuth servers"
    exit 1
fi

# check if empty
SERVER_COUNT=$(echo "$SERVERS_JSON" | python3 -c "import sys, json; print(len(json.load(sys.stdin)))" 2>/dev/null || echo "0")
if [[ "$SERVER_COUNT" == "0" ]]; then
    echo "❌ No OAuth servers found in Claude Code"
    echo "Authenticate at least one HTTP MCP server in Claude Code first."
    exit 1
fi

# if no server specified, list all
if [[ -z "$SERVER_ARG" ]]; then
    echo "OAuth Borrowing Tool: This command extracts OAuth credentials from Claude Code and generates Factory MCP configuration commands."
    echo ""
    echo "Available OAuth servers in Claude Code (these can be borrowed for Factory):"
    echo ""
    python3 -c "
import json
from datetime import datetime

servers = json.loads('''$SERVERS_JSON''')
for i, s in enumerate(servers, 1):
    status = 'EXPIRED' if s['expired'] else 'Valid'
    print(f\"{i}. {s['name']} - {s['url']} (Status: {status})\")
    if s['expired']:
        exp_dt = datetime.fromtimestamp(s['expires_at'] / 1000)
        print(f\"   Token expired on {exp_dt.strftime('%Y-%m-%d')} - re-authenticate in Claude Code first\")
"
    echo ""
    echo "Usage: /use-cc-oauth <server-name> to generate OAuth borrowing commands for a specific server."
    echo "This works by injecting Claude Code's OAuth token into Factory's MCP configuration via custom headers."
    exit 0
fi

# find specific server
echo "OAuth Borrowing: Extracting credentials for '$SERVER_ARG' from Claude Code to use in Factory."
echo ""

SERVER_DATA=$(python3 -c "
import json, sys
servers = json.loads('''$SERVERS_JSON''')
target = '$SERVER_ARG'.lower()
for s in servers:
    if s['name'].lower() == target:
        print(json.dumps(s))
        sys.exit(0)
")

if [[ -z "$SERVER_DATA" ]]; then
    echo "Server '$SERVER_ARG' not found in Claude Code OAuth credentials."
    echo "Available servers: $(echo "$SERVERS_JSON" | python3 -c "import sys,json; servers=json.load(sys.stdin); print(', '.join([s['name'] for s in servers]))")"
    echo "Run /use-cc-oauth without arguments to see full details."
    exit 1
fi

# extract server details
NAME=$(echo "$SERVER_DATA" | python3 -c "import sys, json; print(json.load(sys.stdin)['name'])")
URL=$(echo "$SERVER_DATA" | python3 -c "import sys, json; print(json.load(sys.stdin)['url'])")
TOKEN=$(echo "$SERVER_DATA" | python3 -c "import sys, json; print(json.load(sys.stdin)['token'])")
EXPIRED=$(echo "$SERVER_DATA" | python3 -c "import sys, json; print(json.load(sys.stdin)['expired'])")

if [[ "$EXPIRED" == "True" ]]; then
    echo "ERROR: The OAuth token for $NAME has expired."
    echo "Solution: Re-authenticate this server in Claude Code first, then retry this command."
    exit 1
fi

echo "Found valid OAuth token for $NAME (${TOKEN:0:25}...)"
echo "Server URL: $URL"
echo ""
echo "Generated Factory MCP configuration commands:"
echo "These commands will configure Factory to use Claude Code's OAuth token via custom Authorization header."
echo ""
echo "# Command 1: Remove existing configuration (if any)"
echo "droid mcp remove $NAME 2>/dev/null || true"
echo ""
echo "# Command 2: Add server with borrowed OAuth token"
echo "droid mcp add $NAME $URL --type http --header \"Authorization: Bearer $TOKEN\""
echo ""
echo "# Command 3: Verify the connection works"
echo "droid exec -m glm-4.6 --auto low \"list available $NAME mcp tools\""
echo ""
echo "Instructions: Copy and paste these commands one by one to configure Factory with the borrowed OAuth credentials."
echo "Note: This enables $NAME MCP server in Factory using Claude Code's approved OAuth token, bypassing client approval restrictions."
