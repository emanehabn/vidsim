
from operator import sub
import json
import os
import cv2
import json
import glob
import tqdm
import torch
import shutil
import subprocess
import numpy as np
import esim_torch
from upsampling import *
from upsampling.utils import Upsampler
from esim_torch import esim_torch


class EventGenerator:
    def __init__(self, contrast_threshold_negative, contrast_threshold_positive, refractory_period_ns):
        self.contrast_threshold_negative = contrast_threshold_negative
        self.contrast_threshold_positive = contrast_threshold_positive
        self.refractory_period_ns = refractory_period_ns
        self.esim = esim_torch.ESIM(contrast_threshold_negative,
                                    contrast_threshold_positive,
                                    refractory_period_ns)
    
    @staticmethod
    def is_valid_dir(subdirs, files):
        return len(subdirs) == 1 and len(files) == 1 and "timestamps.txt" in files and "imgs" in subdirs

    @staticmethod
    def is_valid_dir(subdirs, files):
        return len(subdirs) == 1 and len(files) == 1 and "timestamps.txt" in files and "imgs" in subdirs

    def process_dir(self, outdir, indir):
        print(f"Processing folder {indir}... Generating events in {outdir}")
        os.makedirs(outdir, exist_ok=True)

        timestamps = np.genfromtxt(os.path.join(indir, "timestamps.txt"), dtype="float64")
        timestamps_ns = (timestamps * 1e9).astype("int64")
        timestamps_ns = torch.from_numpy(timestamps_ns).cuda()

        image_files = sorted(glob.glob(os.path.join(indir, "imgs", "*.png")))
        
        pbar = tqdm.tqdm(total=len(image_files)-1)
        num_events = 0

        counter = 0
        for image_file, timestamp_ns in zip(image_files, timestamps_ns):
            image = cv2.imread(image_file, cv2.IMREAD_GRAYSCALE)
            log_image = np.log(image.astype("float32") / 255 + 1e-5)
            log_image = torch.from_numpy(log_image).cuda()

            sub_events = self.esim.forward(log_image, timestamp_ns)

            if sub_events is None:
                continue

            sub_events = {k: v.cpu() for k, v in sub_events.items()}    
            num_events += len(sub_events['t'])
     
            np.savez(os.path.join(outdir, "%010d.npz" % counter), **sub_events)
            pbar.set_description(f"Num events generated: {num_events}")
            pbar.update(1)
            counter += 1

        

class EventGenerationManager:
    def __init__(self, input_dir, output_dir, contrast_threshold_negative, contrast_threshold_positive, refractory_period_ns):
        self.input_dir = input_dir
        self.output_dir = output_dir
        self.contrast_threshold_negative = contrast_threshold_negative
        self.contrast_threshold_positive = contrast_threshold_positive
        self.refractory_period_ns = refractory_period_ns
    
    def process_directories(self, event_generator):
        for path, subdirs, files in os.walk(self.input_dir):
            if EventGenerator.is_valid_dir(subdirs, files):
                output_folder = os.path.join(self.output_dir, os.path.relpath(path, self.input_dir))
                event_generator.process_dir(output_folder, path)

    def start_event_generation(self):
        event_gen = EventGenerator(self.contrast_threshold_negative, self.contrast_threshold_positive, self.refractory_period_ns)
        print(f"Generating events with cn={event_gen.contrast_threshold_negative}, cp={event_gen.contrast_threshold_positive} and rp={event_gen.refractory_period_ns}")
        self.process_directories(event_gen)


