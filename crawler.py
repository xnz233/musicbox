"""负责歌曲类管理和数据爬取"""

from typing import List, Optional, Literal
import requests
import os
from dataclasses import dataclass
from concurrent.futures import ThreadPoolExecutor, as_completed

URL = "http://www.yinyueku.cn/api.php"
HEADERS = {
    "user-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/143.0.0.0 Safari/537.36 Edg/143.0.0.0",
    "content-type": "application/x-www-form-urlencoded; charset=UTF-8",
}


@dataclass
class Song:
    """
    歌曲类
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
        
    def download(self, lyric=True,output_folder:str='output'):
        """下载Song中的一首歌曲或歌词

        Args:
            self (Song): 歌曲对象
            lyric (bool, optional): 是否需要歌词, 默认需要
            output_folder (str, optional): 输出目录
        """
        os.makedirs(output_folder,exist_ok=True)
        if url := self.music_url:
            filename =f"{self.name} - {','.join(self.artist)}"
            file_path = os.path.join(output_folder,filename)
            if os.path.exists(file_path + ".mp3"):
                print(f"跳过已下载歌曲：{filename}")
                return
            print(f'下载 {filename} 中...')
            resp = requests.get(url, headers=HEADERS)
            with open(file_path + ".mp3", "wb") as f:
                f.write(resp.content)
            if lyric and self.lyric:    
                with open(file_path + ".lrc", "w") as f:
                    f.write(self.lyric)
            print(f'{filename} 下载成功！')


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


def batch_download(songs: List['Song'], lyric: bool = True, 
                      output_folder: str = 'output', max_workers: int = 5) -> None:
        """多线程批量下载歌曲
        
        Args:
            songs: 歌曲对象列表
            lyric: 是否下载歌词
            output_folder: 输出目录
            max_workers: 最大线程数
        """
        os.makedirs(output_folder, exist_ok=True)
        
        with ThreadPoolExecutor(max_workers=max_workers) as executor:
            # 提交所有下载任务
            futures = [
                executor.submit(song.download, lyric=lyric, output_folder=output_folder)
                for song in songs
            ]
            
            # 等待所有任务完成并处理结果
            for future in as_completed(futures):
                try:
                    future.result()  # 可以获取异常信息
                except Exception as e:
                    print(f"下载任务出错: {str(e)}")

def batch_search(songs_name: List[str],max_workers: int = 5) -> List[Song]:
    """多线程搜索歌曲
    获取搜索结果中第一项

    Args:
        songs_name (List[str]): 歌曲名列表
        max_workers (int, optional): 最大线程数

    Returns:
        List[Song]: 多个搜索结果第一项的Song对象列表
    """
    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        futures = [executor.submit(search_music,song_name)
                   for song_name in songs_name]
        
        results:List[Song] = []
        for future in as_completed(futures):
                try:
                    result=future.result()
                    results.append(result[0])
                except Exception as e:
                    print(f"下载任务出错: {str(e)}")
    return results

if __name__ == "__main__":
    song_list = search_music("always online")
    song_list[0].download()
