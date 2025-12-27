from typing import List, Optional, Literal
import requests
import os
from dataclasses import dataclass

URL = "http://www.yinyueku.cn/api.php"
HEADERS = {
    "user-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/143.0.0.0 Safari/537.36 Edg/143.0.0.0",
    "content-type": "application/x-www-form-urlencoded; charset=UTF-8",
}


@dataclass
class Song:
    """
    歌曲信息类
    """

    album: str
    artist: list[str]
    id: int
    lyric_id: str
    pic_id: str
    sign: str
    name: str
    source: str
    url_id: int

    _music_url: Optional[str] = None
    _lyric: Optional[str] = None

    def _get_url(self, types: Literal["music", "lyric"]) -> Optional[dict]:
        data = f"id={self.id}&song={self.id}&source={self.source}&sign={self.sign}"
        if types == "music":
            data += "&types=url"
        elif types == "lyric":
            data += "&types=lyric"

        try:
            resp = requests.post(url=URL, data=data, headers=HEADERS, timeout=10)
            resp.raise_for_status()
        except requests.exceptions.Timeout:
            print("请求超时")
            return None
        except requests.exceptions.HTTPError as e:
            print(f"HTTP请求错误: {e}")
            return None
        except requests.exceptions.ConnectionError:
            print("网络连接错误")
            return None
        except Exception as e:
            print(f"未知错误:{e}")
            return None

        return resp.json()

    @property
    def music_url(self) -> Optional[str]:
        if self._music_url:
            return self._music_url
        json_data = self._get_url(types="music")
        if json_data:
            music_url = json_data["url"]
            self._music_url = music_url
            return music_url

    @property
    def lyric(self) -> Optional[str]:
        if self._lyric:
            return self._lyric
        json_data = self._get_url(types="lyric")
        if json_data:
            lyric = json_data["lyric"]
            self._lyric = lyric
            return lyric


def search_music(song_name: str) -> List[Song]:
    """通过API搜索歌曲

    Args:
        song_name (str): 歌曲名称

    Returns:
        List[Song]: 歌曲列表
    """
    song_list = []
    data = f"types=search&count=10&pages=1&name={song_name}"
    try:
        resp = requests.post(url=URL, data=data, headers=HEADERS, timeout=10)
        resp.raise_for_status()
        json_data = resp.json()
        for song_data in json_data:
            try:
                song_obj = Song(**song_data)
                song_list.append(song_obj)
            except TypeError as e:
                print(f"创建Song对象失败: {e}")
                continue
            except Exception as e:
                print(f"处理单首歌曲数据失败: {e}")
                continue
    except requests.exceptions.Timeout:
        print("搜索请求超时")
    except requests.exceptions.HTTPError as e:
        print(f"搜索请求HTTP错误: {e}")
    except requests.exceptions.ConnectionError:
        print("搜索请求网络连接错误")
    except requests.exceptions.JSONDecodeError:
        print("搜索响应数据不是有效的JSON格式")
    except Exception as e:
        print(f"搜索歌曲失败: {e}")

    return song_list


def download_song(song: Song, lyric=True,output_folder:str='output'):
    """下载Song中的一首歌曲或歌词

    Args:
        song (Song): 歌曲对象
        lyric (bool, optional): 是否需要歌词, 默认需要
        output_folder (str, optional): 输出目录
    """
    os.makedirs(output_folder,exist_ok=True)
    if url := song.music_url:
        file_name = os.path.join(output_folder,f"{song.name} - {','.join(song.artist)}")
        print(f'下载 {file_name} 中...')
        resp = requests.get(url, headers=HEADERS)
        with open(file_name + ".mp3", "wb") as f:
            f.write(resp.content)
        if lyric and song.lyric:    
            with open(file_name + ".lrc", "w") as f:
                f.write(song.lyric)
        print('下载成功！')

if __name__ == "__main__":
    song_list = search_music("always online")
    download_song(song_list[0])
