import json
import hashlib

def generate_context_hash(context: dict) -> str:
    """
    Generates a SHA256 hash for a given dictionary (context).
    The dictionary is serialized to a canonical JSON string (sorted keys)
    to ensure consistent hashing.
    """
    if not isinstance(context, dict):
        # Or raise an error, depending on how you want to handle non-dict inputs
        return hashlib.sha256("{}".encode('utf-8')).hexdigest() 
        
    try:
        # Sort keys for canonical representation
        context_string = json.dumps(context, sort_keys=True, ensure_ascii=False)
    except TypeError as e:
        # Fallback or error handling if context is not JSON serializable
        # For now, just use a generic string representation, but ideally this should be logged or handled
        # print(f"Warning: Could not serialize context to JSON for hashing: {e}")
        context_string = str(context)

    return hashlib.sha256(context_string.encode('utf-8')).hexdigest()
