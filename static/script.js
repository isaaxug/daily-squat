// スクワット回数を受け取り、グラフ表示する関数
function drawChart(items) {
    // グラフデータの入れ物を用意
    const data = new google.visualization.DataTable();
    // IDがchartのHTML要素をグラフの描画先に設定
    const chart = new google.visualization.ColumnChart(
        document.getElementById('chart')
    );
    // グラフの見た目の設定
    const options = {
        title: 'Recent Activities',
        titleTextStyle: {
            fontSize: 24,
            color: 'white',
            bold: false,
        },
        backgroundColor: {
            fill: 'transparent'
        },
        colors: ['white'],
        hAxis: {
            titleTextStyle: {
                color: 'white'
            },
            textStyle: {
                color: 'white'
            },
            gridlineColor: 'none',
            baselineColor: 'none',
        },
        vAxis: {
            title: 'Count',
            titleTextStyle: {
                color: 'white'
            },
            textStyle: {
                color: 'white'
            },
            gridlineColor: 'none',
            baselineColor: 'white',
        },
        legend: {
            position: 'none'
        }
    };
    // 縦軸と横軸を設定
    data.addColumn('string', 'Count of Day');
    data.addColumn('number');
    // グラフにスクワット回数を追加
    items.forEach((item) => {
        data.addRow([dayjs(item.created_at).format('MM/DD'), item.count]);
    });
    // グラフの描画
    chart.draw(data, options);
}
// SSEのエンドポイントに接続し、メッセージを待ち受ける関数
function listenWakeword() {
    const evtSource = new EventSource('/wakeword');
    evtSource.onmessage = function(e) {
        // メッセージがあったら、/squat に遷移させる
        window.location.replace('/start-squat');
    }
}
// 最初に実行する関数
function init(items) {
    // Google Chartsライブラリの初期化
    google.charts.load('current', {packages: ['corechart', 'bar']});
    // 初期化が完了したら、drawChart関数を実行
    google.charts.setOnLoadCallback(function() {drawChart(items)});
    // SSEの接続
    listenWakeword();
}