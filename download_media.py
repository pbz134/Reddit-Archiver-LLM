import os
import json
import requests
import praw
from urllib.parse import urlparse
from datetime import datetime
from concurrent.futures import ThreadPoolExecutor
import time

# Configuration
REDDIT_CLIENT_ID = 'Put your Client ID here'
REDDIT_SECRET = 'Put your Secret here'
REDDIT_USER_AGENT = 'SubredditArchiver/1.0'
POST_LIMIT = 1000
COMMENT_LIMIT = 500

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

def process_gallery(post, subreddit_dir):
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
                    filepath = os.path.join(subreddit_dir, 'images', filename)
                    
                    if download_file(image_url, filepath):
                        gallery_items.append(filepath)
    
    except Exception as e:
        print(f"Error processing gallery for post {post.id}: {e}")
    
    return gallery_items

def process_media(post, subreddit_dir):
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
            filepath = os.path.join(subreddit_dir, 'images', filename)
            
            if download_file(url, filepath):
                media_path = filepath
        
        # Handle imgur links (simple ones)
        elif 'imgur.com' in parsed.netloc and not url.endswith('/'):
            imgur_url = url + '.jpg'
            filename = f"{post.id}.jpg"
            filepath = os.path.join(subreddit_dir, 'images', filename)
            
            if download_file(imgur_url, filepath):
                media_path = filepath
        
        # Handle reddit video
        elif 'v.redd.it' in parsed.netloc:
            try:
                if hasattr(post, 'media') and post.media and 'reddit_video' in post.media:
                    video_url = post.media['reddit_video']['fallback_url']
                    filename = f"{post.id}.mp4"
                    filepath = os.path.join(subreddit_dir, 'videos', filename)
                    
                    if download_file(video_url, filepath):
                        media_path = filepath
            except Exception as e:
                print(f"Error processing video for post {post.id}: {e}")
    
    # Check for gallery
    if hasattr(post, 'is_gallery') and post.is_gallery:
        gallery_items = process_gallery(post, subreddit_dir)
        if gallery_items:
            media_path = gallery_items
            is_gallery = True
    
    return media_path, is_gallery

def download_subreddit(subreddit_name):
    """Download posts from a subreddit and save them to disk."""
    # Create directories
    subreddit_dir = os.path.join('r', subreddit_name)
    os.makedirs(os.path.join(subreddit_dir, 'images'), exist_ok=True)
    os.makedirs(os.path.join(subreddit_dir, 'videos'), exist_ok=True)
    
    # Initialize Reddit client
    reddit = praw.Reddit(
        client_id=REDDIT_CLIENT_ID,
        client_secret=REDDIT_SECRET,
        user_agent=REDDIT_USER_AGENT
    )
    
    posts_data = []
    
    try:
        print(f"Downloading posts from r/{subreddit_name}...")
        subreddit = reddit.subreddit(subreddit_name)
        
        # Download subreddit icon and banner if available
        try:
            if subreddit.icon_img:
                download_file(subreddit.icon_img, os.path.join(subreddit_dir, 'images', 'icon.png'))
            if subreddit.banner_background_image:
                download_file(subreddit.banner_background_image, os.path.join(subreddit_dir, 'images', 'banner.png'))
        except Exception as e:
            print(f"Error downloading subreddit images: {e}")
        
        # Process posts
        for post in subreddit.hot(limit=POST_LIMIT):
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
                    'saved_at': datetime.utcnow().timestamp()
                }
                
                # Process media
                media_path, is_gallery = process_media(post, subreddit_dir)
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
                
                print(f"Processed post: {post.title[:50]}...")
                
            except Exception as e:
                print(f"Error processing post {post.id}: {e}")
                continue
        
        # Save to JSON
        archive_path = os.path.join(subreddit_dir, 'archive.json')
        with open(archive_path, 'w') as f:
            json.dump(posts_data, f, indent=2)
        
        print(f"Successfully archived {len(posts_data)} posts from r/{subreddit_name}")
    
    except Exception as e:
        print(f"Error downloading subreddit r/{subreddit_name}: {e}")

if __name__ == '__main__':
    subreddit_name = input("Enter subreddit name to archive: ").strip()
    if subreddit_name:
        start_time = time.time()
        download_subreddit(subreddit_name.lower())
        print(f"Archiving completed in {time.time() - start_time:.2f} seconds")
    else:
        print("No subreddit name provided.")