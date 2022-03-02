# Prime Breakout Highscore Server

This server only serves the high score of the game
[Prime Breakout][prime-breakout].
Feel free to fork it, modify it and use it.

## Deployment

You can deploy the app using Heroku.
There is a free plan.

[![Deploy](https://www.herokucdn.com/deploy/button.svg)](https://heroku.com/deploy)

Heroku uses [gunicorn](http://flask.pocoo.org/docs/dev/deploying/wsgi-standalone/#gunicorn)
to run the server, see the [Procfile](Procfile).


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
  api_version: 1,
  source: "server.com/update_highscore.js", // the source url
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
In case of an error, the result looks like this:
```
{
  api_version: 1,
  source: "server.com/update_highscore.js", // the source url
  error: {
    "type": "Exception" // the error type
    "message" : "an error occurred" // the message of the error
    "traceback": "file ... line ... " // a multiline message with the error
  }
}
```

[prime-breakout]: https://niccokunzmann.gitlab.io/prime-breakout/
