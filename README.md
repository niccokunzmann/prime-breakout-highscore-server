# Prime Breakout Highscore Server

This server only serves the high score of the game
[Prime Breakout][prime-breakout].
Feel free to fork it, modify it and use it.

## API

- `/update_highscore.js`
    calls `update_highscore(highscore)` in the JavaSript file that is delivered
- `/update_highscore.js?scores=[...]`
    same as above
    additionally adds the high scores listed as a parameter

A `highscore` is a json of this form:
```
{
  version: 1, // the version as an integer, increasing as the score is modified
  scores: [
    {
      id: 1, // the local id of a score in an app, not global, as int
      name: "The Developer", // a string
      points: 42 // an integer
    },
    // ... more scores
  ]
}
```


[prime-breakout]: https://niccokunzmann.gitlab.io/prime-breakout/
