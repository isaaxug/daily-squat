from tensorflow import keras
import numpy as np
import pyaudio


class Detector:
    """音声をマイクから読み込み、ウェイクワード検知を行う"""

    def __init__(self, model_path, threshold=0.5, debug=False,
                channels=1, rate=44100, chunk=1024):
        """初期化処理"""
        # モデルデータの読み込み
        self.model = keras.models.load_model(model_path, compile=False)
        # ワードの検出を判別するしきい値の設定
        self.threshold = threshold
        # ウェイクワードの検知時に呼び出されるコールバック関数
        self.callback=None
        # 検知スコアの確認用
        self.debug = debug
        # 音声処理のスキップ用
        self.skip_count = 0

        # PyAudioオブジェクトの作成
        self.audio = pyaudio.PyAudio()
        # オーディオ設定
        self.stream = self.audio.open(
            channels=channels, # チャンネル数
            rate=rate, # サンプリングレート
            format=pyaudio.paInt16, # 量子化ビット数
            frames_per_buffer=chunk, # 1度に読み込む音声データのサイズ
            input=True, # マイク入力を有効化
            start=False, # マイク接続時に自動的に読み込みを開始しない
            stream_callback=self._detect # 音声データ処理用の関数を設定 
        )

    def start(self, callback):
        """ウェイクワード検知の開始"""
        self.callback=callback
        self.stream.start_stream()

    def is_active(self):
        """ウェイクワード検知が行われているか確認"""
        return self.stream.is_active()

    def stop(self):
        """ウェイクワード検知の停止"""
        self.stream.stop_stream()

    def close(self):
        """ウェイクワード検知の終了"""
        self.stream.close()
        self.audio.terminate()

    def _detect(self, in_data, frame_count, time_info, status):
        """チャンクごとに音声データを処理するコールバック関数"""
        data = np.frombuffer(in_data, dtype='int16')
        # スペクトログラムの作成
        x = self._spectrogram(data)
        # 入力データをモデルの入力形式に合わせて変換
        x = x.swapaxes(0, 1)
        x = np.expand_dims(x, axis=0)
        # 推論の実行
        score = self.model.predict(x)
        # 誤検知を防ぐため、最初の5チャンクを無視する
        if self.skip_count < 5:
            self.skip_count += 1
            return (None, pyaudio.paContinue)
        if self.debug:
            print(score.max())
        # ウェイクワード検知の判定
        if np.any(score > self.threshold):
            # 検知している場合はコールバック関数を呼び出す
            self.callback(score.max())

        return (None, pyaudio.paContinue)

    def _spectrogram(self, data, nfft=256, fs=44100, noverlap=128):
        """スペクトログラムを作成する関数"""
        window = np.hanning(nfft)
        data = self._stride_windows(data, nfft, noverlap)
        data = data * window.reshape((-1, 1))
        data = np.fft.fft(data, n=nfft, axis=0)[:129, :]
        data = np.conj(data) * data
        slc = slice(1, -1, None)
        data[slc] *= 2.
        data /= fs
        data /= (np.abs(window)**2).sum()
        return data.real

    def _stride_windows(self, data, nfft=256, noverlap=128):
        step = nfft - noverlap
        shape = (nfft, (data.shape[-1]-noverlap)//step)
        strides = (data.strides[0], step*data.strides[0])
        return np.lib.stride_tricks.as_strided(data, shape=shape, strides=strides)


if __name__ == '__main__':
    import time

    detector = Detector(
        model_path='./ai_models/wakeword-detection.h5',
        threshold=0.5,
        debug=True
    )

    detected = False
    def on_detected(score):
        global detected
        detected = True

    detector.start(callback=on_detected)
    while True:
        if detected:
            print('ウェイクワードを検知しました！')
            detector.stop()
            break
        time.sleep(0.1)

    detector.close()