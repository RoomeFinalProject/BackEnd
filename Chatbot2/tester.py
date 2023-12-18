import os

# Set the path to the directory
BackEnd_directory = os.path.dirname(os.path.abspath(os.path.dirname(os.path.abspath(__file__))))
test_data_path = os.path.join(BackEnd_directory, 'data', 'testdata')
file_names = os.listdir(test_data_path)
for file_name in file_names:
    print(file_name)