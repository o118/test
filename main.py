# coding: UTF-8
# stack_pdf_app.py
import os
import pathlib
import tkinter
import datetime
import cv2
import numpy as np
from pathlib import Path
from functools import partial
from pdf2image import convert_from_path
from tkinter import filedialog
from tkinter import messagebox
from PIL import Image


class StackPdfError(Exception):
    pass


black = np.array([0, 0, 0], dtype=np.uint8)
white = np.array([255, 255, 255], dtype=np.uint8)
red = np.array([255, 0, 0], dtype=np.uint8)
green = np.array([0, 255, 0], dtype=np.uint8)
blue = np.array([0, 0, 255], dtype=np.uint8)


# 対象PDFファイル取得処理
def ask_pdffile(_target):
    _target.set(tkinter.filedialog.askopenfilename(filetypes=[("PDF", ".pdf"), ("All", "*")]))


# 出力先ディレクトリ取得処理
def ask_dir(_target):
    _target.set(tkinter.filedialog.askdirectory())


# メイン処理
def main_proc():
    try:
        pdf1 = pathlib.Path(filepath1.get())
        pdf2 = pathlib.Path(filepath2.get())

        # PDFをビットマップに変換 (1枚目)
        cvimage1 = convert_pdf2image(pdf1)
        # ビットマップを2値化 (1枚目)
        cvimage1 = threshold(cvimage1)
        # 透過処理 (1枚目)
        cvimage1 = transparentWhiteColor(cvimage1)

        # PDFをビットマップに変換 (2枚目)
        cvimage2 = convert_pdf2image(pdf2)
        # ビットマップを2値化 (2枚目)
        cvimage2 = transparentWhiteColor(cvimage2)
        # 透過処理 (2枚目)
        cvimage2 = threshold(cvimage2)

        # 重ね合わせ
        stackimage = overlayImage(cvimage1, cvimage2, (0, 0))

        # 出力処理
        outfile = datetime.datetime.now(datetime.timezone(datetime.timedelta(hours=9))).strftime(
            "%Y%m%d%H%M%S") + ".png"
        outfull = os.path.join(outdir.get(), outfile)
        cv2.imwrite(outfull, stackimage)

        tkinter.messagebox.showinfo("完了", "完了しました。")
    except StackPdfError as e:
        tkinter.messagebox.showerror("エラー", e)
    except Exception as e:
        tkinter.messagebox.showerror("エラー", e)


# PDFファイル -> ビットマップ変換処理
def convert_pdf2image(pdffile):
    # 変換処理
    images = convert_from_path(pdffile, grayscale=True, dpi=300)

    if len(images) == 0:
        raise StackPdfError('PDFファイル <' + pdffile + '> のページ数が 0 です。')
    elif len(images) > 1:
        raise StackPdfError('PDFファイル <' + pdffile + '> のページ数が 1 より大きいです。 ページ数：' + len(images))

    cvimage = cv2.cvtColor(np.asarray(images[0]), cv2.COLOR_RGB2BGRA)
    return cvimage


# 白色の透過処理
def transparentWhiteColor(cvimage):
    cvimage[..., 3] = np.where(np.all(cvimage == 255, axis=-1), 0, 255)
    return cvimage


# PDFファイル -> ビットマップ変換処理
def threshold(gray_cvimage):
    # グレースケール変換
    ret, threshold_cvimage = cv2.threshold(gray_cvimage, 127, 255, cv2.THRESH_BINARY)
    return threshold_cvimage


# 重ね合わせ処理
def overlayImage(src, overlay, location):
    overlay_height, overlay_width = overlay.shape[:2]

    # 背景をPIL形式に変換
    src = cv2.cvtColor(src, cv2.COLOR_BGR2RGB)
    pil_src = Image.fromarray(src)
    pil_src = pil_src.convert('RGBA')

    # オーバーレイをPIL形式に変換
    overlay = cv2.cvtColor(overlay, cv2.COLOR_BGRA2RGBA)
    pil_overlay = Image.fromarray(overlay)
    pil_overlay = pil_overlay.convert('RGBA')

    # 画像を合成
    pil_tmp = Image.new('RGBA', pil_src.size, (255, 255, 255, 0))
    pil_tmp.paste(pil_overlay, location, pil_overlay)
    result_image = Image.alpha_composite(pil_src, pil_tmp)

    # OpenCV形式に変換
    return cv2.cvtColor(np.asarray(result_image), cv2.COLOR_RGBA2BGRA)


# メインウィンドウ
main_win = tkinter.Tk()
main_win.title("StackPdf")
main_win.geometry("500x180")

# メインフレーム
main_frm = tkinter.Frame(main_win)
main_frm.grid(column=0, row=0, sticky=tkinter.NSEW, padx=5, pady=10)

# 1つ目のファイル選択
filepath1 = tkinter.StringVar()
pdf_file1_label = tkinter.Label(main_frm, text="比較対象PDFファイル (1)")
pdf_file1_box = tkinter.Entry(main_frm, textvariable=filepath1)
pdf_file1_btn = tkinter.Button(main_frm, text="参照", command=partial(ask_pdffile, filepath1))

# 2つ目のファイル選択
filepath2 = tkinter.StringVar()
pdf_file2_label = tkinter.Label(main_frm, text="比較対象PDFファイル (2)")
pdf_file2_box = tkinter.Entry(main_frm, textvariable=filepath2)
pdf_file2_btn = tkinter.Button(main_frm, text="参照", command=partial(ask_pdffile, filepath2))

# 出力先選択
outdir = tkinter.StringVar()
outdir.set(os.environ['USERPROFILE'])
outdir_label = tkinter.Label(main_frm, text="出力先ディレクトリ")
outdir_box = tkinter.Entry(main_frm, textvariable=outdir)
outdir_btn = tkinter.Button(main_frm, text="参照", command=partial(ask_dir, outdir))

# ウィジェット作成（実行ボタン）
app_btn = tkinter.Button(main_frm, text="実行", command=main_proc)

# ウィジェットの配置
pdf_file1_label.grid(column=0, row=0, pady=10)
pdf_file1_box.grid(column=1, row=0, sticky=tkinter.EW, padx=5)
pdf_file1_btn.grid(column=2, row=0)
pdf_file2_label.grid(column=0, row=1, pady=10)
pdf_file2_box.grid(column=1, row=1, sticky=tkinter.EW, padx=5)
pdf_file2_btn.grid(column=2, row=1)
outdir_label.grid(column=0, row=2, pady=10)
outdir_box.grid(column=1, row=2, sticky=tkinter.EW, padx=5)
outdir_btn.grid(column=2, row=2)
app_btn.grid(column=2, row=3)

# 配置設定
main_win.columnconfigure(0, weight=1)
main_win.rowconfigure(0, weight=1)
main_frm.columnconfigure(1, weight=1)

main_win.mainloop()
