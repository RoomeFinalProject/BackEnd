import os
import json

def convert_to_json(file_name, content, file_path):
    title = file_name
    content = content
    document_summary = {"title": title, "content": content}

    json_result = json.dumps({"document_summary": document_summary}, ensure_ascii=False, indent=2)

    # Change the file extension to .json
    file_name_with_extension = os.path.splitext(file_name)[0] + ".json"
    complete_file_path = os.path.join(file_path, file_name_with_extension)

    # Create the directory if it doesn't exist
    directory = os.path.dirname(complete_file_path)
    if not os.path.exists(directory):
        os.makedirs(directory)

    with open(complete_file_path, 'w', encoding='utf-8') as json_file:
        json_file.write(json_result)