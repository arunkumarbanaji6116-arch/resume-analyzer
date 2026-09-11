import hashlib
import json
import logging
import urllib.request
import urllib.error
from config import Config

logger = logging.getLogger(__name__)

VOICES = {
    'arun': {
        'id': '21m00Tcm4TlvDq8ikWAM',
        'name': 'Arun (Lead Technical Interviewer)',
        'gender': 'male',
        'desc': 'Clear, analytical, and focused'
    },
    'shravan': {
        'id': 'pNInz6obpgDQGcFmaJgB',
        'name': 'Shravan (Senior Hiring Manager)',
        'gender': 'male',
        'desc': 'Deep, authoritative, and structured'
    },
    'rakesh': {
        'id': 'VR6AewLTigWG4xSOukaG',
        'name': 'Rakesh (Technical Lead)',
        'gender': 'male',
        'desc': 'Sharp, engaging, and articulate'
    },
    'sai_srinath': {
        'id': 'JBFqnCBsd6RMkjVDRZzb',
        'name': 'Sai Srinath (Executive Director)',
        'gender': 'male',
        'desc': 'Warm, seasoned, and measured'
    }
}

# Aliases for backward compatibility with existing session values
VOICES['rachel'] = VOICES['arun']
VOICES['adam'] = VOICES['shravan']
VOICES['sarah'] = VOICES['rakesh']
VOICES['george'] = VOICES['sai_srinath']

_AUDIO_CACHE = {}


def get_voice_id(key_or_id: str = None) -> str:
    key_lower = (key_or_id or '').lower().strip()
    if key_lower in VOICES:
        return VOICES[key_lower]['id']
    if key_or_id and len(key_or_id) >= 15:
        return key_or_id
    return getattr(Config, 'ELEVENLABS_DEFAULT_VOICE', None) or VOICES['arun']['id']


def generate_speech(text: str, voice_key_or_id: str = None) -> bytes | None:
    text = (text or '').strip()
    if not text:
        return None

    api_key = getattr(Config, 'ELEVENLABS_API_KEY', None)
    if not api_key or api_key == 'your-elevenlabs-api-key-here':
        return None

    voice_id = get_voice_id(voice_key_or_id)

    cache_key = hashlib.sha256(f'{voice_id}:{text}'.encode('utf-8')).hexdigest()
    if cache_key in _AUDIO_CACHE:
        return _AUDIO_CACHE[cache_key]

    url = f'https://api.elevenlabs.io/v1/text-to-speech/{voice_id}'
    payload = {
        'text': text,
        'model_id': 'eleven_turbo_v2_5',
        'voice_settings': {
            'stability': 0.5,
            'similarity_boost': 0.75,
            'style': 0.0,
            'use_speaker_boost': True
        }
    }

    req = urllib.request.Request(
        url,
        data=json.dumps(payload).encode('utf-8'),
        headers={
            'xi-api-key': api_key,
            'Content-Type': 'application/json',
            'Accept': 'audio/mpeg',
            'User-Agent': 'CareerForgeAI/1.0'
        },
        method='POST'
    )

    try:
        with urllib.request.urlopen(req, timeout=12) as response:
            if response.status == 200:
                audio_bytes = response.read()
                if len(_AUDIO_CACHE) > 100:
                    _AUDIO_CACHE.pop(next(iter(_AUDIO_CACHE)))
                _AUDIO_CACHE[cache_key] = audio_bytes
                return audio_bytes
            return None
    except Exception as e:
        logger.warning(f'ElevenLabs TTS error: {e}')
        return None
