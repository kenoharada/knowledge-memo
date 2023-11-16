from flask import Flask, request, jsonify, render_template
import os
import yt_dlp
from summarize import extract_text_from_vtt, summarize, translate


def download_and_read_subtitles(video_url):
    ydl_opts = {
        'writesubtitles': True,
        'skip_download': True,
        'outtmpl': '%(id)s',  # YouTubeの動画IDをファイル名に指定
        'subtitleslangs': ['en'],  # 英語の字幕を指定
    }

    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        info_dict = ydl.extract_info(video_url, download=True)
        video_id = info_dict.get('id')

        # ダウンロードされた字幕ファイルの名前を見つける
        subtitle_file = None
        for ext in ('vtt', 'srt', 'ass'):  # 一般的な字幕ファイル形式
            if os.path.exists(f'{video_id}.en.{ext}'):
                subtitle_file = f'{video_id}.en.{ext}'
                break

        # 字幕ファイルが見つかった場合、その内容を返す
        if subtitle_file:
            with open(subtitle_file, 'r', encoding='utf-8') as file:
                return file.read()
        else:
            return "字幕ファイルが見つかりませんでした。"

app = Flask(__name__)

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/process_video', methods=['GET'])
def process_video():
    video_id = request.args.get('video_id')
    # YouTube APIを使用して字幕ファイルを取得し、要約を生成するロジックをここに実装
    video_url = f'https://www.youtube.com/watch?v={video_id}'
    subtitles = download_and_read_subtitles(video_url)
    text = extract_text_from_vtt(f'{video_id}.en.vtt')
    summary = summarize(text)
    translated_summary = translate(summary)
    with open(f"data/{video_id}_summary.txt", "w") as file:
        file.write(summary)
    with open(f"data/{video_id}_summary_ja.txt", "w") as file:
        file.write(translated_summary)
    return jsonify({'summary': translated_summary})

@app.route('/save_memo', methods=['POST'])
def save_memo():
    video_id = request.args.get('video_id')
    memo = request.json['memo']
    with open(f"data/{video_id}_memo.txt", "w") as file:
        file.write(memo)
    return jsonify({'message': 'メモが保存されました'})


if __name__ == '__main__':
    app.run(debug=True)
