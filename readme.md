
# ii-KANJi
Want to memorize JLPT kanji? Use ii-KANJi!

> [!NOTE]
> The list of kanji is scraped from [JLPT Sensei](https://jlptsensei.com/). Thanks!

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
## How to use
First of all, [download it here](https://github.com/Diptipper/ii-kanji/archive/refs/heads/main.zip).
Then run the pre-compiled program (e.g., ii-kanji-macos) directly or via console.
Once you start the program, it will create `config.txt` where you can customize the lesson.
In the config file, you can edit your user name (this is required to track the scores), the lesson catagory (meaning, onyomi, or kunyomi), and JLPT levels (which set of kanji you want to memorize)

## Scores and Weights
The program keeps track of which question you got right and wrong in the folder `scores/<player_name>`. This is use to dynamically determine the next question. For example, if you are not good with a certain kanji, it will appear more often (higher weight) than another kanji where you find easy (lower weight). The weight of the draw is given by
```math
\text{weight} = \frac{2+\text{loses}}{2+\text{wins}+\text{loses}}.
```
The 'dynamic difficulty' shown during the run is nothing but $\lfloor 10\times \text{weight}\rfloor$.

Don't be afraid to be wrong!

## Lessons
There are 3 kinds of lessons. 'meaning' will ask you the meaning of a given kanji. To simplify the lesson, I just check if your answer in lower case is contained within one of the prepared answers or not. For example, the prepared answers for the meaning of 以 are "by means of", "because", "in view of", and "compared with". So if you answer with "compa", the program will still consider it as correct because "compa" is a substring of "compared with". If the prepared answer is "thought" and your answer is "think", the program will still count it as wrong, so keep that in mind.

For the JLPT levels, you can add the whole level by using a whole number (4 means all 167 words from N4), or with increments of 10 (4.5 means 41-st to 50-th words of N4), or combined (5, 4.1, 4.3 means all of N5 words and words number 1-10 and 21-30 from N4).

'onyomi' and 'kunyomi' lessons is similar to 'meaning'. You can mix the lessons by including multiple of them in the config file.

