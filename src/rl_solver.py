import random
import math
from src.config import RL_EPISODES, RL_ALPHA, RL_GAMMA, RL_EPSILON
from src.config import W_DELAY, W_RELIABILITY, W_RESOURCE 

class QLearningSolver:
    """
    Q-Learning (Pekiştirmeli Öğrenme) ile Yol Bulan Ajan.
    
    Mantık:
    - Ajan (Agent) ağ üzerinde düğüm düğüm gezer.
    - Her adımda bir ödül veya ceza alır.
    - Q-Tablosu (Q-Table) zamanla 'hangi durumda hangi hareket kazançlı' bilgisini öğrenir.
    - Hedef: Toplam ödülü maksimize (Maliyeti minimize) etmek.
    """
    def __init__(self, network_model, src, dst, min_bw=0):
        self.model = network_model
        # BW Kısıtı: Filtrelenmiş graf (self.graph) üzerinden işlem yap
        self.graph = network_model.get_filtered_graph(min_bw)
        self.src = src
        self.dst = dst
        self.q_table = {} # Q(State, Action) -> Değer

    def get_q(self, s, a):
        """Verilen durum ve eylem için Q değerini döndürür."""
        return self.q_table.get((s, a), 0.0)

    def calculate_step_cost(self, u, v):
        """Tek bir adımın (linkin) ağırlıklı maliyetini hesaplar."""
        edge = self.graph[u][v]
        
        # 1. Gecikme (Link + Hedef Node İşlem)
        delay = edge['link_delay'] + self.model.graph.nodes[u]['proc_delay']
        
        # 2. Güvenilirlik (-log)
        rel_cost = 0
        if edge['reliability'] > 0:
            rel_cost += -math.log(edge['reliability'])
        
        # 3. Kaynak (1000/BW)
        res_cost = 0
        if edge['bandwidth'] > 0:
            res_cost += (1000.0 / edge['bandwidth'])
            
        # Toplam Ağırlıklı Maliyet
        cost = (W_DELAY * delay) + (W_RELIABILITY * rel_cost) + (W_RESOURCE * res_cost)
        return cost

    def train(self):
        """
        Ajanı eğitir ve Q-Tablosunu doldurur.
        
        Döndürür:
            history (list): Her 100 bölümde bir test edilen yolun maliyeti (Grafik için).
        """
        history = []
        
        for episode in range(RL_EPISODES):
            state = self.src
            current_path_cost = 0 # Maliyet sıfırla
            
            # Sonsuz döngü koruması
            steps = 0
            while state != self.dst and steps < 50:
                neighbors = list(self.graph.neighbors(state))
                if not neighbors: break
                
                # Epsilon-Greedy Seçim (Keşfet vs Sömür)
                if random.random() < RL_EPSILON:
                    action = random.choice(neighbors)
                else:
                    qs = [self.get_q(state, n) for n in neighbors]
                    max_q = max(qs) if qs else 0
                    best_opts = [n for n, q in zip(neighbors, qs) if q == max_q]
                    action = random.choice(best_opts) if best_opts else random.choice(neighbors)
                
                # ÖDÜL MEKANİZMASI (SPARSE REWARD)
                step_cost = self.calculate_step_cost(state, action)
                current_path_cost += step_cost
                
                if action == self.dst:
                    # Hedefe ulaşıldığında: 1000 / Toplam Maliyet
                    reward = 1000.0 / current_path_cost if current_path_cost > 0 else 1000.0
                else:
                    # Ara adımlarda ödül yok (veya küçük ceza)
                    reward = -0.1
                
                # Bellman Denklemi ile Güncelleme
                old_q = self.get_q(state, action)
                
                next_neighbors = list(self.graph.neighbors(action))
                next_max = 0
                if next_neighbors:
                    next_max = max([self.get_q(action, n) for n in next_neighbors])
                
                # Q_new = Q_old + alpha * (Reward + gamma * Max_future - Q_old)
                new_q = old_q + RL_ALPHA * (reward + RL_GAMMA * next_max - old_q)
                self.q_table[(state, action)] = new_q
                
                state = action
                steps += 1
            
            # İlerleme Kaydı (Her 100 bölümde bir o anki bilgisiyle yol bulup maliyetine bak)
            if episode % 100 == 0:
                test_path = self.get_path()
                cost_data = self.model.calculate_cost(test_path)
                cost = cost_data['score']
                # Sonsuz maliyetleri grafikte göstermemek için filtreleyebiliriz veya max değer verebiliriz
                history.append(cost if cost != float('inf') else 0)

        return history

    def get_path(self):
        """
        Eğitilmiş Q-Tablosunu kullanarak en iyi yolu ("Greedy" yaklaşım) oluşturur.
        """
        state = self.src
        path = [state]
        visited = {state}
        
        steps = 0
        while state != self.dst and steps < 100:
            neighbors = [n for n in self.graph.neighbors(state) if n not in visited]
            if not neighbors: break
            
            # Öğrenilmiş Q değerlerine göre en iyiyi seç (Exploration kapalı)
            qs = [self.get_q(state, n) for n in neighbors]
            if not qs: break
            
            best_idx = qs.index(max(qs))
            action = neighbors[best_idx]
            
            state = action
            path.append(state)
            visited.add(state)
            steps += 1
            
        return path