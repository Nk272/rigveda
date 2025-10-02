import sqlite3
import matplotlib.pyplot as plt
import numpy as np
from pathlib import Path
from collections import Counter

DB_PATH = Path(__file__).parent.parent / "hymn_vectors.db"

def GetHymnScores():
    """Retrieve all hymn scores from database"""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    cursor.execute('SELECT hymn_score FROM hymn_vectors ORDER BY hymn_score')
    scores = [row[0] for row in cursor.fetchall()]
    
    conn.close()
    return scores

def PlotScoreDistribution():
    """Plot histogram of hymn scores"""
    scores = GetHymnScores()
    
    score_counts = Counter(scores)
    unique_scores = sorted(score_counts.keys())
    counts = [score_counts[score] for score in unique_scores]
    
    plt.figure(figsize=(14, 6))
    plt.bar(unique_scores, counts, width=5, color='steelblue', edgecolor='navy', alpha=0.7)
    plt.xlabel('Hymn Score (Sum of Deity Frequencies)', fontsize=12)
    plt.ylabel('Number of Hymns', fontsize=12)
    plt.title('Distribution of Hymn Scores across Rigveda', fontsize=14, fontweight='bold')
    plt.grid(axis='y', alpha=0.3, linestyle='--')
    
    total_hymns = len(scores)
    avg_score = np.mean(scores)
    median_score = np.median(scores)
    
    plt.axvline(avg_score, color='red', linestyle='--', linewidth=2, label=f'Mean: {avg_score:.1f}')
    plt.axvline(median_score, color='green', linestyle='--', linewidth=2, label=f'Median: {median_score:.1f}')
    
    plt.legend(fontsize=10)
    
    textstr = f'Total Hymns: {total_hymns}\nMin Score: {min(scores):.0f}\nMax Score: {max(scores):.0f}'
    plt.text(0.98, 0.97, textstr, transform=plt.gca().transAxes, 
             fontsize=10, verticalalignment='top', horizontalalignment='right',
             bbox=dict(boxstyle='round', facecolor='wheat', alpha=0.5))
    
    plt.tight_layout()
    
    output_path = Path(__file__).parent.parent / "hymn_score_distribution.png"
    plt.savefig(output_path, dpi=300, bbox_inches='tight')
    print(f"✓ Plot saved to: {output_path}")
    
    plt.show()

def PlotScoreDistributionBinned(bin_size=50):
    """Plot binned histogram of hymn scores"""
    scores = GetHymnScores()
    
    max_score = max(scores)
    bins = np.arange(0, max_score + bin_size, bin_size)
    
    plt.figure(figsize=(14, 6))
    n, bins, patches = plt.hist(scores, bins=bins, color='steelblue', 
                                  edgecolor='navy', alpha=0.7)
    
    plt.xlabel('Hymn Score (Sum of Deity Frequencies)', fontsize=12)
    plt.ylabel('Number of Hymns', fontsize=12)
    plt.title(f'Distribution of Hymn Scores (Binned by {bin_size})', fontsize=14, fontweight='bold')
    plt.grid(axis='y', alpha=0.3, linestyle='--')
    
    avg_score = np.mean(scores)
    median_score = np.median(scores)
    
    plt.axvline(avg_score, color='red', linestyle='--', linewidth=2, label=f'Mean: {avg_score:.1f}')
    plt.axvline(median_score, color='green', linestyle='--', linewidth=2, label=f'Median: {median_score:.1f}')
    
    plt.legend(fontsize=10)
    
    total_hymns = len(scores)
    textstr = f'Total Hymns: {total_hymns}\nMin Score: {min(scores):.0f}\nMax Score: {max(scores):.0f}'
    plt.text(0.98, 0.97, textstr, transform=plt.gca().transAxes, 
             fontsize=10, verticalalignment='top', horizontalalignment='right',
             bbox=dict(boxstyle='round', facecolor='wheat', alpha=0.5))
    
    plt.tight_layout()
    
    output_path = Path(__file__).parent.parent / f"hymn_score_distribution_binned_{bin_size}.png"
    plt.savefig(output_path, dpi=300, bbox_inches='tight')
    print(f"✓ Plot saved to: {output_path}")
    
    plt.show()

def PlotDeityCountVsScore():
    """Plot relationship between deity count and hymn score"""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    cursor.execute('SELECT deity_count, hymn_score FROM hymn_vectors')
    data = cursor.fetchall()
    conn.close()
    
    deity_counts = [row[0] for row in data]
    scores = [row[1] for row in data]
    
    plt.figure(figsize=(12, 6))
    plt.scatter(deity_counts, scores, alpha=0.5, s=30, color='steelblue', edgecolor='navy')
    plt.xlabel('Number of Deities in Hymn', fontsize=12)
    plt.ylabel('Hymn Score', fontsize=12)
    plt.title('Hymn Score vs Number of Deities', fontsize=14, fontweight='bold')
    plt.grid(alpha=0.3, linestyle='--')
    
    z = np.polyfit(deity_counts, scores, 1)
    p = np.poly1d(z)
    plt.plot(sorted(set(deity_counts)), p(sorted(set(deity_counts))), 
             "r--", alpha=0.8, linewidth=2, label=f'Trend: y={z[0]:.1f}x+{z[1]:.1f}')
    
    plt.legend(fontsize=10)
    plt.tight_layout()
    
    output_path = Path(__file__).parent.parent / "deity_count_vs_score.png"
    plt.savefig(output_path, dpi=300, bbox_inches='tight')
    print(f"✓ Plot saved to: {output_path}")
    
    plt.show()

def PrintScoreStatistics():
    """Print detailed statistics about hymn scores"""
    scores = GetHymnScores()
    
    print("\n" + "="*60)
    print("HYMN SCORE STATISTICS")
    print("="*60)
    
    print(f"\nTotal Hymns: {len(scores)}")
    print(f"Mean Score: {np.mean(scores):.2f}")
    print(f"Median Score: {np.median(scores):.2f}")
    print(f"Std Dev: {np.std(scores):.2f}")
    print(f"Min Score: {min(scores):.0f}")
    print(f"Max Score: {max(scores):.0f}")
    
    print(f"\nPercentiles:")
    for p in [25, 50, 75, 90, 95, 99]:
        print(f"  {p}th: {np.percentile(scores, p):.2f}")
    
    score_counts = Counter(scores)
    print(f"\nScore Distribution:")
    print(f"  Hymns with score 0: {score_counts[0]}")
    print(f"  Hymns with score < 100: {sum(1 for s in scores if s < 100)}")
    print(f"  Hymns with score 100-500: {sum(1 for s in scores if 100 <= s < 500)}")
    print(f"  Hymns with score 500-1000: {sum(1 for s in scores if 500 <= s < 1000)}")
    print(f"  Hymns with score >= 1000: {sum(1 for s in scores if s >= 1000)}")

def main():
    print("Rigveda Hymn Score Visualization")
    print("="*60)
    
    PrintScoreStatistics()
    
    print("\nGenerating visualizations...")
    PlotScoreDistribution()
    PlotScoreDistributionBinned(bin_size=50)
    PlotDeityCountVsScore()
    
    print("\n✓ All visualizations complete!")

if __name__ == "__main__":
    main()


