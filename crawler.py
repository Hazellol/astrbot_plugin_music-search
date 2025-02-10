import requests
import json
import sys
import os

# 获取从命令行参数传入的歌曲名称
if len(sys.argv) > 1:
    song_name = sys.argv[1]
else:
    print("请输入歌曲名称作为参数！")
    sys.exit(1)

# 请求的 URL（没准哪天就寄了）
url = "https://music.txqq.pro/"

# 请求头部
headers = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/132.0.0.0 Safari/537.36 Edg/132.0.0.0",
    "Accept": "application/json, text/javascript, */*; q=0.01",
    "X-Requested-With": "XMLHttpRequest",
}

# 请求的数据
data = {
    "input": song_name,  # 替换为你想查询的歌曲名称
    "filter": "name",   # 过滤条件，可以选择以下几种：
                        # - "name": 按歌曲名称搜索（默认）
                        # - "id": 按歌曲 ID 搜索
                        # - "url": 按音乐地址（URL）搜索
    "type": "qq",       # 音乐平台类型，可以选择以下几种：
                        # - "qq": QQ 音乐
                        # - "netease": 网易云音乐
                        # - "kugou": 酷狗音乐
                        # - "kuwo": 酷我音乐
                        # - "baidu": 百度音乐
                        # - "1ting": 一听音乐
                        # - "migu": 咪咕音乐
                        # - "lizhi": 荔枝FM
                        # - "qingting": 蜻蜓FM
                        # - "ximalaya": 喜马拉雅
                        # - "5singyc": 5sing原创
                        # - "5singfc": 5sing翻唱
                        # - "kg": 全民K歌
    "page": 1           # 查询结果的页码，通常从 1 开始。如果你要获取更多结果，可以更改页码
}

# 发送 POST 请求
response = requests.post(url, data=data, headers=headers)

# 打印响应内容
print("响应内容:")
print(response.text)  # 打印返回的原始内容

# 如果请求成功，解析返回的 JSON 数据
if response.status_code == 200:
    try:
        json_data = response.json()  # 解析JSON数据
        # 获取当前脚本所在目录
        current_dir = os.path.dirname(os.path.abspath(__file__))
        # 构造绝对路径
        file_path = os.path.join(current_dir, 'songs_data.json')
        # 将搜索结果保存到 JSON 文件
        with open(file_path, 'w', encoding='utf-8') as json_file:
            json.dump(json_data, json_file, ensure_ascii=False, indent=4)  # 保存为 JSON 文件

        print("数据已保存到 'songs_data.json' 文件")
        
        # 打印歌曲信息
        for song in json_data.get("data", []):
            print(f"歌曲名称: {song['title']}")
            print(f"作者: {song['author']}")
            print(f"歌曲链接: {song['link']}")
            print(f"歌词: {song['lrc']}")
            print(f"下载链接: {song['url']}")
            print(f"封面图: {song['pic']}")
            print("-" * 50)
    except ValueError:
        print("返回的内容不是有效的 JSON 格式")
else:
    print(f"请求失败，状态码: {response.status_code}")
