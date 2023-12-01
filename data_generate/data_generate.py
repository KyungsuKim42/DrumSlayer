import midi_2_wav
import argparse


if __name__ == '__main__':
    
    parser = argparse.ArgumentParser()
    parser.add_argument('--data_type', type=str, default='aa', help='train, valid, test')
    parser.add_argument('--midi_number', type=int, default=10, help='midi number')
    parser.add_argument('--beat', type=int, default=1, help='beat')
    parser.add_argument('--sample_rate', type=int, default=48000, help='sample_rate')
    parser.add_argument('--grid_random', type=str, default='RG', help='R for random, G for grid, RG for random in grid, GG for gaussian in grid')
    parser.add_argument('--random_type', type=str, default='random', help='random or gaussian')
    parser.add_argument('--mono', type=bool, default=False, help='mono or stereo')
    args = parser.parse_args()

    # TODO 1 : midi gen 
    midi_2_wav.generate_midi(args)

    # TODO 2 : midi 2 wav 
    midi_2_wav.midi_2_wav(args)

    import DAFXChain.drum_fx

    # TODO 3 : DAFX
    DAFXChain.drum_fx(args)

    # midi 10개, beat 1, sample rate 48000 -> 27m