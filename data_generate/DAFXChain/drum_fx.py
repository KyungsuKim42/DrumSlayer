import numpy as np
from DAFX import DrumChains
import argparse
from audiotools import AudioSignal
from scipy.io.wavfile import write
import shutil
import os

def drum_fx(args):
        
    # mono, sample rate
    mono = args.mono
    sample_rate = args.sample_rate

    # define chain
    drumchains = DrumChains(mono, sample_rate)

    for i in range(args.midi_number):
        # prepare kick, hihat, snare loops. should be numpy array!
        kick = AudioSignal(f'./generated_data/drum_data_{args.data_type}/generated_loops/kick/{i}.wav').numpy().squeeze()
        snare = AudioSignal(f'./generated_data/drum_data_{args.data_type}/generated_loops/snare/{i}.wav').numpy().squeeze()
        hihat = AudioSignal(f'./generated_data/drum_data_{args.data_type}/generated_loops/hhclosed/{i}.wav').numpy().squeeze()

        # make DAFxed drum mix
        drum_mix_mastered = drumchains.apply(kick, snare, hihat)
        
        # numpy to wav write
        dafx_loop_dir = f'./generated_data/drum_data_{args.data_type}/dafx_loops/{i}.wav'
        write(dafx_loop_dir, sample_rate, drum_mix_mastered.T)

    return None




if __name__ == '__main__':
    
    parser = argparse.ArgumentParser()
    parser.add_argument('--sample_rate', type=int, default=48000, help='sample_rate')
    parser.add_argument('--mono', type=bool, default=False, help='mono or stereo')
    parser.add_argument('--midi_number', type=int, default=10, help='midi number')
    parser.add_argument('--data_type', type=str, default='aa', help='train, val, test')
    args = parser.parse_args()
    drum_fx(args)
    