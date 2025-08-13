import os
import json
from collections import defaultdict

def merge_and_deduplicate_files(input_dir, output_file):
    """
    Merge all JSON files in input_dir into a single JSON file,
    removing duplicate posts (based on 'id') and their comments.
    """
    # Dictionary to store posts by their ID for deduplication
    posts_by_id = {}
    
    # Counters for statistics
    total_files = 0
    total_posts = 0
    duplicate_posts = 0
    
    # Walk through the input directory
    for root, _, files in os.walk(input_dir):
        for filename in files:
            if filename.endswith('.txt'):
                filepath = os.path.join(root, filename)
                try:
                    with open(filepath, 'r', encoding='utf-8') as f:
                        data = json.load(f)
                        total_files += 1
                        
                        for post in data:
                            post_id = post['id']
                            total_posts += 1
                            
                            # If we haven't seen this post before, add it
                            if post_id not in posts_by_id:
                                posts_by_id[post_id] = post
                            else:
                                duplicate_posts += 1
                                
                except (json.JSONDecodeError, UnicodeDecodeError) as e:
                    print(f"Error reading {filepath}: {e}")
                except Exception as e:
                    print(f"Unexpected error processing {filepath}: {e}")
    
    # Convert the dictionary values to a list for the final output
    merged_posts = list(posts_by_id.values())
    
    # Save the merged and deduplicated data
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(merged_posts, f, indent=2, ensure_ascii=False)
    
    # Print statistics
    print(f"Processed {total_files} files with {total_posts} total posts")
    print(f"Found {duplicate_posts} duplicate posts")
    print(f"Saved {len(merged_posts)} unique posts to {output_file}")

if __name__ == '__main__':
    input_directory = './search-results'
    output_filename = './archive.json'
    
    if not os.path.exists(input_directory):
        print(f"Error: Input directory '{input_directory}' does not exist")
        exit(1)
    
    print(f"Merging files from '{input_directory}'...")
    merge_and_deduplicate_files(input_directory, output_filename)
    print("Done!")