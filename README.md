# BSM307 - QoS Odaklı Çok Amaçlı Rotalama Projesi

##  Proje Açıklaması
250 düğümlü karmaşık bir ağ topolojisi üzerinde, çok amaçlı (Gecikme, Güvenilirlik, Kaynak Kullanımı) optimizasyon yapan rotalama algoritmaları.

##  Kullanılan Algoritmalar
1. **Genetik Algoritma (GA)** - Meta-sezgisel yaklaşım
2. **Q-Learning (RL)** - Pekiştirmeli öğrenme yaklaşımı

##  Kurulum

```bash
# Bağımlılıkları yükle
pip install -r requirements.txt

# Veya ayrı ayrı
pip install networkx pandas numpy matplotlib openpyxl
```

##  Çalıştırma

### 1. Yeni Ağ Oluşturma (Opsiyonel)
```bash
python src/data_generator.py
```
- 250 düğümlü Erdős-Rényi (P=0.4) graf oluşturur
- Rastgele gecikme, güvenilirlik ve bant genişliği atar
- 20 adet test senaryosu (S, D, B) üretir

### 2. Görsel Arayüz (Önerilen)
```bash
python src/gui_app.py
```
- Kaynak (S) ve Hedef (D) düğüm seçimi
- Bant Genişliği Talebi (100-1000 Mbps)
- Ağırlık ayarları (Gecikme, Güvenilirlik, Kaynak)
- Yakınsama ve Pareto grafikleri

### 3. Toplu Deneyler
```bash
python src/run_experiments.py
```
- 20 farklı senaryo, 5'er tekrar
- Sonuçlar: `Proje_Sonuclari.xlsx`

##  Dosya Yapısı
```
├── data/                    # Ağ verileri (CSV)
│   ├── NodeData.csv         # Düğüm özellikleri
│   ├── EdgeData.csv         # Bağlantı özellikleri
│   └── DemandData.csv       # Test senaryoları
├── src/
│   ├── config.py            # Parametreler
│   ├── data_generator.py    # Ağ oluşturucu
│   ├── network_model.py     # Graf yapısı
│   ├── ga_solver.py         # Genetik Algoritma
│   ├── rl_solver.py         # Q-Learning
│   ├── gui_app.py           # Görsel arayüz
│   └── run_experiments.py   # Deney scripti
├── Proje_Sonuclari.xlsx     # Karşılaştırma tablosu (Excel)
└── requirements.txt         # Bağımlılıklar
```

## ⚙️ Parametreler (src/config.py)

| Parametre | Varsayılan | Açıklama |
|-----------|------------|----------|
| GA_POP_SIZE | 30 | Popülasyon büyüklüğü |
| GA_GENERATIONS | 50 | Nesil sayısı |
| RL_EPISODES | 3000 | Eğitim tur sayısı |
| RL_EPSILON | 0.1 | Keşif oranı |

##  Sonuçlar
`Proje_Sonuclari.xlsx` dosyasında 20 test senaryosu için:
- En iyi maliyet, ortalama maliyet, standart sapma
- Çalışma süreleri (ms)
- Kazanan algoritma

##  Hazırlayanlar
BSM307 - Bilgisayar Ağları Dersi - Güz 2025

Furkan Durmaz 24110310028

##  Seed Bilgisi
Ağ oluşturma: `seed=42` (Tekrarlanabilirlik için)
