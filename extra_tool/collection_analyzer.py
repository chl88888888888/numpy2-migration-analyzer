import json
import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
import seaborn as sns
import warnings
import ijson
import os
warnings.filterwarnings('ignore')
plt.rcParams['font.sans-serif'] = ['SimHei']
plt.rcParams['axes.unicode_minus'] = False

plt.style.use('seaborn-v0_8-darkgrid')
sns.set_palette("husl")

def load_data(commits_file='./extra_tool/numpy_commits.json', issues_file='./extra_tool/numpy_issues.json'):
    """获取json文件中爬取的数据"""
    commits_data = []
    with open(commits_file, 'r', encoding='utf-8') as f:
        parser = ijson.items(f, 'item')
        for item in parser:
            commits_data.append(item)
    
    issues_data = []
    with open(issues_file, 'r', encoding='utf-8') as f:
        parser = ijson.items(f, 'item')
        for item in parser:
            issues_data.append(item)
    
    commits_df = pd.DataFrame(commits_data)
    issues_df = pd.DataFrame(issues_data)
    
    return commits_df, issues_df

def preprocess_data(commits_df, issues_df):
    """数据预处理并提取标签"""
    commits_df['date'] = pd.to_datetime(commits_df['date'])
    commits_df['year'] = commits_df['date'].dt.year
    commits_df['month'] = commits_df['date'].dt.month
    commits_df['year_month'] = commits_df['date'].dt.to_period('M')
    commits_df['weekday'] = commits_df['date'].dt.day_name()
    commits_df['hour'] = commits_df['date'].dt.hour
    commits_df['time_of_day'] = pd.cut(commits_df['hour'], 
                                       bins=[0, 6, 12, 18, 24],
                                       labels=['Night', 'Morning', 'Afternoon', 'Evening'],
                                       include_lowest=True)
    
    commits_df['message_length'] = commits_df['message'].str.len()
    commits_df['is_bug_fix'] = commits_df['message'].str.contains(
        r'(BUG|FIX|bug|fix|Bug|Fix)', case=False, regex=True
    )
    commits_df['is_feature'] = commits_df['message'].str.contains(
        r'(FEAT|feature|Feature)', case=False, regex=True
    )
    
    issues_df['created_at'] = pd.to_datetime(issues_df['created_at'])
    issues_df['closed_at'] = pd.to_datetime(issues_df['closed_at'])
    issues_df['resolution_time'] = (issues_df['closed_at'] - issues_df['created_at']).dt.total_seconds() / 3600
    issues_df['is_closed'] = issues_df['state'] == 'closed'
    issues_df['resolution_time'].fillna(0, inplace=True)
    issues_df['year'] = issues_df['created_at'].dt.year
    issues_df['month'] = issues_df['created_at'].dt.month
    issues_df['created_weekday'] = issues_df['created_at'].dt.day_name()
    issues_df['type'] = issues_df['is_pr'].apply(lambda x: 'PR' if x else 'Issue')
    
    return commits_df, issues_df

def analyze_contributors(commits_df):
    """分析发展"""
    author_stats = commits_df.groupby('author').agg({
        'sha': 'count',
        'date': ['min', 'max']
    }).round(2)
    
    author_stats.columns = ['commit_count', 'first_commit', 'last_commit']
    author_stats = author_stats.sort_values('commit_count', ascending=False)
    author_stats['active_days'] = (author_stats['last_commit'] - author_stats['first_commit']).dt.days
    
    return author_stats

def create_visualizations(commits_df, issues_df, author_stats):
    """可视化"""
    output_dir = './extra_tool/'
    os.makedirs(output_dir, exist_ok=True)
    
    fig = plt.figure(figsize=(20, 16))
    gs = fig.add_gridspec(4, 3, hspace=0.3, wspace=0.3)
    
    ax1 = fig.add_subplot(gs[0, :])
    commits_by_month = commits_df.groupby('year_month').size()
    commits_by_month.plot(kind='line', ax=ax1, marker='o', linewidth=2, markersize=4)
    ax1.set_title('NumPy Commit Activity Over Time', fontsize=14, fontweight='bold')
    ax1.set_xlabel('Year-Month')
    ax1.set_ylabel('Number of Commits')
    ax1.grid(True, alpha=0.3)
    ax1.xaxis.set_major_locator(plt.MaxNLocator(10))
    
    fig1, ax1_single = plt.subplots(figsize=(12, 6))
    commits_by_month.plot(kind='line', ax=ax1_single, marker='o', linewidth=2, markersize=4)
    ax1_single.set_title('NumPy Commit Activity Over Time', fontsize=14, fontweight='bold')
    ax1_single.set_xlabel('Year-Month')
    ax1_single.set_ylabel('Number of Commits')
    ax1_single.grid(True, alpha=0.3)
    ax1_single.xaxis.set_major_locator(plt.MaxNLocator(10))
    plt.tight_layout()
    plt.savefig(f'{output_dir}1_commit_activity_over_time.png', dpi=300, bbox_inches='tight')
    plt.close(fig1)
    
    ax2 = fig.add_subplot(gs[1, 0])
    issues_by_year = issues_df.groupby(['year', 'type']).size().unstack()
    issues_by_year.plot(kind='bar', ax=ax2, stacked=True)
    ax2.set_title('Issues and PRs Over Years', fontsize=12)
    ax2.set_xlabel('Year')
    ax2.set_ylabel('Count')
    ax2.legend(title='Type')
    ax2.tick_params(axis='x', rotation=45)
    
    fig2, ax2_single = plt.subplots(figsize=(10, 6))
    issues_by_year.plot(kind='bar', ax=ax2_single, stacked=True)
    ax2_single.set_title('Issues and PRs Over Years', fontsize=12)
    ax2_single.set_xlabel('Year')
    ax2_single.set_ylabel('Count')
    ax2_single.legend(title='Type')
    ax2_single.tick_params(axis='x', rotation=45)
    plt.tight_layout()
    plt.savefig(f'{output_dir}2_issues_and_prs_over_years.png', dpi=300, bbox_inches='tight')
    plt.close(fig2)
    
    ax3 = fig.add_subplot(gs[1, 1])
    top_authors = author_stats.head(15)
    ax3.barh(range(len(top_authors)), top_authors['commit_count'].values)
    ax3.set_yticks(range(len(top_authors)))
    ax3.set_yticklabels(top_authors.index)
    ax3.set_title('Top 15 Contributors by Commits', fontsize=12)
    ax3.set_xlabel('Number of Commits')
    ax3.invert_yaxis()
    
    fig3, ax3_single = plt.subplots(figsize=(10, 8))
    ax3_single.barh(range(len(top_authors)), top_authors['commit_count'].values)
    ax3_single.set_yticks(range(len(top_authors)))
    ax3_single.set_yticklabels(top_authors.index)
    ax3_single.set_title('Top 15 Contributors by Commits', fontsize=12)
    ax3_single.set_xlabel('Number of Commits')
    ax3_single.invert_yaxis()
    plt.tight_layout()
    plt.savefig(f'{output_dir}3_top_contributors_by_commits.png', dpi=300, bbox_inches='tight')
    plt.close(fig3)
    
    ax4 = fig.add_subplot(gs[1, 2])
    time_dist = commits_df['time_of_day'].value_counts()
    colors = ['#FF6B6B', '#4ECDC4', '#45B7D1', '#96CEB4']
    ax4.pie(time_dist.values, labels=time_dist.index, autopct='%1.1f%%', 
            colors=colors, startangle=90)
    ax4.set_title('Commit Time Distribution', fontsize=12)
    
    fig4, ax4_single = plt.subplots(figsize=(8, 8))
    ax4_single.pie(time_dist.values, labels=time_dist.index, autopct='%1.1f%%', 
                   colors=colors, startangle=90)
    ax4_single.set_title('Commit Time Distribution', fontsize=12)
    plt.tight_layout()
    plt.savefig(f'{output_dir}4_commit_time_distribution.png', dpi=300, bbox_inches='tight')
    plt.close(fig4)
    
    ax5 = fig.add_subplot(gs[2, 0])
    weekday_hour = pd.crosstab(commits_df['weekday'], commits_df['hour'])
    weekday_order = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday']
    weekday_hour = weekday_hour.reindex(weekday_order)
    im = ax5.imshow(weekday_hour.values, cmap='YlOrRd', aspect='auto')
    ax5.set_xticks(range(0, 24, 3))
    ax5.set_xticklabels(range(0, 24, 3))
    ax5.set_yticks(range(len(weekday_order)))
    ax5.set_yticklabels(weekday_order)
    ax5.set_title('Commits by Weekday and Hour', fontsize=12)
    ax5.set_xlabel('Hour of Day')
    plt.colorbar(im, ax=ax5)
    
    fig5, ax5_single = plt.subplots(figsize=(10, 6))
    im_single = ax5_single.imshow(weekday_hour.values, cmap='YlOrRd', aspect='auto')
    ax5_single.set_xticks(range(0, 24, 3))
    ax5_single.set_xticklabels(range(0, 24, 3))
    ax5_single.set_yticks(range(len(weekday_order)))
    ax5_single.set_yticklabels(weekday_order)
    ax5_single.set_title('Commits by Weekday and Hour', fontsize=12)
    ax5_single.set_xlabel('Hour of Day')
    plt.colorbar(im_single, ax=ax5_single)
    plt.tight_layout()
    plt.savefig(f'{output_dir}5_commits_by_weekday_and_hour.png', dpi=300, bbox_inches='tight')
    plt.close(fig5)
    
    ax6 = fig.add_subplot(gs[2, 1])
    closed_issues = issues_df[issues_df['is_closed'] & (issues_df['resolution_time'] > 0)]
    resolution_days = closed_issues['resolution_time'] / 24
    resolution_days_clean = resolution_days[resolution_days <= resolution_days.quantile(0.95)]
    ax6.hist(resolution_days_clean, bins=50, alpha=0.7, color='#45B7D1', edgecolor='black')
    ax6.set_title('Issue Resolution Time Distribution', fontsize=12)
    ax6.set_xlabel('Resolution Time (Days)')
    ax6.set_ylabel('Frequency')
    ax6.grid(True, alpha=0.3)
    
    fig6, ax6_single = plt.subplots(figsize=(10, 6))
    ax6_single.hist(resolution_days_clean, bins=50, alpha=0.7, color='#45B7D1', edgecolor='black')
    ax6_single.set_title('Issue Resolution Time Distribution', fontsize=12)
    ax6_single.set_xlabel('Resolution Time (Days)')
    ax6_single.set_ylabel('Frequency')
    ax6_single.grid(True, alpha=0.3)
    plt.tight_layout()
    plt.savefig(f'{output_dir}6_issue_resolution_time_distribution.png', dpi=300, bbox_inches='tight')
    plt.close(fig6)
    
    ax7 = fig.add_subplot(gs[2, 2])
    commit_types = {
        'Bug Fixes': commits_df['is_bug_fix'].sum(),
        'Features': commits_df['is_feature'].sum(),
        'Other': len(commits_df) - (commits_df['is_bug_fix'].sum() + commits_df['is_feature'].sum())
    }
    colors = ['#FF6B6B', '#4ECDC4', '#FECA57']
    ax7.bar(commit_types.keys(), commit_types.values(), color=colors, edgecolor='black')
    ax7.set_title('Commit Types Distribution', fontsize=12)
    ax7.set_ylabel('Count')
    ax7.tick_params(axis='x', rotation=45)
    
    fig7, ax7_single = plt.subplots(figsize=(8, 6))
    ax7_single.bar(commit_types.keys(), commit_types.values(), color=colors, edgecolor='black')
    ax7_single.set_title('Commit Types Distribution', fontsize=12)
    ax7_single.set_ylabel('Count')
    ax7_single.tick_params(axis='x', rotation=45)
    plt.tight_layout()
    plt.savefig(f'{output_dir}7_commit_types_distribution.png', dpi=300, bbox_inches='tight')
    plt.close(fig7)
    
    ax8 = fig.add_subplot(gs[3, 0])
    commits_by_month = commits_df.set_index('date').resample('ME').size()
    issues_by_month = issues_df.set_index('created_at').resample('ME').size()
    ax8.plot(commits_by_month.index, commits_by_month.values, label='Commits', linewidth=2)
    ax8.plot(issues_by_month.index, issues_by_month.values, label='Issues/PRs', linewidth=2, alpha=0.7)
    ax8.set_title('Monthly Activity Comparison', fontsize=12)
    ax8.set_xlabel('Date')
    ax8.set_ylabel('Count')
    ax8.legend()
    ax8.grid(True, alpha=0.3)
    ax8.xaxis.set_major_locator(mdates.YearLocator())
    ax8.xaxis.set_major_formatter(mdates.DateFormatter('%Y'))
    
    fig8, ax8_single = plt.subplots(figsize=(10, 6))
    ax8_single.plot(commits_by_month.index, commits_by_month.values, label='Commits', linewidth=2)
    ax8_single.plot(issues_by_month.index, issues_by_month.values, label='Issues/PRs', linewidth=2, alpha=0.7)
    ax8_single.set_title('Monthly Activity Comparison', fontsize=12)
    ax8_single.set_xlabel('Date')
    ax8_single.set_ylabel('Count')
    ax8_single.legend()
    ax8_single.grid(True, alpha=0.3)
    ax8_single.xaxis.set_major_locator(mdates.YearLocator())
    ax8_single.xaxis.set_major_formatter(mdates.DateFormatter('%Y'))
    plt.tight_layout()
    plt.savefig(f'{output_dir}8_monthly_activity_comparison.png', dpi=300, bbox_inches='tight')
    plt.close(fig8)
    
    ax9 = fig.add_subplot(gs[3, 1])
    author_stats['active_years'] = author_stats['active_days'] / 365.25
    ax9.scatter(author_stats['active_years'], author_stats['commit_count'], 
                alpha=0.6, s=50, c='#6C5CE7', edgecolors='black')
    ax9.set_xscale('log')
    ax9.set_yscale('log')
    ax9.set_title('Developer Activity: Duration vs Contributions', fontsize=12)
    ax9.set_xlabel('Active Years (log scale)')
    ax9.set_ylabel('Number of Commits (log scale)')
    ax9.grid(True, alpha=0.3)
    
    fig9, ax9_single = plt.subplots(figsize=(10, 6))
    ax9_single.scatter(author_stats['active_years'], author_stats['commit_count'], 
                      alpha=0.6, s=50, c='#6C5CE7', edgecolors='black')
    ax9_single.set_xscale('log')
    ax9_single.set_yscale('log')
    ax9_single.set_title('Developer Activity: Duration vs Contributions', fontsize=12)
    ax9_single.set_xlabel('Active Years (log scale)')
    ax9_single.set_ylabel('Number of Commits (log scale)')
    ax9_single.grid(True, alpha=0.3)
    plt.tight_layout()
    plt.savefig(f'{output_dir}9_developer_activity_duration_vs_contributions.png', dpi=300, bbox_inches='tight')
    plt.close(fig9)
    
    ax10 = fig.add_subplot(gs[3, 2])
    issue_state = issues_df['state'].value_counts()
    colors = ['#1DD1A1', '#FF6B6B', '#FECA57']
    ax10.pie(issue_state.values, labels=issue_state.index, 
             autopct='%1.1f%%', colors=colors, startangle=90)
    ax10.set_title('Issue Status Distribution', fontsize=12)
    
    fig10, ax10_single = plt.subplots(figsize=(8, 8))
    ax10_single.pie(issue_state.values, labels=issue_state.index, 
                   autopct='%1.1f%%', colors=colors, startangle=90)
    ax10_single.set_title('Issue Status Distribution', fontsize=12)
    plt.tight_layout()
    plt.savefig(f'{output_dir}10_issue_status_distribution.png', dpi=300, bbox_inches='tight')
    plt.close(fig10)
    
    plt.suptitle('NumPy Development Activity Analysis', fontsize=16, fontweight='bold', y=0.98)
    plt.tight_layout()
    
    return fig

def create_summary_statistics(commits_df, issues_df, author_stats):
    """图像子图分组"""
    summary = {
        'Total Commits': len(commits_df),
        'Total Issues/PRs': len(issues_df),
        'Total Contributors': len(author_stats),
        'Time Span': f"{commits_df['date'].min().date()} to {commits_df['date'].max().date()}",
        'Average Commits per Day': round(len(commits_df) / (commits_df['date'].max() - commits_df['date'].min()).days, 2),
        'Average Issues per Day': round(len(issues_df) / (issues_df['created_at'].max() - issues_df['created_at'].min()).days, 2),
        'Bug Fix Commits': int(commits_df['is_bug_fix'].sum()),
        'Feature Commits': int(commits_df['is_feature'].sum()),
        'Closed Issues': int(issues_df['is_closed'].sum()),
        'Average Resolution Time (days)': round(issues_df[issues_df['is_closed']]['resolution_time'].mean() / 24, 2)
    }
    
    return summary

def main():
    """分析数据并保存"""
    os.makedirs('./extra_tool/', exist_ok=True)
    
    commits_df, issues_df = load_data('./extra_tool/numpy_commits.json', './extra_tool/numpy_issues.json')
    print(f"Loaded {len(commits_df)} commits and {len(issues_df)} issues/PRs")
    
    commits_df, issues_df = preprocess_data(commits_df, issues_df)
    author_stats = analyze_contributors(commits_df)
    summary = create_summary_statistics(commits_df, issues_df, author_stats)
    
    print("\nSUMMARY STATISTICS")
    for key, value in summary.items():
        print(f"{key:<30}: {value}")
    
    print("\nTOP 10 CONTRIBUTORS")
    print(author_stats.head(10)[['commit_count', 'active_days']].to_string())
    
    fig = create_visualizations(commits_df, issues_df, author_stats)
    
    output_path = './extra_tool/numpy_development_analysis.png'
    plt.savefig(output_path, dpi=300, bbox_inches='tight')
    print(f"\nComprehensive visualization saved as '{output_path}'")
    
    commits_df.to_csv('./extra_tool/processed_commits.csv', index=False)
    issues_df.to_csv('./extra_tool/processed_issues.csv', index=False)
    author_stats.to_csv('./extra_tool/contributor_stats.csv')
    
    return commits_df, issues_df, author_stats, fig

def additional_analyses(commits_df, issues_df):
    """分析年度数据"""
    yearly_commits = commits_df.groupby('year').agg({
        'sha': 'count',
        'author': lambda x: x.nunique(),
        'is_bug_fix': 'sum',
        'is_feature': 'sum'
    }).rename(columns={'sha': 'total_commits', 'author': 'unique_authors'})
    
    yearly_issues = issues_df.groupby('year').agg({
        'number': 'count',
        'type': lambda x: (x == 'PR').sum(),
        'is_closed': 'sum'
    }).rename(columns={'number': 'total_issues', 'type': 'pr_count'})
    
    yearly_summary = pd.concat([yearly_commits, yearly_issues], axis=1)
    author_engagement = commits_df.groupby(['author', 'year']).size().unstack(fill_value=0)
    
    return yearly_summary, author_engagement

if __name__ == "__main__":
    commits_df, issues_df, author_stats, fig = main()
    
    yearly_summary, author_engagement = additional_analyses(commits_df, issues_df)
    yearly_summary.to_csv('./extra_tool/yearly_summary.csv')
    
    try:
        import plotly.express as px
        import plotly.graph_objects as go
        from plotly.subplots import make_subplots
        
        fig_interactive = make_subplots(
            rows=2, cols=2,
            subplot_titles=('Commit Activity Over Time', 'Issue Resolution Time',
                           'Top Contributors', 'Weekly Activity Pattern'),
            specs=[[{'type': 'scatter'}, {'type': 'histogram'}],
                   [{'type': 'bar'}, {'type': 'heatmap'}]]
        )
        
        monthly_commits = commits_df.groupby(pd.Grouper(key='date', freq='ME')).size().reset_index()
        fig_interactive.add_trace(
            go.Scatter(x=monthly_commits['date'], y=monthly_commits[0], 
                      mode='lines+markers', name='Commits'),
            row=1, col=1
        )
        
        closed_issues = issues_df[issues_df['is_closed']]
        fig_interactive.add_trace(
            go.Histogram(x=closed_issues['resolution_time']/24, nbinsx=50,
                        name='Resolution Time'),
            row=1, col=2
        )
        
        top_20 = author_stats.head(20)
        fig_interactive.add_trace(
            go.Bar(x=top_20['commit_count'], y=top_20.index, 
                  orientation='h', name='Commits'),
            row=2, col=1
        )
        
        commits_df['weekday_num'] = commits_df['date'].dt.weekday
        heatmap_data = commits_df.groupby(['weekday_num', 'hour']).size().unstack(fill_value=0)
        
        fig_interactive.add_trace(
            go.Heatmap(z=heatmap_data.values,
                      x=heatmap_data.columns,
                      y=['Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat', 'Sun'],
                      colorscale='YlOrRd'),
            row=2, col=2
        )
        
        fig_interactive.update_layout(height=800, title_text="Interactive NumPy Development Dashboard")
        fig_interactive.write_html("./extra_tool/numpy_interactive_dashboard.html")
        
    except ImportError:
        pass