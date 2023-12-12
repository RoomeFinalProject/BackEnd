from JSONFormat import convert_to_jsonformat
from llama_index.indices.document_summary import DocumentSummaryIndex
from PromptandSum import doc_summary_index
from Loading import file_names

def summary_list(file_names):
    summary_list = []
    for file_name in file_names:
        content = doc_summary_index.get_document_summary(f"{file_name}")
        json_result = convert_to_jsonformat(file_name, content)
        summary_list.append(json_result)
    return summary_list

if __name__ == 'main':
    summary_list(file_names)


