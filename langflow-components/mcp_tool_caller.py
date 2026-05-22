from langflow.interface.custom.custom_component import CustomComponent
from langflow.field_typing import Data
import httpx
import json

class MCPToolCallerComponent(CustomComponent):
    display_name = "MCP Tool Caller"
    description = "Ruft ein Fußball-Expertentool von einem MCP-Server via HTTP auf."
    icon = "Activity"

    def build_config(self):
        return {
            "mcp_url": {
                "display_name": "MCP Server URL",
                "value": "http://mcp-server:9000",
                "info": "Die Basis-URL des laufenden MCP-Servers."
            },
            "tool_name": {
                "display_name": "Tool Name",
                "options": [
                    "get_matches", 
                    "get_opponents", 
                    "get_team_elo", 
                    "compare_teams", 
                    "get_elo_trend", 
                    "simulate_tournament", 
                    "search_news"
                ],
                "info": "Name des aufzurufenden Tools."
            },
            "parameters": {
                "display_name": "Parameter (JSON)",
                "info": "Die Parameter für das Tool als JSON-String. Z.B. {\"team\": \"Deutschland\"}",
                "value": "{\"team\": \"Deutschland\"}"
            }
        }

    def build(self, mcp_url: str, tool_name: str, parameters: str) -> Data:
        try:
            params = json.loads(parameters) if parameters else {}
        except Exception as e:
            return Data(
                value=f"Fehler beim Parsen der Parameter als JSON: {e}",
                data={"error": str(e)}
            )
        
        try:
            response = httpx.post(
                f"{mcp_url}/call", 
                json={"tool": tool_name, "parameters": params}, 
                timeout=30.0
            )
            response.raise_for_status()
            res_json = response.json()
            result = res_json.get("result", {})
            
            # Formatierte Textdarstellung erzeugen
            if isinstance(result, dict) and "summary" in result:
                text_val = result["summary"]
                if "bar_chart" in result:
                    text_val += "\n\n" + result["bar_chart"]
            elif isinstance(result, dict) and "bar_chart" in result:
                text_val = result["bar_chart"]
            else:
                text_val = json.dumps(result, ensure_ascii=False, indent=2)
                
            return Data(
                value=text_val,
                data=result
            )
        except Exception as e:
            error_msg = f"Fehler beim Aufruf von MCP-Tool '{tool_name}' an {mcp_url}: {e}"
            return Data(
                value=error_msg,
                data={"error": str(e)}
            )
