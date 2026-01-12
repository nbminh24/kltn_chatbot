import yaml
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
from pathlib import Path
import numpy as np

class DatasetStatistics:
    def __init__(self, nlu_path="data/nlu.yml"):
        from pathlib import Path
        if not Path(nlu_path).exists():
            nlu_path = "../data/nlu.yml"
        self.nlu_path = nlu_path
        self.stats = {}
        
    def load_nlu_data(self):
        with open(self.nlu_path, 'r', encoding='utf-8') as f:
            data = yaml.safe_load(f)
        return data['nlu']
    
    def calculate_statistics(self):
        nlu_data = self.load_nlu_data()
        
        intent_counts = {}
        total_utterances = 0
        
        for intent_block in nlu_data:
            intent_name = intent_block['intent']
            examples = intent_block['examples']
            
            utterances = [line.strip() for line in examples.split('\n') if line.strip() and not line.strip().startswith('-')]
            utterances = [u.lstrip('- ') for u in utterances if u]
            
            count = len(utterances)
            intent_counts[intent_name] = count
            total_utterances += count
        
        self.stats = {
            'num_intents': len(intent_counts),
            'total_utterances': total_utterances,
            'avg_utterances': np.mean(list(intent_counts.values())),
            'max_utterances': max(intent_counts.values()),
            'min_utterances': min(intent_counts.values()),
            'median_utterances': np.median(list(intent_counts.values())),
            'std_utterances': np.std(list(intent_counts.values())),
            'intent_counts': intent_counts
        }
        
        return self.stats
    
    def generate_table(self, save_path="evaluation/reports/1_dataset_stats.png"):
        stats = self.calculate_statistics()
        
        fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(16, 6))
        fig.suptitle('Dataset Statistics - Rasa NLU', fontsize=16, fontweight='bold')
        
        table_data = [
            ['Số lượng Intents', f"{stats['num_intents']}"],
            ['Tổng số Utterances', f"{stats['total_utterances']}"],
            ['Trung bình Utterances/Intent', f"{stats['avg_utterances']:.2f}"],
            ['Trung vị Utterances/Intent', f"{stats['median_utterances']:.0f}"],
            ['Độ lệch chuẩn', f"{stats['std_utterances']:.2f}"],
            ['Max Utterances', f"{stats['max_utterances']}"],
            ['Min Utterances', f"{stats['min_utterances']}"]
        ]
        
        ax1.axis('tight')
        ax1.axis('off')
        table = ax1.table(cellText=table_data,
                         colLabels=['Metric', 'Value'],
                         cellLoc='left',
                         loc='center',
                         colWidths=[0.6, 0.4])
        table.auto_set_font_size(False)
        table.set_fontsize(11)
        table.scale(1, 2)
        
        for i in range(len(table_data) + 1):
            if i == 0:
                table[(i, 0)].set_facecolor('#4472C4')
                table[(i, 1)].set_facecolor('#4472C4')
                table[(i, 0)].set_text_props(weight='bold', color='white')
                table[(i, 1)].set_text_props(weight='bold', color='white')
            else:
                table[(i, 0)].set_facecolor('#E7E6E6' if i % 2 == 0 else 'white')
                table[(i, 1)].set_facecolor('#E7E6E6' if i % 2 == 0 else 'white')
        
        sorted_intents = sorted(stats['intent_counts'].items(), key=lambda x: x[1], reverse=True)[:15]
        intents, counts = zip(*sorted_intents)
        
        colors = plt.cm.viridis(np.linspace(0.3, 0.9, len(intents)))
        bars = ax2.barh(range(len(intents)), counts, color=colors)
        ax2.set_yticks(range(len(intents)))
        ax2.set_yticklabels(intents, fontsize=9)
        ax2.set_xlabel('Số lượng Examples', fontsize=11, fontweight='bold')
        ax2.set_title('Top 15 Intents theo số lượng Examples', fontsize=12, fontweight='bold')
        ax2.invert_yaxis()
        ax2.grid(axis='x', alpha=0.3, linestyle='--')
        
        for i, (bar, count) in enumerate(zip(bars, counts)):
            ax2.text(count + 1, i, str(count), va='center', fontsize=9, fontweight='bold')
        
        plt.tight_layout()
        Path(save_path).parent.mkdir(parents=True, exist_ok=True)
        plt.savefig(save_path, dpi=300, bbox_inches='tight')
        plt.close()
        
        print(f"✅ Dataset statistics saved to: {save_path}")
        return save_path
    
    def export_to_csv(self, save_path="evaluation/reports/dataset_stats.csv"):
        stats = self.calculate_statistics()
        
        df = pd.DataFrame(list(stats['intent_counts'].items()), 
                         columns=['Intent', 'Utterances'])
        df = df.sort_values('Utterances', ascending=False)
        
        df.to_csv(save_path, index=False, encoding='utf-8-sig')
        print(f"✅ CSV exported to: {save_path}")
        return save_path

if __name__ == "__main__":
    ds = DatasetStatistics()
    ds.generate_table()
    ds.export_to_csv()
