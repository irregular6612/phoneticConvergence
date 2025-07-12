import sounddevice as sd
import soundfile as sf

class AudioPlayer:
    def __init__(self, folder_path):
        self.folder_path = folder_path
        self.playing = False
        self.stream = None
        self.data = None
        self.samplerate = None
        self.current_frame = 0
        
    def play_audio(self, audio_file):
        if self.playing:
            return 0
            
        try:
            self.data, self.samplerate = sf.read(audio_file)
            duration = len(self.data) / self.samplerate
            self.current_frame = 0
            
            def callback(outdata, frames, time, status):
                if status:
                    print(f'Error: {status}')
                if self.current_frame + frames > len(self.data):
                    # 남은 데이터가 프레임보다 적을 경우
                    remaining = len(self.data) - self.current_frame
                    outdata[:remaining, 0] = self.data[self.current_frame:len(self.data)]
                    outdata[remaining:, 0] = 0
                    self.playing = False
                    raise sd.CallbackStop()
                else:
                    outdata[:, 0] = self.data[self.current_frame:self.current_frame + frames]
                    self.current_frame += frames
            
            self.stream = sd.OutputStream(
                channels=1,
                samplerate=self.samplerate,
                callback=callback
            )
            self.stream.start()
            self.playing = True
            return duration
        except Exception as e:
            print(f"오디오 재생 오류: {str(e)}")
            return 0
            
    def is_playing(self):
        return self.playing

    def stop(self):
        self.playing = False
        if self.stream:
            self.stream.stop()
            self.stream = None
