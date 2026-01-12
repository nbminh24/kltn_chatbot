import json
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
from pathlib import Path
from sklearn.metrics import confusion_matrix
import re

class ConfusionMatrixAnalysis:
    def __init__(self, results_path="results"):
        self.results_path = results_path
        
    def load_test_results(self):
        intent_report_path = Path(self.results_path) / "intent_report.json"
        
        if not intent_report_path.exists():
            print(f"⚠️ File {intent_report_path} không tồn tại.")
            print("ℹ️ Bạn cần chạy: rasa test nlu --cross-validation")
            return None
            
        with open(intent_report_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        return data
    
    def extract_metrics(self, data):
        if not data:
            return None
            
        metrics_list = []
        
        for intent, metrics in data.items():
            if intent in ['accuracy', 'macro avg', 'weighted avg', 'micro avg']:
                continue
                
            metrics_list.append({
                'Intent': intent,
                'Precision': metrics.get('precision', 0),
                'Recall': metrics.get('recall', 0),
                'F1-score': metrics.get('f1-score', 0),
                'Support': metrics.get('support', 0)
            })
        
        df = pd.DataFrame(metrics_list)
        df = df.sort_values('F1-score', ascending=False)
        
        avg_metrics = {
            'macro': data.get('macro avg', {}),
            'weighted': data.get('weighted avg', {}),
            'accuracy': data.get('accuracy', 0)
        }
        
        return df, avg_metrics
    
    def generate_metrics_table(self, save_path="evaluation/reports/2_intent_metrics.png"):
        data = self.load_test_results()
        
        if not data:
            self.generate_placeholder_metrics(save_path)
            return save_path
            
        df, avg_metrics = self.extract_metrics(data)
        
        num_intents = len(df)
        fig_height = max(20, num_intents * 0.5 + 8)
        
        fig = plt.figure(figsize=(18, fig_height))
        gs = fig.add_gridspec(2, 2, hspace=0.3, wspace=0.3, height_ratios=[num_intents * 0.4, 8])
        
        ax1 = fig.add_subplot(gs[0, :])
        ax2 = fig.add_subplot(gs[1, 0])
        ax3 = fig.add_subplot(gs[1, 1])
        
        fig.suptitle(f'Intent Classification Metrics - All {num_intents} Intents', fontsize=16, fontweight='bold')
        
        ax1.axis('tight')
        ax1.axis('off')
        
        table_data = df.values.tolist()
        
        table = ax1.table(cellText=table_data,
                         colLabels=df.columns.tolist(),
                         cellLoc='center',
                         loc='center',
                         colWidths=[0.35, 0.13, 0.13, 0.13, 0.13])
        table.auto_set_font_size(False)
        table.set_fontsize(7)
        table.scale(1, 1.2)
        
        for i in range(len(df.columns)):
            table[(0, i)].set_facecolor('#4472C4')
            table[(0, i)].set_text_props(weight='bold', color='white')
        
        for i in range(1, len(table_data) + 1):
            for j in range(len(df.columns)):
                if j > 0:
                    val = table_data[i-1][j]
                    if isinstance(val, float) and val < 0.85:
                        table[(i, j)].set_facecolor('#FFE699')
                    else:
                        table[(i, j)].set_facecolor('#E7E6E6' if i % 2 == 0 else 'white')
                else:
                    table[(i, j)].set_facecolor('#E7E6E6' if i % 2 == 0 else 'white')
        
        ax1.set_title(f'All {num_intents} Intent Metrics (Sorted by F1-score)', fontsize=12, fontweight='bold', pad=20)
        
        avg_table_data = [
            ['Macro Avg', f"{avg_metrics['macro'].get('precision', 0):.3f}", 
             f"{avg_metrics['macro'].get('recall', 0):.3f}", 
             f"{avg_metrics['macro'].get('f1-score', 0):.3f}"],
            ['Weighted Avg', f"{avg_metrics['weighted'].get('precision', 0):.3f}", 
             f"{avg_metrics['weighted'].get('recall', 0):.3f}", 
             f"{avg_metrics['weighted'].get('f1-score', 0):.3f}"],
            ['Accuracy', '-', '-', f"{avg_metrics['accuracy']:.3f}"]
        ]
        
        ax2.axis('tight')
        ax2.axis('off')
        table2 = ax2.table(cellText=avg_table_data,
                          colLabels=['Metric', 'Precision', 'Recall', 'F1-score'],
                          cellLoc='center',
                          loc='center',
                          colWidths=[0.3, 0.2, 0.2, 0.2])
        table2.auto_set_font_size(False)
        table2.set_fontsize(10)
        table2.scale(1, 2.5)
        
        for i in range(4):
            table2[(0, i)].set_facecolor('#70AD47')
            table2[(0, i)].set_text_props(weight='bold', color='white')
        
        for i in range(1, 4):
            for j in range(4):
                table2[(i, j)].set_facecolor('#E2EFDA')
        
        ax2.set_title('Overall Performance Metrics', fontsize=11, fontweight='bold', pad=10)
        
        metrics_names = ['Precision', 'Recall', 'F1-score']
        macro_vals = [avg_metrics['macro'].get('precision', 0),
                     avg_metrics['macro'].get('recall', 0),
                     avg_metrics['macro'].get('f1-score', 0)]
        weighted_vals = [avg_metrics['weighted'].get('precision', 0),
                        avg_metrics['weighted'].get('recall', 0),
                        avg_metrics['weighted'].get('f1-score', 0)]
        
        x = np.arange(len(metrics_names))
        width = 0.35
        
        bars1 = ax3.bar(x - width/2, macro_vals, width, label='Macro Avg', color='#4472C4')
        bars2 = ax3.bar(x + width/2, weighted_vals, width, label='Weighted Avg', color='#70AD47')
        
        ax3.set_ylabel('Score', fontweight='bold')
        ax3.set_title('Macro vs Weighted Average', fontsize=11, fontweight='bold')
        ax3.set_xticks(x)
        ax3.set_xticklabels(metrics_names)
        ax3.legend()
        ax3.set_ylim([0, 1])
        ax3.grid(axis='y', alpha=0.3, linestyle='--')
        
        for bars in [bars1, bars2]:
            for bar in bars:
                height = bar.get_height()
                ax3.text(bar.get_x() + bar.get_width()/2., height,
                        f'{height:.3f}', ha='center', va='bottom', fontsize=9, fontweight='bold')
        
        Path(save_path).parent.mkdir(parents=True, exist_ok=True)
        plt.savefig(save_path, dpi=300, bbox_inches='tight')
        plt.close()
        
        print(f"✅ Intent metrics saved to: {save_path}")
        return save_path
    
    def generate_placeholder_metrics(self, save_path):
        fig, ax = plt.subplots(figsize=(12, 8))
        
        sample_data = [
            ['greet', 0.98, 0.97, 0.98, 120],
            ['search_product', 0.93, 0.91, 0.92, 200],
            ['ask_product_price', 0.95, 0.94, 0.95, 150],
            ['check_product_availability', 0.90, 0.88, 0.89, 110],
            ['add_to_cart', 0.92, 0.90, 0.91, 95],
        ]
        
        ax.axis('tight')
        ax.axis('off')
        
        table = ax.table(cellText=sample_data,
                        colLabels=['Intent', 'Precision', 'Recall', 'F1-score', 'Support'],
                        cellLoc='center',
                        loc='center')
        table.auto_set_font_size(False)
        table.set_fontsize(11)
        table.scale(1, 2)
        
        ax.text(0.5, 0.95, '⚠️ PLACEHOLDER - Chạy: rasa test nlu --cross-validation', 
                ha='center', va='top', transform=ax.transAxes,
                fontsize=12, color='red', fontweight='bold')
        
        Path(save_path).parent.mkdir(parents=True, exist_ok=True)
        plt.savefig(save_path, dpi=300, bbox_inches='tight')
        plt.close()
        
        print(f"⚠️ Placeholder metrics saved to: {save_path}")
    
    def load_confusion_matrix_data(self):
        intent_report_path = Path(self.results_path) / "intent_report.json"
        intent_errors_path = Path(self.results_path) / "intent_errors.json"
        
        if not intent_report_path.exists():
            return None, None
            
        with open(intent_report_path, 'r', encoding='utf-8') as f:
            report_data = json.load(f)
        
        intents = [k for k in report_data.keys() if k not in ['accuracy', 'macro avg', 'weighted avg', 'micro avg']]
        intents = sorted(intents)
        
        n = len(intents)
        cm = np.zeros((n, n), dtype=int)
        
        intent_to_idx = {intent: i for i, intent in enumerate(intents)}
        
        for intent, metrics in report_data.items():
            if intent in intent_to_idx:
                true_idx = intent_to_idx[intent]
                support = int(metrics.get('support', 0))
                confused_with = metrics.get('confused_with', {})
                
                total_confused = sum(confused_with.values())
                correct_predictions = support - total_confused
                
                cm[true_idx, true_idx] = correct_predictions
                
                for pred_intent, count in confused_with.items():
                    if pred_intent in intent_to_idx:
                        pred_idx = intent_to_idx[pred_intent]
                        cm[true_idx, pred_idx] = count
        
        return cm, intents
    
    def generate_confusion_matrix(self, save_path="evaluation/reports/3_confusion_matrix.png"):
        cm, intents = self.load_confusion_matrix_data()
        
        if cm is None:
            self.generate_placeholder_confmat(save_path)
            return save_path
        
        n = len(intents)
        fig_size = max(16, n * 0.35)
        
        fig, ax = plt.subplots(figsize=(fig_size, fig_size))
        
        annot_fontsize = 5 if n > 40 else 7 if n > 30 else 9
        
        sns.heatmap(cm, annot=True, fmt='d', cmap='Blues', 
                   xticklabels=intents, yticklabels=intents,
                   cbar_kws={'label': 'Count'}, ax=ax,
                   square=True, linewidths=0.3, linecolor='lightgray',
                   annot_kws={'fontsize': annot_fontsize})
        
        ax.set_xlabel('Predicted Intent', fontweight='bold', fontsize=12)
        ax.set_ylabel('True Intent', fontweight='bold', fontsize=12)
        ax.set_title(f'Intent Confusion Matrix - All {n} Intents', 
                    fontsize=14, fontweight='bold', pad=20)
        
        plt.setp(ax.get_xticklabels(), rotation=90, ha='right', fontsize=7)
        plt.setp(ax.get_yticklabels(), rotation=0, fontsize=7)
        
        plt.tight_layout()
        Path(save_path).parent.mkdir(parents=True, exist_ok=True)
        plt.savefig(save_path, dpi=300, bbox_inches='tight')
        plt.close()
        
        print(f"✅ Confusion matrix ({n}x{n}) saved to: {save_path}")
        return save_path
    
    def generate_placeholder_confmat(self, save_path):
        intents = ['greet', 'search_product', 'ask_price', 'add_to_cart', 'nlu_fallback']
        n = len(intents)
        
        cm = np.zeros((n, n))
        for i in range(n):
            cm[i, i] = np.random.randint(80, 100)
            for j in range(n):
                if i != j:
                    cm[i, j] = np.random.randint(0, 10)
        
        fig, ax = plt.subplots(figsize=(10, 8))
        
        sns.heatmap(cm, annot=True, fmt='.0f', cmap='Blues', 
                   xticklabels=intents, yticklabels=intents,
                   cbar_kws={'label': 'Count'}, ax=ax)
        
        ax.set_xlabel('Predicted Intent', fontweight='bold', fontsize=12)
        ax.set_ylabel('True Intent', fontweight='bold', fontsize=12)
        ax.set_title('Intent Confusion Matrix\n⚠️ PLACEHOLDER - Chạy: rasa test nlu', 
                    fontsize=14, fontweight='bold', color='red')
        
        plt.tight_layout()
        Path(save_path).parent.mkdir(parents=True, exist_ok=True)
        plt.savefig(save_path, dpi=300, bbox_inches='tight')
        plt.close()
        
        print(f"⚠️ Placeholder confusion matrix saved to: {save_path}")

if __name__ == "__main__":
    cma = ConfusionMatrixAnalysis()
    cma.generate_metrics_table()
    cma.generate_confusion_matrix()
