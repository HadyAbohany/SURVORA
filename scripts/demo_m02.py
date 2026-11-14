"""Offline M02 sequence against installed FastAPI app; does not fabricate real Gemini calls."""
from fastapi.testclient import TestClient
from app.main import app

client=TestClient(app)
state={'oxygen':65,'power':35,'oxygen_generator_status':'low_power','research_lab_on':True}

def emit(name,number,priority='normal'):
    body={'event_id':f'M02-demo-{number}','event_type':name,'priority':priority,'session_id':'m02-demo',
          'mission_id':'M02_OXYGEN_MYSTERY','state_revision':number,'language':'en','game_state':state}
    payload=client.post('/events',json=body).json()
    print(name,'=>',payload['text'] or '[silent]', 'audio:',payload['audio_ref'])
    return payload

emit('MISSION_STARTED',1)
state.update(oxygen=25,power=15)
r=emit('OXYGEN_LOW',2,'high')
if r['followup_hint_recommended']:
    chat={'question':'Explain why the oxygen plant is underpowered and give one clue.',
          'mission_id':'M02_OXYGEN_MYSTERY','game_state':state,'hint_level':1}
    print('AUTO SCIENCE HINT =>',client.post('/chat',json=chat).json()['answer'])
# This is a simulated Unity state change only inside this standalone scripted demo.
state.update(oxygen=52,power=70,oxygen_generator_status='normal',research_lab_on=False)
emit('OXYGEN_RESTORED',3)
emit('MISSION_COMPLETED',4)
