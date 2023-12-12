import time
from QueryingandPrompt import query_engine


def my_chatbot(text_input):
    start_time = time.time()
    response = query_engine.query(text_input)
    response_time = time.time() - start_time
    print("Response Time: {:.2f} seconds".format(response_time)) 
    print("Response:", str(response.response)) # print("Response:", response.response) 이렇게 하면 에러 발생 ..
    print("Metadata:", response.metadata.values())
    
    return response_time, str(response.response), response.metadata.values()


if __name__ == "__main__":
    while True:
        text_input = input("User: ")
        if text_input.lower() == "exit":
            break
        my_chatbot(text_input)
