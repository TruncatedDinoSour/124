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

- free AI access using `/ai` and `/chatai`, `/aiimg`
    - supported text models : gpt3, gpt4 and alpaca 7b
    - supported image models : prodia
- anonymous confessions database using `/confess` and `/confessions`
- auto-generated help page accessed through `/help`
- music commands and control using `/music`
    - typing `help` shows help
    - `quit` makes the bot quit the voice chat and deletes the control thread
    - access to the queue by typing `queue` and access to current track using `currentn`
    - stopping of music using `stop` and playing with `play`
    - skipping of tracks using `skip`
    - volume control by using `volume [vol in %]`
    - true shuffling using true randomness using `shuffle`
    - queues for both commands and music makes sure everything is managed and ran
    - support for youtube searches ( just type anything in the thread ), youtube urls and youtube playlists
- support for `neofetch` in linux servers
- `/pfp` command to extract user profile pictures
- rules database using `/rules` and `/ruleslb`
    - to create rules create a `#rules` channel and type something
      adding `(real rule)`, `( real rule )`, `(fake rule)` or `( fake rule )`
      at the end of your rule, for example `hello ( fake rule )`,
      all rules must be unique, it wont create a new rule if its already a rule,
      rules are case sensitive
- chat score database using `/score` and `/scorelb`
- support for starboard using `/starboard` to set the starboard channel
- `/timelb` which keeps track of how long a person stayed in the server
- `/tod` using ai to generate truth or dare prompts for fun
- `/wordcloud` which keeps track of all unique words used in the server
- easy setup
- developer-friendly configuration in `src/bot124/const.py`
- feature packed and light
