# -*- coding: utf-8 -*-
"""
PyCraft - Minecraft Python Klonu
Gelişmiş 3D voxel tabanlı sandbox oyunu

Özellikler:
- Prosedürel dünya üretimi (Perlin Noise)
- Chunk tabanlı optimizasyon sistemi
- Gece-gündüz döngüsü
- Hava durumu sistemi (yağmur, fırtına)
- Hayvan AI sistemi
- Crafting sistemi
- Can ve açlık mekaniği
- Gelişmiş ses sistemi
"""

from ursina import *
import ursina
from ursina.prefabs.first_person_controller import FirstPersonController
from perlin_noise import PerlinNoise
import random
import threading
import math
import time
from collections import deque
import os
import heapq
import platform
from datetime import datetime
import ctypes
import psutil
import importlib.metadata
from ursina.lights import DirectionalLight

# Çökmeyi önlemek için bounds güncellemelerini durdur
DirectionalLight.update_bounds = lambda self: None
from ursina import Sky
Sky.instances = []  # Kirli referansları temizle

# Uygulama Başlatma
app = Ursina()

# Pencere Ayarları
window.title = 'PYCRAFT - Minecraft Python Klonu'  # Oyun penceresinin başlık çubuğundaki isim
window.borderless = False  # Pencere kenarlıklı olsun (True olursa kenarlıksız tam ekran)
window.fullscreen = False  # Tam ekran modu kapalı (True olursa tam ekran açılır)
window.exit_button.visible = False  # Sağ üst köşedeki X (çıkış) butonu gizli
window.fps_counter.enabled = True  # Optimize: FPS sayacı açıldı (performans takibi için)
window.entity_counter.enabled = False  # Sahne içindeki entity sayısı gösterilmesin
window.collider_counter.enabled = False  # Collider (çarpışma kutusu) sayısı gösterilmesin
window.cog_button_enabled = False  # Ayarlar (dişli) butonu gizli
window.size = (1280, 720)  # Pencere boyutu: 1280 piksel genişlik, 720 piksel yükseklik (720p)
window.vsync = True  # Optimize: VSync açıldı (screen tearing önler, GPU yükünü azaltır)
window.show_ursina_splash = False  # Oyun başlarken Ursina logosu gösterilmesin
mouse.visible = False  # Fare imleci gizli (FPS oyunları için - kamera kontrolü aktif)

# Sahne Ayarları
# BGR değişimine karşı güvenli olması ve daha temiz görünmesi için beyaz sis
scene.fog_density = (20, 60) 
scene.fog_color = color.white 

# Sky ayarları - hata payını azaltmak için sadeleştirildi
sky_entity = Sky(color=color.azure)

# --- GELİŞTİRİLMİŞ GÖKYÜZÜ SİSTEMİ ---
class EnhancedSky:
    """
    Gelişmiş gökyüzü sistemi - Güneş, ay ve yıldızları yönetir.
    Gece-gündüz döngüsü ile senkronize çalışır.
    """
    def __init__(self):
        # Ana gökyüzü entity'si (mevcut sky_entity'yi kullan)
        self.sky_entity = sky_entity
        
        # Güneş entity'si
        self.sun = Entity(
            parent=scene,
            model='sphere',
            texture='assets/textures/ui/sun.png',
            scale=15,
            position=(100, 60, -100),
            color=color.yellow,
            billboard=True  # Her zaman kameraya baksın
        )
        
        # Ay entity'si
        self.moon = Entity(
            parent=scene,
            model='sphere',
            texture='assets/textures/ui/moon.png',
            scale=12,
            position=(-100, 60, 100),
            color=color.white,
            billboard=True,
            enabled=False  # Başlangıçta gizli (gündüz)
        )
        
        # Yıldızlar listesi
        self.stars = []
        self.create_stars()
        
        print("[GÖKYÜZÜ] Gelişmiş gökyüzü sistemi başlatıldı!")
    
    def create_stars(self):
        """Gökyüzüne rastgele konumlanmış yıldızlar oluştur - Optimize edildi"""
        for _ in range(75):  # Optimize: 150'den 75'e düşürüldü
            # Rastgele konum (gökyüzü küresi üzerinde)
            x = random.uniform(-200, 200)
            y = random.uniform(40, 150)
            z = random.uniform(-200, 200)
            
            # Parlaklık ve boyut varyasyonu
            brightness = random.uniform(0.5, 1.0)
            size = random.uniform(0.3, 1.0)
            
            star = Entity(
                parent=scene,
                model='sphere',
                texture='assets/textures/ui/star.png',
                scale=size,
                position=(x, y, z),
                color=color.rgb(brightness, brightness, brightness),
                billboard=True,
                enabled=False  # Başlangıçta gizli
            )
            self.stars.append(star)
    
    def update_sky(self, time_of_day, is_day, is_transition):
        """
        Gökyüzünü zamanla güncelle - Renk, güneş/ay pozisyonu ve yıldızlar
        Optimize edildi: Yıldızlar sadece gerektiğinde güncellenir
        
        Args:
            time_of_day: Oyun içi saat (0-2400)
            is_day: Gündüz mü?
            is_transition: Geçiş anı mı (şafak/alacakaranlık)?
        """
        # Gökyüzü rengi - Zamana göre değişir
        if is_day:
            sky_color = color.azure  # Gündüz: Açık mavi
        elif is_transition:
            if time_of_day < 600:  # Şafak (05:00-06:00)
                sky_color = color.orange
            else:  # Alacakaranlık (18:00-19:00)
                sky_color = color.red
        else:
            sky_color = color.rgb(0.05, 0.05, 0.2)  # Gece: Koyu lacivert
        
        self.sky_entity.color = sky_color
        
        # Güneş ve ay pozisyonu - Dairesel hareket
        time_angle = (time_of_day / 2400.0) * math.pi * 2
        
        # Güneş pozisyonu
        sun_x = math.cos(time_angle) * 120
        sun_y = max(20, math.sin(time_angle) * 100)
        sun_z = math.sin(time_angle) * 120
        self.sun.position = (sun_x, sun_y, sun_z)
        self.sun.enabled = is_day or is_transition
        
        # Ay pozisyonu (güneşin tam tersi)
        moon_x = -sun_x
        moon_y = max(20, -math.sin(time_angle) * 100)
        moon_z = -sun_z
        self.moon.position = (moon_x, moon_y, moon_z)
        self.moon.enabled = not is_day
        
        # Yıldızlar - Optimize: Sadece gece ve her 0.1 saniyede bir güncelle
        if not hasattr(self, '_last_star_update'):
            self._last_star_update = 0
        
        current_time = time.time()
        if current_time - self._last_star_update > 0.1:
            self._last_star_update = current_time
            for star in self.stars:
                star.enabled = not is_day
                # Geçiş anında yıldızların parlaklığını ayarla
                if is_transition:
                    alpha = 0.5 if time_of_day > 1800 else 0.2
                    r, g, b = star.color.r, star.color.g, star.color.b
                    star.color = color.rgba(r, g, b, alpha)
                elif not is_day:
                    # Gece: Tam parlaklık
                    r, g, b = star.color.r, star.color.g, star.color.b
                    star.color = color.rgba(r, g, b, 1.0)

# Gelişmiş gökyüzü sistemi
enhanced_sky = EnhancedSky()

# --- GELİŞTİRİLMİŞ GECE-GÜNDÜZ DÖNGÜSÜ SİSTEMİ ---
class EnhancedDayNightCycle:
    def __init__(self):
        # Zaman parametreleri
        self.day_length = 1200.0  # Tam döngü süresi (saniye) = 20 dakika
        self.day_duration = 600.0  # Gündüz süresi (saniye) = 10 dakika
        self.night_duration = 600.0  # Gece süresi (saniye) = 10 dakika
        
        # Oyun içi zaman (0-2400, 2400 = 24 saat)
        self.time_of_day = 600.0  # Başlangıç: 06:00 (gündüz)
        
        # Hız çarpanı: Gerçek 1 saniye = oyun içi 1/20 dakika = 0.05 oyun dakikası
        self.time_speed = 0.05 * 60  # Dakikayı saniyeye çevir: 0.05 * 60 = 3 saniye/oyun dakikası
        
        # Zamanın normalde ilerleyip ilerlemediği (duraklatma için)
        self.time_paused = False
        
        # Renk paletleri
        self.day_sky_color = color.azure
        self.night_sky_color = color.rgb(0, 0, 0.2)  # Koyu lacivert
        self.dawn_sky_color = color.orange
        self.dusk_sky_color = color.red
        
        self.day_fog_color = color.white
        self.night_fog_color = color.rgb(0, 0, 0.1)  # Koyu mavi sis
        
        # Işık sistemi
        self.ambient_light = AmbientLight(color=color.white, parent=scene)
        self.sun_light = DirectionalLight(
            direction=(0.5, -1, 0.5),
            color=color.white,
            parent=scene,
            shadows=False # Çökmeyi önlemek için gölgeler devre dışı bırakıldı
        )
        self.sun_light.look_at(Vec3(1, -1, 1))
        
        # Ay ve yıldızlar
        self.moon = None
        self.stars = []
        self.create_night_objects()
        
        # UI Göstergesi
        self.time_display = Text(
            parent=camera.ui,
            text='',
            position=(0, 0.45),
            origin=(0, 0),
            scale=1.2,
            color=color.white,
            background=True,
            background_color=color.rgba(0, 0, 0, 150)
        )
        
        # Zaman çubuğu
        self.time_bar_bg = Entity(
            parent=camera.ui,
            model='quad',
            color=color.rgba(0, 0, 0, 100),
            scale=(0.3, 0.02),
            position=(0, 0.41)
        )
        
        self.time_bar_fill = Entity(
            parent=self.time_bar_bg,
            model='quad',
            color=color.azure,
            scale=(0, 1),
            origin=(-0.5, 0),
            position=(-0.5, 0)
        )
        
        # Hız göstergesi
        self.speed_display = Text(
            parent=camera.ui,
            text='',
            position=(0.42, 0.45),
            origin=(0, 0),
            scale=0.8,
            color=color.yellow,
            background=True,
            background_color=color.rgba(0, 0, 0, 150)
        )
        
        # Durum değişkenleri
        self.is_day = True
        self.is_transition = False
        
    def create_night_objects(self):
        """Ay ve yıldızları oluştur"""
        # Ay
        self.moon = Entity(
            parent=scene,
            model='sphere',
            texture='assets/textures/ui/moon.png',
            scale=10,
            position=(100, 80, -100),
            color=color.white,
            billboard=True,
            enabled=False  # Başlangıçta gizli (gündüz)
        )
        
        # Yıldızlar (performans için 50 adet - optimize edildi)
        for _ in range(50):  # Optimize: 100'den 50'ye düşürüldü
            # Rastgele konum (gökyüzü küresi üzerinde)
            x = random.uniform(-150, 150)
            y = random.uniform(50, 120)
            z = random.uniform(-150, 150)
            
            # Parlaklık varyasyonu
            brightness = random.uniform(0.7, 1.0)
            size = random.uniform(0.5, 1.5)
            
            star = Entity(
                parent=scene,
                model='sphere',
                texture='assets/textures/ui/star.png',
                scale=size,
                position=(x, y, z),
                color=color.rgb(brightness, brightness, brightness),
                billboard=True,
                enabled=False  # Başlangıçta gizli
            )
            self.stars.append(star)
    
    def update(self, dt):
        """Zamanı güncelle ve görsel efektleri ayarla"""
        # Zaman duraklatılmışsa güncelleme yapma
        if self.time_paused:
            return
        
        # Zamanı ilerlet
        self.time_of_day += dt * self.time_speed
        
        # 24 saatlik döngü
        if self.time_of_day >= 2400:
            self.time_of_day = 0
        
        # Gündüz/gece kontrolü
        old_is_day = self.is_day
        self.is_day = 600 <= self.time_of_day < 1800  # 06:00-18:00 arası gündüz
        
        # Geçiş durumu (alacakaranlık)
        self.is_transition = (
            (500 <= self.time_of_day < 600) or  # Şafak: 05:00-06:00
            (1800 <= self.time_of_day < 1900)   # Alacakaranlık: 18:00-19:00
        )
        
        # Görsel efektleri güncelle
        self.update_sky_and_fog()
        self.update_lighting()
        self.update_night_objects()
        self.update_ui()
    
    def update_sky_and_fog(self):
        """Gökyüzü ve sis rengini güncelle"""
        # Zamanın yüzdesini hesapla (0-1)
        time_percent = self.time_of_day / 2400.0
        
        if self.is_day:
            # Gündüz: açık mavi
            sky_color = self.day_sky_color
            fog_color = self.day_fog_color
        elif self.is_transition:
            # Geçiş: turuncu-kırmızı tonları
            if self.time_of_day < 600:  # Şafak
                transition_percent = (self.time_of_day - 500) / 100.0
                sky_color = lerp(self.night_sky_color, self.dawn_sky_color, transition_percent)
                fog_color = lerp(self.night_fog_color, color.orange, transition_percent)
            else:  # Alacakaranlık
                transition_percent = (self.time_of_day - 1800) / 100.0
                sky_color = lerp(self.day_sky_color, self.dusk_sky_color, transition_percent)
                fog_color = lerp(self.day_fog_color, color.red, transition_percent)
        else:
            # Gece: koyu lacivert
            sky_color = self.night_sky_color
            fog_color = self.night_fog_color
        
        # Sky entity'sini güncelle (gelişmiş gökyüzü sistemi ile)
        enhanced_sky.update_sky(self.time_of_day, self.is_day, self.is_transition)
        
        # Sis rengini güncelle
        scene.fog_color = fog_color
    
    def update_lighting(self):
        """Işık seviyelerini güncelle - gelişmiş gece karartma sistemi"""
        if self.is_day:
            # Gündüz: parlak
            target_ambient = color.white
            target_sun = color.white
            sun_intensity = 1.0
            # Gece karartma overlay'ini kaldır
            self.remove_night_overlay()
        elif self.is_transition:
            # Geçiş: orta seviye
            if self.time_of_day < 600:  # Şafak
                transition_percent = (self.time_of_day - 500) / 100.0
                target_ambient = lerp(color.gray, color.white, transition_percent)
                target_sun = lerp(color.gray, color.white, transition_percent)
                sun_intensity = lerp(0.3, 1.0, transition_percent)
                # Şafakta overlay'i yavaşça kaldır
                self.update_night_overlay(1.0 - transition_percent)
            else:  # Alacakaranlık
                transition_percent = (self.time_of_day - 1800) / 100.0
                target_ambient = lerp(color.white, color.gray, transition_percent)
                target_sun = lerp(color.white, color.gray, transition_percent)
                sun_intensity = lerp(1.0, 0.3, transition_percent)
                # Alacakaranlıkta overlay'i yavaşça ekle
                self.update_night_overlay(transition_percent)
        else:
            # Gece: karanlık
            target_ambient = color.rgb(0.2, 0.2, 0.3)  # Çok koyu mavi
            target_sun = color.rgb(0.1, 0.1, 0.2)     # Neredeyse siyah
            sun_intensity = 0.1
            # Gece overlay'ini tam göster
            self.update_night_overlay(1.0)
        
        # Işıkları yumuşak geçişle güncelle
        self.ambient_light.color = lerp(self.ambient_light.color, target_ambient, time.dt * 2)
        self.sun_light.color = lerp(self.sun_light.color, target_sun, time.dt * 2)
        
        # Güneş pozisyonunu güncelle (basit bir dairesel hareket)
        time_angle = (self.time_of_day / 2400.0) * math.pi * 2
        sun_x = math.cos(time_angle) * 100
        sun_y = max(10, math.sin(time_angle) * 100)
        sun_z = math.sin(time_angle) * 100
        
        self.sun_light.position = (sun_x, sun_y, sun_z)
        self.sun_light.look_at(Vec3(0, 0, 0))
    
    def update_night_overlay(self, darkness_level):
        """Gece karartma overlay'ini güncelle"""
        if not hasattr(self, 'night_overlay'):
            # Gece karartma overlay'ini oluştur
            self.night_overlay = Entity(
                parent=camera.ui,
                model='quad',
                color=color.rgba(0, 0, 0.1, 0),  # Koyu mavi overlay
                scale=(2, 2),
                z=0.1  # UI'nin önünde ama diğer elementlerin arkasında
            )
        
        # Karanlık seviyesine göre alpha değerini ayarla
        alpha = darkness_level * 0.6  # Maksimum %60 karartma
        self.night_overlay.color = color.rgba(0, 0, 0.1, alpha)
        self.night_overlay.enabled = darkness_level > 0
    
    def remove_night_overlay(self):
        """Gece overlay'ini kaldır"""
        if hasattr(self, 'night_overlay'):
            self.night_overlay.enabled = False
    
    def update_night_objects(self):
        """Ay ve yıldızları görünürlüğünü güncelle"""
        # Gündüzse gizle, gece ise göster
        should_show = not self.is_day
        
        if self.moon:
            self.moon.enabled = should_show
            
            # Ayın parlaklığını ayarla (alacakaranlıkta daha soluk)
            if self.is_transition:
                self.moon.color = color.rgba(1, 1, 1, 0.5)
            else:
                self.moon.color = color.white
        
        # Yıldızları güncelle
        for star in self.stars:
            star.enabled = should_show
            
            # Geçiş durumunda yıldızları yavaşça göster/gizle
            if self.is_transition:
                if self.time_of_day < 600:  # Şafakta gizle
                    alpha = 1.0 - ((self.time_of_day - 500) / 100.0)
                else:  # Alacakaranlıkta göster
                    alpha = (self.time_of_day - 1800) / 100.0
                
                r, g, b = star.color.r, star.color.g, star.color.b
                star.color = color.rgba(r, g, b, alpha * 0.7)
            elif self.is_day:
                star.color = color.rgba(1, 1, 1, 0)  # Tamamen şeffaf
            else:
                r, g, b = star.color.r, star.color.g, star.color.b
                star.color = color.rgba(r, g, b, 0.7)  # Normal parlaklık
    
    def update_ui(self):
        """Zaman göstergesini güncelle"""
        # Saati formatla (HH:MM)
        hours = int(self.time_of_day // 100)
        minutes = int((self.time_of_day % 100) * 0.6)  # 0-99'u 0-59'a çevir
        
        time_str = f"{hours:02d}:{minutes:02d}"
        
        # Gündüz/gece bilgisi
        if self.is_day:
            period = "GÜNDÜZ"
        elif self.is_transition:
            if self.time_of_day < 600:
                period = "ŞAFAK"
            else:
                period = "ALACAKARANLIK"
        else:
            period = "GECE"
        
        # UI metnini güncelle
        time_display_text = f"{period} {time_str}"
        if self.time_paused:
            time_display_text += " [DURAKLATILDI]"
        
        self.time_display.text = time_display_text
        
        # Zaman çubuğunu güncelle
        time_percent = self.time_of_day / 2400.0
        self.time_bar_fill.scale_x = time_percent
        
        # Çubuğun rengini zamanla değiştir
        if self.is_day:
            bar_color = color.azure
        elif self.is_transition:
            bar_color = color.orange
        else:
            bar_color = color.rgb(0, 0, 0.5)  # Koyu mavi
        
        self.time_bar_fill.color = bar_color
        
        # Hız göstergesini güncelle
        if self.time_paused:
            self.speed_display.text = "DURAKLATILDI"
            self.speed_display.color = color.red
        else:
            speed_multiplier = self.time_speed / (0.05 * 60)  # Normal hıza göre
            self.speed_display.text = f"x{speed_multiplier:.1f}"
            
            if speed_multiplier > 1:
                self.speed_display.color = color.yellow
            else:
                self.speed_display.color = color.white
    
    def get_time_string(self):
        """Zamanı string olarak döndür"""
        hours = int(self.time_of_day // 100)
        minutes = int((self.time_of_day % 100) * 0.6)
        
        if self.is_day:
            return f"Gündüz {hours:02d}:{minutes:02d}"
        elif self.is_transition:
            if self.time_of_day < 600:
                return f"Şafak {hours:02d}:{minutes:02d}"
            else:
                return f"Alacakaranlık {hours:02d}:{minutes:02d}"
        else:
            return f"Gece {hours:02d}:{minutes:02d}"
    
    def skip_to_morning(self):
        """Sabah 06:00'a atla (uyuma mekaniği için)"""
        self.time_of_day = 600.0
        print("[DAYNIGHT] Sabah 06:00'a atlandı!")
    
    # --- TEST FONKSİYONLARI ---
    
    def add_hours(self, hours=1):
        """Saati ileri al"""
        old_time = self.time_of_day
        self.time_of_day += hours * 100  # Her saat 100 birim
        
        # 24 saatlik döngü
        if self.time_of_day >= 2400:
            self.time_of_day -= 2400
        
        print(f"[DAYNIGHT] Saat {hours} saat ileri alındı: {self.format_time(old_time)} -> {self.format_time(self.time_of_day)}")
    
    def subtract_hours(self, hours=1):
        """Saati geri al"""
        old_time = self.time_of_day
        self.time_of_day -= hours * 100  # Her saat 100 birim
        
        # 24 saatlik döngü
        if self.time_of_day < 0:
            self.time_of_day += 2400
        
        print(f"[DAYNIGHT] Saat {hours} saat geri alındı: {self.format_time(old_time)} -> {self.format_time(self.time_of_day)}")
    
    def add_minutes(self, minutes=10):
        """Dakika ileri al"""
        old_time = self.time_of_day
        # Dakikaları saat sistemine çevir (60 dakika = 100 birim)
        self.time_of_day += (minutes / 60.0) * 100
        
        # 24 saatlik döngü
        if self.time_of_day >= 2400:
            self.time_of_day -= 2400
        
        print(f"[DAYNIGHT] Saat {minutes} dakika ileri alındı: {self.format_time(old_time)} -> {self.format_time(self.time_of_day)}")
    
    def subtract_minutes(self, minutes=10):
        """Dakika geri al"""
        old_time = self.time_of_day
        # Dakikaları saat sistemine çevir (60 dakika = 100 birim)
        self.time_of_day -= (minutes / 60.0) * 100
        
        # 24 saatlik döngü
        if self.time_of_day < 0:
            self.time_of_day += 2400
        
        print(f"[DAYNIGHT] Saat {minutes} dakika geri alındı: {self.format_time(old_time)} -> {self.format_time(self.time_of_day)}")
    
    def set_time(self, hour, minute=0):
        """Belirli bir saate ayarla"""
        old_time = self.time_of_day
        # Saat ve dakikayı sistem saatine çevir
        self.time_of_day = hour * 100 + (minute / 60.0) * 100
        
        # 24 saatlik döngü
        if self.time_of_day >= 2400:
            self.time_of_day -= 2400
        
        print(f"[DAYNIGHT] Saat ayarlandı: {self.format_time(old_time)} -> {self.format_time(self.time_of_day)}")
    
    def set_speed(self, multiplier=1.0):
        """Zaman hızını ayarla"""
        old_speed = self.time_speed
        # Normal hız: 0.05 * 60 = 3 saniye/oyun dakikası
        base_speed = 0.05 * 60
        self.time_speed = base_speed * multiplier
        
        print(f"[DAYNIGHT] Zaman hızı değiştirildi: x{old_speed/base_speed:.1f} -> x{multiplier:.1f}")
    
    def toggle_pause(self):
        """Zamanı duraklat/devam ettir"""
        self.time_paused = not self.time_paused
        status = "DURAKLATILDI" if self.time_paused else "DEVAM ETTİRİLDİ"
        print(f"[DAYNIGHT] Zaman {status}")
    
    def format_time(self, time_value):
        """Saat değerini okunabilir formata çevir"""
        hours = int(time_value // 100)
        minutes = int((time_value % 100) * 0.6)
        return f"{hours:02d}:{minutes:02d}"
    
    def print_current_time(self):
        """Mevcut zamanı konsola yazdır"""
        print(f"[DAYNIGHT] Mevcut zaman: {self.get_time_string()}")

# --- YAĞMUR SİSTEMİ ---
class SimpleRainSystem:
    def __init__(self):
        self.is_raining = False
        self.rain_particles = []
        self.max_particles = 200  # Optimize edildi: 400'den 200'e düşürüldü
        self.particle_pool = []  # Object pooling için
        self.weather_type = "clear"
        self.current_rain_type = "medium"
        
        # Ses efektleri
        self.sound_cache = {}
        self.load_sounds()
        
        # Yağmur türleri - optimize edildi
        self.rain_types = {
            'light': {'particle_count': 50, 'speed': 10.0, 'size': (0.08, 1.2, 0.08), 'volume': 0.4},
            'medium': {'particle_count': 100, 'speed': 15.0, 'size': (0.1, 1.5, 0.1), 'volume': 0.6},
            'heavy': {'particle_count': 150, 'speed': 20.0, 'size': (0.12, 2.0, 0.12), 'volume': 0.8},
            'storm': {'particle_count': 200, 'speed': 25.0, 'size': (0.15, 2.5, 0.15), 'volume': 1.0}
        }
        
        # Hava durumu ayarları
        self.weather_settings = {
            'clear': {'rain_type': None, 'chance': 0.0},
            'cloudy': {'rain_type': 'light', 'chance': 0.3},
            'overcast': {'rain_type': 'medium', 'chance': 0.7},
            'rainy': {'rain_type': 'heavy', 'chance': 1.0},
            'stormy': {'rain_type': 'storm', 'chance': 1.0}
        }
        
        print("[YAĞMUR] SimpleRainSystem başlatıldı!")
        
    def load_sounds(self):
        """Ses dosyalarını yükle - Yeni environment sesleri ile"""
        try:
            # Yağmur sesleri (rain1-4.wav)
            self.sound_cache['rain_variants'] = []
            for i in range(1, 5):
                rain_path = f'assets/sounds/environment/rain{i}.wav'
                if os.path.exists(rain_path):
                    audio = Audio(rain_path, loop=True, autoplay=False, volume=0.7)
                    self.sound_cache['rain_variants'].append(audio)
            
            # Şiddetli yağmur sesleri (heavy_rain1-2.wav)
            self.sound_cache['heavy_rain_variants'] = []
            for i in range(1, 3):
                path = f'assets/sounds/environment/heavy_rain{i}.wav'
                if os.path.exists(path):
                    audio = Audio(path, loop=True, autoplay=False, volume=0.8)
                    self.sound_cache['heavy_rain_variants'].append(audio)
            
            # Gök gürültüsü sesleri (thunder1-3.wav)
            self.sound_cache['thunder_variants'] = []
            for i in range(1, 4):
                path = f'assets/sounds/environment/thunder{i}.wav'
                if os.path.exists(path):
                    self.sound_cache['thunder_variants'].append(Audio(
                        path, loop=False, autoplay=False, volume=0.9
                    ))
            
            # Şimşek sesleri (lightning1-2.wav)
            self.sound_cache['lightning_variants'] = []
            for i in range(1, 3):
                path = f'assets/sounds/environment/lightning{i}.wav'
                if os.path.exists(path):
                    self.sound_cache['lightning_variants'].append(Audio(
                        path, loop=False, autoplay=False, volume=0.8
                    ))
            
            # Rüzgar sesleri (wind1-3.wav)
            self.sound_cache['wind_variants'] = []
            for i in range(1, 4):
                path = f'assets/sounds/environment/wind{i}.wav'
                if os.path.exists(path):
                    audio = Audio(path, loop=True, autoplay=False, volume=0.4)
                    self.sound_cache['wind_variants'].append(audio)
            
            # Splash sesi (damla çarpma)
            splash_path = 'assets/sounds/block/place.wav'  # Geçici olarak place sesini kullan
            if os.path.exists(splash_path):
                self.sound_cache['splash'] = Audio(
                    splash_path, loop=False, autoplay=False, volume=0.3
                )

            print(f"[YAĞMUR] Sesler yüklendi:")
            print(f"  - {len(self.sound_cache.get('rain_variants', []))} yağmur sesi")
            print(f"  - {len(self.sound_cache.get('heavy_rain_variants', []))} şiddetli yağmur sesi")
            print(f"  - {len(self.sound_cache.get('thunder_variants', []))} gök gürültüsü")
            print(f"  - {len(self.sound_cache.get('lightning_variants', []))} şimşek sesi")
            print(f"  - {len(self.sound_cache.get('wind_variants', []))} rüzgar sesi")
            
        except Exception as e:
            print(f"[YAĞMUR] Ses yükleme hatası: {e}")
            self.sound_cache = {}
        
    def start_rain(self, rain_type='medium'):
        """Yağmuru başlat - güçlendirilmiş seslerle"""
        if rain_type not in self.rain_types:
            rain_type = 'medium'
            
        self.is_raining = True
        self.current_rain_type = rain_type
        self.max_particles = self.rain_types[rain_type]['particle_count']
        
        print(f"[YAĞMUR] {rain_type.title()} yağmur başladı!")
        print(f"[YAĞMUR] Max parçacık: {self.max_particles}")
        
        # Yağmur türüne göre ses seç
        if rain_type in ['heavy', 'storm']:
            # Şiddetli yağmur için heavy_rain sesleri
            rain_variants = self.sound_cache.get('heavy_rain_variants', [])
            if not rain_variants:
                rain_variants = self.sound_cache.get('rain_variants', [])
        else:
            # Normal yağmur sesleri
            rain_variants = self.sound_cache.get('rain_variants', [])
        
        if rain_variants:
            try:
                # Önce tüm aktif yağmur seslerini durdur
                if 'active_rain' in self.sound_cache and self.sound_cache['active_rain']:
                    self.sound_cache['active_rain'].stop()
                
                # Rastgele bir varyant seç ve oynat
                active_rain = random.choice(rain_variants)
                rain_data = self.rain_types[rain_type]
                volume = rain_data.get('volume', 0.6)
                active_rain.volume = volume
                active_rain.play()
                self.sound_cache['active_rain'] = active_rain
                print(f"[YAĞMUR] Yağmur sesi başlatıldı! Tür: {rain_type}, Ses seviyesi: {volume}")
            except Exception as e:
                print(f"[YAĞMUR] Ses hatası: {e}")
        
        # Rüzgar sesi ekle (fırtınalı havada)
        if rain_type == 'storm':
            wind_variants = self.sound_cache.get('wind_variants', [])
            if wind_variants:
                try:
                    if 'active_wind' in self.sound_cache and self.sound_cache['active_wind']:
                        self.sound_cache['active_wind'].stop()
                    
                    active_wind = random.choice(wind_variants)
                    active_wind.volume = 0.5
                    active_wind.play()
                    self.sound_cache['active_wind'] = active_wind
                    print("[YAĞMUR] Rüzgar sesi eklendi!")
                except Exception as e:
                    print(f"[YAĞMUR] Rüzgar ses hatası: {e}")
        
        # Atmosfer efektlerini ayarla
        if rain_type in ['heavy', 'storm']:
            scene.fog_density = (10, 40)
            print("[YAĞMUR] Yoğun sis aktif!")
        else:
            scene.fog_density = (15, 50)
            print("[YAĞMUR] Hafif sis aktif!")
        
    def stop_rain(self):
        """Yağmuru durdur - Optimize edildi"""
        self.is_raining = False
        
        # Aktif yağmur sesini durdur
        if 'active_rain' in self.sound_cache and self.sound_cache['active_rain']:
            self.sound_cache['active_rain'].stop()
            self.sound_cache['active_rain'] = None
        
        # Aktif rüzgar sesini durdur
        if 'active_wind' in self.sound_cache and self.sound_cache['active_wind']:
            self.sound_cache['active_wind'].stop()
            self.sound_cache['active_wind'] = None
        
        # Tüm varyantları garantiye almak için durdur
        for rv in self.sound_cache.get('rain_variants', []):
            rv.stop()
        for rv in self.sound_cache.get('heavy_rain_variants', []):
            rv.stop()
        for wv in self.sound_cache.get('wind_variants', []):
            wv.stop()
        
        # Mevcut parçacıkları pool'a geri koy (destroy yerine)
        for particle in self.rain_particles[:]:
            particle.enabled = False
            self.particle_pool.append(particle)
        self.rain_particles.clear()
        
        # Atmosfer efektlerini sıfırla
        scene.fog_density = (20, 60)
        
        print("[YAĞMUR] Yağmur durdu!")
    
    def create_rain_particle(self):
        """Yağmur damlası oluştur - Object pooling ile optimize edildi"""
        if len(self.rain_particles) >= self.max_particles:
            return None
        
        # Pool'dan parçacık al veya yeni oluştur
        if self.particle_pool:
            particle = self.particle_pool.pop()
            particle.enabled = True
        else:
            rain_data = self.rain_types[self.current_rain_type]
            particle = Entity(
                model='cube',
                color=color.rgb(0.3, 0.6, 1.0),
                scale=rain_data['size'],
                collider=None
            )
        
        # Pozisyonu ayarla
        player_pos = player.position if 'player' in globals() else Vec3(0, 0, 0)
        angle = random.uniform(0, 2 * math.pi)
        distance = random.uniform(10, 40)
        
        x = player_pos.x + math.cos(angle) * distance
        z = player_pos.z + math.sin(angle) * distance
        y = player_pos.y + random.uniform(30, 50)
        
        particle.position = Vec3(x, y, z)
        particle.speed = self.rain_types[self.current_rain_type]['speed']
        particle.creation_time = time.time()
        
        self.rain_particles.append(particle)
        return particle
    
    def update(self, dt):
        """Yağmur sistemi güncellemesi"""
        if not self.is_raining:
            return
        
        # Mevcut parçacıkları güncelle
        particles_to_remove = []
        player_pos = player.position if 'player' in globals() else Vec3(0, 0, 0)
        
        for particle in self.rain_particles:
            # Aşağı doğru hareket
            particle.y -= particle.speed * dt
            
            # Yere değdi mi kontrol et
            if particle.y <= player_pos.y - 3:
                # Splash efekti ve sesi
                self.create_splash_effect(particle.position)
                particles_to_remove.append(particle)
                continue
            
            # Çok uzaklaştı mı
            distance = (particle.position - player_pos).length()
            if distance > 60:
                particles_to_remove.append(particle)
                continue
            
            # Çok uzun süre yaşadı mı
            if time.time() - particle.creation_time > 10:
                particles_to_remove.append(particle)
        
        # Eski parçacıkları kaldır - Object pooling ile optimize edildi
        for particle in particles_to_remove:
            if particle in self.rain_particles:
                self.rain_particles.remove(particle)
                # Destroy yerine pool'a geri koy
                particle.enabled = False
                self.particle_pool.append(particle)
        
        # Yeni parçacıklar oluştur - optimize edildi
        spawn_count = max(1, int(20 * dt))  # Optimize: 40'tan 20'ye düşürüldü
        for _ in range(spawn_count):
            if self.create_rain_particle() is None:
                break
        
        # Debug bilgisi (her 3 saniyede bir)
        if not hasattr(self, 'last_debug_time'):
            self.last_debug_time = time.time()
        
        if time.time() - self.last_debug_time > 3.0:
            print(f"[YAĞMUR] Aktif parçacık: {len(self.rain_particles)}/{self.max_particles}")
            self.last_debug_time = time.time()
        
        # Gök gürültüsü efekti (fırtınalı havada)
        if self.current_rain_type == 'storm':
            self.create_thunder_effect()
    
    def create_splash_effect(self, position):
        """Yağmur damlası çarpma efekti ve sesi"""
        # Splash sesi çal - daha sık çalsın
        if 'splash' in self.sound_cache and self.sound_cache['splash'] and random.random() < 0.3:
            # %30 olasılıkla ses çal (daha sık)
            try:
                self.sound_cache['splash'].pitch = random.uniform(0.8, 1.4)
                self.sound_cache['splash'].play()
            except Exception as e:
                print(f"[YAĞMUR] Splash ses hatası: {e}")
        
        # Küçük splash parçacıkları
        for _ in range(random.randint(2, 4)):
            splash = Entity(
                model='cube',
                color=color.rgb(0.7, 0.9, 1.0),
                scale=(0.03, 0.03, 0.03),
                position=position + Vec3(
                    random.uniform(-0.3, 0.3),
                    0.1,
                    random.uniform(-0.3, 0.3)
                ),
                parent=scene
            )
            
            # Splash animasyonu
            splash.animate_y(splash.y + random.uniform(0.2, 0.5), duration=0.3)
            splash.animate_color(color.clear, duration=0.3)
            
            # Temizlik (Animasyondan sonra güvenli bekleyiş)
            destroy(splash, delay=0.4)
    
    def create_thunder_effect(self):
        """Gök gürültüsü efekti - fırtınalı havada"""
        if random.random() < 0.01:  # %1 şans her frame'de
            # Önce şimşek sesi (kısa ve keskin)
            lightning_variants = self.sound_cache.get('lightning_variants', [])
            if lightning_variants:
                try:
                    lightning = random.choice(lightning_variants)
                    lightning.pitch = random.uniform(0.9, 1.2)
                    lightning.play()
                except Exception as e:
                    print(f"[YAĞMUR] Lightning ses hatası: {e}")
            
            # Ardından gök gürültüsü (0.2-0.5 saniye sonra)
            delay = random.uniform(0.2, 0.5)
            invoke(self._play_thunder_sound, delay=delay)
    
    def _play_thunder_sound(self):
        """Gök gürültüsü sesini çal (şimşekten sonra)"""
        thunder_variants = self.sound_cache.get('thunder_variants', [])
        if thunder_variants:
            try:
                active_thunder = random.choice(thunder_variants)
                active_thunder.pitch = random.uniform(0.7, 1.1)
                active_thunder.play()
                print(f"[YAĞMUR] ⚡ GÖK GÜRÜLTÜSÜ!")
                
                # Ekran titremesi efekti
                if hasattr(camera, 'shake'):
                    camera.shake(duration=0.3, magnitude=1)
            except Exception as e:
                print(f"[YAĞMUR] Thunder ses hatası: {e}")
    
    def toggle_rain(self):
        """Yağmuru aç/kapat (test için)"""
        print(f"[YAĞMUR] Toggle çağrıldı. Mevcut durum: {self.is_raining}")
        if self.is_raining:
            self.stop_rain()
        else:
            self.start_rain('medium')
    
    def set_weather(self, weather_type):
        """Hava durumuna göre yağmuru ayarla"""
        if weather_type not in self.weather_settings:
            return
        
        self.weather_type = weather_type
        settings = self.weather_settings[weather_type]
        
        # Yağmur olasılığını kontrol et
        if random.random() < settings['chance']:
            if settings['rain_type']:
                self.start_rain(settings['rain_type'])
            else:
                self.stop_rain()
        else:
            self.stop_rain()
    
    def get_rain_info(self):
        """Yağmur sistemi bilgilerini döndür"""
        rain_data = self.rain_types.get(self.current_rain_type, {})
        return {
            'is_raining': self.is_raining,
            'particle_count': len(self.rain_particles),
            'max_particles': self.max_particles,
            'rain_type': self.current_rain_type,
            'weather_type': self.weather_type,
            'speed': rain_data.get('speed', 0),
            'volume': f"%{int(rain_data.get('volume', 0.6) * 100)}"
        }

# Yağmur sistemini oluştur
rain_system = SimpleRainSystem()

# EnhancedDayNightCycle örneğini oluştur
day_night_cycle = EnhancedDayNightCycle()

# Kaplamaları Yükle - Her bloğun özellikleri: kaplama, temel kırma süresi (saniye), tercih edilen alet
# tercih_edilen_alet: None = el yeterli, 'pickaxe' (kazma), 'shovel' (kürek), 'axe' (balta)
# Alet hız çarpanı: Doğru aletle 3 kat daha hızlı
blocks = {
    'grass':   {'texture': 'assets/textures/blocks/grass',   'color': color.white, 'base_break_time': 0.6,  'preferred_tool': 'shovel',  'is_passable': False},
    'stone':   {'texture': 'assets/textures/blocks/stone',   'color': color.white, 'base_break_time': 1.5,  'preferred_tool': 'pickaxe', 'is_passable': False},
    'dirt':    {'texture': 'assets/textures/blocks/dirt', 'color': color.white, 'base_break_time': 0.5,  'preferred_tool': 'shovel',  'is_passable': False},
    'wood':    {'texture': 'assets/textures/blocks/wood',    'color': color.white, 'base_break_time': 2.0,  'preferred_tool': 'axe',     'is_passable': False},
    'bedrock': {'texture': 'assets/textures/blocks/bedrock', 'color': color.white, 'base_break_time': -1,   'preferred_tool': None,    'is_passable': False},
    'leaves':  {'texture': 'assets/textures/blocks/leaves',  'color': color.white, 'base_break_time': 0.1,  'preferred_tool': None,    'is_passable': True}, 
    'crafting_table': {'texture': 'assets/textures/blocks/crafting_table', 'color': color.white, 'base_break_time': 2.5, 'preferred_tool': 'axe', 'is_passable': False},
    'log':     {'texture': 'assets/textures/blocks/log',     'color': color.white, 'base_break_time': 2.0,  'preferred_tool': 'axe',     'is_passable': False},
    'coal_ore':    {'texture': 'assets/textures/blocks/coal_ore',    'color': color.white, 'base_break_time': 3.0,  'preferred_tool': 'pickaxe', 'is_passable': False},
    'iron_ore':    {'texture': 'assets/textures/blocks/iron_ore',    'color': color.white, 'base_break_time': 4.0,  'preferred_tool': 'pickaxe', 'is_passable': False},
    'diamond_ore': {'texture': 'assets/textures/blocks/diamond_ore', 'color': color.white, 'base_break_time': 6.0,  'preferred_tool': 'pickaxe', 'is_passable': False},
    'wool':        {'texture': 'assets/textures/blocks/wool',        'color': color.white, 'base_break_time': 0.8,  'preferred_tool': 'shears',  'is_passable': False},
}

# Alet tanımları
tools = {
    'pickaxe': {'texture': 'assets/textures/items/iron_pickaxe', 'type': 'tool', 'damage': 25, 'effective_blocks': ['stone', 'bedrock']},
    'shovel':  {'texture': 'assets/textures/items/iron_shovel',  'type': 'tool', 'damage': 15, 'effective_blocks': ['grass', 'dirt']},
    'axe':     {'texture': 'assets/textures/items/iron_axe',     'type': 'tool', 'damage': 40, 'effective_blocks': ['wood', 'leaves', 'log', 'crafting_table']},
    # Yeni aletler (Crafting ile gelenler)
    'wooden_pickaxe': {'texture': 'assets/textures/items/wooden_pickaxe', 'type': 'tool', 'damage': 15, 'effective_blocks': ['stone']},
    'stone_pickaxe':  {'texture': 'assets/textures/items/stone_pickaxe',  'type': 'tool', 'damage': 20, 'effective_blocks': ['stone', 'bedrock']},
    'wooden_shovel':  {'texture': 'assets/textures/items/wooden_shovel',  'type': 'tool', 'damage': 12, 'effective_blocks': ['grass', 'dirt']},
    'stone_shovel':   {'texture': 'assets/textures/items/stone_shovel',   'type': 'tool', 'damage': 15, 'effective_blocks': ['grass', 'dirt']},
    'wooden_axe':     {'texture': 'assets/textures/items/wooden_axe',     'type': 'tool', 'damage': 30, 'effective_blocks': ['wood', 'leaves', 'log', 'crafting_table']},
    'stone_axe':      {'texture': 'assets/textures/items/stone_axe',      'type': 'tool', 'damage': 35, 'effective_blocks': ['wood', 'leaves', 'log', 'crafting_table']},
    # Swords
    'wooden_sword':   {'texture': 'assets/textures/items/wooden_sword', 'type': 'weapon', 'damage': 20, 'effective_blocks': []}, # 2 Kalp Hasarı
    'stone_sword':    {'texture': 'assets/textures/items/stone_sword',  'type': 'weapon', 'damage': 30, 'effective_blocks': []},  # 3 Kalp Hasarı
    # Iron Tools
    'iron_pickaxe':   {'texture': 'assets/textures/items/iron_pickaxe', 'type': 'tool', 'damage': 30, 'effective_blocks': ['stone', 'coal_ore', 'iron_ore']},
    'iron_shovel':    {'texture': 'assets/textures/items/iron_shovel',  'type': 'tool', 'damage': 20, 'effective_blocks': ['grass', 'dirt']},
    'iron_axe':       {'texture': 'assets/textures/items/iron_axe',     'type': 'tool', 'damage': 50, 'effective_blocks': ['wood', 'leaves', 'log', 'crafting_table']},
    'iron_sword':     {'texture': 'assets/textures/items/iron_sword',    'type': 'weapon', 'damage': 40, 'effective_blocks': []}, # 4 Kalp Hasarı
    # Diamond Tools
    'diamond_pickaxe': {'texture': 'assets/textures/items/diamond_pickaxe', 'type': 'tool', 'damage': 40, 'effective_blocks': ['stone', 'coal_ore', 'iron_ore', 'diamond_ore']},
    'diamond_shovel':  {'texture': 'assets/textures/items/diamond_shovel',  'type': 'tool', 'damage': 25, 'effective_blocks': ['grass', 'dirt']},
    'diamond_axe':     {'texture': 'assets/textures/items/diamond_axe',     'type': 'tool', 'damage': 60, 'effective_blocks': ['wood', 'leaves', 'log', 'crafting_table']},
    'diamond_sword':   {'texture': 'assets/textures/items/diamond_sword',   'type': 'weapon', 'damage': 50, 'effective_blocks': []}  # 5 Kalp Hasarı
}

# Envanter için birleştirilmiş öğeler (bloklar + aletler)
items = {}
for name, data in blocks.items():
    items[name] = {'texture': data['texture'], 'type': 'block'}
for name, data in tools.items():
    items[name] = data.copy() 

# --- PREMİUM GÖRÜNÜM İÇİN ÖZEL DEĞİŞİKLİKLER ---
# Çimen envanterde 3D ikon olarak görünsün ama elde blok dokusu kalsın
if 'grass' in items:
    items['grass']['icon'] = 'assets/textures/ui/grass_icon_3d.png'

# Ara malzemeler (intermediate items)
items['stick'] = {'texture': 'assets/textures/items/stick', 'type': 'material'}

# Yemek öğeleri (food items) - 'hunger_restore' değeri ile
items['apple'] = {'texture': 'assets/textures/items/apple', 'type': 'food', 'hunger_restore': 20}
items['bread'] = {'texture': 'assets/textures/items/bread', 'type': 'food', 'hunger_restore': 30}
items['cooked_meat'] = {'texture': 'assets/textures/items/cooked_meat', 'type': 'food', 'hunger_restore': 40}
items['chicken_cooked'] = {'texture': 'assets/textures/items/chicken_cooked', 'type': 'food', 'hunger_restore': 30}
items['egg'] = {'texture': 'assets/textures/items/egg', 'type': 'throwable'}
items['wheat'] = {'texture': 'assets/textures/items/wheat', 'type': 'material'}
items['coal'] = {'texture': 'assets/textures/items/coal', 'type': 'material'}
items['iron_ingot'] = {'texture': 'assets/textures/items/iron_ingot', 'type': 'material'}
items['diamond'] = {'texture': 'assets/textures/items/diamond', 'type': 'material'}
items['wool'] = {'texture': 'assets/textures/blocks/wool', 'type': 'block'}
items['shears'] = {'texture': 'assets/textures/items/shears', 'type': 'tool', 'damage': 10, 'effective_blocks': ['leaves']}

# Madencilik mantığı için global değişkenler
mining_progress = 0
target_block = None
last_action_time = 0
current_held_item = None  # Başlangıçta el boş

# --- ENVANTER MİKTAR TAKİBİ ---
inventory_counts = {
    'pickaxe': 0,
    'shovel': 0,
    'axe': 0,
    'grass': 0,
    'dirt': 0,
    'stone': 0,
    'wood': 0,
    'log': 0,
    'leaves': 0,
    'crafting_table': 0,
    'stick': 0,
    'wooden_pickaxe': 0,
    'stone_pickaxe': 0,
    'wooden_shovel': 0,
    'wooden_axe': 0,
    'apple': 0,
    'bread': 0,
    'cooked_meat': 0,
    'chicken_cooked': 0,
    'egg': 0,
    'wheat': 0,
    'coal': 0,
    'iron_ingot': 0,
    'diamond': 0,
    'coal_ore': 0,
    'iron_ore': 0,
    'diamond_ore': 0,
    'iron_pickaxe': 0,
    'iron_shovel': 0,
    'iron_axe': 0,
    'iron_sword': 0,
    'diamond_pickaxe': 0,
    'diamond_shovel': 0,
    'diamond_axe': 0,
    'diamond_sword': 0,
    'wool': 0,
    'shears': 1
}

# Düşen itemleri takip etmek için liste
dropped_items = []

# --- OPTİMİZE EDİLMİŞ SES SİSTEMİ ---
# Ses cache'i - sesler ilk kullanımda yüklenir (lazy loading)
sound_cache = {}
audio_pool = {}  # Ses havuzu - aynı sesi tekrar kullanmak için

step_timer = 0
player_last_position = Vec3(0, 0, 0)  # Yürüme sesi için pozisyon takibi

# İnek sesleri listesi (Önceden yükle)
cow_sounds = []
for i in range(1, 10):
    try:
        s = Audio(f'assets/sounds/mob/cow/cow{i}.wav', loop=False, autoplay=False)
        cow_sounds.append(s)
    except:
        pass

# Domuz sesleri listesi
pig_sounds = []
for i in range(1, 4):
    try:
        s = Audio(f'assets/sounds/mob/pig/pig{i}.wav', loop=False, autoplay=False)
        pig_sounds.append(s)
    except:
        pass

# Koyun sesleri listesi
sheep_sounds = []
for i in range(1, 10):
    try:
        s = Audio(f'assets/sounds/mob/sheep/sheep{i}.wav', loop=False, autoplay=False)
        sheep_sounds.append(s)
    except:
        pass

# Tavuk sesleri listesi
chicken_sounds = []
for i in range(1, 8):  # chicken1.wav - chicken7.wav
    try:
        s = Audio(f'assets/sounds/mob/chicken/chicken{i}.wav', loop=False, autoplay=False)
        chicken_sounds.append(s)
    except:
        pass

if chicken_sounds:
    print(f"[SES] ✓ {len(chicken_sounds)} tavuk sesi yüklendi!")

# Atmosferik Rüzgar (Daimi çalacak) - Optimize edildi
wind_audio = None
# Not: rain.wav dosyası olmadığı için rüzgar sesi devre dışı
# İleride assets/sounds/env/rain.wav eklendiğinde aktif olacak
print("[SES] ℹ Rüzgar sesi devre dışı (rain.wav dosyası bulunamadı)")

def play_block_sound(sound_type, volume=1.0):
    """
    Türüne göre sesi cache'den yükleyip oynatır.
    
    Args:
        sound_type: 'break', 'place', 'swing', 'step', 'damage', 'eat'
        volume: Ses seviyesi (0.0 - 1.0)
    """
    # Ses dosya yolları (Düzenlenmiş klasör yapısı)
    sound_paths = {
        'break': 'assets/sounds/block/break.wav',
        'place': 'assets/sounds/block/place.wav',
        'swing': 'assets/sounds/player/swing.wav',
        'step': 'assets/sounds/player/walk.wav',
        'damage': 'assets/sounds/player/hurt.mp3',
        'eat': 'assets/sounds/player/eat.mp3'
    }
    
    # Pitch aralıkları (her ses tipi için farklı)
    pitch_ranges = {
        'break': (0.8, 1.2),
        'place': (1.2, 1.5),
        'swing': (1.8, 2.2),
        'step': (0.5, 0.7),  # Çok düşük pitch - ayak sesi efekti
        'damage': (0.9, 1.1),
        'eat': (0.9, 1.1)
    }
    
    # Geçersiz ses tipi kontrolü
    if sound_type not in sound_paths:
        print(f"[SES HATA] Bilinmeyen ses tipi '{sound_type}'")
        return
    
    # Dosya varlık kontrolü
    sound_path = sound_paths[sound_type]
    if not os.path.exists(sound_path):
        print(f"[SES HATA] Ses dosyası bulunamadı: {sound_path}")
        return
    
    try:
        # walk.wav için audio pool kullan (Optimize edildi)
        if sound_type == 'step':
            # Pool'da yoksa oluştur
            if 'step_pool' not in audio_pool:
                audio_pool['step_pool'] = []
                for _ in range(3):  # 3 adet step sesi havuzu
                    sound = Audio(sound_path, loop=False, autoplay=False, volume=volume)
                    audio_pool['step_pool'].append(sound)
            
            # Pool'dan uygun bir ses al
            for sound in audio_pool['step_pool']:
                if not sound.playing:
                    pitch_min, pitch_max = pitch_ranges[sound_type]
                    sound.pitch = random.uniform(pitch_min, pitch_max)
                    sound.volume = volume
                    sound.play()
                    return
            
            # Tüm sesler çalıyorsa ilkini kullan
            sound = audio_pool['step_pool'][0]
            pitch_min, pitch_max = pitch_ranges[sound_type]
            sound.pitch = random.uniform(pitch_min, pitch_max)
            sound.volume = volume
            sound.play()
            return
        
        # Diğer sesler için cache kullan
        # Cache'de yoksa yükle
        if sound_type not in sound_cache:
            print(f"[SES] {sound_type} yükleniyor: {sound_path}")
            sound_cache[sound_type] = Audio(
                sound_path,
                loop=False,
                autoplay=False
            )
            print(f"[SES] ✓ {sound_type} başarıyla yüklendi!")
        
        # Ses nesnesini al
        sound = sound_cache[sound_type]
        
        # Ses yüklenemediyse çık
        if sound is None:
            print(f"[SES HATA] {sound_type} sesi çalınamıyor - yüklenmemiş")
            return
        
        # Rastgele pitch ata
        pitch_min, pitch_max = pitch_ranges[sound_type]
        sound.pitch = random.uniform(pitch_min, pitch_max)
        
        # Volume ayarla
        sound.volume = volume
        
        # Sesi çal (Ursina otomatik olarak overlap'i destekler)
        sound.play()
        
        # Debug için ilk çalışmada log
        if not hasattr(play_block_sound, f'played_{sound_type}'):
            print(f"[SES] ✓ {sound_type} sesi çalındı (volume: {volume:.2f}, pitch: {sound.pitch:.2f})")
            setattr(play_block_sound, f'played_{sound_type}', True)
            
    except Exception as e:
        print(f"[SES HATA] {sound_type} çalınırken hata: {e}")

def get_break_time(block_type, held_item):
    """Blok ve tutulan alete göre gerçek kırma süresini hesapla"""
    if block_type not in blocks:
        return 0.5
    
    base_time = blocks[block_type]['base_break_time']
    
    # Kırılamaz bloklar
    if base_time < 0:
        return float('inf')
    
    preferred = blocks[block_type]['preferred_tool']
    
    # Tutulan öğenin doğru alet olup olmadığını kontrol et
    if held_item in tools:
        if preferred and preferred in held_item:
            # Alet seviyesine göre hız çarpanı ekleyelim
            multiplier = 3.0
            if 'diamond' in held_item: multiplier = 8.0
            elif 'iron' in held_item: multiplier = 5.0
            elif 'stone' in held_item: multiplier = 3.0
            
            return base_time / multiplier  
        else:
            return base_time  # Alet ama yanlış tür
    else:
        # Bir blok veya çıplak el kullanılıyor
        if preferred:
            return base_time * 1.5  # Uygun alet olmadan daha yavaş
        else:
            return base_time

# El Animasyon Sınıfı
class Hand(Entity):
    def __init__(self):
        super().__init__(
            parent=camera.ui,
            position=(0.6, -0.6),
            scale=(1, 1, 1), # Container scale 1:1
            rotation=(25, -20, 15)
        )
        self.default_pos = Vec2(0.5, -0.6)
        self.default_rot = Vec3(25, -20, 15)
        self.swinging = False
        self.swing_time = 0
        self.tool_type = 'none' # 'none', 'pickaxe', 'axe', 'shovel', 'sword', 'block'
        
        # Kol (Arm) Mesh
        self.arm_entity = Entity(
            parent=self,
            model='cube',
            texture='assets/textures/ui/hand.png',
            scale=(0.2, 0.7, 0.2),
            position=(0, -0.1, 0.1)
        )
        if self.arm_entity.texture:
            self.arm_entity.texture.filtering = 'nearest'
        
        # Eşya (Item) Mesh
        self.item_entity = Entity(
            parent=self,
            model='cube',
            scale=(0.3, 0.3, 0.3),
            position=(0, 0.2, -0.2),
            rotation=(0, 0, 0),
            visible=False
        )
        # 3D Bloklar için üst yüzey (Grass, Log vb.)
        self.item_top_entity = Entity(
            parent=self.item_entity,
            model='quad',
            rotation=(90, 0, 0),
            position=(0, 0.52, 0), # Daha güvenli ofset
            scale=(1.01, 1.01), # Çok hafif taşıralım ki kenarlar pürüzsüz olsun
            double_sided=True,
            collider=None,
            visible=False
        )

    def update_visuals(self, item_name):
        if not item_name:
            # Boş el
            self.item_entity.visible = False
            self.item_top_entity.visible = False # Üst yüzeyi de gizle
            self.arm_entity.scale = (0.2, 0.75, 0.2)
            self.arm_entity.position = (0, -0.1, 0)
            self.default_pos = Vec3(0.45, -0.6, 0)
            self.default_rot = Vec3(35, -25, 20)
        else:
            item_data = items.get(item_name, {})
            is_block = item_data.get('type') == 'block'
            
            self.item_entity.visible = True
        
            # Eldeki doku için: Eğer bloksa her zaman blok dokusunu kullan (ikonu değil)
            original_tex = blocks[item_name]['texture'] if is_block and item_name in blocks else item_data.get('texture')
            self.item_entity.texture = original_tex
            
            if self.item_entity.texture:
                self.item_entity.texture.filtering = 'nearest'
            
            self.item_top_entity.visible = False # Varsayılan olarak gizle
                
            item_type = item_data.get('type')
            is_weapon = item_type == 'weapon'
            is_tool = item_type == 'tool'
            
            # Animasyon için türü belirle
            if 'pickaxe' in item_name: self.tool_type = 'pickaxe'
            elif 'axe' in item_name and 'pickaxe' not in item_name: self.tool_type = 'axe'
            elif 'shovel' in item_name: self.tool_type = 'shovel'
            elif 'sword' in item_name: self.tool_type = 'sword'
            else: self.tool_type = 'item'
                
            if not is_block:
                # 2D Eşya (Aletler, Yemekler vb.)
                self.item_entity.model = 'quad'
                # Texture zaten yukarıda ayarlandı
                
                if self.item_entity.texture:
                    self.item_entity.texture.filtering = 'nearest'
                
                # Silahlar ve PVP Aletleri
                if is_weapon or is_tool:
                    # Ortak Pozisyon (Sapı ele oturtma) - Daha merkeze çekildi
                    self.item_entity.position = (-0.1, 0.1, -0.2)
                    
                    if is_weapon:
                        # Silah: Doku zaten döndürülmüş (\ şeklinde)
                        self.item_entity.scale = (0.5, 0.5, 1)
                        self.item_entity.rotation = (0, 0, -90)
                    else:
                        # Aletler
                        if self.tool_type == 'axe':
                             # Baltayı düzelt (Kılıç gibi)
                             self.item_entity.scale = (0.5, 0.5, 1)
                             self.item_entity.rotation = (0, 0, -45)
                        else:
                             # Diğer aletler (Kazma, Kürek) - Aynalı
                             self.item_entity.scale = (-0.5, 0.5, 1)
                             self.item_entity.rotation = (0, 0, 30)
                else:
                    # Diğerleri (Yemek, materyal vb.)
                    self.item_entity.scale = (0.35, 0.35, 1)
                    self.item_entity.position = (0, 0.2, -0.2)
                    self.item_entity.rotation = (0, 0, 0)
                    
                self.item_entity.double_sided = True # Çift taraflı görünüm
                
                # Kolu biraz daha geride ve ince yapalım
                self.arm_entity.scale = (0.15, 0.6, 0.15)
                self.arm_entity.position = (0, -0.15, 0)
                self.default_pos = Vec3(0.5, -0.6, 0)
                self.default_rot = Vec3(35, -25, 20)
            else:
                # 3D Blok
                self.tool_type = 'block'
                self.item_entity.model = 'cube'
                self.item_entity.double_sided = False
                self.item_entity.scale = (0.4, 0.4, 0.4) # Biraz daha büyük
                self.item_entity.position = (0, 0.25, -0.1)
                self.item_entity.rotation = (20, 35, 15) # Daha iyi bir perspektif
                
                # Üst yüzey mantığı
                top_tex = None
                front_tex = None
                if item_name == 'grass': top_tex = 'assets/textures/blocks/grass_top.png'
                elif item_name == 'log': top_tex = 'assets/textures/blocks/log_top.png'
                elif item_name == 'crafting_table': 
                    top_tex = 'assets/textures/blocks/crafting_table_top.png'
                    front_tex = 'assets/textures/blocks/crafting_table_front.png'
                
                if top_tex:
                    self.item_top_entity.visible = True
                    self.item_top_entity.texture = top_tex
                    self.item_top_entity.texture.filtering = 'nearest'
                    
                    # Eğer front_tex varsa, yan yüzeyi (ana küpü) buna eşleyelim (Elde ön yüzü görünüyor)
                    if front_tex:
                        self.item_entity.texture = front_tex
                    else:
                        self.item_entity.texture = item_data.get('texture')
                else:
                    self.item_top_entity.visible = False
                    self.item_entity.texture = item_data.get('texture')

                if self.item_entity.texture:
                    self.item_entity.texture.filtering = 'nearest'

                self.arm_entity.scale = (0.2, 0.7, 0.2)
                self.arm_entity.position = (0, -0.05, 0.1)
                self.default_pos = Vec3(0.5, -0.55, 0)
                self.default_rot = Vec3(25, -20, 15)

        # Hızlı seçim efekti
        self.animate_scale(Vec3(1.1, 1.1, 1.1), duration=0.05)
        invoke(self.animate_scale, Vec3(1, 1, 1), duration=0.05, delay=0.05)

        if not self.swinging:
            self.rotation = self.default_rot
            self.position = self.default_pos

    def update(self):
        # --- GELİŞMİŞ HAREKET SİSTEMİ (EĞİLME & KOŞMA & FOV) ---
        is_crouching = held_keys['left shift'] or held_keys['shift']
        is_moving_forward = held_keys['w']
        # Koşma: Ctrl basılı, ileri gidiyor ve eğilmiyor
        is_sprinting = held_keys['left control'] and is_moving_forward and not is_crouching
        
        # --- Hedef Değerler (Duruma Göre) ---
        if is_crouching:
            # Sinsice (Sneak)
            target_height = 1.35
            target_speed = 4.0
            target_fov = 80    # Odaklanma hissi (Zoom in)
            bob_freq = 6       # Yavaş sallanma
            bob_amp = 0.02     # Çok az sallanma
        elif is_sprinting:
            # Depar (Sprint)
            target_height = 2.0
            target_speed = 13.0
            target_fov = 105   # Hız hissi (Zoom out / Speed lines effect)
            bob_freq = 15      # Hızlı ve sert sallanma
            bob_amp = 0.08
        else:
            # Normal Yürüme
            target_height = 2.0
            target_speed = 8.0
            target_fov = 90
            bob_freq = 10
            bob_amp = 0.05
            
        # ZOOM (C Key) - Diğerlerini ezer ve 3. Şahıs için de çalışır
        if held_keys['c']:
            target_fov = 25 # Daha güçlü zoom (Optifine tarzı)
            
        # --- Değerleri Yumuşakça Uygula (Lerp) ---
        # Yükseklik ve Hız (Eğilme hatalarını önlemek için daha stabil lerp)
        player.height = lerp(player.height, target_height, time.dt * 12)
        player.speed = lerp(player.speed, target_speed, time.dt * 10)
        
        # Dinamik FOV (Görüş Açısı) - TÜM MODLAR İÇİN GEÇERLİ
        # camera.fov lerp global update'e taşındı (çakışma önlemek için)
        
        # --- VIEW BOBBING (Kamera ve El Sallanması) ---
        if not self.swinging:
            # Hareket ediliyor mu?
            moving = player.grounded and (held_keys['w'] or held_keys['s'] or held_keys['a'] or held_keys['d'])
            
            if moving:
                t = time.time() * bob_freq
                
                # 1. El Pozisyonu (Nefes alır gibi)
                curr_x = self.default_pos.x + math.sin(t) * (bob_amp * 0.6)
                curr_y = self.default_pos.y + math.cos(t * 0.8) * (bob_amp * 0.6)
                
                self.position = Vec3(curr_x, curr_y, 0)
                
                # 2. El Rotasyonu (Hafif yalpalama)
                self.rotation_z = self.default_rot.z + math.sin(t) * (bob_amp * 80)
                
                # 3. Kamera Hareketi (Yürüme hissi)
                # Hedef yüksekliğin üzerine sinüs dalgası ekle
                cam_y_target = player.height + math.sin(t) * (bob_amp * 0.8)
                player.camera_pivot.y = lerp(player.camera_pivot.y, cam_y_target, time.dt * 10)
                
                # Sağa sola hafif yatma
                player.camera_pivot.x = math.cos(t * 0.5) * (bob_amp * 3)
                
            else:
                # Durma Hali - Her şeyi varsayılana çek
                self.x = lerp(self.x, self.default_pos.x, time.dt * 10)
                self.y = lerp(self.y, self.default_pos.y, time.dt * 10)
                self.rotation = lerp(self.rotation, self.default_rot, time.dt * 10)
                
                # Kamerayı ana yüksekliğe resetle
                player.camera_pivot.y = lerp(player.camera_pivot.y, player.height, time.dt * 5)
                player.camera_pivot.x = lerp(player.camera_pivot.x, 0, time.dt * 5)

    def swing(self):
        """Alet türüne özgü dinamik sallama animasyonu"""
        if not self.swinging:
            self.swinging = True
            play_block_sound('swing')
            
            # --- TÜR BAZLI ANİMASYON ---
            if self.tool_type == 'pickaxe':
                # KAZMA: Dikey, sert ve kısa vuruş (Mining)
                # Ucu bloğa saplanacak şekilde dikleşmeli
                self.animate_position(
                    self.default_pos + Vec3(-0.1, -0.15, 0.4), 
                    duration=0.06, 
                    curve=curve.in_expo
                )
                self.animate_rotation(
                    self.default_rot + Vec3(70, 0, 10), 
                    duration=0.06, 
                    curve=curve.in_expo
                )
                invoke(self._swing_phase_2, delay=0.08)
                
            elif self.tool_type == 'axe':
                # BALTA: Geniş, ağır ve yana açılan vuruş (Chopping)
                self.animate_position(
                    self.default_pos + Vec3(-0.4, -0.3, 0.2), 
                    duration=0.12, # Daha yavaş (ağır hissi)
                    curve=curve.out_circ
                )
                self.animate_rotation(
                    self.default_rot + Vec3(50, -30, -60), 
                    duration=0.12, 
                    curve=curve.out_circ
                )
                invoke(self._swing_phase_2, delay=0.14)
                
            elif self.tool_type == 'shovel':
                # KÜREK: Saplama ve kaldırma (Digging)
                self.animate_position(
                    self.default_pos + Vec3(-0.1, -0.2, 0.3), 
                    duration=0.09, 
                    curve=curve.out_quad
                )
                self.animate_rotation(
                    self.default_rot + Vec3(40, 10, -5), 
                    duration=0.09, 
                    curve=curve.out_quad
                )
                invoke(self._swing_phase_2, delay=0.11)
                
            else:
                # KILIÇ/VARSAYILAN: Yatay savurma (Slash/Sweep)
                self.animate_position(
                    self.default_pos + Vec3(-0.3, -0.2, 0.1), 
                    duration=0.08, 
                    curve=curve.out_expo
                )
                self.animate_rotation(
                    self.default_rot + Vec3(60, -15, -45), 
                    duration=0.08, 
                    curve=curve.out_expo
                )
                invoke(self._swing_phase_2, delay=0.1)

    def _swing_phase_2(self):
        # Türüne özgü geri sekme (Follow-through)
        if self.tool_type == 'pickaxe':
            # Kazma: Saplandıktan sonra hafifçe geri çekilme
            self.animate_position(
                self.default_pos + Vec3(0, 0.1, 0), 
                duration=0.1, 
                curve=curve.out_back
            )
            self.animate_rotation(
                self.default_rot + Vec3(-10, 0, 0), 
                duration=0.1, 
                curve=curve.out_back
            )
            invoke(self.reset_pos, delay=0.12)
            
        elif self.tool_type == 'axe':
            # Balta: Ağırlığıyla aşağıda biraz kalıyor
            self.animate_position(
                self.default_pos + Vec3(-0.1, -0.05, 0), 
                duration=0.15, 
                curve=curve.out_quad
            )
            self.animate_rotation(
                self.default_rot + Vec3(10, -5, -10), 
                duration=0.15, 
                curve=curve.out_quad
            )
            invoke(self.reset_pos, delay=0.18)
            
        elif self.tool_type == 'shovel':
            # Kürek: Toprağı atıyormuş gibi yukarı kalkma
             self.animate_position(
                self.default_pos + Vec3(0.1, 0.1, -0.1), 
                duration=0.1, 
                curve=curve.out_quad
            )
             self.animate_rotation(
                self.default_rot + Vec3(-20, 20, 5), 
                duration=0.1, 
                curve=curve.out_quad
            )
             invoke(self.reset_pos, delay=0.12)
             
        else:
            # Standart/Kılıç: Kavisli devam
            self.animate_position(
                self.default_pos + Vec3(-0.1, 0.15, 0), 
                duration=0.12, 
                curve=curve.out_quad
            )
            self.animate_rotation(
                self.default_rot + Vec3(-20, 5, 10), 
                duration=0.12, 
                curve=curve.out_quad
            )
            invoke(self.reset_pos, delay=0.15)

    def reset_pos(self):
        # Varsayılan başlangıç noktasına yumuşak geçiş
        self.animate_position(self.default_pos, duration=0.2, curve=curve.in_out_quad)
        self.animate_rotation(self.default_rot, duration=0.2, curve=curve.in_out_quad)
        invoke(self._finish_swing, delay=0.2)
    
    def _finish_swing(self):
        self.swinging = False

# Madencilik İlerleme Çubuğu Arayüzü
class MiningProgressBar(Entity):
    def __init__(self):
        super().__init__(
            parent=camera.ui
        )
        # Arka plan çubuğu (koyu gri)
        self.bg = Entity(
            parent=self,
            model='quad',
            color=color.rgba(0, 0, 0, 180),
            scale=(0.3, 0.025),
            position=(0, 0.05),
            visible=False
        )
        
        # İlerleme dolgusu (Altın sarısından turuncuya)
        self.fill = Entity(
            parent=self.bg,
            model='quad',
            color=color.gold,
            scale=(0, 1),
            position=(-0.5, 0),
            origin=(-0.5, 0),
            z=-0.01, # BG'nin bir katman önünde kalsın (Z-fighting engelleme)
            visible=False
        )
        
        # Cila için kenarlık (Siyah saydam)
        self.border = Entity(
            parent=self.bg,
            model='quad',
            color=color.black66,
            scale=(1.05, 1.3),
            z=0.01, # BG'nin bir katman arkasında
            visible=False
        )
        
        self.max_time = 0.25  # Madencilik süresiyle eşleşmeli
        
        # Saniye göstergesi
        self.text_entity = Text(
            parent=self,
            text='',
            origin=(0, 0),
            position=(0, 0.08), # Çubuğun üstünde
            scale=1,
            color=color.white,
            visible=False
        )
        
    def update_progress(self, progress, max_time=0.25):
        """İlerleme çubuğunu sarıdan kırmızıya hatasız şekilde günceller"""
        if max_time <= 0: max_time = 0.25
        self.max_time = max_time
        
        if progress <= 0:
            self.bg.visible = False
            self.fill.visible = False
            self.border.visible = False
            self.text_entity.visible = False
            return

        self.bg.visible = True
        self.fill.visible = True
        self.border.visible = True
        self.text_entity.visible = True
        
        # Yüzdeyi hesapla (0.0 - 1.0)
        percentage = min(progress / max_time, 1.0)
        self.fill.scale_x = percentage
        
        # SARI (1, 0.8, 0) -> TURUNCU/KIRMIZI (1, 0.2, 0)
        val = max(0.2, 0.8 - (percentage * 0.6))
        self.fill.color = color.rgb(1, val, 0)
        
        # Metni güncelle
        self.text_entity.text = f'{progress:.1f}s / {max_time:.1f}s'

# --- BLOK KIRMA GÖRSELİ ---
class BlockIndicator(Entity):
    def __init__(self):
        super().__init__(
            model='cube',
            texture='assets/textures/blocks/break/break_0.png',
            color=color.white,
            scale=1.01,
            enabled=False,
            always_on_top=False
        )
        self.target = None
        
    def show(self, pos, progress_percent):
        self.enabled = True
        self.position = Vec3(pos) + Vec3(0.5, 0.5, 0.5)
        
        # Kırma aşamasına göre dokuyu değiştir (0-9)
        stage = int(min(progress_percent * 10, 9))
        self.texture = f'assets/textures/blocks/break/break_{stage}.png'
        if self.texture:
            self.texture.filtering = 'nearest'
            
        # Sarsılma (Shake) efekti
        shake = (progress_percent ** 2) * 0.05
        self.x += random.uniform(-shake, shake)
        self.y += random.uniform(-shake, shake)
        self.z += random.uniform(-shake, shake)
        # Ölçek efekti
        self.scale = 1.01 + math.sin(time.time() * 20) * (progress_percent * 0.02)

block_indicator = BlockIndicator()

# --- SEÇİM KUTUSU (VURGULAMA) ---
class SelectionBox(Entity):
    def __init__(self):
        super().__init__(
            model='wireframe_cube',
            color=color.white,
            scale=1.05,
            enabled=False,
        )

selection_box = SelectionBox()

# --- CAN VE AÇLIK SİSTEMİ ---
class HealthBar(Entity):
    """Can Barı UI - 10 adet kalpten oluşur"""
    def __init__(self):
        super().__init__(parent=camera.ui)
        self.icons = []
        for i in range(10):
            # Arka plan (Boş Kalp)
            bg = Entity(
                parent=self,
                model='quad',
                texture='assets/textures/ui/heart_empty.png',
                scale=(0.08, 0.08), # Çok daha büyük
                position=(-0.41 + (i * 0.036), -0.33), # Çok daha sıkışık ve dengeli
                z=-0.1
            )
            if bg.texture: bg.texture.filtering = 'nearest'
            
            # Ön plan (Dolu Kalp)
            icon = Entity(
                parent=bg,
                model='quad',
                texture='assets/textures/ui/heart_icon.png',
                scale=(1, 1),
                position=(0, 0),
                z=-0.01
            )
            if icon.texture: icon.texture.filtering = 'nearest'
            self.icons.append(icon)
    
    def update_bar(self, current, maximum):
        """Can durumuna göre kalpleri göster/gizle"""
        # Her kalp 10 birim canı temsil eder
        num_full = int(math.ceil(current / 10))
        for i, icon in enumerate(self.icons):
            icon.visible = i < num_full

class HungerBar(Entity):
    """Açlık Barı UI - 10 adet yemek ikonundan oluşur"""
    def __init__(self):
        super().__init__(parent=camera.ui)
        self.icons = []
        for i in range(10):
            # Arka plan (Boş Yemek İkonu)
            bg = Entity(
                parent=self,
                model='quad',
                texture='assets/textures/ui/hunger_empty.png',
                scale=(0.08, 0.08), # Çok daha büyük
                position=(0.41 - (i * 0.036), -0.33), # Çok daha sıkışık ve dengeli
                z=-0.1
            )
            if bg.texture: bg.texture.filtering = 'nearest'
            
            # Ön plan (Dolu Yemek İkonu)
            icon = Entity(
                parent=bg,
                model='quad',
                texture='assets/textures/ui/hunger_icon.png',
                scale=(1, 1),
                position=(0, 0),
                z=-0.01
            )
            if icon.texture: icon.texture.filtering = 'nearest'
            self.icons.append(icon)
    
    def update_bar(self, current, maximum):
        """Açlık durumuna göre ikonları göster/gizle"""
        num_full = int(math.ceil(current / 10))
        for i, icon in enumerate(self.icons):
            icon.visible = i < num_full

class PlayerStats:
    """Oyuncu istatistiklerini yöneten sınıf"""
    def __init__(self):
        # Can istatistikleri
        self.max_health = 100
        self.current_health = 100
        
        # Açlık istatistikleri
        self.max_hunger = 100
        self.current_hunger = 100
        
        # Zamanlayıcılar
        self.hunger_timer = 0
        self.regen_timer = 0
        self.starvation_timer = 0
        self.stat_log_timer = 0  # Konsol log için
        
        # Düşme hasarı için
        self.last_y_position = 0
        self.is_falling = False
        self.fall_start_y = 0
        self.spawn_protection = True  # Başlangıç koruması
        self.spawn_protection_timer = 0
        
        # Hareket takibi (açlık için)
        self.movement_counter = 0
        self.last_position = Vec3(0, 0, 0)
        
        # Ölüm durumu
        self.is_dead = False
        self.death_message_shown = False
        
        # İstatistik takibi
        self.total_damage_taken = 0
        self.total_food_eaten = 0
        self.total_blocks_mined = 0
    
    def take_damage(self, amount, damage_type="Bilinmeyen"):
        """Oyuncuya hasar ver"""
        if self.is_dead or self.spawn_protection:
            return
        
        self.current_health -= amount
        self.total_damage_taken += amount
        
        # Steve Modelini Kırmızı Yap (3. Şahıs için)
        if 'player_model' in globals():
            player_model.trigger_damage_flash()
        
        # Detaylı konsol logu
        print(f'[HASAR] -{int(amount)} can | Tip: {damage_type} | Kalan Can: {int(self.current_health)}/{self.max_health}')
        
        # Ses efekti
        play_block_sound('damage')
        
        # Ekran titremesi efekti (kamera shake)
        if hasattr(camera, 'shake'):
            camera.shake(duration=0.2, magnitude=2)
            
        # Ekran kırmızılığı efekti
        if 'damage_flash' in globals():
            damage_flash.trigger()
        
        if self.current_health <= 0:
            self.current_health = 0
            self.die()
    
    def heal(self, amount):
        """Oyuncuyu iyileştir"""
        if self.is_dead:
            return
        
        old_health = self.current_health
        self.current_health = min(self.max_health, self.current_health + amount)
        healed = self.current_health - old_health
        
        if healed > 0:
            # İyileşme Partikül Efekti (Yeşil Artılar/Parıltılar)
            if 'spawn_recovery_particle' in globals():
                spawn_recovery_particle(player.position + Vec3(0, 1, 0))
            # Hafif iyileşme tınısı
            play_block_sound('place', volume=0.3)
            print(f'[İYİLEŞME] +{int(healed)} can | Can: {int(self.current_health)}/{self.max_health}')
    
    def eat_food(self, amount):
        """Yemek ye - açlığı artır"""
        if self.is_dead:
            return
        
        old_hunger = self.current_hunger
        self.current_hunger = min(self.max_hunger, self.current_hunger + amount)
        restored = self.current_hunger - old_hunger
        self.total_food_eaten += 1
        
        print(f'[YEMEK] +{int(restored)} açlık | Açlık: {int(self.current_hunger)}/{self.max_hunger} | Toplam Yenen: {self.total_food_eaten}')
    
    def die(self):
        """Oyuncu öldü"""
        self.is_dead = True
        if not self.death_message_shown:
            print('\n' + '='*60)
            print('[!] OLDUNUZ! [!]')
            print('='*60)
            print(f'Toplam Hasar Alınan: {int(self.total_damage_taken)}')
            print(f'Toplam Yemek Yenen: {self.total_food_eaten}')
            print(f'Toplam Blok Kırılan: {self.total_blocks_mined}')
            print('='*60 + '\n')
            self.death_message_shown = True
        
        # 2 saniye sonra yeniden canlan
        invoke(self.respawn, delay=2.0)
    
    def respawn(self):
        """Oyuncuyu yeniden canlandır"""
        self.current_health = self.max_health
        self.current_hunger = self.max_hunger
        self.is_dead = False
        self.death_message_shown = False
        self.spawn_protection = True  # Yeniden canlanınca koruma aktif
        self.spawn_protection_timer = 0
        
        # Güvenli başlangıç noktasına ışınla
        if hasattr(player, 'position'):
            player.position = find_safe_spawn_position()
            print(f"[RESPAWN] Güvenli pozisyonda yeniden canlandınız: {player.position}")
        
        # Karakter modelini sıfırla
        if 'player_model' in globals():
            player_model.is_dead = False
            player_model.rotation_z = 0
            player_model.y = 0 # trigger_death y'yi de düşürür
        
        print('\n' + '='*60)
        print('[!] YENIDEN CANLANDINIZ! [!]')
        print('='*60)
        print(f'Can: {int(self.current_health)}/{self.max_health}')
        print(f'Aclik: {int(self.current_hunger)}/{self.max_hunger}')
        print('[SHIELD] 3 saniye spawn korumasi aktif!')
        print('='*60 + '\n')
    
    def update(self, dt):
        """Her frame çağrılır - istatistikleri günceller"""
        if self.is_dead:
            return
        
        # Spawn koruması (3 saniye)
        if self.spawn_protection:
            self.spawn_protection_timer += dt
            if self.spawn_protection_timer >= 3.0:
                self.spawn_protection = False
                print('[SİSTEM] Spawn koruması sona erdi!')

        # --- DÜŞÜK CAN KALP ATIŞI (PREMİUM FX) ---
        if self.current_health > 0 and self.current_health < 30:
            if not hasattr(self, 'hv_timer'): self.hv_timer = 0
            self.hv_timer += dt
            # Pulse interval based on health (critical health = faster pulse)
            interval = 0.5 if self.current_health < 15 else 1.0
            if self.hv_timer >= interval:
                if 'damage_flash' in globals():
                    damage_flash.trigger(intensity=0.15)
                # Heartbeat audio could go here too
                self.hv_timer = 0
        
        # 1. Açlık Azalması - ZAMANA GÖRE (Daha Gerçekçi)
        self.hunger_timer += dt
        
        # Can az ise açlık daha hızlı azalır (stres mekanizması)
        health_percentage = self.current_health / self.max_health
        hunger_multiplier = 1.0
        
        if health_percentage < 0.3:  # Can %30'un altında
            hunger_multiplier = 2.0  # 2x daha hızlı acıkma
        elif health_percentage < 0.5:  # Can %50'nin altında
            hunger_multiplier = 1.5  # 1.5x daha hızlı acıkma
        
        # Hareket kontrolü
        if hasattr(player, 'position'):
            current_pos = player.position
            distance_moved = (current_pos - self.last_position).length()
            
            # Hareket edildiyse açlık azalt
            if distance_moved > 0.1:  # Minimum hareket eşiği
                self.movement_counter += distance_moved
                
                # Her 10 birim harekette açlık azalt (can durumuna göre çarpanla)
                if self.movement_counter >= 10:
                    hunger_loss = 0.5 * hunger_multiplier
                    self.current_hunger = max(0, self.current_hunger - hunger_loss)
                    self.movement_counter = 0
            
            self.last_position = current_pos
        
        # Zamana dayalı açlık azalması (her 10 saniyede, can durumuna göre)
        hunger_decay_interval = 10.0
        if self.hunger_timer >= hunger_decay_interval:
            hunger_loss = 1.0 * hunger_multiplier
            old_hunger = self.current_hunger
            self.current_hunger = max(0, self.current_hunger - hunger_loss)
            
            if old_hunger != self.current_hunger:
                print(f'[AÇLIK] Zaman geçtikçe açlık azaldı: -{int(hunger_loss)} (Çarpan: {hunger_multiplier}x)')
            
            self.hunger_timer = 0
        
        # 2. Can Yenilenme (Açlık %80'in üzerindeyse)
        if self.current_hunger >= self.max_hunger * 0.8:
            self.regen_timer += dt
            
            # Her 2 saniyede 1 can yenile
            if self.regen_timer >= 2.0:
                self.heal(1)
                self.regen_timer = 0
        else:
            self.regen_timer = 0
        
        # 3. Açlıktan Ölme (Açlık 0 ise)
        if self.current_hunger <= 0:
            self.starvation_timer += dt
            
            # Her saniye 2 hasar
            if self.starvation_timer >= 1.0:
                self.take_damage(2, "Açlık")
                self.starvation_timer = 0
        else:
            self.starvation_timer = 0
        
        # 4. Düşme Hasarı Kontrolü
        if hasattr(player, 'y') and hasattr(player, 'grounded'):
            current_y = player.y
            
            # Düşmeye başladı mı?
            if current_y < self.last_y_position - 0.1 and not player.grounded:
                if not self.is_falling:
                    self.is_falling = True
                    self.fall_start_y = current_y
            
            # Yere indi mi?
            if self.is_falling and player.grounded:
                fall_distance = self.fall_start_y - current_y
                
                # 5 bloktan fazla düşüşte hasar (spawn koruması yoksa)
                if fall_distance > 5 and not self.spawn_protection:
                    # Her blok için 2 hasar (5 blok sonrası)
                    damage = (fall_distance - 5) * 2
                    self.take_damage(damage, f"Düşme ({int(fall_distance)} blok)")
                elif fall_distance > 1:
                    # İniş sarsıntısı (hafif düşüşlerde bile)
                    dip = min(fall_distance * 0.1, 0.4)
                    player.camera_pivot.animate_y(2 - dip, duration=0.1, curve=curve.out_quad)
                    invoke(player.camera_pivot.animate_y, 2, duration=0.2, delay=0.1)
                
                self.is_falling = False
                self.fall_start_y = 0
            
            self.last_y_position = current_y
        
        # 5. Periyodik İstatistik Logu (Her 30 saniyede)
        self.stat_log_timer += dt
        if self.stat_log_timer >= 30.0:
            self.log_stats()
            self.stat_log_timer = 0
    
    def log_stats(self):
        """İstatistikleri konsola yazdır"""
        health_percent = (self.current_health / self.max_health) * 100
        hunger_percent = (self.current_hunger / self.max_hunger) * 100
        
        print('\n' + '-'*60)
        print('[STATS] OYUNCU ISTATISTIKLERI')
        print('-'*60)
        print(f'[HP]  Can: {int(self.current_health)}/{self.max_health} ({health_percent:.1f}%)')
        print(f'[FOOD] Aclik: {int(self.current_hunger)}/{self.max_hunger} ({hunger_percent:.1f}%)')
        print(f'[DMG] Toplam Hasar: {int(self.total_damage_taken)}')
        print(f'[EAT] Toplam Yemek: {self.total_food_eaten}')
        print(f'[MINE]  Toplam Blok: {self.total_blocks_mined}')
        
        # Durum analizi
        if health_percent < 30:
            print('[WARN]  DIKKAT: Can kritik seviyede!')
        if hunger_percent < 30:
            print('[WARN]  DIKKAT: Aclik kritik seviyede!')
        if hunger_percent >= 80:
            print('[OK] Can yenilenme aktif (Aclik %80+)')
        
        print('-'*60 + '\n')
    
    def on_block_mined(self):
        """Blok kırıldığında çağrılır"""
        self.total_blocks_mined += 1
        
        # Her 10 blokta bir bilgi ver
        if self.total_blocks_mined % 10 == 0:
            print(f'[MADENCİLİK] {self.total_blocks_mined} blok kırıldı!')

# Optimizasyon: Dünya verilerini görsel varlıklardan ayrı sakla
world_data = {}   # Blok tiplerini saklar: {(x,y,z): 'grass'}
world_voxels = {} # Not used in chunk system, keeping for reference if needed or can be removed

# --- YAPRAK ÇÜRÜME SİSTEMİ ---
# Manhattan mesafesine göre (1-4) sıralı offset listesi (Performans için önbelleklendi)
def _generate_leaf_offsets():
    offsets = []
    for d in range(1, 5):
        for dx in range(-d, d + 1):
            for dy in range(-d, d + 1):
                for dz in range(-d, d + 1):
                    if abs(dx) + abs(dy) + abs(dz) == d:
                        offsets.append((dx, dy, dz))
    return offsets

LEAF_OFFSETS = _generate_leaf_offsets()
leaves_to_decay = [] # Listemizi heapq için kullanacağız: [(target_time, x, y, z), ...]
leaves_pending_set = set() # O(1) arama için set

def is_leaf_supported(x, y, z):
    """Yaprağın yakınında (mesafe 4) odun olup olmadığını kontrol eder (Yüksek performanslı arama)"""
    for dx, dy, dz in LEAF_OFFSETS:
        if world_data.get((x + dx, y + dy, z + dz)) == 'log':
            return True
    return False

def check_for_leaf_decay(pos):
    """Belirli bir konum etrafındaki yaprakların çürümesini tetikler (O(1) kontrol)"""
    curr_t = time.time()
    x, y, z = int(pos.x), int(pos.y), int(pos.z)
    for dx in range(-1, 2):
        for dy in range(-1, 2):
            for dz in range(-1, 2):
                if dx == 0 and dy == 0 and dz == 0: continue
                nx, ny, nz = x + dx, y + dy, z + dz
                
                if (nx, ny, nz) not in leaves_pending_set and world_data.get((nx, ny, nz)) == 'leaves':
                    leaves_pending_set.add((nx, ny, nz))
                    delay = random.uniform(0.5, 3.2)
                    heapq.heappush(leaves_to_decay, (curr_t + delay, nx, ny, nz))

def spawn_leaf_decay_particle(position):
    """Yaprak çürürken süzülen premium yaprak efekti"""
    p = Entity(
        model='quad',
        texture='assets/textures/blocks/leaves.png',
        position=position + Vec3(random.uniform(-0.4, 0.4), random.uniform(-0.4, 0.4), random.uniform(-0.4, 0.4)),
        scale=random.uniform(0.1, 0.2),
        double_sided=True,
        billboard=True,
        color=color.rgb(random.uniform(0.6, 0.9), 1.0, random.uniform(0.6, 0.9))
    )
    if p.texture: p.texture.filtering = 'nearest'
    
    # Fizik: Süzülerek aşağı düşme ve yalpalanma
    duration = random.uniform(2.5, 4.5)
    sway = random.uniform(0.5, 1.5)
    p.animate_position(p.position + Vec3(random.uniform(-sway, sway), -4 - random.random(), random.uniform(-sway, sway)), 
                       duration=duration, curve=curve.linear)
    p.animate_rotation_z(random.randint(-180, 180), duration=duration)
    p.animate_color(color.clear, duration=0.5, delay=duration-0.5)
    destroy(p, delay=duration + 0.1)


def spawn_particles(position, block_type):
    # Basit parçacık patlaması
    tex = blocks[block_type]['texture']
    if not tex.endswith('.png'):
        tex += '.png'
        
    for i in range(12): # 8'den 12'ye çıkarıldı
        e = Entity(
            model='cube',
            texture=tex,
            position=position + Vec3(random.uniform(-0.4, 0.4), random.uniform(-0.4, 0.4), random.uniform(-0.4, 0.4)),
            scale=random.uniform(0.05, 0.15),
            collider=None # Parçacıklar için collider'a gerek yok, performansı artırır
        )
        if e.texture:
            e.texture.filtering = 'nearest'
            
        dest = e.position + Vec3(random.uniform(-1.5, 1.5), random.uniform(0, 2), random.uniform(-1.5, 1.5))
        e.animate('position', dest, duration=0.6, curve=curve.out_quad)
        e.animate('scale', Vec3(0,0,0), duration=0.6)
        e.animate('rotation', Vec3(random.randint(0,360), random.randint(0,360), random.randint(0,360)), duration=0.6)
        destroy(e, delay=0.7)

def spawn_recovery_particle(position):
    """Can yenilenirken çıkan yeşil artı efektleri"""
    for _ in range(5):
        p = Entity(
            model='quad',
            texture='assets/textures/ui/star.png' if os.path.exists('assets/textures/ui/star.png') else None,
            color=color.lime,
            position=position + Vec3(random.uniform(-0.5, 0.5), random.uniform(0.5, 1.5), random.uniform(-0.5, 0.5)),
            scale=0.15,
            billboard=True,
            always_on_top=True
        )
        if not p.texture: p.model = 'circle'
        p.animate_position(p.position + Vec3(0, 1, 0), duration=1.0, curve=curve.out_quad)
        p.animate_color(color.clear, duration=1.0)
        p.animate_scale(0, duration=1.0)
        destroy(p, delay=1.0)

def spawn_collect_particle(position, tint=color.white):
    """Eşya toplandığında çıkan parıltı efekti"""
    for _ in range(8):
        p = Entity(
            model='quad',
            color=tint,
            position=position,
            scale=random.uniform(0.05, 0.1),
            billboard=True
        )
        p.model = 'circle'
        dest = position + Vec3(random.uniform(-0.8, 0.8), random.uniform(-0.8, 0.8), random.uniform(-0.8, 0.8))
        p.animate_position(dest, duration=0.4, curve=curve.out_expo)
        p.animate_scale(0, duration=0.4)
        destroy(p, delay=0.5)

# --- DÜŞEN ITEM SİSTEMİ ---
class DroppedItem(Entity):
    """Blok kırıldığında düşen, toplanabilir item"""
    def __init__(self, position, item_type):
        item_info = items.get(item_type, {})
        is_block = item_info.get('type') == 'block'
        tex_path = item_info.get('texture', 'assets/textures/blocks/dirt')
        if not tex_path.endswith('.png'):
            tex_path += '.png'
        
        # 2D Eşyalar için Quad ve Billboard, Bloklar için Küp
        model_type = 'cube' if is_block else 'quad'
        
        super().__init__(
            parent=scene,
            position=position + Vec3(0, 0.3, 0),
            model=model_type,
            texture=tex_path,
            scale=0.3 if is_block else 0.4,
            color=color.white,
            collider='box'
        )
        
        # 2D öğeler her zaman oyuncuya baksın ve arkadan da görünsün
        if not is_block:
            self.billboard = True
            self.double_sided = True
            
        self.item_type = item_type
        self.spawn_time = time.time()
        self.collected = False
        
        # Başlangıç hızı (hafif yukarı ve rastgele yana)
        # Başlangıç hızı (daha az zıplama)
        self.velocity = Vec3(
            random.uniform(-1.0, 1.0),
            random.uniform(0.5, 1.0),
            random.uniform(-1.0, 1.0)
        )
        self.gravity = 5.0
        self.bob_offset = random.uniform(0, 6.28)  # Rastgele faz
        
        # Global listeye ekle
        dropped_items.append(self)
        
        # Hitbox Görseli (F3 ile açılır)
        self.hitbox_visual = Entity(
            parent=self,
            model='wireframe_cube',
            scale=(1.1, 1.1, 1.1), # Eşyadan biraz büyük
            color=color.white,
            enabled=show_hitboxes,
            always_on_top=True
        )

    
    def update(self):
        if self.collected:
            return
        
        # Yerçekimi uygula
        self.velocity.y -= self.gravity * time.dt
        
        # Pozisyon güncelle
        new_pos = self.position + self.velocity * time.dt
        
        # Zemin kontrolü
        ground_y = -10  # Varsayılan
        for check_y in range(int(new_pos.y), -15, -1):
            if (int(new_pos.x), check_y, int(new_pos.z)) in world_data:
                ground_y = check_y + 1.2
                break
        
        if new_pos.y <= ground_y:
            new_pos.y = ground_y
            self.velocity = Vec3(0, 0, 0)
        
        self.position = new_pos
        
        # Döndür ve yukarı-aşağı salınım yap
        self.rotation_y += 100 * time.dt
        if self.velocity.length() < 0.1:
            self.y = ground_y + math.sin(time.time() * 3 + self.bob_offset) * 0.1
        
        # Oyuncuya yakınlık kontrolü (1.5 birim)
        if hasattr(self, 'check_pickup') == False:
            self.check_pickup = True
        
        dist = (self.position - player.position).length()
        if dist < 2.5 and time.time() - self.spawn_time > 0.5:  # Menzili artırdık (2.5)
            self.collect()
    
    def collect(self):
        if self.collected:
            return
        self.collected = True
        
        # Envantere ekle
        if inventory:
            inventory.add_item(self.item_type, 1)
        
        # Premium Toplama Efekti (Altın Parıltılar)
        if 'spawn_collect_particle' in globals():
            spawn_collect_particle(self.position, tint=color.yellow)
            
        # Toplama animasyonu
        self.animate_scale(0, duration=0.15)
        self.animate_position(player.position + Vec3(0, 1, 0), duration=0.15)
        
        # Toplama sesi (ince 'pıt')
        play_block_sound('place', volume=0.5)
        
        # Listeden ve sahneden kaldır
        if self in dropped_items:
            dropped_items.remove(self)
        destroy(self, delay=0.18)

def spawn_dropped_item(position, item_type):
    """Belirtilen konumda düşen item oluştur"""
    return DroppedItem(position, item_type)

# --- FIRLATILAN YUMURTA SİSTEMİ ---
class ThrownEgg(Entity):
    """Fırlatılan yumurta - düşük ihtimalle tavuk çıkarır"""
    def __init__(self, position, direction):
        super().__init__(
            parent=scene,
            position=position,
            model='sphere',
            texture='assets/textures/items/egg.png',
            scale=0.25,
            collider='sphere'
        )
        
        if self.texture:
            self.texture.filtering = 'nearest'
        
        self.velocity = direction * 20  # Fırlatma hızı
        self.gravity = 25.0  # Yerçekimi
        self.lifetime = 0
        self.max_lifetime = 10  # 10 saniye sonra yok ol
        self.has_broken = False  # Sadece bir kez kırılsın
        
        # İz efekti için zamanlayıcı
        self.trail_timer = 0
        self.trail_interval = 0.05  # Her 0.05 saniyede bir iz bırak
        
    def update(self):
        if self.has_broken:
            return
            
        dt = time.dt
        self.lifetime += dt
        self.trail_timer += dt
        
        # İz efekti
        if self.trail_timer >= self.trail_interval:
            self.create_trail()
            self.trail_timer = 0
        
        # Maksimum ömür kontrolü
        if self.lifetime > self.max_lifetime:
            self.break_egg()
            return
        
        # Yerçekimi
        self.velocity.y -= self.gravity * dt
        
        # Hareket
        next_pos = self.position + self.velocity * dt
        
        # Çarpışma kontrolü
        hit = False
        hit_pos = next_pos
        
        # 1. Blok çarpışma kontrolü (duvar/tavan)
        bx, by, bz = int(next_pos.x), int(next_pos.y), int(next_pos.z)
        if (bx, by, bz) in world_data:
            hit = True
            hit_pos = Vec3(bx + 0.5, by + 0.5, bz + 0.5)
        
        # 2. Zemin kontrolü (aşağıdan yukarı tara)
        ground_y = -15
        for check_y in range(int(next_pos.y), -16, -1):
            check_x, check_z = int(next_pos.x), int(next_pos.z)
            if (check_x, check_y, check_z) in world_data:
                ground_y = check_y + 1
                if next_pos.y <= ground_y + 0.1:  # Zemine çok yakınsa
                    hit = True
                    hit_pos = Vec3(next_pos.x, ground_y, next_pos.z)
                break
        
        # Pozisyonu güncelle
        if not hit:
            self.position = next_pos
            self.rotation_y += 500 * dt  # Döndür
        else:
            # Çarpışma noktasında kır
            self.position = hit_pos
            self.break_egg()
    
    def create_trail(self):
        """Yumurta izi oluştur"""
        trail = Entity(
            model='sphere',
            color=color.rgba(255, 255, 255, 150),
            position=self.position,
            scale=0.15
        )
        trail.animate_scale(0, duration=0.3)
        trail.animate_color(color.clear, duration=0.3)
        destroy(trail, delay=0.3)
    
    def break_egg(self):
        """Yumurta kırılır - düşük ihtimalle tavuk çıkar"""
        if self.has_broken:
            return
        
        self.has_broken = True
        
        # Kırılma sesi
        play_block_sound('break', volume=0.4)
        
        # Kırılma efekti (beyaz parçacıklar + sarı yumurta içi)
        for i in range(12):
            # Beyaz kabuk parçaları
            if i < 8:
                p = Entity(
                    model='cube',
                    color=color.white,
                    position=self.position + Vec3(random.uniform(-0.3, 0.3), random.uniform(-0.3, 0.3), random.uniform(-0.3, 0.3)),
                    scale=random.uniform(0.05, 0.12)
                )
            # Sarı yumurta içi
            else:
                p = Entity(
                    model='sphere',
                    color=color.yellow,
                    position=self.position + Vec3(random.uniform(-0.2, 0.2), random.uniform(-0.2, 0.2), random.uniform(-0.2, 0.2)),
                    scale=random.uniform(0.08, 0.15)
                )
            
            dest = p.position + Vec3(random.uniform(-1, 1), random.uniform(0, 1.5), random.uniform(-1, 1))
            p.animate_position(dest, duration=0.5, curve=curve.out_quad)
            p.animate_scale(0, duration=0.5)
            destroy(p, delay=0.6)
        
        # Zemin lekesi efekti
        splat = Entity(
            model='quad',
            color=color.rgba(255, 255, 200, 150),
            position=self.position + Vec3(0, 0.01, 0),
            rotation_x=90,
            scale=0.5
        )
        splat.animate_scale(0, duration=2.0)
        splat.animate_color(color.clear, duration=2.0)
        destroy(splat, delay=2.0)
        
        # Tavuk spawn sistemi (geliştirilmiş)
        CHICKEN_SPAWN_CHANCE = 0.125  # %12.5 (Minecraft default)
        
        if random.random() < CHICKEN_SPAWN_CHANCE:
            # Çoklu tavuk spawn şansı (çok düşük)
            num_chickens = 1
            if random.random() < 0.03:  # %3 şans
                num_chickens = 4  # 4 tavuk birden!
            
            # Tavukları spawn et
            for i in range(num_chickens):
                offset = Vec3(random.uniform(-0.5, 0.5), 0, random.uniform(-0.5, 0.5))
                new_chicken = Chicken(self.position + offset)
                
                # İlk tavuk için spawn efekti
                if i == 0:
                    for _ in range(15):
                        p = Entity(
                            model='quad',
                            color=color.white,
                            position=self.position + Vec3(random.uniform(-0.5, 0.5), random.uniform(0, 1), random.uniform(-0.5, 0.5)),
                            scale=0.15,
                            billboard=True
                        )
                        p.animate_position(p.position + Vec3(0, 1, 0), duration=0.8)
                        p.animate_scale(0, duration=0.8)
                        destroy(p, delay=0.8)
            
            # Ses efekti
            if chicken_sounds:
                random.choice(chicken_sounds).play()
        
        # Yumurtayı yok et
        destroy(self)

def throw_egg():
    """Oyuncu yumurta fırlatır - mouse'un işaret ettiği noktaya"""
    # Fırlatma pozisyonu (oyuncunun önü)
    throw_pos = player.position + Vec3(0, 1.5, 0)
    
    # Hedef belirleme - raycast ile mouse'un baktığı noktayı bul
    ray = raycast(camera.world_position, camera.forward, distance=100, ignore=(player,))
    
    if ray.hit:
        # Bir şeye bakıyorsa o noktaya fırlat
        target_point = ray.world_point
    else:
        # Hiçbir şeye bakmıyorsa kamera yönünde uzak bir nokta
        target_point = camera.world_position + camera.forward * 50
    
    # Fırlatma yönü (hedef noktaya doğru)
    throw_dir = (target_point - throw_pos).normalized()
    
    # Yumurta oluştur
    egg = ThrownEgg(throw_pos, throw_dir)
    
    # Fırlatma sesi
    play_block_sound('swing', volume=0.6)
    
    print("[YUMURTA] Fırlatıldı!")

# --- YEMEK YEME ANİMASYONU ---
def start_eating_animation(food_item):
    """Yemek yeme animasyonu - el hareketi (Minecraft tarzı basılı tutma)"""
    if 'hand_entity' not in globals() or not hand_entity:
        return
    
    # Orijinal pozisyon ve rotasyon
    original_pos = Vec3(0.35, -0.25, 0.5)
    original_rot = Vec3(0, 0, 0)
    
    # Yemek yeme pozisyonu (ağza yakın)
    eating_pos = Vec3(0.15, -0.15, -0.25)
    eating_rot = Vec3(50, -35, 30)
    
    # Tekrarlayan animasyon (1.5 saniye boyunca)
    def eating_loop():
        if not hasattr(update, 'eating') or not update.eating:
            # Yemek yeme bittiyse orijinal pozisyona dön
            hand_entity.animate_position(original_pos, duration=0.2, curve=curve.in_out_quad)
            hand_entity.animate_rotation(original_rot, duration=0.2, curve=curve.in_out_quad)
            return
        
        # Ağza götür
        hand_entity.animate_position(eating_pos, duration=0.25, curve=curve.in_out_quad)
        hand_entity.animate_rotation(eating_rot, duration=0.25, curve=curve.in_out_quad)
        
        # Geri çek
        invoke(lambda: hand_entity.animate_position(
            original_pos + Vec3(0, -0.05, 0.1), 
            duration=0.25, 
            curve=curve.in_out_quad
        ), delay=0.25)
        invoke(lambda: hand_entity.animate_rotation(
            Vec3(10, -5, 5), 
            duration=0.25, 
            curve=curve.in_out_quad
        ), delay=0.25)
        
        # Tekrar et
        invoke(eating_loop, delay=0.5)
    
    # Animasyonu başlat
    eating_loop()
    
    # İlk parçacık efekti
    invoke(lambda: create_eating_particles(food_item), delay=0.3)

def create_eating_particles(food_item):
    """Yemek yeme parçacık efekti - geliştirilmiş"""
    # Kamera kontrolü
    if not camera:
        return
    
    # Yemek yeme devam etmiyorsa parçacık oluşturma
    if not hasattr(update, 'eating') or not update.eating:
        return
    
    # Yemek rengini belirle
    food_colors = {
        'apple': color.red,
        'bread': color.rgb(210, 180, 140),
        'cooked_meat': color.rgb(139, 69, 19),
        'chicken_cooked': color.rgb(205, 133, 63),
        'wheat': color.yellow,
        'egg': color.white
    }
    
    food_color = food_colors.get(food_item, color.white)
    
    # Ağız pozisyonu (kamera önü - biraz daha yakın)
    mouth_pos = camera.world_position + camera.forward * 0.4 + Vec3(0, -0.15, 0)
    
    # Parçacıklar (yemek kırıntıları) - daha az ama daha görünür
    for _ in range(3):
        p = Entity(
            model='cube',
            color=food_color,
            position=mouth_pos + Vec3(
                random.uniform(-0.08, 0.08),
                random.uniform(-0.05, 0.05),
                random.uniform(-0.08, 0.08)
            ),
            scale=random.uniform(0.04, 0.1)
        )
        
        # Rastgele yöne saçılma (aşağı doğru)
        dest = p.position + Vec3(
            random.uniform(-0.4, 0.4),
            random.uniform(-0.6, -0.2),
            random.uniform(-0.4, 0.4)
        )
        
        p.animate_position(dest, duration=0.4, curve=curve.out_quad)
        p.animate_scale(0, duration=0.4)
        p.animate_rotation(
            Vec3(random.randint(0, 360), random.randint(0, 360), random.randint(0, 360)),
            duration=0.4
        )
        destroy(p, delay=0.4)

# --- STABİL VE TEMİZ HAYVAN SİSTEMİ (FACE OVERLAY DESTEKLİ) ---
animals = []
show_hitboxes = False # Hitbox görünürlüğü kontrolü

class MinecraftModel(Entity):
    """
    Çok parçalı karakterler için standart Minecraft model oluşturucu.
    64x32 skin haritalamayı destekler.
    """
    def __init__(self, texture_path, texture_size=(64, 32), **kwargs):
        super().__init__(**kwargs)
        self.texture_path = texture_path
        self.parts = {}
        self.tex_w, self.tex_h = float(texture_size[0]), float(texture_size[1])

    def add_part(self, name, size, position, uv_origin, parent=None):
        """Creates a part with proper Minecraft UV mapping for all 6 faces."""
        w, h, d = size
        ux, uy = uv_origin
        tw, th = self.tex_w, self.tex_h

        def get_uvs(x, y, width, height):
            u_min = x / tw
            u_max = (x + width) / tw
            v_min = 1.0 - (y + height) / th
            v_max = 1.0 - y / th
            return (u_min, v_min, u_max, v_max)

        verts = []
        uvs = []
        sw, sh, sd = w/16, h/16, d/16
        hw, hh, hd = sw/2, sh/2, sd/2

        uv = get_uvs(ux + d, uy + d, w, h)
        verts.extend([(-hw, -hh, hd), (hw, -hh, hd), (hw, hh, hd), (-hw, hh, hd)])
        uvs.extend([(uv[0], uv[1]), (uv[2], uv[1]), (uv[2], uv[3]), (uv[0], uv[3])])

        uv = get_uvs(ux + 2*d + w, uy + d, w, h)
        verts.extend([(hw, -hh, -hd), (-hw, -hh, -hd), (-hw, hh, -hd), (hw, hh, -hd)])
        uvs.extend([(uv[0], uv[1]), (uv[2], uv[1]), (uv[2], uv[3]), (uv[0], uv[3])])

        uv = get_uvs(ux, uy + d, d, h)
        verts.extend([(-hw, -hh, -hd), (-hw, -hh, hd), (-hw, hh, hd), (-hw, hh, -hd)])
        uvs.extend([(uv[0], uv[1]), (uv[2], uv[1]), (uv[2], uv[3]), (uv[0], uv[3])])

        uv = get_uvs(ux + d + w, uy + d, d, h)
        verts.extend([(hw, -hh, hd), (hw, -hh, -hd), (hw, hh, -hd), (hw, hh, hd)])
        uvs.extend([(uv[0], uv[1]), (uv[2], uv[1]), (uv[2], uv[3]), (uv[0], uv[3])])

        uv = get_uvs(ux + d, uy, w, d)
        verts.extend([(-hw, hh, hd), (hw, hh, hd), (hw, hh, -hd), (-hw, hh, -hd)])
        uvs.extend([(uv[0], uv[1]), (uv[2], uv[1]), (uv[2], uv[3]), (uv[0], uv[3])])

        uv = get_uvs(ux + d + w, uy, w, d)
        verts.extend([(-hw, -hh, -hd), (hw, -hh, -hd), (hw, -hh, hd), (-hw, -hh, hd)])
        uvs.extend([(uv[0], uv[1]), (uv[2], uv[1]), (uv[2], uv[3]), (uv[0], uv[3])])

        part = Entity(
            parent=parent if parent else self,
            model=Mesh(vertices=verts, uvs=uvs, triangles=[(i*4, i*4+1, i*4+2, i*4+3) for i in range(6)]),
            texture=self.texture_path,
            position=position
        )
        if part.texture: part.texture.filtering = 'nearest'
        self.parts[name] = part
        return part

    def add_cape(self, uv_origin=(0, 0)):
        """Adds a standard Minecraft cape (10x16x1)"""
        # Cape UVs are often separate or in a specific part of a larger texture
        # Assuming we use a dedicated cape texture or part of the skin
        self.cape = self.add_part('cape', (10, 16, 1), (0, 0.8, -0.15), uv_origin)
        self.cape.origin = (0, 0.5, 0.5) # Top-center hinge
        return self.cape

class BasePlayerModel(MinecraftModel):
    def __init__(self, texture_path, texture_size=(64, 32), **kwargs):
        super().__init__(texture_path=texture_path, texture_size=texture_size, **kwargs)
        self.walk_timer = 0
        self.last_pos = Vec3(0,0,0)
        self.swing_timer = 0
        self.is_swinging = False
        self.blink_timer = 0
        self.eat_timer = 0
        self.is_eating = False
        self.is_dead = False
        self.damage_flash_timer = 0
        self.current_item_name = None
        
        # Shadow
        self.shadow = Entity(
            parent=scene,
            model='circle',
            color=color.rgba(0,0,0,0.4),
            rotation_x=90,
            scale=1.2,
            add_to_scene_entities=False
        )

    def trigger_damage_flash(self):
        self.damage_flash_timer = 0.5
        
    def trigger_eat(self):
        self.is_eating = True
        self.eat_timer = 0
        
    def trigger_death(self):
        self.is_dead = True
        self.animate_rotation_z(90, duration=0.8, curve=curve.out_back)
        self.animate_y(self.y - 0.5, duration=0.5)

    def update(self):
        if self.is_dead: return
        if not self.enabled: 
            self.shadow.enabled = False
            return
        
        self.shadow.enabled = True
        dt = time.dt
        
        # 1. Kafa Takibi
        if hasattr(player, 'camera_pivot'):
            self.head.rotation_x = player.camera_pivot.rotation_x
            
        # 2. Hareket ve Hız Hesaplama
        diff = player.position - self.last_pos
        movement = Vec3(diff.x, 0, diff.z).length() / dt if dt > 0 else 0
        self.last_pos = player.position
        
        # 3. Eğilme (Sneaking) ve Koşma (Sprinting)
        is_sneaking = (held_keys['shift'] or held_keys['left shift']) and player.grounded
        is_sprinting = held_keys['left control'] and movement > 1.0 and not is_sneaking
        
        target_body_y = 0.875
        target_head_y = 1.5
        target_body_rot_x = 0
        
        if is_sneaking:
            target_body_y = 0.75
            target_head_y = 1.4
            target_body_rot_x = 15
        elif is_sprinting:
            target_body_rot_x = 10
            
        self.body.y = lerp(self.body.y, target_body_y, dt * 10)
        self.head.y = lerp(self.head.y, target_head_y, dt * 10)
        self.body.rotation_x = lerp(self.body.rotation_x, target_body_rot_x, dt * 10)
        
        # 4. Yürüme Animasyonu
        if movement > 0.5 and player.grounded:
            anim_speed = 1.5 if not is_sprinting else 2.5
            self.walk_timer += dt * movement * anim_speed
            swing_amp = 35 if not is_sprinting else 50
            swing = math.sin(self.walk_timer) * swing_amp
            
            self.l_arm.rotation_x = swing
            if not self.is_swinging and not self.is_eating:
                self.r_arm.rotation_x = -swing
            self.l_leg.rotation_x = -swing
            self.r_leg.rotation_x = swing
        else:
            self.walk_timer = 0
            self.l_arm.rotation_x = lerp(self.l_arm.rotation_x, 0, dt * 10)
            if not self.is_swinging and not self.is_eating:
                self.r_arm.rotation_x = lerp(self.r_arm.rotation_x, 0, dt * 10)
            self.l_leg.rotation_x = lerp(self.l_leg.rotation_x, 0, dt * 10)
            self.r_leg.rotation_x = lerp(self.r_leg.rotation_x, 0, dt * 10)

        # 5. Vurma (Swing) Senkronizasyonu
        if 'hand_entity' in globals() and hand_entity.swinging:
            self.is_swinging = True
            self.swing_timer += dt * 15
            self.r_arm.rotation_x = -40 + math.sin(self.swing_timer) * 60
            if self.swing_timer > math.pi:
                self.is_swinging = False
                self.swing_timer = 0
        
        # 6. Yemek Yeme Senkronizasyonu
        if self.is_eating:
            self.eat_timer += dt * 10
            self.r_arm.rotation_x = lerp(self.r_arm.rotation_x, 70, dt * 10)
            self.r_arm.rotation_z = lerp(self.r_arm.rotation_z, -20, dt * 10)
            self.head.y = target_head_y + math.sin(self.eat_timer * 2) * 0.02
            if self.eat_timer > 3:
                self.is_eating = False
                self.r_arm.rotation_z = 0

        # 7. Pelerin Fiziği
        cape_swing = math.sin(time.time() * 2) * 2
        target_cape_rot = 5 + (movement * 3) + cape_swing
        if not player.grounded: target_cape_rot += 40
        if is_sneaking: target_cape_rot += 15
        self.cape.rotation_x = lerp(self.cape.rotation_x, -target_cape_rot, dt * 5)
        
        # 8. Elindeki Eşyayı Güncelle (PREMIUM)
        new_item = inventory.get_selected_item()
        if new_item != self.current_item_name:
            self.current_item_name = new_item
            if new_item and new_item in items:
                item_data = items[new_item]
                self.hand_item.enabled = True
                self.hand_item.scale = 0
                self.hand_item.animate_scale(0.3 if item_data['type'] == 'block' else 0.6, duration=0.2, curve=curve.out_back)
                
                if item_data['type'] == 'block':
                    self.hand_item.model = 'cube'
                    self.hand_item.texture = item_data['texture']
                    self.hand_item.rotation = (20, 35, 0)
                    self.hand_item.position = (0, -0.4, 0.3)
                else:
                    self.hand_item.model = 'quad'
                    self.hand_item.texture = item_data['texture']
                    self.hand_item.rotation = (0, 0, -45)
                    self.hand_item.position = (0, -0.4, 0.4)
                if self.hand_item.texture: self.hand_item.texture.filtering = 'nearest'
            else:
                self.hand_item.enabled = False
        
        if self.hand_item.enabled:
            bob = math.sin(time.time() * 2) * 0.02
            self.hand_item.y = -0.4 + bob
            if movement > 0.1:
                self.hand_item.x = math.sin(time.time() * 10) * 0.05
                
        # 9. Göz Kırpma
        self.blink_timer -= dt
        if self.blink_timer <= 0:
            self.l_eye.visible = self.r_eye.visible = False
            if self.blink_timer <= -0.1:
                self.blink_timer = random.uniform(2, 6)
                self.l_eye.visible = self.r_eye.visible = True

        # 10. Hasar Flash
        if self.damage_flash_timer > 0:
            self.damage_flash_timer -= dt
            t = clamp(self.damage_flash_timer * 2, 0, 1)
            tint = color.rgb(1, lerp(1, 0, t), lerp(1, 0, t))
            for part in self.parts.values(): part.color = tint
        else:
            for part in self.parts.values(): part.color = color.white

        # 11. Gölge Takibi
        self.shadow.position = player.position + Vec3(0, 0.02, 0)
        ground_dist = player.y - 0 
        self.shadow.scale = max(0.2, 1.2 - (ground_dist * 0.1))
        self.shadow.color = color.rgba(0,0,0, max(0, 0.4 - (ground_dist * 0.05)))

class SteveModel(BasePlayerModel):
    def __init__(self, **kwargs):
        super().__init__(texture_path='assets/skins/steve.png', **kwargs)
        self.rotation_y = 180
        self.head = self.add_part('head', (8, 8, 8), (0, 1.5, 0), (0, 0))
        self.body = self.add_part('body', (8, 12, 4), (0, 0.875, 0), (16, 16))
        self.l_arm = self.add_part('l_arm', (4, 12, 4), (-0.375, 0.875, 0), (40, 16))
        self.r_arm = self.add_part('r_arm', (4, 12, 4), (0.375, 0.875, 0), (40, 16))
        self.l_leg = self.add_part('l_leg', (4, 12, 4), (-0.125, 0.375, 0), (0, 16))
        self.r_leg = self.add_part('r_leg', (4, 12, 4), (0.125, 0.375, 0), (0, 16))
        self.add_cape((0, 0))
        self.cape.color = color.red
        self.hand_item = Entity(parent=self.r_arm, position=(0, -0.4, 0.4), scale=0.5)
        self.l_eye = Entity(parent=self.head, model='quad', color=color.blue, scale=(0.1, 0.05), position=(-0.15, 0.05, 0.51))
        self.r_eye = Entity(parent=self.head, model='quad', color=color.blue, scale=(0.1, 0.05), position=(0.15, 0.05, 0.51))

class AlexModel(BasePlayerModel):
    def __init__(self, **kwargs):
        super().__init__(texture_path='assets/skins/alex.png', texture_size=(64, 64), **kwargs)
        self.rotation_y = 180
        self.head = self.add_part('head', (8, 8, 8), (0, 1.5, 0), (0, 0))
        self.body = self.add_part('body', (8, 12, 4), (0, 0.875, 0), (16, 16))
        self.r_arm = self.add_part('r_arm', (3, 12, 4), (0.34375, 0.875, 0), (40, 16))
        self.l_arm = self.add_part('l_arm', (3, 12, 4), (-0.34375, 0.875, 0), (32, 48))
        self.r_leg = self.add_part('r_leg', (4, 12, 4), (0.125, 0.375, 0), (0, 16))
        self.l_leg = self.add_part('l_leg', (4, 12, 4), (-0.125, 0.375, 0), (16, 48))
        self.add_cape((0, 0))
        self.cape.color = color.orange
        self.hand_item = Entity(parent=self.r_arm, position=(0, -0.4, 0.4), scale=0.5)
        self.l_eye = Entity(parent=self.head, model='quad', color=color.green, scale=(0.1, 0.05), position=(-0.15, 0.05, 0.51))
        self.r_eye = Entity(parent=self.head, model='quad', color=color.green, scale=(0.1, 0.05), position=(0.15, 0.05, 0.51))

class Animal(Entity):
    def __init__(self, position, texture_path, animal_type, food_drop):
        super().__init__(
            parent=scene,
            position=position,
            scale=1.0,
            collider='box'
        )
        self.texture_path = texture_path
        self.animal_type = animal_type
        self.food_drop = food_drop
        self.velocity = Vec3(0, 0, 0)
        self.speed = 2.4
        self.gravity = 15.0
        self.grounded = False
        self.health = 100 # Standart 100 Sağlık (10 Kalp)
        self.is_dead = False
        self.body_parts = []
        self.head = None
        self.legs = []
        
        # YZ Durumları: 'idle' (bekleme), 'walking' (yürüme), 'fleeing' (kaçma), 'following' (takip), 'love' (çiftleşme), 'eating' (yemek)
        self.state = 'idle'
        self.state_timer = 0
        self.walk_direction = Vec3(0, 0, 0)
        self.push_velocity = Vec3(0, 0, 0)
        self.flee_timer = 0
        self.love_timer = 0
        
        # Ses Zamanlayıcısı (Rastgele sesler için)
        self.sound_timer = random.uniform(10, 30)
        
        # Gölge Sistemi (Fake Blob Shadow)
        self.shadow = Entity(
            parent=scene,
            model='quad',
            color=color.rgba(0,0,0,0.4),
            rotation_x=90,
            scale=1.2,
            add_to_scene_entities=False
        )
        
        # Growth System
        self.is_baby = False
        self.growth_timer = 0
        self.max_growth_time = 300 # 5 dakika (test için 60 yapılabilir)
        
        # Görsel Grup
        self.graphics = Entity(parent=self) # Görsel yapı
        self._build_anatomy() # Anatomi oluştur
        
        # Hitbox Ayarları (Varsayılan)
        self.hitbox_size = Vec3(1.2, 1.4, 1.8)
        self.hitbox_center = Vec3(0, 0.7, 0)
        self._setup_hitbox_specifics()
        
        # Collider'ı uygula
        self.collider.scale = self.hitbox_size
        self.collider.position = self.hitbox_center
        
        # UI Kurulumu
        self._setup_ui()
        
        # Hitbox Görseli (Hata ayıklama için)
        self.hitbox_visual = Entity(
            parent=self,
            model='wireframe_cube',
            scale=self.hitbox_size,
            position=self.hitbox_center,
            color=color.green, # Daha belirgin bir renk
            enabled=show_hitboxes,
            always_on_top=True
        )

        # AI Debug Yazısı
        self.debug_info = Text(
            parent=self,
            text='',
            position=(0, 2.2, 0),
            scale=6,
            color=color.yellow,
            billboard=True,
            enabled=show_hitboxes
        )
        
        animals.append(self)


    def create_part(self, scale, position, uv_offset=(0,0), uv_size=(0.5, 0.5), parent=None, color=color.white):
        """Tek bir parça oluşturur (Küp)"""
        part = Entity(
            parent=parent if parent else self.graphics,
            model='cube',
            texture=self.texture_path,
            scale=scale,
            position=position,
            color=color,
            double_sided=True,
            
        )
        if part.texture:
            part.texture.filtering = 'nearest'
            part.texture_scale = uv_size
            part.texture_offset = uv_offset
        self.body_parts.append(part)
        return part

    def create_face(self, uv_offset, uv_size):
        """Kafanın önüne yüz hatlarını ekler (Overlay)"""
        if not self.head: return
        face = Entity(
            parent=self.head,
            model='quad',
            texture=self.texture_path,
            scale=(0.95, 0.95),
            position=(0, 0.1, 0.55),
            texture_scale=uv_size,
            texture_offset=uv_offset,
            transparent=True,
            double_sided=True,
            render_queue=2,
            unlit=True
        )
        if face.texture:
            face.texture.filtering = 'nearest'
        return face

        return face


    def _play_curiosity_animation(self):
        """Oyuncuyu fark edince yapılan tatlı bir hareket"""
        if not self.head or self.is_dead: return
        
        # 1. Kafa tilting (Meraklı bakış)
        tilt = random.choice([-20, 20])
        self.head.animate_rotation_z(tilt, duration=0.3, curve=curve.out_quad)
        self.head.animate_rotation_z(0, duration=0.3, delay=0.6, curve=curve.in_quad)
        
        # 2. Küçük bir zıplama (Heyecan)
        if random.random() < 0.4:
            self.animate_y(self.y + 0.4, duration=0.15, curve=curve.out_quad)
            invoke(self.animate_y, self.y, duration=0.15, delay=0.15, curve=curve.in_quad)

    def _build_anatomy(self):
        pass

    def _setup_hitbox_specifics(self):
        """Her hayvan türü için özel hitbox ayarları"""
        pass

    def on_eat_grass(self):
        """Çimen yendiğinde tetiklenir (Koyunlarda yün çıkması için)"""
        pass

    def _setup_ui(self):
        self.ui_container = Entity(parent=self, position=(0, 1.1, 0), scale=1.2, billboard=True, enabled=False)
        self.is_baby = False
        self.growth_timer = 0
        self.health_icons = []
        
        self.health_text = Text(
            parent=self.ui_container,
            text=str(int(self.health)),
            scale=3.5,
            position=(0, 0.25, 0),
            color=color.red,
            origin=(0,0)
        )
        
        max_health = 10
        for i in range(max_health):
            icon = Entity(
                parent=self.ui_container,
                model='quad',
                texture='assets/textures/ui/heart_icon.png',
                scale=0.15,
                visible=False
            )
            if icon.texture: icon.texture.filtering = 'nearest'
            self.health_icons.append(icon)
        
        self.update_health_ui()

    def update_health_ui(self):
        active_health = max(0, int(self.health))
        if hasattr(self, 'health_text'):
            self.health_text.text = str(active_health)
        
        num_hearts = int(math.ceil(active_health / 10.0))
        spacing = 0.1
        start_x = -((num_hearts - 1) * spacing) / 2
        
        for i, icon in enumerate(self.health_icons):
            if i < num_hearts:
                icon.visible = True
                icon.position = (start_x + (i * spacing), 0, 0)
            else:
                icon.visible = False

    def update(self):
        if self.is_dead: return
        dt = time.dt
        t = time.time()
        
        # --- RASTGELE HAYVAN SESLERİ ---
        if not self.is_dead:
            self.sound_timer -= dt
            if self.sound_timer <= 0:
                # Sadece oyuncu yakınsa ses çıkar (Performans ve gürültü kontrolü)
                dist = (self.position - player.position).length()
                if dist < 25:
                    if self.animal_type == 'cow' and cow_sounds:
                        chosen_sound = random.choice(cow_sounds)
                        vol = max(0.1, 0.8 - (dist / 30))
                        chosen_sound.volume = vol
                        chosen_sound.play()
                    elif self.animal_type == 'pig' and pig_sounds:
                        chosen_sound = random.choice(pig_sounds)
                        vol = max(0.1, 0.7 - (dist / 30))
                        chosen_sound.volume = vol
                        chosen_sound.play()
                    elif self.animal_type == 'sheep' and sheep_sounds:
                        chosen_sound = random.choice(sheep_sounds)
                        vol = max(0.1, 0.7 - (dist / 30))
                        chosen_sound.volume = vol
                        chosen_sound.play()
                    elif self.animal_type == 'chicken' and chicken_sounds:
                        chosen_sound = random.choice(chicken_sounds)
                        vol = max(0.1, 0.6 - (dist / 30))
                        chosen_sound.volume = vol
                        chosen_sound.play()
                
                # Yeni rastgele süre belirle
                self.sound_timer = random.uniform(15, 45)
        
        # --- GÖLGE TAKİBİ ---
        self.shadow.enabled = not self.is_dead
        if self.shadow.enabled:
            # Zemine raycast veya basit takip
            self.shadow.position = self.position + Vec3(0, 0.02, 0)
            # Yüksekliğe göre boyut/şeffaflık ayarı (atlama vs durumları için)
            dist_to_ground = self.y - self.y # Basit ama efektif, ileride raycast eklenebilir
            self.shadow.scale = max(0.2, 1.2 - (dist_to_ground * 0.1))
            self.shadow.color = color.rgba(0,0,0, max(0, 0.4 - (dist_to_ground * 0.05)))

        # --- UI GÖRÜNÜRLÜĞÜ ---
        self.ui_container.enabled = (mouse.hovered_entity == self or (self.position - player.position).length() < 5)

        # Curiosity Animation Logic (Oyuncu yakındayken ara sıra tepki ver)
        dist_to_player = (self.position - player.position).length()
        if dist_to_player < 4 and not hasattr(self, '_curiosity_timer'):
            self._curiosity_timer = 0
            
        if dist_to_player < 4:
            self._curiosity_timer += dt
            if self._curiosity_timer > random.uniform(5, 10):
                self._play_curiosity_animation()
                self._curiosity_timer = 0

        # Growth Logic
        if self.is_baby:
            self.growth_timer += dt
            if self.growth_timer >= self.max_growth_time:
                self.is_baby = False
                self.animate_scale(1.0, duration=2.0)
                self.speed /= 1.2 # Normal hıza dön

        # AI Temelleri
        self.state_timer += dt
        dist_to_player = (self.position - player.position).length()
        held_item = inventory.get_selected_item()
        is_holding_food = held_item in ['apple', 'bread', 'wheat']

        # --- DURUM GEÇİŞLERİ ---
        if self.flee_timer > 0:
            self.state = 'fleeing'
            self.flee_timer -= dt
        elif is_holding_food and dist_to_player < 8:
            self.state = 'following'
        elif self.love_timer > 0:
            self.state = 'love'
            self.love_timer -= dt
        elif self.state in ['fleeing', 'following', 'love']:
            # Aktif koşullar bittiyse idle'a dön
            self.state = 'idle'
            self.state_timer = 0
        elif self.state == 'eating':
            if self.state_timer > 3: # 3 saniye yemek ye
                self.state = 'idle'
                self.state_timer = 0
        elif self.state == 'walking' or self.state == 'idle':
             # Rastgele yemek yeme şansı
             if self.grounded and random.random() < 0.002:
                 self.state = 'eating'
                 self.state_timer = 0
                 # Çimen yeme: Altındaki blok çimense toprağa çevir
                 bx, by, bz = int(self.x), int(self.y - 0.5), int(self.z)
                 if world_data.get((bx, by, bz)) == 'grass':
                    world_data[(bx, by, bz)] = 'dirt'
                    # Chunk'ı güncelle (Basitçe en yakın chunk'ı bul ve tetikle)
                    cx, cz = bx // chunk_size, bz // chunk_size
                    if (cx, cz) in chunks:
                        chunks[(cx, cz)].generate_mesh()
                    # Efekt
                    spawn_particles(Vec3(bx, by+1, bz), 'grass')
                    self.on_eat_grass()

        # --- İTME MEKANİZMASI (HAYVAN ÇAKIŞMASINI ÖNLEME) ---
        total_push = Vec3(0, 0, 0)
        
        # 1. Oyuncu İtmesi
        if dist_to_player < 1.2:
            push_dir = (self.position - player.position).normalized()
            push_dir.y = 0
            total_push += push_dir * (1.2 - dist_to_player) * 5.0
            
        # 2. Diğer Hayvanlarla Çakışma Kontrolü
        for other in animals:
            if other == self or other.is_dead: continue
            
            # Mesafe kontrolü (optimum mesafe 0.9 birim)
            diff = self.position - other.position
            dist = diff.length()
            
            if dist < 0.9:
                if dist < 0.05: # Tamamen üst üste binmişlerse rastgele bir yöne it
                    push_dir = Vec3(random.uniform(-1, 1), 0, random.uniform(-1, 1)).normalized()
                else:
                    push_dir = diff.normalized()
                
                push_dir.y = 0
                # Mesafe ne kadar azsa itme kuvveti o kadar artar
                total_push += push_dir * (0.9 - dist) * 3.0

        # İtme hızını yumuşak bir şekilde uygula
        self.push_velocity = lerp(self.push_velocity, total_push, dt * 10)

        # --- DURUM MANTIĞI ---
        if self.state == 'idle':
            self.walk_direction = Vec3(0, 0, 0)
            if self.state_timer > random.uniform(4, 8):
                self.state = 'walking'
                self.state_timer = 0
                angle = random.uniform(0, 360)
                self.walk_direction = Vec3(math.cos(math.radians(angle)), 0, math.sin(math.radians(angle)))
        
        elif self.state == 'walking':
            if self.state_timer > random.uniform(2, 5):
                self.state = 'idle'
                self.state_timer = 0
                self.walk_direction = Vec3(0, 0, 0)

        elif self.state == 'eating':
            self.walk_direction = Vec3(0,0,0)
            # Başı aşağı eğ
            if self.head:
                self.head.rotation_x = lerp(self.head.rotation_x, 40, dt * 5)
        
        elif self.state == 'fleeing':
            # Oyuncudan uzağa kaç
            flee_dir = (self.position - player.position).normalized()
            flee_dir.y = 0
            self.walk_direction = flee_dir
            self.speed = 4.5 # Daha hızlı koş
            
        elif self.state == 'following':
            # Oyuncuya yaklaş ama çok yaklaşma
            if dist_to_player > 2.5:
                follow_dir = (player.position - self.position).normalized()
                follow_dir.y = 0
                self.walk_direction = follow_dir
                self.speed = 3.0
            else:
                self.walk_direction = Vec3(0, 0, 0)
                
        elif self.state == 'love':
            # Diğer aşık hayvanları ara (Aynı tür)
            near_mate = False
            for other in animals:
                if other != self and other.animal_type == self.animal_type and other.state == 'love' and not self.is_baby and not other.is_baby:
                    mate_dist = (other.position - self.position).length()
                    if mate_dist < 1.0:
                        self.breed(other)
                        near_mate = True
                        break
                    elif mate_dist < 6.0:
                        love_dir = (other.position - self.position).normalized()
                        love_dir.y = 0
                        self.walk_direction = love_dir
                        self.speed = 2.0
                        near_mate = True
                        break
            
            if not near_mate:
                # Eş bulamazsa oyuncuyu takip et veya rastgele gez
                if is_holding_food and dist_to_player < 8:
                    follow_dir = (player.position - self.position).normalized()
                    follow_dir.y = 0
                    self.walk_direction = follow_dir
                else:
                    if self.state_timer > 2:
                        angle = random.uniform(0, 360)
                        self.walk_direction = Vec3(math.cos(math.radians(angle)), 0, math.sin(math.radians(angle)))
                        self.state_timer = 0

        # --- HAREKET VE ÇARPIŞMA ---
        vx, vz = 0, 0
        if self.walk_direction.length() > 0:
            # Önünde engel var mı kontrol et (ZIVLAMA / JUMPING)
            check_dist = 0.8
            ahead_pos = self.position + self.walk_direction * check_dist
            ax, ay, az = int(ahead_pos.x), int(self.y), int(ahead_pos.z)
            
            # 1 blok yüksekliğinde engel varsa ve üstü boşsa zıpla
            is_blocked = False
            if (ax, ay, az) in world_data:
                b = world_data[(ax, ay, az)]
                if not blocks.get(b, {}).get('is_passable', False):
                    is_blocked = True
            
            if is_blocked and self.grounded:
                # Üstü boş mu?
                if (ax, ay+1, az) not in world_data:
                    self.velocity.y = 6.5 # Zıpla!
            
            if not is_blocked or self.velocity.y > 0:
                vx = self.walk_direction.x * self.speed
                vz = self.walk_direction.z * self.speed
                target_rot = math.degrees(math.atan2(self.walk_direction.x, self.walk_direction.z))
                self.rotation_y = lerp(self.rotation_y, target_rot, dt * 6)

        # Hızları uygula
        tx = vx + self.push_velocity.x
        tz = vz + self.push_velocity.z

        # Yatay Çarpışma
        r = 0.35
        moved_x, moved_z = False, False
        
        # X
        if abs(tx) > 0.001:
            next_x = self.x + tx * dt
            bx = int(next_x + (r if tx > 0 else -r))
            can_move = True
            for dy in [0, 1]:
                if (bx, int(self.y + dy), int(self.z)) in world_data:
                    if not blocks.get(world_data[(bx, int(self.y + dy), int(self.z))], {}).get('is_passable', False):
                        can_move = False; break
            if can_move: self.x = next_x; moved_x = True
        
        # Z
        if abs(tz) > 0.001:
            next_z = self.z + tz * dt
            bz = int(next_z + (r if tz > 0 else -r))
            can_move = True
            for dy in [0, 1]:
                if (int(self.x), int(self.y + dy), bz) in world_data:
                    if not blocks.get(world_data[(int(self.x), int(self.y + dy), bz)], {}).get('is_passable', False):
                        can_move = False; break
            if can_move: self.z = next_z; moved_z = True

        # Fizik
        self.velocity.y -= self.gravity * dt
        self.y += self.velocity.y * dt
        
        # Zemin
        self.grounded = False
        bx, bz = int(self.x), int(self.z)
        floor_y = -15
        for y_check in range(int(self.y + 0.1), -16, -1):
            if (bx, y_check, bz) in world_data:
                b_type = world_data[(bx, y_check, bz)]
                if not blocks.get(b_type, {}).get('is_passable', False):
                    floor_y = y_check + 1.0
                    self.grounded = True; break
        
        if self.y <= floor_y:
            self.y = floor_y; self.velocity.y = 0

        # --- PREMIUM ANİMASYON SİSTEMİ ---
        is_moving = (abs(vx) > 0.1 or abs(vz) > 0.1) and self.grounded
        t = time.time()
        
        if is_moving:
            # Yürüyüş Animasyonu: Daha akıcı ayak ve gövde hareketi
            anim_speed = 14 if self.state == 'fleeing' else 9
            wave = math.sin(t * anim_speed)
            wave_fast = math.sin(t * anim_speed * 1.5)
            
            # Ayak Sallanması (Alternatif çapraz ayaklar)
            for i, leg in enumerate(self.legs):
                # 0,3 (Ön Sol, Arka Sağ) | 1,2 (Ön Sağ, Arka Sol)
                angle = 40 if self.state == 'fleeing' else 30
                leg.rotation_x = wave * angle if i in [0, 3] else -wave * angle
            
            # Gövde Sallanması (Waddle)
            self.graphics.y = abs(wave) * 0.12
            self.graphics.rotation_z = wave * 2.5 # Sağa sola hafif yatma
            self.graphics.rotation_y = wave * 1.5 # Hafif kalça sallama
            
        else:
            # Idle (Durma) Animasyonu: "Nefes Alma" ve Hafif Salınım
            idle_wave = math.sin(t * 1.5)
            self.graphics.y = lerp(self.graphics.y, idle_wave * 0.02, dt * 4)
            self.graphics.scale_y = 1.0 + (idle_wave * 0.01) # Hafif nefes alma şişmesi
            
            # Ayakları ve rotasyonu sıfırla
            for leg in self.legs:
                if self.state != 'eating':
                    leg.rotation_x = lerp(leg.rotation_x, 0, dt * 6)
            self.graphics.rotation_z = lerp(self.graphics.rotation_z, 0, dt * 6)
            self.graphics.rotation_y = lerp(self.graphics.rotation_y, 0, dt * 6)

        # Kafa Takibi ve Rastgele Bakış (Daha doğal geçişler)
        if self.head:
            if self.state == 'eating':
                # Ot yeme kafayı aşağı yukarı sallama
                eat_wave = math.sin(t * 15)
                self.head.rotation_x = lerp(self.head.rotation_x, 45 + eat_wave * 5, dt * 8)
            elif dist_to_player < 6:
                # Oyuncuya odaklanırken hafif "meraklı" kafa eğimi
                target_pos = player.position + Vec3(0, 1.5, 0)
                self.head.look_at(target_pos)
                # target_pos.y += math.sin(t * 2) * 0.2 # Hafif kafa salınımı takibi
            else:
                # Rastgele kafa hareketi (boş bakışlar)
                look_t = t * 0.6
                self.head.rotation_x = lerp(self.head.rotation_x, math.sin(look_t) * 12, dt * 1.5)
                self.head.rotation_y = lerp(self.head.rotation_y, math.cos(look_t * 0.8) * 25, dt * 1.5)
                self.head.rotation_z = lerp(self.head.rotation_z, math.sin(look_t * 0.5) * 5, dt * 1.5)
            
            self.head.rotation_x = clamp(self.head.rotation_x, -30, 50)
            self.head.rotation_y = clamp(self.head.rotation_y, -50, 50)

        # AI DEBUG INFO GÜNCELLE
        if self.debug_info.enabled:
            tx = f"State: {self.state.upper()}\n"
            tx += f"Health: {int(self.health)}/{100}\n"
            tx += f"Timer: {self.state_timer:.1f}s\n"
            if self.flee_timer > 0: tx += f"Flee: {self.flee_timer:.1f}s\n"
            if self.is_baby: tx += f"Growth: {int(self.growth_timer)}s\n"
            self.debug_info.text = tx

    def take_damage(self, amount):
        if self.is_dead: return
        self.health -= amount
        self.update_health_ui()
        self.flee_timer = 5.0 # 5 saniye boyunca kaç
        self.state = 'fleeing'
        
        # Hayvan Acı Sesi
        if self.animal_type == 'cow' and cow_sounds:
            random.choice(cow_sounds).play()
        elif self.animal_type == 'pig' and pig_sounds:
            random.choice(pig_sounds).play()
        elif self.animal_type == 'sheep' and sheep_sounds:
            random.choice(sheep_sounds).play()
        elif self.animal_type == 'chicken' and chicken_sounds:
            random.choice(chicken_sounds).play()
        
        # Hasar Numarası
        indicator = Text(
            text=f"-{int(amount)}",
            position=self.position + Vec3(random.uniform(-0.5, 0.5), 1.5, random.uniform(-0.5, 0.5)),
            scale=5, color=color.red, billboard=True
        )
        indicator.animate_position(indicator.position + Vec3(0, 1.5, 0), duration=0.8)
        indicator.animate_color(color.clear, duration=0.8)
        destroy(indicator, delay=0.8)

        for part in self.body_parts:
            part.color = color.red
            invoke(setattr, part, 'color', color.white, delay=0.1)
        
        if self.health <= 0: self.die()
        else: self.panic_nearby()

    def panic_nearby(self):
        """Yakındaki hayvanları korkutarak kaçmalarını sağlar"""
        for other in animals:
            if other != self and (other.position - self.position).length() < 8:
                other.flee_timer = 5.0
                other.state = 'fleeing'
                other.speed = 4.0

    def die(self):
        if self.is_dead: return
        self.is_dead = True
        if self in animals: animals.remove(self)
        if self.food_drop: spawn_dropped_item(self.position + Vec3(0, 0.5, 0), self.food_drop)
        
        # Ölüm Sesi
        if self.animal_type == 'cow' and cow_sounds:
            random.choice(cow_sounds).play()
        elif self.animal_type == 'pig' and pig_sounds:
            random.choice(pig_sounds).play()
        elif self.animal_type == 'sheep' and sheep_sounds:
            random.choice(sheep_sounds).play()
        elif self.animal_type == 'chicken' and chicken_sounds:
            random.choice(chicken_sounds).play()
            
        play_block_sound('damage', volume=0.8)
        
        # Kafa animasyonunu durdur (Crash önlemek için)
        if self.head:
            self.head.rotation_z = 0
            
        self.animate_scale(0, duration=0.2); destroy(self, delay=0.3)
        if hasattr(self, 'shadow'): destroy(self.shadow)

    def interact(self):
        """Yemek verildiğinde aşk durumuna geçer"""
        held_item = inventory.get_selected_item()
        if held_item in ['apple', 'bread', 'wheat']:
            if self.love_timer <= 0 and not self.is_baby:
                self.love_timer = 30.0 # 30 saniye çiftleşme modu
                inventory.use_selected_item()
                self.show_love_effects()
        else:
            # Sadece sevilme animasyonu
            self.show_love_effects(count=1)

    def show_love_effects(self, count=5):
        for _ in range(count):
            heart = Entity(
                model='quad', 
                texture='assets/textures/ui/heart_icon.png', 
                position=self.position + Vec3(random.uniform(-0.5, 0.5), 1.6, random.uniform(-0.5, 0.5)), 
                scale=0.25, 
                billboard=True
            )
            heart.animate_position(heart.position + Vec3(0, 1.5, 0), duration=1.5)
            heart.animate_scale(0, duration=1.5)
            destroy(heart, delay=1.5)

    def breed(self, partner):
        """Yeni bir yavru oluşturur"""
        self.love_timer = 0
        partner.love_timer = 0
        self.show_love_effects(count=8)
        
        # Ortalama pozisyonda yavru doğur
        spawn_pos = (self.position + partner.position) / 2
        baby = None
        if self.animal_type == 'cow':
            baby = Cow(spawn_pos)
        elif self.animal_type == 'sheep':
            baby = Sheep(spawn_pos)
        elif self.animal_type == 'pig':
            baby = Pig(spawn_pos)
        elif self.animal_type == 'chicken':
            baby = Chicken(spawn_pos)
        
        if baby:
            baby.scale = 0.5 # Yavru daha küçük
            baby.speed *= 1.2 # Yavrular daha hareketli
            baby.is_baby = True
            baby.growth_timer = 0
            baby.animate_scale(0.5, duration=0.5)
            print(f"[BREEDING] Yeni bir {self.animal_type} doğdu!")

class Cow(Animal):
    def __init__(self, pos):
        super().__init__(pos, 'assets/textures/entities/cow.png', 'cow', 'cooked_meat')

    def _setup_hitbox_specifics(self):
        # İnekler daha büyük ve uzundur
        self.hitbox_size = Vec3(1.4, 1.7, 2.2)
        self.hitbox_center = Vec3(0, 0.85, 0)

    def _build_anatomy(self):
        tex_w, tex_h = 64, 32

        def uv(x, y, w, h):
            return (x / tex_w, 1 - (y + h) / tex_h), (w / tex_w, h / tex_h)

        # BODY
        off, size = uv(20, 20, 8, 12)
        self.create_part(
            scale=(1.2, 1.0, 1.6),
            position=(0, 1.0, 0),
            uv_offset=off,
            uv_size=size
        )

        # HEAD
        off, size = uv(8, 8, 8, 8)
        self.head = self.create_part(
            scale=(0.6, 0.6, 0.6),
            position=(0, 1.6, 0.9),
            uv_offset=off,
            uv_size=size
        )

        # LEGS
        off, size = uv(4, 20, 4, 12)
        positions = [
            (-0.4, 0.6,  0.6),
            ( 0.4, 0.6,  0.6),
            (-0.4, 0.6, -0.6),
            ( 0.4, 0.6, -0.6),
        ]

        for p in positions:
            leg = self.create_part(
                scale=(0.3, 0.9, 0.3),
                position=p,
                uv_offset=off,
                uv_size=size
            )
            self.legs.append(leg)

class Sheep(Animal):
    def __init__(self, pos, is_shorn=None):
        self.is_shorn = is_shorn if is_shorn is not None else (random.random() < 0.2)
        self.wool_part = None
        self.naked_body = None
        super().__init__(pos, 'assets/textures/entities/sheep.png', 'sheep', 'cooked_meat')
        
        # Başlangıçta kırkılmışsa yünü gizle
        if self.is_shorn and self.wool_part:
            self.wool_part.enabled = False

    def _setup_hitbox_specifics(self):
        # Koyunlar orta boyuttadır
        self.hitbox_size = Vec3(1.3, 1.5, 1.8)
        self.hitbox_center = Vec3(0, 0.75, 0)

    def _build_anatomy(self):
        tex_w, tex_h = 64, 32
        def uv(x, y, w, h):
            return (x / tex_w, 1 - (y + h) / tex_h), (w / tex_w, h / tex_h)

        # 1. ÇIPLAK VÜCUT (Kırkılmış) - Artık Üst Half'ı kullanıyoruz (İnversiyon düzeltmesi)
        skin_off, skin_size = uv(0, 0, 16, 16) 
        self.naked_body = self.create_part(
            scale=(0.95, 0.85, 1.45),
            position=(0, 0.95, 0),
            uv_offset=skin_off,
            uv_size=skin_size
        )

        # 2. YÜN VÜCUT (Kaplama) - Alt Half'ı kullanıyoruz
        off, size = uv(0, 16, 16, 16)
        self.wool_part = self.create_part(
            scale=(1.3, 1.1, 1.6),
            position=(0, 0.95, 0),
            uv_offset=off,
            uv_size=size
        )

        # HEAD
        off, size = uv(16, 0, 8, 8)
        self.head = self.create_part(
            scale=(0.55, 0.55, 0.65),
            position=(0, 1.45, 0.9),
            uv_offset=off,
            uv_size=size
        )
        
        # YÜZ (FACE - Kaplama)
        off_face, size_face = uv(24, 0, 8, 8)
        self.create_face(off_face, size_face)

        # LEGS
        off, size = uv(16, 8, 4, 12)
        positions = [
            (-0.38, 0.55,  0.6),
            ( 0.38, 0.55,  0.6),
            (-0.38, 0.55, -0.6),
            ( 0.38, 0.55, -0.6),
        ]

        for p in positions:
            leg = self.create_part(
                scale=(0.26, 0.75, 0.26),
                position=p,
                uv_offset=off,
                uv_size=size
            )
            self.legs.append(leg)

    def interact(self):
        held_item = inventory.get_selected_item()
        # Bir defa kırkalım, çimen yemeden tekrar kırpılmasın
        if held_item == 'shears' and not self.is_shorn and not self.is_baby:
            self.is_shorn = True
            if self.wool_part: 
                self.wool_part.enabled = False
            
            # Blok olarak yün düşürsün (1-4 arası, yüksek sayılar daha düşük ihtimal)
            # İhtimaller: 1 (%55), 2 (%30), 3 (%10), 4 (%5)
            num_drops = random.choices([1, 2, 3, 4], weights=[55, 30, 10, 5])[0]
            for _ in range(num_drops):
                spawn_dropped_item(self.position + Vec3(0, 1, 0), 'wool')
            
            play_block_sound('break', volume=0.8)
            print(f"[SHEARING] Koyun kırkıldı, {num_drops} yün bloğu düştü!")
            return
        
        super().interact()

    def on_eat_grass(self):
        """Koyun çimen yediğinde yünü geri çıkar"""
        if self.is_shorn:
            self.is_shorn = False
            if self.wool_part: 
                self.wool_part.enabled = True
            self.show_love_effects(count=3)
            # Koyun çimen yeme sesi
            if sheep_sounds:
                random.choice(sheep_sounds).play()
            print("[SHEEP] Koyun ot yedi ve yünü geri çıktı!")

class Pig(Animal):
    def __init__(self, pos):
        super().__init__(pos, 'assets/textures/entities/pig.png', 'pig', 'cooked_meat')

    def _setup_hitbox_specifics(self):
        # Domuzlar daha alçak ve küçüktür
        self.hitbox_size = Vec3(1.0, 1.1, 1.4)
        self.hitbox_center = Vec3(0, 0.55, 0)

    def _build_anatomy(self):
        tex_w, tex_h = 64, 32
        def uv(x, y, w, h):
            return (x / tex_w, 1 - (y + h) / tex_h), (w / tex_w, h / tex_h)

        # BODY
        # off, size = uv(28, 8, 8, 12)
        self.create_part(scale=(0.9, 0.8, 1.3), position=(0, 0.8, 0), uv_offset=(0.4, 0.3), uv_size=(0.2, 0.3))

        # HEAD
        self.head = self.create_part(scale=(0.6, 0.6, 0.6), position=(0, 1.1, 0.7), uv_offset=(0, 0.7), uv_size=(0.15, 0.25))

        for p in [(-0.3, 0.4, 0.4), (0.3, 0.4, 0.4), (-0.3, 0.4, -0.4), (0.3, 0.4, -0.4)]:
            self.legs.append(self.create_part(scale=(0.3, 0.5, 0.3), position=p, uv_offset=(0, 0.4), uv_size=(0.1, 0.2)))

    def on_eat_grass(self):
        """Domuz ot yediğinde ses çıkarır"""
        if pig_sounds:
            random.choice(pig_sounds).play()

class Chicken(Animal):
    def __init__(self, pos):
        super().__init__(pos, 'assets/textures/entities/chicken.png', 'chicken', 'chicken_cooked')
        # Yumurta düşürme zamanlayıcısı
        self.egg_timer = random.uniform(15, 35)  # 15-35 saniye arası (daha sık)
        self.egg_laying_animation = False
        self.egg_animation_timer = 0
        self.can_lay_eggs = True  # Bebek tavuklar yumurta bırakmaz
        
        # Zıplama zamanlayıcısı
        self.hop_timer = random.uniform(2, 5)
        
        # Baş sallama için
        self.head_bob_offset = 0
        self.head_forward_offset = 0

    def _setup_hitbox_specifics(self):
        # Tavuklar küçük ve alçaktır
        self.hitbox_size = Vec3(0.8, 1.0, 0.8)
        self.hitbox_center = Vec3(0, 0.5, 0)

    def _build_anatomy(self):
        """Tavuk anatomisi - Minecraft tarzı UV mapping ile"""
        tex_w, tex_h = 64, 32
        
        def uv(x, y, w, h):
            return (x / tex_w, 1 - (y + h) / tex_h), (w / tex_w, h / tex_h)
        
        # Bebek tavuk için ölçek faktörü
        scale_factor = 0.5 if self.is_baby else 1.0
        
        # GÖVDE (Body) - Beyaz, yuvarlak
        off, size = uv(0, 16, 16, 16)
        self.body = self.create_part(
            scale=(0.6 * scale_factor, 0.7 * scale_factor, 0.8 * scale_factor),
            position=(0, 0.7 * scale_factor, 0),
            uv_offset=off,
            uv_size=size
        )

        # KAFA (Head) - Beyaz, küçük (bebeklerde orantısız büyük)
        head_scale = 0.4 * scale_factor * (1.3 if self.is_baby else 1.0)
        off, size = uv(0, 0, 8, 8)
        self.head = self.create_part(
            scale=(head_scale, head_scale, head_scale),
            position=(0, 1.2 * scale_factor, 0.4 * scale_factor),
            uv_offset=off,
            uv_size=size
        )
        
        # YÜZ OVERLAY (Gözler ve gaga detayları)
        off_face, size_face = uv(16, 16, 8, 8)
        self.create_face(off_face, size_face)

        # İBİK (Crest) - Kırmızı tarak
        off, size = uv(8, 0, 8, 8)
        self.crest = Entity(
            parent=self.head,
            model='cube',
            texture=self.texture_path,
            scale=(0.15, 0.25, 0.1),
            position=(0, 0.25, 0),
            double_sided=True
        )
        if self.crest.texture:
            self.crest.texture.filtering = 'nearest'
            self.crest.texture_scale = size
            self.crest.texture_offset = off

        # SAKAL (Wattle) - Kırmızı sallantılar
        off, size = uv(16, 0, 8, 8)
        self.wattle = Entity(
            parent=self.head,
            model='cube',
            texture=self.texture_path,
            scale=(0.2, 0.15, 0.1),
            position=(0, -0.15, 0.15),
            double_sided=True
        )
        if self.wattle.texture:
            self.wattle.texture.filtering = 'nearest'
            self.wattle.texture_scale = size
            self.wattle.texture_offset = off

        # BACAKLAR (Legs) - Turuncu, ince
        off, size = uv(24, 0, 8, 12)
        leg_positions = [
            (-0.2 * scale_factor, 0.35 * scale_factor, 0.1 * scale_factor),   # Sol
            (0.2 * scale_factor, 0.35 * scale_factor, 0.1 * scale_factor),    # Sağ
        ]

        for p in leg_positions:
            leg = self.create_part(
                scale=(0.15 * scale_factor, 0.5 * scale_factor, 0.15 * scale_factor),
                position=p,
                uv_offset=off,
                uv_size=size
            )
            self.legs.append(leg)

        # KANATLAR (Wings) - Beyaz, gövdenin yanlarında
        off, size = uv(32, 0, 16, 12)
        self.left_wing = Entity(
            parent=self.body,
            model='cube',
            texture=self.texture_path,
            scale=(0.1, 0.4, 0.5),
            position=(-0.35, 0, 0),
            double_sided=True
        )
        if self.left_wing.texture:
            self.left_wing.texture.filtering = 'nearest'
            self.left_wing.texture_scale = size
            self.left_wing.texture_offset = off
        
        self.right_wing = Entity(
            parent=self.body,
            model='cube',
            texture=self.texture_path,
            scale=(0.1, 0.4, 0.5),
            position=(0.35, 0, 0),
            double_sided=True
        )
        if self.right_wing.texture:
            self.right_wing.texture.filtering = 'nearest'
            self.right_wing.texture_scale = size
            self.right_wing.texture_offset = off

        # KUYRUK (Tail) - Beyaz tüyler
        off, size = uv(48, 0, 8, 8)
        self.tail = Entity(
            parent=self.body,
            model='cube',
            texture=self.texture_path,
            scale=(0.2, 0.3, 0.15),
            position=(0, 0.1, -0.45),
            double_sided=True
        )
        if self.tail.texture:
            self.tail.texture.filtering = 'nearest'
            self.tail.texture_scale = size
            self.tail.texture_offset = off
        
        # Bebek tavuklar yumurta bırakmaz
        if self.is_baby:
            self.can_lay_eggs = False

    def on_eat_grass(self):
        """Tavuk tohum yediğinde - yumurta bırakma şansı artar"""
        if chicken_sounds:
            random.choice(chicken_sounds).play()
        
        # Tohum yedikten sonra yumurta bırakma şansı artar
        if not self.is_baby and random.random() < 0.3:  # %30 şans
            self.egg_timer = min(self.egg_timer, 5)  # 5 saniye içinde yumurta
    
    def find_nearby_chickens(self):
        """Yakındaki tavukları bul (sürü davranışı için)"""
        nearby = []
        for animal in animals:
            if animal.animal_type == 'chicken' and animal != self and not animal.is_dead:
                dist = distance(self.position, animal.position)
                if dist < 5:
                    nearby.append(animal)
        return nearby
    
    def update(self):
        """Tavuk özel animasyonları - kanat çırpma, baş sallama ve yumurta düşürme"""
        super().update()  # Ana hayvan update'ini çağır
        
        if self.is_dead:
            return
        
        dt = time.dt
        
        # Performans optimizasyonu - oyuncudan çok uzaktaysa bazı işlemleri atla
        player_distance = distance(self.position, player.position)
        skip_animations = player_distance > 50
        
        # === DÜŞME HASARI SİSTEMİ (Kanat çırpma ile yavaşlama) ===
        if self.velocity.y < -5:  # Hızlı düşüyorsa
            self.velocity.y = max(self.velocity.y, -5)  # Maksimum düşme hızı sınırla
            # Hızlı kanat çırpma animasyonu (düşerken)
            if not skip_animations:
                wing_speed = 30
                wing_angle = math.sin(time.time() * wing_speed) * 35
                if hasattr(self, 'left_wing') and self.left_wing:
                    self.left_wing.rotation_z = wing_angle
                if hasattr(self, 'right_wing') and self.right_wing:
                    self.right_wing.rotation_z = -wing_angle
        
        # === RASTGELE ZIPLAMA ===
        self.hop_timer -= dt
        if self.hop_timer <= 0:
            if self.grounded and random.random() < 0.5:  # %50 şans
                self.velocity.y = 4  # Küçük zıplama
                if chicken_sounds and random.random() < 0.3:  # %30 ses şansı
                    random.choice(chicken_sounds).play()
            self.hop_timer = random.uniform(2, 5)
        
        # === YUMURTA BIRAKMA ANİMASYONU ===
        if self.egg_laying_animation:
            self.egg_animation_timer += dt
            # Çömelme animasyonu
            self.graphics.y = lerp(self.graphics.y, -0.3, dt * 10)
            
            if self.egg_animation_timer >= 1.2:
                self.egg_laying_animation = False
                self.egg_animation_timer = 0
        else:
            # Normal pozisyona dön
            if self.graphics.y < -0.05:
                self.graphics.y = lerp(self.graphics.y, 0, dt * 5)
        
        # === YUMURTA DÜŞÜRME SİSTEMİ ===
        if not self.is_baby and self.can_lay_eggs and player_distance < 50:
            self.egg_timer -= dt
            
            if self.egg_timer <= 0:
                # Yumurta düşür (artan ihtimal)
                if random.random() < 0.5:  # %50 şans (artırıldı)
                    # Yumurta bırakma animasyonu başlat
                    self.egg_laying_animation = True
                    self.state = 'idle'  # Dur
                    
                    # Yumurta düşür
                    spawn_dropped_item(self.position + Vec3(0, 0.3, 0), 'egg')
                    
                    # Tavuk sesi (yumurta bırakma)
                    if chicken_sounds:
                        random.choice(chicken_sounds).play()
                    
                    # Geliştirilmiş parçacık efekti
                    for _ in range(8):
                        p = Entity(
                            model='sphere',
                            color=color.white,
                            position=self.position + Vec3(random.uniform(-0.2, 0.2), 0.3, random.uniform(-0.2, 0.2)),
                            scale=0.08,
                            billboard=True
                        )
                        dest = p.position + Vec3(random.uniform(-0.3, 0.3), random.uniform(0.3, 0.8), random.uniform(-0.3, 0.3))
                        p.animate_position(dest, duration=0.6, curve=curve.out_quad)
                        p.animate_scale(0, duration=0.6)
                        destroy(p, delay=0.6)
                
                # Zamanlayıcıyı sıfırla (daha sık yumurta)
                self.egg_timer = random.uniform(15, 35)  # 15-35 saniye
        
        # Animasyonları atla (performans)
        if skip_animations:
            return
        
        # === KANAT ÇIRPMA ANİMASYONU ===
        t = time.time()
        
        # Yürürken daha hızlı kanat çırpma
        if self.state == 'walking' or self.state == 'fleeing':
            wing_speed = 20 if self.state == 'fleeing' else 15
            wing_angle = math.sin(t * wing_speed) * 25
        else:
            # Idle durumunda yavaş kanat çırpma
            wing_angle = math.sin(t * 3) * 10
        
        # Kanatları animasyon ile hareket ettir
        if hasattr(self, 'left_wing') and self.left_wing:
            self.left_wing.rotation_z = wing_angle
        
        if hasattr(self, 'right_wing') and self.right_wing:
            self.right_wing.rotation_z = -wing_angle
        
        # === BAŞ SALLAMA ANİMASYONU ===
        if self.state == 'walking' and self.head:
            # Yürürken baş sallama (tavuklar karakteristik)
            self.head_bob_offset = math.sin(t * 8) * 0.05
            self.head.y = (1.2 if not self.is_baby else 0.6) + self.head_bob_offset
            
            # İleri-geri baş hareketi
            self.head_forward_offset = math.sin(t * 8) * 0.1
            self.head.z = (0.4 if not self.is_baby else 0.2) + self.head_forward_offset
        else:
            # Normal pozisyona yumuşak geçiş
            if self.head:
                target_y = 1.2 if not self.is_baby else 0.6
                target_z = 0.4 if not self.is_baby else 0.2
                self.head.y = lerp(self.head.y, target_y, dt * 5)
                self.head.z = lerp(self.head.z, target_z, dt * 5)
        
        # === KUYRUK SALLAMA ===
        if hasattr(self, 'tail') and self.tail:
            tail_wag = math.sin(t * 5) * 5
            self.tail.rotation_y = tail_wag
        
        # === HAREKET HIZI (Tavuklar daha hızlı ve çevik) ===
        if not self.is_baby:
            self.speed = 3.5 if self.state != 'fleeing' else 6.5
        else:
            self.speed = 2.0 if self.state != 'fleeing' else 4.0

def spawn_animals_in_world():
    """Dünyaya hayvanları yerleştirir"""
    for _ in range(12): # İnekler
        spawn_x = random.randint(15, scale - 15)
        spawn_z = random.randint(15, scale - 15)
        # Zemin yüksekliğini bul
        ground_y = 0
        for y in range(40, -10, -1):
            if (spawn_x, y, spawn_z) in world_data:
                ground_y = y + 1; break
        Cow(Vec3(spawn_x, ground_y, spawn_z))

    for _ in range(12): # Koyunlar
        spawn_x = random.randint(15, scale - 15)
        spawn_z = random.randint(15, scale - 15)
        ground_y = 0
        for y in range(40, -10, -1):
            if (spawn_x, y, spawn_z) in world_data:
                ground_y = y + 1; break
        Sheep(Vec3(spawn_x, ground_y, spawn_z))
    
    for _ in range(12): # Domuzlar
        spawn_x = random.randint(15, scale - 15)
        spawn_z = random.randint(15, scale - 15)
        ground_y = 0
        for y in range(40, -10, -1):
            if (spawn_x, y, spawn_z) in world_data:
                ground_y = y + 1; break
        Pig(Vec3(spawn_x, ground_y, spawn_z))
    
    for _ in range(12): # Tavuklar
        spawn_x = random.randint(15, scale - 15)
        spawn_z = random.randint(15, scale - 15)
        ground_y = 0
        for y in range(40, -10, -1):
            if (spawn_x, y, spawn_z) in world_data:
                ground_y = y + 1; break
        Chicken(Vec3(spawn_x, ground_y, spawn_z))
    
    print("[HAYVANLAR] Çiftlik hayatı güçlendirildi: 48 canlı eklendi!")

# Arazi Oluşturma
noise = PerlinNoise(octaves=2, seed=random.randint(1, 10000)) # Daha az oktav = daha pürüzsüz
scale = 256 # Dünya boyutu 256x256 olarak güncellendi

def generate_tree_data(x, y, z):
    # Sadece world_data'ya yazmak için yardımcı
    # Gövde
    for i in range(1, 5):
        world_data[(x, y + i, z)] = 'log'
    
    # Yapraklar
    for lx in range(-2, 3):
        for lz in range(-2, 3):
            if abs(lx) == 2 and abs(lz) == 2: continue
            world_data[(x + lx, y + 5, z + lz)] = 'leaves'
            world_data[(x + lx, y + 6, z + lz)] = 'leaves'
            
    for lx in range(-1, 2):
        for lz in range(-1, 2):
            if abs(lx) == 1 and abs(lz) == 1: continue 
            world_data[(x + lx, y + 7, z + lz)] = 'leaves'
            
    world_data[(x, y + 8, z)] = 'leaves'

# Doku Atlası Eşleşmesi
block_uvs = {
    'grass': 5/6,  
    'stone': 4/6,
    'dirt': 3/6,
    'wood': 2/6,
    'bedrock': 1/6,
    'leaves': 0/6
}
uv_height = 1.0 / 6.0

# Chunk Sistemi
chunk_size = 16
chunks = {} # {(cx, cz): Chunk}

# Dünya hiyerarşisi (Passable blokların oyuncuya takılmaması için)
solid_world = Entity()
passable_world = Entity()

# Threading için Kuyruk (Ana iş parçacığında mesh güncellemek için)
# (chunk_ref, vertices, uvs, p_verts, p_uvs)
mesh_callback_queue = deque()

class Chunk(Entity):
    def __init__(self, cx, cz):
        super().__init__(parent=solid_world, model=Mesh(), texture='assets/textures/blocks/atlas.png', collider='mesh')
        self.cx = cx
        self.cz = cz
        self.is_generating = False
        
        # Keskin pikseller için filtreleme
        if self.texture:
            self.texture.filtering = 'nearest'
            self.texture.repeat = False
        
        # Geçilebilir bloklar (Yapraklar)
        self.passable_entity = Entity(
            parent=passable_world, 
            model=Mesh(), 
            texture='assets/textures/blocks/atlas.png', 
            collider='mesh',
            transparent=True, # Şeffaf dokular (yapraklar vs) için gerekli
            double_sided=True # Alt/İç yüzeylerin görünmesi için CRITICAL
        )
        if self.passable_entity.texture:
            self.passable_entity.texture.filtering = 'nearest'
            self.passable_entity.texture.repeat = False
            self.passable_entity.texture.repeat = False
        
        self.generate_mesh()

    def generate_mesh(self):
        if self.is_generating:
            return
        self.is_generating = True
        
        # Arka planda hesaplama yap
        t = threading.Thread(target=self.calculate_mesh_bg)
        t.start()
        
    def calculate_mesh_bg(self):
        # Mesh verilerini arka planda hesapla
        verts = []
        uvs = []
        p_verts = [] # Passable vertices
        p_uvs = []   # Passable uvs
        
        start_x = self.cx * chunk_size
        end_x = start_x + chunk_size
        start_z = self.cz * chunk_size
        end_z = start_z + chunk_size
        
        try:
            for x in range(start_x, end_x):
                for z in range(start_z, end_z):
                    for y in range(-10, 40): 
                        if (x, y, z) in world_data:
                            block = world_data[(x, y, z)]
                            # Passable kontrolü
                            is_p = blocks.get(block, {}).get('is_passable', False)
                            if is_p:
                                self.add_face_data(x, y, z, block, p_verts, p_uvs)
                            else:
                                self.add_face_data(x, y, z, block, verts, uvs)
            
            # Sonuçları kuyruğa ekle
            mesh_callback_queue.append((self, verts, uvs, p_verts, p_uvs))
            
        except Exception as e:
            print(f"Chunk Oluşturma Hatası: {e}")
            self.is_generating = False

    def assign_mesh(self, verts, uvs, p_verts, p_uvs):
        # Ana iş parçacığında çalışır
        
        # Katı bloklar
        self.model.vertices = verts
        self.model.uvs = uvs
        self.model.generate()
        self.collider = 'mesh' 
        
        # Geçilebilir bloklar
        self.passable_entity.model.vertices = p_verts
        self.passable_entity.model.uvs = p_uvs
        self.passable_entity.model.generate()
        self.passable_entity.collider = 'mesh'
        
        self.is_generating = False
    
    def on_destroy(self):
        if hasattr(self, 'passable_entity'):
            destroy(self.passable_entity)
            
    def add_face_data(self, x, y, z, block_type, verts, uvs):
        # Blok adını indeksle eşle (Atlas sırası ile AYNI olmalı)
        mapping = [
            'grass',          # 0: Side
            'grass_top',      # 1: Top
            'dirt',           # 2: Dirt
            'stone',          # 3: Stone
            'wood',           # 4: Wood planks
            'log',            # 5: Side
            'log_top',        # 6: Top
            'leaves',         # 7: Leaves
            'bedrock',        # 8: Bedrock
            'crafting_table', # 9: Crafting Table Side
            'crafting_table_top', # 10: Crafting Table Top
            'crafting_table_front', # 11: Crafting Table Front
            'coal_ore',       # 12: Coal
            'iron_ore',       # 13: Iron
            'diamond_ore',    # 14: Diamond
            'wool'            # 15: Wool
        ]
        
        uv_height = 1.0 / len(mapping) 
        
        def get_texture_idx(b_type, face_dir):
            if b_type == 'grass':
                if face_dir == 'top': return 1 
                if face_dir == 'bottom': return 2
                return 0 
            if b_type == 'log':
                if face_dir == 'top' or face_dir == 'bottom': return 6
                return 5
            if b_type == 'crafting_table':
                if face_dir == 'top': return 10
                if face_dir == 'bottom': return 4 
                # Tüm yan yüzlerde (ön, arka, sağ, sol) aletlerin olduğu dokuyu (front) kullan
                return 11 
            if b_type in mapping:
                return mapping.index(b_type)
            return 0

        padding_v = 0.005
        padding_u = 0.02
        # Yan Yüzler için genel UV hesaplama fonksiyonu
        def add_face_verts(v0, v1, v2, v3, face_dir):
            idx = get_texture_idx(block_type, face_dir)
            row = idx
            
            # V koordinatları (Y ekseni) - Atlasta yukarıdan aşağıya
            v_max = 1.0 - (row * uv_height) - padding_v
            v_min = 1.0 - ((row + 1) * uv_height) + padding_v
            
            # U koordinatları (X ekseni)
            u_min = 0.0 + padding_u
            u_max = 1.0 - padding_u
            
            uv0 = (u_min, v_max) # Top Left
            uv1 = (u_max, v_max) # Top Right
            uv2 = (u_max, v_min) # Bottom Right
            uv3 = (u_min, v_min) # Bottom Left
            
            # Triangles: (v2, v1, v0) and (v0, v3, v2)
            # v0=BL, v1=TL, v2=TR, v3=BR
            verts.extend([v2, v1, v0, v0, v3, v2])
            uvs.extend([uv1, uv0, uv3, uv3, uv2, uv1])

        def should_draw_face(nx, ny, nz):
            if (nx, ny, nz) not in world_data:
                return True
            neighbor = world_data[(nx, ny, nz)]
            self_is_p = blocks.get(block_type, {}).get('is_passable', False)
            neighbor_is_p = blocks.get(neighbor, {}).get('is_passable', False)
            if self_is_p:
                if neighbor == block_type: return False 
                return True 
            if neighbor_is_p:
                return True
            return False

        # Üst Yüz (y+1)
        if should_draw_face(x, y+1, z):
            add_face_verts((x,y+1,z+1), (x+1,y+1,z+1), (x+1,y+1,z), (x,y+1,z), 'top')
            
        # Alt Yüz (y-1)
        if should_draw_face(x, y-1, z):
            add_face_verts((x,y,z), (x+1,y,z), (x+1,y,z+1), (x,y,z+1), 'bottom')
            
        # Sağ Yüz (x+1)
        if should_draw_face(x+1, y, z):
            add_face_verts((x+1, y, z), (x+1, y+1, z), (x+1, y+1, z+1), (x+1, y, z+1), 'side')
            
        # Sol Yüz (x-1)
        if should_draw_face(x-1, y, z):
            add_face_verts((x, y, z+1), (x, y+1, z+1), (x, y+1, z), (x, y, z), 'side')
            
        # Ön Yüz (z+1)
        if should_draw_face(x, y, z+1):
            add_face_verts((x+1, y, z+1), (x+1, y+1, z+1), (x, y+1, z+1), (x, y, z+1), 'front')
            
        # Arka Yüz (z-1)
        if should_draw_face(x, y, z-1):
            add_face_verts((x, y, z), (x, y+1, z), (x+1, y+1, z), (x+1, y, z), 'back')

# Yerleştirme/Kırma Mantığını Yeniden Uygula
def update_chunk(x, z):
    cx, cz = int(x // chunk_size), int(z // chunk_size)
    if (cx, cz) in chunks:
        chunks[(cx, cz)].generate_mesh()
    # Komşuları güncelle
    if x % chunk_size == 0 and (cx-1, cz) in chunks: chunks[(cx-1, cz)].generate_mesh()
    if x % chunk_size == chunk_size-1 and (cx+1, cz) in chunks: chunks[(cx+1, cz)].generate_mesh()
    if z % chunk_size == 0 and (cx, cz-1) in chunks: chunks[(cx, cz-1)].generate_mesh()
    if z % chunk_size == chunk_size-1 and (cx, cz+1) in chunks: chunks[(cx, cz+1)].generate_mesh()

def place_block_logic(pos, block_type):
    x, y, z = int(pos.x), int(pos.y), int(pos.z)
    world_data[(x, y, z)] = block_type
    update_chunk(x, z)
    play_block_sound('place')

def break_block_logic(pos):
    x, y, z = int(pos.x), int(pos.y), int(pos.z)
    if (x,y,z) in world_data:
        block_type = world_data[(x,y,z)]  # Bloğun tipini al
        del world_data[(x,y,z)]
        update_chunk(x, z)
        play_block_sound('break')
        
        # Düşen item oluştur (doğrudan envantere ekleme)
        drop_item = block_type
        if block_type == 'coal_ore': drop_item = 'coal'
        elif block_type == 'iron_ore': drop_item = 'iron_ingot'
        elif block_type == 'diamond_ore': drop_item = 'diamond'
        
        # print(f'Eşya düşürüldü: {drop_item} Konum: {pos}')
        spawn_dropped_item(Vec3(x + 0.5, y + 0.2, z + 0.5), drop_item)
        
        # --- YAPRAK ÇÜRÜME TETİKLEME ---
        if block_type == 'log' or block_type == 'leaves':
            check_for_leaf_decay(pos)
            
        # --- ELMA DÜŞME ŞANSI (Sadece yapraklar için) ---
        if block_type == 'leaves' and random.random() < 0.10: # %10 şans
            print(f'Özel eşya (elma) düştü: {pos}')
            spawn_dropped_item(Vec3(x + 0.5, y + 0.2, z + 0.5), 'apple')

def vein_mine_logic(pos, block_type):
    """
    Geliştirilmiş Vein Miner:
    - Zincirleme reaksiyon (Chain reaction) animasyonu
    - 26-yönlü arama (Köşegen kütük desteği)
    - Mesafe bazlı sıralı kırma
    - Dinamik ses ve açlık maliyeti
    """
    start_pos = Vec3(pos)
    to_check = [start_pos]
    to_break = []
    visited = { (int(start_pos.x), int(start_pos.y), int(start_pos.z)) }
    
    # 26 yön: Bir bloğun etrafındaki 3x3x3 küp (kendisi hariç tüm komşular)
    directions = []
    for dx in [-1, 0, 1]:
        for dy in [-1, 0, 1]:
            for dz in [-1, 0, 1]:
                if dx == 0 and dy == 0 and dz == 0: continue
                directions.append(Vec3(dx, dy, dz))

    # 1. Bağlı Blokları Keşfet (Hızlı BFS)
    idx = 0
    while idx < len(to_check) and len(to_break) < 128:
        curr = to_check[idx]
        idx += 1
        
        c_tuple = (int(curr.x), int(curr.y), int(curr.z))
        if world_data.get(c_tuple) == block_type:
            to_break.append(curr)
            
            for move in directions:
                neighbor = curr + move
                n_tuple = (int(neighbor.x), int(neighbor.y), int(neighbor.z))
                if n_tuple not in visited:
                    visited.add(n_tuple)
                    to_check.append(neighbor)

    if not to_break: return

    # 2. Mesafeye göre sırala (Vurulan noktadan uzağa/yukarıya doğru kırılsın)
    to_break.sort(key=lambda p: (p - start_pos).length())

    # 3. Zincirleme Reaksiyon (Animasyonlu Kırma)
    def break_chain(index):
        if index >= len(to_break):
            print(f"[VEIN MINE] Zincirleme kırma tamamlandı: {len(to_break)} blok.")
            return

        b_pos = to_break[index]
        bx, by, bz = int(b_pos.x), int(b_pos.y), int(b_pos.z)
        
        if (bx, by, bz) in world_data:
            bt = world_data[(bx, by, bz)]
            
            # Dünyadan sil
            del world_data[(bx, by, bz)]
            
            # Efektler
            spawn_particles(Vec3(bx+0.5, by+0.5, bz+0.5), bt)
            
            # Item düşür
            drop_item = bt
            if bt == 'coal_ore': drop_item = 'coal'
            elif bt == 'iron_ore': drop_item = 'iron_ingot'
            elif bt == 'diamond_ore': drop_item = 'diamond'
            spawn_dropped_item(Vec3(bx + 0.5, by + 0.2, bz + 0.5), drop_item)
            
            # Ses (Giderek tizleşen/değişen ses efekti)
            p_val = 0.8 + (index / len(to_break)) * 0.4
            play_block_sound('break', volume=0.5)
            # Not: play_block_sound içinde rastgele pitch var zaten ama bu efekt tatlı olur
            
            # Yaprak çürümesini tetikle
            check_for_leaf_decay(b_pos)
            
            # Chunk ve Mesh güncelleme
            update_chunk(bx, bz)
            
            # Ek Açlık Maliyeti
            if 'player_stats' in globals():
                player_stats.current_hunger = max(0, player_stats.current_hunger - 0.2)

        # Bir sonraki blok için küçük gecikme (Animasyon hissi)
        next_delay = 0.04 
        invoke(break_chain, index + 1, delay=next_delay)

    # Animasyonu Başlat
    break_chain(0)

# Dünya Meshini Oluştur
def generate_world_mesh():
    print("Dünya Meshi Arka Planda Oluşturuluyor...")
    
    # Chunkları tanımla
    active_chunks = set()
    for (x,y,z) in world_data.keys():
        cx = x // chunk_size
        cz = z // chunk_size
        active_chunks.add((cx, cz))
    
    # Chunk nesnelerini oluştur (Thread içinde mesh hesaplayacaklar)
    for (cx, cz) in active_chunks:
        if (cx, cz) not in chunks:
            chunks[(cx, cz)] = Chunk(cx, cz)

# Culling (Gizleme) Mantığı
def cull_chunks():
    # Oyuncu pozisyonu
    p_pos = player.position
    p_forward = player.forward
    
    # Culling mesafesi (örneğin 3 chunk = 48 birim)
    cull_dist_sq = (chunk_size * 3) ** 2
    
    for (cx, cz), chunk in chunks.items():
        # Chunk merkezini bul (yaklaşık)
        chunk_center = Vec3(cx * chunk_size + chunk_size/2, p_pos.y, cz * chunk_size + chunk_size/2)
        
        # Mesafeyi kontrol et (Kare alma işlemi kök almaktan hızlıdır)
        dist_sq = (chunk_center.x - p_pos.x)**2 + (chunk_center.z - p_pos.z)**2
        
        if dist_sq > cull_dist_sq:
            chunk.enabled = False
        else:
            # Mesafe yakınsa, arkada mı diye bak
            # Oyuncunun çok yakınındaysa (örn 1 chunk) her zaman göster
            if dist_sq < (chunk_size * 1.5) ** 2:
                chunk.enabled = True
            else:
                # Görüş açısı kontrolü (Dot Product)
                to_chunk = (chunk_center - p_pos).normalized()
                dot = p_forward.dot(to_chunk)
                
                # Eğer dot < 0 ise arkadadır (veya yanların arkası)
                # Biraz esneklik payı bırak (-0.5 gibi) ki yan dönerken aniden kaybolmasın
                if dot < -0.4:
                     chunk.enabled = False
                     chunk.passable_entity.enabled = False
                else:
                     chunk.enabled = True
                     chunk.passable_entity.enabled = True

# Arazi Oluşturma (Katı dolguya sabitlendi)
def generate_terrain():
    print("Arazi Verileri Oluşturuluyor...")
    bottom_level = -10 # Sabit ana kaya seviyesi
    
    for z in range(scale):
        for x in range(scale):
            # Pürüzsüz arazi - Daha geniş düzlükler için frekansı düşürdük
            y = noise([x * 0.03, z * 0.03])
            surface_y = math.floor(y * 8) # Tepeleri alçalt (Amplitude 10 -> 8)
            
            # Üstte çimen
            world_data[(x, surface_y, z)] = 'grass'
            
            # Ağaç Şansı - Azaltıldı (0.015 -> 0.010)
            if random.random() < 0.010 and 2 < x < scale - 2 and 2 < z < scale - 2:
                generate_tree_data(x, surface_y, z)
            
            # Ana kayaya kadar doldur
            for depth in range(surface_y - 1, bottom_level - 1, -1):
                if depth >= surface_y - 3:
                     world_data[(x, depth, z)] = 'dirt'
                elif depth > bottom_level:
                     # Ore spawning logic
                     rand = random.random()
                     if rand < 0.03: # %3 Coal
                         world_data[(x, depth, z)] = 'coal_ore'
                     elif rand < 0.045: # %1.5 Iron
                         world_data[(x, depth, z)] = 'iron_ore'
                     elif rand < 0.047 and depth < 0: # %0.2 Diamond (only deep)
                         world_data[(x, depth, z)] = 'diamond_ore'
                     else:
                         world_data[(x, depth, z)] = 'stone'
                else:
                     world_data[(x, depth, z)] = 'bedrock'

generate_terrain()
generate_world_mesh()

# Hayvanları oluştur
spawn_animals_in_world()

# Oyuncu Kurulumu
player = FirstPersonController()
player.mouse_sensitivity = (40, 40)
player.speed = 8
player.gravity = 0.5
player.jump_height = 2

# Güvenli spawn pozisyonu bul (blokların içine girmemek için)
def find_safe_spawn_position():
    """Oyuncunun blokların içine girmeyeceği güvenli bir spawn pozisyonu bulur"""
    spawn_x = scale // 2
    spawn_z = scale // 2
    
    # Yukarıdan aşağıya tara, ilk katı bloğu bul
    for y in range(60, 0, -1):
        # Ayakların altındaki blok katı mı?
        block_below = world_data.get((spawn_x, y - 1, spawn_z))
        # Oyuncunun duracağı yer boş mu? (2 blok yükseklik)
        block_at_feet = world_data.get((spawn_x, y, spawn_z))
        block_at_head = world_data.get((spawn_x, y + 1, spawn_z))
        
        if block_below and block_below != 'air' and not block_at_feet and not block_at_head:
            # Güvenli pozisyon bulundu: Katı zemin var, üstü boş
            return Vec3(spawn_x + 0.5, y + 0.1, spawn_z + 0.5)
    
    # Güvenli pozisyon bulunamadıysa yüksekte spawn et
    return Vec3(spawn_x + 0.5, 50, spawn_z + 0.5)

player.position = find_safe_spawn_position()
print(f"[SPAWN] Oyuncu güvenli pozisyonda spawn oldu: {player.position}")

player.cursor.visible = False
player.traverse_target = solid_world # Oyuncu sadece katı dünyaya çarpar

# Kamera Sistemi Değişkenleri
camera_mode = 0 # 0: 1. Şahıs, 1: 3. Şahıs Arka, 2: 3. Şahıs Ön

# Oyuncu Modeli (Steve)
# Karakter Modelleri
steve_model = SteveModel(parent=player, enabled=False)
alex_model = AlexModel(parent=player, enabled=False)

# Varsayılan Model: Steve
current_character_type = 'steve'
player_model = steve_model # Başlangıç referansı
# Not: player_model.enabled durumu input() içinde camera_mode'a göre yönetiliyor

# Crosshair UI
crosshair = Entity(
    parent=camera.ui,
    model='quad',
    texture='assets/textures/ui/crosshair',
    scale=0.04,
    color=color.white
)
if crosshair.texture:
    crosshair.texture.filtering = 'nearest'

# Envanter Sistemi
class Inventory(Entity):
    def __init__(self):
        super().__init__(parent=camera.ui)
        self.visible = True
        self.is_open = False
        self.z = -40 # Envanteri en öne taşı (Diğer UI elemanlarının önüne)
        
        # Envanter Verisi (36 Slot: 0-8 Hotbar, 9-35 Main)
        self.slots_data = [None] * 36
        self.slots_count = [0] * 36
        
        # Başlangıçta envanter boş
        starter_items = []
        for i, item in enumerate(starter_items):
            self.slots_data[i] = item

        self.selected_slot = 0 # Hotbar seçimi (0-8)
        
        # --- CRAFTING VERİLERİ (2x2) ---
        self.craft_data = [None] * 4
        self.craft_count = [0] * 4
        self.result_data = None
        self.result_count = 0

        # --- DRAG & DROP & DISTRIBUTE ---
        self.dragged_item_name = None
        self.dragged_item_count = 0
        self.drag_distributed_slots = [] 
        self.distribute_button = None # 'left' or 'right'

        # --- DOUBLE CLICK & QUICK MOVE ---
        self.last_click_time = 0
        self.last_click_slot = -1
        
        # --- GÖRSEL ELEMANLAR ---
        
        # Renk Paleti (Gri Tema)
        self.color_panel = color.rgb(198/255, 198/255, 198/255) # Light Gray
        self.color_slot = color.rgb(139/255, 139/255, 139/255)  # Dark Gray
        self.color_slot_hover = color.rgb(160/255, 160/255, 160/255)
        
        # 1. Hotbar (Sürekli Görünür)
        # Oyun içindeki ince hotbar
        self.hotbar_bg = Entity(
            parent=self,
            model='quad', 
            color=color.rgba(0, 0, 0, 0.8),
            scale=(0.8, 0.09),
            position=(0, -0.45)
        )
        
        self.hotbar_slots = []
        self.hotbar_icons = []
        self.hotbar_texts = []
        
        # Hotbar slotlarını oluştur
        for i in range(9):
            # Slot Arkaplanı
            slot = Entity(
                parent=self.hotbar_bg,
                model='quad',
                color=color.rgba(0.5, 0.5, 0.5, 0.5) if i == self.selected_slot else color.rgba(0.2, 0.2, 0.2, 0.5),
                scale=(0.1, 0.9),
                position=(-0.45 + (i * 0.112), 0),
                z=-0.1,
                collider='box'
            )
            self.hotbar_slots.append(slot)
            
            # İkon
            icon = Entity(
                parent=slot,
                model='quad',
                texture=None,
                color=color.white,
                scale=(0.8, 0.8),
                z=-0.2,
                visible=False
            )
            self.hotbar_icons.append(icon)
            
            # Miktar Metni
            txt = Text(
                parent=slot,
                text='',
                origin=(0.5, -0.5),
                position=(0.45, -0.4),
                scale=15,
                color=color.white,
                z=-0.3
            )
            self.hotbar_texts.append(txt)

        # 2. Ana Envanter Paneli (E ile açılır)
        self.main_panel = Entity(
            parent=self,
            model='quad',
            color=self.color_panel,
            scale=(1.0, 0.92), # Daha uzun panel
            position=(0, 0.02),
            enabled=False
        )
        

        
        # 2.1 Crafting Alanı (2x2) - Sağ Üst
        self.craft_label = Text(
            parent=self.main_panel,
            text='Üretim Masası',
            origin=(-0.5, 0.5),
            position=(0.05, 0.38), # Crafting üstünde
            color=color.black66,
            scale=1.2
        )
        
        self.craft_slots = []
        self.craft_icons = []
        self.craft_texts = []
        
        # Slot boyutlarını kare yapmak için oran
        slot_aspect = self.main_panel.scale_x / self.main_panel.scale_y
        
        # 2x2 Üretim Izgarası
        start_x_craft = 0.15
        start_y_craft = 0.30
        spacing = 0.08
        
        for i in range(4):
            # 2x2 Grid: 0 1
            #           2 3
            row = i // 2
            col = i % 2
            slot = Entity(
                parent=self.main_panel,
                model='quad',
                color=self.color_slot,
                scale=(0.07, 0.07 * slot_aspect),
                position=(start_x_craft + (col * spacing), start_y_craft - (row * (spacing * slot_aspect))),
                z=-0.1,
                collider='box'
            )
            self.craft_slots.append(slot)
            
            icon = Entity(
                parent=slot,
                model='quad',
                texture=None,
                color=color.white,
                scale=(0.8, 0.8),
                z=-0.2,
                visible=False
            )
            self.craft_icons.append(icon)
            
            txt = Text(
                parent=slot,
                text='',
                origin=(0.5, -0.5),
                position=(0.45, -0.4),
                scale=15,
                color=color.white,
                z=-0.3
            )
            self.craft_texts.append(txt)
            
        # Ok (Üretim oku)
        self.arrow = Text(
            parent=self.main_panel,
            text='->',
            origin=(0, 0),
            position=(0.32, 0.24),
            color=color.black66,
            scale=2
        )
        
        # Sonuç Slotu - Tekli
        self.result_slot = Entity(
            parent=self.main_panel,
            model='quad',
            color=self.color_slot,
            scale=(0.09, 0.09 * slot_aspect),
            position=(0.42, 0.24),
            z=-0.1,
            collider='box'
        )
        self.result_icon = Entity(
            parent=self.result_slot,
            model='quad',
            texture=None,
            color=color.white,
            scale=(0.8, 0.8),
            z=-0.2,
            visible=False
        )
        self.result_text = Text(
            parent=self.result_slot,
            text='',
            origin=(0.5, -0.5),
            position=(0.45, -0.4),
            scale=15,
            color=color.white,
            z=-0.3,
            ignore=True
        )
        
        self.main_slots = [] # Görsel slotlar (Grid)
        self.main_icons = []
        self.main_texts = []
        
        # 3. Ana Envanter + Hotbar Grid (Alt Kısım)
        # 3 sıra Main Inventory (Y: -0.05, -0.15, -0.25)
        # 1 sıra Hotbar (Y: -0.38 - Biraz boşluklu)
        
        # 3x9 Ana Envanter Izgarası
        grid_start_x = -0.36
        grid_start_y = 0.05 # Yukarı çekildi
        grid_spacing = 0.09
        
        for row in range(3):
            for col in range(9):
                # Slot indeksi: 9 + (row * 9) + col
                slot = Entity(
                    parent=self.main_panel,
                    model='quad',
                    color=self.color_slot,
                    scale=(0.08, 0.08 * slot_aspect),
                    position=(grid_start_x + (col * grid_spacing), grid_start_y - (row * (grid_spacing * slot_aspect))),
                    z=-0.1,
                    collider='box'
                )
                self.main_slots.append(slot)
                
                # İkon
                icon = Entity(
                    parent=slot,
                    model='quad',
                    texture=None,
                    color=color.white,
                    scale=(0.8, 0.8),
                    z=-0.2,
                    visible=False
                )
                self.main_icons.append(icon)
                
                # Miktar
                txt = Text(
                    parent=slot,
                    text='',
                    origin=(0.5, -0.5),
                    position=(0.45, -0.4),
                    scale=15,
                    color=color.white,
                    z=-0.3
                )
                self.main_texts.append(txt)
                if slot.texture: slot.texture.filtering = 'nearest'
        
        self.drag_icon = Entity(
            parent=camera.ui,
            model='quad',
            texture=None,
            scale=(0.06, 0.06),
            z=-10,
            visible=False,
            ignore=True
        )
        self.drag_text = Text(
            parent=self.drag_icon,
            text='',
            origin=(0.5, -0.5),
            position=(0.4, -0.4),
            scale=15,
            color=color.white,
            z=-0.1,
            ignore=True
        )
        self.dragged_item_index = None 
        
        self.update_ui()

    def update_ui(self):
        """Tüm slot verilerini görselle eşle"""
        # 1. Hotbar Güncelle (0-8)
        for i in range(9):
            item_name = self.slots_data[i]
            
            # Seçim Vurgusu
            if i == self.selected_slot:
                self.hotbar_slots[i].color = color.white # Seçili
            else:
                self.hotbar_slots[i].color = color.hsv(0, 0, 0.3, 1) # Normal
                
            if item_name:
                item_data = items.get(item_name, {})
                tex_path = item_data.get('icon') or item_data.get('texture')
                if tex_path and not tex_path.endswith('.png'): tex_path += '.png'
                
                # Texture yükle
                self.hotbar_icons[i].texture = tex_path
                if self.hotbar_icons[i].texture:
                    self.hotbar_icons[i].texture.filtering = 'nearest'
                self.hotbar_icons[i].visible = True
                
                # Ölçeklendirme (aletler/yemekler vs bloklar)
                item_type = item_data.get('type')
                if item_name in ['grass', 'dirt']: # 2D görünümlü bloklar
                    self.hotbar_icons[i].scale = (0.7, 0.7)
                elif item_type in ['tool', 'food', 'material']:
                    self.hotbar_icons[i].scale = (0.9, 0.9)
                else:
                    self.hotbar_icons[i].scale = (0.6, 0.6) # Normal bloklar

                # Miktar
                count = self.slots_count[i]
                self.hotbar_texts[i].text = str(count) if count > 1 else ''
            else:
                self.hotbar_icons[i].visible = False
                self.hotbar_texts[i].text = ''

        # 2. Ana Panel Güncelleme (9-35)
        if self.is_open:
            for i in range(27):
                data_idx = 9 + i
                item_name = self.slots_data[data_idx]
                
                if item_name:
                    item_data = items.get(item_name, {})
                    tex_path = item_data.get('icon') or item_data.get('texture')
                    if tex_path and not tex_path.endswith('.png'): tex_path += '.png'
                    
                    self.main_icons[i].texture = tex_path
                    if self.main_icons[i].texture:
                        self.main_icons[i].texture.filtering = 'nearest'
                    self.main_icons[i].visible = True
                    
                    # Ölçeklendirme
                    item_type = item_data.get('type')
                    if item_name in ['grass', 'dirt']:
                        self.main_icons[i].scale = (0.7, 0.7)
                    elif item_type in ['tool', 'food', 'material']:
                        self.main_icons[i].scale = (0.9, 0.9)
                    else:
                        self.main_icons[i].scale = (0.6, 0.6)
                    
                    # Miktar
                    count = self.slots_count[data_idx]
                    self.main_texts[i].text = str(count) if count > 1 else ''
                else:
                    self.main_icons[i].visible = False
                    self.main_texts[i].text = ''
            
            # 3. Üretim Izgarasını Güncelle
            for i in range(4):
                item_name = self.craft_data[i]
                if item_name:
                    item_data = items.get(item_name, {})
                    tex_path = item_data.get('icon') or item_data.get('texture')
                    if tex_path and not tex_path.endswith('.png'): tex_path += '.png'
                    self.craft_icons[i].texture = tex_path
                    if self.craft_icons[i].texture:
                        self.craft_icons[i].texture.filtering = 'nearest'
                    self.craft_icons[i].visible = True
                    
                    # Ölçeklendirme
                    item_type = item_data.get('type')
                    if item_name in ['grass', 'dirt']: self.craft_icons[i].scale = (0.7, 0.7)
                    elif item_type in ['tool', 'food', 'material']: self.craft_icons[i].scale = (0.9, 0.9)
                    else: self.craft_icons[i].scale = (0.6, 0.6)
                    
                    count = self.craft_count[i]
                    self.craft_texts[i].text = str(count) if count > 1 else ''
                else:
                    self.craft_icons[i].visible = False
                    self.craft_texts[i].text = ''
            
            # 4. Crafting Sonucu Güncelle
            self.check_crafting()
            if self.result_data:
                item_data = items.get(self.result_data, {})
                tex_path = item_data.get('icon') or item_data.get('texture')
                if tex_path:
                    if not tex_path.endswith('.png'): tex_path += '.png'
                    self.result_icon.texture = tex_path
                    if self.result_icon.texture:
                        self.result_icon.texture.filtering = 'nearest'
                
                self.result_icon.visible = True
                
                # Ölçeklendirme
                item_type = item_data.get('type')
                if self.result_data in ['grass', 'dirt']: self.result_icon.scale = (0.7, 0.7)
                elif item_type in ['tool', 'food', 'material']: self.result_icon.scale = (0.9, 0.9)
                else: self.result_icon.scale = (0.6, 0.6)
                
                self.result_text.text = str(self.result_count) if self.result_count > 1 else ''
            else:
                self.result_icon.visible = False
                self.result_text.text = ''

    def check_crafting(self):
        """2x2 tarifleri kontrol et"""
        self.result_data = None
        self.result_count = 0
        c = self.craft_data
        
        # Crafting grid boş mu?
        if all(x is None for x in c):
            return

        # --- Tarif 1: Log -> Wood (1 kütük = 4 tahta) ---
        log_count = sum(1 for x in c if x == 'log')
        other_count = sum(1 for x in c if x and x != 'log')
        if log_count == 1 and other_count == 0:
            self.result_data = 'wood'
            self.result_count = 4
            return
        
        # --- Tarif 2: Wood x2 dikey -> Stick (2 tahta = 4 çubuk) ---
        if (c[0] == 'wood' and c[2] == 'wood' and c[1] is None and c[3] is None) or \
           (c[1] == 'wood' and c[3] == 'wood' and c[0] is None and c[2] is None):
            self.result_data = 'stick'
            self.result_count = 4
            return
            
        # --- Tarif 3: Wood x4 (2x2) -> Crafting Table ---
        if all(x == 'wood' for x in c):
            self.result_data = 'crafting_table'
            self.result_count = 1
            return

    def sync_total_counts(self):
        """Global inventory_counts'u slot verileriyle senkronize et"""
        global inventory_counts
        # Tüm anahtarları sıfırla (mevcut items listesini baz alarak)
        for k in items:
            inventory_counts[k] = 0
        
        # Main Slots (Hotbar + Panel)
        for i in range(36):
            if self.slots_data[i]:
                item = self.slots_data[i]
                if item in inventory_counts:
                    inventory_counts[item] += self.slots_count[i]
                else:
                    inventory_counts[item] = self.slots_count[i]
                    
        # Craft Slots
        for i in range(4):
            if self.craft_data[i]:
                item = self.craft_data[i]
                if item in inventory_counts:
                    inventory_counts[item] += self.craft_count[i]
                else:
                    inventory_counts[item] = self.craft_count[i]
                    
        # Dragged Item
        if self.dragged_item_name:
            item = self.dragged_item_name
            if item in inventory_counts:
                inventory_counts[item] += self.dragged_item_count
            else:
                inventory_counts[item] = self.dragged_item_count

    def update_counts(self):
        self.sync_total_counts()
        self.update_ui()
        if 'crafting_system' in globals() and crafting_system.visible:
            crafting_system.update_ui()
            crafting_system.check_crafting() # Ensure result slot is up to date
    
    def add_item(self, item_name, count=1, start_idx=0, end_idx=36):
        """Envantere öğe ekle (Stackleme mantığıyla + Overflow kontrolü)"""
        # 1. Mevcut stack'lere ekle
        if item_name not in tools:
            for i in range(start_idx, end_idx):
                if self.slots_data[i] == item_name and self.slots_count[i] < 64:
                    can_add = min(count, 64 - self.slots_count[i])
                    self.slots_count[i] += can_add
                    count -= can_add
                    if count <= 0:
                        self.update_counts()
                        return True
        
        # 2. Boş slotlara ekle
        while count > 0:
            found_empty = False
            for i in range(start_idx, end_idx):
                if self.slots_data[i] is None:
                    stack_limit = 64 if item_name not in tools else 1
                    take = min(count, stack_limit)
                    self.slots_data[i] = item_name
                    self.slots_count[i] = take
                    count -= take
                    found_empty = True
                    break
            if not found_empty:
                break # Belirtilen alan dolu
        
        self.update_counts()
        return count <= 0

    def remove_item(self, item_name, count=1):
        """Envanterden belirli bir öğeyi ve miktarı çıkar"""
        # Önce slotlarda arayalım
        total_found = 0
        for i in range(36):
            if self.slots_data[i] == item_name:
                total_found += self.slots_count[i]
        
        if total_found < count:
            return False

        # Çıkarma işlemi (sondan başla ki hotbar en son etkilensin)
        for i in range(35, -1, -1):
            if self.slots_data[i] == item_name:
                take = min(count, self.slots_count[i])
                self.slots_count[i] -= take
                count -= take
                if self.slots_count[i] <= 0:
                    self.slots_data[i] = None
                if count <= 0:
                    break
        
        self.update_counts()
        return True

    def use_selected_item(self):
        """Seçili slotu 1 azalt"""
        idx = self.selected_slot
        if self.slots_data[idx] and self.slots_count[idx] > 0:
            if self.slots_data[idx] not in tools:
                self.slots_count[idx] -= 1
                if self.slots_count[idx] <= 0:
                    self.slots_data[idx] = None
            else:
                # Alet kullanımı (şu anlık sınırsız veya tek kullanımlık değil)
                # Eğer aletleri kırmak isterseniz buraya dayanıklılık gelebilir
                pass
            self.update_counts()
            return True
        return False

    def toggle(self):
        """Envanteri aç/kapat"""
        self.is_open = not self.is_open
        self.main_panel.enabled = self.is_open
        
        if self.is_open:
            mouse.locked = False
            mouse.visible = True
            player.mouse_sensitivity = Vec2(0, 0)
            
            # Açılış animasyonu
            self.main_panel.scale = (0, 0)
            self.main_panel.animate_scale((1.0, 0.85), duration=0.15, curve=curve.out_back)
            
            # Hotbar'ı panelin içine taşı
            self.hotbar_bg.animate_position((0, -0.32), duration=0.15, curve=curve.out_back)
            self.hotbar_bg.color = color.rgba(0, 0, 0, 0) # Panel rengi zaten var, BG gizle
            
            for slot in self.hotbar_slots:
                slot.color = self.color_slot
                
            if 'crafting_system' in globals() and crafting_system.visible:
                crafting_system.close()
                
            self.update_ui()
        else:
            mouse.locked = True
            mouse.visible = False
            player.mouse_sensitivity = Vec2(40, 40)
            
            # Hotbar'ı eski yerine, eski haline döndür
            self.hotbar_bg.position = (0, -0.45)
            self.hotbar_bg.color = color.rgba(0, 0, 0, 0.8)
            
            # Elimizdeki eşya varsa geri koy
            if self.dragged_item_name:
                self.add_item(self.dragged_item_name, self.dragged_item_count)
                self.dragged_item_name = None
                self.dragged_item_count = 0
            
            self.update_ui() # Renkleri düzeltmek için (hotbar selection geri gelir)

    def drop_item(self, item_name, count=1):
        """Eşyayı fiziksel dünyaya at"""
        if not item_name or count <= 0: return
        
        # Oyuncunun önünü ve kamerasını baz alarak atma yönü
        drop_pos = player.position + Vec3(0, 1.2, 0) + camera.forward * 1.0
        dropped_item = spawn_dropped_item(drop_pos, item_name)
        
        # Fırlatma hızı
        dropped_item.velocity = camera.forward * 4.0 + Vec3(0, 2, 0)
        
        # Ses
        play_block_sound('swing', volume=0.5)
            
    def update(self):
        """Sürükleme ve görsel güncellemeler"""
        if (self.is_open or crafting_system.visible) and self.dragged_item_name:
            # Fix: Ensure texture is loaded
            tex = items.get(self.dragged_item_name, {}).get('icon') or items.get(self.dragged_item_name, {}).get('texture')
            if tex:
                if not tex.endswith('.png'): tex += '.png'
                self.drag_icon.texture = tex
                self.drag_icon.color = color.white 
            else:
                self.drag_icon.color = color.white # Fallback

            # Update position (convert mouse UI coords to screen relative)
            self.drag_icon.position = Vec3(mouse.x, mouse.y, -50)  # Inventory Z -40 olduğu için bu -50 olmalı
            self.drag_icon.visible = True
            
            # Text update with z-layering
            self.drag_text.text = str(self.dragged_item_count) if self.dragged_item_count > 1 else ''
            self.drag_text.z = -16
            
            # --- Sürükleyerek Dağıtma Kontrolü (Sol veya Sağ) ---
            if held_keys['left mouse'] or held_keys['right mouse']:
                btn = 'left' if held_keys['left mouse'] else 'right'
                
                # Eğer buton değişirse ve dağıtım başlamışsa sıfırlama (basit tutmak için)
                if self.distribute_button and self.distribute_button != btn:
                    return

                idx = self.get_hovered_slot_index()
                # Sonuç slotlarına (200, 400) dağıtım yapılmaz
                if idx != -1 and idx != 200 and idx != 400:
                    data, count, r_idx = self.get_slot_info(idx)
                    # Sadece aynı item veya boş slotlara dağıtılabilir
                    # Eğer data None dönerse (geçersiz slot) işlem yapma
                    if data is not None:
                         # Slot uygun mu? (Boş veya aynı item)
                        is_compatible = (data[r_idx] is None or data[r_idx] == self.dragged_item_name)
                        # Daha önce bu slota dağıtıldı mı?
                        is_new_slot = idx not in self.drag_distributed_slots
                        
                        if is_compatible and is_new_slot:
                            # Sağ tık dağıtımında miktar kontrolü (En az 1 tane kalmalı)
                            if btn == 'right' and self.dragged_item_count <= len(self.drag_distributed_slots):
                                pass 
                            else:
                                self.drag_distributed_slots.append(idx)
                                self.distribute_button = btn
        else:
            self.drag_icon.visible = False

    def get_selected_item(self):
        return self.slots_data[self.selected_slot]

    def get_hovered_slot_index(self):
        # 1. Hotbar
        for i, s in enumerate(self.hotbar_slots):
            if s.hovered: return i
        # 2. Main
        if self.is_open:
            for i, s in enumerate(self.main_slots):
                if s.hovered: return 9 + i
            for i, s in enumerate(self.craft_slots):
                if s.hovered: return 100 + i
            if self.result_slot.hovered: return 200
        
        # 3. Crafting Table Slots (if open)
        if crafting_system.visible:
            # Crafting System's own inventory displays
            for i, s in enumerate(crafting_system.inv_main_slots):
                if s.hovered: return 9 + i
            for i, s in enumerate(crafting_system.inv_hotbar_slots):
                if s.hovered: return i
            
            # Crafting Grid (3x3)
            for i, s in enumerate(crafting_system.craft_slots):
                if s.hovered: return 300 + i
            # Result Slot
            if crafting_system.result_slot.hovered: return 400
            
        return -1

    def get_slot_info(self, idx):
        if idx < 100: return self.slots_data, self.slots_count, idx
        if idx < 200: return self.craft_data, self.craft_count, idx - 100
        if idx == 200: return None, None, 200
        
        if idx >= 300 and idx < 400: # Crafting Table Grid
            return crafting_system.craft_data, crafting_system.craft_count, idx - 300
        if idx == 400: # Crafting Table Result
            return None, None, 400
            
        return None, None, -1

    def input(self, key):
        if not self.is_open and not crafting_system.visible:
            if key in ['1','2','3','4','5','6','7','8','9','scroll up','scroll down']:
                if key.isdigit(): self.selected_slot = int(key)-1
                elif key == 'scroll up': self.selected_slot = (self.selected_slot - 1) % 9
                else: self.selected_slot = (self.selected_slot + 1) % 9
                self.update_ui()
                return

            # Q ile Atma
            if key == 'q':
                item_name = self.get_selected_item()
                if item_name:
                    # Shift veya Ctrl ile tam stack atma
                    is_stack_drop = held_keys['left shift'] or held_keys['right shift'] or held_keys['left control'] or held_keys['right control']
                    drop_count = self.slots_count[self.selected_slot] if is_stack_drop else 1
                    self.drop_item(item_name, drop_count)
                    self.slots_count[self.selected_slot] -= drop_count
                    if self.slots_count[self.selected_slot] <= 0: self.slots_data[self.selected_slot] = None
                    self.update_counts()
                return

        # --- Tıklama ve Sürükleme Mantığı ---
        idx = self.get_hovered_slot_index()

        if key == 'left mouse down':
            if idx == -1:
                # Sol tıkla dışarı hepsini at
                if self.dragged_item_name:
                    self.drop_item(self.dragged_item_name, self.dragged_item_count)
                    self.dragged_item_name = None
                    self.dragged_item_count = 0
                    self.update_counts()
                return

            if idx != -1:
                # --- ÇİFT TIKLAMA (Hepsini Topla) ---
                current_time = time.time()
                if current_time - self.last_click_time < 0.3 and idx == self.last_click_slot:
                    if self.dragged_item_name:
                        for i in range(36):
                            if self.slots_data[i] == self.dragged_item_name:
                                can_take = min(self.slots_count[i], 64 - self.dragged_item_count)
                                self.dragged_item_count += can_take
                                self.slots_count[i] -= can_take
                                if self.slots_count[i] <= 0: self.slots_data[i] = None
                                if self.dragged_item_count >= 64: break
                        self.update_counts()
                        return

                self.last_click_time = current_time
                self.last_click_slot = idx

                # --- HIZLI TAŞIMA (Shift + Sol Tık) ---
                if held_keys['left shift'] and idx < 100:
                    data, count, r_idx = self.get_slot_info(idx)
                    if data[r_idx]:
                        item_n, item_c = data[r_idx], count[r_idx]
                        # Bölgeyi belirle
                        if idx < 9: # Hotbar -> Main Inv(9-36)
                            s, e = 9, 36
                        else:       # Main Inv -> Hotbar(0-9)
                            s, e = 0, 9
                        
                        if self.add_item(item_n, item_c, start_idx=s, end_idx=e):
                            data[r_idx] = None
                            count[r_idx] = 0
                        else:
                            # Eğer hedef bölge doluysa, yine de herhangi bir yere sığdırmayı dene (add_item varsayılan)
                            if self.add_item(item_n, item_c):
                                data[r_idx] = None
                                count[r_idx] = 0
                        
                        self.update_counts()
                    return

                # Crafting Sonucu Al (Player 2x2 veya Table 3x3)
                if idx == 200 or idx == 400:
                    is_table = (idx == 400)
                    res_data = crafting_system.result_data if is_table else self.result_data
                    res_count = crafting_system.result_count if is_table else self.result_count
                    
                    if res_data:
                        can_take = not self.dragged_item_name or (self.dragged_item_name == res_data and self.dragged_item_count + res_count <= 64)
                        
                        if can_take:
                            if not self.dragged_item_name:
                                self.dragged_item_name = res_data
                                self.dragged_item_count = res_count
                            else:
                                self.dragged_item_count += res_count

                            # --- Tüketim Mantığı ---
                            # Grid'deki her slottan 1 tane eksilt
                            c_data = crafting_system.craft_data if is_table else self.craft_data
                            c_count = crafting_system.craft_count if is_table else self.craft_count
                            
                            for i in range(len(c_data)):
                                if c_data[i]:
                                    c_count[i] -= 1
                                    if c_count[i] <= 0: c_data[i] = None
                            
                            if is_table:
                                crafting_system.check_crafting()
                                crafting_system.update_ui()
                            else:
                                self.check_crafting()
                            
                            self.update_counts()
                    return

                if self.dragged_item_name:
                    self.distribute_button = 'left'
                    self.drag_distributed_slots = [idx]
                    return

                data, count, r_idx = self.get_slot_info(idx)
                if data and data[r_idx]:
                    self.dragged_item_name = data[r_idx]
                    self.dragged_item_count = count[r_idx]
                    data[r_idx] = None
                    count[r_idx] = 0
                    if idx >= 300: # CT Grid
                        crafting_system.check_crafting()
                        crafting_system.update_ui()
                    elif idx >= 100 and idx < 200: # Player Craft Grid
                        self.check_crafting()
                    self.update_counts()

        elif key == 'right mouse down':
            if idx == -1:
                # Sağ tıkla dışarı 1 tane at
                if self.dragged_item_name:
                    self.drop_item(self.dragged_item_name, 1)
                    self.dragged_item_count -= 1
                    if self.dragged_item_count <= 0: self.dragged_item_name = None
                    self.update_counts()
                return

            if idx != -1 and idx != 200 and idx != 400:
                # --- HIZLI ATMA (Shift + Sağ Tık) ---
                if held_keys['left shift']:
                    data, count, r_idx = self.get_slot_info(idx)
                    if data and data[r_idx]:
                        # Dünyaya fırlat
                        self.drop_item(data[r_idx], count[r_idx])
                        data[r_idx] = None
                        count[r_idx] = 0
                        if idx >= 300: crafting_system.check_crafting(); crafting_system.update_ui()
                        self.update_counts()
                    return

                if self.dragged_item_name:
                    self.distribute_button = 'right'
                    self.drag_distributed_slots = [idx]
                    return

                data, count, r_idx = self.get_slot_info(idx)
                if not self.dragged_item_name:
                    if data and data[r_idx] and count[r_idx] > 0:
                        take = math.ceil(count[r_idx] / 2)
                        self.dragged_item_name = data[r_idx]
                        self.dragged_item_count = take
                        count[r_idx] -= take
                        if count[r_idx] <= 0: data[r_idx] = None
                        if idx >= 300: crafting_system.check_crafting(); crafting_system.update_ui()
                        elif idx >= 100: self.check_crafting()
                        self.update_counts()
                
        elif key == 'left mouse up' or key == 'right mouse up':
            btn_up = 'left' if 'left' in key else 'right'
            if self.distribute_button == btn_up:
                # Case 1: Tek slot (Normal Tıklama)
                if len(self.drag_distributed_slots) == 1:
                    s_idx = self.drag_distributed_slots[0]
                    data, count, r_idx = self.get_slot_info(s_idx)
                    
                    if data is not None:
                        if btn_up == 'left': # Sol Tık: Swap veya Stack
                            if data[r_idx] == self.dragged_item_name:
                                add = min(self.dragged_item_count, 64 - count[r_idx])
                                count[r_idx] += add
                                self.dragged_item_count -= add
                            else:
                                temp_n, temp_c = data[r_idx], count[r_idx]
                                data[r_idx], count[r_idx] = self.dragged_item_name, self.dragged_item_count
                                self.dragged_item_name, self.dragged_item_count = temp_n, temp_c
                        else: # Sağ Tık: 1 Tane Bırak
                            if data[r_idx] is None or data[r_idx] == self.dragged_item_name:
                                if data[r_idx] is None: data[r_idx] = self.dragged_item_name
                                if count[r_idx] < 64:
                                    count[r_idx] += 1
                                    self.dragged_item_count -= 1
                        
                        if s_idx >= 300: crafting_system.check_crafting(); crafting_system.update_ui()
                        elif s_idx >= 100: self.check_crafting()
                
                # Case 2: Birden fazla slot (Dağıtma)
                elif len(self.drag_distributed_slots) > 1:
                    if btn_up == 'left': # Sol Dağıtım: Eşit Paylaş
                        total = self.dragged_item_count
                        per_slot = total // len(self.drag_distributed_slots)
                        if per_slot > 0:
                            for s_idx in self.drag_distributed_slots:
                                data, count, r_idx = self.get_slot_info(s_idx)
                                if data is not None:
                                    if data[r_idx] is None: data[r_idx] = self.dragged_item_name
                                    add = min(per_slot, 64 - count[r_idx])
                                    count[r_idx] += add
                                    self.dragged_item_count -= add
                                    if s_idx >= 300: crafting_system.check_crafting()
                    else: # Sağ Dağıtım: Her birine 1 tane
                        for s_idx in self.drag_distributed_slots:
                            if self.dragged_item_count <= 0: break
                            data, count, r_idx = self.get_slot_info(s_idx)
                            if data is not None:
                                if data[r_idx] is None: data[r_idx] = self.dragged_item_name
                                if count[r_idx] < 64:
                                    count[r_idx] += 1
                                    self.dragged_item_count -= 1
                                    if s_idx >= 300: crafting_system.check_crafting()
                    
                    if any(s_idx >= 300 for s_idx in self.drag_distributed_slots):
                        crafting_system.update_ui()
                    if any(100 <= s_idx < 200 for s_idx in self.drag_distributed_slots):
                        self.check_crafting()
                
                if self.dragged_item_count <= 0: self.dragged_item_name = None
                self.distribute_button = None
                self.drag_distributed_slots = []
                self.update_counts()

# --- NİŞANGAH ---
class Crosshair(Entity):
    def __init__(self):
        super().__init__(
            parent=camera.ui,
            model='quad',
            texture='assets/textures/ui/crosshair.png',
            scale=(0.04, 0.04),
            z=-10 # Hotbar ve diğer UI'ların önünde/arkasında uygun bir katman
        )

crosshair = Crosshair()

# --- CHUNK GÖRSELLEŞTİRME VE DEBUG SİSTEMİ ---
class ChunkDebugger(Entity):
    def __init__(self):
        super().__init__(parent=scene)
        self.enabled = False
        self.mode = 1 # 1: Wireframe, 2: Grid, 3: Highlight, 4: Load Zone
        self.show_info = True
        self.view_distance = 4
        
        # Görsel havuzu
        self.visuals = []
        self.labels = []
        self.info_panel = Entity(parent=camera.ui, enabled=False)
        self.info_text = Text(
            parent=self.info_panel, 
            text='', 
            position=(-0.85, 0.4), 
            scale=1.1,
            font='assets/fonts/consola.ttf',
            color=color.white,
            background=True,
            background_color=color.rgba(0,0,0,150)
        )
        
        self.last_update_pos = Vec3(0,0,0)
        self.update_interval = 0.5
        self.timer = 0

    def toggle(self):
        self.enabled = not self.enabled
        if not self.enabled:
            self.clear_visuals()
            self.info_panel.enabled = False
        else:
            self.refresh()
            self.info_panel.enabled = self.show_info

    def set_mode(self, mode):
        self.mode = mode
        if self.enabled:
            self.refresh()

    def clear_visuals(self):
        for v in self.visuals:
            destroy(v)
        self.visuals.clear()
        for l in self.labels:
            destroy(l)
        self.labels.clear()

    def refresh(self):
        if not self.enabled: return
        self.clear_visuals()
        
        px, pz = int(player.x // chunk_size), int(player.z // chunk_size)
        
        for cx in range(px - self.view_distance, px + self.view_distance + 1):
            for cz in range(pz - self.view_distance, pz + self.view_distance + 1):
                self.create_chunk_visual(cx, cz, px, pz)

    def create_chunk_visual(self, cx, cz, px, pz):
        is_current = (cx == px and cz == pz)
        chunk_exists = (cx, cz) in chunks
        chunk_ref = chunks.get((cx, cz))
        
        # Renk Belirleme (Min Minecraft Tarzı)
        if is_current:
            main_color = color.lime
        elif chunk_exists:
            if chunk_ref and chunk_ref.is_generating:
                main_color = color.yellow
            else:
                main_color = color.cyan if self.mode == 4 else color.rgba(255,255,255,100)
        else:
            main_color = color.red if (cx, cz) in world_data else color.gray

        # 1. Wireframe Mode
        if self.mode == 1:
            v = Entity(
                parent=self,
                model='wireframe_cube',
                scale=(chunk_size, 50, chunk_size),
                position=(cx * chunk_size + chunk_size/2, 15, cz * chunk_size + chunk_size/2),
                color=main_color,
                always_on_top=True
            )
            self.visuals.append(v)
            
        # 2. Grid Mode (Yer düzleminde)
        elif self.mode == 2:
            y_pos = player.y - 0.45
            # Zemin bul
            bx, bz = int(cx * chunk_size + 8), int(cz * chunk_size + 8)
            for ty in range(int(player.y), -15, -1):
                if (bx, ty, bz) in world_data:
                    y_pos = ty + 1.05; break

            v = Entity(
                parent=self,
                model=Grid(chunk_size, chunk_size),
                scale=chunk_size,
                rotation_x=90,
                position=(cx * chunk_size + chunk_size/2, y_pos, cz * chunk_size + chunk_size/2),
                color=main_color
            )
            self.visuals.append(v)

        # 3. Highlight Mode (Aktif Chunk)
        elif self.mode == 3:
            if is_current:
                v = Entity(
                    parent=self,
                    model='cube',
                    scale=(chunk_size, 55, chunk_size),
                    position=(cx * chunk_size + chunk_size/2, 15, cz * chunk_size + chunk_size/2),
                    color=color.rgba(0, 255, 0, 40),
                    always_on_top=True
                )
                self.visuals.append(v)

        # 4. Load Zone (Yüklü alan)
        elif self.mode == 4:
            if chunk_exists:
                v = Entity(
                    parent=self,
                    model='cube',
                    scale=(chunk_size - 0.1, 0.1, chunk_size - 0.1),
                    position=(cx * chunk_size + chunk_size/2, player.y - 0.48, cz * chunk_size + chunk_size/2),
                    color=color.rgba(0, 255, 255, 120) if chunk_ref.enabled else color.rgba(255, 100, 0, 80)
                )
                self.visuals.append(v)

        # Koordinat TextLabels
        if self.show_info and (is_current or self.mode == 1):
            label = Text(
                parent=self,
                text=f"CH {cx},{cz}",
                position=(cx * chunk_size + chunk_size/2, 42, cz * chunk_size + chunk_size/2),
                scale=12,
                color=main_color,
                billboard=True,
                always_on_top=True
            )
            self.labels.append(label)

    def update(self):
        if not self.enabled: return
        
        self.timer += time.dt
        if self.timer > self.update_interval:
            self.timer = 0
            curr_pos = Vec3(int(player.x // chunk_size), 0, int(player.z // chunk_size))
            if curr_pos != self.last_update_pos:
                self.last_update_pos = curr_pos
                self.refresh()
            
        if self.show_info:
            self.update_hud()

    def update_hud(self):
        cx, cz = int(player.x // chunk_size), int(player.z // chunk_size)
        chunk = chunks.get((cx, cz))
        
        info = f"<orange>CHUNK VISUALIZER [MODE {self.mode}]</orange>\n"
        info += f"Coords: {cx}, {cz} (P: {int(player.x)}, {int(player.z)})\n"
        
        if chunk:
            try:
                tri_count = (len(chunk.model.vertices) + len(chunk.passable_entity.model.vertices)) // 3
            except: tri_count = 0
            
            # Optimized block counting
            block_count = sum(1 for (x,y,z) in world_data if x // chunk_size == cx and z // chunk_size == cz)
            
            status = "LOADED"
            if chunk.is_generating: status = "<yellow>GENERATING</yellow>"
            elif not chunk.enabled: status = "<gray>CULLED</gray>"
            
            info += f"Bloklar: {block_count}\n"
            info += f"Üçgenler: {tri_count}\n"
            info += f"Durum: {status}\n"
        else:
            info += "Durum: <red>BAŞLATILAMADI</red>\n"
            
        mem = 0
        if 'debug_overlay' in globals():
            mem = debug_overlay.get_mem()
        info += f"Sistem BELLEK: {mem:.1f} MB\n"
        info += f"Mesafe: {self.view_distance} chunk\n"
        info += "-" * 20 + "\n"
        info += "[1-4] Modlar  [+/-] Mesafe\n"
        info += "[I] Bilgi  [DEL] Kaldır\n"
        info += "[F4] Kapat"
        
        self.info_text.text = info
        self.info_panel.enabled = True

    def force_reload(self):
        cx, cz = int(player.x // chunk_size), int(player.z // chunk_size)
        if (cx, cz) in chunks:
            chunks[(cx, cz)].generate_mesh()
            print(f"[DEBUG] Chunk {cx},{cz} reloaded.")
            self.refresh()

    def unload_chunk(self):
        cx, cz = int(player.x // chunk_size), int(player.z // chunk_size)
        if (cx, cz) in chunks:
            destroy(chunks[(cx, cz)])
            del chunks[(cx, cz)]
            print(f"[DEBUG] Chunk {cx},{cz} unloaded.")
            self.refresh()

class PerformanceMonitor(Entity):
    def __init__(self):
        super().__init__(parent=camera.ui)
        self.enabled = False
        self.detailed = False
        self.z = -500
        
        # --- COLOR SYSTEM ---
        self.C_BG = color.clear
        self.C_ACCENT = color.white
        self.C_GRAY = color.white
        self.C_WARN = color.white
        
        # Geçmiş Veriler
        self.fps_history = deque([0]*200, maxlen=200)
        self.frame_time_history = deque([0]*200, maxlen=200)
        self.mem_history = deque([0]*200, maxlen=200)
        
        # Benchmark
        self.benchmarking = False
        self.benchmark_start = 0
        self.benchmark_duration = 10
        self.benchmark_data = []
        
        # --- UI ELEMENTS ---
        # 1. Main Dashboard Panel
        self.panel = Entity(
            parent=self, 
            model='quad', 
            color=color.clear, 
            scale=(0.65, 0.95), # Panel boyutu genişletildi
            position=(-0.55, 0.0), # Merkeze yaklaştırıldı
            origin=(0, 0)
        )
        
        # Accent Bar Removed
        
        # Üst kısım hizalaması
        self.header = Entity(parent=self.panel, position=(-0.46, 0.46)) 
        self.title = Text(
            parent=self.header, 
            text='SİSTEM ANALİZİ', # Başlık Türkçeleştirildi
            scale=2.2,
            position=(0, 0), 
            color=color.white,
            font='assets/fonts/Minecraftia.ttf',
            z=-0.1
        )
        
        # Metric Container (Yazılar)
        self.main_text = Text(
            parent=self.panel, 
            text='', 
            scale=1.1, # Azıcık küçülterek ferah alan bırakma
            position=(-0.46, 0.41), 
            line_height=1.0, 
            color=color.white,
            font='assets/fonts/Minecraftia.ttf',
            z=-0.1 
        )
        
        # --- GRAPH HUD ---
        self.graph_container = Entity(parent=self.panel, position=(0, -0.22))
        
        # FPS Module
        self.fps_module = Entity(parent=self.graph_container, position=(0, 0.22)) 
        self.fps_label = Text(parent=self.fps_module, text='FPS: 0', scale=0.9, position=(-0.45, 0.12), color=color.white, font='assets/fonts/Minecraftia.ttf', z=-0.1)
        self.fps_bg = Entity(parent=self.fps_module, model='quad', color=color.clear, scale=(0.9, 0.12), position=(0, 0))
        self.fps_mesh = Entity(parent=self.fps_bg, model=Mesh(vertices=[], mode='line', thickness=2.5), color=color.white, z=-0.01)
        
        # Latency Module
        self.ft_module = Entity(parent=self.graph_container, position=(0, 0.05))
        self.ft_label = Text(parent=self.ft_module, text='FT: 0 ms', scale=0.9, position=(-0.45, 0.12), color=color.white, font='assets/fonts/Minecraftia.ttf', z=-0.1)
        self.ft_bg = Entity(parent=self.ft_module, model='quad', color=color.clear, scale=(0.9, 0.12), position=(0, 0))
        self.ft_mesh = Entity(parent=self.ft_bg, model=Mesh(vertices=[], mode='line', thickness=2.5), color=color.white, z=-0.01)
        
        # Memory Module (Hidden by default)
        self.mem_module = Entity(parent=self.graph_container, position=(-0, -0.12), enabled=False)
        self.mem_label = Text(parent=self.mem_module, text='RAM: 0 MB', scale=0.9, position=(-0.45, 0.12), color=self.C_GRAY, font='assets/fonts/Minecraftia.ttf', z=-0.1)
        self.mem_bg = Entity(parent=self.mem_module, model='quad', color=color.clear, scale=(0.9, 0.11), position=(0, 0))
        self.mem_mesh = Entity(parent=self.mem_bg, model=Mesh(vertices=[], mode='line', thickness=2.5), color=color.orange, z=-0.01)

        # 2. System Intelligence Panel (Top Right)
        self.sys_panel = Entity(
            parent=self, 
            model='quad', 
            color=color.clear, 
            scale=(0.35, 0.38), 
            position=(0.70, 0.3),
            enabled=False
        )
        # Borders Removed
        
        self.sys_text = Text(parent=self.sys_panel, text='', scale=2.5, position=(-0.46, 0.42), line_height=1.6, font='assets/fonts/Minecraftia.ttf', z=-0.1)
        
        # Footer Hints
        self.hint = Text(
            parent=self.panel, 
            text='F3: UI | SF3: SYS | CF3: RST | AF3: LOG', 
            scale=1.0, 
            position=(-0.46, -0.48), 
            color=color.white,
            font='assets/fonts/Minecraftia.ttf',
            z=-0.1
        )

    def on_enable(self):
        self.panel.scale_x = 0
        self.panel.animate_scale_x(0.65, duration=0.25, curve=curve.out_quad)

    def get_mem(self):
        try:
            process = psutil.Process(os.getpid())
            mem = process.memory_info().rss / (1024 * 1024)
            return mem
        except: return 0

    def update(self):
        if not self.enabled: return
        
        fps = 1.0 / time.dt if time.dt > 0 else 0
        ft = time.dt * 1000
        mem = self.get_mem()
        
        self.fps_history.append(fps)
        self.frame_time_history.append(ft)
        self.mem_history.append(mem)
        
        if self.benchmarking:
            self.benchmark_data.append(fps)
            if time.time() - self.benchmark_start > self.benchmark_duration:
                self.end_benchmark()

        # Grafikleri Güncelle
        self._update_graph(self.fps_mesh, self.fps_history, 144)
        self.fps_label.text = f"FPS: {int(fps)}"
        
        self._update_graph(self.ft_mesh, self.frame_time_history, 50)
        self.ft_label.text = f"FT: {ft:.1f}ms"
        
        if self.detailed:
            self.mem_module.enabled = True
            self._update_graph(self.mem_mesh, self.mem_history, 2048)
            self.mem_label.text = f"RAM: {mem:.1f} MB"
            self.sys_panel.enabled = True
        else:
            self.mem_module.enabled = False
            self.sys_panel.enabled = False

        # Renk Atamaları (FPS Geri Bildirimi)
        if fps >= 60: self.fps_mesh.color = color.lime
        elif fps >= 30: self.fps_mesh.color = color.yellow
        else: self.fps_mesh.color = color.red
        
        # Data Polling
        chunks_count = len(globals().get('chunks', {}))
        animals_list = globals().get('animals', [])
        items_list = globals().get('dropped_items', [])
        rain_sys = globals().get('rain_system')
        p_count = len(rain_sys.rain_particles) if rain_sys else 0
        total_e = len(animals_list) + len(items_list) + p_count
        
        # Gösterge Paneli İçeriği
        info = [
            f"<scale:1.1> + Sistem Analizi</scale>",
            f"   FPS: {int(fps)} | FT: {ft:.1f}ms",
            f"   RAM: {mem:.1f} MB",
            f"<scale:1.1> + Dünya Durumu</scale>",
            f"   CHUNK: {chunks_count} | VARLIK: {total_e}",
            f"   Canli: {len(animals_list)} | Eşya: {len(items_list)}",
            f"<scale:1.1> + Navigasyon</scale>",
            f"   XYZ: {player.x:.1f}, {player.y:.1f}, {player.z:.1f}",
            f"   HPR: {player.rotation_y:.1f} ({self.get_dir()[:1]})",
        ]
        
        if self.benchmarking:
            rem = int(self.benchmark_duration - (time.time() - self.benchmark_start))
            info.append(f"\n<scale:1.4>PERFORMANS TESTİ... {rem}sn</scale>")
            
        self.main_text.text = "\n".join(info)

        if self.detailed:
            gpu = "Algilaniyor..."
            try: gpu = app.loader.engine.win.getGsg().getDriverVendor()
            except: gpu = "Bilinmeyen GPU"
            
            try: urs_v = importlib.metadata.version('ursina')
            except: urs_v = "7.x.x"
            
            self.sys_text.text = (
                f"SİSTEM MİMARİSİ\n"
                f"Platform: {platform.system()} {platform.machine()}\n"
                f"Grafik: {gpu}\n"
                f"Python: {platform.python_version()}\n"
                f"Motor: Ursina {urs_v}\n"
                f"Görünüm: {window.size[0]}x{window.size[1]}\n"
            )

    def _update_graph(self, mesh_entity, data, max_val):
        verts = []
        for i, val in enumerate(data):
            x = -0.5 + (i / 200)
            y = -0.5 + min(1.0, val / max_val)
            verts.append((x, y, 0))
        mesh_entity.model.vertices = verts
        mesh_entity.model.generate()

    def get_dir(self):
        r = player.rotation_y % 360
        if 315 <= r or r < 45: return "Kuzey (+Z)"
        elif 45 <= r < 135: return "Doğu (+X)"
        elif 135 <= r < 225: return "Güney (-Z)"
        else: return "Batı (-X)"

    def get_advice(self, fps, mem):
        if fps < 35: return "• Yüksek karmaşıklık. Görüşü düşür.\n• Yağmuru (R) kapat."
        if mem > 1200: return "• Bellek doldu. Yeniden başlatın."
        return "• Motor sağlığı: MÜKEMMEL"

    def reset_metrics(self):
        self.fps_history = deque([0]*200, maxlen=200)
        self.frame_time_history = deque([0]*200, maxlen=200)
        print("[ANALİZ] Veriler temizlendi.")

    def start_benchmark(self, dur=20):
        if self.benchmarking: return
        self.benchmarking = True
        self.benchmark_start = time.time()
        self.benchmark_duration = dur
        self.benchmark_data = []
        print(f"[ANALİZ] Benchmark {dur}sn boyunca başlatıldı")

    def end_benchmark(self):
        self.benchmarking = False
        if not self.benchmark_data: return
        avg = sum(self.benchmark_data) / len(self.benchmark_data)
        low = sorted(self.benchmark_data)[int(len(self.benchmark_data)*0.01)]
        with open("benchmark_report.txt", "a", encoding='utf-8') as f:
            f.write(f"{datetime.now()}: ORTALAMA={avg:.1f} FPS, EN DÜŞÜK %1={low:.1f} FPS\n")
        print("[ANALİZ] Rapor oluşturuldu: benchmark_report.txt")

    def log_snapshot(self):
        try:
            fps = int(sum(self.fps_history)/len(self.fps_history)) if self.fps_history else 0
            mem = self.get_mem()
            with open(self.log_file, "a", encoding='utf-8') as f:
                f.write(f"{datetime.now()},{fps},{time.dt*1000:.2f},{mem:.1f},{len(chunks)},{len(scene.entities)}\n")
        except: pass



# Öğe adı göstergesi (Animasyonlu)
class ScreenshotFlash(Entity):
    """F2 ile fotoğraf çekildiğinde ekranı parlatan efekt"""
    def __init__(self):
        super().__init__(
            parent=camera.ui,
            model='quad',
            color=color.white,
            scale=(2, 2),
            z=-1000, 
            enabled=False
        )
    
    def trigger(self):
        self.enabled = True
        self.alpha = 1
        self.animate('alpha', 0, duration=0.5, curve=curve.out_quad)
        invoke(setattr, self, 'enabled', False, delay=0.5)

screenshot_flash = ScreenshotFlash()

class DamageFlash(Entity):
    """Hasar alındığında veya can azaldığında ekranın kenarlarını kırmızı yapan efekt"""
    def __init__(self):
        super().__init__(
            parent=camera.ui,
            model='quad',
            texture='assets/textures/ui/damage_vignette.png',
            color=color.rgba(255, 0, 0, 0),
            scale=(2, 2),
            z=-999
        )
        if not os.path.exists('assets/textures/ui/damage_vignette.png'):
            self.texture = None
            self.model = 'quad'
            # Doku yoksa Overlay olarak çalışır
    
    def trigger(self, intensity=0.4):
        self.animate_color(color.rgba(255, 0, 0, intensity * 255), duration=0.1, curve=curve.out_quad)
        self.animate_color(color.rgba(255, 0, 0, 0), duration=0.4, delay=0.1, curve=curve.in_quad)

damage_flash = DamageFlash()

class ItemNameDisplay(Text):
    """Eşya seçildiğinde adını gösteren, arkaplansız premium UI"""
    def __init__(self):
        super().__init__(
            text='',
            parent=camera.ui,
            position=(0, -0.32),
            origin=(0, 0),
            scale=1.5,
            color=color.white,
            z=-105
        )
        self.background = False # Arkaplanı tamamen kapattık
        self.alpha = 0
        self.original_y = -0.32
        
        # Yazıya hafif bir gölge ekleyerek her zeminde okunmasını sağlayalım
        self.shadow = True
        self.shadow_color = color.black33

    def show_text(self, text_str):
        # Önceki animasyonları temizle
        self.interrupt_animations()
        
        # Metni hazırla (Büyük harf her zaman daha profesyonel durur)
        self.text = text_str.upper()
        self.alpha = 1
        self.y = self.original_y
        
        # --- ANİMASYONLAR ---
        
        # 1. Yavaşça yukarı kayma (Yüzme efekti)
        self.animate_y(self.original_y + 0.015, duration=2.0, curve=curve.out_quad)
        
        # 2. Yumuşak bir şekilde kaybolma
        # 1 saniye tam görünür kalır, sonra 1 saniyede solar
        self.animate('alpha', 0, duration=1.0, delay=1.0, curve=curve.in_sine)

    def interrupt_animations(self):
        if hasattr(self, 'animations'):
            for anim in self.animations:
                anim.finish()

item_name_display = ItemNameDisplay()

# Öğe adı çevirileri
item_names = {
    'pickaxe': 'Demir Kazma',
    'shovel': 'Demir Kürek', 
    'axe': 'Demir Balta',
    'grass': 'Çimen',
    'stone': 'Taş',
    'dirt': 'Toprak',
    'wood': 'Tahta',
    'leaves': 'Yaprak',
    'bedrock': 'Katman Kayası',
    'log': 'Kütük',
    'crafting_table': 'Çalışma Masası',
    'stick': 'Çubuk',
    'wooden_pickaxe': 'Ahşap Kazma',
    'stone_pickaxe': 'Taş Kazma',
    'wooden_axe': 'Ahşap Balta',
    'stone_axe': 'Taş Balta',
    'wooden_shovel': 'Ahşap Kürek',
    'stone_shovel': 'Taş Kürek',
    'apple': 'Elma',
    'bread': 'Ekmek',
    'cooked_meat': 'Pişmiş Et',
    'chicken_cooked': 'Pişmiş Tavuk',
    'egg': 'Yumurta',
    'wooden_sword': 'Tahta Kılıç',
    'stone_sword': 'Taş Kılıç',
    'coal': 'Kömür',
    'iron_ingot': 'Demir Külçesi',
    'diamond': 'Elmas',
    'coal_ore': 'Kömür Cevheri',
    'iron_ore': 'Demir Cevheri',
    'diamond_ore': 'Elmas Cevheri',
    'iron_pickaxe': 'Demir Kazma',
    'iron_shovel': 'Demir Kürek',
    'iron_axe': 'Demir Balta',
    'iron_sword': 'Demir Kılıç',
    'diamond_pickaxe': 'Elmas Kazma',
    'diamond_shovel': 'Elmas Kürek',
    'diamond_axe': 'Elmas Balta',
    'diamond_sword': 'Elmas Kılıç',
    'wool': 'Yün',
    'shears': 'Makas',
    'pig': 'Domuz',
    'cow': 'İnek',
    'sheep': 'Koyun',
    'sword': 'Taş Kılıç'
}

# --- EŞYA ÜRETİM (CRAFTİNG) SİSTEMİ ---
class CraftingSystem(Entity):
    """Crafting Table menüsü ve tarif sistemi (3x3) - Premium UI"""
    
    RECIPES_3x3 = [
        # --- ALETLER (AHŞAP) ---
        (('wood', 'wood', 'wood', None, 'stick', None, None, 'stick', None), 'wooden_pickaxe', 1),
        (('wood', 'wood', None, 'wood', 'stick', None, None, 'stick', None), 'wooden_axe', 1),
        ((None, 'wood', None, None, 'stick', None, None, 'stick', None), 'wooden_shovel', 1),
        ((None, 'wood', None, None, 'wood', None, None, 'stick', None), 'wooden_sword', 1),
        
        # --- ALETLER (TAŞ) ---
        (('stone', 'stone', 'stone', None, 'stick', None, None, 'stick', None), 'stone_pickaxe', 1),
        (('stone', 'stone', None, 'stone', 'stick', None, None, 'stick', None), 'stone_axe', 1),
        ((None, 'stone', None, None, 'stick', None, None, 'stick', None), 'stone_shovel', 1),
        ((None, 'stone', None, None, 'stone', None, None, 'stick', None), 'stone_sword', 1),

        # --- ALETLER (DEMİR) ---
        (('iron_ingot', 'iron_ingot', 'iron_ingot', None, 'stick', None, None, 'stick', None), 'iron_pickaxe', 1),
        (('iron_ingot', 'iron_ingot', None, 'iron_ingot', 'stick', None, None, 'stick', None), 'iron_axe', 1),
        ((None, 'iron_ingot', None, None, 'stick', None, None, 'stick', None), 'iron_shovel', 1),
        ((None, 'iron_ingot', None, None, 'iron_ingot', None, None, 'stick', None), 'iron_sword', 1),

        # --- ALETLER (ELMAS) ---
        (('diamond', 'diamond', 'diamond', None, 'stick', None, None, 'stick', None), 'diamond_pickaxe', 1),
        (('diamond', 'diamond', None, 'diamond', 'stick', None, None, 'stick', None), 'diamond_axe', 1),
        ((None, 'diamond', None, None, 'stick', None, None, 'stick', None), 'diamond_shovel', 1),
        ((None, 'diamond', None, None, 'diamond', None, None, 'stick', None), 'diamond_sword', 1),
    ]

    def __init__(self):
        super().__init__(parent=camera.ui)
        self.enabled = False
        self.visible = False
        self.z = -100 # UI layer
        
        # Veri
        self.craft_data = [None] * 9
        self.craft_count = [0] * 9
        self.result_data = None
        self.result_count = 0
        
        # --- UI ELEMANLARI ---
        # Ana Panel (Premium Dark Look - Glassmorphism)
        self.panel = Entity(
            parent=self,
            model='quad',
            color=color.rgba(30/255, 30/255, 35/255, 245/255), # Daha derin, sofistike koyu gri
            scale=(0.95, 0.8), # Biraz daha geniş ve orantılı
            position=(0, 0.05),
            visible=False,
            z=0
        )
        
        # Panel Border - İnce ve Zarif
        self.border = Entity(
            parent=self.panel,
            model='quad',
            color=color.rgba(0, 255/255, 255/255, 76/255), # Neon cyan ama düşük opaklık
            scale=(1.002, 1.002),
            z=0.01
        )
        
        # Title - Daha Minimalist ve Modern
        self.title_bg = Entity(
            parent=self.panel,
            model='quad',
            color=color.rgba(0, 0, 0, 100/255),
            scale=(1, 0.08),
            position=(0, 0.46),
            z=-0.05
        )
        
        self.title = Text(
            parent=self.panel,
            text='ÜRETİM İSTASYONU',
            origin=(0, 0),
            position=(0, 0.46),
            color=color.rgba(200/255, 255/255, 255/255, 255/255),
            scale=1.5,
            z=-0.1
        )
        
        # Grid Container
        self.grid_parent = Entity(parent=self.panel, position=(0, 0))

        # 3x3 Grid - Daha Ferah
        self.craft_slots = []
        self.craft_icons = []
        self.craft_texts = []
        
        aspect = 0.9/0.75
        for i in range(9):
            row = i // 3
            col = i % 3
            # Slot Arka Planı
            slot = Button(
                parent=self.grid_parent,
                model='quad',
                color=color.rgba(0, 0, 0, 128/255), # Daha koyu ve saydam slotlar
                scale=(0.09, 0.09 * aspect),
                position=(-0.25 + (col * 0.11), 0.22 - (row * 0.12)), # Spacing iyileştirildi
                z=-0.1,
                pressed_color=color.rgba(0, 255/255, 255/255, 76/255),
                highlight_color=color.rgba(255/255, 255/255, 255/255, 25/255), # Subtle highlight
                radius=0.1 # Köşeleri yumuşatmayı dene (destekleniyorsa)
            )
            self.craft_slots.append(slot)
            
            icon = Entity(parent=slot, model='quad', scale=(0.8, 0.8), z=-0.1, visible=False)
            self.craft_icons.append(icon)
            
            txt = Text(parent=slot, text='', origin=(0.5, -0.5), position=(0.45, -0.4), scale=12, z=-0.2, color=color.white)
            self.craft_texts.append(txt)

        # Arrow - Minimalist Çizgi
        self.arrow = Text(
            parent=self.grid_parent,
            text='→', # Basit, temiz ok karakteri
            origin=(0, 0),
            scale=4,
            color=color.rgba(255/255, 255/255, 255/255, 128/255),
            position=(0.14, 0.10),
            z=-0.1
        )

        # Result Slot - Vurgulu
        self.result_slot = Button(
            parent=self.grid_parent,
            model='quad',
            color=color.rgba(20/255, 20/255, 20/255, 200/255),
            scale=(0.14, 0.14 * aspect), # Biraz daha büyük
            position=(0.32, 0.10),
            z=-0.1,
            pressed_color=color.rgba(255/255, 215/255, 0, 50/255), # Altın vurgu
            highlight_color=color.rgba(255/255, 255/255, 255/255, 25/255)
        )
        # Sonuç slotu için özel bir parıltı (border)
        Entity(parent=self.result_slot, model='quad', color=color.rgba(255/255, 215/255, 0, 76/255), scale=(1.05, 1.05), z=0.01)

        self.result_icon = Entity(parent=self.result_slot, model='quad', scale=(0.7, 0.7), z=-0.1, visible=False)
        self.result_text = Text(parent=self.result_slot, text='', origin=(0.5, -0.5), position=(0.45, -0.4), scale=15, z=-0.2, color=color.gold)

        # --- ENVANTER ÖNİZLEME ---
        # Envanter Etiketi
        Entity(parent=self.panel, model='quad', color=color.rgba(255/255,255/255,255/255,25/255), scale=(0.9, 0.002), position=(0, -0.05), z=-0.05)
        
        self.inv_label = Text(parent=self.panel, text='ENVANTER', origin=(-0.5, 0), position=(-0.42, -0.08), color=color.rgba(255/255,255/255,255/255,180/255), scale=1, z=-0.1)
        
        self.inv_main_slots = []
        self.inv_main_icons = []
        self.inv_main_texts = []
        self.inv_hotbar_slots = []
        self.inv_hotbar_icons = []
        self.inv_hotbar_texts = []

        # 3x9 Grid
        for row in range(3):
            for col in range(9):
                slot = Button(
                    parent=self.panel,
                    model='quad',
                    color=color.rgba(0, 0, 0, 100/255),
                    scale=(0.08, 0.08 * aspect),
                    position=(-0.4 + (col * 0.1), -0.20 - (row * 0.10)),
                    z=-0.1,
                    highlight_color=color.rgba(255/255, 255/255, 255/255, 40/255)
                )
                self.inv_main_slots.append(slot)
                icon = Entity(parent=slot, model='quad', scale=(0.8, 0.8), z=-0.1, visible=False)
                self.inv_main_icons.append(icon)
                txt = Text(parent=slot, text='', origin=(0.5, -0.5), position=(0.45, -0.4), scale=12, z=-0.2, color=color.white)
                self.inv_main_texts.append(txt)

        # Hotbar (Ayrık, biraz aşağıda)
        for col in range(9):
            slot = Button(
                parent=self.panel,
                model='quad',
                color=color.rgba(0, 0, 0, 150/255), # Hotbar daha koyu
                scale=(0.08, 0.08 * aspect),
                position=(-0.4 + (col * 0.1), -0.55),
                z=-0.1,
                highlight_color=color.rgba(255/255, 255/255, 255/255, 50/255)
            )
            self.inv_hotbar_slots.append(slot)
            icon = Entity(parent=slot, model='quad', scale=(0.8, 0.8), z=-0.1, visible=False)
            self.inv_hotbar_icons.append(icon)
            txt = Text(parent=slot, text='', origin=(0.5, -0.5), position=(0.45, -0.4), scale=12, z=-0.2)
            self.inv_hotbar_texts.append(txt)

        # Recipe Book (Premium Minimalist Sidebar)
        self.book_btn = Button(
            parent=self.panel,
            text='TARİFLER',
            scale=(0.14, 0.045),
            position=(-0.38, 0.46),
            model='quad',
            color=color.rgba(0, 0, 0, 76/255),
            text_color=color.rgba(255/255, 255/255, 255/255, 200/255),
            highlight_color=color.rgba(255/255, 255/255, 255/255, 25/255),
            on_click=self.toggle_recipe_book,
            z=-0.1
        )
        self.book_btn.text_entity.scale = 0.8
        
        self.book_panel = Entity(
            parent=self,
            model='quad',
            color=color.rgba(25/255, 25/255, 30/255, 250/255), # Ana panele çok yakın bir ton
            scale=(0.35, 0.8),
            position=(0.68, 0.05),
            visible=False,
            z=-1
        )
        # Sağ panel border
        self.book_border = Entity(parent=self.book_panel, model='quad', color=color.rgba(255/255, 255/255, 255/255, 25/255), scale=(1.01, 1), z=0.01)
        
        self.book_title = Text(parent=self.book_panel, text='TARİF KİTABI', origin=(0, 0), position=(0, 0.45), scale=1.5, color=color.cyan, z=-101) # Daha canlı renk
        # Subtle glowing line under title
        Entity(parent=self.book_panel, model='quad', color=color.cyan, scale=(0.8, 0.002), position=(0, 0.42), z=-101)
        
        # Status Text
        self.status_text = Text(
            parent=self.book_panel,
            text='',
            origin=(0, 0),
            position=(0, -0.42),
            scale=1.2,
            color=color.white,
            z=-0.2
        )

        # Preview Grid (Mini 3x3)
        self.preview_slots = []
        grid_y_start = -0.12
        slot_size = 0.2
        slot_gap = 0.22 
        
        for i in range(9):
            row = i // 3
            col = i % 3
            slot = Entity(
                parent=self.book_panel,
                model='quad',
                color=color.rgba(0, 0, 0, 0.6),
                scale=(slot_size, 0.11), 
                position=(-0.22 + (col * slot_gap), grid_y_start - (row * 0.12)),
                z=-0.1
            )
            icon = Entity(parent=slot, model='quad', scale=(0.8, 0.8), z=-0.1, visible=False)
            self.preview_slots.append(icon)

        self.preview_label = Text(parent=self.book_panel, text='ÖNİZLEME', origin=(0, 0), position=(0, -0.06), scale=1, color=color.gray, z=-0.1)

        # Sayfalama Bileşenleri
        self.current_page = 0
        self.items_per_page = 4 # Artırıldı, liste sıkılaştırıldı
        self.total_pages = (len(self.RECIPES_3x3) + self.items_per_page - 1) // self.items_per_page

        self.recipe_btns = []
        
        # Gezinme Butonları
        self.prev_btn = Button(parent=self.book_panel, text='GERİ', scale=(0.14, 0.05), position=(-0.15, 0.38), color=color.rgba(255/255,255/255,255/255,25/255), on_click=self.prev_page, z=-0.1)
        self.next_btn = Button(parent=self.book_panel, text='İLERİ', scale=(0.14, 0.05), position=(0.15, 0.38), color=color.rgba(255/255,255/255,255/255,25/255), on_click=self.next_page, z=-0.1)
        
        self.page_txt = Text(parent=self.book_panel, text=f'1/{self.total_pages}', position=(0, 0.38), origin=(0, 0), scale=1, z=-0.1, color=color.gray)

        self.refresh_recipe_list()

    def refresh_recipe_list(self):
        # Eski butonları temizle
        for btn in self.recipe_btns:
            destroy(btn)
        self.recipe_btns = []

        start_index = self.current_page * self.items_per_page
        end_index = min(start_index + self.items_per_page, len(self.RECIPES_3x3))
        
        y_pos = 0.28 
        
        for i in range(start_index, end_index):
            pattern, res, count = self.RECIPES_3x3[i]
            text_str = item_names.get(res, res).upper()
            
            # Premium Card Button
            btn = Button(
                parent=self.book_panel,
                text=text_str,
                text_origin=(-0.4, 0),
                model='quad',
                color=color.rgba(255, 255, 255, 15), 
                scale=(0.88, 0.08), 
                position=(0, y_pos),
                z=-0.1,
                highlight_color=color.rgba(0, 220, 255, 60),
                pressed_color=color.white
            )
            # Text Styling
            btn.text_entity.scale = 0.85
            btn.text_entity.alignment = 'left'
            btn.text_entity.x = -0.42
            btn.text_entity.color = color.white
            
            # Icon preview on the right of the button
            res_icon = Entity(
                parent=btn,
                model='quad',
                texture=self.get_item_tex(res),
                scale=(0.06, 0.06 * (0.95/0.8)),
                position=(0.38, 0),
                z=-0.01
            )
            if res_icon.texture: res_icon.texture.filtering = 'nearest'

            btn.on_click = Func(self.try_autofill_recipe, pattern)
            
            self.recipe_btns.append(btn)
            y_pos -= 0.10

        # Gezinmeyi Güncelle
        self.page_txt.text = f'{self.current_page + 1} / {self.total_pages}'
        self.prev_btn.visible = self.current_page > 0
        self.next_btn.visible = self.current_page < self.total_pages - 1

    def get_item_tex(self, item):
        if not item: return None
        tex = items.get(item, {}).get('icon') or items.get(item, {}).get('texture')
        if not tex:
            if item == 'stick': return 'assets/textures/items/stick.png'
            return None
        if not tex.endswith('.png'): tex += '.png'
        return tex

    def prev_page(self):
        if self.current_page > 0:
            self.current_page -= 1
            self.refresh_recipe_list()

    def next_page(self):
        if self.current_page < self.total_pages - 1:
            self.current_page += 1
            self.refresh_recipe_list()

    def try_autofill_recipe(self, pattern):
        # 1. Update Preview
        for icon in self.preview_slots: icon.visible = False
        def get_tex(item):
            if not item: return None
            # Special case for stick if needed, otherwise standard lookup
            base_tex = items.get(item, {}).get('icon') or items.get(item, {}).get('texture')
            if not base_tex:
                 # Fallback for stick if not in main dict correctly
                 if item == 'stick': return 'assets/textures/items/stick.png'
                 return None
            
            if not base_tex.endswith('.png'): base_tex += '.png'
            return base_tex
        for i, item_name in enumerate(pattern):
            if item_name:
                self.preview_slots[i].texture = get_tex(item_name)
                self.preview_slots[i].visible = True

        # 2. Malzemeleri Kontrol Et
        needed = {}
        for item in pattern:
            if item: needed[item] = needed.get(item, 0) + 1
        
        # Mevcut envanteri hesapla (önce ızgara öğelerini geri döndürmeyi simüle et)
        current_inv = inventory_counts.copy()
        for i in range(9):
            if self.craft_data[i]:
                current_inv[self.craft_data[i]] = current_inv.get(self.craft_data[i], 0) + self.craft_count[i]

        missing = []
        for item, qty in needed.items():
            if current_inv.get(item, 0) < qty:
                missing.append(item)
        
        if missing:
            tr_missing = [item_names.get(m, m) for m in missing]
            self.status_text.text = 'Eksiğin Var!\n' + ', '.join(tr_missing)
            self.status_text.color = color.red
            return

        # 3. Autofill
        # Önce, ızgarayı envantere boşalt
        for i in range(9):
            if self.craft_data[i]:
                inventory.add_item(self.craft_data[i], self.craft_count[i])
                self.craft_data[i] = None
                self.craft_count[i] = 0
        
        # Envanterden öğeleri yerleştir
        for i, item in enumerate(pattern):
            if item:
                # Envanterde bul
                for inv_i in range(36):
                    if inventory.slots_data[inv_i] == item and inventory.slots_count[inv_i] > 0:
                        inventory.slots_count[inv_i] -= 1
                        if inventory.slots_count[inv_i] == 0: inventory.slots_data[inv_i] = None
                        
                        self.craft_data[i] = item
                        self.craft_count[i] = 1
                        break
        
        self.status_text.text = 'Hazır!'
        self.status_text.color = color.green
        inventory.update_counts()
        self.check_crafting()

    def toggle_recipe_book(self):
        self.book_panel.visible = not self.book_panel.visible

    def open(self):
        self.enabled = True
        self.visible = True
        self.panel.visible = True
        mouse.locked = False
        mouse.visible = True
        player.mouse_sensitivity = Vec2(0, 0)
        
        # Çakışmaları önlemek için standart arayüzü gizle
        if hasattr(inventory, 'hotbar_bg'): inventory.hotbar_bg.enabled = False
        if 'health_bar' in globals(): health_bar.enabled = False
        if 'hunger_bar' in globals(): hunger_bar.enabled = False
        if 'crosshair' in globals(): crosshair.enabled = False
        
        self.update_ui()
        if inventory.is_open: inventory.toggle()

    def close(self):
        # Öğeleri envantere geri döndür
        for i in range(9):
            if self.craft_data[i]:
                inventory.add_item(self.craft_data[i], self.craft_count[i])
                self.craft_data[i] = None
                self.craft_count[i] = 0
        
        self.enabled = False
        self.visible = False
        self.panel.visible = False
        self.book_panel.visible = False
        mouse.locked = True
        mouse.visible = False
        player.mouse_sensitivity = Vec2(40, 40)
        
        # Standart arayüzü geri yükle
        if hasattr(inventory, 'hotbar_bg'): inventory.hotbar_bg.enabled = True
        if 'health_bar' in globals(): health_bar.enabled = True
        if 'hunger_bar' in globals(): hunger_bar.enabled = True
        if 'crosshair' in globals(): crosshair.enabled = True
        
        inventory.update_counts()

    def update_ui(self):
        def get_tex(item):
            if not item: return None
            t = items.get(item, {}).get('icon') or items.get(item, {}).get('texture')
            if t and not t.endswith('.png'): t += '.png'
            return t

        # 3x3 Grid
        for i in range(9):
            item = self.craft_data[i]
            count = self.craft_count[i]
            if item:
                item_data = items.get(item, {})
                # Varsa ikon kullan, yoksa dokuyu kullan
                tex = item_data.get('icon') or item_data.get('texture')
                if tex and not tex.endswith('.png'): tex += '.png'
                
                self.craft_icons[i].texture = tex
                self.craft_icons[i].visible = True
                self.craft_texts[i].text = str(count) if count > 1 else ''
                # Adaptive scaling
                itype = items.get(item, {}).get('type')
                if itype == 'tool': self.craft_icons[i].scale = (0.9, 0.9)
                elif item in ['grass', 'dirt']: self.craft_icons[i].scale = (0.7, 0.7)
                else: self.craft_icons[i].scale = (0.6, 0.6)
            else:
                self.craft_icons[i].visible = False
                self.craft_texts[i].text = ''

        # Result
        if self.result_data:
            self.result_icon.texture = get_tex(self.result_data)
            self.result_icon.visible = True
            self.result_text.text = str(self.result_count) if self.result_count > 1 else ''
            self.result_icon.scale = (0.7, 0.7)
        else:
            self.result_icon.visible = False
            self.result_text.text = ''

        # Inventory Sync
        for i in range(27):
            item = inventory.slots_data[9+i]
            count = inventory.slots_count[9+i]
            if item:
                # Use icon override if exists
                item_data = items.get(item, {})
                tex = item_data.get('icon') or item_data.get('texture')
                
                self.inv_main_icons[i].texture = tex
                self.inv_main_icons[i].visible = True
                self.inv_main_texts[i].text = str(count) if count > 1 else ''
                self.inv_main_icons[i].scale = (0.6, 0.6)
            else:
                self.inv_main_icons[i].visible = False
                self.inv_main_texts[i].text = ''

        for i in range(9):
            item = inventory.slots_data[i]
            count = inventory.slots_count[i]
            if item:
                item_data = items.get(item, {})
                tex = item_data.get('icon') or item_data.get('texture')
                
                self.inv_hotbar_icons[i].texture = tex
                self.inv_hotbar_icons[i].visible = True
                self.inv_hotbar_texts[i].text = str(count) if count > 1 else ''
                self.inv_hotbar_icons[i].scale = (0.6, 0.6)
            else:
                self.inv_hotbar_icons[i].visible = False
                self.inv_hotbar_texts[i].text = ''

    def check_crafting(self):
        self.result_data = None
        self.result_count = 0
        grid = tuple(self.craft_data)
        if all(x is None for x in grid): return
        for pattern, res, count in self.RECIPES_3x3:
            if grid == pattern:
                self.result_data = res
                self.result_count = count
                return
        # Dinamik tarifler
        log_indices = [i for i, x in enumerate(grid) if x == 'log']
        if len(log_indices) == 1 and sum(1 for x in grid if x and x != 'log') == 0:
            self.result_data = 'wood'; self.result_count = 4; return
        for col in range(3):
            for row in range(2):
                idx = row * 3 + col
                if grid[idx] == 'wood' and grid[idx+3] == 'wood' and sum(1 for x in grid if x) == 2:
                    self.result_data = 'stick'; self.result_count = 4; return
        for r in range(2):
            for c in range(2):
                idx = r * 3 + c
                if grid[idx] == 'wood' and grid[idx+1] == 'wood' and grid[idx+3] == 'wood' and grid[idx+4] == 'wood' and sum(1 for x in grid if x) == 4:
                    self.result_data = 'crafting_table'; self.result_count = 1; return

    def input(self, key):
        if key == 'escape' and self.visible:
            self.close()

# Crafting sistemi örneği
crafting_system = CraftingSystem()

# Crafting table'a bakıldığında kullanılacak değişken
looking_at_crafting_table = False
crafting_table_pos = None

def get_player_damage(held_item):
    """Tutulan eşyaya göre hasarı hesaplar"""
    base_damage = 10 # 1 Heart (Hand)
    
    if held_item and held_item in items:
        item_data = items[held_item]
        if 'damage' in item_data:
            return item_data['damage']
            
    return base_damage


# Oyun Mantığı
def update():
    global current_block, mining_progress, target_block, last_action_time, current_held_item, step_timer, day_night_cycle, player_last_position
    
    # 0. Gece-Gündüz Döngüsü Güncelleme
    day_night_cycle.update(time.dt)
    
    # 0.1. Yağmur Sistemi Güncelleme
    rain_system.update(time.dt)
    
    # Hızlı test kontrolleri (tuş basılı tutma)
    if held_keys['page up']:  # Saati hızlı ileri alma
        day_night_cycle.add_minutes(1 * time.dt * 60)  # Saniyede 1 dakika
    if held_keys['page down']:  # Saati hızlı geri alma
        day_night_cycle.subtract_minutes(1 * time.dt * 60)  # Saniyede 1 dakika

    # --- DİNAMİK FOV VE HIZ EFEKTİ (PREMIUM) ---
    is_sprinting = held_keys['left control'] or held_keys['right control']
    is_moving = player.grounded and (held_keys['w'] or held_keys['s'] or held_keys['a'] or held_keys['d'])
    is_sneaking = held_keys['left shift'] or held_keys['right shift']
    is_zooming = held_keys['c'] # OptiFine style zoom

    target_fov = 90
    if is_zooming:
        target_fov = 30 # Zoom FOV
    elif is_sprinting and is_moving:
        target_fov = 102 # Sprint FOV
    elif is_sneaking:
        target_fov = 85 # Sneak FOV
        
    camera.fov = lerp(camera.fov, target_fov, time.dt * 10)

    # Zoom sırasında fare hassasiyetini düşür (Daha hassas kontrol için)
    if 'player' in globals():
        if is_zooming:
            player.mouse_sensitivity = (15, 15)
        else:
            player.mouse_sensitivity = (40, 40)

    # 0.2. Atmosferik Rüzgar Güncelleme (Yüksekliğe göre ses artar)
    if wind_audio and hasattr(wind_audio, '_clip') and wind_audio._clip:
        # 10 blok yüksekten sonra başlar, 40 blokta max (0.1 vol) olur
        wind_vol = clamp((player.y - 10) / 300, 0, 0.1)
        try:
            wind_audio.volume = wind_vol
        except:
            pass  # Ses sistemi hatası, sessizce devam et

    # 1. Can ve Açlık Sistemi Güncelle
    player_stats.update(time.dt)
    health_bar.update_bar(player_stats.current_health, player_stats.max_health)
    hunger_bar.update_bar(player_stats.current_hunger, player_stats.max_hunger)
    
    # --- YAPRAK ÇÜRÜME GÜNCELLEME (OPTIMIZED BATCHED HEAP) ---
    curr_t = time.time()
    processed = 0
    # Frame başına en fazla 5 yaprak çürüt (Spike engelleme + O(1) check)
    while leaves_to_decay and leaves_to_decay[0][0] <= curr_t and processed < 5:
        target_t, lx, ly, lz = heapq.heappop(leaves_to_decay)
        leaves_pending_set.discard((lx, ly, lz))
        
        if world_data.get((lx, ly, lz)) == 'leaves':
            if not is_leaf_supported(lx, ly, lz):
                if random.random() < 0.2:
                    spawn_leaf_decay_particle(Vec3(lx+0.5, ly+0.5, lz+0.5))
                break_block_logic(Vec3(lx, ly, lz))
        
        processed += 1

    
    # 1. Yürüme Sesi Mantığı (Blok Bazlı)
    # Oyuncunun gerçekten hareket edip etmediğini kontrol et (pozisyon değişimi ile)
    global player_last_position
    current_position = Vec3(player.x, player.y, player.z)
    position_change = (current_position - player_last_position).length()
    is_actually_moving = position_change > 0.01  # Minimum hareket eşiği (frame başına)
    player_last_position = current_position
    
    if player.grounded and (held_keys['w'] or held_keys['s'] or held_keys['a'] or held_keys['d']) and is_actually_moving:
        # Hareket durumuna göre hız
        is_sprinting = held_keys['left control'] or held_keys['right control']
        is_sneaking = held_keys['left shift'] or held_keys['right shift']
        
        step_freq = 0.35
        if is_sprinting: step_freq = 0.25
        if is_sneaking: step_freq = 0.5
        
        step_timer += time.dt
        if step_timer >= step_freq:
            # Karakterin altındaki bloğu tespit et
            bx, by, bz = int(player.x), int(player.y - 1.1), int(player.z)
            under = world_data.get((bx, by, bz))
            
            vol = 0.6 if not is_sprinting else 0.8
            if is_sneaking: vol = 0.2 # Gizlice yürüme butonu
            
            # Materyale göre ses seç
            if under in ['stone', 'coal_ore', 'iron_ore', 'diamond_ore', 'bedrock']:
                play_block_sound('break', volume=vol * 0.4) # Taş sesi için break (tok ses)
            elif under in ['wood', 'log', 'crafting_table']:
                play_block_sound('place', volume=vol * 0.7) # Ahşap sesi için place (ahşap sesi)
            else:
                play_block_sound('step', volume=vol) # Çimen/Toprak - walk.wav
                
            step_timer = 0
    else:
        step_timer = 0.3 

    # Envanter Seçimi
    current_held_item = inventory.get_selected_item()
    
    # Seçim değiştiyse güncelle
    if current_held_item != getattr(update, 'last_item', 'none_sentinel'):
        hand_entity.update_visuals(current_held_item)
        
        if current_held_item:
            tr_name = item_names.get(current_held_item, current_held_item.capitalize())
            item_name_display.show_text(tr_name)
        
        update.last_item = current_held_item
    
    # Bir blok tutup tutmadığını belirle (yerleştirme için)
    # Eğer elimiz boşsa veya tool varsa 'grass' varsayılan blok olmamalı, yerleştirme yapamamalıyız
    # Ama kodda basitleştirmek için:
    current_block = current_held_item if (current_held_item and current_held_item in blocks) else None
    
    # Yeniden Canlanma (Boşluğa düşme)
    if player.y < -30:
        player.position = find_safe_spawn_position()
        print(f"[RESPAWN] Boşluktan kurtarıldınız: {player.position}")
        
    # --- FARE ETKİLEŞİM MANTIĞI (GELİŞTİRİLMİŞ) ---
    # Menüler açıksa hiçbir şey yapma
    if inventory.is_open or crafting_system.visible:
        mining_progress = 0
        target_block = None
        return
    
    # --- YUMURTA FIRLATMA VE YEMEK YEME (Her zaman çalışır - bloğa bakmaya gerek yok) ---
    if held_keys['right mouse']:
        current_item = inventory.get_selected_item()
        
        # Yumurta fırlatma
        if current_item == 'egg':
            if time.time() - last_action_time > 0.2:
                throw_egg()
                inventory.use_selected_item()
                last_action_time = time.time()
            # Yumurta fırlattıktan sonra geri dön (diğer sağ tık işlemlerini atla)
            return
        
        # Yemek yeme (basılı tutma - Minecraft tarzı)
        elif current_item and current_item in items:
            item_data = items[current_item]
            if item_data.get('type') == 'food':
                # Yemek yeme başlat/devam ettir
                if not hasattr(update, 'eating'):
                    update.eating = False
                    update.eating_timer = 0
                    update.eating_item = None
                    update.eating_sound_played = False
                    update.eating_crunch_timer = 0
                
                if not update.eating:
                    # Yemek yemeye başla
                    if player_stats.current_hunger < player_stats.max_hunger:
                        update.eating = True
                        update.eating_timer = 0
                        update.eating_item = current_item
                        update.eating_sound_played = False
                        update.eating_crunch_timer = 0
                        start_eating_animation(current_item)
                        
                        # Yemek yeme sesini hemen başlat
                        play_block_sound('eat', volume=0.8)
                        update.eating_sound_played = True
                    else:
                        return
                else:
                    # Yemek yeme devam ediyor
                    update.eating_timer += time.dt
                    update.eating_crunch_timer += time.dt
                    
                    # Her 0.3 saniyede bir çiğneme sesi (Minecraft tarzı)
                    if update.eating_crunch_timer >= 0.3:
                        play_block_sound('step', volume=0.25)
                        update.eating_crunch_timer = 0
                        
                        # Parçacık efekti (her çiğnemede)
                        if random.random() < 0.6:  # %60 ihtimal
                            create_eating_particles(current_item)
                    
                    # 1.5 saniye sonra yemek yenmiş olur
                    if update.eating_timer >= 1.5:
                        hunger_restore = item_data.get('hunger_restore', 20)
                        player_stats.eat_food(hunger_restore)
                        inventory.use_selected_item()
                        
                        # Son bir çiğneme sesi
                        play_block_sound('step', volume=0.4)
                        
                        # 3. Şahıs Animasyonunu Tetikle
                        if 'player_model' in globals() and player_model:
                            player_model.trigger_eat()
                        
                        # Sıfırla
                        update.eating = False
                        update.eating_timer = 0
                        update.eating_item = None
                        update.eating_sound_played = False
                        update.eating_crunch_timer = 0
                
                # Yemek yerken diğer işlemleri yapma
                return
    else:
        # Sağ tık bırakıldığında yemek yemeyi iptal et
        if hasattr(update, 'eating') and update.eating:
            update.eating = False
            update.eating_timer = 0
            update.eating_item = None
            update.eating_sound_played = False
            update.eating_crunch_timer = 0
            
            # El animasyonunu sıfırla
            if 'hand_entity' in globals() and hand_entity:
                hand_entity.animate_position(Vec3(0.35, -0.25, 0.5), duration=0.2)
                hand_entity.animate_rotation(Vec3(0, 0, 0), duration=0.2)

    # --- HEDEF BELİRLEME (RAYCAST) ---
    # Hayvanlar ve Bloklar için mesafe kontrolü
    ray = raycast(camera.world_position, camera.forward, distance=5, ignore=(player,))
    
    hit_info = ray.entity
    hit_point = ray.point
    hit_normal = ray.normal
    
    # Hayvan Kontrol Fonksiyonu (Parent ağacını tara)
    def find_animal(entity):
        if not entity: return None
        if isinstance(entity, Animal): return entity
        # Uzuvları veya görselleri vurduysak üst kategoriye git
        if hasattr(entity, 'parent'):
            p = entity.parent
            if isinstance(p, Animal): return p
            if hasattr(p, 'parent') and isinstance(p.parent, Animal): return p.parent
        return None

    target_animal = find_animal(hit_info)
    
    # Ekstra Hassasiyet: mouse.hovered_entity kontrolü (Bazen raycast kaçırabiliyor)
    if not target_animal and mouse.hovered_entity:
        target_animal = find_animal(mouse.hovered_entity)
        if target_animal:
            # Mesafe kontrolü
            dist = (target_animal.position - player.position).length()
            if dist > 5: target_animal = None
            else:
                hit_info = target_animal
                hit_point = mouse.world_point if mouse.world_point else target_animal.position

    is_animal = target_animal is not None
    if is_animal: hit_info = target_animal

    is_world = hit_info and not is_animal and (isinstance(hit_info, Chunk) or 
                            hit_info.parent == passable_world or 
                            (hasattr(hit_info, 'parent') and isinstance(hit_info.parent, Chunk)))

    if hit_info and (is_animal or is_world):
        # --- SEÇİM KUTUSU GÜNCELLEME ---
        if is_world and hit_point:
            l_vec = hit_point - hit_normal * 0.1
            abx, aby, abz = math.floor(l_vec.x), math.floor(l_vec.y), math.floor(l_vec.z)
            if 'selection_box' in globals():
                selection_box.position = Vec3(abx + 0.5, aby + 0.5, abz + 0.5)
                selection_box.enabled = True
        elif 'selection_box' in globals():
             selection_box.enabled = False

        # --- KIRMA / SALDIRMA (Left Click) ---
        if held_keys['left mouse']:
            hand_entity.swing()
            
            if is_animal:
                # Hayvana vur - Cooldown 0.3 saniyeye düşürüldü (daha seri vuruş)
                if time.time() - last_action_time > 0.3:
                    damage = get_player_damage(current_held_item)
                    hit_info.take_damage(damage)
                    last_action_time = time.time()
                    
                    # Premium Vuruş Efekti
                    if 'sword' in str(current_held_item):
                        a_path = 'assets/sounds/player/attack.wav'
                        Audio(a_path, volume=0.8).play() if os.path.exists(a_path) else play_block_sound('swing', volume=0.8)
                        # Kritik Yıldızlar
                        spawn_collect_particle(hit_point if hit_point else hit_info.position, tint=color.yellow)
                    else:
                        play_block_sound('swing', volume=0.5)
            elif is_world and hit_point:
                # Blok kırma mantığı
                target_pos_vec = hit_point - hit_normal * 0.1
                tx, ty, tz = math.floor(target_pos_vec.x), math.floor(target_pos_vec.y), math.floor(target_pos_vec.z)
                
                if (tx, ty, tz) in world_data:
                    block_type = world_data[(tx, ty, tz)]
                    required_break_time = get_break_time(block_type, current_held_item)
                    
                    if mining_progress == 0: target_block = (tx, ty, tz)
                    
                    if target_block == (tx, ty, tz):
                        mining_progress += time.dt
                        
                        # Kazma Sesi (Periyodik)
                        p_path = 'assets/sounds/player/pickaxe.wav'
                        if 'pickaxe' in str(current_held_item) and os.path.exists(p_path):
                            if not hasattr(update, 'mining_sound_timer'): update.mining_sound_timer = 0
                            update.mining_sound_timer += time.dt
                            if update.mining_sound_timer >= 0.4:
                                Audio(p_path, volume=0.5).play()
                                update.mining_sound_timer = 0
                        
                        if mining_progress >= required_break_time and required_break_time != float('inf'):
                            # --- VEIN MINER (TIMBER) MANTIĞI ---
                            is_shift = held_keys['shift'] or held_keys['left shift'] or held_keys['right shift']
                            
                            # Sadece kütükler için ve shift basılıyken tetikle (Kullanıcı isteği: yapraklar hariç)
                            if is_shift and block_type == 'log':
                                vein_mine_logic(Vec3(tx, ty, tz), block_type)
                            else:
                                spawn_particles(Vec3(tx+0.5, ty+0.5, tz+0.5), block_type)
                                break_block_logic(Vec3(tx, ty, tz))
                                
                            player_stats.current_hunger = max(0, player_stats.current_hunger - 0.3)
                            player_stats.on_block_mined()
                            mining_progress = 0
                            target_block = None
                    else:
                        mining_progress = 0
                        target_block = None
            
        # --- ETKİLEŞİM / YERLEŞTİRME (Sağ Tık) ---
        elif held_keys['right mouse']:
            mining_progress = 0
            target_block = None
            
            if time.time() - last_action_time > 0.2:
                if is_animal:
                    hit_info.interact()
                    last_action_time = time.time()
                elif is_world and hit_point:
                    # Crafting Table kontrolü
                    look_pos_vec = hit_point - hit_normal * 0.1
                    lx, ly, lz = math.floor(look_pos_vec.x), math.floor(look_pos_vec.y), math.floor(look_pos_vec.z)
                    
                    if (lx, ly, lz) in world_data and world_data[(lx, ly, lz)] == 'crafting_table':
                        crafting_system.open()
                        last_action_time = time.time()
                    # Yerleştirme
                    elif current_block and inventory_counts.get(current_block, 0) > 0:
                        target_pos_vec = hit_point + hit_normal * 0.1
                        tx, ty, tz = math.floor(target_pos_vec.x), math.floor(target_pos_vec.y), math.floor(target_pos_vec.z)
                        
                        # Oyuncuyla çakışma kontrolü
                        p_bx, p_by, p_bz = math.floor(player.x), math.floor(player.y), math.floor(player.z)
                        if not ((tx == p_bx and tz == p_bz and ty == p_by) or
                                (tx == p_bx and tz == p_bz and ty == p_by + 1)):
                            hand_entity.swing()
                            place_block_logic(Vec3(tx, ty, tz), current_block)
                            inventory.use_selected_item()
                            last_action_time = time.time()
        else:
            mining_progress = 0
            target_block = None
    else:
        # Hiçbir şeye bakmıyorsak sıfırla
        mining_progress = 0
        target_block = None
        if 'selection_box' in globals():
            selection_box.enabled = False
    
    if target_block and target_block in world_data:
        block_type = world_data[target_block]
        max_time = get_break_time(block_type, current_held_item)
        if max_time == float('inf'): max_time = 10
        mining_progress_bar.update_progress(mining_progress, max_time=max_time)
        # Blok kırma göstergesi
        block_indicator.show(target_block, mining_progress / max_time)
            
    else:
        mining_progress_bar.update_progress(0, max_time=0.25)
        block_indicator.enabled = False

    processed_count = 0
    while mesh_callback_queue and processed_count < 5:
        chunk, verts, uvs, p_verts, p_uvs = mesh_callback_queue.popleft()
        if chunk and chunk.enabled is not None:
            chunk.assign_mesh(verts, uvs, p_verts, p_uvs)
        processed_count += 1
        
    cull_chunks()

# --- GENEL GİRİŞLER (INPUT) ---
# ============================================
# INPUT SİSTEMİ - OYUN KONTROL YÖNETİCİSİ
# ============================================
# Bu fonksiyon tüm klavye ve fare girişlerini yönetir.
# Kategoriler:
# 1. Kamera Kontrolleri (Mouse 4/5)
# 2. Sistem Kontrolleri (F2-F12)
# 3. Oyun Mekanikleri (E, F, Q)
# 4. Geliştirici Araçları (R, N, V, U, T)
# ============================================

def input(key):
    """
    Ana input yönetim fonksiyonu - Tüm tuş basışlarını işler
    
    Kategoriler:
    - Kamera: Mouse4 (karakter), Mouse5 (görünüm)
    - Ekran: F2 (screenshot)
    - Debug: F3 (performans), F4 (chunk)
    - Zaman: F6-F12 (gün/gece kontrolleri)
    - Hava: R (yağmur), N (hava durumu), V (bilgi)
    - Oyun: E (envanter), F (yemek), Q (at)
    - Test: U (parçacık), T (zaman)
    """
    global camera_mode, current_character_type, player_model
    
    # ============================================
    # KAMERA VE KARAKTER KONTROLLERİ
    # ============================================
    
    # Mouse 5: Kamera Görünüm Modu (1. Şahıs / 3. Şahıs Arka / 3. Şahıs Ön)
    if key == 'mouse5':
        camera_mode = (camera_mode + 1) % 3
        
        # Kamera Geçiş Animasyon Ayarları
        duration = 0.2
        curve_type = curve.out_sine
        
        # Modları Uygula
        if camera_mode == 0: # Birinci Şahıs
            camera.animate_position((0, 0, 0), duration=duration, curve=curve_type)
            camera.animate_rotation((0, 0, 0), duration=duration, curve=curve_type)
            # Birinci şahsa geçerken modeli hemen gizle
            invoke(setattr, player_model, 'enabled', False, delay=duration)
            if 'hand_entity' in globals(): hand_entity.enabled = True
            if 'crosshair' in globals(): crosshair.enabled = True
            print("[CAMERA] Birinci Şahıs Modu")
            
        elif camera_mode == 1: # Üçüncü Şahıs (Arka)
            player_model.enabled = True
            camera.animate_position((0, 1, -5), duration=duration, curve=curve_type)
            camera.animate_rotation((0, 0, 0), duration=duration, curve=curve_type)
            if 'hand_entity' in globals(): hand_entity.enabled = False
            if 'crosshair' in globals(): crosshair.enabled = False
            print("[CAMERA] Üçüncü Şahıs (Arka) Modu")
            
        elif camera_mode == 2: # Üçüncü Şahıs (Ön)
            player_model.enabled = True
            camera.animate_position((0, 1, 5), duration=duration, curve=curve_type)
            camera.animate_rotation((0, 180, 0), duration=duration, curve=curve_type)
            if 'hand_entity' in globals(): hand_entity.enabled = False
            if 'crosshair' in globals(): crosshair.enabled = False
            print("[CAMERA] Üçüncü Şahıs (Ön) Modu")
    
    # Mouse 4: Karakter Değiştirme (Steve <-> Alex)
    elif key == 'mouse4':
        # Hedeflenen yeni karakteri belirle
        target_char = 'alex' if current_character_type == 'steve' else 'steve'
        target_theme = color.orange if target_char == 'alex' else color.azure
        
        # --- 1. EFEKTLER (VFX & SFX) ---
        play_block_sound('place', volume=0.8)
        
        # Partikül Patlaması
        if hasattr(player, 'position'):
            for _ in range(25):
                p = Entity(
                    model='quad',
                    texture='assets/textures/ui/star.png',
                    color=target_theme,
                    scale=random.uniform(0.05, 0.15),
                    position=player.position + Vec3(0, 1.2, 0) + Vec3(random.uniform(-0.3,0.3), random.uniform(-0.5,0.5), random.uniform(-0.3,0.3)),
                    billboard=True,
                    always_on_top=False
                )
                if p.texture is None: p.model = 'circle'
                
                # Patlama Hareketi
                offset = Vec3(random.uniform(-1.5, 1.5), random.uniform(-0.5, 1.5), random.uniform(-1.5, 1.5))
                p.animate_position(p.position + offset, duration=0.6, curve=curve.out_expo)
                p.animate_scale(0, duration=0.6)
                p.animate_color(color.clear, duration=0.6)
                destroy(p, delay=0.7)

        # --- 2. MODEL DEĞİŞİMİ ---
        player_model.enabled = False
        
        if target_char == 'alex':
            current_character_type = 'alex'
            player_model = alex_model
            print("[KARAKTER] Alex seçildi (Slim Arms)")
        else:
            current_character_type = 'steve'
            player_model = steve_model
            print("[KARAKTER] Steve seçildi (Classic)")
            
        # Kamera 3. şahıstaysa yeni modeli göster
        if camera_mode != 0:
            player_model.enabled = True
        
        # Anlık büyüme animasyonu (Pop effect)
        player_model.scale = 0.8
        player_model.animate_scale(1, duration=0.3, curve=curve.out_back)

        # --- 3. PREMIUM BİLDİRİM UI (V3) ---
        for e in camera.ui.children:
            if getattr(e, 'is_char_notif', False): 
                e.active = False
                destroy(e)
            
        char_display_name = target_char.upper()
        sub_text_display = "SLIM MODEL" if target_char == 'alex' else "CLASSIC MODEL"

        # Ana Konteyner
        container = Entity(parent=camera.ui, position=(0, 0.45), is_char_notif=True, active=True, z=-200) 
        
        # Arkaplan Paneli
        bg = Entity(
            parent=container,
            model='quad',
            scale=(0.55, 0.14),
            color=color.rgba(15, 18, 25, 0.95),
            texture='assets/textures/ui/button_bg.png' if os.path.exists('assets/textures/ui/button_bg.png') else None
        )
        
        # Avatar Kutusu
        avatar_bg = Entity(
            parent=container,
            model='quad',
            scale=(0.1, 0.1),
            position=(-0.18, 0),
            color=color.rgba(255, 255, 255, 0.1)
        )
        
        # Avatar
        avatar_letter = Text(
            parent=avatar_bg,
            text=char_display_name[0],
            origin=(0, 0),
            scale=4,
            color=target_theme,
            font='assets/fonts/consola.ttf'
        )
        
        # Yazı Grubu
        text_group = Entity(parent=container, position=(0.02, 0))
        
        title = Text(
            parent=text_group,
            text=char_display_name,
            origin=(-0.5, 0),
            position=(-0.12, 0.025),
            scale=2.2,
            font='assets/fonts/consola.ttf',
            color=target_theme
        )
        
        desc = Text(
            parent=text_group,
            text=sub_text_display,
            origin=(-0.5, 0),
            position=(-0.12, -0.025),
            scale=0.9,
            color=color.light_gray
        )
        
        # Progress Bar
        bar = Entity(
            parent=container,
            model='quad',
            scale=(0.55, 0.004),
            position=(0, -0.068),
            color=target_theme
        )
        bar.animate_scale_x(0, duration=2.5)

        # Giriş Animasyonu
        container.y += 0.1
        container.animate_y(0.45, duration=0.4, curve=curve.out_expo)
        container.scale = 0.8
        container.animate_scale(1, duration=0.4, curve=curve.out_back)
        
        # Çıkış Animasyonu
        def close_notif():
            if not getattr(container, 'active', False): return
            try:
                container.animate_y(container.y + 0.2, duration=0.3, curve=curve.in_quad)
                container.animate_scale(0, duration=0.3)
                destroy(container, delay=0.4)
            except: pass
            
        invoke(close_notif, delay=2.5)
    
    # ============================================
    # SİSTEM KONTROLLERİ (EKRAN GÖRÜNTÜSÜ)
    # ============================================
    
    # F2: Ekran Görüntüsü Al
    elif key == 'f2':
        if not os.path.exists('screenshots'):
            os.makedirs('screenshots')
        
        timestamp = time.strftime("%Y-%m-%d_%H-%M-%S")
        name = f'screenshots/{timestamp}'
        base.screenshot(namePrefix=name)
        
        # Premium Bildirim UI
        notify_ui = Entity(parent=camera.ui, position=(0, 0.55), z=-200)
        
        # Gölge
        Entity(
            parent=notify_ui, 
            model='quad', 
            scale=(0.62, 0.13), 
            color=color.rgba(0, 0, 0, 0.5), 
            position=(0.005, -0.005),
            z=0.1
        )
        
        # Ana Panel
        bg = Entity(
            parent=notify_ui, 
            model='quad', 
            scale=(0.6, 0.11), 
            color=color.rgba(20/255, 25/255, 30/255, 0.95), 
            z=0
        )
        
        # Glass Border
        Entity(
            parent=bg,
            model='quad',
            scale=(1.005, 1.04),
            color=color.rgba(255, 255, 255, 0.15),
            z=0.01
        )
        
        # Progress Bar
        progress_bar = Entity(
            parent=bg, 
            model='quad', 
            scale=(1, 0.03), 
            origin=(-0.5, 0),
            position=(-0.5, -0.485, -0.01),
            color=color.rgba(0, 1, 1, 1) 
        )
        progress_bar.animate_scale_x(0, duration=3.0, curve=curve.linear)
        
        # Başlık
        Text(
            parent=notify_ui,
            text='GÖRÜNTÜ YAKALANDI',
            origin=(0, 0),
            position=(0, 0.02),
            scale=1.2,
            color=color.cyan,
            z=-0.1
        )
        
        # Dosya Adı
        Text(
            parent=notify_ui,
            text=f"{name}.png",
            origin=(0, 0),
            position=(0, -0.025),
            scale=0.8,
            color=color.white,
            z=-0.1
        )
        
        # Animasyon
        notify_ui.animate_position((0, 0.40), duration=0.5, curve=curve.out_back)
        
        def close_notify():
            notify_ui.animate_position((0, 0.55), duration=0.5, curve=curve.in_back)
            destroy(notify_ui, delay=0.5)
            
        invoke(close_notify, delay=3.0)
        
        print(f'[EKRAN GÖRÜNTÜSÜ] Kaydedildi: {name}')
    
    # ============================================
    # DEBUG VE PERFORMANS KONTROLLERİ
    # ============================================
    
    # F3: Performans Monitörü (Motor Analizi)
    elif key == 'f3':
        # Shift+F3: Detaylı Mod
        if held_keys['shift'] or held_keys['left shift']:
            debug_overlay.detailed = not debug_overlay.detailed
            debug_overlay.enabled = True
        # Ctrl+F3: Metrikleri Sıfırla
        elif held_keys['control'] or held_keys['left control']:
            debug_overlay.reset_metrics()
        # Alt+F3: Benchmark Başlat (30sn)
        elif held_keys['alt'] or held_keys['left alt']:
            debug_overlay.start_benchmark(30)
        # Sadece F3: Aç/Kapat
        else:
            debug_overlay.enabled = not debug_overlay.enabled
            
        global show_hitboxes
        show_hitboxes = debug_overlay.enabled
        
        # Sahnedeki tüm hayvan ve item hitboxlarını güncelle
        for a in animals:
            if hasattr(a, 'hitbox_visual'): a.hitbox_visual.enabled = show_hitboxes
            if hasattr(a, 'debug_info'): a.debug_info.enabled = show_hitboxes
        for i in dropped_items:
            if hasattr(i, 'hitbox_visual'): i.hitbox_visual.enabled = show_hitboxes
    
    # F4: Chunk Debugger
    elif key == 'f4':
        chunk_visualizer.toggle()
    
    # Chunk Debugger Aktifken Ek Kontroller
    if chunk_visualizer.enabled:
        if key in ['1', '2', '3', '4']:
            chunk_visualizer.set_mode(int(key))
        elif key == '+':
            chunk_visualizer.view_distance = min(10, chunk_visualizer.view_distance + 1)
            chunk_visualizer.refresh()
        elif key == '-':
            chunk_visualizer.view_distance = max(1, chunk_visualizer.view_distance - 1)
            chunk_visualizer.refresh()
        elif key == 'i':
            chunk_visualizer.show_info = not chunk_visualizer.show_info
            chunk_visualizer.info_panel.enabled = chunk_visualizer.show_info
            chunk_visualizer.refresh()
        elif key == 'delete':
            chunk_visualizer.unload_chunk()
        elif key == 'home':
            chunk_visualizer.force_reload()
    
    # ============================================
    # ZAMAN VE GÜN/GECE DÖNGÜSÜ KONTROLLERİ
    # ============================================
    
    elif key == 'f6':  # Saat -1
        day_night_cycle.subtract_hours(1)
    elif key == 'f7':  # Hız x2
        day_night_cycle.set_speed(2.0)
    elif key == 'f8':  # Hız x10
        day_night_cycle.set_speed(10.0)
    elif key == 'f9':  # Duraklat/Devam
        day_night_cycle.toggle_pause()
    elif key == 'f10':  # Hız sıfırla (normal)
        day_night_cycle.set_speed(1.0)
    elif key == 'f11':  # Gece 22:00 (karanlık test)
        day_night_cycle.set_time(22, 0)
    elif key == 'f12':  # Sabah 06:00
        day_night_cycle.set_time(6, 0)
    elif key == 't':  # Mevcut zamanı göster
        day_night_cycle.print_current_time()
    
    # ============================================
    # HAVA DURUMU VE YAĞMUR SİSTEMİ
    # ============================================
    
    # R: Yağmuru Aç/Kapat
    elif key == 'r':
        rain_system.toggle_rain()
        print(f"[YAĞMUR] Durum: {'Açık' if rain_system.is_raining else 'Kapalı'}")
    
    # N: Hava Durumu Değiştir
    elif key == 'n':
        weather_cycle = ['clear', 'cloudy', 'overcast', 'rainy', 'stormy']
        current_weather = rain_system.weather_type
        try:
            current_index = weather_cycle.index(current_weather)
            next_weather = weather_cycle[(current_index + 1) % len(weather_cycle)]
        except ValueError:
            next_weather = weather_cycle[0]
        
        rain_system.set_weather(next_weather)
        
        # Türkçe isimler
        weather_names = {
            'clear': 'Açık',
            'cloudy': 'Bulutlu', 
            'overcast': 'Kapalı',
            'rainy': 'Yağmurlu',
            'stormy': 'Fırtınalı'
        }
        print(f"[HAVA DURUMU] {weather_names.get(next_weather, next_weather)}")
    
    # V: Yağmur/Hava Durumu Bilgisi
    elif key == 'v':
        info = rain_system.get_rain_info()
        print("=" * 50)
        print("[YAĞMUR SİSTEMİ BİLGİLERİ]")
        print(f"Yağmur Durumu: {'Yağıyor' if info['is_raining'] else 'Yağmıyor'}")
        if info['is_raining']:
            print(f"Yağmur Türü: {info['rain_type'].title()}")
            print(f"Damla Sayısı: {info['particle_count']}/{info['max_particles']}")
            
            rain_data = rain_system.rain_types.get(info['rain_type'], {})
            if rain_data:
                print(f"Hız: {rain_data['speed']}")
                print(f"Ses Seviyesi: %{int(rain_data.get('volume', 0.6) * 100)}")
        print(f"Hava Durumu: {info['weather_type'].title()}")
        print("=" * 50)
    
    # ============================================
    # TEST VE GELİŞTİRİCİ ARAÇLARI
    # ============================================
    
    # U: Test Parçacığı Oluştur
    elif key == 'u':
        print(f"[TEST] U tuşuna basıldı - Test parçacığı oluşturuluyor!")
        player_pos = player.position if 'player' in globals() else Vec3(0, 0, 0)
        
        # Oyuncunun önünde test parçacığı
        test_particle = Entity(
            model='cube',
            color=color.red,  # Kırmızı test parçacığı
            scale=(2, 2, 2),  # Büyük boyut
            position=player_pos + Vec3(0, 10, 10),  # Oyuncunun önünde ve yukarısında
            parent=scene
        )
        
        print(f"[TEST] Test parçacığı oluşturuldu: {test_particle.position}")
        
        # 5 saniye sonra sil
        destroy(test_particle, delay=5)
    
    
    # T: Mevcut Zamanı Konsola Yazdır
    elif key == 't':
        day_night_cycle.print_current_time()
    
    # ============================================
    # OYUN MEKANİKLERİ (ENVANTER, YEMEK, EŞYA)
    # ============================================
    
    # E: Envanter Aç/Kapat
    if key == 'e':
        # Crafting açıksa onu kapat
        if crafting_system.visible:
            crafting_system.close()
        # Envanter açıksa onu kapat, kapalıysa aç
        inventory.toggle()
    
    # ============================================
    # CRAFTING SİSTEMİ
    # ============================================
    
    # Üretim (Crafting) menüsü girişi (ESC için)
    if crafting_system.visible:
        crafting_system.input(key)


# ============================================
# OYUN BAŞLATMA - NESNE OLUŞTURMA
# ============================================
inventory = Inventory()
# Başlangıç aletlerini ver
start_tools = [
    'diamond_sword',
    'diamond_pickaxe',
    'diamond_axe',
    'diamond_shovel',
    'shears'
]
for t in start_tools:
    inventory.add_item(t, 1)

# Başlangıç yemekleri ve materyalleri (Deneme kolaylığı için)
testing_items = [
    ('chicken_cooked', 16),
    ('egg', 16)
]
for item, count in testing_items:
    inventory.add_item(item, count)

hand_entity = Hand()
mining_progress_bar = MiningProgressBar()
health_bar = HealthBar()
hunger_bar = HungerBar()
player_stats = PlayerStats()
damage_flash = DamageFlash()
crosshair = Crosshair()
debug_overlay = PerformanceMonitor()
chunk_visualizer = ChunkDebugger()
item_name_display = ItemNameDisplay()

app.run()
