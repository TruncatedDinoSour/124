# 124

> silly little bot for my friend grp server

ur also free to join it if u want, it was made public for clyde AI access,
but honestly its mainly used for fun at this point : <https://discord.gg/PqcseUzDGF>

# running

```sh
python3 -m pip install --user -r requirements.txt
export D='your-discord-token'
python3 src/main.py
```

ty

# thank you

-   https://cataas.com/ for cat pics
-   https://github.com/cat-milk/Anime-Girls-Holding-Programming-Books for anime girls holding programming books
-   https://gimmeproxy.com/ for free proxies
-   https://api.adviceslip.com/ for advice
-   https://ari-web.xyz/gh/rebelai ( me ) for ai library shit :3

# features

-   free AI access using `/ai` and `/chatai`, `/aiimg`
    -   supported text models : gpt3, gpt4, deepai, alpaca 7b, inferkit, falcon 40 b
    -   supported image models : prodia, pollinations
-   anonymous confessions database using `/confess` and `/confessions`
-   auto-generated help page accessed through `/help`
-   music commands and control using `/music`
    -   controlled through a thread
    -   u can send messages in it as normal but prefix it with `;`
    -   support for youtube urls, playlists and search queries ( u have to just type anything without prefixing it with a command or `;` and itll be treated as a search query )
    -   human-readable and uncomplicated command syntax
    -   `help` which shows the auto-generated help page for music commands
    -   `quit` for clean quitting, also happens if the voice chat is empty
    -   support for clearing all queues -- command queue and music queue with `clear`
    -   `pause` and `play` commands for controlling audio playback
    -   `next`, `begin`, `end`, `back` and `goto [idx starting at 1]` for controlling the queue cursor
    -   `remove [optional idx default = current]` and `pop` for removing songs in the queue
    -   `volume [vol in %]` for volume control and `volume` checking
    -   true shuffling support with `shuffle`
    -   showing of current song and audio source using `current`
    -   `random [optional n default = 1] [optional topics default = ...]` which uses ai to suggest songs, default topics r alternative music
    -   `loop` and `repeat` for looping the queue and repeating current tacks
    -   `info` for displaying the music bot info
    -   saving of queues using `save [name]`
    -   listing of queues or their content using `listq [optional name]`
    -   loading of queues using `load [name]` or `loadadd [name]` for adding it instead of overwriting it
    -   `delq [name]` to delete queues ( only admins )
-   support for `/neofetch` in linux servers
-   `/pfp` command to extract user profile pictures
-   rules database using `/rules` and `/ruleslb`
    -   to create rules create a `#rules` channel and type something
        adding `(real rule)`, `( real rule )`, `(fake rule)` or `( fake rule )`
        at the end of your rule, for example `hello ( fake rule )`,
        all rules must be unique, it wont create a new rule if its already a rule,
        rules are case sensitive
-   chat score database using `/score` and `/scorelb`
    -   based off a formula taking these inputs
        -   total send text bytes in all messages ( positive effect )
        -   total message count ( positive effect )
        -   average voice chat length in seconds ( weighted positive effect )
        -   log2 of time spent in seconds in voice chats + 1 ( weighted positive effect )
        -   log2 of all new words + 1 ( weighted positive effect )
        -   all reactions received ( positive effect )
        -   all reactions posted ( weighted negative effect )
        -   log of all `ok`s + 1 ( positive effect )
        -   diff between 2 utc timestamps -- now and ur last activity ( exponential negative effect )
        -   stars removed ( weighted negative effect )
        -   star participations ( weighed positive effect )
        -   \- score bar ( constant negative effect )
        -   \* score weight ( constant neutral effect )
        -   / kicks ( constant linear effect )
        -   \*\* score exponent ( constant exponential effect )
-   support for starboard using `/starboard` to set the starboard channel
-   `/timelb` which keeps track of how long a person stayed in the server
-   `/tod` for truth, dare or paranoia games
-   `/wordcloud` which keeps track of all unique words used in the server
-   `/src` for displaying a url for source code
-   `/invite` for displaying the top invite
-   `/cat` and `/anime` pics
-   `/kicks` and `/kickslb` scoreboards for kick scores ( how many times uve been kicked off )
-   `/advice` for random advice and searching for it
-   `/tr` for ai-powered translations
-   `/deepai` for more customisable deepai model access
-   `/prodia` for more customisable prodia model access
-   `/yt` for searching youtube :)
-   `/r34` bc my friends forced me to ( i am not happy abt it )
-   ping `/everyone` individually with a single command
-   `/guilds` for showing all guilds the bot is in
-   get the server `/icon`
-   `/uwu`-ify text
-   `/tkill` all threads
-   easy setup
-   developer-friendly configuration in `src/bot124/const.py`
-   feature packed and light
