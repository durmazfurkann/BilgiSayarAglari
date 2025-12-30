import pandas as pd
import time
import numpy as np
import sys
import os

# Proje kök dizinini path'e ekle
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.config import NODE_FILE, EDGE_FILE, DEMAND_FILE
from src.network_model import NetworkModel
from src.ga_solver import GeneticSolver
from src.rl_solver import QLearningSolver

# DENEY AYARLARI
REPEAT_COUNT = 5  # PDF Madde 6: En az 5 tekrar 

def run_experiments():
    print(f"=== DENEY BAŞLIYOR ({REPEAT_COUNT} Tekrar) ===")
    
    # 1. Modeli Yükle
    network = NetworkModel(NODE_FILE, EDGE_FILE)
    demands = pd.read_csv(DEMAND_FILE, delimiter=';')
    
    results = []

    # 2. Her talep için döngü
    total_demands = len(demands)
    for idx, row in demands.iterrows():
        src, dst = int(row['src']), int(row['dst'])
        print(f"[{idx+1}/{total_demands}] Talep İşleniyor: {src} -> {dst} ...")

        # --- GENETİK ALGORİTMA (GA) ---
        ga_costs = []
        ga_times = []
        for _ in range(REPEAT_COUNT):
            start_time = time.time()
            solver = GeneticSolver(network, src, dst)
            _, cost = solver.solve()
            duration = (time.time() - start_time) * 1000 # ms cinsinden
            
            ga_costs.append(cost)
            ga_times.append(duration)

        # --- Q-LEARNING (RL) ---
        rl_costs = []
        rl_times = []
        for _ in range(REPEAT_COUNT):
            start_time = time.time()
            solver = QLearningSolver(network, src, dst)
            solver.train() # Eğit
            path = solver.get_path() # Yolu bul
            cost = network.calculate_cost(path)
            duration = (time.time() - start_time) * 1000 # ms cinsinden
            
            rl_costs.append(cost)
            rl_times.append(duration)

        # İstatistikleri Kaydet
        results.append({
            "Demand ID": idx,
            "Source": src,
            "Destination": dst,
            # GA Sonuçları
            "GA_Best_Cost": np.min(ga_costs),
            "GA_Avg_Cost": np.mean(ga_costs),
            "GA_Std_Dev": np.std(ga_costs),
            "GA_Avg_Time_ms": np.mean(ga_times),
            # RL Sonuçları
            "RL_Best_Cost": np.min(rl_costs),
            "RL_Avg_Cost": np.mean(rl_costs),
            "RL_Std_Dev": np.std(rl_costs),
            "RL_Avg_Time_ms": np.mean(rl_times),
            # Kazanan
            "Winner": "GA" if np.mean(ga_costs) < np.mean(rl_costs) else "RL"
        })

    # 3. Sonuçları Excel/CSV'ye Yaz
    df_res = pd.DataFrame(results)
    df_res.to_csv("Proje_Sonuclari.csv", index=False)
    print("\n✅ Tüm deneyler bitti! Sonuçlar 'Proje_Sonuclari.csv' dosyasına kaydedildi.")
    print("Bu dosyayı açıp Raporuna tablo olarak ekleyebilirsin.")

if __name__ == "__main__":
    run_experiments()