# imports

import os
# Must be set before importing torch.
from PIL import ImageFile
from upsampling.utils import Upsampler
from esim_torch import esim_torch

from operator import sub
import os
import cv2
import glob
import tqdm
import torch
import glob
import numpy as np
import matplotlib.pyplot as plt
from PIL import Image



ImageFile.LOAD_TRUNCATED_IMAGES = True
os.environ['CUDA_DEVICE_ORDER'] = 'PCI_BUS_ID'

# variables

# videos characteristics
fps = 30
shape = [256, 320]

input_video_path = "/home/eman/Documents/AUC/ESIM/rpg_vid2e/pie_example/rgb/video_0001.mp4"

# upsampling paths
sampling_input_dir = "/home/eman/Documents/AUC/ESIM/rpg_vid2e/pie_example/origional/"
sampling_output_dir = "/home/eman/Documents/AUC/ESIM/rpg_vid2e/pie_example/upsampled/"

#events paths

contrast_threshold_negative = 0.2
contrast_threshold_positive = 0.2
refractory_period_ns = 0
events_input_dir = "/home/eman/Documents/AUC/ESIM/rpg_vid2e/pie_example/upsampled/"
events_output_dir = "/home/eman/Documents/AUC/ESIM/rpg_vid2e/pie_example/events/"

# events2rgb"
images_output_folder = "/home/eman/Documents/AUC/ESIM/rpg_vid2e/pie_example/events2imgs"


#----------------------------------------------------------------
"""Generating Images from a Video File

https://github.com/uzh-rpg/rpg_vid2e/tree/master/upsampling

If you want to convert a video file to a sequence of images:

input_file = nput_video_path
output_dirpath=sampling_input_dir
ffmpeg -i $input_file "$output_dirpath/%08d.png""""


#----------------------------------------------------------------

# functions


def is_valid_dir(subdirs, files):
    return len(subdirs) == 1 and len(files) == 1 and "timestamps.txt" in files and "imgs" in subdirs


def process_dir(outdir, indir, contrast_threshold_negative, contrast_threshold_positive, refractory_period_ns):
    print(f"Processing folder {indir}... Generating events in {outdir}")
    os.makedirs(outdir, exist_ok=True)

    # constructor
    esim = esim_torch.ESIM(contrast_threshold_negative, contrast_threshold_positive, refractory_period_ns)

    timestamps = np.genfromtxt(os.path.join(indir, "timestamps.txt"), dtype="float64")
    timestamps_ns = (timestamps * 1e9).astype("int64")
    timestamps_ns = torch.from_numpy(timestamps_ns).cuda()

    image_files = sorted(glob.glob(os.path.join(indir, "imgs", "*.png")))
    
    pbar = tqdm.tqdm(total=len(image_files)-1)
    num_events = 0

    counter = 0
    v_counter = 0

    for image_file, timestamp_ns in zip(image_files, timestamps_ns):
        image = cv2.imread(image_file, cv2.IMREAD_GRAYSCALE)
        log_image = np.log(image.astype("float32") / 255 + 1e-5)
        log_image = torch.from_numpy(log_image).cuda()

        sub_events = esim.forward(log_image, timestamp_ns)

        # for the first image, no events are generated, so this needs to be skipped
        if sub_events is None:
            continue

        sub_events = {k: v.cpu() for k, v in sub_events.items()}    
        num_events += len(sub_events['t'])
 
        # do something with the events
        np.savez(os.path.join(outdir, "%010d.npz" % counter), **sub_events)




        # FROM EVENTS into IMAGES >>>> the final output.   (pathes havnt been handeled yet!)

        v_timestamps = np.genfromtxt(os.path.join(images_output_folder, "timestamps.txt"), dtype="float64")
        v_timestamps_ns = (v_timestamps * 1e9).astype("int64")
        v_timestamps_ns = torch.from_numpy(v_timestamps_ns).cuda()

        img = render(shape=shape, **sub_events)
        im = Image.fromarray(img)

        im.save(os.path.join(images_output_folder, "%010d.npz" % v_counter))





        pbar.set_description(f"Num events generated: {num_events}")
        pbar.update(1)
        counter += 1



def render(x, y, t, p, shape):
    img = np.full(shape=shape + [3], fill_value=255, dtype="uint8")
    img[y, x, :] = 0
    img[y, x, p] = 255
    return img


#--
# upsampling
upsampler = Upsampler(input_dir=sampling_input_dir, output_dir=sampling_output_dir)
upsampler.upsample()

print(f"Generating events with cn={contrast_threshold_negative}, cp={contrast_threshold_positive} and rp={refractory_period_ns}")

for path, subdirs, files in os.walk(events_input_dir):
    if is_valid_dir(subdirs, files):

        output_folder = os.path.join(events_output_dir, os.path.relpath(path, events_input_dir))

        process_dir(output_folder, path, contrast_threshold_negative, contrast_threshold_positive, refractory_period_ns)

event_files = sorted(glob.glob(os.path.join(output_folder, "*.npz")))



# save events into image files


for f in event_files[1:]:
    events = np.load(f)
    img = render(shape=shape, **events)
    im = Image.fromarray(img)
    im_name = images_output_folder + "filename.jpeg"
    im.save(im_name")


