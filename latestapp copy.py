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
 


def detect_unique_screenshots(video_path, output_folder_screenshot_path):
    ''''''
    fgbg = cv2.createBackgroundSubtractorMOG2(history=FGBG_HISTORY, varThreshold=VAR_THRESHOLD,detectShadows=DETECT_SHADOWS)

    captured = False
    start_time = time.time()
    (W, H) = (None, None)

    screenshoots_count = 0
    last_screenshot = None
    saved_files = []  # Keep track of saved files
    
    for frame_count, frame_time, frame in get_frames(video_path):
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
                    print("saving {}".format(path))
                    cv2.imwrite(str(path), orig)
                    last_screenshot = orig
                    saved_files.append(path)  # Add to saved files list
                    screenshoots_count += 1
                except Exception as e:
                    print(f"Error saving image: {str(e)}")
                    continue

        elif captured and p_diff >= MAX_PERCENT:
            captured = False

    print(f'{screenshoots_count} screenshots Captured!')
    print(f'Time taken {time.time()-start_time}s')
    return saved_files  # Return the list of saved files


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


def video_to_slides(video_path):
    output_folder_screenshot_path = initialize_output_folder(video_path)
    saved_files = detect_unique_screenshots(video_path, output_folder_screenshot_path)
    return output_folder_screenshot_path, saved_files


def slides_to_pdf(video_path, output_folder_screenshot_path, saved_files):
    # Create a safe filename
    video_filename = os.path.splitext(os.path.basename(video_path))[0]
    safe_filename = "".join(x for x in video_filename if x.isalnum() or x in (' ', '-', '_'))
    output_pdf_path = os.path.join(OUTPUT_SLIDES_DIR, f"{safe_filename}.pdf")
    
    try:
        print('output_folder_screenshot_path', output_folder_screenshot_path)
        print('output_pdf_path', output_pdf_path)
        print('converting images to pdf..')
        
        if not saved_files:
            raise Exception("No screenshots were captured from the video")
            
        # Verify all files exist
        existing_files = [f for f in saved_files if os.path.exists(f)]
        if not existing_files:
            raise Exception("No PNG files found in the output directory")
            
        with open(output_pdf_path, "wb") as f:
            f.write(img2pdf.convert(existing_files))
            
        print('Pdf Created!')
        print('pdf saved at', output_pdf_path)
        return output_pdf_path
    except Exception as e:
        print(f"Error creating PDF: {str(e)}")
        raise


def run_app(video_path):
    output_folder_screenshot_path, saved_files = video_to_slides(video_path)
    return slides_to_pdf(video_path, output_folder_screenshot_path, saved_files)


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
"""

with gr.Blocks(css=css) as iface:
    gr.Markdown(
        """
        # 🎥 视频转PDF智能助手
        
        ### 轻松将视频转换为高质量PDF文档
        公众号：正经人王同学 | 全网同名
        """
    )
    
    with gr.Row():
        with gr.Column():
            # Allow both video upload and path input
            video_input = gr.Video(label="上传视频")
            video_path = gr.Textbox(label="或输入视频路径", placeholder="例如: ./input/video.mp4")
            convert_btn = gr.Button("开始转换", variant="primary")
        
    with gr.Row():
        output_file = gr.File(label="下载PDF")
    
    gr.Markdown(
        """
        ### 使用说明
        1. 上传视频文件 或 输入视频文件路径
        2. 点击"开始转换"按钮
        3. 等待处理完成后下载生成的PDF文件
        
        ### 特点
        - 智能检测视频关键帧
        - 高质量PDF输出
        - 支持多种视频格式
        """
    )
    
    # Handle both video upload and path input
    convert_btn.click(
        fn=process_video_file,
        inputs=[video_input],
        outputs=[output_file],
    ).then(
        fn=process_video_file,
        inputs=[video_path],
        outputs=[output_file],
    )

if __name__ == "__main__":
    iface.launch()
