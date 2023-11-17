def read_and_save_unique_urls_from_file(input_file_path, output_file_path):
    """
    Read URLs from a file, remove duplicates, and save the unique URLs to another file.
    """
    with open(input_file_path, 'r', encoding='utf-8') as file:
        unique_urls = set(line.strip() for line in file if line.strip())

    with open(output_file_path, 'w', encoding='utf-8') as file:
        for url in unique_urls:
            file.write(url + "\n")

    return f"Read and saved {len(unique_urls)} unique URLs from '{input_file_path}' to '{output_file_path}'"

# Replace these paths with the actual file paths on your system
input_file_path = 'data/london-rest-urls.txt'  # Path to the input file containing URLs
output_file_path = 'data/london-urls-unique.txt'  # Path to save the unique URLs

# Example usage
result = read_and_save_unique_urls_from_file(input_file_path, output_file_path)
#print(result)
