import os
import glob
import tempfile
from flask import Flask, render_template, request, jsonify, send_file
import yt_dlp

app = Flask(__name__, template_folder='templates')

@app.route('/')
def home():
    return render_template('index.html')

@app.route('/api/search', methods=['POST'])
def search():
    data = request.json or {}
    query = data.get('query')
    if not query:
        return jsonify({'status': 'error'})

    ydl_opts = {'quiet': True, 'extract_flat': True, 'skip_download': True}
    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(f"ytsearch5:{query}", download=False)
            entries = info.get('entries', [])
            results = []
            for item in entries:
                results.append({
                    'title': item.get('title', 'Video Title'),
                    'url': item.get('url') or f"https://www.youtube.com/watch?v={item.get('id')}",
                    'thumbnail': item.get('thumbnails', [{}])[0].get('url', '') if item.get('thumbnails') else f"https://i.ytimg.com/vi/{item.get('id')}/hqdefault.jpg"
                })
            return jsonify({'status': 'success', 'results': results})
    except Exception as e:
        return jsonify({'status': 'error', 'message': str(e)})

@app.route('/api/preview', methods=['POST'])
def preview():
    data = request.json or {}
    url = data.get('url')
    if not url:
        return jsonify({'status': 'error'})
    
    ydl_opts = {'quiet': True, 'skip_download': True}
    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=False)
            return jsonify({
                'status': 'success',
                'title': info.get('title', 'Video Media'),
                'thumbnail': info.get('thumbnail', '')
            })
    except Exception as e:
        return jsonify({'status': 'error'})

@app.route('/api/download', methods=['POST'])
def download():
    data = request.json or {}
    url = data.get('url')
    mode = data.get('mode')
    quality = data.get('quality')

    temp_dir = tempfile.mkdtemp()
    out_template = os.path.join(temp_dir, '%(title)s.%(ext)s')

    ydl_opts = {
        'outtmpl': out_template,
        'quiet': True,
        'nocheckcertificate': True,
        'user_agent': 'Mozilla/5.0 (Linux; Android 10; K) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Mobile Safari/537.36',
    }

    if mode == 'audio':
        bitrate = '320' if '320' in quality else '128'
        ydl_opts['format'] = 'bestaudio/best'
        ydl_opts['postprocessors'] = [
            {'key': 'FFmpegExtractAudio', 'preferredcodec': 'mp3', 'preferredquality': bitrate},
            {'key': 'EmbedThumbnail'},
            {'key': 'FFmpegMetadata'}
        ]
        ydl_opts['writethumbnail'] = True
    else:
        if quality == '720p':
            ydl_opts['format'] = 'bestvideo[height<=720][ext=mp4]+bestaudio[ext=m4a]/best[ext=mp4]/best'
        elif quality == '1080p':
            ydl_opts['format'] = 'bestvideo[height<=1080][ext=mp4]+bestaudio[ext=m4a]/best[ext=mp4]/best'
        elif quality == '2K':
            ydl_opts['format'] = 'bestvideo[height<=1440][ext=mp4]+bestaudio[ext=m4a]/best[ext=mp4]/best'
        elif quality == '4K':
            ydl_opts['format'] = 'bestvideo[height<=2160][ext=mp4]+bestaudio[ext=m4a]/best[ext=mp4]/best'
        else:
            ydl_opts['format'] = 'bestvideo[ext=mp4]+bestaudio[ext=m4a]/best[ext=mp4]/best'
        
        ydl_opts['merge_output_format'] = 'mp4'

    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            ydl.download([url])

        files = glob.glob(os.path.join(temp_dir, '*'))
        if not files:
            return jsonify({'status': 'error'}), 500

        downloaded_file = files[0]
        filename = os.path.basename(downloaded_file)

        return send_file(downloaded_file, as_attachment=True, download_name=filename)

    except Exception as e:
        return jsonify({'status': 'error', 'message': str(e)}), 500

if __name__ == '__main__':
    port = int(os.environ.get("PORT", 5000))
    app.run(host='0.0.0.0', port=port, debug=False)
