# DrumSlayer
The End of Drum Reconstruction

Mixture Audio -> Drum Midi & Drum Source

## Dataset
`pip install -r requirements.txt`

Make your dataset by yourself

1. put your own drum one shots at `data_generate/midi_2_wav/one_shots/<train,test,valid>/<kick,snare,hhclosed>`

- get data from `scp -rP 20022 marg@147.47.120.221:/home/marg/st_drums/one_shots <데이터 저장공간>` 

2. `data_generate/data_generate.py --data_type all --oneshot_dir <데이터 저장공간> `


# Reference
