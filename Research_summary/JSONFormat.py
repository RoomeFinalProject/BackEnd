import os
import json

def convert_to_jsonformat(file_name, content):
    title = file_name
    content = content
    document_summary = {"title": title, "content": content}

    json_result = json.dumps({"document_summary": document_summary}, ensure_ascii=False, indent=2)
    
    return json_result