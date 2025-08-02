# syncSound

A P-O-S python script for syncing music from youtube music down to your device


# Usage

Put full links to albums into into links.txt
Run the script using python 3.
 
## Files

Create or let the script create links.txt and history.txt in the root folder of the script.
The script will attempt to sync music files into appropriately named folders.
The file structure is /Artist/Album

# Required modules

pip install yt-dlp
pip install ffmpeg
pip install mutagen

install other stuff the script tells you to, this is probably the only time I'm updating the readme

# Troubleshooting

If not working
```
pip install yt-dlp --upgrade
```
Will fix 99% of your issues.
Some linux systems wont like you installing python modules. Ignore the warning, and force install. All modules need to be installed using pip.


# Feedback

Will be ignored
