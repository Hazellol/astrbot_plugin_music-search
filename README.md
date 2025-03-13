# astrbot_plugin_music-search

适配AstrBot的交互式歌曲搜索插件

A interactive music-search plugin for AstrBot plugin feature

## 更新
- 新增自定义等待时长配置面板
- 将歌曲信息渲染成图片（还在优化）
- ......
正在努力更新zzz

## 指令

- **/找歌**：发送之后在30s之内发送要搜索的歌名，随即根据bot提示进行点歌操作
- 目前应该支持LLM自然语言搜歌
   <img width="1000" alt="image" src="https://github.com/Hazellol/vivo-50/blob/main/QQ20250212-034321.png">

## 配置

无需配置，后面应该会更新并完善功能。

# 常见问题
- 运行 crawler.py 时发生错误: Command '['python', 'C:\Users\Administrator\Downloads\AstrBotLauncher-0.1.5.5\AstrBotLauncher-0.1.5.5\AstrBot\data\plugins\astrbot_plugin_music_search\crawler.py', '春日影']' returned non-zero exit status 1.

- *解决方法:* 需要运行一下插件目录下的“首次运行请点我.bat”安装requests(能力不足只能这样了awa)

- [botpy] 接口请求异常，请求连接: https://api.sgroup.qq.com/v2/users/xxxxxxxxxxxxx/messages, 错误代码: 400, 返回内容: {'message': '消息发送失败, 不允许发送url crawler.py,crawler.py', 'code': 40054010, 'err_code': 40054010, 'trace_id': '6179d5176.......................

- *原因* 目前不适配QQ官方机器人
# 开发

- 本人也是初次开发，有不足请包含！
- 参考 [AstrBot 插件开发文档](https://astrbot.soulter.top/dev/plugin.html) 了解更多插件开发和打包上传的细节。
