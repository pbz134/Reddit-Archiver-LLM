# Reddit-Archiver-LLM
Reddit-Archiver-LLM is a collection of scripts that, when put together, enable you to download way past the Reddit API's native limit of 1000 posts.

By first downloading a 1000 posts and then extracting key terms from the final posts inside the .json file, we are able to iterate through each search term using an automated script.
This then downloads massive amounts of data from a single subreddit, sometimes even exceeding 400,000 posts in one session with over 100GB of posts, comments, videos and images.


# Setup Tutorial
To get started using the archiver, first obtain your Reddit API and Secret key
- Visit https://old.reddit.com/prefs/apps in your browser
   - For the name, input anything you want
  - For the redirect URL, input `http://localhost:8080`
- After creating the app, note down the `secret` and `Client ID` value, found below your blue app name
- Git clone my repo: `git clone https://github.com/pbz134/Reddit-Archiver-LLM`
- Insert your own `CLIENT_ID` and `REDDIT_SECRET` strings at line 11 of `download_media.py` and into the `.env` file

Now, we will initiate the raw subreddit download of 1000 posts. For this example, we will use r/Touhou.
- `pip install -r requirements.txt`
- `python download_media.py`
- Enter any subreddit you want, for example `Touhou`
- Wait for the download to finish (this should only take 10-15 minutes)

Next, extract search terms from the archive.json file that you just generated with the 1000 posts:
- `python 1-extract-search-terms.py -i .\r\Touhou\archive.json -o Touhou.txt` (this might take up to an hour on CPU and ~5 minutes on a RTX 4070S)

Strip the search terms inside the .txt file to avoid duplicate API calls
- `python 2-strip_txt.py -i Touhou.txt -o Touhou_stripped.txt`

Finally, start downloading (this might take up to 30 hours and 100GB, depending on the subreddit size, so please be patient)
- `python 3-download-from-txt.py` then enter the name of your stripped .txt file, e.g. `Touhou_stripped.txt`

After the download is done, we will make sure there are no duplicate posts
  - `python 4-merge-and-remove-duplicates.py`
 
We will also merge all search term media folders into one
- `python 5-merge-search-results-folders.py`

Lastly, we will delete duplicate media files
- `python 6-delete-dupes.py .\search-results\Touhou`

Move your final archive.json file, as well as the "images" and "videos" folders into /r/Touhou/

# Launching the viewer
- To view your downloaded subreddit, execute `python app.py` and visit `http://127.0.0.1:5000/r/` in your browser
