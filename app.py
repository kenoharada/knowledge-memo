from flask import Flask, request, jsonify, render_template
from werkzeug.utils import secure_filename
import os
import yt_dlp
from summarize import extract_text_from_vtt, summarize, translate
from transcribe import transcribe

# ファイルが許可された拡張子を持っているかをチェックするヘルパー関数


def allowed_file(filename):
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower(
           ) in app.config['ALLOWED_EXTENSIONS']


def download_audio_from_youtube(video_url, output_path='audio'):
    # 出力ディレクトリが存在しない場合は作成
    if not os.path.exists(output_path):
        os.makedirs(output_path)

    # 音声をダウンロードするための設定
    ydl_opts = {
        'format': 'bestaudio/best',
        'outtmpl': output_path + '/%(title)s.%(ext)s',
        'postprocessors': [{
            'key': 'FFmpegExtractAudio',
            'preferredcodec': 'mp3',
            'preferredquality': '128',  # 128k
        }],
        'keepvideo': False,
        'restrictfilenames': True,
    }

    # ビデオ情報を取得し、ダウンロード
    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        info_dict = ydl.extract_info(video_url, download=True)
        downloaded_file = ydl.prepare_filename(info_dict)

    downloaded_file = downloaded_file.replace(
        '.webm', '.mp3').replace('.m4a', '.mp3')

    return downloaded_file


def download_and_read_subtitles(video_url):
    ydl_opts = {
        'writesubtitles': True,
        'skip_download': True,
        'outtmpl': '%(id)s',  # YouTubeの動画IDをファイル名に指定
        'subtitleslangs': ['en', 'en-GB'],  # 英語の字幕を指定
        'restrictfilenames': True,
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
            if os.path.exists(f'{video_id}.en-GB.{ext}'):
                # ファイル名を変更
                os.rename(f'{video_id}.en-GB.{ext}', f'{video_id}.en.{ext}')
                subtitle_file = f'{video_id}.en.{ext}'
                break

        # 字幕ファイルが見つかった場合、その内容を返す
        if subtitle_file:
            with open(subtitle_file, 'r', encoding='utf-8') as file:
                return file.read()
        else:
            return None


app = Flask(__name__)

# ファイルアップロードの設定
app.config['UPLOAD_FOLDER'] = 'uploads/'
app.config['ALLOWED_EXTENSIONS'] = {
    'mp4', 'mp3', 'm4a', 'mov', 'wav', 'webm'}  # 許可する拡張子


@app.route('/')
def index():
    return render_template('index.html')


@app.route('/process_video', methods=['GET'])
def process_video():
    video_id = request.args.get('video_id')
    video_url = f'https://www.youtube.com/watch?v={video_id}'
    subtitles = download_and_read_subtitles(video_url)
    if subtitles:
        text = extract_text_from_vtt(f'{video_id}.en.vtt')
    else:
        audio_file_path = download_audio_from_youtube(video_url)
        transcript_file_path = transcribe(audio_file_path)
        text = extract_text_from_vtt(transcript_file_path)
        subtitles = open(transcript_file_path, 'r').read()

    summary = summarize(text)
    translated_summary = translate(summary)
    with open(f"data/{video_id}_summary.txt", "w") as file:
        file.write(summary)
    with open(f"data/{video_id}_summary_ja.txt", "w") as file:
        file.write(translated_summary)
    return jsonify(
        {
            'summary': translated_summary,
            'subtitles': subtitles,
        }
    )


@app.route('/process_media', methods=['POST'])
def process_media():
    # ファイルがPOSTリクエストの一部として送信されたか確認
    if 'file' not in request.files:
        return jsonify({'error': 'ファイルがPOSTに含まれていません'}), 400
    file = request.files['file']
    if file.filename == '':
        return jsonify({'error': 'ファイル名がありません'}), 400
    if file and allowed_file(file.filename):
        filename = secure_filename(file.filename)
        file_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        file.save(file_path)
        # ファイルを処理して要約を生成するロジックを実装...
        # ここで要約や翻訳などの処理を行う
        transcript_file_path = transcribe(file_path)
        if transcript_file_path:
            text = extract_text_from_vtt(transcript_file_path)
            subtitles = open(transcript_file_path, 'r').read()
            summary = summarize(text)
            translated_summary = translate(summary)
            with open(f"data/{filename[:-4]}_summary.txt", "w") as file:
                file.write(summary)
            with open(f"data/{filename[:-4]}_summary_ja.txt", "w") as file:
                file.write(translated_summary)
            return jsonify(
                {
                    'summary': translated_summary,
                    'subtitles': subtitles,
                }
            )
        else:
            return jsonify({'error': 'ファイルの処理中にエラーが発生しました'}), 500
    else:
        return jsonify({'error': '許可されていないファイル形式です'}), 400


@app.route('/save_memo', methods=['POST'])
def save_memo():
    file_name = request.args.get('file_name')
    memo = request.json['memo']
    with open(f"data/{file_name}_memo.txt", "w") as file:
        file.write(memo)
    return jsonify({'message': 'メモが保存されました'})


if __name__ == '__main__':
    os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)  # アップロードフォルダを作成
    app.run(debug=True)
