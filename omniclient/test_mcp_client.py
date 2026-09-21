#!/usr/bin/env python3
"""
MCP Client di test per Omninode

Testa i 4 tools MCP esponibili dal server Omninode:
- list_nodes
- get_node_status
- dispatch_task
- get_fabric_health

Utilizzo:
    python test_mcp_client.py [--stdio | --sse]
"""

import json
import subprocess
import sys
import requests
from typing import Any


class MCPClient:
    """Client MCP semplificato per testare il server Omninode"""

    def __init__(self, mode: str = "stdio"):
        self.mode = mode
        self.request_id = 0

    def _next_id(self) -> int:
        self.request_id += 1
        return self.request_id

    def call_tool_stdio(self, tool_name: str, arguments: dict = None) -> Any:
        """Chiama un tool MCP via stdio (esecuzione locale)"""
        # Build richiesta MCP
        request = {
            "jsonrpc": "2.0",
            "id": self._next_id(),
            "method": "tools/call",
            "params": {
                "name": tool_name,
                "arguments": arguments or {}
            }
        }

        # Avvia il server in modalità stdio
        proc = subprocess.Popen(
            ["./omniclient", "--mcp-stdio"],
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True
        )

        # Invia richiesta
        request_str = json.dumps(request) + "\n"
        proc.stdin.write(request_str)
        proc.stdin.flush()

        # Leggi risposta
        response_line = proc.stdout.readline()
        response = json.loads(response_line)

        proc.terminate()

        if "error" in response:
            raise Exception(f"MCP Error: {response['error']}")

        return response.get("result", {})

    def call_tool_sse(self, tool_name: str, arguments: dict = None, base_url: str = "http://localhost:8080") -> Any:
        """Chiama un tool MCP via SSE (server remoto)"""
        # Nota: questa è una implementazione semplificata
        # Per SSE reale serve gestire lo stream eventi
        url = f"{base_url}/mcp"

        request = {
            "jsonrpc": "2.0",
            "id": self._next_id(),
            "method": "tools/call",
            "params": {
                "name": tool_name,
                "arguments": arguments or {}
            }
        }

        response = requests.post(url, json=request, headers={"Content-Type": "application/json"})
        response.raise_for_status()

        data = response.json()
        if "error" in data:
            raise Exception(f"MCP Error: {data['error']}")

        return data.get("result", {})

    def call_tool(self, tool_name: str, arguments: dict = None) -> Any:
        """Chiama un tool MCP nel modo configurato"""
        if self.mode == "stdio":
            return self.call_tool_stdio(tool_name, arguments)
        else:
            return self.call_tool_sse(tool_name, arguments)


def test_list_nodes(client: MCPClient):
    """Test: lista tutti i nodi"""
    print("\n" + "="*50)
    print("TEST: list_nodes")
    print("="*50)

    result = client.call_tool("list_nodes")
    print(json.dumps(result, indent=2))
    return result


def test_get_node_status(client: MCPClient):
    """Test: ottieni stato di un nodo specifico"""
    print("\n" + "="*50)
    print("TEST: get_node_status (node_id='gateway')")
    print("="*50)

    result = client.call_tool("get_node_status", {"node_id": "gateway"})
    print(json.dumps(result, indent=2))
    return result


def test_dispatch_task(client: MCPClient):
    """Test: invia un task a un nodo"""
    print("\n" + "="*50)
    print("TEST: dispatch_task")
    print("="*50)

    result = client.call_tool("dispatch_task", {
        "node_id": "node-1",
        "task_type": "compute",
        "payload": {
            "operation": "sum",
            "values": [1, 2, 3, 4, 5]
        }
    })
    print(json.dumps(result, indent=2))
    return result


def test_get_fabric_health(client: MCPClient):
    """Test: ottieni salute del fabric"""
    print("\n" + "="*50)
    print("TEST: get_fabric_health")
    print("="*50)

    result = client.call_tool("get_fabric_health")
    print(json.dumps(result, indent=2))
    return result


def main():
    mode = "stdio"
    if len(sys.argv) > 1:
        if sys.argv[1] == "--sse":
            mode = "sse"
        elif sys.argv[1] == "--stdio":
            mode = "stdio"

    print(f"MCP Client Test - Modalità¹¹ {mode}")
    print(f"Server: Omninode MCP Server")
    print(f"Tools: list_nodes, get_node_status, dispatch_task, get_fabric_health")

    client = MCPClient(mode=mode)

    try:
        # Esegui tutti i test
        test_list_nodes(client)
        test_get_node_status(client)
        test_dispatch_task(client)
        test_get_fabric_health(client)

        print("\n" + "="*50)
        print("✅ TUTTI I TEST COMPLETATI CON SUCCESSO")
        print("="*50)

    except Exception as e:
        print(f"\n❌ ERRORE: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
