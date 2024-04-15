import os
import time
import cv2
import imutils
import shutil
import img2pdf
import glob
import argparse
import gradio as gr
from skimage.metrics import structural_similarity

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
    # Initialize fgbg a Background object with Parameters
    # history = The number of frames history that effects the background subtractor
    # varThreshold = Threshold on the squared Mahalanobis distance between the pixel and the model to decide whether a pixel is well described by the background model. This parameter does not affect the background update.
    # detectShadows = If true, the algorithm will detect shadows and mark them. It decreases the speed a bit, so if you do not need this feature, set the parameter to false.

    fgbg = cv2.createBackgroundSubtractorMOG2(history=FGBG_HISTORY, varThreshold=VAR_THRESHOLD,detectShadows=DETECT_SHADOWS)

    
    captured = False
    start_time = time.time()
    (W, H) = (None, None)

    screenshoots_count = 0
    last_screenshot_file_path = ""
    for frame_count, frame_time, frame in get_frames(video_path):
        orig = frame.copy() # clone the original frame (so we can save it later), 
        frame = imutils.resize(frame, width=600) # resize the frame
        mask = fgbg.apply(frame) # apply the background subtractor

        if W is None or H is None:
            (H, W) = mask.shape[:2]

        p_diff = (cv2.countNonZero(mask) / float(W * H)) * 100

        if p_diff < MIN_PERCENT and not captured and frame_count > WARMUP:
            captured = True
            filename = f"{screenshoots_count:03}_{round(frame_time/60, 2)}.png"

            path = os.path.join(output_folder_screenshot_path, filename)

            image_ssim = 0.0;
            if last_screenshot_file_path != "":
                image_last = cv2.imread(last_screenshot_file_path)
                image_ssim = structural_similarity(image_last, orig, channel_axis=2, data_range=255)

            if image_ssim < SSIM_THRESHOLD:
                print("saving {}".format(path))
                cv2.imwrite(path, orig)
                last_screenshot_file_path = path
                screenshoots_count += 1

        elif captured and p_diff >= MAX_PERCENT:
            captured = False
    print(f'{screenshoots_count} screenshots Captured!')
    print(f'Time taken {time.time()-start_time}s')
    return 


def initialize_output_folder(video_path):
    '''Clean the output folder if already exists'''
    output_folder_screenshot_path = f"{OUTPUT_SLIDES_DIR}/{video_path.rsplit('/')[-1].split('.')[0]}"

    if os.path.exists(output_folder_screenshot_path):
        shutil.rmtree(output_folder_screenshot_path)

    os.makedirs(output_folder_screenshot_path, exist_ok=True)
    print('initialized output folder', output_folder_screenshot_path)
    return output_folder_screenshot_path


def convert_screenshots_to_pdf(video_path, output_folder_screenshot_path):
    output_pdf_path = f"{OUTPUT_SLIDES_DIR}/{video_path.rsplit('/')[-1].split('.')[0]}" + '.pdf'
    print('output_folder_screenshot_path', output_folder_screenshot_path)
    print('output_pdf_path', output_pdf_path)
    print('converting images to pdf..')
    with open(output_pdf_path, "wb") as f:
        f.write(img2pdf.convert(sorted(glob.glob(f"{output_folder_screenshot_path}/*.png"))))
    print('Pdf Created!')
    print('pdf saved at', output_pdf_path)


def video_to_slides(video_path):
    output_folder_screenshot_path = initialize_output_folder(video_path)
    detect_unique_screenshots(video_path, output_folder_screenshot_path)
    return output_folder_screenshot_path


def slides_to_pdf(video_path, output_folder_screenshot_path):
    convert_screenshots_to_pdf(video_path, output_folder_screenshot_path)
    return f"{output_folder_screenshot_path}.pdf"


def run_app(video_path):
    output_folder_screenshot_path = video_to_slides(video_path)
    return slides_to_pdf(video_path, output_folder_screenshot_path)


iface = gr.Interface(
    fn=run_app,
    inputs="text",
    outputs="file",
    title="loopytransform：视频转图文pdf||公众号：正经人王同学",
    description="公众号：正经人王同学  全网同名||video_path填写要转换的视频的路径就好 转换完成后即可下载pdf的文件",
    examples=[["./input/test1.mp4"]]
)
8
iface.launch()
