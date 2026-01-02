"""一个交互式命令行界面，用于从网络上搜索和下载音乐。"""

import os
from typing import Callable, List
from dataclasses import dataclass
from prompt_toolkit import prompt, choice
from prompt_toolkit.shortcuts import confirm

import crawler


@dataclass
class DownloadOption:
    """
    用于封装一个下载选项的元数据类。
    """

    name: str
    handler: Callable


download_options: List[DownloadOption] = []  # 下载选项的全局列表


def register_options(name: str):
    """用于注册菜单的装饰器工厂

    Args:
        name (str): 菜单名
    """

    def decorator(func):
        option = DownloadOption(name, func)
        download_options.append(option)
        return func

    return decorator


@register_options("下载单首")
def _download_single(need_lyric):
    """
    提示用户输入歌曲名，进行搜索，然后让用户从搜索结果中
    选择一首歌曲进行下载
    """
    song_name = prompt("请输入查找的歌曲名称:")
    song_list = crawler.search_music(song_name)
    song = choice(
        "请选择要下载的歌曲",
        options=[
            (song, f"{song.name} - {','.join(song.artist)}") for song in song_list
        ],
    )
    song.download(lyric=need_lyric)


@register_options("批量下载")
def _download_from_txt(need_lyric):
    """
    读取一个名为 `music.txt` 的文件，逐行解析歌曲名，
    并自动下载每首歌曲的第一个搜索结果。以 `#` 开头的行将被视为注释并忽略。
    """
    filename = "music.txt"
    if not os.path.exists(filename):
        with open(filename, "w", encoding="UTF-8") as f:
            print(f"已创建搜索文件 {filename} ,填写后保存")
            f.write(
                "# 请在下面每输入要搜索的歌名，一行一首\n# 以'#'开头的行将被忽略\n"
            )
        prompt('保存后请回车确认...')
    with open(filename,encoding="UTF-8") as f:
        songs_name = []
        for song_name in f:
            if song_name.startswith("#"):  # 忽略#开头的行
                continue
            songs_name.append(song_name)
        songs: List[crawler.Song] = crawler.batch_search(songs_name)
        crawler.batch_download(songs, need_lyric)


if __name__ == "__main__":
    print("MP3用户建议下载歌词")
    need_lyric = confirm("是否下载歌词? ", suffix="(Y/n)") or True

    selected_option = choice(
        "请选择下载方式",
        options=[(option, option.name) for option in download_options],
    )
    selected_option.handler(need_lyric)
    prompt('按回车键退出...')
