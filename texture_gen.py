# -*- coding: utf-8 -*-
"""
PyCraft Doku Üretici
Bu betik, oyun için gerekli tüm dokuları (texture) prosedürel olarak oluşturur.
Blok dokuları, UI elementleri, varlık dokuları ve efekt dokuları üretilir.
"""

from PIL import Image, ImageDraw
import random
import os
import math

# Temel aset dizinlerini tanımla
ASSETS_DIR = 'assets'
BLOCKS_DIR = os.path.join(ASSETS_DIR, 'textures/blocks')  # Blok dokuları
BREAK_DIR = os.path.join(BLOCKS_DIR, 'break')  # Blok kırılma animasyonları
ITEMS_DIR = os.path.join(ASSETS_DIR, 'textures/items')  # Eşya dokuları
UI_DIR = os.path.join(ASSETS_DIR, 'textures/ui')  # Kullanıcı arayüzü dokuları
ENTITIES_DIR = os.path.join(ASSETS_DIR, 'textures/entities')  # Varlık (mob) dokuları

# Gerekli klasörlerin varlığını kontrol et ve yoksa oluştur
for d in [BLOCKS_DIR, BREAK_DIR, ITEMS_DIR, UI_DIR, ENTITIES_DIR]:
    if not os.path.exists(d):
        os.makedirs(d)

def create_bedrock_texture():
    """
    Katman kayası (Bedrock) dokusunu rastgele gürültü ile oluşturur.
    Bedrock kırılamaz bir bloktur ve koyu gri tonlarında görünür.
    """
    img = Image.new('RGB', (16, 16))  # 16x16 piksel RGB görüntü oluştur
    pixels = img.load()
    
    # Her piksel için rastgele koyu gri ton ata
    for x in range(16):
        for y in range(16):
            val = random.randint(0, 60)  # 0-60 arası koyu gri tonlar
            pixels[x, y] = (val, val, val)
    
    img.save(os.path.join(BLOCKS_DIR, 'bedrock.png'))

def create_ui_icons():
    """
    Can ve Açlık barı için kalp ve yemek ikonlarını oluşturur.
    Dolu ve boş versiyonları üretilir.
    """
    # Kalp şeklini oluşturan piksel koordinatları
    h_pixels = [(2,5),(3,5),(5,5),(6,5),(1,6),(2,6),(3,6),(4,6),(5,6),(6,6),(7,6),
                (1,7),(2,7),(3,7),(4,7),(5,7),(6,7),(7,7),(2,8),(3,8),(4,8),(5,8),(6,8),
                (3,9),(4,9),(5,9),(4,10)]
    
    # Dolu Kalp İkonu (Can barı için)
    heart = Image.new('RGBA', (16, 16), (0, 0, 0, 0))  # Şeffaf arka plan
    draw = ImageDraw.Draw(heart)
    for px in h_pixels:
        draw.point(px, fill=(255, 0, 0, 255))  # Kırmızı kalp
    heart.save(os.path.join(UI_DIR, 'heart_icon.png'))
    
    # Boş Kalp İkonu (Kaybedilen can için)
    heart_empty = Image.new('RGBA', (16, 16), (0, 0, 0, 0))
    draw_e = ImageDraw.Draw(heart_empty)
    for px in h_pixels:
        # Kenar pikselleri mi kontrol et
        is_edge = any((px[0]+dx, px[1]+dy) not in h_pixels for dx, dy in [(0,1),(0,-1),(1,0),(-1,0)])
        if is_edge:
            draw_e.point(px, fill=(60, 0, 0, 255))  # Koyu kırmızı kenar
        else:
            draw_e.point(px, fill=(40, 40, 40, 100))  # Yarı şeffaf iç
    heart_empty.save(os.path.join(UI_DIR, 'heart_empty.png'))
    
    # Yemek/Açlık şeklini oluşturan piksel koordinatları (et parçası şekli)
    f_pixels = [(8,4),(9,4),(10,4),(7,5),(8,5),(9,5),(10,5),(11,5),
                (6,6),(7,6),(8,6),(9,6),(10,6),(11,6),(6,7),(7,7),(8,7),(9,7),(10,7),
                (7,8),(8,8),(9,8)]
    
    # Dolu Açlık İkonu (Açlık barı için)
    hunger = Image.new('RGBA', (16, 16), (0, 0, 0, 0))
    draw = ImageDraw.Draw(hunger)
    for px in f_pixels:
        draw.point(px, fill=(139, 69, 19, 255))  # Kahverengi (et rengi)
    hunger.save(os.path.join(UI_DIR, 'hunger_icon.png'))
    
    # Boş Açlık İkonu (Kaybedilen açlık için)
    hunger_empty = Image.new('RGBA', (16, 16), (0, 0, 0, 0))
    draw_fe = ImageDraw.Draw(hunger_empty)
    for px in f_pixels:
        # Kenar pikselleri mi kontrol et
        is_edge = any((px[0]+dx, px[1]+dy) not in f_pixels for dx, dy in [(0,1),(0,-1),(1,0),(-1,0)])
        if is_edge:
            draw_fe.point(px, fill=(40, 20, 5, 255))  # Koyu kahverengi kenar
        else:
            draw_fe.point(px, fill=(30, 30, 30, 100))  # Yarı şeffaf iç
    hunger_empty.save(os.path.join(UI_DIR, 'hunger_empty.png'))

def create_vignette():
    """
    Hasar alındığında ekranda beliren kırmızı kenarlık efektini (vignette) oluşturur.
    Merkezden kenarlara doğru kırmızı renk yoğunluğu artar.
    """
    img = Image.new('RGBA', (64, 64), (0, 0, 0, 0))  # 64x64 şeffaf görüntü
    
    for x in range(64):
        for y in range(64):
            # Merkezden uzaklığı hesapla (normalize edilmiş)
            dist = math.sqrt(((x-31.5)/32)**2 + ((y-31.5)/32)**2)
            
            # Merkez bölge şeffaf, kenarlara doğru kırmızı
            if dist > 0.4:
                # Uzaklığa göre alpha değerini hesapla
                alpha = int(min(1.0, (dist-0.4)*1.5)*180)
                img.putpixel((x, y), (255, 0, 0, alpha))  # Kırmızı, değişken şeffaflık
    
    img.save(os.path.join(UI_DIR, 'damage_vignette.png'))

def create_hand_texture():
    """
    Oyuncu elinin (Steve kolu) dokusunu oluşturur.
    Ten rengi ve mavi gömlek kolu içerir.
    """
    img = Image.new('RGBA', (16, 16), (197, 137, 110, 255))  # Ten rengi ile başla
    pixels = img.load()
    
    # Ten rengi varyasyonları
    skin = [(197, 137, 110), (219, 161, 131), (161, 102, 76)]
    
    # Ten dokusuna rastgele varyasyon ekle
    for x in range(16):
        for y in range(16):
            if random.random() < 0.2:
                c = random.choice(skin)
            else:
                # Mevcut piksele hafif gürültü ekle
                c = tuple(max(0, min(255, v+random.randint(-5, 5))) for v in pixels[x,y][:3])
            pixels[x, y] = c + (255,)
    
    # Mavi gömlek kolu (alt kısım)
    cyan = [(0, 135, 148), (0, 160, 176), (0, 190, 204)]
    for x in range(16):
        for y in range(10, 16):  # Alt 6 piksel
            c = random.choice(cyan)
            n = random.randint(-8, 8)  # Gürültü
            pixels[x, y] = tuple(max(0, min(255, v+n)) for v in c) + (255,)
        # Gömlek kenarını koyulaştır
        pixels[x, 10] = tuple(max(0, v-30) for v in pixels[x,10][:3]) + (255,)
    
    img.save(os.path.join(UI_DIR, 'hand.png'))

def create_break_textures():
    """
    Blok kırma aşamalarını (çatlaklar) 10 kademeli olarak oluşturur.
    Stage 0: Hafif çatlak, Stage 9: Tamamen parçalanmış
    """
    # Çatlak piksellerini önceden bir "büyüme rotası" olarak belirle
    crack_pixels = []
    
    # 6 farklı başlangıç noktasından çatlaklar başlat
    seeds = [(random.randint(2, 13), random.randint(2, 13)) for _ in range(6)]
    
    for sx, sy in seeds:
        cx, cy = sx, sy
        # Her daldan 30 piksel potansiyeli
        for _ in range(30):
            if (cx, cy) not in crack_pixels:
                crack_pixels.append((cx, cy))
            
            # Rastgele bir yöne ilerle (8 yön)
            dx, dy = random.choice([(0,1),(0,-1),(1,0),(-1,0),(1,1),(-1,-1),(1,-1),(-1,1)])
            cx, cy = max(0, min(15, cx+dx)), max(0, min(15, cy+dy))

    # 10 farklı kırılma aşaması oluştur
    for stage in range(10):
        img = Image.new('RGBA', (16, 16), (0, 0, 0, 0))  # Şeffaf arka plan
        pixels = img.load()
        
        # Bu aşamada kaç pikselin aktif olacağını hesapla (lineer artış)
        limit = int(len(crack_pixels) * ((stage + 1) / 10))
        alpha = min(255, 130 + (stage * 13))  # Stage ilerledikçe koyulaşır
        
        for i in range(limit):
            px, py = crack_pixels[i]
            # Ana çatlak hattı
            pixels[px, py] = (0, 0, 0, alpha)
            
            # Stage 5'ten sonra çatlakların etrafına "çapak" ve kalınlık ekle
            if stage > 4:
                for dx, dy in [(0,1), (1,0), (0,-1), (-1,0)]:
                    nx, ny = px+dx, py+dy
                    if 0 <= nx < 16 and 0 <= ny < 16:
                        prob = 0.2 if stage < 8 else 0.4
                        if random.random() < prob:
                            old_a = pixels[nx, ny][3]
                            pixels[nx, ny] = (0, 0, 0, max(old_a, alpha // 2))

        img.save(os.path.join(BREAK_DIR, f'break_{stage}.png'))

def create_atlas():
    """
    Tüm blok dokularını tek bir atlas dosyasında birleştirir.
    Chunk sistemi için gereklidir - GPU'ya tek seferde yüklenir.
    """
    # Atlas'a dahil edilecek blok dokuları (sıralı)
    mapping = [
        'grass', 'grass_top', 'dirt', 'stone', 'wood', 'log', 'log_top', 
        'leaves', 'bedrock', 'crafting_table', 'crafting_table_top', 
        'crafting_table_front', 'coal_ore', 'iron_ore', 'diamond_ore', 'wool'
    ]
    
    # Dikey olarak birleştirilmiş atlas oluştur (16 piksel genişlik, N*16 yükseklik)
    atlas = Image.new('RGB', (16, 16 * len(mapping)))
    
    for i, name in enumerate(mapping):
        path = os.path.join(BLOCKS_DIR, f'{name}.png')
        if os.path.exists(path):
            # Her dokuyu atlas'ın ilgili satırına yapıştır
            atlas.paste(Image.open(path), (0, i * 16))
    
    atlas.save(os.path.join(BLOCKS_DIR, 'atlas.png'))
    print(f"[ATLAS] {len(mapping)} doku birleştirildi: atlas.png oluşturuldu.")

def create_sheep_texture():
    """Koyun (Sheep) dokusunu oluşturur: Yün, deri ve yüz hatları."""
    # 64x32 Boyutunda şeffaf bir tuval oluştur
    img = Image.new('RGBA', (64, 32), (0, 0, 0, 0))
    pixels = img.load()
    
    # 1. Yün Dokusu (Body - 16x16 alan)
    # Konum: (0, 0) - (15, 15)
    wool_colors = [
        (139, 115, 85, 255), (120, 100, 75, 255), (100, 80, 60, 255), # Koyu ve orta kahverengi
        (230, 230, 230, 255), (245, 245, 245, 255), # Beyaz benekler
        (160, 140, 110, 255) # Açık kahverengi
    ]
    for x in range(16):
        for y in range(16):
            pixels[x, y] = random.choice(wool_colors)
            # Kenarlara hafif gölge ekle
            if x == 0 or x == 15 or y == 0 or y == 15:
                if random.random() < 0.5:
                    r, g, b, a = pixels[x, y]
                    pixels[x, y] = (max(0, r-20), max(0, g-20), max(0, b-20), 255)

    # 2. Deri Dokusu (Head & Legs - 8x8 ve 4x12 alanlar)
    # Head Base (16, 0) - (23, 7)
    skin_colors = [(240, 213, 213, 255), (230, 200, 200, 255), (250, 225, 225, 255)]
    for x in range(16, 24):
        for y in range(0, 8):
            pixels[x, y] = random.choice(skin_colors)
            
    # Legs (16, 8) - (19, 19)
    for x in range(16, 20):
        for y in range(8, 20):
            pixels[x, y] = random.choice(skin_colors)
            # Toynak (üstte veya altta - burada alt 3 piksel)
            if y > 16:
                pixels[x, y] = (100, 80, 80, 255) # Koyu toynak rengi

    # 3. Yüz Detayları (Overlay - 24, 0 - 31, 7)
    # Bu alan create_face() tarafından kullanılacak
    # Tamamen şeffaf taban üzerine sadece gözler ve burun
    for x in range(24, 32):
        for y in range(0, 8):
            # Şeffaf deri rengi (maske gibi)
            pixels[x, y] = (240, 213, 213, 255)
            
    # Gözler
    pixels[25, 2] = (255, 255, 255, 255); pixels[25, 3] = (0, 0, 0, 255) # Sol
    pixels[30, 2] = (255, 255, 255, 255); pixels[30, 3] = (0, 0, 0, 255) # Sağ
    
    # Burun / Ağız
    pixels[27, 5] = (255, 170, 170, 255)
    pixels[28, 5] = (255, 170, 170, 255)
    pixels[27, 6] = (220, 150, 150, 255)
    pixels[28, 6] = (220, 150, 150, 255)

    # 4. Kırkılmış (Shorn) Gövde Dokusu (0, 16 - 15, 31)
    # Bu alan yün gittiğinde görünecek pembe deri dokusudur
    shorn_skin_colors = [(245, 220, 220, 255), (235, 210, 210, 255), (250, 225, 225, 255)]
    for x in range(0, 16):
        for y in range(16, 32):
            pixels[x, y] = random.choice(shorn_skin_colors)
            # Hafif kırpılmış yün kalıntıları (beyaz benekler)
            if random.random() < 0.05:
                pixels[x, y] = (255, 255, 255, 255)
    pixels[28, 6] = (220, 150, 150, 255)

    img.save(os.path.join(ENTITIES_DIR, 'sheep.png'))
    print("[TEXTURE] Koyun dokusu oluşturuldu: sheep.png")

def create_pig_texture():
    """Domuz (Pig) dokusunu oluşturur: Pembe deri ve yüz hatları."""
    img = Image.new('RGBA', (64, 32), (0, 0, 0, 0))
    pixels = img.load()
    
    # 1. Deri/Vücut
    pig_pink = [(255, 170, 170, 255), (255, 150, 150, 255), (255, 180, 180, 255), (240, 140, 140, 255)]
    for x in range(64):
        for y in range(32):
            if random.random() < 0.8:
                pixels[x, y] = random.choice(pig_pink)
            else:
                c = random.choice(pig_pink)
                pixels[x, y] = (c[0]-20, c[1]-20, c[2]-20, 255)

    # Gözler
    pixels[1, 2] = (255, 255, 255, 255); pixels[1, 3] = (0, 0, 0, 255) # Sol
    pixels[6, 2] = (255, 255, 255, 255); pixels[6, 3] = (0, 0, 0, 255) # Sağ
    
    # Burun (Snout)
    for x in range(2, 6):
        for y in range(4, 7):
            pixels[x, y] = (255, 130, 130, 255)
    pixels[3, 5] = (200, 100, 100, 255); pixels[4, 5] = (200, 100, 100, 255)

    img.save(os.path.join(ENTITIES_DIR, 'pig.png'))
    print("[TEXTURE] Domuz dokusu oluşturuldu: pig.png")

def create_chicken_texture():
    """Tavuk (Chicken) dokusunu oluşturur: Beyaz tüyler, kırmızı ibik ve turuncu gaga - Minecraft tarzı 64x32."""
    img = Image.new('RGBA', (64, 32), (0, 0, 0, 0))
    pixels = img.load()
    
    # Renk paletleri
    white_feathers = [(255, 255, 255, 255), (245, 245, 245, 255), (250, 250, 250, 255)]
    white_shadow = [(220, 220, 220, 255), (210, 210, 210, 255)]
    red_crest = [(220, 20, 20, 255), (200, 0, 0, 255), (240, 40, 40, 255)]
    orange_beak = [(255, 165, 0, 255), (255, 140, 0, 255)]
    orange_legs = [(255, 140, 0, 255), (240, 130, 0, 255)]
    
    # ============================================
    # GÖVDE (Body) - 16x16 (0, 16) - (15, 31)
    # ============================================
    for x in range(0, 16):
        for y in range(16, 32):
            if random.random() < 0.9:
                pixels[x, y] = random.choice(white_feathers)
            else:
                pixels[x, y] = random.choice(white_shadow)
    
    # Gövde gölgelendirme (alt kısım)
    for x in range(0, 16):
        for y in range(28, 32):
            if random.random() < 0.5:
                pixels[x, y] = random.choice(white_shadow)
    
    # ============================================
    # KAFA (Head) - 8x8 (0, 0) - (7, 7)
    # ============================================
    for x in range(0, 8):
        for y in range(0, 8):
            pixels[x, y] = random.choice(white_feathers)
    
    # Gözler - Siyah noktalar
    # Sol göz
    pixels[1, 2] = (0, 0, 0, 255)
    pixels[2, 2] = (0, 0, 0, 255)
    pixels[1, 3] = (0, 0, 0, 255)
    pixels[2, 3] = (0, 0, 0, 255)
    
    # Sağ göz
    pixels[5, 2] = (0, 0, 0, 255)
    pixels[6, 2] = (0, 0, 0, 255)
    pixels[5, 3] = (0, 0, 0, 255)
    pixels[6, 3] = (0, 0, 0, 255)
    
    # Gaga - Turuncu (ortada, aşağıda)
    for x in range(2, 6):
        for y in range(4, 7):
            pixels[x, y] = random.choice(orange_beak)
    
    # Gaga ucu (koyu)
    for x in range(3, 5):
        pixels[x, 6] = (200, 100, 0, 255)
    
    # ============================================
    # İBİK (Crest) - Kırmızı tarak (8, 0) - (15, 7)
    # ============================================
    # Tarak şekli (dalgalı üst)
    crest_pattern = [
        (8,0),(9,0),(10,0),(11,0),(12,0),(13,0),(14,0),(15,0),
        (8,1),(9,1),(10,1),(11,1),(12,1),(13,1),(14,1),(15,1),
        (9,2),(10,2),(11,2),(12,2),(13,2),(14,2),
        (10,3),(11,3),(12,3),(13,3)
    ]
    
    for px, py in crest_pattern:
        pixels[px, py] = random.choice(red_crest)
    
    # Tarak gölgelendirme
    for x in range(10, 14):
        if pixels[x, 3][3] > 0:  # Eğer pixel doluysa
            pixels[x, 3] = (180, 0, 0, 255)
    
    # ============================================
    # SAKAL (Wattle) - Kırmızı sallantılar (16, 0) - (23, 7)
    # ============================================
    wattle_pattern = [
        (17,4),(18,4),(19,4),(20,4),
        (17,5),(18,5),(19,5),(20,5),
        (18,6),(19,6)
    ]
    
    for px, py in wattle_pattern:
        pixels[px, py] = random.choice(red_crest)
    
    # ============================================
    # BACAKLAR (Legs) - 4x12 (24, 0) - (31, 11)
    # ============================================
    for x in range(24, 32):
        for y in range(0, 12):
            pixels[x, y] = random.choice(orange_legs)
    
    # Bacak gölgelendirme (yan taraflar)
    for y in range(0, 12):
        pixels[24, y] = (200, 100, 0, 255)
        pixels[31, y] = (200, 100, 0, 255)
    
    # Pençe detayları (alt kısım)
    for x in range(24, 32):
        for y in range(9, 12):
            if random.random() < 0.4:
                pixels[x, y] = (180, 90, 0, 255)
    
    # ============================================
    # KANATLAR (Wings) - 8x12 (32, 0) - (47, 11)
    # ============================================
    for x in range(32, 48):
        for y in range(0, 12):
            if random.random() < 0.85:
                pixels[x, y] = random.choice(white_feathers)
            else:
                pixels[x, y] = random.choice(white_shadow)
    
    # Kanat tüy çizgileri (detay)
    for x in range(32, 48, 3):
        for y in range(0, 12):
            if random.random() < 0.3:
                pixels[x, y] = (200, 200, 200, 255)
    
    # Kanat uçları (hafif gri)
    for x in range(32, 48):
        for y in range(10, 12):
            if random.random() < 0.5:
                pixels[x, y] = random.choice(white_shadow)
    
    # ============================================
    # KUYRUK (Tail) - 8x8 (48, 0) - (55, 7)
    # ============================================
    for x in range(48, 56):
        for y in range(0, 8):
            pixels[x, y] = random.choice(white_feathers)
    
    # Kuyruk tüy detayları
    for x in range(48, 56, 2):
        for y in range(0, 8):
            if random.random() < 0.3:
                pixels[x, y] = (230, 230, 230, 255)
    
    # ============================================
    # YÜZ OVERLAY (Face Details) - 8x8 (16, 16) - (23, 23)
    # ============================================
    # Bu alan create_face() için kullanılacak
    for x in range(16, 24):
        for y in range(16, 24):
            # Şeffaf beyaz taban
            pixels[x, y] = (255, 255, 255, 0)
    
    # Gözler (overlay için)
    pixels[17, 18] = (255, 255, 255, 255)  # Sol göz beyazı
    pixels[18, 18] = (0, 0, 0, 255)        # Sol göz bebeği
    
    pixels[21, 18] = (255, 255, 255, 255)  # Sağ göz beyazı
    pixels[22, 18] = (0, 0, 0, 255)        # Sağ göz bebeği
    
    # Gaga detayı (overlay)
    for x in range(18, 22):
        for y in range(20, 23):
            pixels[x, y] = random.choice(orange_beak)
    
    img.save(os.path.join(ENTITIES_DIR, 'chicken.png'))
    print("[TEXTURE] Tavuk dokusu oluşturuldu: chicken.png (64x32, yüz detaylı)")

def create_grass_icon():

    """Envanterde çimenin 3D görünümlü ikonunu oluşturur."""
    try:
        top_tex = Image.open(os.path.join(BLOCKS_DIR, 'grass_top.png'))
        side_tex = Image.open(os.path.join(BLOCKS_DIR, 'grass.png'))
        img = Image.new('RGBA', (32, 32), (0, 0, 0, 0))
        top = top_tex.resize((24, 12))
        side = side_tex.resize((12, 14))
        img.paste(top, (4, 4), top if top.mode == 'RGBA' else None)
        img.paste(side, (4, 16), side if side.mode == 'RGBA' else None)
        img.paste(side, (16, 16), side if side.mode == 'RGBA' else None)
        img.save(os.path.join(UI_DIR, 'grass_icon_3d.png'))
    except Exception: pass

def create_moon_texture():
    """
    Ay dokusunu oluşturur.
    Kraterler ve kenar koyulaşması ile gerçekçi görünüm.
    """
    img = Image.new('RGBA', (16, 16), (0, 0, 0, 0))
    draw = ImageDraw.Draw(img)
    
    # Ayın merkezi ve yarıçapı
    center_x, center_y = 8, 8
    radius = 6
    
    for x in range(16):
        for y in range(16):
            # Merkezden uzaklığı hesapla
            distance = ((x - center_x) ** 2 + (y - center_y) ** 2) ** 0.5
            
            if distance <= radius:
                # Ayın yüzeyinde kraterler oluştur
                if random.random() < 0.3:
                    # Kraterler (koyu bölgeler)
                    intensity = random.randint(100, 150)
                    color = (intensity, intensity, intensity, 255)
                else:
                    # Ana ay yüzeyi (açık gri)
                    intensity = random.randint(180, 220)
                    color = (intensity, intensity, intensity, 255)
                
                # Kenarlara doğru koyulaşma efekti
                edge_factor = distance / radius
                if edge_factor > 0.7:
                    darken = int((edge_factor - 0.7) * 100)
                    color = tuple(max(0, c - darken) for c in color[:3]) + (255,)
                
                img.putpixel((x, y), color)
    
    img.save(os.path.join(UI_DIR, 'moon.png'))
    print("[TEXTURE] Ay dokusu oluşturuldu: moon.png")

def create_star_texture():
    """
    Yıldız dokusunu oluşturur.
    Parlaklık varyasyonları ve renk tonları ile gerçekçi görünüm.
    """
    img = Image.new('RGBA', (8, 8), (0, 0, 0, 0))
    draw = ImageDraw.Draw(img)
    
    # Parlak merkez
    center_x, center_y = 4, 4
    
    for x in range(8):
        for y in range(8):
            distance = ((x - center_x) ** 2 + (y - center_y) ** 2) ** 0.5
            
            if distance <= 3:
                # Yıldızın parlaklığı (merkezden kenara doğru azalır)
                if distance <= 1:
                    # Çekirdek - çok parlak
                    brightness = random.randint(240, 255)
                elif distance <= 2:
                    # Orta katman
                    brightness = random.randint(220, 240)
                else:
                    # Dış katman
                    brightness = random.randint(180, 220)
                
                # Rastgele renk varyasyonu (çoğunlukla beyaz, bazen mavi/mor)
                if random.random() < 0.8:
                    color = (brightness, brightness, brightness, 255)
                elif random.random() < 0.5:
                    # Hafif mavi ton
                    color = (brightness - 20, brightness - 10, brightness, 255)
                else:
                    # Hafif mor ton
                    color = (brightness, brightness - 30, brightness, 255)
                
                # Parlaklık efekti için geçiş (alpha fade)
                fade = 1.0 - (distance / 3) ** 2
                alpha = int(255 * fade)
                color = color[:3] + (alpha,)
                
                img.putpixel((x, y), color)
    
    img.save(os.path.join(UI_DIR, 'star.png'))
    print("[TEXTURE] Yıldız dokusu oluşturuldu: star.png")

def create_night_sky_texture():
    """
    Gece gökyüzü dokusunu oluşturur.
    Koyu lacivert ton ve hafif gürültü ile doğal görünüm.
    """
    img = Image.new('RGBA', (64, 64), (0, 0, 0, 0))
    
    # Temel gece gökyüzü rengi (koyu lacivert)
    base_color = (10, 10, 40, 255)
    
    for x in range(64):
        for y in range(64):
            # Hafif gürültü ekleyerek doğal görünüm
            noise_r = random.randint(-5, 5)
            noise_g = random.randint(-5, 5)
            noise_b = random.randint(0, 10)  # Mavilikte biraz varyasyon
            
            color = (
                max(0, min(255, base_color[0] + noise_r)),
                max(0, min(255, base_color[1] + noise_g)),
                max(0, min(255, base_color[2] + noise_b)),
                255
            )
            
            # Kenarlara doğru daha koyu (vignette efekti)
            edge_factor_x = min(x, 63 - x) / 32
            edge_factor_y = min(y, 63 - y) / 32
            edge_factor = min(edge_factor_x, edge_factor_y)
            
            if edge_factor < 0.5:
                darken = int((0.5 - edge_factor) * 40)
                color = tuple(max(0, c - darken) for c in color[:3]) + (255,)
            
            img.putpixel((x, y), color)
    
    img.save(os.path.join(UI_DIR, 'night_sky.png'))
    print("[TEXTURE] Gece gökyüzü dokusu oluşturuldu: night_sky.png")

def create_sun_texture():
    """
    Güneş dokusunu oluşturur.
    Merkez beyaz, dış katmanlar sarı-turuncu geçişli.
    """
    img = Image.new('RGBA', (16, 16), (0, 0, 0, 0))
    draw = ImageDraw.Draw(img)
    
    center_x, center_y = 8, 8
    radius = 6
    
    for x in range(16):
        for y in range(16):
            distance = ((x - center_x) ** 2 + (y - center_y) ** 2) ** 0.5
            
            if distance <= radius:
                # Güneşin renk geçişleri (merkezden kenara)
                if distance <= 2:
                    # Çekirdek - beyaz sıcak
                    color = (255, 255, 200, 255)
                elif distance <= 4:
                    # Orta katman - altın sarısı
                    color = (255, 220, 100, 255)
                else:
                    # Dış katman - turuncu
                    color = (255, 180, 50, 255)
                
                # Kenarlara doğru parlaklık düşüşü (fade out)
                if distance > radius * 0.7:
                    fade = 1.0 - ((distance - radius * 0.7) / (radius * 0.3))
                    alpha = int(255 * fade)
                    color = color[:3] + (alpha,)
                
                img.putpixel((x, y), color)
    
    img.save(os.path.join(UI_DIR, 'sun.png'))
    print("[TEXTURE] Güneş dokusu oluşturuldu: sun.png")

if __name__ == "__main__":
    # Tüm dokuları sırayla oluştur
    print("[BAŞLANGIÇ] Doku üretimi başlatılıyor...")
    
    create_bedrock_texture()
    create_ui_icons()
    create_vignette()
    create_hand_texture()
    create_break_textures()
    create_sheep_texture()
    create_pig_texture()
    create_chicken_texture()
    create_grass_icon()
    create_atlas()

    # Gece-gündüz döngüsü dokuları
    create_moon_texture()
    create_star_texture()
    create_night_sky_texture()
    create_sun_texture()

    print("[BAŞARILI] Tüm temel dokular güncellendi.")
