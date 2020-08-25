import json
from os.path import join, dirname
from ibm_watson import SpeechToTextV1
from ibm_watson.websocket import RecognizeCallback, AudioSource
from ibm_cloud_sdk_core.authenticators import IAMAuthenticator
import pyaudio
import wave
import requests
from urllib.parse import quote
import re
from ibm_watson import AssistantV2
import argparse
from ibm_watson import TextToSpeechV1
from ibm_cloud_sdk_core.authenticators import IAMAuthenticator
import os
import yaml
from ibm_watson import AssistantV2
from ibm_cloud_sdk_core.authenticators import IAMAuthenticator
import simpleaudio as sa

with open('apikey.yml') as f:
    data_of_yml = yaml.load(f, Loader=yaml.FullLoader)
    stt_api_key = data_of_yml.get('stt').get('apikey')
    stt_url = data_of_yml.get('stt').get('url')
    tts_api_key = data_of_yml.get('tts').get('apikey')
    tts_url = data_of_yml.get('tts').get('url')
    assistant_api_key = data_of_yml.get('assisstant').get('apikey')
    assistant_url = data_of_yml.get('assisstant').get('url')
    assisstant_id = data_of_yml.get('assisstant').get('assisstant_id')

form_1 = pyaudio.paInt16  # 16-bit resolution
chans = 1  # 1 channel
samp_rate = 44100  # 44.1kHz sampling rate
chunk = 4096  # 2^12 samples for buffer
record_secs = 5  # seconds to record
dev_index = 2  # device index found by p.get_device_info_by_index(ii)
wav_output_filename = 'audio.wav'  # name of .wav file

audio = pyaudio.PyAudio()  # create pyaudio instantiation

# create pyaudio stream
stream = audio.open(format=form_1, rate=samp_rate, channels=chans, \
                    input_device_index=dev_index, input=True, \
                    frames_per_buffer=chunk)
print("recording")
frames = []

# loop through stream and append audio chunks to frame array
for ii in range(0, int((samp_rate / chunk) * record_secs)):
    data = stream.read(chunk)
    frames.append(data)

print("finished recording")

# stop the stream, close it, and terminate the pyaudio instantiation
stream.stop_stream()
stream.close()
audio.terminate()

# save the audio frames as .wav file
wavefile = wave.open(wav_output_filename, 'wb')
wavefile.setnchannels(chans)
wavefile.setsampwidth(audio.get_sample_size(form_1))
wavefile.setframerate(samp_rate)
wavefile.writeframes(b''.join(frames))
wavefile.close()

authenticator = IAMAuthenticator(stt_api_key)
speech_to_text = SpeechToTextV1(
    authenticator=authenticator
)

speech_to_text.set_service_url(
    stt_url)


class MyRecognizeCallback(RecognizeCallback):
    def __init__(self):
        RecognizeCallback.__init__(self)

    def on_data(self, data):
        datae = data["results"][0]["alternatives"][0]["transcript"]
        output_response = datae
        return output_response
    output_response = on_data(data)

    def on_error(self, error):
        print('Error received: {}'.format(error))

    def on_inactivity_timeout(self, error):
        print('Inactivity timeout: {}'.format(error))


question = MyRecognizeCallback.output_response

myRecognizeCallback = MyRecognizeCallback()
with open(join(dirname(__file__), '/home/pi', 'audio.wav'),
          'rb') as audio_file:
    audio_source = AudioSource(audio_file)
    speech_to_text.recognize_using_websocket(
        audio=audio_source,
        content_type='audio/wav',
        recognize_callback=myRecognizeCallback,
        model='ar-AR_BroadbandModel',
    )

    authenticator = IAMAuthenticator(assistant_api_key)
    assistant = AssistantV2(
        version='2020-04-01',
        authenticator = authenticator
    )
    message_input = question
    message_input.encode('utf-8')
    assistant.set_service_url(assistant_url)
    session_id = assistant.create_session(
        assistant_id=assisstant_id
    ).get_result()
    session_idj = json.dumps(session_id['session_id'])[1 : -1]
    response = assistant.message(
        assistant_id=assisstant_id,
        session_id=session_idj,
        input={
            'message_type': 'text',
            'text': message_input
        }
    ).get_result()
    response_of_assistant = json.loads(json.dumps(response['output']['generic'][0]['text']))
    print(response_of_assistant)
    authenticator = IAMAuthenticator(tts_api_key)
    text_to_speech = TextToSpeechV1(
        authenticator=authenticator
    )

    text_to_speech.set_service_url(
        tts_url)

    with open('response.wav', 'wb') as audio_file:
        audio_file.write(
            text_to_speech.synthesize(
                response_of_assistant,
                voice='ar-AR_OmarVoice',
                accept='audio/wav'
            ).get_result().content)
filename = 'response.wav'
wave_obj = sa.WaveObject.from_wave_file(filename)
play_obj = wave_obj.play()
play_obj.wait_done()  # Wait until sound has finished playing
