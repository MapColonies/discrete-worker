discrete_schema = {
    "type": "object",
    "properties": {
        "id": {"type": "string"},
        "version": {"type": "string"},
        "tasks": {"type": "array"},
        "metadata": {"type": "object"}
    }
}

task_schema = {
    "type": "object",
    "properties": {
        "id": {"type": "string"},
        "status": {"type": "string"},
        "reason": {"type": "number"},
        "minZoom": {"type": "number"},
        "maxZoom": {"type": "number"}
    }
}
