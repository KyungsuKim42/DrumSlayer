import random
from pedalboard import Pedalboard, Limiter, Reverb, Delay, HighpassFilter, LowpassFilter
from pedalboard import Gain as pedalboard_gain

from mixing_manipulator.audio_effects_chain import create_effects_augmentation_chain
from mixing_manipulator.common_audioeffects import *
from utils import RMS_parallel


class DrumChains():
    def __init__(self, mono:bool, sample_rate):
        if mono:
            n_channels = 1
        else:
            n_channels = 2
        self.mono = mono
        self.sample_rate = sample_rate

        #####################
        # Individual chains #
        #####################
        # GAIN
        # RMS 분포 -> gain
        kick_gain_params = ParameterList()
        kick_gain_params.add(Parameter('gain', -15.0, 'float', units='dB', minimum=-21.0, maximum=-14.0))
        kick_gain_params.add(Parameter('invert', False, 'bool'))
        kick_gain = Gain(parameters=kick_gain_params)

        snare_gain_params = ParameterList()
        snare_gain_params.add(Parameter('gain', -8.0, 'float', units='dB', minimum=-17.0, maximum=-7.0))
        snare_gain_params.add(Parameter('invert', False, 'bool'))
        snare_gain = Gain(parameters=snare_gain_params)

        hihat_gain_params = ParameterList()
        hihat_gain_params.add(Parameter('gain', -15.0, 'float', units='dB', minimum=-17.5, maximum=-14.5))
        hihat_gain_params.add(Parameter('invert', False, 'bool'))
        hihat_gain = Gain(parameters=hihat_gain_params)

            # EQ
        kick_eq_params = ParameterList()
        kick_eq_params.add(Parameter('low_shelf_gain', -0.2, 'float', minimum=-0.5, maximum=0.5))
        kick_eq_params.add(Parameter('low_shelf_freq', 30.0, 'float', minimum=20.0, maximum=30.0))
        kick_eq_params.add(Parameter('first_band_gain', 0.0, 'float', minimum=-2.0, maximum=2.0))
        kick_eq_params.add(Parameter('first_band_freq', 75.0, 'float', minimum=50.0, maximum=100.0))
        kick_eq_params.add(Parameter('first_band_q', 5.0, 'float', minimum=1.5, maximum=10.0))
        kick_eq_params.add(Parameter('second_band_gain', 0.0, 'float', minimum=-2.0, maximum=2.0))
        kick_eq_params.add(Parameter('second_band_freq', 150.0, 'float', minimum=100.0, maximum=200.0))
        kick_eq_params.add(Parameter('second_band_q', 1.5, 'float', minimum=1.5, maximum=10.0))
        kick_eq_params.add(Parameter('third_band_gain', 0.0, 'float', minimum=-2.0, maximum=2.0))
        kick_eq_params.add(Parameter('third_band_freq', 400.0, 'float', minimum=300.0, maximum=500.0))
        kick_eq_params.add(Parameter('third_band_q', 2.0, 'float', minimum=1.5, maximum=10.0))
        kick_eq = Equaliser(n_channels=n_channels, sample_rate=sample_rate, bands=['low_shelf', 'first_band', 'second_band', 'third_band'], parameters=kick_eq_params)

        snare_eq_params = ParameterList()
        snare_eq_params.add(Parameter('low_shelf_gain', -2, 'float', minimum=-3, maximum=0))
        snare_eq_params.add(Parameter('low_shelf_freq', 50.0, 'float', minimum=50.0, maximum=100.0))
        snare_eq = Equaliser(n_channels=n_channels, sample_rate=sample_rate, bands=['low_shelf'], parameters=snare_eq_params)

        hihat_eq_params = ParameterList()
        hihat_eq_params.add(Parameter('low_shelf_gain', -2, 'float', minimum=-3, maximum=0))
        hihat_eq_params.add(Parameter('low_shelf_freq', 50.0, 'float', minimum=50.0, maximum=100.0))
        hihat_eq = Equaliser(n_channels=n_channels, sample_rate=sample_rate, bands=['low_shelf'], parameters=hihat_eq_params)

            # COMP
        kick_comp_params = ParameterList()
        kick_comp_params.add(Parameter('threshold', -20.0, 'float', units='dB', minimum=-40.0, maximum=0.0))
        kick_comp_params.add(Parameter('attack_time', 10.0, 'float', units='ms', minimum=1.0, maximum=100.0))
        kick_comp_params.add(Parameter('release_time', 100.0, 'float', units='ms', minimum=10.0, maximum=500.0))
        kick_comp_params.add(Parameter('ratio', 4.0, 'float', minimum=2.0, maximum=10.0))
        kick_comp = Compressor(sample_rate = sample_rate, parameters=kick_comp_params)

        snare_comp_params = ParameterList()
        snare_comp_params.add(Parameter('threshold', -40.0, 'float', units='dB', minimum=-40.0, maximum=0.0))
        snare_comp_params.add(Parameter('attack_time', 77.0, 'float', units='ms', minimum=20.0, maximum=100.0))
        snare_comp_params.add(Parameter('release_time', 100.0, 'float', units='ms', minimum=50.0, maximum=500.0))
        snare_comp_params.add(Parameter('ratio', 4.0, 'float', minimum=3.0, maximum=5.0))
        snare_comp = Compressor(sample_rate = sample_rate, parameters=snare_comp_params)

        hihat_comp_params = ParameterList()
        hihat_comp_params.add(Parameter('threshold', -40.0, 'float', units='dB', minimum=-50.0, maximum=0.0))
        hihat_comp_params.add(Parameter('attack_time', 15.0, 'float', units='ms', minimum=1., maximum=100.0))
        hihat_comp_params.add(Parameter('release_time', 100.0, 'float', units='ms', minimum=50.0, maximum=500.0))
        hihat_comp_params.add(Parameter('ratio', 4.0, 'float', minimum=2.0, maximum=5.0))
        hihat_comp = Compressor(sample_rate = sample_rate, parameters=hihat_comp_params)

            # PAN    
        kick_pan_params = ParameterList()
        kick_pan_params.add(Parameter('pan', 0.5, 'float', minimum=0.46, maximum=0.56))
        kick_pan_params.add(Parameter('pan_law', '-4.5dB', 'string', options=['-4.5dB', 'linear', 'constant_power']))
        kick_pan = Panner(parameters=kick_pan_params)

        snare_pan_params = ParameterList()
        snare_pan_params.add(Parameter('pan', 0.5, 'float', minimum=0.46, maximum=0.56))
        snare_pan_params.add(Parameter('pan_law', '-4.5dB', 'string', options=['-4.5dB', 'linear', 'constant_power']))
        snare_pan = Panner(parameters=snare_pan_params)

        hihat_pan_params = ParameterList()
        hihat_pan_params.add(Parameter('pan', 0.5, 'float', minimum=0.2, maximum=0.8))
        hihat_pan_params.add(Parameter('pan_law', '-4.5dB', 'string', options=['-4.5dB', 'linear', 'constant_power']))
        hihat_pan = Panner(parameters=hihat_pan_params)

            # CHAIN
        self.kick_chain = create_effects_augmentation_chain([kick_gain, kick_eq, kick_comp, kick_pan], ir_dir_path=None, sample_rate=sample_rate)
        self.snare_chain = create_effects_augmentation_chain([snare_gain, snare_eq, snare_comp, snare_pan], ir_dir_path=None, sample_rate=sample_rate)
        self.hihat_chain = create_effects_augmentation_chain([hihat_gain, hihat_eq, hihat_comp, hihat_pan], ir_dir_path=None, sample_rate=sample_rate)

        #############
        # Sum chain #
        #############
            # HPF
        self.HPF = Pedalboard([
            HighpassFilter(
                cutoff_frequency_hz=2000.0
            )
        ])
         
            # LPF
        self.LPF = Pedalboard([
            LowpassFilter(
                cutoff_frequency_hz=200.0
            )
        ])

            # REVERB
        self.snare_reverb = Pedalboard([
            Reverb(
                room_size = 0.5, # 0 ~ 1
                damping = 0.5, # 0 ~ 1
                wet_level = 1.0, # 0 ~ 1
                dry_level = 0.0, # 0 ~ 1
                width = 1.0, # 0 ~ 1
                freeze_mode = 0 # 0 ~ 1
            ),
            pedalboard_gain(
                gain_db = 1.0
            )
        ])

        self.hihat_reverb = Pedalboard([
            Reverb(
                room_size = 0.5, # 0 ~ 1
                damping = 0.5, # 0 ~ 1
                wet_level = 1.0, # 0 ~ 1
                dry_level = 0.0, # 0 ~ 1
                width = 1.0, # 0 ~ 1
                freeze_mode = 0 # 0 ~ 1
            ),
            pedalboard_gain(
                gain_db = 1.0
            )
        ])
            # DELAY
        self.snare_delay = Pedalboard([
            Delay(
                delay_seconds = 0.5, # 0 ~
                feedback = 0.0, # 0 ~ 1
                mix = 1.0 # 0 ~ 1
            ),
            pedalboard_gain(
                gain_db = 1.0
            )
        ])

        self.hihat_delay = Pedalboard([
            Delay(
                delay_seconds = 0.5, # 0 ~
                feedback = 0.0, # 0 ~ 1
                mix = 1.0 # 0 ~ 1
            ),
            pedalboard_gain(
                gain_db = 1.0
            )
        ])
            # EQ
        mix_eq_params = ParameterList()
        mix_eq_params.add(Parameter('first_band_gain', 0.0, 'float', minimum=-1.0, maximum=1.0))
        mix_eq_params.add(Parameter('first_band_freq', 80.0, 'float', minimum=20.0, maximum=200.0))
        mix_eq_params.add(Parameter('first_band_q', 1.5, 'float', minimum=0.75, maximum=3.0))
        mix_eq_params.add(Parameter('second_band_gain', 0.0, 'float', minimum=-1.0, maximum=1.0))
        mix_eq_params.add(Parameter('second_band_freq', 800.0, 'float', minimum=200.0, maximum=3000.0))
        mix_eq_params.add(Parameter('second_band_q', 1.5, 'float', minimum=0.75, maximum=3.0))
        mix_eq_params.add(Parameter('third_band_gain', 0.0, 'float', minimum=-1.0, maximum=1.0))
        mix_eq_params.add(Parameter('third_band_freq', 6000.0, 'float', minimum=3000.0, maximum=20000.0))
        mix_eq_params.add(Parameter('third_band_q', 1.5, 'float', minimum=0.75, maximum=3.0))
        mix_eq = Equaliser(n_channels=n_channels, sample_rate=sample_rate, bands=['first_band', 'second_band', 'third_band'], parameters=mix_eq_params)
        self.mix_eq = create_effects_augmentation_chain([mix_eq], ir_dir_path=None, sample_rate=sample_rate)

            # LIMITER
        self.limiter = Pedalboard([
            pedalboard_gain(
                gain_db = 1.0
            ),
            Limiter(
                threshold_db=0.0, # MUSDB 랑 합쳐서 들어보고 판단.
                release_ms = 100 # 2.0 ~ 1000.0
            )
        ])

    def update_chains(self, samples):
        #####################
        # Individual chains #
        #####################
        individual_chains = [self.kick_chain, self.snare_chain, self.hihat_chain]
        RMS_range = 0.7
        RMS_values = RMS_parallel(samples, self.mono)
        for i in range(len(individual_chains)):
            individual_chains[i].fxs[0][0].parameters.gain.value =  max(
                individual_chains[i].fxs[0][0].parameters.gain.min,
                min(
                    individual_chains[i].fxs[0][0].parameters.gain.max,
                    individual_chains[i].fxs[0][0].parameters.gain.max - (RMS_values[i]/RMS_range) * individual_chains[i].fxs[0][0].parameters.gain.range + random.random()*2 - 1
                    )
                )
            ###? ?? 
            individual_chains[i].fxs[1][0].randomize()
            individual_chains[i].fxs[2][0].randomize()
            individual_chains[i].fxs[3][0].randomize()
            
        #############
        # Sum chain #
        #############
        self.HPF[0].cutoff_frequency_hz = 2000 + (random.random()*2-1)*500
        self.LPF[0].cutoff_frequency_hz = 200 + (random.random()*2-1)*100

        self.snare_reverb[0].room_size = random.random()
        self.snare_reverb[0].damping = random.random()
        self.snare_reverb[0].width = random.random()
        self.snare_reverb[0].freeze_mode = random.random()
        self.snare_reverb[1].gain_db = random.random()*(-3) - 3

        self.hihat_reverb[0].room_size = random.random()
        self.hihat_reverb[0].damping = random.random()
        self.hihat_reverb[0].width = random.random()
        self.hihat_reverb[0].freeze_mode = random.random()
        self.hihat_reverb[1].gain_db = random.random()*(-3) - 3

        self.snare_delay[0].delay_seconds = random.random()
        self.snare_delay[0].feedback = random.random()*0.005
        self.snare_delay[1].gain_db = random.random()*(-3) - 7

        self.hihat_delay[0].delay_seconds = random.random()
        self.hihat_delay[0].feedback = random.random()*0.005
        self.hihat_delay[1].gain_db = random.random()*(-3) - 7

        self.mix_eq.fxs[0][0].randomize()

        self.limiter[0].gain_db = random.random()*20 + 5
        self.limiter[1].threshold_db = -random.random()
        self.limiter[1].release_ms = float(random.randrange(2, 1001))
    
    def apply(self, kick, snare, hihat):
        self.update_chains([kick, snare, hihat])

        #####################
        # Individual chains #
        #####################
        kick_modified = self.kick_chain.__call__([kick.T])
        snare_modified = self.snare_chain.__call__([snare.T])
        hihat_modified = self.hihat_chain.__call__([hihat.T])
        #############
        # Sum chain #
        #############
        snare_reverbed = [[0, 0]]
        hihat_reverbed = [[0, 0]]
        snare_delayed = [[0, 0]]
        hihat_delayed = [[0, 0]]

        if random.random() <= 0.5:
            snare_reverbed += self.HPF(self.snare_reverb(snare_modified[0], self.sample_rate), self.sample_rate)
        if random.random() <= 0.01:
            snare_reverbed +=  self.LPF(self.snare_reverb(snare_modified[0], self.sample_rate), self.sample_rate)
        if random.random() <= 0.5:
            hihat_reverbed += self.HPF(self.hihat_reverb(hihat_modified[0], self.sample_rate), self.sample_rate)
        if random.random() <= 0.01:
            hihat_reverbed += self.LPF(self.hihat_reverb(hihat_modified[0], self.sample_rate), self.sample_rate)
        if random.random() <= 0.5:
            snare_delayed += self.HPF(self.snare_delay(snare_modified[0], self.sample_rate), self.sample_rate)
        if random.random() <= 0.01:
            snare_delayed +=  self.LPF(self.snare_delay(snare_modified[0], self.sample_rate), self.sample_rate)
        if random.random() <= 0.5:
            hihat_delayed += self.HPF(self.hihat_delay(hihat_modified[0], self.sample_rate), self.sample_rate)
        if random.random() <= 0.01:
            hihat_delayed += self.LPF(self.hihat_delay(hihat_modified[0], self.sample_rate), self.sample_rate)
        
        drum_mix = self.limiter(self.mix_eq.__call__([kick_modified[0] + snare_modified[0] + hihat_modified[0]])[0], self.sample_rate)
        output = drum_mix + snare_reverbed + hihat_reverbed + snare_delayed + hihat_delayed

        return output.T


class SSChains():
    def __init__(self, mono:bool, sample_rate):
        if mono:
            n_channels = 1
        else:
            n_channels = 2
        self.mono = mono
        self.sample_rate = sample_rate

        #####################
        # Individual chains #
        #####################
            # GAIN
        gain_params = ParameterList()
        gain_params.add(Parameter('gain', -15.0, 'float', units='dB', minimum=-21.0, maximum=-10.0))
        gain_params.add(Parameter('invert', False, 'bool'))
        gain = Gain(parameters=gain_params)

            # EQ
        eq_params = ParameterList()
        eq_params.add(Parameter('low_shelf_gain', -0.2, 'float', minimum=-0.5, maximum=0.5))
        eq_params.add(Parameter('low_shelf_freq', 30.0, 'float', minimum=20.0, maximum=30.0))
        eq_params.add(Parameter('first_band_gain', 0.0, 'float', minimum=-2.0, maximum=2.0))
        eq_params.add(Parameter('first_band_freq', 75.0, 'float', minimum=50.0, maximum=100.0))
        eq_params.add(Parameter('first_band_q', 5.0, 'float', minimum=1.5, maximum=10.0))
        eq_params.add(Parameter('second_band_gain', 0.0, 'float', minimum=-2.0, maximum=2.0))
        eq_params.add(Parameter('second_band_freq', 150.0, 'float', minimum=100.0, maximum=200.0))
        eq_params.add(Parameter('second_band_q', 1.5, 'float', minimum=1.5, maximum=10.0))
        eq_params.add(Parameter('third_band_gain', 0.0, 'float', minimum=-2.0, maximum=2.0))
        eq_params.add(Parameter('third_band_freq', 400.0, 'float', minimum=300.0, maximum=500.0))
        eq_params.add(Parameter('third_band_q', 2.0, 'float', minimum=1.5, maximum=10.0))
        eq = Equaliser(n_channels=n_channels, sample_rate=sample_rate, bands=['low_shelf', 'first_band', 'second_band', 'third_band'], parameters=eq_params)

            # COMP
        comp_params = ParameterList()
        comp_params.add(Parameter('threshold', -20.0, 'float', units='dB', minimum=-50.0, maximum=0.0))
        comp_params.add(Parameter('attack_time', 10.0, 'float', units='ms', minimum=1.0, maximum=500.0))
        comp_params.add(Parameter('release_time', 100.0, 'float', units='ms', minimum=10.0, maximum=500.0))
        comp_params.add(Parameter('ratio', 4.0, 'float', minimum=2.0, maximum=10.0))
        comp = Compressor(sample_rate = sample_rate, parameters=comp_params)

            # PAN    
        pan_params = ParameterList()
        pan_params.add(Parameter('pan', 0.5, 'float', minimum=0.45, maximum=0.55))
        pan_params.add(Parameter('pan_law', '-4.5dB', 'string', options=['-4.5dB', 'linear', 'constant_power']))
        pan = Panner(parameters=pan_params)

            # CHAIN
        self.chain = create_effects_augmentation_chain([gain, eq, comp, pan], ir_dir_path=None, sample_rate=sample_rate)
        
        #############
        # Sum chain #
        #############
            # HPF
        self.HPF = Pedalboard([
            HighpassFilter(
                cutoff_frequency_hz=2000.0
            )
        ])
         
            # LPF
        self.LPF = Pedalboard([
            LowpassFilter(
                cutoff_frequency_hz=200.0
            )
        ])

            # REVERB
        self.reverb = Pedalboard([
            Reverb(
                room_size = 0.5, # 0 ~ 1
                damping = 0.5, # 0 ~ 1
                wet_level = 1.0, # 0 ~ 1
                dry_level = 0.0, # 0 ~ 1
                width = 1.0, # 0 ~ 1
                freeze_mode = 0 # 0 ~ 1
            ),
            pedalboard_gain(
                gain_db = -4.0
            )
        ])

            # DELAY
        self.delay = Pedalboard([
            Delay(
                delay_seconds = 0.5, # 0 ~
                feedback = 0.0, # 0 ~ 1
                mix = 1.0 # 0 ~ 1
            ),
            pedalboard_gain(
                gain_db = -4.0
            )
        ])

            # EQ
        mix_eq_params = ParameterList()
        mix_eq_params.add(Parameter('first_band_gain', 0.0, 'float', minimum=-1.0, maximum=1.0))
        mix_eq_params.add(Parameter('first_band_freq', 80.0, 'float', minimum=20.0, maximum=200.0))
        mix_eq_params.add(Parameter('first_band_q', 1.5, 'float', minimum=0.75, maximum=3.0))
        mix_eq_params.add(Parameter('second_band_gain', 0.0, 'float', minimum=-1.0, maximum=1.0))
        mix_eq_params.add(Parameter('second_band_freq', 800.0, 'float', minimum=200.0, maximum=3000.0))
        mix_eq_params.add(Parameter('second_band_q', 1.5, 'float', minimum=0.75, maximum=3.0))
        mix_eq_params.add(Parameter('third_band_gain', 0.0, 'float', minimum=-1.0, maximum=1.0))
        mix_eq_params.add(Parameter('third_band_freq', 6000.0, 'float', minimum=3000.0, maximum=20000.0))
        mix_eq_params.add(Parameter('third_band_q', 1.5, 'float', minimum=0.75, maximum=3.0))
        mix_eq = Equaliser(n_channels=n_channels, sample_rate=sample_rate, bands=['first_band', 'second_band', 'third_band'], parameters=mix_eq_params)
        self.mix_eq = create_effects_augmentation_chain([mix_eq], ir_dir_path=None, sample_rate=sample_rate)

            # LIMITER
        self.limiter = Pedalboard([
            pedalboard_gain(
                gain_db = 1.0
            ),
            Limiter(
                threshold_db=0.0, # MUSDB 랑 합쳐서 들어보고 판단.
                release_ms = 100 # 2.0 ~ 1000.0
            )
        ])

    def update_chains(self):
        #####################
        # Individual chains #
        #####################
        self.chain.fxs[0][0].randomize()
        self.chain.fxs[1][0].randomize()
        self.chain.fxs[2][0].randomize()
        self.chain.fxs[3][0].randomize()

        #############
        # Sum chain #
        #############
        self.HPF[0].cutoff_frequency_hz = 2000 + (random.random()*2-1)*500
        self.LPF[0].cutoff_frequency_hz = 200 + (random.random()*2-1)*100

        self.reverb[0].room_size = random.random()
        self.reverb[0].damping = random.random()
        self.reverb[0].width = random.random()
        self.reverb[0].freeze_mode = random.random()
        self.reverb[1].gain_db = random.random()*(-3) - 3

        self.delay[0].delay_seconds = random.random()
        self.delay[0].feedback = random.random()*0.005
        self.delay[1].gain_db = random.random()*(-3) - 7

        self.mix_eq.fxs[0][0].randomize()

        self.limiter[0].gain_db = random.random()*20 + 5
        self.limiter[1].threshold_db = -random.random()
        self.limiter[1].release_ms = float(random.randrange(2, 1001))
    
    def apply(self, sample, intensity):
        # reverb & delay probs
        prob_hpf_reverb = random.random()
        prob_lpf_reverb = random.random()
        prob_hpf_delay = random.random()
        prob_lpf_delay = random.random()
        # updating chains parameters
        self.update_chains()
        # applying chian
        sample_modified = self.chain.__call__([sample.T])
        sample_reverbed = [[0, 0]]
        sample_delayed = [[0, 0]]
        if prob_hpf_reverb <= 0.5:
            sample_reverbed += self.HPF(self.reverb(sample_modified[0], self.sample_rate), self.sample_rate)
        if prob_lpf_reverb <= 0.01:
            sample_reverbed +=  self.LPF(self.reverb(sample_modified[0], self.sample_rate), self.sample_rate)
        if prob_hpf_delay <= 0.5:
            sample_delayed += self.HPF(self.delay(sample_modified[0], self.sample_rate), self.sample_rate)
        if prob_lpf_delay <= 0.01:
            sample_delayed +=  self.LPF(self.delay(sample_modified[0], self.sample_rate), self.sample_rate)
        sample_modified = self.limiter(self.mix_eq.__call__([sample_modified[0]])[0], self.sample_rate)
        sample_modified = sample_modified + sample_reverbed + sample_delayed
        # updating chains parameters by intensity
        self.chain.fxs[1][0].parameters.low_shelf_gain.value = self.chain.fxs[1][0].parameters.low_shelf_gain.value * intensity
        self.chain.fxs[1][0].parameters.first_band_gain.value = self.chain.fxs[1][0].parameters.first_band_gain.value * intensity
        self.chain.fxs[1][0].parameters.second_band_gain.value = self.chain.fxs[1][0].parameters.second_band_gain.value * intensity
        self.chain.fxs[1][0].parameters.third_band_gain.value = self.chain.fxs[1][0].parameters.third_band_gain.value * intensity
        self.chain.fxs[2][0].parameters.threshold.value = self.chain.fxs[2][0].parameters.threshold.value * intensity
        self.chain.fxs[3][0].parameters.pan.value = (self.chain.fxs[3][0].parameters.pan.value - 0.5) * intensity + 0.5
        self.reverb[1].gain_db = self.reverb[1].gain_db - 30*(1-intensity)
        self.delay[1].gain_db = self.delay[1].gain_db - 30*(1-intensity)
        self.mix_eq.fxs[0][0].parameters.first_band_gain.value = self.mix_eq.fxs[0][0].parameters.first_band_gain.value * intensity
        self.mix_eq.fxs[0][0].parameters.second_band_gain.value = self.mix_eq.fxs[0][0].parameters.second_band_gain.value * intensity
        self.mix_eq.fxs[0][0].parameters.third_band_gain.value = self.mix_eq.fxs[0][0].parameters.third_band_gain.value * intensity
        self.limiter[1].threshold_db = self.limiter[1].threshold_db * intensity
        # applying chains
        sample_modified_intensity = self.chain.__call__([sample.T])
        sample_reverbed = [[0, 0]]
        sample_delayed = [[0, 0]]
        if prob_hpf_reverb <= 0.5:
            sample_reverbed += self.HPF(self.reverb(sample_modified_intensity[0], self.sample_rate), self.sample_rate)
        if prob_lpf_reverb <= 0.01:
            sample_reverbed +=  self.LPF(self.reverb(sample_modified_intensity[0], self.sample_rate), self.sample_rate)
        if prob_hpf_delay <= 0.5:
            sample_delayed += self.HPF(self.delay(sample_modified_intensity[0], self.sample_rate), self.sample_rate)
        if prob_lpf_delay <= 0.01:
            sample_delayed +=  self.LPF(self.delay(sample_modified_intensity[0], self.sample_rate), self.sample_rate)
        sample_modified_intensity = self.limiter(self.mix_eq.__call__([sample_modified_intensity[0]])[0], self.sample_rate)
        sample_modified_intensity = sample_modified_intensity + sample_reverbed + sample_delayed

        return sample_modified.T, sample_modified_intensity.T


if __name__ == '__main__':
    sschains = SSChains(False, 48000)
    x = np.random.rand(2, 2**17)
    a, b = sschains.apply(x, 0.0)

    print(a.shape, b.shape)

# sample_rate = 44100
# mono = False
# dict = {'eq':1, 'comp':1, 'pan':1, 'imager':1, 'reverb':1, 'gain':1}
# kick = librosa.load('./samples/kick_loop_0.wav', sr = sample_rate, mono=False)[0]
# snare = librosa.load('./samples/snare_loop_0.wav', sr = sample_rate, mono=False)[0]
# hihat = librosa.load('./samples/hihat_loop_0.wav', sr = sample_rate, mono=False)[0]

# drum_chains = DrumChains(mono = mono, sample_rate = sample_rate)
# output = drum_chains.apply(kick, snare, hihat)
# sf.write('./samples/drum_before_DAFXed.wav', np.transpose(kick[0] + snare[0] + hihat[0]), sample_rate, format = 'WAV', subtype = 'PCM_24')
# sf.write('./samples/drum_DAFXed.wav', output, sample_rate, format = 'WAV', subtype = 'PCM_24')

# kick_chain, snare_chain, hihat_chain = drum_chains(mono=False, sample_rate=sample_rate)

# sum_chain = 0

# update_chains([kick_chain, snare_chain, hihat_chain], sum_chain, [kick, snare, hihat], mono=False)

# kick_modified = kick_chain.__call__([kick.T])
# snare_modified = snare_chain.__call__([snare.T])
# hihat_modified = hihat_chain.__call__([hihat.T])
# drum = [kick_modified[0] + snare_modified[0] + hihat_modified[0]]
# drum_modified = sum_chain.__call__(drum)

# sf.write('./samples/drum_loop.wav', drum[0], 44100, format = 'WAV', subtype = 'PCM_24')
# sf.write('./samples/drum_loop_modified.wav', drum_modified[0], 44100, format = 'WAV', subtype = 'PCM_24')

# sf.write('./samples/kick_loop_modified.wav', kick_modified[0], 44100, format = 'WAV', subtype = 'PCM_24')
# sf.write('./samples/snare_loop_modified.wav', snare_modified[0], 44100, format = 'WAV', subtype = 'PCM_24')
# sf.write('./samples/hihat_loop_modified.wav', hihat_modified[0], 44100, format = 'WAV', subtype = 'PCM_24')

# 0.25
# 0.04
# 0.02

# # 이해한 점

# #1. create_effects_augmentation_chain 을 사용해서 eq, comp 등의 DAFX chain 을 만든다.
# #2. create_effects_augmentation_chain 은 recursive 하게 사용이 가능하다.
# #3. create_inst_effects_augmentation_chain 을 쓰기 전에 one-shot-sample 들에 DAFX 를 우선 써줘야 한다.
# #4. parameter randomize 하는 자체 내장 함수도 있고, 하나하나 변경도 가능하다.
# #5. augmentation chain 함수를 통해 단순히 묶어두는 것 뿐이다(한번에 통과시키려고). 각 DAFX 의 params 를 변경하려면 내부로 들어가서 DAFX 를 하나하나 건드려줘야 한다.

# # 궁금증

# #1. DAFX params 는 어떻게 조정하지? -> random 인지 아닌지를 모르겠다. -> random 아니네. 그럼 manually 어떻게 params 주는지를 봐야겠다.
# # -> 또 다시 헷갈리는게, 왜 parameter 에 min, max 가 있는지 모르겠다. 근데 위에서 단일 값으로 설정해줄 땐 min, max 도 설정값과 동일하게 하더라.
# # -> 따라서 드는 합리적 생각은, params 를 설정할 때 random 성을 얼마나 가할지를 min & max 로 조절한다는 것이다. 이걸 한번 실험해보자.
# # -> randomize 라는 자체 내장 함수가 있어서, 모든 value 들을 바꿔준다.
# # -> randomize 를 쓰면 굳이 update() 함수를 쓰지 않아도 된다. 하지만 'low_pass_eq.high_shelf_freq.value = 10000.0' 식으로 하나하나 randomize 해주면, 그 후에는 low_pass_eq.update() 를 해줘야 한다.


# low_pass_eq_params = ParameterList() # pymixconsole library 에서 온 애
# low_pass_eq_params.add(Parameter('high_shelf_gain', -50.0, 'float', minimum=-100.0, maximum=0.0))
# low_pass_eq_params.add(Parameter('high_shelf_freq', 8000.0, 'float', minimum=5000.0, maximum=10000.0))
# low_pass_eq = Equaliser(n_channels=2, \
#                             sample_rate=44100, \
#                             bands=['high_shelf'], \
#                             parameters=low_pass_eq_params)

# y, sr = sf.read('./samples/output.wav', sr = 44100, mono=False)
# output = low_pass_eq.process(sf.read('./samples/output.wav', sr = 44100, mono=False)[0])
# # print(output)
# sf.write('./samples/output_eq.wav', output, 44100, format = 'WAV', subtype = 'PCM_24')

# # # print(low_pass_eq.parameters)

# low_pass_eq.parameters.high_shelf_freq.value = 10000.0
# low_pass_eq.update()
# low_pass_eq.randomize()

# # print(low_pass_eq.parameters)
# output = low_pass_eq.process(librosa.load('./samples/output.wav', sr = 44100, mono=False)[0].T)
# sf.write('./samples/output_eq_changed.wav', output, 44100, format = 'WAV', subtype = 'PCM_24')
# # print(output)

# dict = {'eq':1, 'comp':1, 'pan':1, 'imager':1, 'reverb':1, 'gain':1}

# drum_chain = create_inst_effects_augmentation_chain('drums', dict, algorithmic=True)
# # print('EQ: ', drum_chain.fxs[0][0].fxs[0][0].parameters)
# # drum_chain.fxs[0][0].fxs[0][0].randomize()
# # print('EQ:', drum_chain.fxs[0][0].fxs[0][0].parameters)
# # print(low_pass_eq)
# # print('Comp:', drum_chain.fxs[0][0].fxs[1][0])
# # drum_chain.fxs[0][0].fxs[1][0].randomize()
# # print('Comp:', drum_chain.fxs[0][0].fxs[1][0])
# audio = librosa.load('./samples/output.wav', sr = 44100, mono=False)[0]
# print(audio.shape)
# output = drum_chain.__call__([audio.T])
# # sf.write('./samples/output_drummix.wav', output[0], 44100, format = 'WAV', subtype = 'PCM_24')