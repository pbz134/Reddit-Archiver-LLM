import argparse

def filter_entries(input_file, output_file):
    with open(input_file, 'r', encoding='utf-8') as f:
        entries = [line.strip() for line in f.readlines() if line.strip()]
    
    # Sort by length (shortest first) to check shorter entries first
    entries_sorted = sorted(entries, key=len)
    
    to_keep = []
    
    for entry in entries_sorted:
        # Check if this entry is not a "superset" of any kept entry
        keep = True
        for kept in to_keep:
            if entry.startswith(kept) and (len(entry) > len(kept)):
                # Check if the next character after the kept entry is a space or special character
                next_char = entry[len(kept)]
                if not next_char.isalnum():  # if it's space or punctuation
                    keep = False
                    break
        if keep:
            to_keep.append(entry)
    
    # Write the filtered entries back to the output file
    with open(output_file, 'w', encoding='utf-8') as f:
        for entry in sorted(to_keep):  # sort alphabetically for output
            f.write(entry + '\n')

def main():
    parser = argparse.ArgumentParser(description='Filter text entries by removing entries that start with other existing entries.')
    parser.add_argument('-i', '--input', required=True, help='Input text file path')
    parser.add_argument('-o', '--output', required=True, help='Output text file path')
    
    args = parser.parse_args()
    
    filter_entries(args.input, args.output)
    print(f"Filtering complete. Results saved to {args.output}")

if __name__ == '__main__':
    main()