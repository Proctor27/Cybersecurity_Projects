import json
from pathlib import Path
from base64_tool.encoders import encode, decode
from base64_tool.utils import decode_url, encode_url

# Map CyberChef operation names to internal Florence handlers
OP_MAP = {
    "To Base64": lambda data, args: encode(data, "base64"),
    "From Base64": lambda data, args: decode(data, "base64"),
    "URL Encode": lambda data, args: encode_url(data),
    "URL Decode": lambda data, args: decode_url(data),
}

def parse_cyberchef_recipe(recipe_path: Path) -> list[dict]:
    """Parse a CyberChef recipe JSON file."""
    content = recipe_path.read_text(encoding="utf-8")
    recipe_data = json.loads(content)
    # CyberChef format typically has an "op" and "args" list
    if isinstance(recipe_data, list):
        return recipe_data
    elif isinstance(recipe_data, dict) and "op" in recipe_data:
        return [recipe_data]
    raise ValueError("Invalid CyberChef recipe format.")

def execute_recipe(data: str, recipe_path: Path) -> str | bytes:
    """Execute a chain of operations defined in a CyberChef recipe."""
    operations = parse_cyberchef_recipe(recipe_path)
    current_data = data

    for op_info in operations:
        op_name = op_info.get("op")
        op_args = op_info.get("args", [])
        
        if op_name not in OP_MAP:
            raise NotImplementedError(f"CyberChef operation '{op_name}' is not supported by Florence yet.")
        
        # Run the operation handler
        current_data = OP_MAP[op_name](current_data, op_args)
        
        # Ensure string compatibility for text-based cascading steps if needed
        if isinstance(current_data, bytes):
            try:
                current_data = current_data.decode("utf-8")
            except UnicodeDecodeError:
                pass  # Keep as bytes if it's a raw binary payload

    return current_data