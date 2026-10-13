py-multiQR-study
===

🐍 OpenCV の `QRCodeDetector.detectAndDecodeMulti` で、1枚の画像・動画・カメラ映像から複数の QR コードを同時に読み取る勉強用リポジトリです。

- Docker: 対応!
- Python: 3.14!
- Linter: ruff!
- Test: pytest!
- opencv-python-headless 5.0.0.93!

## パッと実行してみたい

```bash
docker build -t py-multiqr-study .
mkdir -p out

# サンプルの QR 画像と動画を out/ に作ります。
docker run --rm --user "$(id -u):$(id -g)" -v "$PWD/out:/out" py-multiqr-study \
  python make_samples.py --out-dir /out

# 画像から複数の QR コードを読み取り、枠を描いた画像を保存します。(foo.py)
docker run --rm --user "$(id -u):$(id -g)" -v "$PWD/out:/out" py-multiqr-study \
  python foo.py /out/sample.png --output /out/sample_result.png

# 動画を二値化してから読み取り、結果のフレームを保存します。(baz.py)
docker run --rm --user "$(id -u):$(id -g)" -v "$PWD/out:/out" py-multiqr-study \
  python baz.py --video /out/sample.avi --no-window --save-frame --out-dir /out/frames
```

こんな感じに表示されます。

```
wrote /out/sample.png
wrote /out/sample.avi
hello-1
hello-2
テスト3
wrote /out/sample_result.png
frame 0001 (thresh 80): hello-1, hello-2, テスト3
...
frame 0012 (thresh 80): hello-1, hello-2, テスト3
```

`out/sample_result.png` には、読み取れた QR コードに緑の枠と文字列が描かれます。`out/frames/` には「元フレーム | 二値化して描画したフレーム」を横に並べた画像が保存されます。

## スクリプト

| ファイル | やること |
|---|---|
| `foo.py` | 画像を読み込んで `detectAndDecodeMulti` をかけます。透過 PNG は白い背景に重ねてから読みます。`--output` を付けると枠を描いた画像を保存します(入力画像と同じファイルには保存しません)。 |
| `bar.py` | カメラ(または動画)の映像に `detectAndDecodeMulti` をかけ、ウィンドウに表示します。読めた QR は緑、読めなかった QR は赤で囲みます。 |
| `baz.py` | カメラ(または動画)の映像を二値化してから読み取ります。しきい値は `--thresh` で 0〜255 の整数を指定します(省略時は 80)。ウィンドウ表示中は `a` / `z` キーでしきい値を変えられます。`q` で終了します。 |
| `make_samples.py` | `cv2.QRCodeEncoder` で、QR コードが3つ並んだサンプル画像と短い動画を作ります。 |
| `multiqr.py` | 上のスクリプトが共通で使う読み取り・描画の処理です。 |

`bar.py` と `baz.py` の `--video` は、`0` のような半角数字ならカメラ番号、それ以外なら動画ファイルのパスとして扱います(省略時はカメラ 0 です)。`--no-window` を付けるとウィンドウを出さずに標準出力だけで動きます(Docker ではウィンドウを出せないのでこちらを使います)。

読み取った文字列は、foo.py は1コード1行、bar.py と baz.py は1フレーム1行で表示します。制御文字や改行のような表示できない文字は `\x1b` や `\n` のようにエスケープして表示します。

`baz.py --save-frame` の保存先は `--out-dir` で指定します(省略時は `out/video`)。Docker ではイメージ内の `/app` に書き込めないので、上の例のようにマウントしたフォルダを指定してください。保存できなかったときはエラーを表示して終了コード 1 で止まります。

Docker イメージでは `OPENCV_IO_MAX_IMAGE_PIXELS` を 67108864(8192×8192)にしています。これより大きい画像は読み込まずに「画像を読み込めません」と表示します。

## ローカルでカメラを使う

カメラ映像をウィンドウで見るには、GUI 付きの opencv-python を使います。

```bash
python3.14 -m venv .venv
. .venv/bin/activate
pip install -r requirements-gui.txt
python bar.py
python baz.py --video 0 --thresh 100
```

## 開発

```bash
docker build -t py-multiqr-study .
docker run --rm py-multiqr-study ruff check .
docker run --rm py-multiqr-study ruff format --check .
docker run --rm py-multiqr-study pytest
```

テストは合成した QR 画像・動画に対して実際に OpenCV で検出・デコードします。カメラはテスト用の偽キャプチャを差し込んで確かめます。

## 分かったこと

- opencv.js には `detectAndDecodeMulti` がありません([nuxt-multiQR-study](https://github.com/yuu-eguci/nuxt-multiQR-study) で確認しました)。そのため、このリポジトリでは Python の OpenCV を使っています。
- `detectAndDecodeMulti` は、1枚の画像に並んだ単一の QR コードを複数まとめて読めます。
    - 二値化すると読みやすくなります(baz.py)。
    - 連結 QR コードは `detectAndDecodeMulti` ではそもそも読めません。
- baz.py は [OPTiM Tech Blog の記事](https://tech-blog.optim.co.jp/entry/2020/12/15/100000) のコードを元にしています。
