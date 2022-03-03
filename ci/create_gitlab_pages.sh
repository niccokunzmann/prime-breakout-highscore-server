#!/bin/bash

cd "`dirname \"$0\"`"
cd ..

mkdir -p pages

cp highscore.json pages
(
  echo "/* generated with GitLab CI */"
  echo "/* `date` */"
  echo "update_highscore("
  cat highscore.json
  echo ");"
) > pages/update_highscore.js
