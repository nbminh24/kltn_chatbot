import json
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
from pathlib import Path

class FallbackAnalysis:
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
    
    def categorize_predictions(self, data):
        if not data:
            return None
            
        correct_high_conf = 0
        fallback_cases = 0
        open_ended_cases = 0
        incorrect_high_conf = 0
        
        fallback_intents = []
        open_ended_intents = []
        
        for item in data:
            confidence = item.get('confidence', 0)
            intent = item.get('intent', '')
            predicted = item.get('predicted', '')
            
            if confidence >= self.threshold:
                if intent == predicted:
                    correct_high_conf += 1
                else:
                    incorrect_high_conf += 1
            else:
                if predicted in ['nlu_fallback', 'out_of_scope']:
                    fallback_cases += 1
                    fallback_intents.append(intent)
                elif predicted in ['open_ended_query', 'ask_advice', 'ask_general_question']:
                    open_ended_cases += 1
                    open_ended_intents.append(intent)
                else:
                    fallback_cases += 1
                    fallback_intents.append(intent)
        
        total = len(data)
        
        stats = {
            'total': total,
            'correct_high_conf': correct_high_conf,
            'fallback': fallback_cases,
            'open_ended': open_ended_cases,
            'incorrect_high_conf': incorrect_high_conf,
            'fallback_intents': fallback_intents,
            'open_ended_intents': open_ended_intents
        }
        
        return stats
    
    def generate_fallback_analysis(self, save_path="evaluation/reports/5_fallback_analysis.png"):
        data = self.load_predictions()
        
        if not data:
            self.generate_placeholder_fallback(save_path)
            return save_path
            
        stats = self.categorize_predictions(data)
        
        fig = plt.figure(figsize=(16, 10))
        gs = fig.add_gridspec(2, 2, hspace=0.3, wspace=0.3)
        
        ax1 = fig.add_subplot(gs[0, 0])
        ax2 = fig.add_subplot(gs[0, 1])
        ax3 = fig.add_subplot(gs[1, :])
        
        fig.suptitle('Fallback & LLM Usage Analysis (Rasa + Gemini)', fontsize=16, fontweight='bold')
        
        total = stats['total']
        categories = ['Correct Intent\n(High Conf)', 'NLU Fallback\n(Low Conf)', 
                     'Open-ended\n(LLM)', 'Incorrect\n(High Conf)']
        values = [stats['correct_high_conf'], stats['fallback'], 
                 stats['open_ended'], stats['incorrect_high_conf']]
        percentages = [v/total*100 for v in values]
        
        colors = ['#70AD47', '#FFC000', '#4472C4', '#C55A11']
        wedges, texts, autotexts = ax1.pie(values, labels=categories, autopct='%1.1f%%',
                                           colors=colors, startangle=90,
                                           textprops={'fontsize': 10, 'weight': 'bold'})
        
        for autotext in autotexts:
            autotext.set_color('white')
            autotext.set_fontsize(11)
            autotext.set_weight('bold')
        
        ax1.set_title('Distribution of Prediction Categories', fontsize=12, fontweight='bold', pad=20)
        
        table_data = [
            ['Correct Intent (High Confidence)', f'{stats["correct_high_conf"]}', f'{percentages[0]:.1f}%'],
            ['NLU Fallback (Low Confidence)', f'{stats["fallback"]}', f'{percentages[1]:.1f}%'],
            ['Open-ended Advice (LLM)', f'{stats["open_ended"]}', f'{percentages[2]:.1f}%'],
            ['Incorrect (High Confidence)', f'{stats["incorrect_high_conf"]}', f'{percentages[3]:.1f}%'],
            ['', '', ''],
            ['TOTAL', f'{total}', '100.0%'],
        ]
        
        ax2.axis('tight')
        ax2.axis('off')
        
        table = ax2.table(cellText=table_data,
                         colLabels=['Category', 'Count', 'Percentage'],
                         cellLoc='left',
                         loc='center',
                         colWidths=[0.5, 0.2, 0.2])
        table.auto_set_font_size(False)
        table.set_fontsize(10)
        table.scale(1, 2.2)
        
        for i in range(len(table_data) + 1):
            if i == 0:
                for j in range(3):
                    table[(i, j)].set_facecolor('#4472C4')
                    table[(i, j)].set_text_props(weight='bold', color='white')
            elif i == 6:
                for j in range(3):
                    table[(i, j)].set_facecolor('#70AD47')
                    table[(i, j)].set_text_props(weight='bold', color='white')
            elif i == 5:
                for j in range(3):
                    table[(i, j)].set_facecolor('white')
            else:
                for j in range(3):
                    table[(i, j)].set_facecolor('#E7E6E6' if i % 2 == 0 else 'white')
        
        ax2.set_title('Detailed Statistics', fontsize=12, fontweight='bold', pad=10)
        
        key_insights = [
            f"✅ Rasa xử lý thành công: {percentages[0]:.1f}% cases",
            f"⚠️ Fallback rate: {percentages[1]:.1f}% (threshold < {self.threshold})",
            f"🤖 LLM (Gemini) chỉ dùng cho: {percentages[2]:.1f}% cases",
            f"❌ Cần cải thiện: {percentages[3]:.1f}% (predicted sai dù confident)",
            "",
            f"💡 Kết luận: LLM chỉ là bổ trợ ({percentages[2]:.1f}%), không phải core engine",
            f"💡 Rasa NLU đảm nhận chính: {percentages[0] + percentages[1]:.1f}% workload"
        ]
        
        ax3.axis('off')
        
        y_pos = 0.9
        for insight in key_insights:
            if insight == "":
                y_pos -= 0.08
                continue
            
            if insight.startswith("💡"):
                ax3.text(0.05, y_pos, insight, fontsize=12, weight='bold', 
                        transform=ax3.transAxes, color='#4472C4',
                        bbox=dict(boxstyle='round,pad=0.5', facecolor='#E7E6E6', edgecolor='#4472C4', linewidth=2))
            else:
                ax3.text(0.05, y_pos, insight, fontsize=11, transform=ax3.transAxes)
            
            y_pos -= 0.12
        
        ax3.set_title('Key Insights & Justification for Hybrid Approach', 
                     fontsize=12, fontweight='bold', pad=10, loc='left')
        
        Path(save_path).parent.mkdir(parents=True, exist_ok=True)
        plt.savefig(save_path, dpi=300, bbox_inches='tight')
        plt.close()
        
        print(f"✅ Fallback analysis saved to: {save_path}")
        return save_path
    
    def generate_placeholder_fallback(self, save_path):
        np.random.seed(42)
        
        fig = plt.figure(figsize=(14, 8))
        gs = fig.add_gridspec(1, 2, hspace=0.3, wspace=0.3)
        
        ax1 = fig.add_subplot(gs[0, 0])
        ax2 = fig.add_subplot(gs[0, 1])
        
        fig.suptitle('Fallback Analysis\n⚠️ PLACEHOLDER - Chạy: rasa test nlu', 
                    fontsize=14, fontweight='bold', color='red')
        
        categories = ['Correct Intent', 'NLU Fallback', 'Open-ended (LLM)', 'Incorrect']
        values = [850, 100, 50, 50]
        percentages = [v/sum(values)*100 for v in values]
        
        colors = ['#70AD47', '#FFC000', '#4472C4', '#C55A11']
        wedges, texts, autotexts = ax1.pie(values, labels=categories, autopct='%1.1f%%',
                                           colors=colors, startangle=90)
        
        for autotext in autotexts:
            autotext.set_color('white')
            autotext.set_fontsize(11)
            autotext.set_weight('bold')
        
        ax1.set_title('Sample Distribution', fontsize=12, fontweight='bold')
        
        table_data = [
            ['Correct Intent', '850', '85.0%'],
            ['NLU Fallback', '100', '10.0%'],
            ['Open-ended (LLM)', '50', '5.0%'],
            ['Incorrect', '50', '5.0%'],
        ]
        
        ax2.axis('tight')
        ax2.axis('off')
        
        table = ax2.table(cellText=table_data,
                         colLabels=['Category', 'Count', '%'],
                         cellLoc='center',
                         loc='center')
        table.auto_set_font_size(False)
        table.set_fontsize(11)
        table.scale(1, 2.5)
        
        ax2.set_title('Sample Statistics', fontsize=12, fontweight='bold')
        
        Path(save_path).parent.mkdir(parents=True, exist_ok=True)
        plt.savefig(save_path, dpi=300, bbox_inches='tight')
        plt.close()
        
        print(f"⚠️ Placeholder fallback analysis saved to: {save_path}")

if __name__ == "__main__":
    fa = FallbackAnalysis(threshold=0.7)
    fa.generate_fallback_analysis()
