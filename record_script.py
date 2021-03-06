import os
import pyaudio
import wave
import PySimpleGUI as sg
import json

# Consts
RECORDS_PATH = os.path.dirname(os.path.realpath(__file__)) + '/'
f = open('config.json', 'r')
config = json.load(f)
WORDS = config['words']
NUM_RECORDS = config['records']
RECORD_SECONDS = config['record_sec']
f.close() 

# GUI layout
layout = [
    [
        sg.Text('Recorder Name:', font=('Helvetica', 64), key='-CURR_WORD-'),
    ],
    [
        sg.Input('', pad=4, font=('Helvetica', 16), size=16, enable_events=True, key='-NAME-'),
        sg.Button('Start', pad=4, button_color='#66B2FF', font=('Helvetica', 16), size=16, enable_events=True, key='-START-'),
    ],
    [
        sg.Button('Replay', pad=4, button_color='gray', font=('Helvetica', 16), size=16, enable_events=True, key='-PLAY-', disabled=True,),
        sg.Button('Record', pad=4, button_color='gray', font=('Helvetica', 16), size=32, enable_events=True, key='-REC-', disabled=True,),
        sg.Button('Next', pad=4, button_color='gray', font=('Helvetica', 16), focus=True, size=32, enable_events=True, key='-NEXT-', disabled=True),
    ],
]

# PyAudio Consts
CHUNK = 1024
FORMAT = pyaudio.paInt16
CHANNELS = 1
RATE = 44100

# Record function
def record(output_name):
    WAVE_OUTPUT_FILENAME = output_name
    p = pyaudio.PyAudio()

    stream = p.open(format=FORMAT,
                    channels=CHANNELS,
                    rate=RATE,
                    input=True,
                    frames_per_buffer=CHUNK)

    print('* recording - Start!')
    global window
    window['-REC-'].update(button_color='red')
    window.finalize()

    frames = []

    for i in range(0, int(RATE / CHUNK * RECORD_SECONDS)):
        data = stream.read(CHUNK)
        frames.append(data)

    print('* done recording - Stop!')

    stream.stop_stream()
    stream.close()
    p.terminate()

    wf = wave.open(WAVE_OUTPUT_FILENAME, 'wb')
    wf.setnchannels(CHANNELS)
    wf.setsampwidth(p.get_sample_size(FORMAT))
    wf.setframerate(RATE)
    wf.writeframes(b''.join(frames))
    wf.close()

    print(WAVE_OUTPUT_FILENAME)

def play_recording(file_name):
    wf = wave.open(file_name, 'rb')

    # instantiate PyAudio (1)
    p = pyaudio.PyAudio()

    # open stream (2)
    stream = p.open(format=p.get_format_from_width(wf.getsampwidth()),
                    channels=wf.getnchannels(),
                    rate=wf.getframerate(),
                    output=True)

    # read data
    data = wf.readframes(CHUNK)

    # play stream (3)
    while len(data) > 0:
        stream.write(data)
        data = wf.readframes(CHUNK)

    # stop stream (4)
    stream.stop_stream()
    stream.close()

    # close PyAudio (5)
    p.terminate()

# Build the directory tree
def build_dir_tree(name):
    # root dir
    cont_dir = RECORDS_PATH+name
    os.mkdir(cont_dir)

    # init words list and dir tree
    words_list = []
    for i in range(len(WORDS)):
        word = WORDS[i]
        word_dir = f'{cont_dir}/{word}'
        os.mkdir(word_dir)
        for pron in ['good', 'bad']:
            pron_dir = f'{word_dir}/{pron}'
            os.mkdir(pron_dir)
            for j in range(NUM_RECORDS):
                words_list.append(f'{word}/{pron}')

    return words_list, cont_dir

# Disable button
def disable_button(window, key):
    window[key].update(disabled=True)
    window[key].update(button_color='gray')
def enable_button(window, key):
    window[key].update(disabled=False)
    window[key].update(button_color='#66B2FF')

# Main
def main():
    # init vars
    word_cnt = 0
    words_list = []
    cont_dir = ''
    file_path = ''

    global window
    window = sg.Window('Lisp Records', layout,
                       element_justification='c', finalize=True)

    # Run the Event Loop
    while True:
        event, values = window.read()
        if event == sg.WIN_CLOSED:
            break
        if event == '-START-':
            # update buttons
            enable_button(window, '-NEXT-')
            enable_button(window, '-REC-')
            disable_button(window, '-START-')
            window['-NAME-'].update(disabled=True)
            
            # prepare for recording
            name = values['-NAME-']
            words_list, cont_dir = build_dir_tree(name)
            word, pron = words_list[word_cnt].split('/', 2)
            curr_word = f'{word} | {pron} ({str(word_cnt % NUM_RECORDS + 1)})'
            window['-CURR_WORD-'].update(curr_word)

        if event == '-REC-':
            word, pron = words_list[word_cnt].split('/', 2)
            pron_dir = cont_dir + '/' + words_list[word_cnt]
            file_path = f'{pron_dir}/{str(word_cnt // (2 * NUM_RECORDS))}_{pron[0]}{str(word_cnt % NUM_RECORDS)}.wav'
            record(file_path)
            window['-REC-'].update(button_color='#66B2FF')
            enable_button(window, '-PLAY-')
        
        if event == '-PLAY-':
            play_recording(file_path)

        if event == '-NEXT-':
            word_cnt += 1
            if(word_cnt == len(words_list)):
                break
            word, pron = words_list[word_cnt].split('/', 2)
            curr_word = f'{word} | {pron} ({str(word_cnt % NUM_RECORDS + 1)})'
            window['-CURR_WORD-'].update(curr_word)
            disable_button(window, '-PLAY-')
    window.close()
    exit()


if __name__ == '__main__':
    main()
