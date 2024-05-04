from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas
from PIL import Image


# 创建一个PDF文件
c = canvas.Canvas("example.pdf", pagesize=letter)

# 添加图片
c.drawImage("test.png", 100, 500, width=200, height=150)  # 请根据需要调整图片路径及大小

# 添加文本
c.drawString(100, 100, "这是一个文本说明。")

# 保存PDF文件
c.save()