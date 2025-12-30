import tkinter as tk
from tkinter import ttk, messagebox
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
import networkx as nx
import sys
import threading
import matplotlib.gridspec as gridspec

# Proje Modüllerini Ekle
sys.path.append('.')
from src.config import NODE_FILE, EDGE_FILE
from src.network_model import NetworkModel
from src.ga_solver import GeneticSolver
from src.rl_solver import QLearningSolver
import src.config as config

class QoSRoutingApp:
    """
    QoS Rotalama Projesi Grafik Arayüzü (GUI).
    
    Özellikler:
    - Sekmeli Yapı: 'Rotalama' ve 'Analiz' sekmeleri.
    - Rotalama: Kaynak ve Hedef seçip en iyi yolu harita üzerinde görme.
    - Analiz: Algoritmaların öğrenme eğrilerini (Convergence) ve
      alternatif yolların dağılımını (Pareto Frontier) inceleme.
    """
    def __init__(self, root):
        self.root = root
        self.root.title("BSM307 - QoS Rotalama ve Analiz Aracı")
        self.root.geometry("1400x900")
        
        # Veri Yükleme Durumu
        self.status_var = tk.StringVar()
        self.status_var.set("Ağ Modeli Yükleniyor...")
        self.network = None
        
        # Arayüz Bileşenlerini Oluştur
        self.create_layout()
        
        # Arkaplanda veri yükle
        threading.Thread(target=self.load_network, daemon=True).start()

    def load_network(self):
        """Ağ modelini CSV dosyalarından okur."""
        try:
            self.network = NetworkModel(NODE_FILE, EDGE_FILE)
            self.max_nodes = self.network.graph.number_of_nodes()
            # Combobox'ları güncelle (GUI thread'inde yapılması güvenli)
            self.root.after(0, self.update_node_combos)
            self.status_var.set(f"Hazır. ({self.max_nodes} Düğüm)")
            self.root.after(0, self.draw_initial_graph)
        except Exception as e:
            self.status_var.set(f"Hata: {str(e)}")
            messagebox.showerror("Veri Hatası", str(e))

    def update_node_combos(self):
        nodes = sorted(list(self.network.graph.nodes()))
        self.src_combo['values'] = nodes
        self.dst_combo['values'] = nodes
        if nodes:
            self.src_combo.current(0)
            self.dst_combo.current(len(nodes)-1)

    def create_layout(self):
        """Ana pencere düzenini (Sekmeler ve Paneller) oluşturur."""
        # 1. Kontrol Paneli (Sol Taraf - Sabit)
        control_panel = ttk.Frame(self.root, padding=10)
        control_panel.pack(side=tk.LEFT, fill=tk.Y)
        
        self.create_controls(control_panel)
        
        # 2. Ana Sekme Alanı (Sağ Taraf)
        self.tabs = ttk.Notebook(self.root)
        self.tabs.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        # --- Sekme 1: Rotalama (Harita) ---
        self.tab_routing = ttk.Frame(self.tabs)
        self.tabs.add(self.tab_routing, text=" 🌍 Rotalama ve Harita ")
        
        self.fig_map = plt.Figure(figsize=(8, 8), dpi=100)
        self.ax_map = self.fig_map.add_subplot(111)
        self.canvas_map = FigureCanvasTkAgg(self.fig_map, self.tab_routing)
        self.canvas_map.get_tk_widget().pack(fill=tk.BOTH, expand=True)
        
        # --- Sekme 2: Analiz (Grafikler) ---
        self.tab_analysis = ttk.Frame(self.tabs)
        self.tabs.add(self.tab_analysis, text=" 📊 Bilimsel Analiz (Pareto & Convergence) ")
        
        # Matplotlib GridSpec ile 2 grafik alt alta
        self.fig_analysis = plt.Figure(figsize=(8, 8), dpi=100)
        gs = gridspec.GridSpec(2, 1, height_ratios=[1, 1])
        
        self.ax_convergence = self.fig_analysis.add_subplot(gs[0])
        self.ax_pareto = self.fig_analysis.add_subplot(gs[1])
        
        self.canvas_analysis = FigureCanvasTkAgg(self.fig_analysis, self.tab_analysis)
        self.canvas_analysis.get_tk_widget().pack(fill=tk.BOTH, expand=True)

    def create_controls(self, parent):
        frame = ttk.LabelFrame(parent, text="Parametreler", padding=10)
        frame.pack(fill=tk.X, pady=5)
        
        # Düğüm Seçimi
        ttk.Label(frame, text="Kaynak (S):").pack(anchor=tk.W)
        self.src_combo = ttk.Combobox(frame, state="readonly", width=15)
        self.src_combo.pack(fill=tk.X, pady=2)
        
        ttk.Label(frame, text="Hedef (D):").pack(anchor=tk.W)
        self.dst_combo = ttk.Combobox(frame, state="readonly", width=15)
        self.dst_combo.pack(fill=tk.X, pady=2)
        
        # Bant Genişliği Talebi (Yeni)
        ttk.Label(frame, text="Talep Edilen BW (Mbps):").pack(anchor=tk.W, pady=(10, 0))
        self.bw_demand_var = tk.IntVar(value=500)
        bw_frame = ttk.Frame(frame)
        bw_frame.pack(fill=tk.X, pady=2)
        ttk.Spinbox(bw_frame, from_=100, to=1000, textvariable=self.bw_demand_var, width=13).pack(side=tk.LEFT)
        ttk.Label(bw_frame, text="(100-1000)", font=("Arial", 8)).pack(side=tk.LEFT, padx=5)
        
        # Ağırlıklar (Akıllı Slider)
        ttk.Separator(frame, orient='horizontal').pack(fill=tk.X, pady=10)
        ttk.Label(frame, text="Optimizasyon Ağırlıkları").pack()
        
        self.w_delay_var = tk.DoubleVar(value=0.33)
        self.w_rel_var = tk.DoubleVar(value=0.33)
        self.w_res_var = tk.DoubleVar(value=0.34)
        
        # Slider Mantığı (Toplamı 1.0 tutma)
        self.updating_weights = False
        def on_weight_change(var_name, *args):
            if self.updating_weights: return
            self.updating_weights = True
            try:
                vars_map = {str(self.w_delay_var): self.w_delay_var, 
                           str(self.w_rel_var): self.w_rel_var, 
                           str(self.w_res_var): self.w_res_var}
                
                if var_name not in vars_map: return
                changed_var = vars_map[var_name]
                new_val = changed_var.get()
                
                others = [v for k,v in vars_map.items() if k != var_name]
                sum_others = sum(v.get() for v in others)
                
                # Eğer toplam 1.0'ı aşarsa diğerlerini kıs
                total = new_val + sum_others
                if total > 1.0:
                    diff = total - 1.0
                    for v in others:
                        # Basit orantılı azaltma
                        current = v.get()
                        if sum_others > 0:
                            reduce = (current / sum_others) * diff
                            v.set(max(0, round(current - reduce, 2)))
            except: pass
            finally: self.updating_weights = False

        self.w_delay_var.trace_add('write', on_weight_change)
        self.w_rel_var.trace_add('write', on_weight_change)
        self.w_res_var.trace_add('write', on_weight_change)

        def make_slider(lbl, var):
            sf = ttk.Frame(frame)
            sf.pack(fill=tk.X)
            ttk.Label(sf, text=lbl, width=10).pack(side=tk.LEFT)
            ttk.Scale(sf, from_=0, to=1, variable=var).pack(side=tk.LEFT, fill=tk.X, expand=True)
            ttk.Label(sf, textvariable=var, width=5).pack(side=tk.RIGHT)

        make_slider("Gecikme:", self.w_delay_var)
        make_slider("Güven:", self.w_rel_var)
        make_slider("Kaynak:", self.w_res_var)
        
        # Buton
        ttk.Separator(frame, orient='horizontal').pack(fill=tk.X, pady=10)
        self.btn_run = ttk.Button(frame, text="ANALİZİ BAŞLAT", command=self.run_algorithms)
        self.btn_run.pack(fill=tk.X, pady=5)
        
        # Sonuç Alanı
        self.result_text = tk.Text(parent, height=20, width=35)
        self.result_text.pack(fill=tk.BOTH, expand=True, pady=10)
        
        ttk.Label(parent, textvariable=self.status_var, relief=tk.SUNKEN).pack(fill=tk.X)

    def draw_initial_graph(self):
        self.ax_map.clear()
        if self.network:
            G = self.network.graph
            pos = nx.spring_layout(G, seed=42, k=0.15, iterations=20)
            nx.draw_networkx_nodes(G, pos, node_size=20, node_color='#CCCCCC', alpha=0.6, ax=self.ax_map)
            nx.draw_networkx_edges(G, pos, width=0.5, edge_color='#DDDDDD', alpha=0.4, ax=self.ax_map)
            self.ax_map.set_title("Ağ Topolojisi (Grafik)")
            self.ax_map.axis('off')
            self.canvas_map.draw()

    def run_algorithms(self):
        if not self.network: return
        
        src = int(self.src_combo.get())
        dst = int(self.dst_combo.get())
        if src == dst:
            messagebox.showerror("Hata", "Kaynak ve hedef aynı olamaz.")
            return

        # Ağırlıkları Config'e işle
        config.W_DELAY = self.w_delay_var.get()
        config.W_RELIABILITY = self.w_rel_var.get()
        config.W_RESOURCE = self.w_res_var.get()

        self.btn_run['state'] = 'disabled'
        self.status_var.set("Algoritmalar çalışıyor...")
        self.result_text.delete(1.0, tk.END)
        self.result_text.insert(tk.END, "Lütfen bekleyin, hesaplanıyor...\n(RL eğitimi zaman alabilir)")
        
        threading.Thread(target=self._solve_thread, args=(src, dst)).start()

    def _solve_thread(self, src, dst):
        try:
            # GA Çalıştır
            ga = GeneticSolver(self.network, src, dst)
            # solve() artık (path, cost, history, pareto_data) dönüyor
            ga_path, ga_cost, ga_hist, ga_pareto = ga.solve()
            
            # RL Çalıştır
            rl = QLearningSolver(self.network, src, dst)
            # train() artık history dönüyor
            rl_hist = rl.train()
            rl_path = rl.get_path()
            rl_cost_data = self.network.calculate_cost(rl_path)
            rl_cost = rl_cost_data['score']
            
            # GUI Güncelleme
            self.root.after(0, lambda: self.show_results(src, dst, 
                                                         ga_path, ga_cost, ga_hist, ga_pareto,
                                                         rl_path, rl_cost, rl_hist))
        except Exception as e:
            # Hata Olursa Kullanıcıya Bildir ve Butonu Aç
            print(f"Hata detayı: {e}")
            self.root.after(0, lambda: messagebox.showerror("Beklenmedik Hata", f"Analiz sırasında bir hata oluştu:\n{str(e)}"))
            self.root.after(0, lambda: self.reset_ui_state())

    def reset_ui_state(self):
        """Hata durumunda arayüzü eski haline döndürür."""
        self.status_var.set("Hata oluştu. Tekrar deneyin.")
        self.btn_run['state'] = 'normal'
        self.result_text.delete(1.0, tk.END)
        self.result_text.insert(tk.END, "İşlem başarısız oldu.")

    def show_results(self, src, dst, ga_path, ga_cost, ga_hist, ga_pareto, rl_path, rl_cost, rl_hist):
        try:
            # 1. Metin Sonuçları
            metrics_ga = self.network.calculate_metrics(ga_path)
            metrics_rl = self.network.calculate_metrics(rl_path)
            
            bw_demand = self.bw_demand_var.get()
            ga_min_bw = self.network.get_path_min_bandwidth(ga_path)
            rl_min_bw = self.network.get_path_min_bandwidth(rl_path)
            
            res = f"--- SONUÇLAR ---\n"
            res += f"Kaynak: {src} -> Hedef: {dst}\n"
            res += f"Talep Edilen BW: {bw_demand} Mbps\n\n"
            
            res += " GENETİK ALGORİTMA\n"
            if metrics_ga:
                res += f"Maliyet: {metrics_ga['cost']:.4f}\n"
                res += f"Gecikme: {metrics_ga['delay']} ms\n"
                res += f"Güvenilirlik: {metrics_ga['reliability']:.5f}\n"
                res += f"Adım Sayısı: {metrics_ga['hops']}\n"
                res += f"Yolun Min BW: {ga_min_bw} Mbps"
                if ga_min_bw and ga_min_bw >= bw_demand:
                    res += " \n"
                else:
                    res += "  (Yetersiz!)\n"
            else: res += "Yol bulunamadı.\n"
            
            res += "\n Q-LEARNING (RL)\n"
            if metrics_rl:
                res += f"Maliyet: {metrics_rl['cost']:.4f}\n"
                res += f"Gecikme: {metrics_rl['delay']} ms\n"
                res += f"Güvenilirlik: {metrics_rl['reliability']:.5f}\n"
                res += f"Adım Sayısı: {metrics_rl['hops']}\n"
                res += f"Yolun Min BW: {rl_min_bw} Mbps"
                if rl_min_bw and rl_min_bw >= bw_demand:
                    res += " \n"
                else:
                    res += "  (Yetersiz!)\n"
            else: res += "Yol bulunamadı.\n"
            
            self.result_text.delete(1.0, tk.END)
            self.result_text.insert(tk.END, res)

            # 2. Harita Güncelleme (Her iki yolu da göster)
            winner_name = "GA" if ga_cost < rl_cost else "RL"
            
            self.ax_map.clear()
            G = self.network.graph
            pos = nx.spring_layout(G, seed=42, k=0.15, iterations=20)
            
            # Silik Arkaplan
            nx.draw_networkx_nodes(G, pos, node_size=20, node_color='#DDDDDD', alpha=0.5, ax=self.ax_map)
            nx.draw_networkx_edges(G, pos, width=0.5, edge_color='#EEEEEE', alpha=0.4, ax=self.ax_map)
            
            # GA Yolu (Mavi) - Kaybedense ince, kazandıysa kalın
            if ga_path and len(ga_path) >= 2:
                ga_edges = list(zip(ga_path, ga_path[1:]))
                ga_width = 3 if winner_name == "GA" else 1.5
                ga_style = 'solid' if winner_name == "GA" else 'dashed'
                nx.draw_networkx_edges(G, pos, edgelist=ga_edges, edge_color='#2196F3', 
                                      width=ga_width, style=ga_style, alpha=0.8, ax=self.ax_map)
                # GA yolu düğümleri
                ga_middle_nodes = ga_path[1:-1]  # Baş ve son hariç
                if ga_middle_nodes:
                    nx.draw_networkx_nodes(G, pos, nodelist=ga_middle_nodes, node_size=40, 
                                          node_color='#2196F3', alpha=0.7, ax=self.ax_map)
            
            # RL Yolu (Turuncu) - Kaybedense ince, kazandıysa kalın
            if rl_path and len(rl_path) >= 2:
                rl_edges = list(zip(rl_path, rl_path[1:]))
                rl_width = 3 if winner_name == "RL" else 1.5
                rl_style = 'solid' if winner_name == "RL" else 'dashed'
                nx.draw_networkx_edges(G, pos, edgelist=rl_edges, edge_color='#FF9800', 
                                      width=rl_width, style=rl_style, alpha=0.8, ax=self.ax_map)
                # RL yolu düğümleri
                rl_middle_nodes = rl_path[1:-1]  # Baş ve son hariç
                if rl_middle_nodes:
                    nx.draw_networkx_nodes(G, pos, nodelist=rl_middle_nodes, node_size=40, 
                                          node_color='#FF9800', alpha=0.7, ax=self.ax_map)
            
            # Kaynak ve Hedef (Her zaman en üstte görünsün)
            nx.draw_networkx_nodes(G, pos, nodelist=[src], node_size=150, node_color='#4CAF50', 
                                  edgecolors='white', linewidths=2, ax=self.ax_map)
            nx.draw_networkx_nodes(G, pos, nodelist=[dst], node_size=150, node_color='#F44336', 
                                  edgecolors='white', linewidths=2, ax=self.ax_map)
            
            # Legend ve Başlık
            from matplotlib.lines import Line2D
            legend_elements = [
                Line2D([0], [0], color='#2196F3', linewidth=2, label=f'GA Yolu (Maliyet: {ga_cost:.2f})'),
                Line2D([0], [0], color='#FF9800', linewidth=2, label=f'RL Yolu (Maliyet: {rl_cost:.2f})'),
                Line2D([0], [0], marker='o', color='w', markerfacecolor='#4CAF50', markersize=10, label='Kaynak (S)'),
                Line2D([0], [0], marker='o', color='w', markerfacecolor='#F44336', markersize=10, label='Hedef (D)')
            ]
            self.ax_map.legend(handles=legend_elements, loc='upper left', fontsize=8)
            self.ax_map.set_title(f"Yol Karşılaştırması - Kazanan: {winner_name} ")
            
            self.ax_map.axis('off')
            self.canvas_map.draw()

            # 3. Analiz Grafikleri (Sekme 2)
            # Komple temizlik ve yeniden oluşturma (Hata önleyici kesin çözüm)
            self.fig_analysis.clear()
            gs = gridspec.GridSpec(2, 1, height_ratios=[1, 1], figure=self.fig_analysis)
            
            self.ax_convergence = self.fig_analysis.add_subplot(gs[0])
            self.ax_pareto = self.fig_analysis.add_subplot(gs[1])

            # A) Yakınsama Grafiği (Convergence)
            self.ax_convergence.set_title("Yakınsama Grafiği (Öğrenme Eğrisi)")
            self.ax_convergence.set_xlabel("İterasyon (Gen / Episode)")
            self.ax_convergence.set_ylabel("Maliyet (Cost)")
            self.ax_convergence.grid(True, linestyle='--', alpha=0.6)
            
            if ga_hist:
                self.ax_convergence.plot(ga_hist, label="Genetik (Nesiller)", color='blue', marker='o', markersize=3)
            if rl_hist:
                x_rl = [i*100 for i in range(len(rl_hist))]
                self.ax_convergence.plot(x_rl, rl_hist, label="Q-Learning (x100 Ep.)", color='orange')
                
            self.ax_convergence.legend()

            # B) Pareto Frontier Analizi (Scatter Plot)
            self.ax_pareto.set_title("Pareto Analizi (Alternatif Çözümler)")
            self.ax_pareto.set_xlabel("Gecikme (ms) [Daha az iyi]")
            self.ax_pareto.set_ylabel("Güvenilirlik (Reliability) [Daha çok iyi]")
            self.ax_pareto.grid(True, linestyle='--', alpha=0.6)
            
            # GA popülasyonundaki tüm bireyleri çiz
            if ga_pareto:
                delays = [d['delay'] for d in ga_pareto]
                reliabilities = [d['reliability'] for d in ga_pareto]
                costs = [d['cost'] for d in ga_pareto]
                
                sc = self.ax_pareto.scatter(delays, reliabilities, c=costs, cmap='inferno_r', label="GA Çözüm Adayları", alpha=0.8, edgecolors='black')
                self.fig_analysis.colorbar(sc, ax=self.ax_pareto, label="Toplam Maliyet")
                
            # RL Sonucunu da ekle
            if metrics_rl:
                self.ax_pareto.scatter([metrics_rl['delay']], [metrics_rl['reliability']], 
                                       color='blue', marker='X', s=120, label="RL Sonucu", zorder=5, edgecolors='white')
                
            self.ax_pareto.legend()
            
            # Grafiklerin sığması için boşlukları ayarla
            self.fig_analysis.tight_layout(pad=2.0)
            self.canvas_analysis.draw()

            self.status_var.set("Analiz Tamamlandı.")

        except Exception as e:
            print(f"show_results hatası: {e}")
            messagebox.showerror("Görselleştirme Hatası", f"Sonuçlar gösterilirken hata oluştu:\n{e}")
        finally:
            self.btn_run['state'] = 'normal'
        
        # Sonuçlar hazır olunca Analiz sekmesine geçiş önerilebilir ama kullanıcıda kalsın
        # self.tabs.select(1) 

if __name__ == "__main__":
    root = tk.Tk()
    app = QoSRoutingApp(root)
    root.mainloop()
