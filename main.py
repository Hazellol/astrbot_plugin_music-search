from typing import Dict
from astrbot.api.all import *
import asyncio
import time
import subprocess
import os
import json
import requests
from jinja2 import Template

# 用于跟踪每个用户的状态，记录用户请求的时间和当前状态
USER_STATES: Dict[int, Dict[str, float]] = {}

@register("astrbot_plugin_music-search", "Hazellol", "一个交互式音乐搜索插件", "1.0.2")
class MusicSearchPlugin(Star):
    def __init__(self, context: Context, config: AstrBotConfig):
        super().__init__(context)
        self.config = config
        # 获取配置中的等待时长，如果没有配置则使用默认值
        self.song_name_wait_time = self.config.get("song_name_wait_time", 30)
        self.song_number_wait_time = self.config.get("song_number_wait_time", 10)

    # 处理"找歌"命令
    @command("找歌")
    async def find_song(self, event: AstrMessageEvent):
        '''这是一个交互式音乐搜索指令，只需要发送/找歌 随后发送歌曲名称和序号即可！'''
        user_id = event.get_sender_id()

        if user_id in USER_STATES:
            # 用户已经处于等待状态
            yield event.plain_result("唔...！你明明知道我已经在等待你发送歌名了！哼！")
            # 重置等待时间
            USER_STATES[user_id] = {
                "state": "waiting_song_name",
                "start_time": time.time()
            }
            await asyncio.sleep(self.song_name_wait_time)  # 使用配置中的等待时长
            # 检查是否超时
            if user_id in USER_STATES and USER_STATES[user_id]["state"] == "waiting_song_name":
                del USER_STATES[user_id]
                yield event.plain_result("哼，不想找就不找了啦~ （等待已超时{}s）".format(self.song_name_wait_time))
        else:
            USER_STATES[user_id] = {
                "state": "waiting_song_name",
                "start_time": time.time()
            }
            yield event.plain_result("哼，才不想帮你找歌呢，不过你发歌名过来我也可以听听看~")
            await asyncio.sleep(self.song_name_wait_time)  # 使用配置中的等待时长
            # 检查是否超时
            if user_id in USER_STATES and USER_STATES[user_id]["state"] == "waiting_song_name":
                del USER_STATES[user_id]
                yield event.plain_result("哼，不想找就不找了啦~ （等待已超时{}s）".format(self.song_name_wait_time))

    # 处理所有消息类型的事件
    @event_message_type(EventMessageType.ALL)
    async def handle_message(self, event: AstrMessageEvent):
        user_id = event.get_sender_id()
        current_time = time.time()

        # 检查用户是否有待处理状态
        if user_id in USER_STATES:
            state = USER_STATES[user_id]
            if state["state"] == "waiting_song_name":
                # 用户输入歌名，处理并搜索
                del USER_STATES[user_id]
                async for item in self.process_song_search(event):
                    yield item
            elif state["state"] == "waiting_song_number":
                # 用户输入歌序号，处理并点歌
                message = event.message_str.strip()

                # 处理自然语言点歌
                if "我要听第" in message:
                    try:
                        song_number = int(message.split("第")[1].split("首")[0])
                        song_info = self.get_song_info(song_number)
                        if song_info:
                            yield event.plain_result(f"@{event.get_sender_name()} 大人点了第 {song_number} 首歌，都来听！")
                            async for message in self.download_song(song_info, event):
                                yield message
                    except:
                        yield event.plain_result("请输入正确的歌曲序号")
                elif message.isdigit():
                    song_number = int(message)
                    song_info = self.get_song_info(song_number)
                    if song_info:
                        yield event.plain_result(f"@{event.get_sender_name()} 大人点了第 {song_number} 首歌，都来听！")
                        async for message in self.download_song(song_info, event):
                            yield message

                # 删除用户状态
                if user_id in USER_STATES and USER_STATES[user_id]["state"] == "waiting_song_number":
                    del USER_STATES[user_id]
                return

    async def process_song_search(self, event: AstrMessageEvent):
        # 处理歌曲搜索逻辑
        song_name = event.message_str.strip()
        yield event.plain_result(f"好吧，我就帮你找找这首叫《{song_name}》的歌")

        # 获取当前文件所在目录
        current_dir = os.path.dirname(os.path.abspath(__file__))
        crawler_path = os.path.join(current_dir, "crawler.py")
        songs_data_path = os.path.join(current_dir, "songs_data.json")
        pics_dir = os.path.join(current_dir, "pics")

        # 检查 crawler.py 是否存在
        if not os.path.exists(crawler_path):
            yield event.plain_result("错误：crawler.py 文件不存在，请检查文件路径。")
            return

        # 运行 crawler.py 并传递歌名作为参数
        try:
            subprocess.run(["python", crawler_path, song_name], check=True)
        except subprocess.CalledProcessError as e:
            yield event.plain_result(f"运行 crawler.py 时发生错误: {e}")
            return

        # 检查 songs_data.json 是否存在
        if not os.path.exists(songs_data_path):
            yield event.plain_result("呃呃啊，解析不了返回的json......")
            return

        # 检查或创建 pics 文件夹
        if not os.path.exists(pics_dir):
            os.makedirs(pics_dir)  # 创建文件夹

        # 解析 songs_data.json
        try:
            with open(songs_data_path, 'r', encoding='utf-8') as json_file:
                json_data = json.load(json_file)
                data = json_data.get("data", [])
                if not data:
                    yield event.plain_result("嗯……没有找到符合要求的歌曲。")
                    return

                # 构建消息列表
                msg_list = [Plain("哈...帮你找歌真是废了我好大的劲呢💦💦......\n")]

                for idx, song in enumerate(data, 1):
                    title = song.get("title", "未知歌曲")
                    author = song.get("author", "未知歌手")
                    pic_url = song.get("pic", "无封面图")
                    platform = song.get("type", "未知平台")
                    songid = song.get("songid", "未知ID")
                    url = song.get("url", "无音频链接")

                    # 下载封面图片
                    if pic_url:
                        image_path = os.path.join(pics_dir, f"{songid}.jpg")
                        if not os.path.exists(image_path):  # 检查文件是否已存在
                            try:
                                response = requests.get(pic_url, stream=True)
                                if response.status_code == 200:
                                    with open(image_path, 'wb') as f:
                                        for chunk in response.iter_content(1024):
                                            f.write(chunk)
                            except Exception as e:
                                print(f"下载封面图片失败: {e}")

                    # 添加结果到消息列表
                    msg_list.append(Plain(f"\n✨️✨️✨️✨️✨️✨️✨️✨️✨️✨️✨️✨️✨️✨️✨️✨️✨️\n"))
                    msg_list.append(Plain(f"\n{idx}. 🎵歌曲名称：{title}\n"))
                    msg_list.append(Plain(f"    🧑‍🎤歌手：{author}\n"))
                    msg_list.append(Plain(f"    💽平台：{platform}音乐\n"))
                    if os.path.exists(image_path):
                        msg_list.append(Image.fromFileSystem(image_path))  # 从本地文件目录发送图片

                    # 如果是最后一首歌，添加提示
                    if idx == len(data):
                        msg_list.append(Plain("\n{}秒内发送对应歌曲的序号我就可以帮你点歌~！".format(self.song_number_wait_time)))

                # 发送最终的结果
                yield event.chain_result(msg_list)

                # 设置用户状态为等待序号输入
                USER_STATES[event.get_sender_id()] = {
                    "state": "waiting_song_number",
                    "start_time": time.time(),
                    "songs_data": data  # 保存歌曲数据
                }

                # 启动一个任务，等待指定时长后自动清除状态
                loop = asyncio.get_running_loop()
                loop.call_later(self.song_number_wait_time, self.cancel_song_number_input, event.get_sender_id())

        except Exception as e:
            yield event.plain_result("呃呃呃啊，解析不了返回的json......")
            print(f"Error processing song search: {e}")

    def cancel_song_number_input(self, user_id):
        if user_id in USER_STATES and USER_STATES[user_id]["state"] == "waiting_song_number":
            del USER_STATES[user_id]
            print("点歌操作等待超时")

    def get_song_info(self, song_number):
        # 获取用户点播的歌曲信息
        for user_id in USER_STATES:
            state = USER_STATES.get(user_id)
            if state and state["state"] == "waiting_song_number":
                songs_data = state.get("songs_data", [])
                if song_number <= len(songs_data):
                    return songs_data[song_number - 1]
        return None

    async def download_song(self, song_info, event: AstrMessageEvent):
        # 下载歌曲
        title = song_info.get("title", "未知歌曲")
        url = song_info.get("url", "")
        if url:
            current_dir = os.path.dirname(os.path.abspath(__file__))
            songs_dir = os.path.join(current_dir, "songs")
            if not os.path.exists(songs_dir):
                os.makedirs(songs_dir)
            # 构造文件名
            filename = f"{title}.mp3".replace("/", "-").replace("\\", "-").replace(":", "-")
            file_path = os.path.join(songs_dir, filename)
            # 下载歌曲
            try:
                response = requests.get(url, stream=True)
                if response.status_code == 200:
                    with open(file_path, 'wb') as f:
                        for chunk in response.iter_content(1024):
                            f.write(chunk)
                    print(f"歌曲 {title} 下载完成，保存到 {file_path}")
                    # 修改为 async for 迭代发送语音
                    async for message in self.send_voice_message(event, file_path):
                        yield message
                else:
                    yield event.plain_result("歌曲下载失败，请检查网络连接或歌曲链接")
            except Exception as e:
                yield event.plain_result(f"歌曲下载失败，错误信息：{e}")

    # 发送语音消息
    async def send_voice_message(self, event: AstrMessageEvent, voice_file_path: str):
        """发送语音文件"""
        # 检查文件是否存在
        if not os.path.exists(voice_file_path):
            yield event.plain_result("语音文件不存在，请检查文件路径。")
            return

        # 构建消息链
        chain = [
            Record.fromFileSystem(voice_file_path)
        ]

        # 发送消息链
        yield event.chain_result(chain)

    @llm_tool(name="find_song_by_name")
    async def find_song_by_name(self, event: AstrMessageEvent, song_name: str):
        '''通过歌曲名称搜索歌曲信息。

        Args:
            song_name (string): 歌曲名称
        '''
        yield event.plain_result(f"正在搜索歌曲《{song_name}》，请稍候...")
        USER_STATES[event.get_sender_id()] = {
            "state": "waiting_song_name",
            "start_time": time.time()
        }
        async for item in self.process_song_search(event):
            yield item

    @llm_tool(name="play_song_by_number")
    async def play_song_by_number(self, event: AstrMessageEvent, song_number: int):
        '''通过歌曲序号点播歌曲。

        Args:
            song_number (number): 歌曲序号
        '''
        song_info = self.get_song_info(song_number)
        if song_info:
            yield event.plain_result(f"@{event.get_sender_name()} 大人点了第 {song_number} 首歌，都来听！")
            async for message in self.download_song(song_info, event):
                yield message
        else:
            yield event.plain_result("请输入正确的歌曲序号")

    async def generate_song_info_image(self, event: AstrMessageEvent, songs_data):
        template_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "song_info_template.html")
        try:
            with open(template_path, 'r', encoding='utf-8') as f:
                template_content = f.read()

            template = Template(template_content)
            rendered_html = template.render(
                songs=songs_data
            )

            image_url = await self.html_render(rendered_html, {})
            yield event.image_result(image_url)
        except Exception as e:
            yield event.plain_result(f"生成歌曲信息图片失败: {e}")

    async def process_song_search(self, event: AstrMessageEvent):
        song_name = event.message_str.strip()
        yield event.plain_result(f"好吧，我就帮你找找这首叫《{song_name}》的歌")

        current_dir = os.path.dirname(os.path.abspath(__file__))
        crawler_path = os.path.join(current_dir, "crawler.py")
        songs_data_path = os.path.join(current_dir, "songs_data.json")
        pics_dir = os.path.join(current_dir, "pics")

        if not os.path.exists(crawler_path):
            yield event.plain_result("错误：crawler.py 文件不存在，请检查文件路径。")
            return

        try:
            subprocess.run(["python", crawler_path, song_name], check=True)
        except subprocess.CalledProcessError as e:
            yield event.plain_result(f"运行 crawler.py 时发生错误: {e}")
            return

        if not os.path.exists(songs_data_path):
            yield event.plain_result("呃呃啊，解析不了返回的json......")
            return

        if not os.path.exists(pics_dir):
            os.makedirs(pics_dir)

        try:
            with open(songs_data_path, 'r', encoding='utf-8') as json_file:
                json_data = json.load(json_file)
                data = json_data.get("data", [])
                if not data:
                    yield event.plain_result("嗯……没有找到符合要求的歌曲。")
                    return

                msg_list = [Plain("哈...帮你找歌真是废了我好大的劲呢💦💦......\n")]

                for idx, song in enumerate(data, 1):
                    title = song.get("title", "未知歌曲")
                    author = song.get("author", "未知歌手")
                    pic_url = song.get("pic", "无封面图")
                    platform = song.get("type", "未知平台")
                    songid = song.get("songid", "未知ID")
                    url = song.get("url", "无音频链接")

                    image_path = os.path.join(pics_dir, f"{songid}.jpg")
                    if pic_url and not os.path.exists(image_path):
                        try:
                            response = requests.get(pic_url, stream=True)
                            if response.status_code == 200:
                                with open(image_path, 'wb') as f:
                                    for chunk in response.iter_content(1024):
                                        f.write(chunk)
                        except Exception as e:
                            print(f"下载封面图片失败: {e}")

                    msg_list.append(Plain(f"\n✨️✨️✨️✨️✨️✨️✨️✨️✨️✨️✨️✨️✨️✨️✨️✨️✨️✨️✨️\n"))
                    msg_list.append(Plain(f"\n{idx}. 🎵歌曲名称：{title}\n"))
                    msg_list.append(Plain(f"    🧑‍🎤歌手：{author}\n"))
                    msg_list.append(Plain(f"    💽平台：{platform}音乐\n"))
                    if os.path.exists(image_path):
                        msg_list.append(Image.fromFileSystem(image_path))

                    if idx == len(data):
                        msg_list.append(Plain("\n{}秒内发送对应歌曲的序号我就可以帮你点歌~！".format(self.song_number_wait_time)))

                yield event.chain_result(msg_list)

                async for message in self.generate_song_info_image(event, data):
                    yield message

                USER_STATES[event.get_sender_id()] = {
                    "state": "waiting_song_number",
                    "start_time": time.time(),
                    "songs_data": data
                }

                loop = asyncio.get_running_loop()
                loop.call_later(self.song_number_wait_time, self.cancel_song_number_input, event.get_sender_id())

        except Exception as e:
            yield event.plain_result("呃呃呃啊，解析不了返回的json......")
            print(f"Error processing song search: {e}")
