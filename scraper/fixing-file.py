def replace_text_in_file(input_file_path, output_file_path):
    with open(input_file_path, 'r') as file:
        lines = file.readlines()

    modified_lines = [line.replace('//gb/', '/gb/') for line in lines]

    with open(output_file_path, 'w') as file:
        file.writelines(modified_lines)

input_file_path = './data/london-categories.txt'  # Replace with your input file path
output_file_path = 'london-cat.txt'      # Replace with your desired output file path
replace_text_in_file(input_file_path, output_file_path)
