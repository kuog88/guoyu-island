"""把「全字庫正楷體 TW-Kai」切成只含遊戲用到的字的網路字型 game/fonts/twkai.woff2。

各裝置的內建楷體不一樣（手機常常沒有標楷體，會改用日文或大陸字形的字型），
所以字卡、題目一律用這份依教育部標準字形的楷體，每台裝置看到的寫法都一樣。

字型來源：全字庫 https://www.cns11643.gov.tw/opendata/Fonts_Kai.zip（政府資料開放授權條款第 1 版）
把 TW-Kai-98_1.ttf 放在 fonts_src/ 再執行；build_game.py 產生遊戲時會自動呼叫。
"""
import glob
import os
import re

from fontTools import subset

SRC = "fonts_src/TW-Kai-98_1.ttf"
OUT = "game/fonts/twkai.woff2"


def used_chars():
    text = ""
    for p in ["game/index.html"] + glob.glob("game/data/*.json"):
        text += open(p, encoding="utf-8").read()
    # 中日韓文字、注音、全形標點
    return sorted(set(c for c in text if re.match(r"[\u2e80-\u9fff\uf900-\ufaff\u3000-\u303f\u3100-\u312f\u02c7-\u02d9\uff00-\uffef]", c)) | set("ˉˊˇˋ˙"))


def main():
    if not os.path.exists(SRC):
        print("找不到", SRC, "，略過字型（沿用現有的 twkai.woff2）")
        return
    chars = used_chars()
    os.makedirs("game/fonts", exist_ok=True)
    opts = subset.Options()
    opts.flavor = "woff2"
    opts.layout_features = ["*"]
    font = subset.load_font(SRC, opts)
    sub = subset.Subsetter(opts)
    sub.populate(text="".join(chars))
    sub.subset(font)
    cmap = font.getBestCmap()
    missing = [c for c in chars if ord(c) not in cmap]
    subset.save_font(font, OUT, opts)
    print("font", len(chars), "chars,", os.path.getsize(OUT) // 1024, "KB, 缺字:", "".join(missing))


if __name__ == "__main__":
    main()
