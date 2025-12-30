import networkx as nx
import matplotlib.pyplot as plt

def draw_network_path(graph, path, title="Sonuç", details=""):
    """
    Seçilen yolu graf üzerinde çizer.
    Sadece yol üzerindeki düğümlerin numaraları gösterilir.
    """
    # Düzen (Layout) - Her seferinde aynı şekli çizmesi için seed sabitliyoruz
    pos = nx.spring_layout(graph, seed=42, k=0.15, iterations=20)
    
    plt.figure(figsize=(12, 10))
    
    # 1. Tüm Ağı Çiz (Arkaplan - Silik)
    # Düğümler
    nx.draw_networkx_nodes(graph, pos, node_size=20, node_color='#CCCCCC', alpha=0.6)
    # Kenarlar
    nx.draw_networkx_edges(graph, pos, width=0.5, edge_color='#DDDDDD', alpha=0.4)
    
    # 2. Bulunan Yolu Çiz (Önplan - Canlı)
    if path:
        # Yol kenarlarını belirle
        path_edges = list(zip(path, path[1:]))
        
        # Yol üzerindeki düğümler (Mavi)
        nx.draw_networkx_nodes(graph, pos, nodelist=path, node_size=100, node_color='blue')
        
        # Başlangıç (Yeşil) ve Bitiş (Kırmızı) düğümlerini vurgula
        nx.draw_networkx_nodes(graph, pos, nodelist=[path[0]], node_size=200, node_color='green', label="Başlangıç")
        nx.draw_networkx_nodes(graph, pos, nodelist=[path[-1]], node_size=200, node_color='red', label="Bitiş")
        
        # Yol kenarları (Kırmızı çizgi)
        nx.draw_networkx_edges(graph, pos, edgelist=path_edges, edge_color='red', width=2.5)
        
        # Sadece yol üzerindeki düğümlerin numaralarını yaz
        labels = {node: str(node) for node in path}
        nx.draw_networkx_labels(graph, pos, labels, font_size=10, font_weight='bold', font_color='black')

    # Başlık ve Bilgiler
    plt.title(title, fontsize=14, fontweight='bold')
    # Alt tarafa detayları yaz
    plt.xlabel(details, fontsize=11, style='italic', bbox=dict(facecolor='white', alpha=0.8))
    
    plt.axis('off') # Eksenleri kapat
    plt.tight_layout()
    plt.show()