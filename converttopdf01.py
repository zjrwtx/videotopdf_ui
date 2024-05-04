import os
from PIL import Image
from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas
import re

def parse_srt(srt_filename):
    with open(srt_filename, 'r', encoding='utf-8') as file:
        lines = file.read().split('\n\n')
        captions = {}
        for line in lines:
            parts = line.strip().split('\n')
            if len(parts) >= 3:
                start_time, end_time = parts[1].split(' --> ')
                caption_text = '\n'.join(parts[2:])
                captions[start_time] = caption_text
        return captions

def create_pdf(images_folder, srt_filename, output_filename):
    captions = parse_srt(srt_filename)
    c = canvas.Canvas(output_filename, pagesize=letter)
    current_page = 0
    for image_filename in sorted(os.listdir(images_folder)):
        if image_filename.endswith('.png'):
            # 提取图片名中的时间戳
            timestamp = image_filename.split('_')[1].split('.')[0]
            # 查找对应的字幕内容
            caption_text = captions.get(timestamp, "No caption found")
            
            image_path = os.path.join(images_folder, image_filename)
            img = Image.open(image_path)
            c.drawImage(img, 10, 750 - current_page * 750, width=img.width, height=img.height)
            
            c.setFont("Helvetica", 12)
            c.drawString(10, 750 - current_page * 750 - 50, caption_text)
            
            if (current_page + 1) * 750 < 750:
                current_page += 1
            else:
                c.showPage()
                current_page = 0
    
    c.save()
# Example usage
create_pdf('./output/test01', './input/test01.srt', 'output.pdf')