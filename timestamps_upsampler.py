
class TimestampsUpsampler:

    def __init__(self, upsample_dir, framerate):
        self.upsample_dir = upsample_dir
        self.framerate = framerate

    def generate_timestamps(self):

        for i, seq_path in enumerate(self.upsample_dir):

            images = sorted(
                [f for f in os.listdir(seq_path +"/imgs") if f.endswith('.png')])

            print('Will write file: {} with framerate: {} Hz'.format(\
                seq_path + '/timestamps.txt',  self.framerate))
            
            stamp_nanoseconds = 1
            dt_nanoseconds = int((1.0 /  self.framerate) * 1e9 )


            with open(os.path.join(seq_path, 'timestamps.txt'), 'w') as f:
                for image_path in images:

                    f.write('{}\n'.format(int(stamp_nanoseconds)))
                    stamp_nanoseconds += dt_nanoseconds
                f.close()
