from ast import arguments, mod
import json
import os
from unittest import result

from dotenv import load_dotenv
from openai import OpenAI

from app.tools import TOOL_SCHEMAS, ToolExecutor

load_dotenv()

class TravelPlanner:
    def __init__(self) -> None:
        self.client = OpenAI()
        self.model = os.getenv(
            "OPENAI_MODEL"
        )

        self.tool_executor = ToolExecutor()
        self.max_tool_calls = 5

    def plan(self, request: str):
        input_items = [
            {
                "role": "user",
                "content": request
            }
        ]

        tool_calls_used = 0
        trace = []

        while True:
            
            response = self.client.responses.create(
            model=self.model,
            input=input_items,
            tools=TOOL_SCHEMAS,
            instructions="""
                You are a travel planning assistant.

                Use tools whenever you need factual travel information.

                Treat tool results as the source of truth.
                Do not invent factual details that are not present
                in tool results.

                When you have enough information,
                provide a useful travel recommendation.
                """
            )
            
            input_items += response.output
            
            function_calls = [
                item 
                for item in response.output
                if item.type == "function_call"
            ]
            
            if not function_calls:
                return {
                    "response": response.output_text,
                    "tool_calls_used": tool_calls_used,
                    "trace": trace
                    }
            
            for call in function_calls:
                if tool_calls_used >= self.max_tool_calls:
                    return {
                        "response": "Tool-call limit reached",
                        "tool_calls_used": tool_calls_used,
                        "trace": trace
                    }

                arguments = json.loads(
                    call.arguments
                    )
                
                result = self.tool_executor.execute(call.name, arguments)

                tool_calls_used += 1

                trace.append(
                    {
                        "step": tool_calls_used,
                        "tool": call.name,
                        "arguments": arguments,
                        "result": result
                    }
                )
            
                input_items.append({
                    "type": "function_call_output",
                    "call_id": call.call_id,
                    "output": json.dumps(result)
                    }
                )