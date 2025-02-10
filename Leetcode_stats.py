import requests
import os

def get_leetcode_progress(username):
    """
    从 https://leetcode-stats-api.herokuapp.com/{username} 获取 LeetCode 统计信息。
    如果成功返回包含统计信息的字典，否则返回 None。
    """
    url = f"https://leetcode-stats-api.herokuapp.com/{username}"
    print(f"Fetching LeetCode data from: {url}")

    try:
        response = requests.get(url, timeout=10)
        response.raise_for_status()
        data = response.json()

        # 接口出错时，会返回 status = "error" 
        if data.get("status") == "error":
            print(f"[ERROR] LeetCode API: {data.get('message')}")
            return None
        
        return data
    except requests.exceptions.RequestException as e:
        print(f"[ERROR] Error fetching data from LeetCode API: {e}")
        return None

def generate_svg_progress_bar(solved, total, title, filename):
    """
    生成一个可视化进度条的 SVG 文件。
    """
    if not os.path.exists('images'):
        os.makedirs('images', exist_ok=True)

    percentage = 0
    if total and total != 0:
        percentage = solved / total * 100

    # 这里可以根据需要自定义渐变色或动画
    svg_content = f'''
<svg xmlns="http://www.w3.org/2000/svg" width="300" height="50">
    <defs>
        <linearGradient id="gradient" x1="0%" y1="0%" x2="100%" y2="0%">
            <stop offset="0%" stop-color="#80D0C7"/>
            <stop offset="100%" stop-color="#0093E9"/>
        </linearGradient>
        <style>
            .progress-bar {{
                fill: url(#gradient);
            }}
            text {{
                font-weight: bold;
                font-family: Verdana, Geneva, sans-serif;
            }}
        </style>
    </defs>
    <!-- Background Bar -->
    <rect x="0" y="15" width="300" height="20" rx="10" fill="#ccc"/>
    <!-- Progress Bar -->
    <rect x="0" y="15" width="{percentage*3:.2f}" height="20" rx="10" class="progress-bar"/>
    <!-- Text -->
    <text x="150" y="12" text-anchor="middle" font-size="12" fill="#333">{title}</text>
    <text x="150" y="32" text-anchor="middle" font-size="12" fill="#000">{solved}/{total} ({percentage:.2f}%)</text>
</svg>
    '''.strip()

    with open(filename, 'w', encoding='utf-8') as f:
        f.write(svg_content)

    print(f"[INFO] SVG file '{filename}' generated -> {solved}/{total} ({percentage:.2f}%) for {title}")

def update_readme(data):
    """
    使用占位符的方式更新 README.md，让 README 在指定位置动态替换。
    """
    # 首先生成并更新四个难度的 SVG 进度条
    generate_svg_progress_bar(data['totalSolved'], data['totalQuestions'], "Total Solved", "images/total_solved.svg")
    generate_svg_progress_bar(data['easySolved'], data['totalEasy'], "Easy", "images/easy_solved.svg")
    generate_svg_progress_bar(data['mediumSolved'], data['totalMedium'], "Medium", "images/medium_solved.svg")
    generate_svg_progress_bar(data['hardSolved'], data['totalHard'], "Hard", "images/hard_solved.svg")

    # 准备表格形式的数据
    table_content = f"""<table>
<tr>
  <th>Difficulty</th>
  <th>Solved</th>
  <th>Total</th>
  <th>Progress</th>
</tr>
<tr>
  <td>Easy</td>
  <td>{data['easySolved']}</td>
  <td>{data['totalEasy']}</td>
  <td><img src="./images/easy_solved.svg" width="200"/></td>
</tr>
<tr>
  <td>Medium</td>
  <td>{data['mediumSolved']}</td>
  <td>{data['totalMedium']}</td>
  <td><img src="./images/medium_solved.svg" width="200"/></td>
</tr>
<tr>
  <td>Hard</td>
  <td>{data['hardSolved']}</td>
  <td>{data['totalHard']}</td>
  <td><img src="./images/hard_solved.svg" width="200"/></td>
</tr>
<tr>
  <td><b>Total</b></td>
  <td><b>{data['totalSolved']}</b></td>
  <td><b>{data['totalQuestions']}</b></td>
  <td><img src="./images/total_solved.svg" width="200"/></td>
</tr>
</table>
"""

    readme_path = "README.md"
    if not os.path.isfile(readme_path):
        print(f"[WARN] {readme_path} not found, creating a new one...")
        with open(readme_path, "w") as f:
            f.write("# My LeetCode Journey\n\n")

    with open(readme_path, "r", encoding='utf-8') as f:
        readme_content = f.read()

    # 占位符替换： <!-- LEETCODE_STATS:START --> 与 <!-- LEETCODE_STATS:END -->之间的内容全部替换
    start_marker = "<!-- LEETCODE_STATS:START -->"
    end_marker = "<!-- LEETCODE_STATS:END -->"

    new_section = (
        f"{start_marker}\n"
        f"{table_content}\n"
        f"{end_marker}"
    )

    if start_marker in readme_content and end_marker in readme_content:
        # 替换 start_marker 和 end_marker 之间的内容
        before = readme_content.split(start_marker)[0]
        after = readme_content.split(end_marker)[-1]
        updated_content = before + new_section + after
    else:
        # 如果原本没有这两个占位符，直接追加
        updated_content = readme_content + "\n\n" + new_section

    with open(readme_path, "w", encoding='utf-8') as f:
        f.write(updated_content)

    print("[INFO] README.md updated successfully.")

if __name__ == "__main__":
    username = "GiveMeAJob9"  # 你的 LeetCode 用户名
    progress_data = get_leetcode_progress(username)

    if progress_data:
        update_readme(progress_data)
        print("[INFO] LeetCode data fetched and README updated.")
    else:
        print("[ERROR] Failed to fetch LeetCode data. README not updated.")
