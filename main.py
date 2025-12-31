import os
from typing import Callable, List
from dataclasses import dataclass
from prompt_toolkit import prompt, choice
from prompt_toolkit.shortcuts import confirm

import crawler

@dataclass
class DownloadOption:
    """管理下载方法的类
    """
    name: str
    handler: Callable


download_options: List[DownloadOption] = []


def register_options(name:str):
    """用于注册菜单的装饰器

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
    filename = "music.txt"
    if os.path.exists(filename):
        with open(filename) as f:
            for song_name in f:
                if song_name.startswith("#"):
                    continue
                song = crawler.search_music(song_name)[0]
                song.download(need_lyric)
    else:
        with open(filename, "w") as f:
            print(f"已创建搜索文件{filename},填写后重新运行")
            f.write(
                "# 请在下面每输入要搜索的歌名，一行一首\n# 例子: always online 林俊杰"
            )


if __name__ == "__main__":
    print("MP3用户建议下载歌词")
    need_lyric = confirm("是否下载歌词? ", suffix="(Y/n)") or True

    selected_option = choice(
        "请选择下载方式",
        options=[(option, option.name) for option in download_options],
    )
    selected_option.handler(need_lyric)
