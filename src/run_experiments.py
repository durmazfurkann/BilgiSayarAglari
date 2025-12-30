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
        ga_delays = []
        ga_reliabilities = []
        
        for _ in range(REPEAT_COUNT):
            start_time = time.time()
            solver = GeneticSolver(network, src, dst)
            ga_path, cost, _, _ = solver.solve()
            duration = (time.time() - start_time) * 1000 # ms cinsinden
            
            # Detaylı metrikleri hesapla
            metrics = network.calculate_metrics(ga_path)
            
            ga_costs.append(cost)
            ga_times.append(duration)
            ga_delays.append(metrics['delay'] if metrics else 0)
            ga_reliabilities.append(metrics['reliability'] if metrics else 0)

        # --- Q-LEARNING (RL) ---
        rl_costs = []
        rl_times = []
        rl_delays = []
        rl_reliabilities = []
        
        for _ in range(REPEAT_COUNT):
            start_time = time.time()
            solver = QLearningSolver(network, src, dst)
            solver.train() 
            path = solver.get_path() # Yolu bul
            
            # Detaylı metrikleri hesapla
            metrics = network.calculate_metrics(path)
            cost = metrics['cost'] if metrics else float('inf')
            
            duration = (time.time() - start_time) * 1000 # ms cinsinden
            
            rl_costs.append(cost)
            rl_times.append(duration)
            rl_delays.append(metrics['delay'] if metrics else 0)
            rl_reliabilities.append(metrics['reliability'] if metrics else 0)

        
        # İstatistikleri Kaydet
        results.append({
            "Demand ID": idx,
            "Source": src,
            "Destination": dst,
            # GA Sonuçları
            "GA_Best_Cost": np.min(ga_costs),
            "GA_Avg_Cost": np.mean(ga_costs),
            "GA_Avg_Delay_ms": np.mean(ga_delays),
            "GA_Avg_Reliability": np.mean(ga_reliabilities),
            "GA_Std_Dev": np.std(ga_costs),
            "GA_Avg_Time_ms": np.mean(ga_times),
            # RL Sonuçları
            "RL_Best_Cost": np.min(rl_costs),
            "RL_Avg_Cost": np.mean(rl_costs),
            "RL_Avg_Delay_ms": np.mean(rl_delays),
            "RL_Avg_Reliability": np.mean(rl_reliabilities),
            "RL_Std_Dev": np.std(rl_costs),
            "RL_Avg_Time_ms": np.mean(rl_times),
            # Kazanan
            "Winner": "GA" if np.mean(ga_costs) < np.mean(rl_costs) else "RL"
        })

    
    # 3. Sonuçları Excel'e Yaz
    df_res = pd.DataFrame(results)
    excel_file = "Proje_Sonuclari.xlsx"
    
    # Sütun sırasını düzenle
    cols = ["Demand ID", "Source", "Destination", 
            "GA_Best_Cost", "GA_Avg_Cost", "GA_Avg_Delay_ms", "GA_Avg_Reliability", "GA_Avg_Time_ms",
            "RL_Best_Cost", "RL_Avg_Cost", "RL_Avg_Delay_ms", "RL_Avg_Reliability", "RL_Avg_Time_ms",
            "Winner"]
            
    # Sadece mevcut sütunları seç (hata önlemek için)
    existing_cols = [c for c in cols if c in df_res.columns]
    df_res = df_res[existing_cols]
    
    df_res.to_excel(excel_file, index=False)
    print(f"\n Tüm deneyler bitti! Sonuçlar '{excel_file}' dosyasına kaydedildi.")


if __name__ == "__main__":
    run_experiments()