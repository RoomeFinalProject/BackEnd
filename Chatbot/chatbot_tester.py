import time
from QueryingandPrompt import query_engine


def my_chatbot(text_input):
    start_time = time.time()
    response = query_engine.query(text_input)
    
    response_time = time.time() - start_time
    # Print the selected metadata
    print("Response Time: {:.2f} seconds".format(response_time)) 
    print("Response:", response) # print("Response:", response.response) 이렇게 하면 에러 발생 ..
    print("Response:", response.metadata) # print("Response:", response.response) 이렇게 하면 에러 발생 ..
    
    
    return response_time, 


if __name__ == "__main__":
    while True:
        text_input = input("User: ")
        if text_input.lower() == "exit":
            break
        my_chatbot(text_input)
