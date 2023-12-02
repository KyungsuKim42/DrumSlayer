import os
import librosa
import numpy as np
from torch.utils.data import Dataset
from natsort import natsorted
from scipy import signal

# TODO : 앞 sample 자르고 들어가기 
class Loop(Dataset):
    def __init__(self, single_shot_dataset, midi_dataset, loop_seconds, reference_pitch=48): #60
        self.ssdataset = single_shot_dataset
        self.mididataset = midi_dataset
        self.loop_length = loop_seconds * self.ssdataset.sample_rate
        self.reference_pitch = reference_pitch
    
    def __len__(self):
        return len(self.mididataset)

    def __getitem__(self, index):
        # Choose a random dataset
        ssindex = np.random.choice(len(self.ssdataset))
        midiindex = index

        # Get singleshot & velocity & pitch
        ss = self.ssdataset[ssindex]
        velocity, pitch = self.mididataset[midiindex]
        onset = (velocity != 0).astype(int)
        pitch_shifted = (pitch - self.reference_pitch)*onset

        # Make a list consisted of velocity and pitch
        velocity_and_pitch = []
        for pitch in np.unique(pitch_shifted):
            mask = pitch_shifted == pitch
            velocity_masked = velocity * mask
            velocity_and_pitch.append([velocity_masked, pitch])

        # Make a loop
        loop = np.zeros((2, self.loop_length))
        for velocity, pitch in velocity_and_pitch:
            if pitch != 0:
                ss_shifted = librosa.effects.pitch_shift(ss, sr=self.ssdataset.sample_rate, n_steps=pitch)
            else:
                ss_shifted = ss
            loop += np.array([signal.convolve(velocity, ss_shifted[0])[:self.loop_length], 
                            signal.convolve(velocity, ss_shifted[1])[:self.loop_length]])

        return loop, velocity, pitch


class SingleShot(Dataset):
    def __init__(self, directory, sample_rate):
        self.sample_rate = sample_rate
        self.data = [os.path.join(directory, f) for f in natsorted(os.listdir(directory)) if f.endswith('.wav')]
        # data = directory내 wav파일 list
        
    def __len__(self):
        return len(self.data)

    def __getitem__(self, idx):
        audio, _ = librosa.load(self.data[idx], sr=self.sample_rate, mono=False)
        if audio.ndim == 1:
            audio = np.stack((audio, audio))
        return audio
    

class MIDI(Dataset):
    def __init__(self, directory):
        self.data = [os.path.join(directory, f) for f in natsorted(os.listdir(directory)) if f.endswith('.npy')]

    def __len__(self):
        return len(self.data)

    def __getitem__(self, idx):
        # breakpoint()
        midi_1920 = np.load(self.data[idx]) # (2, 1920)
        midi_96000 = np.zeros([midi_1920.shape[0],96000])
        upsample_factor = 96000 // 1920  # 확장 비율 계산
        for i in range(upsample_factor):
            midi_96000[:, i::upsample_factor] = midi_1920
        return midi_96000


def midi_2_wav(args):

    data_type = args.data_type
    if data_type == 'all':
        midi_2_wav_all(args)
    else:
        midi_2_wav_one(args)
    return None

def midi_2_wav_all(args):
    from tqdm import tqdm
    import soundfile as sf
    import torch
    all = ['train', 'valid', 'test']
    for data_type in all:
        
        sample_rate = args.sample_rate
        loop_seconds = 2
        oneshot_dir = args.oneshot_dir
        output_dir = args.output_dir
        device = torch.device("cuda" if torch.cuda.is_available() else "cpu")

        #single shot dir
        dir_ss_kick =       oneshot_dir + f'{data_type}/kick'
        dir_ss_snare =      oneshot_dir + f'{data_type}/snare'
        dir_ss_hhclosed =   oneshot_dir + f'{data_type}/hhclosed'
        # dir_ss_hhopen = './midi_2_wav/drum_data_practice/proprietary_dataset/hhopen'

        #midi numpy dir
        dir_midi_kick =     output_dir + f'drum_data_{data_type}/generated_midi_numpy/kick_midi_numpy'
        dir_midi_snare =    output_dir + f'drum_data_{data_type}/generated_midi_numpy/snare_midi_numpy'
        dir_midi_hhclosed = output_dir + f'drum_data_{data_type}/generated_midi_numpy/hihat_midi_numpy'

        ss_kick = SingleShot(dir_ss_kick, sample_rate)
        ss_snare = SingleShot(dir_ss_snare, sample_rate)
        ss_hhclosed = SingleShot(dir_ss_hhclosed, sample_rate)
        # ss_hhopen = SingleShot(dir_ss_hhopen, sample_rate)

        midi_kick = MIDI(dir_midi_kick)
        midi_snare = MIDI(dir_midi_snare)
        midi_hhclosed = MIDI(dir_midi_hhclosed)

        loop_kick = Loop(ss_kick, midi_kick, loop_seconds)
        loop_snare = Loop(ss_snare, midi_snare, loop_seconds)
        loop_hhclosed = Loop(ss_hhclosed, midi_hhclosed, loop_seconds)

        # Bring the each loop separately
        for idx in tqdm(range(len(loop_kick))): 
            audio_loop_kick, _, _  = loop_kick[idx]
            audio_loop_snare, _, _  = loop_snare[idx]
            audio_loop_hhclosed, _, _  = loop_hhclosed[idx]
            
            audio_loop_kick = np.transpose(audio_loop_kick)
            audio_loop_snare = np.transpose(audio_loop_snare)
            audio_loop_hhclosed = np.transpose(audio_loop_hhclosed)
            
            kick_dir = f'./generated_data/drum_data_{data_type}/generated_loops/kick/'
            os.makedirs(kick_dir, exist_ok=True)
            snare_dir = f'./generated_data/drum_data_{data_type}/generated_loops/snare/'
            os.makedirs(snare_dir, exist_ok=True)
            hhclosed_dir = f'./generated_data/drum_data_{data_type}/generated_loops/hhclosed/'
            os.makedirs(hhclosed_dir, exist_ok=True)

            sf.write( f'{kick_dir}'+f'{idx}.wav', audio_loop_kick, sample_rate)
            sf.write( f'{snare_dir}'+f'{idx}.wav', audio_loop_snare, sample_rate)
            sf.write( f'{hhclosed_dir}'+f'{idx}.wav', audio_loop_hhclosed, sample_rate)
        
    return None

def midi_2_wav_one(args):
    from tqdm import tqdm
    import soundfile as sf
    import torch
    data_type = args.data_type
    sample_rate = args.sample_rate
    loop_seconds = 2
    oneshot_dir = args.oneshot_dir
    output_dir = args.output_dir
    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")

    #single shot dir
    dir_ss_kick =       oneshot_dir + f'{data_type}/kick'
    dir_ss_snare =      oneshot_dir + f'{data_type}/snare'
    dir_ss_hhclosed =   oneshot_dir + f'{data_type}/hhclosed'
    # dir_ss_hhopen = './midi_2_wav/drum_data_practice/proprietary_dataset/hhopen'

    #midi numpy dir
    dir_midi_kick =     output_dir + f'drum_data_{data_type}/generated_midi_numpy/kick_midi_numpy'
    dir_midi_snare =    output_dir + f'drum_data_{data_type}/generated_midi_numpy/snare_midi_numpy'
    dir_midi_hhclosed = output_dir + f'drum_data_{data_type}/generated_midi_numpy/hhclosed_midi_numpy'

    ss_kick = SingleShot(dir_ss_kick, sample_rate)
    ss_snare = SingleShot(dir_ss_snare, sample_rate)
    ss_hhclosed = SingleShot(dir_ss_hhclosed, sample_rate)
    # ss_hhopen = SingleShot(dir_ss_hhopen, sample_rate)

    midi_kick = MIDI(dir_midi_kick)
    midi_snare = MIDI(dir_midi_snare)
    midi_hhclosed = MIDI(dir_midi_hhclosed)

    loop_kick = Loop(ss_kick, midi_kick, loop_seconds)
    loop_snare = Loop(ss_snare, midi_snare, loop_seconds)
    loop_hhclosed = Loop(ss_hhclosed, midi_hhclosed, loop_seconds)

    # Bring the each loop separately
    for idx in tqdm(range(len(loop_kick))): 
        audio_loop_kick, _, _  = loop_kick[idx]
        audio_loop_snare, _, _  = loop_snare[idx]
        audio_loop_hhclosed, _, _  = loop_hhclosed[idx]
        
        audio_loop_kick = np.transpose(audio_loop_kick)
        audio_loop_snare = np.transpose(audio_loop_snare)
        audio_loop_hhclosed = np.transpose(audio_loop_hhclosed)
        
        kick_dir = f'./generated_data/drum_data_{data_type}/generated_loops/kick/'
        os.makedirs(kick_dir, exist_ok=True)
        snare_dir = f'./generated_data/drum_data_{data_type}/generated_loops/snare/'
        os.makedirs(snare_dir, exist_ok=True)
        hhclosed_dir = f'./generated_data/drum_data_{data_type}/generated_loops/hhclosed/'
        os.makedirs(hhclosed_dir, exist_ok=True)

        sf.write( f'{kick_dir}'+f'{idx}.wav', audio_loop_kick, sample_rate)
        sf.write( f'{snare_dir}'+f'{idx}.wav', audio_loop_snare, sample_rate)
        sf.write( f'{hhclosed_dir}'+f'{idx}.wav', audio_loop_hhclosed, sample_rate)
        
    return None

    # # Bring the whole loop at once
    # for idx in tqdm(range(len(loop_kick))): 
    #     audio_loop_kick, _, _  = loop_kick[idx]
    #     audio_loop_snare, _, _  = loop_snare[idx]
    #     audio_loop_hhclosed, _, _  = loop_hhclosed[idx]
    #     audio_loop_drum = audio_loop_kick + audio_loop_snare + audio_loop_hhclosed
    #     audio_loop_drum = np.transpose(audio_loop_drum)
    #     output_dir = f'./generated_data/drum_data_{data_type}/generated_loops/'
    #     os.makedirs(output_dir, exist_ok=True)
    #     sf.write( f'{output_dir}'+f'{idx}.wav', audio_loop_drum, sample_rate)

if __name__ == '__main__':
    import argparse

    parser = argparse.ArgumentParser()
    parser.add_argument('--data_type', type=str, default='aa', help='all, train, valid, test')
    parser.add_argument('--sample_rate', type=int, default=48000, help='sample_rate')
    args = parser.parse_args()
    midi_2_wav(args)