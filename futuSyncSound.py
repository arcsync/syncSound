import requests
import subprocess
import os
import json
from datetime import datetime

mutagenEnabled = None
try:
    from mutagen.mp3 import MP3
    from mutagen.id3 import ID3, APIC, error
    mutagenEnabled = True
except ImportError:
    print("\n Missing mutagen module, album art attachment will not be preformed")
    print("\n please install mutagen")
    print("\n pip install mutagen")
    print("\n proceeding without mutagen, album art attachment will not be preformed")
    print("\n advanced metadata operations will not be preformed")
    input("\n Press Enter to continue...")
    mutagenEnabled = False


__version__ = 'first and a half since started versioning now with ugly bootstraps for adding album art via mutagen'
file = open('links.txt', 'r')
history = open('history.txt', 'a')
raw = file.readlines()
sanitizedLinks = []
unsanitizedLinks = []
ignored = []
i = 0

#region STRING VARS
audioArgs = ' -x --audio-format mp3 --audio-quality 0 --embed-metadata'
additionalArgs = ' --windows-filenames --no-warnings --cookies-from-browser firefox'
artArgs = """ --write-thumbnail --convert-thumbnails jpg --ppa "ThumbnailsConvertor+ffmpeg_o:-c:v png -vf crop='ih'" """
firstTrackOnly = ' --playlist-items 1 --skip-download --no-warnings'
outputTemplateArgs = r' -o "%(uploader)s/%(uploader)s - %(playlist)s/%(title)s.%(ext)s"'
outputTemplateArgsExtended = r' -o "pl_thumbnail:%(uploader)s/%(uploader)s - %(playlist)s/cover.%(ext)s" -o "thumbnail:"'
forbiddenSuffix = (' ', '.')
forbiddenChars = (r'<', r'>', r':', r'"', '\\', r'/', r'|', r'?', r'*')
forbiddenNames = ('CON', 'PRN', 'AUX', 'NUL', 'COM1', 'COM2', 'COM3', 'COM4', 'COM5', 'COM6', 'COM7', 'COM8', 'COM9',
'LPT1', 'LPT2', 'LPT3', 'LPT4', 'LPT5', 'LPT6', 'LPT7', 'LPT8', 'LPT9')
#endregion

def sanitizeName(name):
    print('\n Sanitizing Name')
    if name.endswith(forbiddenSuffix):
        print('\n' + name + ' name ends with "' + name[-1] + '"' + ' replacing recursively.')
        name = name.strip()
        name = name.replace(".","")
        sanitizeName(name)
    if any(char in name for char in forbiddenChars):
        print('\n' + name + ' name contains forbidden chars, replacing recursively.')
        for char in forbiddenChars:        
            name = name.replace(char, 'x')
        sanitizeName(name)
    for ban in forbiddenNames:
        if ban == name:
            name = 'asshole'
    return name

def getMetadataViaJSON(link):
    success = True
    artist = 'none'
    album = 'none'
    print('\n Getting and parsing data...')
    jsonStr = 'yt-dlp'+ ' ' + link + firstTrackOnly + ' --write-info-json -o "' + str(i) + r'.json"' + ' --referer ' + link
    print('\n     JSONSTR:   '+jsonStr)
    try:
        subprocess.run(jsonStr, shell=True, check=True)
    except subprocess.CalledProcessError as e:
        print("\n Exception getting metadata: \n" + str(e) + '\n\n')
        print('\n For link: ' + link)
        print('\n For JSONSTR: ' + jsonStr)
        print('adding link to fallback queue...')
        unsanitizedLinks.append(link)
        success = False
        return artist, album, success

    trackJSONhandler = open(str(i) + r'.json.info.json', 'r', encoding='utf-8', errors = "ignore")
    trackJSONraw = trackJSONhandler.readlines()
    albumJSONhandler = open(str(i) + r'.info.json', 'r', encoding='utf-8', errors = "ignore")
    albumJSONraw = albumJSONhandler.readlines()
    trackJSON = json.loads(trackJSONraw[0])
    albumJSON = json.loads(albumJSONraw[0])    
    artist = trackJSON['artists'][0].strip()
    album = trackJSON['album'].strip()
    albumArtLink = albumJSON['thumbnails'][1]['url']
    if albumArtLink is None:
        albumArtLink = albumJSON['thumbnails'][0]['url']
    trackJSONhandler.close()
    albumJSONhandler.close()
    os.remove(str(i) + '.json.info.json')
    os.remove(str(i) + '.info.json')
    
    artist = sanitizeName(artist)
    album = sanitizeName(album)
    print('\n    Album data:')
    print('\n   Author: ' + artist)
    print('\n   Album: ' + album)
    print('\n   AlbumArt link: ' + albumArtLink)
    print('\n')
    print('\n Getting album art')  
    print('\n')  
    newpath = r'./' + artist + r'/' + artist + ' - ' + album
    os.makedirs(newpath, exist_ok = True)
    artData = requests.get(albumArtLink).content
    artSaveDir = newpath + r'/' + 'folder.png'
    with open(artSaveDir, 'wb') as Art:
        Art.write(artData)
    return artist, album, success

def appendHistory(artist, album, link):
    history.writelines("\n")
    #fucking americans and their crappy time formats...
    history.writelines("\nDate: " + datetime.now().strftime("%A %d %B %Y %H:%M:%S:%f"))
    history.writelines("\n" + artist + " - " + album)
    history.writelines("\n" + link)

def sanitizeLinks(links):
    for link in links:
        link = link.strip()
        link = link.replace("\'n", '')
        if not link.startswith('https://music.youtube.com/playlist?list='):
            print('\nX#####X')
            print('\n#X###X# Warning')
            print('\n##X#X## Unexpected link provided')
            print('\n###X### ' + link)
            print('\n##X#X## Please refer to (inexistent) documentation')
            print('\n#X###X# Link format expected: https://music.youtube.com/playlist?list=...')
            print('\nX#####X Please provide a valid URL. This will be attempted but will likely fail.')
            print('\n \n Will be processed via fallback mode.')
            unsanitizedLinks.append(link)
        elif link.startswith('#'):
            ignored.append(link)
        else:
            sanitizedLinks.append(link)

def realityCheck():
    try:
        subprocess.run('yt-dlp --version', shell=True, check=True)
        subprocess.run('ffmpeg -version', shell=True, check=True)
    except Exception as e:
        print("\n")
        print("\n Exception: " + str(e))
        print("\n")
        print("\n An exception occurred, please make sure you have both yt-dlp and ffmpeg installed.")
        print("\n pip install yt-dlp")
        print("\n pip install ffmpeg")
        print("\n")
        input("\n Press Enter to continue...")
        exit(1)
    try:
        f = open('links.txt', 'r')
        f.close()
    except Exception as e:
        print("\n Exception opening links.txt: " + str(e))
        f = open('links.txt', 'xt')
        f.close()
        print("\n links.txt was missing and has been created")
        print("\n terminating since newly created links file is empty")
        print("\n")
        input("\n Press Enter to continue...")
        exit(1)
    try:
        f = open('history.txt', 'r')
        f.close()
    except Exception as e:
        print("\n Exception opening history.txt: " + str(e))
        f = open('history.txt', 'xt')
        f.close()
        print("\n history.txt was missing and has been created")
    return True


def fallbackMode(unsanitizedLinks):
    for link in unsanitizedLinks:
        print('\nxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx')
        print('\n FALLBACK MODE \n \n \n')
        print('\nAttempting download of ' + link)
        try:
            fallbackStr = 'yt-dlp' + ' ' + link + audioArgs + additionalArgs + outputTemplateArgs + ' --referer ' + link
            subprocess.run(fallbackStr, shell=True, check=True)
        except Exception as e:
            print("\n Exception in fallback mode: " + str(e))
            print("\n retrying with less args")
            try:
                fallbackStr = 'yt-dlp' + ' ' + link + audioArgs + additionalArgs + ' --referer ' + link
                subprocess.run(fallbackStr, shell=True, check=True)
            except Exception as e:
                print("\n Exception in second fallback mode: " + str(e))
                print("\n retrying with even less args")
                try:
                    fallbackStr = 'yt-dlp' + ' ' + link + ' -x --audio-format mp3 --audio-quality 0'
                    subprocess.run(fallbackStr, shell=True, check=True)
                except Exception as e:
                    print("\n Exception in third fallback mode: " + str(e))
                    print("\n just trying to get the damn content")
                    try:
                        fallbackStr = 'yt-dlp' + ' ' + link
                        subprocess.run(fallbackStr, shell=True, check=True)
                    except Exception as e:
                        print("\n Exception in last fallback mode: " + str(e))
                        print("\n Not gonna retry")


def fullMode(sanitizedLinks):
    print('\n#####################links provided:#################################')
    print('\n')
    for link in sanitizedLinks:
        print('\n' + link)
    print('\nlinks ignored:' + str(len(ignored)))
    for ignoredLink in ignored:
        print('\n' + ignoredLink)
    print('\n######################################################')
    successful = 0
    i = 0
    for link in sanitizedLinks:
        i += 1
        print('\nxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx')
        print('Working on album ' + str(i) + ' of ' + str(len(sanitizedLinks)))
        print('\n' + link)
        print('\n')

        artist, album, getMetadataWasSuccesfull = getMetadataViaJSON(link)
        if not getMetadataWasSuccesfull:
            print("\n Metadata could not be retrieved")
            print("\n Skipping this in fullQueue")
            break

        print('\n Reassembling output template')
        print('\n')
        outputTemplateArgs = r' -o ' + '"' + artist + r'/' + artist + ' - ' + album + r'/' + '%(title)s.%(ext)s"'

        fullstr = 'yt-dlp' + ' ' + link + audioArgs + additionalArgs + outputTemplateArgs + ' --referer ' + link
        subprocess.run(fullstr, shell=True)
        currentAlbumDir = "./" + artist + "/" + artist + ' - ' + album + r'/'
        if mutagenEnabled:
            mp3s = getMp3Files(currentAlbumDir)
            art = getAlbumImage(currentAlbumDir)
            attachAlbumArt(mp3s, art)

        appendHistory(artist, album, link)
        successful += 1
        print('xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx\n')
    print('\n' + str(successful) + ' links (albums/playlists) downloaded')

def getMp3Files(currentAlbumDir):
    mp3Files = []
    for file in os.listdir(currentAlbumDir):
        if file.endswith(".mp3"):
            mp3Files.append(currentAlbumDir + '\\' + file)
    return mp3Files

def getAlbumImage(currentAlbumDir):
    arts = [f for f in os.listdir(currentAlbumDir) if (f.endswith('.jpg') or f.endswith('.png'))]
    return (currentAlbumDir + '\\' + arts[0])

#TODO: to dodawanie wszedzie currentAlbumDir jest ugly af musze to ogarnac
def attachAlbumArt(mp3s, art):
    for mp3 in mp3s:
        track = MP3(mp3, ID3=ID3)
        try:
            track.add_tags()
        except error:
            pass
        with open(art, "rb") as img:
            track.tags.add(
                APIC(
                    encoding=3,
                    mime='image/jpeg' if art.endswith('.jpg') else 'image/png',
                    type=3,
                    desc='Cover',
                    data=img.read()
                )
            )
        track.save()
        print("\n album art added to " + mp3)

def main():
    print('\n Version: ' + __version__)
    if not realityCheck():
        exit(1)

    sanitizeLinks(raw)
    fullMode(sanitizedLinks)
    fallbackMode(unsanitizedLinks)

if __name__ == '__main__':
    main()






        