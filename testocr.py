import os
import base64
import requests
import json

# OCR API的URL
ocr_api_url = "http://127.0.0.1:1224/api/ocr"

# 图像文件夹的路径
image_folder_path = "output/test01"

# 遍历文件夹中的所有文件
for filename in os.listdir(image_folder_path):
    # 检查文件是否是图像
    if filename.lower().endswith(('.png', '.jpg', '.jpeg', '.bmp', '.gif', '.tiff')):
        # 构建文件的完整路径
        file_path = os.path.join(image_folder_path, filename)
        
        # 读取图像文件并转换为Base64编码
        with open(file_path, "rb") as image_file:
            encoded_string = base64.b64encode(image_file.read()).decode('utf-8')
        
        # 构建请求数据
        data = {
            "base64": encoded_string
        }
        headers = {"Content-Type": "application/json"}
        data_str = json.dumps(data)
        
        # 发送POST请求
        response = requests.post(ocr_api_url, data=data_str, headers=headers)
        
        # 检查响应状态
        if response.status_code == 200:
            # 解析响应内容
            res_dict = json.loads(response.text)
            
            # 初始化一个空字符串，用于存储合并后的文本
            merged_text = ""
            
            # 检查返回的数据结构
            if "data" in res_dict and isinstance(res_dict["data"], list):
                # 遍历每一行的文本
                for line in res_dict["data"]:
                    text = line.get("text", "")
                    merged_text += text + " "  # 添加一个空格作为分隔符，避免粘连在一起
            else:
                print("没有检测到文本行。")
            
            # 打印合并后的文本
            print(f"图像文件 {filename} 的合并文本:")
            print(merged_text)
        else:
            print(f"请求失败，状态码：{response.status_code}, 文件：{filename}")