import requests
import json
import time
from datetime import datetime

#GITHUB_TOKEN = '' 这里要添加github爬取使用的token
HEADERS = {'Authorization': f'token {GITHUB_TOKEN}'} # type: ignore
REPO_OWNER = 'numpy'
REPO_NAME = 'numpy'

BASE_URL = f'https://api.github.com/repos/{REPO_OWNER}/{REPO_NAME}'

def fetch_all_pages(url, params=None):
    """通过GitHub API获取数据,并限制每页数量逐次获取"""
    results = []
    page = 1
    per_page = 100
    while True:
        if params is None:
            params = {}
        params.update({'page': page, 'per_page': per_page})
        print(f"正在获取: {url}, 第 {page} 页")
        response = requests.get(url, headers=HEADERS, params=params, verify=False)
        if response.status_code != 200:
            print(f"请求失败: {response.status_code}, {response.text}")
            break
        data = response.json()
        if not data:
            break
        results.extend(data)
        if len(data) < per_page:
            break
        page += 1
        time.sleep(0.5)#避免限流
    return results

def crawl_commits():
    """爬取所有提交记录"""
    print("开始爬取提交记录...")
    commits_url = f'{BASE_URL}/commits'
    all_commits = fetch_all_pages(commits_url, {'since': '2005-01-01T00:00:00Z'})
    #保留关键信息
    simplified_commits = []
    for commit in all_commits:
        simplified_commits.append({
            'sha': commit['sha'][:7],
            'author': commit['commit']['author']['name'] if commit['author'] is None else commit['author'].get('login', 'Unknown'),
            'date': commit['commit']['author']['date'],
            'message': commit['commit']['message'].split('\n')[0][:150],  # 取提交信息首行
            'html_url': commit['html_url']
        })
    with open('numpy_commits.json', 'w', encoding='utf-8') as f:
        json.dump(simplified_commits, f, ensure_ascii=False, indent=2)
    print(f"提交记录爬取完成，共 {len(simplified_commits)} 条，已保存至 numpy_commits.json")

def crawl_issues():
    """爬取Issues"""
    print("爬取Issues记录")
    issues_url = f'{BASE_URL}/issues'
    all_issues = fetch_all_pages(issues_url, {'state': 'all', 'since': '2005-01-01T00:00:00Z'})
    simplified_issues = []
    for issue in all_issues:
        simplified_issues.append({
            'number': issue['number'],
            'title': issue['title'],
            'state': issue['state'],
            'user': issue['user']['login'],
            'created_at': issue['created_at'],
            'closed_at': issue.get('closed_at'),
            'labels': [label['name'] for label in issue['labels']],
            'html_url': issue['html_url'],
            'is_pr': 'pull_request' in issue  # 标记是否为PR
        })
    with open('numpy_issues.json', 'w', encoding='utf-8') as f:
        json.dump(simplified_issues, f, ensure_ascii=False, indent=2)
    print(f"Issues爬取完成，共 {len(simplified_issues)} 条")

if __name__ == '__main__':
    crawl_commits()
    crawl_issues()