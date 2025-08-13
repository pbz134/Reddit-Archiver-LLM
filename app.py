from flask import Flask, render_template, json, send_from_directory, redirect, url_for
import os
from urllib.parse import unquote

app = Flask(__name__)

# Configuration
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
ARCHIVES_DIR = os.path.join(BASE_DIR, 'r')

@app.route('/')
def index():
    subreddits = get_available_subreddits()
    if subreddits:
        return redirect(url_for('show_subreddit', subreddit=subreddits[0]))
    return "No subreddits archived yet. Use the download script first."

@app.route('/r/')
def list_subreddits():
    subreddits = get_available_subreddits()
    subreddit_data = []
    for subreddit in subreddits:
        post_count = len(load_posts(subreddit))
        subreddit_data.append({
            'name': subreddit,
            'post_count': post_count
        })
    return render_template('subreddits.html', subreddits=subreddit_data)

@app.route('/r/<subreddit>')
def show_subreddit(subreddit):
    if not os.path.exists(os.path.join(ARCHIVES_DIR, subreddit)):
        return "Subreddit not found", 404

    posts = load_posts(subreddit)
    subreddits = get_available_subreddits()
    
    # Check for icon in multiple formats
    icon_path = None
    icon_formats = ['icon.png', 'icon.jpg', 'icon.jpeg', 'icon.gif', 'icon.webp']
    for fmt in icon_formats:
        test_path = os.path.join(ARCHIVES_DIR, subreddit, 'images', fmt)
        if os.path.exists(test_path):
            icon_path = test_path
            break
    
    # Check for banner in multiple formats
    banner_path = None
    banner_formats = ['banner.png', 'banner.jpg', 'banner.jpeg', 'banner.gif', 'banner.webp']
    for fmt in banner_formats:
        test_path = os.path.join(ARCHIVES_DIR, subreddit, 'images', fmt)
        if os.path.exists(test_path):
            banner_path = test_path
            break

    icon_url = f"/r/{subreddit}/images/{os.path.basename(icon_path)}" if icon_path else None
    banner_url = f"/r/{subreddit}/images/{os.path.basename(banner_path)}" if banner_path else None

    return render_template('archive.html',
                         posts=posts,
                         subreddit=subreddit,
                         subreddits=subreddits,
                         icon_url=icon_url,
                         banner_url=banner_url)

@app.route('/r/<subreddit>/images/<path:filename>')
def serve_image(subreddit, filename):
    return send_from_directory(
        os.path.join(ARCHIVES_DIR, subreddit, 'images'),
        unquote(filename)
    )

@app.route('/r/<subreddit>/post/<int:post_id>')
def show_post(subreddit, post_id):
    posts = load_posts(subreddit)
    if 0 <= post_id < len(posts):
        return render_template('archive.html',
                            posts=[posts[post_id]],
                            subreddit=subreddit,
                            subreddits=get_available_subreddits())
    else:
        return "Post not found", 404

@app.route('/r/<subreddit>/videos/<path:filename>')
def serve_video(subreddit, filename):
    return send_from_directory(
        os.path.join(ARCHIVES_DIR, subreddit, 'videos'),
        unquote(filename)
    )

# API endpoints
@app.route('/api/subreddits')
def list_subreddits_api():
    subreddits = get_available_subreddits()
    subreddit_data = []
    for subreddit in subreddits:
        post_count = len(load_posts(subreddit))
        subreddit_data.append({
            'name': subreddit,
            'post_count': post_count
        })
    return json.jsonify(subreddit_data)

@app.route('/api/r/<subreddit>/posts')
def get_posts_api(subreddit):
    return json.jsonify(load_posts(subreddit))

def load_posts(subreddit):
    archive_path = os.path.join(ARCHIVES_DIR, subreddit, 'archive.json')
    try:
        with open(archive_path, 'r') as f:
            posts = json.load(f)
            # Convert paths to web-accessible URLs
            for post in posts:
                if 'local_media' in post:
                    if isinstance(post['local_media'], str):
                        if post['local_media'].endswith(('.jpg', '.jpeg', '.png', '.gif', '.webp')):
                            post['local_media'] = f"/r/{subreddit}/images/{os.path.basename(post['local_media'])}"
                        elif post['local_media'].endswith(('.mp4', '.webm')):
                            post['local_media'] = f"/r/{subreddit}/videos/{os.path.basename(post['local_media'])}"
                    elif isinstance(post['local_media'], list):
                        post['local_media'] = [
                            f"/r/{subreddit}/images/{os.path.basename(media)}" if media.endswith(('.jpg', '.jpeg', '.png', '.gif', '.webp')) else
                            f"/r/{subreddit}/videos/{os.path.basename(media)}"
                            for media in post['local_media']
                        ]
            return posts
    except FileNotFoundError:
        return []

def get_available_subreddits():
    try:
        return sorted([
            d for d in os.listdir(ARCHIVES_DIR)
            if os.path.isdir(os.path.join(ARCHIVES_DIR, d))
        ])
    except FileNotFoundError:
        return []

if __name__ == '__main__':
    os.makedirs(ARCHIVES_DIR, exist_ok=True)
    print("Visit http://127.0.0.1:5000/r/ to view all subreddits")
    app.run(debug=True)
