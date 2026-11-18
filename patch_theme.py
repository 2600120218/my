# -*- coding: utf-8 -*-
"""把主题字体统一替换为微软雅黑，避免打开时缺字体回退。"""
import re
import shutil
import zipfile

SRC = "骆绍杰-电气工程及其自动化-职业生涯规划.pptx"
TMP = "_theme_tmp.pptx"
FONT = "微软雅黑"

zin = zipfile.ZipFile(SRC, "r")
zout = zipfile.ZipFile(TMP, "w", zipfile.ZIP_DEFLATED)
for item in zin.infolist():
    data = zin.read(item.filename)
    if item.filename.startswith("ppt/theme/theme") and item.filename.endswith(".xml"):
        t = data.decode("utf-8")
        t = re.sub(r'(<a:majorFont><a:latin typeface=")[^"]*(")', r"\g<1>" + FONT + r"\g<2>", t)
        t = re.sub(r'(<a:minorFont><a:latin typeface=")[^"]*(")', r"\g<1>" + FONT + r"\g<2>", t)
        t = re.sub(r'(<a:majorFont>.*?<a:ea typeface=")[^"]*(")', r"\g<1>" + FONT + r"\g<2>", t, flags=re.S)
        t = re.sub(r'(<a:minorFont>.*?<a:ea typeface=")[^"]*(")', r"\g<1>" + FONT + r"\g<2>", t, flags=re.S)
        data = t.encode("utf-8")
    zout.writestr(item, data)
zout.close()
zin.close()
shutil.move(TMP, SRC)
print("theme patched")
