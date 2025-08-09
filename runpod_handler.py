import runpod
import json
import uuid
import logging
import numpy as np
import soundfile as sf
import io
import time

# NO TTS IMPORTS - NO MODEL LOADING - BUT SIMULATE REAL TTS FORMAT

def simulate_indic_parler_tts_chunks(text, sample_rate=22050, chunk_duration=0.5):
    """Simulate Indic Parler TTS audio chunks with realistic format"""
    
    # Estimate realistic audio length based on text (rough: 10 chars per second)
    estimated_duration = max(2.0, len(text) / 10.0)
    
    total_samples = int(estimated_duration * sample_rate)
    chunk_samples = int(chunk_duration * sample_rate)
    
    # Generate more realistic speech-like audio (multiple frequencies)
    t = np.linspace(0, estimated_duration, total_samples)
    
    # Simulate speech formants (like vowels)
    fundamental = 150  # Base frequency
    audio_data = (
        0.3 * np.sin(2 * np.pi * fundamental * t) +           # Fundamental
        0.2 * np.sin(2 * np.pi * fundamental * 2.5 * t) +     # Second formant
        0.1 * np.sin(2 * np.pi * fundamental * 4.0 * t)       # Third formant
    )
    
    # Add some envelope (fade in/out like speech)
    envelope = np.exp(-t / (estimated_duration * 0.7))
    audio_data = (audio_data * envelope * 0.3).astype(np.float32)
    
    # Split into chunks (same as real Parler TTS)
    chunks = []
    for i in range(0, len(audio_data), chunk_samples):
        chunk = audio_data[i:i + chunk_samples]
        if len(chunk) < chunk_samples:
            # Pad last chunk to maintain consistent format
            chunk = np.pad(chunk, (0, chunk_samples - len(chunk)), 'constant')
        
        # Convert to WAV bytes (EXACT same format as real TTS)
        buffer = io.BytesIO()
        sf.write(buffer, chunk, sample_rate, format='WAV')
        buffer.seek(0)
        wav_bytes = buffer.read()
        chunks.append(wav_bytes)
    
    return chunks

def handler(job):
    """Simulate EXACT Indic Parler TTS streaming format"""
    try:
        job_input = job['input']
        text = job_input.get('text', '').strip()
        voice = job_input.get('voice', 'aryan_default')
        play_steps_in_s = job_input.get('play_steps_in_s', 0.5)
        
        logging.info(f"🔍 Handler received job: text='{text[:50]}...', voice='{voice}'")
        
        if not text:
            yield {"error": "Text required"}
            return

        request_id = str(uuid.uuid4())[:8]
        logging.info(f"🎵 Simulated TTS request [{request_id}]: '{text[:50]}...'")
        
        # EXACT SAME MESSAGE FORMAT as real Indic Parler TTS
        yield {
            "type": "stream_start",
            "request_id": request_id,
            "text": text,
            "voice": voice,
            "sampling_rate": 22050  # Same as real TTS
        }
        
        # Generate simulated TTS chunks
        audio_chunks = simulate_indic_parler_tts_chunks(text, chunk_duration=play_steps_in_s)
        
        # Stream chunks with EXACT same format as real TTS
        for chunk_id, wav_chunk in enumerate(audio_chunks, 1):
            # Simulate processing delay (like real TTS)
            time.sleep(0.1)
            
            logging.info(f"📤 [{request_id}] Simulated TTS chunk {chunk_id}: {len(wav_chunk)} bytes")
            
            yield {
                "type": "audio_chunk",
                "chunk_id": chunk_id,
                "audio_data": wav_chunk.hex(),  # EXACT hex format as real TTS
                "request_id": request_id
            }
        
        yield {
            "type": "stream_complete", 
            "request_id": request_id,
            "total_chunks": len(audio_chunks)
        }
        
    except Exception as e:
        logging.error(f"Handler error: {e}")
        yield {"error": str(e)}   
        
if __name__ == "__main__":
    runpod.serverless.start({
        "handler": handler,
        "return_aggregate_stream": True
    })
