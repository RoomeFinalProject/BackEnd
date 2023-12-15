import time
from .QueryingandPrompt import query_engine


def my_chatbot(text_input):
    start_time = time.time()
    response = query_engine.query(text_input)
    
    if response.metadata is not None:
        selected_metadata = [{'page_label': metadata['page_label'], 'file_name': metadata['file_name']} for metadata in response.metadata.values()]
    else:
        selected_metadata = 'Reference가 없습니다.'
    response_time = time.time() - start_time
    # Print the selected metadata
    print("Response Time: {:.2f} seconds".format(response_time)) 
    print("Response:", str(response.response)) # print("Response:", response.response) 이렇게 하면 에러 발생 ..
    print("Selected Metadata:", selected_metadata)
    
    
    return response_time, str(response.response), selected_metadata


if __name__ == "__main__":
    while True:
        text_input = input("User: ")
        if text_input.lower() == "exit":
            break
        my_chatbot(text_input)
