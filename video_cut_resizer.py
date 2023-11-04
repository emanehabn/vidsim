import os
import json
import shutil
import subprocess

class VideoCutResizer_:

    def __init__(self, video_path, cut_part_duration = 2, resize_scale=0.3, debug=False):
        """ 
        Class that preprocess video, devide it into chuncks and 
        """
        self.video_path = video_path
        self.cut_part_duration = cut_part_duration
        self.resize_scale = resize_scale
        self.debug = debug

        self.video_name = os.path.basename(self.video_path).split(".")[0]
        
        self.main_folder_path = os.path.join(os.path.dirname(self.video_path), "/original_" + self.video_name)


        if debug:
            print(f"video_name: {self.video_name}")
            print(f"main_folder_path: {self.main_folder_path}")
        
        try:
            self.width, self.height, self.video_duration, self.total_frames, \
                                        self.fps = self.__get_video_info()
            self.num_cut_parts = int(self.video_duration) // int(self.cut_part_duration)
            

        except Exception as e:
            print(f"Error getting video info: {e}")
            print("---")

            self.width, self.height, self.video_duration, self.total_frames, \
                self.fps = None, None, None, None, None
            print(self.width, self.height, self.video_duration, self.total_frames, \
                self.fps) 

    def __get_video_info(self):

            try:

                """Calculates the proberities of a video file using ffprobe. """

                properties_cmd = ["ffprobe", "-v", "error", "-select_streams", "v:0", "-show_entries",
                        "stream=height,width,nb_frames,duration", "-of", "json", 
                        self.video_path]
                
                result = subprocess.run(properties_cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE,
                                        text=True)

                # Parse the JSON output to get the duration.
                
                output_json = json.loads(result.stdout)
                
                width = int(output_json["streams"][0]["width"])
                height = int(output_json["streams"][0]["height"])
                duration = float(output_json["streams"][0]["duration"])
                frame_count = int(output_json["streams"][0]["nb_frames"])
                fps = int(frame_count/duration)
                return width, height, duration, frame_count, fps
            
            except:
                print("No VIDEO output found")
                return None

                   
        

    def cut_resize_video(self):

        for i in range(self.num_cut_parts):
            if i == 0:
                cut_part_start_time = 0
            else:
                cut_part_start_time = i + self.cut_part_duration
                
            cut_part_end_time = cut_part_start_time + self.cut_part_duration

            # Handle last video duration
            if (cut_part_start_time + self.cut_part_duration) > self.video_duration :
                cut_part_end_time = self.video_duration
                
                
            #create a cut sequence folder
            
            video_parts_path = os.path.join(os.path.dirname(self.video_path), f"seq_{i}")


            if not os.path.exists(video_parts_path):
                os.mkdir( video_parts_path)

            # Create the output file path for the cut part
            cut_part_output_path = os.path.join(video_parts_path, f"{self.video_name}_part_{i}.mp4")

            if self.debug:

                print(f"cut_part_start_time: {cut_part_start_time}", cut_part_start_time, end=" - ")
                print(f"cut_part_end_time: {cut_part_end_time}", end=" - ")
                print(f"video_parts_path: {video_parts_path}", end=" - ")
                print(f"cut_part_output_path: {cut_part_output_path}", end=" - ")
                print("----------------------------------------------")
                

            # Cut and resize the video
            cut_resize_cmd = ["ffmpeg", "-i", self.video_path, 
                            "-ss", str(cut_part_start_time), 
                            "-t", str(cut_part_end_time),
                            "-vf", f"scale={self.resize_scale}*iw:{self.resize_scale}*ih",
                            cut_part_output_path]
            subprocess.run(cut_resize_cmd)
            

            # Check if the video if empty through number of frames
            print(self.video_duration)
            if self.__get_video_info() is None:

                print(cut_part_output_path)
                print(" video cut error")
                shutil.rmtree(video_parts_path)
                print(f"cut_part_end_time: {cut_part_end_time} ")
                print(f"The whole video duration is {self.duration}")

                break
            else:
                # Add a subprocess to extract video frames from the new video chuncks

                cut_part_frames_path = os.path.join(video_parts_path, "imgs")
                
                if not os.path.exists(cut_part_frames_path):
                    os.mkdir( cut_part_frames_path)

                vid2frame_cmd = ["ffmpeg",
                        "-i",
                        cut_part_output_path,
                        f"{cut_part_frames_path}/%08d.png",]

                subprocess.run(vid2frame_cmd)

                # Create fps.txt file
                fps_txt_path = os.path.join(video_parts_path, "fps.txt")
                
                with open(fps_txt_path, "w") as f:
                    f.write(str(self.fps))

