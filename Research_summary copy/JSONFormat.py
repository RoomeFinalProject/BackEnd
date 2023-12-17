import os
import json
from Loading2Sum import file_names
from datetime import datetime


def convert_to_jsonfile(file_name, content, file_path):
    title = file_name
    
    date = file_name.split('_')[-2]
    date_object = datetime.strptime(date, '%Y%m%d')
    formatted_date = date_object.strftime('%Y-%m-%d')
    
    content = content
    document_summary = {"title": title, "Date" : formatted_date, "Link" : "", "content": content}

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
        

def convert_to_jsonformat(file_name, content):
    title = file_name
    content = content
    document_summary = {"title": title, "content": content}

    json_result = json.dumps({"document_summary": document_summary}, ensure_ascii=False, indent=2)
    
    return json_result

if __name__ == '__main__':
    for file_name in file_names:
        
        break