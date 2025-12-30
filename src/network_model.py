# src/network_model.py
import pandas as pd
import networkx as nx
import math
from .config import W_DELAY, W_RELIABILITY, W_RESOURCE

class NetworkModel:
    def __init__(self, node_file, edge_file):
        self.graph = nx.Graph()
        self.load_data(node_file, edge_file)

    def load_data(self, node_file, edge_file):
        try:
            nodes_df = pd.read_csv(node_file, delimiter=';')
            edges_df = pd.read_csv(edge_file, delimiter=';')

            # Sayısal düzeltmeler (Virgül -> Nokta)
            nodes_df['s_ms'] = nodes_df['s_ms'].astype(str).str.replace(',', '.').astype(float)
            nodes_df['r_node'] = nodes_df['r_node'].astype(str).str.replace(',', '.').astype(float)
            edges_df['r_link'] = edges_df['r_link'].astype(str).str.replace(',', '.').astype(float)

            for _, row in nodes_df.iterrows():
                self.graph.add_node(int(row['node_id']), 
                                    proc_delay=row['s_ms'], 
                                    reliability=row['r_node'])

            for _, row in edges_df.iterrows():
                self.graph.add_edge(int(row['src']), int(row['dst']), 
                                    bandwidth=row['capacity_mbps'], 
                                    link_delay=row['delay_ms'], 
                                    reliability=row['r_link'])
            print(f"[INFO] Ağ Yüklendi: {self.graph.number_of_nodes()} Düğüm.")
        except Exception as e:
            print(f"[ERROR] Veri yükleme hatası: {e}")

    def calculate_cost(self, path):
        """
        Verilen yolun toplam ağırlıklı maliyetini ve detaylarını hesaplar.
        Formül: W_delay * Gecikme + W_rel * Güven_Maliyeti + W_res * Kaynak_Maliyeti
        
        Dönüş: {
            'score': float,           # Ağırlıklı toplam maliyet
            'delay': float,           # Toplam gecikme (ms)
            'bandwidth': float,       # Minimum bant genişliği (Mbps)
            'reliability': float      # Toplam güvenilirlik (0-1 arası)
        }
        """
        if not path or len(path) < 2:
            return {
                'score': float('inf'),
                'delay': float('inf'),
                'bandwidth': 0,
                'reliability': 0
            }

        total_delay = 0
        total_rel_cost = 0
        total_res_cost = 0
        total_reliability = 1.0
        min_bandwidth = float('inf')

        for i in range(len(path) - 1):
            u, v = path[i], path[i+1]
            edge = self.graph[u][v]
            
            # 1. Gecikme (Link + İşlem)
            total_delay += edge['link_delay']
            if i > 0:
                total_delay += self.graph.nodes[u]['proc_delay']
            
            # 2. Güvenilirlik (-log ile toplamsal hale getirme)
            if edge['reliability'] > 0:
                total_rel_cost += -math.log(edge['reliability'])
                total_reliability *= edge['reliability']
            if i > 0 and self.graph.nodes[u]['reliability'] > 0:
                total_rel_cost += -math.log(self.graph.nodes[u]['reliability'])
                total_reliability *= self.graph.nodes[u]['reliability']

            # 3. Kaynak Kullanımı (1000/Bant Genişliği)
            if edge['bandwidth'] > 0:
                total_res_cost += (1000.0 / edge['bandwidth'])
                if edge['bandwidth'] < min_bandwidth:
                    min_bandwidth = edge['bandwidth']

        weighted_cost = (W_DELAY * total_delay) + \
                        (W_RELIABILITY * total_rel_cost) + \
                        (W_RESOURCE * total_res_cost)
        
        return {
            'score': round(weighted_cost, 4),
            'delay': round(total_delay, 2),
            'bandwidth': int(min_bandwidth) if min_bandwidth != float('inf') else 0,
            'reliability': round(total_reliability, 5)
        }

    def calculate_metrics(self, path):
        """
        Yolun ham metriklerini (Gecikme, Güvenilirlik, Maliyet) hesaplar.
        Pareto analizi ve raporlama için kullanılır.
        
        Dönüş: {'cost': float, 'delay': float, 'reliability': float, 'hops': int}
        """
        if not path: return None
        
        total_delay = 0
        total_reliability = 1.0
        
        for i in range(len(path) - 1):
            u, v = path[i], path[i+1]
            edge = self.graph[u][v]
            
            # Gecikme
            total_delay += edge['link_delay']
            if i > 0:
                total_delay += self.graph.nodes[u]['proc_delay']
                
            # Güvenilirlik (Çarpımsal)
            total_reliability *= edge['reliability']
            if i > 0:
                total_reliability *= self.graph.nodes[u]['reliability']
                
        return {
            'cost': self.calculate_cost(path)['score'],
            'delay': round(total_delay, 2),
            'reliability': round(total_reliability, 5),
            'hops': len(path) - 1
        }

    def get_path_min_bandwidth(self, path):
        """
        Yoldaki en düşük bant genişliğini (darboğaz) döndürür.
        
        Dönüş: Minimum BW (Mbps) veya None
        """
        if not path or len(path) < 2: return None
        
        min_bw = float('inf')
        for i in range(len(path) - 1):
            u, v = path[i], path[i+1]
            edge = self.graph[u][v]
            bw = edge.get('bandwidth', 0)
            if bw < min_bw:
                min_bw = bw
                
        return int(min_bw) if min_bw != float('inf') else None