// npm install jspdf --save
// 导入jsPDF库
const { jsPDF } = require('jspdf');

// 创建一个新的PDF文档实例
const doc = new jsPDF();

// 添加文本到PDF中
doc.text('Hello World!', 10, 10); // 在坐标(10, 10)处添加文本"Hello World!"

// 添加图片到PDF中（假设你已经有了一个图片URL）
const imageUrl = 'test.png'; // 替换为你的图片路径
doc.addImage(imageUrl, 'PNG', 10, 20, 50, 50); // 在坐标(10, 20)处添加图片，尺寸为50x50

// 保存PDF文件
doc.save('myDocument.pdf');