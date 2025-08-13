import os
import json
import requests
import praw
from urllib.parse import urlparse
from datetime import datetime
import time

# Configuration
REDDIT_CLIENT_ID = 'axpuodBt4YCmRabQX6NVpw'
REDDIT_SECRET = '_8qmePmBYRzlkmHzEMBl9fnwiyavXw'
REDDIT_USER_AGENT = 'SubredditArchiver/1.0'
POST_LIMIT = 1000
COMMENT_LIMIT = 500

def ensure_directories(subreddit_name, search_query):
    """Ensure all necessary directories exist."""
    # Sanitize both subreddit name and search query
    safe_subreddit = sanitize_filename(subreddit_name)
    safe_query = sanitize_filename(search_query.lower().replace(' ', '_'))
    
    # Main results directory
    os.makedirs('./search-results', exist_ok=True)
    
    # Media directories
    media_base = os.path.join('./search-results', 'media', safe_subreddit, safe_query)
    try:
        os.makedirs(os.path.join(media_base, 'images'), exist_ok=True)
        os.makedirs(os.path.join(media_base, 'videos'), exist_ok=True)
    except OSError as e:
        print(f"Error creating media directories: {e}")
        media_base = os.path.join('./search-results', 'media', safe_subreddit, 'default')
        os.makedirs(os.path.join(media_base, 'images'), exist_ok=True)
        os.makedirs(os.path.join(media_base, 'videos'), exist_ok=True)
        print(f"Using fallback directory: {media_base}")
    return media_base

def sanitize_filename(filename):
    """Sanitize the filename to remove invalid characters."""
    invalid_chars = '<>:"/\\|?*'
    for char in invalid_chars:
        filename = filename.replace(char, '_')
    # Remove trailing periods/spaces (Windows doesn't like these)
    filename = filename.rstrip('. ')
    return filename[:200]  # Limit filename length

def download_file(url, filepath):
    """Download a file from a URL and save it to the specified path."""
    try:
        response = requests.get(url, stream=True)
        response.raise_for_status()
        
        with open(filepath, 'wb') as f:
            for chunk in response.iter_content(chunk_size=8192):
                if chunk:
                    f.write(chunk)
        return True
    except Exception as e:
        print(f"Failed to download {url}: {e}")
        return False

def process_gallery(post, media_dir):
    """Process a gallery post and download all images."""
    gallery_items = []
    
    try:
        if hasattr(post, 'media_metadata'):
            for idx, (media_id, media_item) in enumerate(post.media_metadata.items()):
                image_url = None
                # Find the highest resolution image
                if 's' in media_item and 'u' in media_item['s']:
                    image_url = media_item['s']['u']
                elif 'p' in media_item and len(media_item['p']) > 0:
                    image_url = media_item['p'][-1]['u']
                
                if image_url:
                    # Parse URL to get extension
                    parsed = urlparse(image_url)
                    ext = os.path.splitext(parsed.path)[1]
                    if not ext:
                        ext = '.jpg'  # default extension if none found
                    
                    filename = f"gallery_{post.id}_{idx}{ext}"
                    filepath = os.path.join(media_dir, 'images', filename)
                    
                    if download_file(image_url, filepath):
                        gallery_items.append(filepath)
    
    except Exception as e:
        print(f"Error processing gallery for post {post.id}: {e}")
    
    return gallery_items

def process_media(post, media_dir):
    """Process media (images/videos) from a post."""
    media_path = None
    is_gallery = False
    
    # Check for image
    if hasattr(post, 'url') and post.url:
        url = post.url
        parsed = urlparse(url)
        path = parsed.path.lower()
        
        # Handle direct image links
        if path.endswith(('.jpg', '.jpeg', '.png', '.gif')):
            ext = os.path.splitext(path)[1]
            filename = f"{post.id}{ext}"
            filepath = os.path.join(media_dir, 'images', filename)
            
            if download_file(url, filepath):
                media_path = filepath
        
        # Handle imgur links (simple ones)
        elif 'imgur.com' in parsed.netloc and not url.endswith('/'):
            imgur_url = url + '.jpg'
            filename = f"{post.id}.jpg"
            filepath = os.path.join(media_dir, 'images', filename)
            
            if download_file(imgur_url, filepath):
                media_path = filepath
        
        # Handle reddit video
        elif 'v.redd.it' in parsed.netloc:
            try:
                if hasattr(post, 'media') and post.media and 'reddit_video' in post.media:
                    video_url = post.media['reddit_video']['fallback_url']
                    filename = f"{post.id}.mp4"
                    filepath = os.path.join(media_dir, 'videos', filename)
                    
                    if download_file(video_url, filepath):
                        media_path = filepath
            except Exception as e:
                print(f"Error processing video for post {post.id}: {e}")
    
    # Check for gallery
    if hasattr(post, 'is_gallery') and post.is_gallery:
        gallery_items = process_gallery(post, media_dir)
        if gallery_items:
            media_path = gallery_items
            is_gallery = True
    
    return media_path, is_gallery

def search_subreddit(subreddit_name, search_query):
    """Search posts in a subreddit and save results + media."""
    # Create all necessary directories
    media_dir = ensure_directories(subreddit_name, search_query)
    
    # Initialize Reddit client
    reddit = praw.Reddit(
        client_id=REDDIT_CLIENT_ID,
        client_secret=REDDIT_SECRET,
        user_agent=REDDIT_USER_AGENT
    )
    
    posts_data = []
    post_count = 0
    
    try:
        subreddit = reddit.subreddit(subreddit_name)
        
        # Perform the search
        search_results = subreddit.search(search_query, limit=POST_LIMIT, sort='relevance')
        
        # Process search results
        for post in search_results:
            try:
                post_data = {
                    'id': post.id,
                    'title': post.title,
                    'author': str(post.author),
                    'score': post.score,
                    'created_utc': post.created_utc,
                    'num_comments': post.num_comments,
                    'permalink': post.permalink,
                    'url': post.url,
                    'selftext': post.selftext,
                    'is_self': post.is_self,
                    'over_18': post.over_18,
                    'saved_at': datetime.utcnow().timestamp(),
                    'search_query': search_query
                }
                
                # Process and download media
                media_path, is_gallery = process_media(post, media_dir)
                if media_path:
                    post_data['local_media'] = media_path
                    post_data['is_gallery'] = is_gallery
                
                # Get comments
                post.comment_sort = 'top'
                post.comment_limit = COMMENT_LIMIT
                comments = []
                
                for comment in post.comments:
                    if isinstance(comment, praw.models.MoreComments):
                        continue
                    
                    comment_data = {
                        'id': comment.id,
                        'author': str(comment.author),
                        'body': comment.body,
                        'score': comment.score,
                        'created_utc': comment.created_utc
                    }
                    comments.append(comment_data)
                
                post_data['comments'] = comments
                posts_data.append(post_data)
                post_count += 1
                
            except Exception as e:
                print(f"Error processing post {post.id}: {e}")
                continue
        
        # Save to JSON
        filename = sanitize_filename(f"{subreddit_name}_{search_query}.txt")
        filepath = os.path.join('./search-results', filename)
        
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(posts_data, f, indent=2, ensure_ascii=False)
        
        return True, post_count
    
    except Exception as e:
        print(f"Error searching r/{subreddit_name}: {e}")
        return False, 0

def read_search_terms(file_path):
    """Read search terms from a text file, one per line."""
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            terms = [line.strip() for line in f.readlines() if line.strip()]
        return terms
    except Exception as e:
        print(f"Error reading search terms file: {e}")
        return []

def print_progress(current, total, start_time):
    """Print a progress bar showing the current progress."""
    progress = current / total
    bar_length = 40
    filled_length = int(bar_length * progress)
    bar = '█' * filled_length + '-' * (bar_length - filled_length)
    
    elapsed_time = time.time() - start_time
    if current > 0:
        estimated_total = elapsed_time / progress
        remaining_time = estimated_total - elapsed_time
        time_str = f"Elapsed: {elapsed_time:.1f}s | Remaining: {remaining_time:.1f}s"
    else:
        time_str = f"Elapsed: {elapsed_time:.1f}s"
    
    print(f"\rProgress: |{bar}| {current}/{total} terms ({progress:.1%}) | {time_str}", end='')
    if current == total:
        print()

if __name__ == '__main__':
    # Get input file path
    input_file = input("Enter path to search terms file: ").strip()
    if not os.path.isfile(input_file):
        print(f"Error: File not found - {input_file}")
        exit(1)
    
    # Read search terms
    search_terms = read_search_terms(input_file)
    if not search_terms:
        print("No valid search terms found in the file.")
        exit(1)
    
    # Get subreddit name
    subreddit_name = input("Enter subreddit name: ").strip()
    if not subreddit_name:
        print("Subreddit name is required.")
        exit(1)
    
    # Process each search term
    start_time = time.time()
    total_success = 0
    total_posts = 0
    
    print(f"\nStarting search for {len(search_terms)} terms in r/{subreddit_name}")
    
    for i, term in enumerate(search_terms, 1):
        print_progress(i-1, len(search_terms), start_time)
        success, post_count = search_subreddit(subreddit_name.lower(), term)
        if success:
            total_success += 1
            total_posts += post_count
        time.sleep(2)  # Be polite to Reddit's API
    
    print_progress(len(search_terms), len(search_terms), start_time)
    print(f"\nCompleted {total_success}/{len(search_terms)} searches with {total_posts} total posts in {time.time() - start_time:.2f} seconds")
    print(f"Results saved to:")
    print(f"- Metadata: ./search-results/[subreddit]_[term].txt")
    print(f"- Media:    ./search-results/media/[subreddit]/[term]/")