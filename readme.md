# How to use
### Option 1: run the pre-compiled executable
Run the pre-compiled program (e.g., ii-kanji-macos) directly or via console
### Option 2: run via the source
In the source folder, run app.py with python. You need to install numpy as well to run this.

In either case, once you start the program, it will create `config.txt` where you can customize the lesson.
In the config file, you can edit your user name (this is required to track the scores), the lesson catagory (meaning, onyomi, or kunyomi), and JLPT levels (which set of kanji you want to memorize)

# Features
```
 ╭───────────┬────────────────────────────────────────────────────────────╮
 │           │        player: diptip                                      │
 │ ii-KANJi™ │      attempts: 2261                                        │
 │ ʙy ᴅɪᴩᴛɪᴩ │         level: N5 (80 words), N4 (80 words)                │
 │           │ session score: 0.884                                       │
 ╰───────────┴────────────────────────────────────────────────────────────╯

   What's the meaning of 友
   (dynamic difficulty: 0/10)
    >> friend
    ✅ meaning: friend
        onyomi: yuu
       kunyomi: tomo

   What's the meaning of 以
   (dynamic difficulty: 0/10)
    >> compar
    ✅ meaning: by means of, because, in view of, compared with
        onyomi: i
       kunyomi: mo(tte)

   What's the meaning of 有
   (dynamic difficulty: 0/10)
    >>

 ╭────────────────────────────────────────────────────────────────────────╮
 │ type -x to close the program                                           │
 ╰────────────────────────────────────────────────────────────────────────╯
```
## Scores and Weights
The program keeps track of which question you got right and wrong in the folder `scores/<player_name>`. This is use to dynamically determine the next question. For example, if you are not good with a certain kanji, it will appear more often (higher weight) than another kanji where you find easy (lower weight). The weight of the draw is given by
```math
\text{weight} = \frac{2+\text{loses}}{2+\text{wins}+\text{loses}}.
```
Don't be afraid to be wrong!

## Lessons
There are 3 kinds of lessons. 'meaning' will ask you the meaning of a given kanji. To simplify the lesson, I just check if your answer in lower case is contained within one of the prepared answers or not. For example, the prepared answers for the meaning of 以 are "by means of", "because", "in view of", and "compared with". So if you answer with "compa", the program will still consider it as correct because "compa" is a substring of "compared with". If the prepared answer is "thought" and your answer is "think", the program will still count it as wrong, so keep that in mind.

'onyomi' and 'kunyomi' lessons is similar to 'meaning'. You can mix the lessons by including multiple of them in the config file.

