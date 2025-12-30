import pandas as pd
import sys
import src.config as config
from src.config import NODE_FILE, EDGE_FILE
from src.network_model import NetworkModel
from src.ga_solver import GeneticSolver
from src.rl_solver import QLearningSolver
from src.visualizer import draw_network_path

def get_valid_node(prompt, max_node):
    """Kullanıcıdan geçerli bir düğüm ID'si ister."""
    while True:
        try:
            val = input(prompt)
            if val.lower() == 'q': return 'q'
            node_id = int(val)
            if 0 <= node_id < max_node:
                return node_id
            else:
                print(f"❌ Hata: Düğüm 0 ile {max_node-1} arasında olmalı.")
        except ValueError:
            print("❌ Hata: Lütfen sayı girin.")

def get_weights():
    """Kullanıcıdan optimizasyon ağırlıklarını ister."""
    print("\n--- Optimizasyon Kriterleri ---")
    print("1. Standart (Dengeli: Hepsi ~0.33)")
    print("2. Hız Odaklı (Gecikme Önemli)")
    print("3. Güvenlik Odaklı (Güvenilirlik Önemli)")
    print("4. Özel Ağırlık Gir")
    
    choice = input("Seçiminiz (1-4): ")
    
    if choice == '2':
        return 0.8, 0.1, 0.1
    elif choice == '3':
        return 0.1, 0.8, 0.1
    elif choice == '4':
        try:
            w_d = float(input("Gecikme Ağırlığı (0.0-1.0): "))
            w_r = float(input("Güvenilirlik Ağırlığı (0.0-1.0): "))
            w_res = float(input("Kaynak Ağırlığı (0.0-1.0): "))
            total = w_d + w_r + w_res
            if total == 0: return 0.33, 0.33, 0.33
            return w_d/total, w_r/total, w_res/total
        except:
            print("Hatalı giriş, standart kullanılıyor.")
            return 0.33, 0.33, 0.34
    else:
        return 0.33, 0.33, 0.34

def format_path(path):
    """Yolu okunaklı bir stringe çevirir (0 -> 5 -> 10)"""
    if not path:
        return "Yol Bulunamadı"
    # Eğer yol çok uzunsa özet geç, kısaysa hepsini göster
    if len(path) > 15:
        return f"{path[0]} -> ... ({len(path)-2} düğüm) ... -> {path[-1]}"
    return " -> ".join(map(str, path))

def main():
    print("=================================================")
    print("   BSM307 - QoS Odaklı Rotalama Projesi (Demo)   ")
    print("=================================================")
    
    # 1. Ağı Yükle
    print("⏳ Ağ modeli yükleniyor... Lütfen bekleyin.")
    try:
        network = NetworkModel(NODE_FILE, EDGE_FILE)
        max_nodes = network.graph.number_of_nodes()
    except Exception as e:
        print(f"Kritik Hata: Veri dosyaları bulunamadı! ({e})")
        print("Lütfen 'data' klasörünün ve CSV dosyalarının doğru yerde olduğundan emin olun.")
        return

    while True:
        print("\n" + "="*50)
        print("YENİ SORGULAMA (Çıkmak için 'q' basın)")
        
        # 2. Kullanıcı Girdileri
        src = get_valid_node(f"📌 Kaynak Düğüm (Source 0-{max_nodes-1}): ", max_nodes)
        if src == 'q': break
        
        dst = get_valid_node(f"🏁 Hedef Düğüm (Destination 0-{max_nodes-1}): ", max_nodes)
        if dst == 'q': break
        
        if src == dst:
            print("⚠️ Kaynak ve Hedef aynı olamaz!")
            continue

        # 3. Ağırlık Ayarları
        w_d, w_r, w_res = get_weights()
        config.W_DELAY = w_d
        config.W_RELIABILITY = w_r
        config.W_RESOURCE = w_res
        
        print(f"\n⚙️ Parametreler: Gecikme={w_d:.2f}, Güven={w_r:.2f}, Kaynak={w_res:.2f}")
        print("-" * 40)

        # 4. Algoritmaları Çalıştır
        print(f"🧬 Genetik Algoritma (GA) çalışıyor...")
        ga = GeneticSolver(network, src, dst)
        ga_path, ga_cost = ga.solve()
        
        print(f"🤖 Q-Learning (RL) çalışıyor (Eğitim)...")
        rl = QLearningSolver(network, src, dst)
        rl.train()
        rl_path = rl.get_path()
        rl_cost = network.calculate_cost(rl_path)

        # 5. Sonuçları Karşılaştır ve Yazdır
        print("\n" + "-"*60)
        print(f"{'METRİK':<15} | {'GENETİK (GA)':<20} | {'Q-LEARNING (RL)':<20}")
        print("-" * 60)
        print(f"{'Maliyet':<15} | {ga_cost:<20.4f} | {rl_cost:<20.4f}")
        print(f"{'Adım Sayısı':<15} | {len(ga_path) if ga_path else 0:<20} | {len(rl_path) if rl_path else 0:<20}")
        print("-" * 60)
        
        # --- EKLENEN KISIM: YOL LİSTESİ ---
        print("📍 BULUNAN YOLLAR:")
        print(f"   🧬 GA Yolu: {format_path(ga_path)}")
        print(f"   🤖 RL Yolu: {format_path(rl_path)}")
        
        winner_path = None
        winner_name = ""
        
        if ga_cost < rl_cost:
            print("\n🏆 KAZANAN: Genetik Algoritma (Daha Düşük Maliyet)")
            winner_path = ga_path
            winner_name = "Genetik Algoritma (GA)"
        else:
            print("\n🏆 KAZANAN: Q-Learning (Daha Düşük Maliyet)")
            winner_path = rl_path
            winner_name = "Q-Learning (RL)"

        # 6. Görselleştirme
        if winner_path:
            metrics = f"Maliyet: {min(ga_cost, rl_cost):.2f} | Adımlar: {len(winner_path)}\nAğırlıklar: D={w_d:.2f}, R={w_r:.2f}, C={w_res:.2f}"
            print("📈 Grafik çiziliyor... (Pencereyi kapatınca yeni sorgu yapabilirsiniz)")
            draw_network_path(network.graph, winner_path, 
                            title=f"En İyi Yol: {src} -> {dst} ({winner_name})", 
                            details=metrics)
        else:
            print("❌ İki algoritma da yol bulamadı!")

if __name__ == "__main__":
    main()