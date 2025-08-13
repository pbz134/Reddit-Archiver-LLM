import json
import argparse
from pathlib import Path
from transformers import pipeline
import re
from tqdm import tqdm

def initialize_ner_model():
    """Initialize the Named Entity Recognition model"""
    print("Loading NLP model...")
    return pipeline("ner", model="dbmdz/bert-large-cased-finetuned-conll03-english", 
                  aggregation_strategy="simple", device=0)  # device=0 for GPU

def extract_key_terms(text, ner_model):
    """Extract key terms using NER and custom filtering"""
    if not text.strip():
        return set()
    
    # Process text with NER model
    entities = ner_model(text)
    
    # Extract unique terms
    terms = set()
    for entity in entities:
        if entity['score'] > 0.8:  # Only high-confidence entities
            term = entity['word'].strip()
            # Filter out common words and simple punctuation
            if (len(term) > 2 and 
                not term.lower() in {'the', 'and', 'for', 'you', 'this', 'that', 'with', 'have', 'has'} and
                not re.match(r'^[\W\d_]+$', term)):
                terms.add(term)
    
    return terms

def process_content(content, ner_model, pbar=None):
    """Process content chunks and extract terms"""
    all_terms = set()
    
    # Process in chunks (adjust based on your memory constraints)
    chunk_size = 2000  # Increased chunk size for better performance
    chunks = [content[i:i+chunk_size] for i in range(0, len(content), chunk_size)]
    
    for chunk in chunks:
        terms = extract_key_terms(chunk, ner_model)
        all_terms.update(terms)
        if pbar:
            pbar.update(len(chunk))
    
    return all_terms

def main():
    parser = argparse.ArgumentParser(description='Extract key terms from a subreddit JSON file')
    parser.add_argument('-i', '--input', required=True, help='Input JSON file')
    parser.add_argument('-o', '--output', required=True, help='Output text file')
    args = parser.parse_args()
    
    # Initialize NER model
    try:
        ner_model = initialize_ner_model()
    except Exception as e:
        print(f"Error loading model: {e}")
        return
    
    # Read input JSON file
    try:
        with open(args.input, 'r', encoding='utf-8') as f:
            data = json.load(f)
    except Exception as e:
        print(f"Error loading input file: {e}")
        return
    
    # Calculate total content size for progress bar
    total_size = sum(
        len(post.get('title', '')) + 
        len(post.get('selftext', '')) + 
        sum(len(comment.get('body', '')) for comment in post.get('comments', []))
        for post in data
    )
    
    # Extract terms from all relevant fields
    all_terms = set()
    
    with tqdm(total=total_size, unit='char', desc="Processing content") as pbar:
        for post in data:
            # Process title
            if 'title' in post and post['title']:
                all_terms.update(process_content(post['title'], ner_model, pbar))
            
            # Process selftext
            if 'selftext' in post and post['selftext']:
                all_terms.update(process_content(post['selftext'], ner_model, pbar))
            
            # Process comments
            if 'comments' in post and post['comments']:
                for comment in post['comments']:
                    if 'body' in comment and comment['body']:
                        all_terms.update(process_content(comment['body'], ner_model, pbar))
    
    # Write to output file
    try:
        with open(args.output, 'w', encoding='utf-8') as f:
            for term in sorted(all_terms):
                f.write(term + '\n')
        print(f"\nSuccessfully wrote {len(all_terms)} key terms to '{args.output}'")
    except Exception as e:
        print(f"\nError writing output file: {e}")

if __name__ == '__main__':
    main()