import os
import time
import cv2
import imutils
import shutil
import img2pdf
import glob
from skimage.metrics import structural_similarity
import gradio as gr
import tempfile
import whisper
from moviepy.editor import VideoFileClip
from PIL import Image, ImageDraw, ImageFont

############# Define constants

OUTPUT_SLIDES_DIR = f"./output"

FRAME_RATE = 3                   # no.of frames per second that needs to be processed, fewer the count faster the speed
WARMUP = FRAME_RATE              # initial number of frames to be skipped
FGBG_HISTORY = FRAME_RATE * 15   # no.of frames in background object
VAR_THRESHOLD = 16               # Threshold on the squared Mahalanobis distance between the pixel and the model to decide whether a pixel is well described by the background model.
DETECT_SHADOWS = False            # If true, the algorithm will detect shadows and mark them.
MIN_PERCENT = 0.1                # min % of diff between foreground and background to detect if motion has stopped
MAX_PERCENT = 3                  # max % of diff between foreground and background to detect if frame is still in motion
SSIM_THRESHOLD = 0.9             # SSIM threshold of two consecutive frame


def get_frames(video_path):
    '''A fucntion to return the frames from a video located at video_path
    this function skips frames as defined in FRAME_RATE'''
    
    
    # open a pointer to the video file initialize the width and height of the frame
    vs = cv2.VideoCapture(video_path)
    if not vs.isOpened():
        raise Exception(f'unable to open file {video_path}')


    total_frames = vs.get(cv2.CAP_PROP_FRAME_COUNT)
    frame_time = 0
    frame_count = 0

    # loop over the frames of the video
    while True:
        vs.set(cv2.CAP_PROP_POS_MSEC, frame_time * 1000)    # move frame to a timestamp
        frame_time += 1/FRAME_RATE

        (_, frame) = vs.read()
        # if the frame is None, then we have reached the end of the video file
        if frame is None:
            break

        frame_count += 1
        yield frame_count, frame_time, frame

    vs.release()
 


def detect_unique_screenshots(video_path, output_folder_screenshot_path, progress=gr.Progress()):
    '''Extract unique screenshots from video'''
    fgbg = cv2.createBackgroundSubtractorMOG2(history=FGBG_HISTORY, varThreshold=VAR_THRESHOLD,detectShadows=DETECT_SHADOWS)

    captured = False
    start_time = time.time()
    (W, H) = (None, None)

    # Get total frames for progress calculation
    cap = cv2.VideoCapture(video_path)
    total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
    cap.release()

    screenshoots_count = 0
    last_screenshot = None
    saved_files = []
    
    progress(0, desc="初始化视频处理...")
    
    for frame_count, frame_time, frame in get_frames(video_path):
        # Update progress
        progress((frame_count / total_frames) * 0.7, desc=f"处理视频帧 {frame_count}/{total_frames}")
        
        orig = frame.copy()
        frame = imutils.resize(frame, width=600)
        mask = fgbg.apply(frame)

        if W is None or H is None:
            (H, W) = mask.shape[:2]

        p_diff = (cv2.countNonZero(mask) / float(W * H)) * 100

        if p_diff < MIN_PERCENT and not captured and frame_count > WARMUP:
            captured = True
            filename = f"{screenshoots_count:03}_{round(frame_time/60, 2)}.png"
            path = os.path.join(output_folder_screenshot_path, filename)

            image_ssim = 0.0
            if last_screenshot is not None:
                image_ssim = structural_similarity(last_screenshot, orig, channel_axis=2, data_range=255)

            if image_ssim < SSIM_THRESHOLD:
                try:
                    progress(0.7 + (screenshoots_count * 0.1), desc=f"保存截图 {screenshoots_count + 1}")
                    print("saving {}".format(path))
                    cv2.imwrite(str(path), orig)
                    last_screenshot = orig
                    saved_files.append(path)
                    screenshoots_count += 1
                except Exception as e:
                    print(f"Error saving image: {str(e)}")
                    continue

        elif captured and p_diff >= MAX_PERCENT:
            captured = False

    progress(0.8, desc="截图提取完成")
    print(f'{screenshoots_count} screenshots Captured!')
    print(f'Time taken {time.time()-start_time}s')
    return saved_files


def initialize_output_folder(video_path):
    '''Clean the output folder if already exists'''
    # Create a safe folder name from video filename
    video_filename = os.path.splitext(os.path.basename(video_path))[0]
    # Replace potentially problematic characters
    safe_filename = "".join(x for x in video_filename if x.isalnum() or x in (' ', '-', '_'))
    output_folder_screenshot_path = os.path.join(OUTPUT_SLIDES_DIR, safe_filename)

    if os.path.exists(output_folder_screenshot_path):
        shutil.rmtree(output_folder_screenshot_path)

    os.makedirs(output_folder_screenshot_path, exist_ok=True)
    print('initialized output folder', output_folder_screenshot_path)
    return output_folder_screenshot_path


def convert_screenshots_to_pdf(video_path, output_folder_screenshot_path):
    # Create a safe filename
    video_filename = os.path.splitext(os.path.basename(video_path))[0]
    safe_filename = "".join(x for x in video_filename if x.isalnum() or x in (' ', '-', '_'))
    output_pdf_path = os.path.join(OUTPUT_SLIDES_DIR, f"{safe_filename}.pdf")
    
    try:
        print('output_folder_screenshot_path', output_folder_screenshot_path)
        print('output_pdf_path', output_pdf_path)
        print('converting images to pdf..')
        
        # Get all PNG files and ensure they exist
        png_files = sorted(glob.glob(os.path.join(output_folder_screenshot_path, "*.png")))
        if not png_files:
            raise Exception("No PNG files found to convert to PDF")
            
        with open(output_pdf_path, "wb") as f:
            f.write(img2pdf.convert(png_files))
            
        print('Pdf Created!')
        print('pdf saved at', output_pdf_path)
        return output_pdf_path
    except Exception as e:
        print(f"Error creating PDF: {str(e)}")
        raise


def video_to_slides(video_path, progress=gr.Progress()):
    progress(0.1, desc="准备处理视频...")
    output_folder_screenshot_path = initialize_output_folder(video_path)
    saved_files = detect_unique_screenshots(video_path, output_folder_screenshot_path, progress)
    return output_folder_screenshot_path, saved_files


def slides_to_pdf(video_path, output_folder_screenshot_path, saved_files, progress=gr.Progress()):
    video_filename = os.path.splitext(os.path.basename(video_path))[0]
    safe_filename = "".join(x for x in video_filename if x.isalnum() or x in (' ', '-', '_'))
    output_pdf_path = os.path.join(OUTPUT_SLIDES_DIR, f"{safe_filename}.pdf")
    
    try:
        progress(0.9, desc="正在生成PDF...")
        print('output_folder_screenshot_path', output_folder_screenshot_path)
        print('output_pdf_path', output_pdf_path)
        
        if not saved_files:
            raise Exception("未从视频中捕获到截图")
            
        existing_files = [f for f in saved_files if os.path.exists(f)]
        if not existing_files:
            raise Exception("未找到保存的截图文件")
            
        with open(output_pdf_path, "wb") as f:
            f.write(img2pdf.convert(existing_files))
            
        progress(1.0, desc="处理完成！")
        print('PDF创建成功！')
        print('PDF保存位置:', output_pdf_path)
        return output_pdf_path
    except Exception as e:
        print(f"创建PDF时出错: {str(e)}")
        raise


def run_app(video_path, progress=gr.Progress()):
    try:
        if not video_path:
            raise gr.Error("请选择要处理的视频文件")
            
        progress(0, desc="开始处理...")
        output_folder_screenshot_path, saved_files = video_to_slides(video_path, progress)
        return slides_to_pdf(video_path, output_folder_screenshot_path, saved_files, progress)
    except Exception as e:
        raise gr.Error(f"处理失败: {str(e)}")


def process_video_file(video_file):
    """Handle uploaded video file and return PDF"""
    try:
        # If video_file is a string (path), use it directly
        if isinstance(video_file, str):
            if video_file.strip() == "":
                return None
            return run_app(video_file)
            
        # If it's an uploaded file, create a temporary file
        if video_file is not None:
            # Generate a unique filename for the temporary video
            temp_filename = f"temp_video_{int(time.time())}.mp4"
            temp_path = os.path.join(tempfile.gettempdir(), temp_filename)
            
            try:
                if hasattr(video_file, 'name'):  # If it's already a file path
                    shutil.copyfile(video_file, temp_path)
                else:  # If it's file content
                    with open(temp_path, 'wb') as f:
                        f.write(video_file)
                
                # Process the video
                output_folder_screenshot_path, saved_files = video_to_slides(temp_path)
                pdf_path = slides_to_pdf(temp_path, output_folder_screenshot_path, saved_files)
                
                # Cleanup
                if os.path.exists(temp_path):
                    os.unlink(temp_path)
                return pdf_path
                
            except Exception as e:
                if os.path.exists(temp_path):
                    os.unlink(temp_path)
                raise gr.Error(f"处理视频时出错: {str(e)}")
        return None
    except Exception as e:
        raise gr.Error(f"处理视频时出错: {str(e)}")


def extract_audio_and_transcribe(video_path, progress=gr.Progress()):
    """Extract audio from video and transcribe it using Whisper"""
    progress(0, desc="正在提取音频...")
    
    # Load the video and extract audio
    video = VideoFileClip(video_path)
    audio = video.audio
    
    # Save audio to temporary file
    temp_audio = tempfile.mktemp(suffix='.wav')
    audio.write_audiofile(temp_audio)
    
    progress(0.3, desc="正在转录音频...")
    
    # Load Whisper model and transcribe
    model = whisper.load_model("base")
    result = model.transcribe(temp_audio)
    print("完成的转录文本结果如下："+result)
    
    # Clean up
    os.remove(temp_audio)
    video.close()
    
    # Process segments with timestamps
    segments = []
    for segment in result["segments"]:
        segments.append({
            "start": segment["start"],
            "end": segment["end"],
            "text": segment["text"].strip()
        })
    
    return segments

def add_text_to_image(image_path, text):
    """Add text below the image"""
    # Open image
    img = Image.open(image_path)
    width, height = img.size
    
    # Create new image with space for text
    font_size = 30
    font = ImageFont.truetype("arial.ttf", font_size)
    text_height = font_size * (text.count('\n') + 2)  # Add padding
    
    new_img = Image.new('RGB', (width, height + text_height), 'white')
    new_img.paste(img, (0, 0))
    
    # Add text
    draw = ImageDraw.Draw(new_img)
    draw.text((10, height + 10), text, font=font, fill='black')
    
    # Save the modified image
    new_img.save(image_path)

def process_video_with_transcription(video_path, output_folder_screenshot_path, progress=gr.Progress()):
    """Process video with transcription and add text to images"""
    # First, get the transcription
    segments = extract_audio_and_transcribe(video_path, progress)
    
    # Then get the frames as before
    saved_files = detect_unique_screenshots(video_path, output_folder_screenshot_path, progress)
    
    progress(0.8, desc="正在添加字幕...")
    
    # Match transcription segments with images
    for i, image_path in enumerate(saved_files):
        # Extract timestamp from filename (format: 000_1.23.png)
        timestamp = float(os.path.basename(image_path).split('_')[1].split('.png')[0])
        
        # Find relevant text segments for this timestamp
        relevant_text = []
        for segment in segments:
            if segment["start"] <= timestamp * 60 <= segment["end"]:
                relevant_text.append(segment["text"])
        
        # Add text to image
        if relevant_text:
            text = "\n".join(relevant_text)
            add_text_to_image(image_path, text)
    
    progress(0.9, desc="处理完成...")
    return saved_files

def run_app_with_transcription(video_path, progress=gr.Progress()):
    try:
        if not video_path:
            raise gr.Error("请选择要处理的视频文件")
            
        progress(0, desc="开始处理...")
        output_folder_screenshot_path = initialize_output_folder(video_path)
        saved_files = process_video_with_transcription(video_path, output_folder_screenshot_path, progress)
        return slides_to_pdf(video_path, output_folder_screenshot_path, saved_files, progress)
    except Exception as e:
        raise gr.Error(f"处理失败: {str(e)}")

def process_video_file_with_transcription(video_file):
    """Handle uploaded video file and return PDF with transcription"""
    try:
        # If video_file is a string (path), use it directly
        if isinstance(video_file, str):
            if video_file.strip() == "":
                return None
            return run_app_with_transcription(video_file)
            
        # If it's an uploaded file, create a temporary file
        if video_file is not None:
            # Generate a unique filename for the temporary video
            temp_filename = f"temp_video_{int(time.time())}.mp4"
            temp_path = os.path.join(tempfile.gettempdir(), temp_filename)
            
            try:
                if hasattr(video_file, 'name'):  # If it's already a file path
                    shutil.copyfile(video_file, temp_path)
                else:  # If it's file content
                    with open(temp_path, 'wb') as f:
                        f.write(video_file)
                
                # Process the video
                output_folder_screenshot_path, saved_files = video_to_slides(temp_path)
                saved_files = process_video_with_transcription(temp_path, output_folder_screenshot_path)
                pdf_path = slides_to_pdf(temp_path, output_folder_screenshot_path, saved_files)
                
                # Cleanup
                if os.path.exists(temp_path):
                    os.unlink(temp_path)
                return pdf_path
                
            except Exception as e:
                if os.path.exists(temp_path):
                    os.unlink(temp_path)
                raise gr.Error(f"处理视频时出错: {str(e)}")
        return None
    except Exception as e:
        raise gr.Error(f"处理视频时出错: {str(e)}")


def process_video(video, path):
    if video:
        return run_app(video)
    elif path:
        return run_app(path)
    else:
        raise gr.Error("请上传视频或输入视频路径")

def handle_video_with_transcription(video, path):
    if video:
        return run_app_with_transcription(video)
    elif path:
        return run_app_with_transcription(path)
    else:
        raise gr.Error("请上传视频或输入视频路径")

# Create a modern interface with custom CSS
css = """
.gradio-container {
    font-family: 'SF Pro Display', -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Oxygen, Ubuntu, Cantarell, 'Open Sans', 'Helvetica Neue', sans-serif;
}
.container {
    max-width: 900px;
    margin: auto;
    padding: 20px;
}
.gr-button {
    background: linear-gradient(90deg, #2563eb, #3b82f6);
    border: none;
    color: white;
}
.gr-button:hover {
    background: linear-gradient(90deg, #1d4ed8, #2563eb);
    transform: translateY(-1px);
    box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.1), 0 2px 4px -1px rgba(0, 0, 0, 0.06);
}
.status-info {
    margin-top: 10px;
    padding: 10px;
    border-radius: 4px;
    background-color: #f3f4f6;
}
"""

if __name__ == "__main__":
    with gr.Blocks(css=css) as iface:
        gr.Markdown("# 视频转PDF工具")
        
        with gr.Tab("基础转换"):
            with gr.Row():
                with gr.Column():
                    video_input = gr.Video(label="上传视频")
                    video_path = gr.Textbox(label="或输入视频路径", placeholder="例如: ./input/video.mp4")
                    convert_btn = gr.Button("开始转换", variant="primary")
                
            with gr.Row():
                output_file = gr.File(label="下载PDF")
        
        with gr.Tab("带语音转文字"):
            with gr.Row():
                with gr.Column():
                    video_input_with_transcription = gr.Video(label="上传视频")
                    video_path_with_transcription = gr.Textbox(label="或输入视频路径", placeholder="例如: ./input/video.mp4")
                    convert_btn_with_transcription = gr.Button("开始转换（带字幕）", variant="primary")
                
            with gr.Row():
                output_file_with_transcription = gr.File(label="下载PDF（带字幕）")
        
        convert_btn.click(
            fn=process_video,
            inputs=[video_input, video_path],
            outputs=[output_file],
        )
        
        convert_btn_with_transcription.click(
            fn=handle_video_with_transcription,
            inputs=[video_input_with_transcription, video_path_with_transcription],
            outputs=[output_file_with_transcription],
        )
        
    iface.launch()
