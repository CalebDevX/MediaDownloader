from flask import Flask, render_template, request, jsonify, send_file, send_from_directory
import yt_dlp
import os
import time
import uuid
from threading import Thread

app = Flask(__name__)

# Configuration
DOWNLOAD_FOLDER = 'static/downloads'
os.makedirs(DOWNLOAD_FOLDER, exist_ok=True)

# Global dictionary to store download progress
download_progress = {}

# File cleanup function
def cleanup_old_files():
    """Remove files older than 5 minutes"""
    while True:
        try:
            current_time = time.time()
            for filename in os.listdir(DOWNLOAD_FOLDER):
                filepath = os.path.join(DOWNLOAD_FOLDER, filename)
                if os.path.isfile(filepath):
                    file_age = current_time - os.path.getmtime(filepath)
                    if file_age > 300:  # 5 minutes
                        os.remove(filepath)
                        print(f"Cleaned up old file: {filename}")
        except Exception as e:
            print(f"Cleanup error: {e}")
        time.sleep(60)  # Check every minute

# Start cleanup thread
cleanup_thread = Thread(target=cleanup_old_files, daemon=True)
cleanup_thread.start()

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/youtube-downloader')
def youtube_downloader():
    return render_template('youtube.html')

@app.route('/tiktok-downloader')
def tiktok_downloader():
    return render_template('tiktok.html')

@app.route('/instagram-downloader')
def instagram_downloader():
    return render_template('instagram.html')

@app.route('/facebook-downloader')
def facebook_downloader():
    return render_template('facebook.html')

@app.route('/spotify-downloader')
def spotify_downloader():
    return render_template('spotify.html')

@app.route('/audiomack-downloader')
def audiomack_downloader():
    return render_template('audiomack.html')

@app.route('/sw.js')
def service_worker():
    return send_from_directory('.', 'sw.js', mimetype='application/javascript')

@app.route('/robots.txt')
def robots():
    return send_from_directory('.', 'robots.txt', mimetype='text/plain')

@app.route('/ads.txt')
def ads_txt():
    return send_from_directory('.', 'ads.txt', mimetype='text/plain')

@app.route('/fetch_info', methods=['POST'])
def fetch_info():
    url = ''
    ydl_opts = {}
    try:
        data = request.get_json()
        url = data.get('url')

        if not url:
            return jsonify({'error': 'URL is required'}), 400

        # Enhanced options for Instagram and other platforms
        ydl_opts = {
            'quiet': True,
            'no_warnings': True,
            'extract_flat': False,
            'socket_timeout': 30,
            'retries': 5,
            'geo_bypass': True,
            'geo_bypass_country': 'US',
            'age_limit': None,
            'nocheckcertificate': True,
            'source_address': '0.0.0.0',
            'force_ipv4': True,
            'http_headers': {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/130.0.0.0 Safari/537.36',
                'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8',
                'Accept-Language': 'en-US,en;q=0.9',
                'Accept-Encoding': 'gzip, deflate, br',
                'Connection': 'keep-alive',
                'Upgrade-Insecure-Requests': '1',
                'Sec-Fetch-Dest': 'document',
                'Sec-Fetch-Mode': '',
                'Sec-Fetch-Site': 'none',
                'Sec-Fetch-User': '?1',
                'Cache-Control': 'max-age=0',
            },
            'extractor_args': {
                'instagram': {
                    'include_stories': True,
                    'include_highlights': True,
                },
                'twitter': {
                    'api': 'syndication',
                },
                'tiktok': {
                    'api': 'mobile_app',
                    'webpage_download': True,
                },
                'youtube': {
                    'player_client': ['android', 'web'],
                    'skip': ['hls', 'dash'],
                },
                'facebook': {
                    'legacy_api': False,
                },
            },
            'force_generic_extractor': False,
        }

        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=False)

            if info is None:
                return jsonify({'error': 'Could not extract media information'}), 400

            # Get video formats
            video_formats = []
            audio_formats = []

            if 'formats' in info and info['formats']:
                for f in info['formats']:
                    # Video formats (has video and optionally audio)
                    if f.get('vcodec') != 'none':
                        quality = f.get('format_note', f.get('quality', 'Unknown'))
                        height = f.get('height', 0)
                        ext = f.get('ext', 'mp4')
                        filesize = f.get('filesize', 0) or f.get('filesize_approx', 0)
                        filesize_mb = round(filesize / (1024 * 1024), 2) if filesize else 'Unknown'

                        video_formats.append({
                            'format_id': f.get('format_id'),
                            'quality': f"{height}p" if height else quality,
                            'ext': ext,
                            'filesize': filesize_mb
                        })

                    # Audio-only formats
                    elif f.get('acodec') != 'none' and f.get('vcodec') == 'none':
                        abr = f.get('abr', 0)
                        ext = f.get('ext', 'mp3')
                        filesize = f.get('filesize', 0) or f.get('filesize_approx', 0)
                        filesize_mb = round(filesize / (1024 * 1024), 2) if filesize else 'Unknown'

                        audio_formats.append({
                            'format_id': f.get('format_id'),
                            'quality': f"{int(abr)}kbps" if abr else 'Audio',
                            'ext': ext,
                            'filesize': filesize_mb
                        })

                # Remove duplicates and sort
                video_formats = list({v['format_id']: v for v in video_formats}.values())
                audio_formats = list({a['format_id']: a for a in audio_formats}.values())

                video_formats = sorted(video_formats, key=lambda x: int(x['quality'].replace('p', '')) if x['quality'].replace('p', '').isdigit() else 0, reverse=True)
                audio_formats = sorted(audio_formats, key=lambda x: int(x['quality'].replace('kbps', '')) if 'kbps' in x['quality'] else 0, reverse=True)

            return jsonify({
                'success': True,
                'title': info.get('title', 'Unknown Title'),
                'thumbnail': info.get('thumbnail', ''),
                'uploader': info.get('uploader', 'Unknown'),
                'duration': info.get('duration_string', 'Unknown'),
                'video_formats': video_formats[:15],
                'audio_formats': audio_formats[:8]
            })

    except yt_dlp.utils.DownloadError as e:
        error_msg = str(e)
        print(f"Download Error: {error_msg}")

        # Detect platform from URL for accurate error messages
        platform = 'unknown'
        if url:
            url_lower = url.lower()
            if 'tiktok.com' in url_lower or 'vm.tiktok.com' in url_lower:
                platform = 'tiktok'
            elif 'instagram.com' in url_lower:
                platform = 'instagram'
            elif 'youtube.com' in url_lower or 'youtu.be' in url_lower:
                platform = 'youtube'
            elif 'twitter.com' in url_lower or 'x.com' in url_lower:
                platform = 'twitter'
            elif 'facebook.com' in url_lower or 'fb.watch' in url_lower or 'fb.me' in url_lower:
                platform = 'facebook'
            elif 'spotify.com' in url_lower:
                platform = 'spotify'
            elif 'audiomack.com' in url_lower:
                platform = 'audiomack'
            elif 'soundcloud.com' in url_lower:
                platform = 'soundcloud'
            elif 'vimeo.com' in url_lower:
                platform = 'vimeo'
            elif 'netflix.com' in url_lower:
                platform = 'netflix'

        # Platform-specific error handling with detailed messages
        if platform == 'tiktok':
            if 'Unable to extract' in error_msg or 'webpage video data' in error_msg or 'video data' in error_msg.lower():
                return jsonify({'error': '📱 TikTok Error: Unable to access this video. Possible reasons:\n• Video is private or deleted\n• Account is private\n• Video is region-locked\n• TikTok is blocking automated access\n\nSolutions:\n✓ Make sure the video is public\n✓ Try a different TikTok video\n✓ Wait 2-3 minutes and try again\n✓ Copy the link directly from TikTok app/website'}), 400
            elif 'Login required' in error_msg or 'sign in' in error_msg.lower():
                return jsonify({'error': '📱 TikTok requires login to access this content. Only public videos from public accounts can be downloaded without authentication.'}), 400
            else:
                return jsonify({'error': '📱 TikTok download failed. The video may be unavailable or TikTok is blocking requests. Wait 2-3 minutes and try again with a different video.'}), 400

        elif platform == 'instagram':
            if 'rate-limit' in error_msg.lower() or 'rate limit' in error_msg.lower():
                return jsonify({'error': '📸 Instagram Rate Limit: Too many requests detected.\n\nSolutions:\n✓ Wait 5-10 minutes before trying again\n✓ Instagram blocks automated downloads temporarily\n✓ Try a different post in the meantime\n✓ Make sure the post is public'}), 400
            elif 'login required' in error_msg.lower() or 'authentication' in error_msg.lower():
                return jsonify({'error': '📸 Instagram Login Required: This content requires authentication.\n\nPossible reasons:\n• Post is from a private account\n• Content is age-restricted\n• Instagram is blocking automated access\n\nOnly public posts and reels can be downloaded.'}), 400
            elif 'not available' in error_msg.lower() or 'content is not available' in error_msg.lower():
                return jsonify({'error': '📸 Instagram Content Unavailable:\n• Post may be deleted or made private\n• Story/Highlight has expired\n• Account is private or blocked\n• Region restrictions apply\n\nTry a different public post or reel.'}), 400
            elif 'private' in error_msg.lower():
                return jsonify({'error': '📸 This Instagram account/post is private. Only public content can be downloaded.'}), 400
            else:
                return jsonify({'error': '📸 Instagram Error: Unable to fetch content. Instagram may be blocking requests.\n\nSolutions:\n✓ Wait 5-10 minutes and try again\n✓ Make sure the post/reel is public\n✓ Try copying the link directly from Instagram app\n✓ Use a different public post'}), 400

        elif platform == 'youtube':
            if 'private' in error_msg.lower() or 'unavailable' in error_msg.lower():
                return jsonify({'error': '🎬 YouTube video is private, deleted, or unavailable in your region.'}), 400
            elif 'age' in error_msg.lower() or 'restricted' in error_msg.lower():
                return jsonify({'error': '🔞 This YouTube video is age-restricted and requires login to access.'}), 400
            elif 'live' in error_msg.lower():
                return jsonify({'error': '📡 Live streams cannot be downloaded. Wait until the stream ends and try again.'}), 400
            else:
                return jsonify({'error': '🎬 YouTube download failed. The video may be region-locked, removed, or have download restrictions.'}), 400

        elif platform == 'facebook':
            if 'login required' in error_msg.lower() or 'private' in error_msg.lower():
                return jsonify({'error': '📘 Facebook content is private or requires login. Only public videos can be downloaded.'}), 400
            else:
                return jsonify({'error': '📘 Facebook download failed. Make sure the video is public and not from a private group or profile.'}), 400

        elif platform == 'twitter':
            if 'no video' in error_msg.lower() or 'no media' in error_msg.lower():
                return jsonify({'error': '😕 This tweet doesn\'t contain a video. We can only download tweets with video content.'}), 400
            elif 'private' in error_msg.lower() or 'protected' in error_msg.lower():
                return jsonify({'error': '🔒 This Twitter/X account is private. Only public tweets can be downloaded.'}), 400
            else:
                return jsonify({'error': '❌ Twitter/X download failed. Make sure the tweet is public and contains video content.'}), 400

        elif platform == 'spotify':
            return jsonify({'error': '🎧 Spotify Error: Spotify uses DRM protection and requires premium subscription.\n\nThis content cannot be downloaded directly. Spotify restricts downloading to prevent piracy.'}), 400

        elif platform == 'audiomack':
            return jsonify({'error': '🎵 Audiomack download failed.\n\nPossible reasons:\n• Track is premium-only\n• Content is region-locked\n• Link is invalid\n\nSolutions:\n✓ Make sure the track is publicly available\n✓ Copy the link directly from Audiomack\n✓ Try a different free track'}), 400

        elif platform == 'soundcloud':
            if 'private' in error_msg.lower():
                return jsonify({'error': '🎶 This SoundCloud track is private. Only public tracks can be downloaded.'}), 400
            else:
                return jsonify({'error': '🎶 SoundCloud download failed. Make sure the track is public and not premium-only.'}), 400

        elif platform == 'vimeo':
            if 'password' in error_msg.lower() or 'private' in error_msg.lower():
                return jsonify({'error': '🎥 This Vimeo video is password-protected or private. Only public videos can be downloaded.'}), 400
            else:
                return jsonify({'error': '🎥 Vimeo download failed. The video may have download restrictions or be private.'}), 400

        elif platform == 'netflix':
            return jsonify({'error': '🎬 Netflix content is DRM-protected and cannot be downloaded. This is a copyright restriction enforced by Netflix.'}), 400

        # Generic error handling for other platforms
        if 'DRM' in error_msg or 'protected' in error_msg.lower():
            return jsonify({'error': '🔒 This content is DRM-protected and cannot be downloaded due to copyright restrictions.'}), 400
        elif '429' in error_msg or 'Too Many Requests' in error_msg or 'rate limit' in error_msg.lower():
            return jsonify({'error': '⏰ Rate Limit Reached: Too many requests.\n\nPlease wait 5-10 minutes and try again. The platform is temporarily blocking automated downloads.'}), 400
        elif 'geo' in error_msg.lower() or 'region' in error_msg.lower():
            return jsonify({'error': '🌍 This content is region-locked and not available in your location.'}), 400
        elif 'private' in error_msg.lower():
            return jsonify({'error': '🔒 This content is private. Only public content can be downloaded.'}), 400
        elif 'login' in error_msg.lower() or 'sign in' in error_msg.lower() or 'authentication' in error_msg.lower():
            return jsonify({'error': '🔐 Login required. Only public content can be downloaded without authentication.'}), 400
        elif 'no video' in error_msg.lower() or 'no media' in error_msg.lower():
            return jsonify({'error': '📭 No video found. This post may contain only images or text.'}), 400
        else:
            return jsonify({'error': f'⚠️ Download Error: Unable to access this content.\n\nPossible reasons:\n• Content is unavailable or deleted\n• Platform is blocking automated access\n• Link is invalid\n\nPlease try:\n✓ Checking if the content is public\n✓ Waiting a few minutes and trying again\n✓ Using a different link'}), 400

    except Exception as e:
        error_message = str(e)
        print(f"ERROR: {error_message}")

        # Detect platform from URL
        platform = 'unknown'
        if url:
            url_lower = url.lower()
            if 'instagram.com' in url_lower:
                platform = 'instagram'
            elif 'tiktok.com' in url_lower:
                platform = 'tiktok'
            elif 'youtube.com' in url_lower or 'youtu.be' in url_lower:
                platform = 'youtube'
            elif 'facebook.com' in url_lower or 'fb.watch' in url_lower:
                platform = 'facebook'
            elif 'twitter.com' in url_lower or 'x.com' in url_lower:
                platform = 'twitter'
            elif 'spotify.com' in url_lower:
                platform = 'spotify'
            elif 'audiomack.com' in url_lower:
                platform = 'audiomack'
            elif 'netflix.com' in url_lower:
                platform = 'netflix'

        # Provide more helpful, user-friendly error messages based on detected platform
        if platform == 'twitter':
            if 'no video' in error_message.lower():
                error_message = "😕 This tweet doesn't have a video. We can only download tweets that contain videos."
            else:
                error_message = "❌ Couldn't access this Twitter/X content. Make sure the tweet is public and contains media."
        elif platform == 'instagram':
            error_message = "📸 Instagram temporarily blocked this request. Please wait 2-3 minutes and try again. Make sure you're using a public post or reel link."
        elif platform == 'tiktok':
            error_message = "📱 TikTok download failed. Make sure the video is public and the link is correct. If it's a private account, we can't access it."
        elif platform == 'audiomack':
            error_message = "🎵 Couldn't download from Audiomack. Please check the link and make sure the song is publicly available. Try copying the link directly from your browser."
        elif 'spotify' in error_message.lower() or (url and 'spotify.com' in url.lower()):
            error_message = "🎧 Spotify content couldn't be accessed. Make sure the track/playlist is public and the link is correct."
        elif 'netflix' in error_message.lower() or (url and 'netflix.com' in url.lower()):
            error_message = "🎬 Netflix content is DRM-protected and cannot be downloaded. This is due to copyright restrictions."
        elif 'tiktok' in error_message.lower() or (url and 'tiktok.com' in url.lower()):
            error_message = "📱 TikTok download failed. Make sure the video is public and the link is correct."
        elif 'facebook' in error_message.lower() or (url and 'facebook.com' in url.lower()):
            error_message = "📘 Facebook content couldn't be accessed. Only public videos can be downloaded. Private or friends-only posts won't work."
        elif 'youtube' in error_message.lower() or (url and ('youtube.com' in url.lower() or 'youtu.be' in url.lower())):
            if 'private' in error_message.lower():
                error_message = "🔒 This YouTube video is private or unavailable."
            elif 'age' in error_message.lower():
                error_message = "🔞 Age-restricted YouTube content cannot be downloaded without login."
            else:
                error_message = "🎬 YouTube download failed. The video might be region-locked, removed, or live-streamed."
        elif 'soundcloud' in error_message.lower() or (url and 'soundcloud.com' in url.lower()):
            error_message = "🎶 SoundCloud download failed. Make sure the track is public and not premium-only."
        elif 'vimeo' in error_message.lower() or (url and 'vimeo.com' in url.lower()):
            error_message = "🎥 Vimeo content couldn't be accessed. Only public videos without download restrictions can be downloaded."
        elif 'unsupported' in error_message.lower():
            error_message = "❓ This website is not supported yet. We support YouTube, Spotify, Audiomack, Netflix, Instagram, TikTok, Facebook, and 1000+ other platforms."
        elif 'url' in error_message.lower() or 'invalid' in error_message.lower():
            error_message = "🔗 Invalid link format. Please copy and paste the full URL from your browser."
        else:
            error_message = f"⚠️ Something went wrong: {error_message}. Please try again or use a different link."

        return jsonify({'error': error_message}), 400


def progress_hook(d, download_id):
    """Hook function to track download progress"""
    if d['status'] == 'downloading':
        # Calculate progress percentage
        if 'total_bytes' in d or 'total_bytes_estimate' in d:
            total = d.get('total_bytes') or d.get('total_bytes_estimate', 0)
            downloaded = d.get('downloaded_bytes', 0)

            if total > 0:
                percentage = int((downloaded / total) * 100)
            else:
                percentage = 0

            # Calculate speed and ETA
            speed = d.get('speed', 0)
            eta = d.get('eta', 0)

            download_progress[download_id] = {
                'status': 'downloading',
                'percentage': percentage,
                'downloaded': downloaded,
                'total': total,
                'speed': speed if speed else 0,
                'eta': eta if eta else 0
            }
        else:
            download_progress[download_id] = {
                'status': 'downloading',
                'percentage': 0,
                'message': 'Starting download...'
            }
    elif d['status'] == 'finished':
        download_progress[download_id] = {
            'status': 'processing',
            'percentage': 100,
            'message': 'Processing file...'
        }

@app.route('/progress/<download_id>')
def get_progress(download_id):
    """Endpoint to check download progress"""
    progress = download_progress.get(download_id, {'status': 'not_found', 'percentage': 0})
    return jsonify(progress)

@app.route('/start_download', methods=['POST'])
def start_download():
    """Initialize download and return download_id for progress tracking"""
    try:
        data = request.get_json()
        url = data.get('url')
        format_id = data.get('format_id')
        download_type = data.get('type', 'video')

        if not url:
            return jsonify({'error': 'URL is required'}), 400

        # Generate unique download ID
        download_id = str(uuid.uuid4())
        timestamp = int(time.time())

        # Initialize progress
        download_progress[download_id] = {
            'status': 'starting',
            'percentage': 0,
            'message': 'Initializing download...',
            'timestamp': timestamp,
            'type': download_type
        }

        # Return download_id immediately so client can start polling
        return jsonify({
            'success': True,
            'download_id': download_id
        })

    except Exception as e:
        return jsonify({'error': f'Failed to start download: {str(e)}'}), 500

@app.route('/download', methods=['POST'])
def download():
    download_id = None
    try:
        data = request.get_json()
        url = data.get('url')
        format_id = data.get('format_id')
        download_type = data.get('type', 'video')
        download_id = data.get('download_id')

        if not url:
            return jsonify({'error': 'URL is required'}), 400

        if not download_id:
            return jsonify({'error': 'Download ID is required'}), 400

        timestamp = int(time.time())

        # Update progress status
        if download_id in download_progress:
            download_progress[download_id]['status'] = 'downloading'
            download_progress[download_id]['message'] = 'Starting download...'

        if download_type == 'audio':
            output_template = os.path.join(DOWNLOAD_FOLDER, f'audio_{timestamp}.%(ext)s')
            audio_format = format_id if format_id else 'bestaudio/best'
            ydl_opts = {
                'format': audio_format,
                'outtmpl': output_template,
                'quiet': True,
                'no_warnings': True,
                'progress_hooks': [lambda d: progress_hook(d, download_id)],
                'postprocessors': [{
                    'key': 'FFmpegExtractAudio',
                    'preferredcodec': 'mp3',
                    'preferredquality': '320',
                }],
                'socket_timeout': 30,
                'retries': 5,
                'geo_bypass': True,
                'nocheckcertificate': True,
                'source_address': '0.0.0.0',
                'force_ipv4': True,
                'http_headers': {
                    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/130.0.0.0 Safari/537.36',
                    'Accept': '*/*',
                    'Accept-Language': 'en-US,en;q=0.9',
                },
                'extractor_args': {
                    'youtube': {
                        'player_client': ['android', 'web'],
                        'skip': ['hls', 'dash'],
                    },
                },
            }
        else:
            output_template = os.path.join(DOWNLOAD_FOLDER, f'video_{timestamp}.%(ext)s')
            video_format = format_id if format_id else 'bestvideo+bestaudio/best'
            ydl_opts = {
                'format': video_format,
                'outtmpl': output_template,
                'quiet': True,
                'no_warnings': True,
                'merge_output_format': 'mp4',
                'progress_hooks': [lambda d: progress_hook(d, download_id)],
                'socket_timeout': 30,
                'retries': 5,
                'geo_bypass': True,
                'nocheckcertificate': True,
                'source_address': '0.0.0.0',
                'force_ipv4': True,
                'http_headers': {
                    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/130.0.0.0 Safari/537.36',
                    'Accept': '*/*',
                    'Accept-Language': 'en-US,en;q=0.9',
                },
                'extractor_args': {
                    'youtube': {
                        'player_client': ['android', 'web'],
                        'skip': ['hls', 'dash'],
                    },
                },
            }

        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            ydl.download([url])

        downloaded_files = [f for f in os.listdir(DOWNLOAD_FOLDER) if f.startswith(f'{download_type}_{timestamp}')]

        if not downloaded_files:
            if download_id in download_progress:
                download_progress[download_id] = {'status': 'error', 'percentage': 0, 'message': 'No file was created'}
                # Schedule cleanup for this error case too
                def cleanup_no_file():
                    time.sleep(10)
                    download_progress.pop(download_id, None)
                Thread(target=cleanup_no_file, daemon=True).start()
            return jsonify({'error': 'Download failed - no file was created'}), 500

        download_filename = downloaded_files[0]
        download_url = f'/static/downloads/{download_filename}'

        # Mark as complete and schedule cleanup
        if download_id in download_progress:
            download_progress[download_id] = {
                'status': 'complete',
                'percentage': 100,
                'message': 'Download complete!'
            }

        # Schedule cleanup after 10 seconds
        def cleanup():
            time.sleep(10)
            download_progress.pop(download_id, None)
        Thread(target=cleanup, daemon=True).start()

        return jsonify({
            'success': True,
            'download_url': download_url
        })

    except Exception as e:
        if download_id and download_id in download_progress:
            download_progress[download_id] = {'status': 'error', 'percentage': 0, 'message': str(e)}
            # Schedule cleanup for errored downloads too
            def cleanup_error():
                time.sleep(10)
                download_progress.pop(download_id, None)
            Thread(target=cleanup_error, daemon=True).start()
        return jsonify({'error': f'Download failed: {str(e)}'}), 500

if __name__ == '__main__':
    # For local development
    app.run(host='0.0.0.0', port=5000, debug=False)

# For production WSGI server (required by shared hosting)
# The 'app' object is what the server will use