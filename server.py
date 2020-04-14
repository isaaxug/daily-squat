from flask import Flask, render_template, Response, redirect, session
from datastore import Datastore
from datetime import datetime
import wakeword as wa
import squat as sq
import cv2
import time


# Flaskサーバーの初期化
app = Flask(__name__)
# データストアの初期化
datastore = Datastore('data.json')
# ウェイクワード検知の初期化
wakeword_detector = wa.Detector('./ai_models/wakeword-detection.h5')
# 人体検知の初期化
squat_detector = sq.Detector('./ai_models/person_detection.tflite')
squat_detector.start()
# カウンターの作成
counter = sq.Counter()


# ルートパス (/) にアクセスがあれば実行する
@app.route('/')
def index():
    # 直近２週間分のスクワット記録を取得
    items = datastore.get_items(days=14)
    # クライアントに index.html を返す
    return render_template('index.html', items=items)

# /wakeword にアクセスがあれば実行する
@app.route('/wakeword')
def wakeword():
    detected = False
    # ウェイクワードの検知時に呼び出されるコールバック関数
    def on_detected(score):
        nonlocal detected
        detected = True

    # ウェイクワード検知を開始
    wakeword_detector.start(callback=on_detected)
    while True:
        if detected:
            time.sleep(1)
            wakeword_detector.stop()
            # ブラウザ側にメッセージを送信する
            return Response('event: message\ndata: detected\n\n', 
                            mimetype='text/event-stream')

        time.sleep(0.1)

# /squat にアクセスがあれば実行する
@app.route('/start-squat')
def start_squat():
    # ウェイクワード検知が行われていたら停止を行う
    if wakeword_detector.is_active():
        wakeword_detector.stop()
    # クライアントに squat.html を返す
    return render_template('squat.html')

# /camera.mjpeg にアクセスがあれば実行する
@app.route('/camera.mjpeg')
def camera():
    def gen():
        while True:
            # スクワットの状態と最新のフレームを取得
            squatted, frame = squat_detector.process_frame(counter.get())
            if squatted:
                counter.increment()
            # フレームをJPEGに変換
            ret, jpeg = cv2.imencode('.jpg', frame)
            # レスポンスデータの作成
            yield (b'--frame\n'
                b'Content-Type: image/jpeg\n\n' + jpeg.tobytes() + b'\n\n')

    # クライアントにMotion JPEGを配信
    return Response(gen(),
                    mimetype='multipart/x-mixed-replace; boundary=frame')

# /finish-squat にアクセスがあれば実行する
@app.route('/finish-squat')
def finish_squat():
    # 現在のカウントと日付・時刻を保存
    item = {
        "count": counter.get(),
        "created_at": datetime.now().isoformat(),
    }
    datastore.add_item(item)
    # カウンターを0に戻す
    counter.reset()
    # ホーム画面に遷移させる
    return redirect('/')


if __name__ == '__main__':
    # サーバーを起動
    app.run(
        # 開発時
        # host='0.0.0.0',
        # 完成時
        host='localhost',
        debug=False,
        threaded=True,
        use_reloader=False
    )
