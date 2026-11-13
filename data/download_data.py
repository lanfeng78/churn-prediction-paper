"""下载 UCI Online Retail II 原始数据到 data/retail_ii.csv

UCI 官方站点直连存在限速（实测约 14 KB/s），因此默认走 Hugging Face 镜像。
也可手动下载官方 zip 后解压，把其中的 "online_retail_II.csv" 放到本目录并改名。
"""
import os
import sys
import urllib.request

BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA = os.path.join(BASE, "data")
TARGET = os.path.join(DATA, "retail_ii.csv")

MIRROR = ("https://huggingface.co/datasets/attik/Online-Retail-II-UCI/"
          "resolve/main/online_retail_II.csv")


def _progress(block, block_size, total):
    done = block * block_size
    if total > 0:
        pct = min(done / total * 100, 100)
        sys.stdout.write("\r%6.1f%%  %.1f / %.1f MB" % (pct, done / 1e6, total / 1e6))
    else:
        sys.stdout.write("\r%.1f MB" % (done / 1e6))
    sys.stdout.flush()


def main():
    os.makedirs(DATA, exist_ok=True)
    if os.path.exists(TARGET) and os.path.getsize(TARGET) > 50_000_000:
        print("已存在 %s（%.1f MB），跳过下载。" % (TARGET, os.path.getsize(TARGET) / 1e6))
        return
    print("下载 Online Retail II ->  %s" % TARGET)
    urllib.request.urlretrieve(MIRROR, TARGET, reporthook=_progress)
    print("\n完成：%.1f MB" % (os.path.getsize(TARGET) / 1e6))


if __name__ == "__main__":
    main()
