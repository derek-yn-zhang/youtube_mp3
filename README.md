# 💿 YouTube_MP3
Rip MP3 audio tracks from YouTube videos

## Dependencies
Python 3.12 [[Pyenv]](https://github.com/pyenv/pyenv?tab=readme-ov-file#installation)

## Installation
Install `virtualenv` if you have not already
```
pip install virtualenv
```

Create Python 3.12 virtual environment
```
python3.12 -m venv "venv"
```

Activate the virtual environment
```
source ./venv/bin/activate
```

Install dependencies in the virtual environment
```
pip install -r requirements.txt
```

## Usage

### Help
```
python main.py -h
```

### 💿 Single Track
```
python main.py -t FeelingBlew__Covers.json -b safari
```

### 💿💿 Multiple Tracks
```
python main.py -t Go_Sailor__Go_Sailor.json -b safari
```

## User Notes

### Cookies
Make sure you are signed into YouTube from either Chrome, Edge or Safari.  

If using Safari, give Full Disk Access to Terminal. [[Issue]](https://github.com/yt-dlp/yt-dlp/issues/7392#issuecomment-1657496651)  

Try using an incognito window if you have trouble. [[Issue]](https://github.com/yt-dlp/yt-dlp/issues/8227#issuecomment-1793513579)  

### Playlists
Make sure you don't copy video links from a playlist view, this creates a download loop the size of playlist.  
Check for urls ending in `&list={list_id}&index={index_id}` and delete this segment of the url if needed.

## `[TODO]`
- Thread