from datetime import datetime, timedelta
import pathlib
import json
 
 
class Datastore:
    """スクワット記録の取得や保存を行う"""
    def __init__(self, data_path='data.json'):
        """初期化処理"""
        # データファイルへのパスを保持
        self.data_path = data_path
        # データファイルの存在を確認
        path = pathlib.Path(data_path)
        if not path.exists():
            # データファイルが存在しない場合は、
            # 14日間分のデータをカウント0で作成する
            items = []
            for i in range(15):
                date = (datetime.today() - timedelta(days=14-i)).isoformat()
                items.append({
                    "count": 0,
                    "created_at": date
                }) 
            # JSONファイルへの書き込み
            with open(path,'w') as f:
                json.dump(items, f)

    def add_item(self, item):
        """スクワット記録を追加する"""
        # スクワット記録を取得
        items = self._load()
        # 新しい記録を追加
        items.append(item)
        # ファイルへの保存
        self._save(items)
 
    def get_items(self, days=None):
        """スクワット記録の取得と整形を行う"""
        # スクワット記録を取得
        items = self._load()
        # もしdaysが指定されている場合は
        if days is not None:
            # 本日から days 日前までのスクワット記録に絞る
            items = self._filter_by_date(items, days)
        # 同じ日に行なったスクワットは１つの記録にまとめ、一覧を返す
        return self._accumulate_by_date(items)
 
    def _load(self):
        """スクワット記録をファイルから読み込む"""
        with open(self.data_path, 'r') as f:
            # JSON文字列を辞書型に変換
            items = json.load(f)
        return items
 
    def _save(self, items):
        """スクワット記録をファイルに保存する"""
        with open(self.data_path, 'w') as f:
            # 辞書型をJSON文字列に変換してファイルに書き込み
            json.dump(items, f)
 
    def _filter_by_date(self, items, days):
        """スクワット記録を指定した日数分に絞り込む"""
        filtered = []
        # days 日前の日付を計算
        start_date = datetime.now() - timedelta(days=days)
        for item in items:
            created_at = datetime.fromisoformat(item['created_at'])
            # もし start_date 以降の記録なら
            if created_at > start_date:
                # 一覧に追加する
                filtered.append(item)
        # 絞り込んだ記録を返す
        return filtered
 
    def _accumulate_by_date(self, items):
        """記録された日付が同じ要素をまとめる"""
        # 最初の要素で変数を初期化する
        first = items[0]
        result = [{'count': first['count'], 'created_at': first['created_at']}]
        previous = datetime.fromisoformat(first['created_at'])
        # 2番目の要素から最後の要素まで
        for item in items[1:]:
            current = datetime.fromisoformat(item['created_at'])
            # もし1つ前の要素と日付が同じなら
            if previous.date() is current.date():
                # 1つ前の要素のカウントに加える
                result[-1]['count'] += item['count']
                continue
            # 1つ前の要素と日付が違うなら、
            # 新しい要素として加える
            result.append({
                "count": item['count'],
                "created_at": item['created_at']
            })
            # 比較用の日付を更新
            previous = current

        return result


if __name__ == '__main__':
    ds = Datastore()
    print(ds.get_items())