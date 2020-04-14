from imutils.video.pivideostream import PiVideoStream
import cv2
import tensorflow as tf
import numpy as np


class Detector:
    """カメラ映像を読み込み、人体検知を用いたスクワット回数の計測を行う"""

    def __init__(self, model_path, threshold=0.8,
                 resolution=(512, 352), framerate=5, head_line=80):
        """初期化処理"""  
        # True: 立っている状態, False: かがんでいる状態
        self.is_standing = True
        # is_standing の判定に使うしきい値
        self.head_line = head_line

        # カメラへの接続
        self.camera = PiVideoStream(
            resolution=resolution,
            framerate=framerate
        )

        # どのくらいの尤度で人として検知するか
        self.threshold = threshold
        # TFLiteモデルの読み込み
        self.detector = tf.lite.Interpreter(model_path=model_path)
        # TFLiteの初期化
        self.detector.allocate_tensors()
        self.detector.set_num_threads(4)
        # モデルの入出力情報の取得
        self.input_details = self.detector.get_input_details()
        self.output_details = self.detector.get_output_details()
        self.input_height = self.input_details[0]['shape'][1]
        self.input_width = self.input_details[0]['shape'][2]

    def start(self):
        """カメラ映像の読み込み開始"""
        self.camera.start()

    def stop(self):
        """カメラ映像の読み込みを終了"""
        self.camera.stop()

    def process_frame(self, count):
        squatted = False
        # 映像フレームの読み込み
        frame = self.camera.read()
        # 人体検知の実行
        detection = self._detect(frame)
        if detection:
            # 検知結果をフレームに描画
            self._draw_box(frame, detection)
            # スクワットの判定
            squatted = self._update_state(head_position=detection[4])

        # head_line の位置を描画
        cv2.line(frame,(0, self.head_line),(frame.shape[1], self.head_line),
                 (0,255,255),2)
        # is_standing 状態の描画
        cv2.putText(frame, f'standing: {self.is_standing}', (20,20), cv2.FONT_HERSHEY_SIMPLEX,
                    0.5, (0, 255, 255), 1)
        # スクワット回数を描画
        cv2.putText(frame, str(count), (5,332), cv2.FONT_HERSHEY_SIMPLEX,
                    4, (0, 255, 255), 2)

        return squatted, frame

    def _detect(self, frame):
        """人体検知の実行"""
        # 映像フレームのサイズを取得
        height, width, channels = frame.shape
        # 入力データの用意
        resized = cv2.resize(frame, (self.input_width, self.input_height))
        data = np.expand_dims(resized, axis=0)
        self.detector.set_tensor(self.input_details[0]['index'], data)
        # 推論の実行
        self.detector.invoke()
        # 推論結果の取得
        boxes = self.detector.get_tensor(self.output_details[0]['index'])
        scores = self.detector.get_tensor(self.output_details[2]['index'])
        num_boxes = self.detector.get_tensor(self.output_details[3]['index'])
        if int(num_boxes) < 1:
            return
        # 最も尤度の高かった物体の情報のみ取得
        top, left, bottom, right = boxes[0][0]
        score = scores[0][0]
        # 尤度が threshold 以下の場合は無視する
        if score < self.threshold:
            return
        # 矩形座標をオリジナル画像用にスケール
        xmin = int(left * width)
        ymin = int(bottom * height)
        xmax = int(right * width)
        ymax = int(top * height)
        
        return (score, xmin, ymin, xmax, ymax)

    def _draw_box(self, frame, detection):
        """推論結果を映像フレームに描画"""
        score, xmin, ymin, xmax, ymax = detection
        # 検知した人の位置を描画
        cv2.rectangle(frame, (xmin, ymin), (xmax, ymax), (0, 255, 0), 2)
        # スクワットを行う際の目印となる点を描画
        xcent = int(((xmax - xmin) // 2) + xmin)
        cv2.circle(frame, (xcent, ymax), 3, (0, 0, 255), 5, 8, 0)
        # 尤度の描画
        label = 'person: {:.2f}%'.format(score * 100)
        y = ymin - 15 if ymin - 15 > 15 else ymin + 15
        cv2.putText(frame, label, (xmin, y), cv2.FONT_HERSHEY_SIMPLEX,
                    0.5, (0, 255, 0), 1)

    def _update_state(self, head_position):
        """
        立ち・屈みの状態を更新し、
        屈みから立ちの状態になった場合はスクワットした判定を返す
        """
        current = head_position < self.head_line
        # もし以前と状態が違うなら
        if current is not self.is_standing:
            # 新しい状態に更新する
            self.is_standing = current
            # 屈みから立ちの状態になった場合は
            if current:
                # Trueを返す
                return True
        # そうでない場合はFalseを返す
        return False


class Counter:
    """スクワットの回数計算をおこなう"""
    def __init__(self):
        """初期化処理"""
        self.count = 0

    def get(self):
        """現在のカウントを取得"""
        return self.count

    def increment(self):
        """カウントを1増やす"""
        self.count += 1

    def reset(self):
        """カウントを0に戻す"""
        self.count = 0


if __name__ == '__main__':
    import time

    detector = Detector(model_path='./ai_models/person_detection.tflite')
    detector.start()
    counter = Counter()
    time.sleep(2)

    while True:
        try:
            squatted, frame = detector.process_frame(counter.get())
            if squatted:
                counter.increment()
            cv2.imshow('frame', frame)
            if cv2.waitKey(1) & 0xFF == ord('q'):
                break
        except KeyboardInterrupt:
            break

    detector.stop()
    cv2.destroyAllWindows()