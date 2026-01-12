import json
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
from pathlib import Path

class ConfidenceDistribution:
    def __init__(self, results_path="results", threshold=0.7):
        self.results_path = results_path
        self.threshold = threshold
        
    def load_predictions(self):
        intent_errors_path = Path(self.results_path) / "intent_errors.json"
        
        if not intent_errors_path.exists():
            print(f"⚠️ File {intent_errors_path} không tồn tại.")
            print("ℹ️ Bạn cần chạy: rasa test nlu --cross-validation")
            return None
            
        with open(intent_errors_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        return data
    
    def analyze_confidence(self, data):
        if not data:
            return None
            
        correct_confidences = []
        incorrect_confidences = []
        
        for item in data:
            confidence = item.get('confidence', 0)
            intent = item.get('intent', '')
            predicted = item.get('predicted', '')
            
            if intent == predicted:
                correct_confidences.append(confidence)
            else:
                incorrect_confidences.append(confidence)
        
        return correct_confidences, incorrect_confidences
    
    def generate_distribution_plot(self, save_path="evaluation/reports/4_confidence_distribution.png"):
        data = self.load_predictions()
        
        if not data:
            self.generate_placeholder_distribution(save_path)
            return save_path
            
        correct_conf, incorrect_conf = self.analyze_confidence(data)
        
        fig = plt.figure(figsize=(16, 10))
        gs = fig.add_gridspec(2, 2, hspace=0.3, wspace=0.3)
        
        ax1 = fig.add_subplot(gs[0, :])
        ax2 = fig.add_subplot(gs[1, 0])
        ax3 = fig.add_subplot(gs[1, 1])
        
        fig.suptitle('Confidence Score Distribution Analysis', fontsize=16, fontweight='bold')
        
        bins = np.linspace(0, 1, 21)
        
        ax1.hist(correct_conf, bins=bins, alpha=0.7, label='Correct Predictions', 
                color='#70AD47', edgecolor='black', linewidth=0.5)
        ax1.hist(incorrect_conf, bins=bins, alpha=0.7, label='Incorrect Predictions', 
                color='#C55A11', edgecolor='black', linewidth=0.5)
        ax1.axvline(x=self.threshold, color='red', linestyle='--', linewidth=2, 
                   label=f'Threshold = {self.threshold}')
        
        ax1.set_xlabel('Confidence Score', fontweight='bold', fontsize=11)
        ax1.set_ylabel('Frequency', fontweight='bold', fontsize=11)
        ax1.set_title('Confidence Distribution: Correct vs Incorrect Predictions', 
                     fontsize=12, fontweight='bold')
        ax1.legend(loc='upper left', fontsize=10)
        ax1.grid(axis='y', alpha=0.3, linestyle='--')
        ax1.set_xlim([0, 1])
        
        total = len(correct_conf) + len(incorrect_conf)
        above_threshold_correct = sum(1 for c in correct_conf if c >= self.threshold)
        above_threshold_incorrect = sum(1 for c in incorrect_conf if c >= self.threshold)
        below_threshold = sum(1 for c in correct_conf + incorrect_conf if c < self.threshold)
        
        stats_data = [
            ['Tổng số predictions', f'{total}'],
            ['Correct predictions', f'{len(correct_conf)} ({len(correct_conf)/total*100:.1f}%)'],
            ['Incorrect predictions', f'{len(incorrect_conf)} ({len(incorrect_conf)/total*100:.1f}%)'],
            ['', ''],
            [f'Confidence ≥ {self.threshold} (Correct)', f'{above_threshold_correct} ({above_threshold_correct/len(correct_conf)*100:.1f}%)'],
            [f'Confidence ≥ {self.threshold} (Incorrect)', f'{above_threshold_incorrect} ({above_threshold_incorrect/len(incorrect_conf)*100 if len(incorrect_conf) > 0 else 0:.1f}%)'],
            [f'Confidence < {self.threshold} (→ Fallback)', f'{below_threshold} ({below_threshold/total*100:.1f}%)'],
        ]
        
        ax2.axis('tight')
        ax2.axis('off')
        
        table = ax2.table(cellText=stats_data,
                         colLabels=['Metric', 'Value'],
                         cellLoc='left',
                         loc='center',
                         colWidths=[0.6, 0.4])
        table.auto_set_font_size(False)
        table.set_fontsize(10)
        table.scale(1, 2)
        
        for i in range(len(stats_data) + 1):
            if i == 0:
                table[(i, 0)].set_facecolor('#4472C4')
                table[(i, 1)].set_facecolor('#4472C4')
                table[(i, 0)].set_text_props(weight='bold', color='white')
                table[(i, 1)].set_text_props(weight='bold', color='white')
            elif i == 4:
                table[(i, 0)].set_facecolor('white')
                table[(i, 1)].set_facecolor('white')
            else:
                table[(i, 0)].set_facecolor('#E7E6E6' if i % 2 == 0 else 'white')
                table[(i, 1)].set_facecolor('#E7E6E6' if i % 2 == 0 else 'white')
        
        ax2.set_title('Statistics Summary', fontsize=11, fontweight='bold', pad=10)
        
        bins_box = [0, 0.3, 0.5, self.threshold, 0.9, 1.0]
        labels = ['0-0.3', '0.3-0.5', f'0.5-{self.threshold}', f'{self.threshold}-0.9', '0.9-1.0']
        
        correct_binned = np.histogram(correct_conf, bins=bins_box)[0]
        incorrect_binned = np.histogram(incorrect_conf, bins=bins_box)[0]
        
        x = np.arange(len(labels))
        width = 0.35
        
        bars1 = ax3.bar(x - width/2, correct_binned, width, label='Correct', color='#70AD47')
        bars2 = ax3.bar(x + width/2, incorrect_binned, width, label='Incorrect', color='#C55A11')
        
        ax3.set_xlabel('Confidence Range', fontweight='bold')
        ax3.set_ylabel('Count', fontweight='bold')
        ax3.set_title('Confidence Score Binned Distribution', fontsize=11, fontweight='bold')
        ax3.set_xticks(x)
        ax3.set_xticklabels(labels)
        ax3.legend()
        ax3.grid(axis='y', alpha=0.3, linestyle='--')
        
        for bars in [bars1, bars2]:
            for bar in bars:
                height = bar.get_height()
                if height > 0:
                    ax3.text(bar.get_x() + bar.get_width()/2., height,
                            f'{int(height)}', ha='center', va='bottom', fontsize=9)
        
        Path(save_path).parent.mkdir(parents=True, exist_ok=True)
        plt.savefig(save_path, dpi=300, bbox_inches='tight')
        plt.close()
        
        print(f"✅ Confidence distribution saved to: {save_path}")
        return save_path
    
    def generate_placeholder_distribution(self, save_path):
        np.random.seed(42)
        correct_conf = np.random.beta(8, 2, 800)
        incorrect_conf = np.random.beta(2, 5, 150)
        
        fig, ax = plt.subplots(figsize=(12, 8))
        
        bins = np.linspace(0, 1, 21)
        
        ax.hist(correct_conf, bins=bins, alpha=0.7, label='Correct Predictions (Sample)', 
               color='#70AD47', edgecolor='black', linewidth=0.5)
        ax.hist(incorrect_conf, bins=bins, alpha=0.7, label='Incorrect Predictions (Sample)', 
               color='#C55A11', edgecolor='black', linewidth=0.5)
        ax.axvline(x=self.threshold, color='red', linestyle='--', linewidth=2, 
                  label=f'Threshold = {self.threshold}')
        
        ax.set_xlabel('Confidence Score', fontweight='bold', fontsize=12)
        ax.set_ylabel('Frequency', fontweight='bold', fontsize=12)
        ax.set_title('Confidence Distribution\n⚠️ PLACEHOLDER - Chạy: rasa test nlu', 
                    fontsize=14, fontweight='bold', color='red')
        ax.legend(loc='upper left', fontsize=11)
        ax.grid(axis='y', alpha=0.3, linestyle='--')
        ax.set_xlim([0, 1])
        
        Path(save_path).parent.mkdir(parents=True, exist_ok=True)
        plt.savefig(save_path, dpi=300, bbox_inches='tight')
        plt.close()
        
        print(f"⚠️ Placeholder confidence distribution saved to: {save_path}")

if __name__ == "__main__":
    cd = ConfidenceDistribution(threshold=0.7)
    cd.generate_distribution_plot()
