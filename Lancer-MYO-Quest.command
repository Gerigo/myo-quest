#!/bin/zsh
APP_DIR=${0:A:h}
cd "$APP_DIR" || exit 1
print 'MYO Quest : ouvrez http://localhost:4173 dans votre navigateur.'
print 'Pour arrêter le serveur : Ctrl+C dans cette fenêtre.'
python3 -m http.server 4173 --directory dist
