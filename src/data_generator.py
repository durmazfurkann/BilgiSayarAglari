import networkx as nx
import pandas as pd
import random
import os
import math

# Dosya Yolları
DATA_DIR = 'data'
if not os.path.exists(DATA_DIR):
    os.makedirs(DATA_DIR)

NODE_FILE = os.path.join(DATA_DIR, 'BSM307_317_Guz2025_TermProject_NodeData.csv')
EDGE_FILE = os.path.join(DATA_DIR, 'BSM307_317_Guz2025_TermProject_EdgeData.csv')
DEMAND_FILE = os.path.join(DATA_DIR, 'BSM307_317_Guz2025_TermProject_DemandData.csv')

def generate_network():
    """
    Proje isterlerine uygun rastgele bir ağ topolojisi oluşturur.
    
    Özellikler:
    - 250 Düğüm
    - Bağlantı Olasılığı (P) = 0.4 (Erdős–Rényi Modeli)
    - Rastgele Gecikme, Güvenilirlik ve Bant Genişliği değerleri atanır.
    
    Döndürür:
        G (networkx.Graph): Oluşturulan graf nesnesi.
    """
    print("Core Network oluşturuluyor (N=250, P=0.4)...")
    # 1. 250 Düğümlü, P=0.4 Erdős–Rényi Grafı
    # Not: P=0.4 çok yoğun bir graf oluşturur (yaklaşık 12,000 kenar).
    G = nx.erdos_renyi_graph(n=250, p=0.4, seed=42)
    
    # Bağlılık Kontrolü (Ağın tek parça olduğundan emin ol)
    if not nx.is_connected(G):
        print("Uyarı: Graf bağlı değil, en büyük bileşen alınıyor...")
        largest_cc = max(nx.connected_components(G), key=len)
        G = G.subgraph(largest_cc).copy()
    
    print(f"Graf Oluşturuldu: {G.number_of_nodes()} Düğüm, {G.number_of_edges()} Kenar")

    # 2. Düğüm (Node) Özellikleri Atama
    node_data = []
    for node in G.nodes():
        # İşlem Süresi: [0.5, 2.0] ms
        proc_delay = round(random.uniform(0.5, 2.0), 2)
        # Güvenilirlik: [0.95, 0.999]
        reliability = round(random.uniform(0.95, 0.999), 4)
        
        G.nodes[node]['proc_delay'] = proc_delay
        G.nodes[node]['reliability'] = reliability
        
        node_data.append({
            'node_id': node,
            's_ms': proc_delay,
            'r_node': reliability
        })

    # 3. Kenar (Link) Özellikleri Atama
    edge_data = []
    for u, v in G.edges():
        # Bant Genişliği: [100, 1000] Mbps
        bandwidth = random.randint(100, 1000)
        # Gecikme: [3, 15] ms
        delay = random.randint(3, 15)
        # Güvenilirlik: [0.95, 0.999]
        reliability = round(random.uniform(0.95, 0.999), 4)
        
        edge_data.append({
            'src': u,
            'dst': v,
            'capacity_mbps': bandwidth,
            'delay_ms': delay,
            'r_link': reliability
        })

    # 4. CSV Kaydı
    pd.DataFrame(node_data).to_csv(NODE_FILE, sep=';', index=False)
    pd.DataFrame(edge_data).to_csv(EDGE_FILE, sep=';', index=False)
    print("Node ve Edge verileri kaydedildi.")

    return G

def generate_demands(graph, num_demands=20):
    """
    Algoritmaları test etmek için rastgele trafik talepleri (Kaynak -> Hedef) üretir.
    """
    print(f"{num_demands} adet rastgele talep oluşturuluyor...")
    nodes = list(graph.nodes())
    demands = []
    
    for i in range(num_demands):
        src = random.choice(nodes)
        dst = random.choice(nodes)
        while src == dst:
            dst = random.choice(nodes)
            
        bw_demand = random.choice([50, 100, 200, 500]) # Örnek bant genişliği talebi
        
        demands.append({
            'id': i+1,
            'src': src,
            'dst': dst,
            'bw_demand': bw_demand
        })
        
    pd.DataFrame(demands).to_csv(DEMAND_FILE, sep=';', index=False)
    print("Demand verileri kaydedildi.")

if __name__ == "__main__":
    G = generate_network()
    generate_demands(G)
