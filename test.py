def extract_date(line):
    # Assuming the date format is consistent and always at the beginning of the line
    date_str = line.split(' | ')[0]
    return date_str

# Example usage
before_function = """2023/11/28 | 이안나이현수
2023/11/20 | 이승은
2023/11/15 | 기업분석팀"""

# Split the input into lines
lines = before_function.split('\n')

# Apply the function to each line
after_function = [extract_date(line) for line in lines if line]

# Print the result
for date in after_function:
    print(date)