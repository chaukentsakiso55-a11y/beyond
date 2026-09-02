from infinity_os.contracts import ToolResult
def register(registry):
    registry.register("example.hello","Example plugin tool","",lambda:ToolResult(True,"Hello from an Infinity plugin"),source="example-system-info")
