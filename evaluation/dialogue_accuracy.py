import json
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
from pathlib import Path

class DialogueAccuracy:
    def __init__(self, results_path="results"):
        self.results_path = results_path
        
    def load_story_results(self):
        story_report_path = Path(self.results_path) / "story_report.json"
        
        if not story_report_path.exists():
            print(f"⚠️ File {story_report_path} không tồn tại.")
            print("ℹ️ Bạn cần chạy: rasa test core")
            return None
            
        with open(story_report_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        return data
    
    def analyze_dialogue_metrics(self, data):
        if not data:
            return None
            
        total_stories = data.get('total_stories', 0)
        correct_stories = data.get('correct_stories', 0)
        total_actions = data.get('total_actions', 0)
        correct_actions = data.get('correct_actions', 0)
        
        story_accuracy = correct_stories / total_stories if total_stories > 0 else 0
        action_accuracy = correct_actions / total_actions if total_actions > 0 else 0
        
        metrics = {
            'total_stories': total_stories,
            'correct_stories': correct_stories,
            'story_accuracy': story_accuracy,
            'total_actions': total_actions,
            'correct_actions': correct_actions,
            'action_accuracy': action_accuracy
        }
        
        return metrics
    
    def generate_dialogue_report(self, save_path="evaluation/reports/6_dialogue_accuracy.png"):
        data = self.load_story_results()
        
        if not data:
            self.generate_placeholder_dialogue(save_path)
            return save_path
            
        metrics = self.analyze_dialogue_metrics(data)
        
        fig = plt.figure(figsize=(16, 10))
        gs = fig.add_gridspec(2, 2, hspace=0.3, wspace=0.3)
        
        ax1 = fig.add_subplot(gs[0, 0])
        ax2 = fig.add_subplot(gs[0, 1])
        ax3 = fig.add_subplot(gs[1, :])
        
        fig.suptitle('End-to-End Dialogue Accuracy - Rasa Core', fontsize=16, fontweight='bold')
        
        categories = ['Stories', 'Actions']
        correct = [metrics['correct_stories'], metrics['correct_actions']]
        total = [metrics['total_stories'], metrics['total_actions']]
        incorrect = [total[i] - correct[i] for i in range(len(total))]
        
        x = np.arange(len(categories))
        width = 0.35
        
        bars1 = ax1.bar(x, correct, width, label='Correct', color='#70AD47')
        bars2 = ax1.bar(x, incorrect, width, bottom=correct, label='Incorrect', color='#C55A11')
        
        ax1.set_ylabel('Count', fontweight='bold', fontsize=11)
        ax1.set_title('Dialogue Components: Correct vs Incorrect', fontsize=12, fontweight='bold')
        ax1.set_xticks(x)
        ax1.set_xticklabels(categories)
        ax1.legend()
        ax1.grid(axis='y', alpha=0.3, linestyle='--')
        
        for i, (bar1, bar2, tot) in enumerate(zip(bars1, bars2, total)):
            height1 = bar1.get_height()
            height2 = bar2.get_height()
            
            ax1.text(bar1.get_x() + bar1.get_width()/2., height1/2,
                    f'{int(correct[i])}', ha='center', va='center', 
                    fontsize=11, fontweight='bold', color='white')
            
            if height2 > 0:
                ax1.text(bar2.get_x() + bar2.get_width()/2., height1 + height2/2,
                        f'{int(incorrect[i])}', ha='center', va='center', 
                        fontsize=11, fontweight='bold', color='white')
            
            ax1.text(bar1.get_x() + bar1.get_width()/2., tot + 5,
                    f'{tot}', ha='center', va='bottom', fontsize=10, fontweight='bold')
        
        accuracies = [metrics['story_accuracy'] * 100, metrics['action_accuracy'] * 100]
        colors_pie = ['#4472C4', '#70AD47']
        
        wedges, texts, autotexts = ax2.pie(accuracies, labels=categories, autopct='%1.1f%%',
                                           colors=colors_pie, startangle=90,
                                           textprops={'fontsize': 11, 'weight': 'bold'})
        
        for autotext in autotexts:
            autotext.set_color('white')
            autotext.set_fontsize(12)
            autotext.set_weight('bold')
        
        ax2.set_title('Accuracy by Component', fontsize=12, fontweight='bold')
        
        table_data = [
            ['Total Stories Tested', f"{metrics['total_stories']}"],
            ['Correct Story Flows', f"{metrics['correct_stories']}"],
            ['Story Accuracy', f"{metrics['story_accuracy']*100:.2f}%"],
            ['', ''],
            ['Total Actions Predicted', f"{metrics['total_actions']}"],
            ['Correct Actions', f"{metrics['correct_actions']}"],
            ['Action Accuracy', f"{metrics['action_accuracy']*100:.2f}%"],
            ['', ''],
            ['Overall E2E Performance', f"{(metrics['story_accuracy']*0.5 + metrics['action_accuracy']*0.5)*100:.2f}%"],
        ]
        
        ax3.axis('tight')
        ax3.axis('off')
        
        table = ax3.table(cellText=table_data,
                         colLabels=['Metric', 'Value'],
                         cellLoc='left',
                         loc='upper center',
                         colWidths=[0.4, 0.2])
        table.auto_set_font_size(False)
        table.set_fontsize(11)
        table.scale(1.5, 2.5)
        
        for i in range(len(table_data) + 1):
            if i == 0:
                table[(i, 0)].set_facecolor('#4472C4')
                table[(i, 1)].set_facecolor('#4472C4')
                table[(i, 0)].set_text_props(weight='bold', color='white')
                table[(i, 1)].set_text_props(weight='bold', color='white')
            elif i in [4, 8]:
                table[(i, 0)].set_facecolor('white')
                table[(i, 1)].set_facecolor('white')
            elif i == 9:
                table[(i, 0)].set_facecolor('#70AD47')
                table[(i, 1)].set_facecolor('#70AD47')
                table[(i, 0)].set_text_props(weight='bold', color='white')
                table[(i, 1)].set_text_props(weight='bold', color='white')
            else:
                table[(i, 0)].set_facecolor('#E7E6E6' if i % 2 == 0 else 'white')
                table[(i, 1)].set_facecolor('#E7E6E6' if i % 2 == 0 else 'white')
        
        insights_text = f"""
📊 Kết quả End-to-End Dialogue Testing:

✅ Story Accuracy: {metrics['story_accuracy']*100:.1f}% 
   → {metrics['correct_stories']}/{metrics['total_stories']} conversation flows đi đúng hướng

✅ Action Accuracy: {metrics['action_accuracy']*100:.1f}%
   → {metrics['correct_actions']}/{metrics['total_actions']} actions được predict đúng

💡 Overall E2E Performance: {(metrics['story_accuracy']*0.5 + metrics['action_accuracy']*0.5)*100:.1f}%
   → Chatbot có khả năng xử lý conversation đúng ngữ cảnh
        """
        
        ax3.text(0.05, 0.3, insights_text, fontsize=11, transform=ax3.transAxes,
                verticalalignment='top', family='monospace',
                bbox=dict(boxstyle='round,pad=1', facecolor='#E7E6E6', edgecolor='#4472C4', linewidth=2))
        
        ax3.set_title('Detailed Metrics & Insights', fontsize=12, fontweight='bold', 
                     pad=10, loc='left')
        
        Path(save_path).parent.mkdir(parents=True, exist_ok=True)
        plt.savefig(save_path, dpi=300, bbox_inches='tight')
        plt.close()
        
        print(f"✅ Dialogue accuracy saved to: {save_path}")
        return save_path
    
    def generate_placeholder_dialogue(self, save_path):
        fig = plt.figure(figsize=(14, 10))
        gs = fig.add_gridspec(2, 1, hspace=0.3)
        
        ax1 = fig.add_subplot(gs[0, 0])
        ax2 = fig.add_subplot(gs[1, 0])
        
        fig.suptitle('End-to-End Dialogue Accuracy\n⚠️ PLACEHOLDER - Chạy: rasa test core', 
                    fontsize=14, fontweight='bold', color='red')
        
        categories = ['Stories', 'Actions']
        correct = [85, 320]
        total = [100, 350]
        incorrect = [total[i] - correct[i] for i in range(len(total))]
        
        x = np.arange(len(categories))
        width = 0.35
        
        bars1 = ax1.bar(x, correct, width, label='Correct (Sample)', color='#70AD47')
        bars2 = ax1.bar(x, incorrect, width, bottom=correct, label='Incorrect (Sample)', color='#C55A11')
        
        ax1.set_ylabel('Count', fontweight='bold')
        ax1.set_title('Sample: Correct vs Incorrect', fontsize=12, fontweight='bold')
        ax1.set_xticks(x)
        ax1.set_xticklabels(categories)
        ax1.legend()
        ax1.grid(axis='y', alpha=0.3, linestyle='--')
        
        table_data = [
            ['Total Stories', '100'],
            ['Correct Stories', '85'],
            ['Story Accuracy', '85.0%'],
            ['', ''],
            ['Total Actions', '350'],
            ['Correct Actions', '320'],
            ['Action Accuracy', '91.4%'],
        ]
        
        ax2.axis('tight')
        ax2.axis('off')
        
        table = ax2.table(cellText=table_data,
                         colLabels=['Metric', 'Value'],
                         cellLoc='center',
                         loc='center')
        table.auto_set_font_size(False)
        table.set_fontsize(11)
        table.scale(1, 2.5)
        
        Path(save_path).parent.mkdir(parents=True, exist_ok=True)
        plt.savefig(save_path, dpi=300, bbox_inches='tight')
        plt.close()
        
        print(f"⚠️ Placeholder dialogue accuracy saved to: {save_path}")

if __name__ == "__main__":
    da = DialogueAccuracy()
    da.generate_dialogue_report()
