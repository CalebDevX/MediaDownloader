# Render Deployment Guide

## Docker-Based Deployment on Render

This application is now configured to deploy on Render using Docker, which ensures yt-dlp stays updated and works correctly.

### What Was Fixed

The Facebook video download error was caused by an outdated yt-dlp version. The fix includes:

1. **Updated `requirements.txt`**: yt-dlp now always installs the latest version (no version pinning)
2. **Created `Dockerfile`**: Ensures proper Python 3.11 environment with FFmpeg and latest yt-dlp
3. **Created `render.yaml`**: Configures Render to use Docker deployment
4. **Created `.dockerignore`**: Optimizes Docker build process

### Deployment Steps on Render

#### Option 1: Using render.yaml (Recommended)

1. Push all changes to your Git repository
2. In Render Dashboard:
   - Click "New +" → "Blueprint"
   - Connect your repository
   - Render will automatically detect `render.yaml` and configure the service
   - Click "Apply" to deploy

#### Option 2: Manual Web Service Setup

1. Push all changes to your Git repository
2. In Render Dashboard:
   - Click "New +" → "Web Service"
   - Connect your repository
   - Configure:
     - **Environment**: Docker
     - **Region**: Choose your preferred region
     - **Branch**: main (or your default branch)
     - **Dockerfile Path**: ./Dockerfile
     - **Docker Context**: .
3. Click "Create Web Service"

### Key Features of This Setup

- **Auto-updates yt-dlp**: The Dockerfile runs `pip install --upgrade yt-dlp` on every build
- **FFmpeg included**: Required for audio/video processing
- **Optimized for Render**: Uses gunicorn with 2 workers and 120s timeout
- **Port 5000**: Configured correctly for Render's proxy

### Keeping yt-dlp Updated

To ensure yt-dlp stays current:

1. **Manual redeploy**: In Render dashboard, click "Manual Deploy" → "Deploy latest commit"
2. **Automatic**: Any git push will trigger a new build with latest yt-dlp
3. **Scheduled**: Consider setting up a weekly auto-deploy to keep dependencies fresh

### Troubleshooting

If downloads still fail after deployment:

1. Check Render logs for specific errors
2. Verify the build installed latest yt-dlp (check build logs)
3. For Facebook-specific issues, the platform may require additional cookies/headers (see app.py configuration)

### Environment Variables (Optional)

If needed, you can add these in Render's Environment tab:

- Custom timeout values
- API keys for services
- Debug flags

If you want Spotify metadata/preview support, add these environment variables in Render (Service → Environment):

- `SPOTIFY_CLIENT_ID` — your Spotify app client id
- `SPOTIFY_CLIENT_SECRET` — your Spotify app client secret

Without these credentials the Spotify feature will return an informative error explaining how to enable Spotify API access.

### Cost

This configuration works on Render's **Free tier** but will:
- Sleep after 15 minutes of inactivity
- Have limited bandwidth/build minutes

For production, consider upgrading to a paid plan.
