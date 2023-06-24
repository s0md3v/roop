import cv2
import numpy as np
from PIL import Image

"""
下記を参考
1.[Python OpenCV の cv2.imread 及び cv2.imwrite で日本語を含むファイルパスを取り扱う際の問題への対処について - Qiita](https://qiita.com/SKYS/items/cbde3775e2143cad7455)  
2.[【OpenCV/Python】日本語の画像ファイル読込・保存 | イメージングソリューション](https://imagingsolution.net/program/python/opencv-python/read_save_image_files_in_japanese/#toc3)  

2に準じて読み書きの早い方を採用し、1に準じて失敗時対応を追加。

"""

def imread(filename, flags=cv2.IMREAD_COLOR, dtype=np.uint8):
	try:
		n = np.fromfile(filename, dtype)
		img = cv2.imdecode(n, flags)
		return img
	except Exception as e:
		print(e)
		return None


def imwrite(filename, img, params=None):
	try:
		# カラー画像のときは、BGRからRGBへ変換する
		if img.ndim == 3:
			img = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)

		# NumPyからPillowへ変換
		pil_image = Image.fromarray(img)

		# Pillowで画像ファイルへ保存
		pil_image.save(filename, params)
		return True

	except Exception as e:
		print(e)
		return False
