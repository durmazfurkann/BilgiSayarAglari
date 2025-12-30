import random
import networkx as nx
from src.config import GA_POP_SIZE, GA_GENERATIONS, GA_MUTATION_RATE

class GeneticSolver:
    """
    Genetik Algoritma (GA) ile En 'İyi' Yolu Bulan Sınıf.
    
    Özellikler:
    - Popülasyon Tabanlı: Çok sayıda çözüm adayı aynı anda geliştirilir.
    - Operatörler: Çaprazlama (Crossover) ve Mutasyon ile yeni yollar keşfedilir.
    - Amaç: Gecikme, Güvenilirlik ve Kaynak kullanımını optimize etmek.
    """
    def __init__(self, network_model, src, dst):
        self.model = network_model
        self.graph = network_model.graph
        self.src = src
        self.dst = dst
        self.population = [] # Kromozomlar (Yollar)

    def create_random_path(self):
        """
        Başlangıçtan hedefe rastgele (geçerli) bir yol oluşturur.
        Döngüye girmemesi için ziyaret edilenleri takip eder.
        """
        path = [self.src]
        curr = self.src
        visited = {self.src}
        
        while curr != self.dst:
            # Gidilebilecek, henüz gezilmemiş komşular
            neighbors = [n for n in self.graph.neighbors(curr) if n not in visited]
            
            # Çıkmaz sokaksa veya yol çok uzadıysa (max 50) iptal
            if not neighbors or len(path) > 50: 
                return None
            
            curr = random.choice(neighbors)
            path.append(curr)
            visited.add(curr)
            
        return path

    def crossover(self, parent1, parent2):
        """
        Çaprazlama Operatörü: İki ebeveyn yolun ortak bir noktasından
        kesilip parçalarının birleştirilmesiyle yeni bir 'çocuk' yol üretir.
        """
        # Başlangıç ve bitiş hariç ortak düğümleri bul
        common = [node for node in parent1[1:-1] if node in parent2[1:-1]]
        
        if not common:
            return parent1 # Ortak nokta yoksa değişim yapma
            
        # Rastgele bir kesişim noktası seç
        cross_node = random.choice(common)
        
        idx1 = parent1.index(cross_node)
        idx2 = parent2.index(cross_node)
        
        # P1'in başı + P2'nin sonu (YENİ ÇOCUK)
        child = parent1[:idx1] + parent2[idx2:]
        
        # Döngü kontrolü (Aynı düğüm 2 kere geçmemeli)
        if len(child) != len(set(child)):
            return parent1
            
        return child

    def mutate(self, path):
        """
        Mutasyon Operatörü: Yolun bir noktasından kopup hedefe 
        farklı (rastgele/kısa) bir yoldan gitmeyi dener.
        Çeşitliliği sağlar ve yerel minimumdan kurtarır.
        """
        if len(path) < 3: return path
        
        # Rastgele bir kopma noktası seç
        mutate_idx = random.randint(1, len(path)-2)
        sub_src = path[mutate_idx]
        
        # O noktadan hedefe yeni bir yol bulmayı dene
        try:
            # Yamama işlemi için shortest_path kullanıyoruz (ancak sadece ara parça için)
            sub_path = nx.shortest_path(self.graph, sub_src, self.dst)
            new_path = path[:mutate_idx] + sub_path
            
            # Döngü kontrolü
            if len(new_path) == len(set(new_path)):
                return new_path
        except:
            pass
            
        return path

    def solve(self):
        """
        Algoritmayı çalıştıran ana fonksiyon.
        
        Döndürür:
            best_path (list): Bulunan en iyi yol
            best_cost (float): O yolun maliyeti
            history (list): Her jenerasyondaki en iyi maliyet (Grafik için)
            pareto_data (list): Popülasyondaki tüm bireylerin analiz verisi (Scatter plot için)
        """
        # 1. Başlangıç Popülasyonu
        # Hile yapmıyoruz, tamamen rastgele yollarla başlıyoruz.
        attempts = 0
        while len(self.population) < GA_POP_SIZE and attempts < GA_POP_SIZE * 50:  # 10'dan 50'ye çıkarıldı
            p = self.create_random_path()
            if p: self.population.append(p)
            attempts += 1
            
        if not self.population: return None, float('inf'), [], []

        best_path = None
        best_cost = float('inf')
        
        history = [] # Yakınsama grafiği için kayıt
        
        # 2. Nesiller Boyunca Evrim
        for gen in range(GA_GENERATIONS):
            # Maliyetleri hesapla
            scored_pop = []
            for p in self.population:
                cost = self.model.calculate_cost(p)
                scored_pop.append((cost, p))
            
            # Sırala (Küçükten büyüğe)
            scored_pop.sort(key=lambda x: x[0])
            
            # En iyiyi güncelle
            current_best = scored_pop[0]
            if current_best[0] < best_cost:
                best_cost = current_best[0]
                best_path = current_best[1]
            
            # Tarihçeye kaydet
            history.append(current_best[0])

            # Elitizm: En iyi %50'yi doğrudan sonraki nesle aktar
            selected = [x[1] for x in scored_pop[:len(scored_pop)//2]]
            
            new_generation = list(selected)
            
            # Yeni bireyler üret (Crossover & Mutation)
            while len(new_generation) < GA_POP_SIZE:
                if len(selected) < 2: break
                p1 = random.choice(selected)
                p2 = random.choice(selected)
                
                child = self.crossover(p1, p2)
                
                if random.random() < GA_MUTATION_RATE:
                    child = self.mutate(child)
                    
                new_generation.append(child)
            
            self.population = new_generation

        # Analiz için son popülasyon verilerini hazırla (Pareto)
        pareto_data = []
        for p in self.population:
            # Her bir yolun detaylı metriklerini (Delay, Reliability) hesapla
            # Bunun için modelde ayrı fonksiyonumuz yok ama manuel hesaplayabiliriz ya da tahmini cost verebiliriz
            # Şimdilik maliyet ve adım sayısını dönelim
            metrics = self.model.calculate_metrics(p) # Bu fonksiyonu Model'e ekleyeceğiz
            pareto_data.append(metrics)

        return best_path, best_cost, history, pareto_data