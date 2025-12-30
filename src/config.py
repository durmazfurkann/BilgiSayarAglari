# Dosya Yolları (Proje kök dizinine göre)
NODE_FILE = 'data/BSM307_317_Guz2025_TermProject_NodeData.csv'
EDGE_FILE = 'data/BSM307_317_Guz2025_TermProject_EdgeData.csv'
DEMAND_FILE = 'data/BSM307_317_Guz2025_TermProject_DemandData.csv'

# Optimizasyon Ağırlıkları (Varsayılan Değerler)
# Bu değerler GUI üzerinden değiştirilebilir.
# Toplamları daima 1.0 olmalıdır.
W_DELAY = 0.33       # Gecikme Ağırlığı
W_RELIABILITY = 0.33 # Güvenilirlik Ağırlığı
W_RESOURCE = 0.34    # Kaynak Kullanımı Ağırlığı

# Genetik Algoritma (GA) Parametreleri
GA_POP_SIZE = 30       # Popülasyon Büyüklüğü (Birey Sayısı)
GA_GENERATIONS = 50    # Jenerasyon (Nesil) Sayısı
GA_MUTATION_RATE = 0.1 # Mutasyon (Değişim) Olasılığı

# Pekiştirmeli Öğrenme (RL - Q-Learning) Parametreleri
RL_EPISODES = 3000     # Eğitim Tur Sayısı (250 düğümlü ağ için artırıldı)
RL_ALPHA = 0.1         # Öğrenme Hızı (Learning Rate - Yeni bilgiye ne kadar değer verileceği)
RL_GAMMA = 0.9         # Gelecek İskonto Katsayısı (Discount Factor - Gelecekteki ödülün önemi)
RL_EPSILON = 0.1       # Keşfetme Oranı (Exploration Rate - Rastgele hareket ihtimali)