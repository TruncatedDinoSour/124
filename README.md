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

# features

-   free AI access using `/ai` and `/chatai`, `/aiimg`
    -   supported text models : gpt3, gpt4, [todo] deepai and alpaca 7b
    -   supported image models : prodia, [todo] pollinations
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
    -   `random [optional n default = 1]` which uses
    -   `loop` and `repeat` for looping the queue and repeating current tacks
    -   `info` for displaying the music bot info
    -   saving of queues using `save [name]`
    -   listing of queues or their content using `listq [optional name]`
    -   loading of queues using `load [name]` or `loadadd [name]` for adding it instead of overwriting it
    -   [todo https://stackoverflow.com/questions/76829194/how-do-i-skip-x-seconds-in-discord-py-audio-source] `seek ( - )[seconds]` to skip time back or forth
-   support for `neofetch` in linux servers
-   `/pfp` command to extract user profile pictures
-   rules database using `/rules` and `/ruleslb`
    -   to create rules create a `#rules` channel and type something
        adding `(real rule)`, `( real rule )`, `(fake rule)` or `( fake rule )`
        at the end of your rule, for example `hello ( fake rule )`,
        all rules must be unique, it wont create a new rule if its already a rule,
        rules are case sensitive
-   chat score database using `/score` and `/scorelb`
    -   based off a complex formula taking these inputs
        -   average bytes sent per all messages sent ( positive effect )
        -   average time ( in seconds ) spent in all voice chats ( positive effect )
        -   square root of all reactions gotten ( positive effect )
        -   log base 2 of all rules made ( positive effect )
        -   log of all `ok`s + 1 in the ok channel ( positive effect )
        -   messages ppl started of urs ( positive effect )
        -   square root of all posted ( given ) reactions ( negative effect )
        -   stars removed if u star a message ( negative effect )
        -   inverse average of all values ( neutral effect )
        -   all divided by times uve been kicked off the scoreboard ( linear effect )
-   support for starboard using `/starboard` to set the starboard channel
-   `/timelb` which keeps track of how long a person stayed in the server
-   `/tod` for truth, dare or paranoia games
-   `/wordcloud` which keeps track of all unique words used in the server
-   `/src` for displaying a url for source code
-   `/invite` for displaying the top invite
-   `/cat` and `/anime` pics
-   `/kicks` and `/kickslb` scoreboards for kick scores ( how many times uve been kicked off )
-   easy setup
-   developer-friendly configuration in `src/bot124/const.py`
-   feature packed and light
