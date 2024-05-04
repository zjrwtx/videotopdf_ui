pdf_file = './output/test01.pdf' 
from pypdf import PdfReader

reader = PdfReader(pdf_file)
number_of_pages = len(reader.pages)
page = reader.pages[0]
text = page.extract_text()

print(text, end='')

print(number_of_pages)
print("hello")