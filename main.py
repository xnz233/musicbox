import crawler
from prompt_toolkit import prompt, choice
from prompt_toolkit.shortcuts import confirm

# song_name = 'always online'

song_name = prompt("请输入查找的歌曲名称:")
song_list = crawler.search_music(song_name)
song = choice(
        "请选择要下载的歌曲",
        options=[
            (song, f"{song.name} - {','.join(song.artist)}") for song in song_list
        ],
    )
crawler.download_song(song,lyric=confirm('是否下载歌词? ',suffix="(Y/n)") or True)
