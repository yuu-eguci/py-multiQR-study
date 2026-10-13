py-multiQR-study
===

OpenCV で、画像・動画・カメラ映像から複数の QR コードを読むやつ。

- Docker: 対応!
- Python: 3.14!
- Linter: ruff!
- Test: pytest!
- opencv-python-headless: 5.0.0.93!

## パッと実行してみたい

```bash
docker build -t py-multiqr-study .
mkdir -p out

# サンプルの画像と動画を作る
docker run --rm --user "$(id -u):$(id -g)" -v "$PWD/out:/out" py-multiqr-study \
  python make_samples.py --out-dir /out

# 画像を読んで、QR の枠つき画像を保存
docker run --rm --user "$(id -u):$(id -g)" -v "$PWD/out:/out" py-multiqr-study \
  python foo.py /out/sample.png --output /out/sample_result.png

# 動画を二値化して読み、結果のフレームも保存
docker run --rm --user "$(id -u):$(id -g)" -v "$PWD/out:/out" py-multiqr-study \
  python baz.py --video /out/sample.avi --no-window --save-frame --out-dir /out/frames
```

`hello-1`・`hello-2`・`テスト3` が表示される。
`out/sample_result.png` に枠つき画像、`out/frames/` に元映像と二値化した映像を並べた画像ができるよ。

## どれを使う?

| ファイル | やること |
| --- | --- |
| `foo.py` | 画像を読む。`--output` で枠つき画像も保存。 |
| `bar.py` | カメラや動画をそのまま読む。 |
| `baz.py` | カメラや動画を二値化して読む。`--thresh` は 0〜255、既定は 80。 |
| `make_samples.py` | QR が 3 つ並ぶ画像と、短い動画を作る。 |

動画ファイルなら `--video path/to/video.avi --no-window`。
カメラ番号なら `--video 0`。省略してもカメラ 0 になる。
Docker では `--no-window` を付けてね。

フレーム保存は `baz.py --save-frame --out-dir PATH`。
Docker では上の例みたいに、書き込めるフォルダをマウントする。
保存に失敗したら終了コード 1。入力画像そのものへの上書きはしない。

透過 PNG は白背景に重ねて読む。
読み取った改行や制御文字はエスケープして表示する。
Docker では 67,108,864 ピクセルを超える画像は読み込まない。

## 手元のカメラを使うなら

```bash
python3.14 -m venv .venv
. .venv/bin/activate
pip install -r requirements-gui.txt
python bar.py
python baz.py --video 0 --thresh 100
```

`q` で終了。`baz.py` は `a` / `z` でしきい値を変えられる。
実カメラと GUI の動作はまだ未確認。生成した画像・動画での読み取りは確認済みだよ。

## テストとか

```bash
docker run --rm py-multiqr-study ruff check .
docker run --rm py-multiqr-study ruff format --check .
docker run --rm py-multiqr-study pytest
```

テストでも、生成した画像・動画を本物の OpenCV で読む。カメラとウィンドウはテスト用の代役を使う。

## メモ

[nuxt-multiQR-study](https://github.com/yuu-eguci/nuxt-multiQR-study) から派生した Python 版。
二値化が効くかは画像次第。ぼやけた画像では逆に読みにくくなることもある。
QR の位置によって読み落とすこともあるので、読めた内容は確認してね。
連結 QR の読み取りは、今回の仕上げでは再確認していない。

`baz.py` は [OPTiM Tech Blog の記事](https://tech-blog.optim.co.jp/entry/2020/12/15/100000) を元にしているよ。
