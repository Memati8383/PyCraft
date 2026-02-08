import wave
import struct
import random
import math

def generate_rain_sound(filename, duration=3.0, sample_rate=44100):
    """
    Gerçekçi yağmur sesi oluşturur (sadece standart kütüphaneler ile)
    """
    num_samples = int(duration * sample_rate)
    audio = [0.0] * num_samples
    
    # Beyaz gürültü oluştur (yağmur damlalarının temel sesi)
    for i in range(num_samples):
        audio[i] = random.uniform(-0.2, 0.2)
    
    # Rastgele damla sesleri ekle
    num_drops = random.randint(80, 200)
    
    for _ in range(num_drops):
        pos = random.randint(0, num_samples - 1000)
        drop_duration = random.randint(100, 300)
        freq = random.uniform(1000, 2500)
        amplitude = random.uniform(0.15, 0.4)
        
        for j in range(drop_duration):
            if pos + j < num_samples:
                t = j / sample_rate
                # Damla sesi: sönümlü sinüs dalgası
                drop_sound = amplitude * math.sin(2 * math.pi * freq * t) * math.exp(-t * 15)
                audio[pos + j] += drop_sound
    
    # Normalize et
    max_val = max(abs(x) for x in audio)
    if max_val > 0:
        audio = [x / max_val * 0.7 for x in audio]
    
    # Fade in/out ekle
    fade_samples = int(0.15 * sample_rate)
    for i in range(fade_samples):
        audio[i] *= i / fade_samples
        audio[-(i+1)] *= i / fade_samples
    
    # WAV dosyasına yaz
    audio_int = [int(x * 32767) for x in audio]
    
    with wave.open(filename, 'w') as wav_file:
        wav_file.setnchannels(1)  # Mono
        wav_file.setsampwidth(2)  # 16-bit
        wav_file.setframerate(sample_rate)
        for sample in audio_int:
            wav_file.writeframes(struct.pack('<h', sample))
    
    print(f"✓ {filename} oluşturuldu")

def generate_thunder_sound(filename, duration=2.5, sample_rate=44100):
    """
    Gök gürültüsü sesi oluşturur
    """
    num_samples = int(duration * sample_rate)
    audio = [0.0] * num_samples
    
    # Düşük frekanslı gürültü (gök gürültüsünün gürlemesi)
    for i in range(num_samples):
        t = i / sample_rate
        # Birden fazla düşük frekans katmanı
        rumble = 0
        for freq in [40, 60, 80, 120]:
            phase = random.uniform(0, 2 * math.pi)
            rumble += math.sin(2 * math.pi * freq * t + phase) * random.uniform(0.3, 0.5)
        
        # Rastgele gürültü ekle
        noise = random.uniform(-0.3, 0.3)
        audio[i] = rumble + noise
    
    # Zarf (envelope) - başlangıçta ani artış, sonra yavaş azalma
    attack_samples = int(0.05 * sample_rate)
    decay_samples = num_samples - attack_samples
    
    for i in range(num_samples):
        if i < attack_samples:
            envelope = (i / attack_samples) ** 0.5
        else:
            decay_pos = (i - attack_samples) / decay_samples
            envelope = math.exp(-decay_pos * 3)
        audio[i] *= envelope
    
    # Normalize
    max_val = max(abs(x) for x in audio)
    if max_val > 0:
        audio = [x / max_val * 0.9 for x in audio]
    
    # WAV dosyasına yaz
    audio_int = [int(x * 32767) for x in audio]
    
    with wave.open(filename, 'w') as wav_file:
        wav_file.setnchannels(1)
        wav_file.setsampwidth(2)
        wav_file.setframerate(sample_rate)
        for sample in audio_int:
            wav_file.writeframes(struct.pack('<h', sample))
    
    print(f"✓ {filename} oluşturuldu")

def generate_wind_sound(filename, duration=4.0, sample_rate=44100):
    """
    Rüzgar sesi oluşturur
    """
    num_samples = int(duration * sample_rate)
    audio = [0.0] * num_samples
    
    # Düşük frekanslı gürültü (rüzgar uğultusu)
    for i in range(num_samples):
        t = i / sample_rate
        # Yavaş değişen rüzgar
        wind_base = math.sin(2 * math.pi * 0.5 * t) * 0.3
        wind_base += math.sin(2 * math.pi * 1.2 * t) * 0.2
        
        # Rastgele gürültü (rüzgar türbülansı)
        noise = random.uniform(-0.4, 0.4)
        
        # Düşük frekanslı bileşen
        low_freq = math.sin(2 * math.pi * 80 * t + random.uniform(0, 0.1)) * 0.2
        
        audio[i] = wind_base + noise * 0.6 + low_freq
    
    # Yumuşak fade in/out
    fade_samples = int(0.3 * sample_rate)
    for i in range(fade_samples):
        audio[i] *= i / fade_samples
        audio[-(i+1)] *= i / fade_samples
    
    # Normalize
    max_val = max(abs(x) for x in audio)
    if max_val > 0:
        audio = [x / max_val * 0.6 for x in audio]
    
    # WAV dosyasına yaz
    audio_int = [int(x * 32767) for x in audio]
    
    with wave.open(filename, 'w') as wav_file:
        wav_file.setnchannels(1)
        wav_file.setsampwidth(2)
        wav_file.setframerate(sample_rate)
        for sample in audio_int:
            wav_file.writeframes(struct.pack('<h', sample))
    
    print(f"✓ {filename} oluşturuldu")

def generate_lightning_sound(filename, duration=0.3, sample_rate=44100):
    """
    Şimşek çarpma sesi oluşturur (kısa ve keskin)
    """
    num_samples = int(duration * sample_rate)
    audio = [0.0] * num_samples
    
    # Yüksek frekanslı çatırtı
    for i in range(num_samples):
        t = i / sample_rate
        # Çok hızlı sönümlü yüksek frekans
        crack = 0
        for freq in [2000, 3000, 4000, 5000]:
            crack += math.sin(2 * math.pi * freq * t) * math.exp(-t * 50)
        
        # Yüksek frekanslı gürültü
        noise = random.uniform(-1, 1) * math.exp(-t * 30)
        
        audio[i] = crack * 0.5 + noise * 0.5
    
    # Normalize
    max_val = max(abs(x) for x in audio)
    if max_val > 0:
        audio = [x / max_val * 0.95 for x in audio]
    
    # WAV dosyasına yaz
    audio_int = [int(x * 32767) for x in audio]
    
    with wave.open(filename, 'w') as wav_file:
        wav_file.setnchannels(1)
        wav_file.setsampwidth(2)
        wav_file.setframerate(sample_rate)
        for sample in audio_int:
            wav_file.writeframes(struct.pack('<h', sample))
    
    print(f"✓ {filename} oluşturuldu")

def generate_heavy_rain_sound(filename, duration=3.5, sample_rate=44100):
    """
    Şiddetli yağmur sesi oluşturur
    """
    num_samples = int(duration * sample_rate)
    audio = [0.0] * num_samples
    
    # Daha yoğun beyaz gürültü
    for i in range(num_samples):
        audio[i] = random.uniform(-0.4, 0.4)
    
    # Çok daha fazla damla sesi
    num_drops = random.randint(200, 400)
    
    for _ in range(num_drops):
        pos = random.randint(0, num_samples - 500)
        drop_duration = random.randint(80, 250)
        freq = random.uniform(1200, 3000)
        amplitude = random.uniform(0.2, 0.5)
        
        for j in range(drop_duration):
            if pos + j < num_samples:
                t = j / sample_rate
                drop_sound = amplitude * math.sin(2 * math.pi * freq * t) * math.exp(-t * 20)
                audio[pos + j] += drop_sound
    
    # Normalize
    max_val = max(abs(x) for x in audio)
    if max_val > 0:
        audio = [x / max_val * 0.8 for x in audio]
    
    # Fade in/out
    fade_samples = int(0.15 * sample_rate)
    for i in range(fade_samples):
        audio[i] *= i / fade_samples
        audio[-(i+1)] *= i / fade_samples
    
    # WAV dosyasına yaz
    audio_int = [int(x * 32767) for x in audio]
    
    with wave.open(filename, 'w') as wav_file:
        wav_file.setnchannels(1)
        wav_file.setsampwidth(2)
        wav_file.setframerate(sample_rate)
        for sample in audio_int:
            wav_file.writeframes(struct.pack('<h', sample))
    
    print(f"✓ {filename} oluşturuldu")

def main():
    print("Hava durumu sesleri oluşturuluyor...\n")
    
    print("→ Yağmur sesleri...")
    for i in range(1, 5):
        filename = f"assets/sounds/environment/rain{i}.wav"
        duration = random.uniform(2.5, 4.0)
        generate_rain_sound(filename, duration=duration)
    
    print("\n→ Şiddetli yağmur sesleri...")
    for i in range(1, 3):
        filename = f"assets/sounds/environment/heavy_rain{i}.wav"
        duration = random.uniform(3.0, 4.0)
        generate_heavy_rain_sound(filename, duration=duration)
    
    print("\n→ Gök gürültüsü sesleri...")
    for i in range(1, 4):
        filename = f"assets/sounds/environment/thunder{i}.wav"
        duration = random.uniform(2.0, 3.5)
        generate_thunder_sound(filename, duration=duration)
    
    print("\n→ Şimşek sesleri...")
    for i in range(1, 3):
        filename = f"assets/sounds/environment/lightning{i}.wav"
        duration = random.uniform(0.2, 0.4)
        generate_lightning_sound(filename, duration=duration)
    
    print("\n→ Rüzgar sesleri...")
    for i in range(1, 4):
        filename = f"assets/sounds/environment/wind{i}.wav"
        duration = random.uniform(3.5, 5.0)
        generate_wind_sound(filename, duration=duration)
    
    print("\n✓ Tüm hava durumu sesleri başarıyla oluşturuldu!")

if __name__ == "__main__":
    main()
