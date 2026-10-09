"""Every sentence O.R.I.O.N. says, in English and French.

A value may be a list: one entry is picked at random so replies feel less
robotic. To add a language, add a block with the same keys and register its
speech-recognition locale in ``LOCALES``.
"""

from __future__ import annotations

import random

# Locale codes sent to the speech recognizer.
LOCALES = {"en": "en-US", "fr": "fr-FR"}

LANGUAGE_NAMES = {
    "en": {"en": "English", "fr": "French"},
    "fr": {"en": "anglais", "fr": "français"},
}

STRINGS: dict[str, dict[str, str | list[str]]] = {
    "en": {
        "morning": "Good morning",
        "afternoon": "Good afternoon",
        "evening": "Good evening",
        "night": "Hello, working late",
        "intro": "I'm {name}, your AI voice assistant. How can I help?",
        "hello": ["Hello{user}! What can I do for you?", "Hi{user}, I'm listening."],
        "thanks": ["You're welcome.", "Happy to help.", "Anytime."],
        "listening": "Listening...",
        "thinking": "Thinking...",
        "speaking": "Speaking...",
        "idle": "Ready",
        "not_understood": [
            "Sorry, I didn't understand that. Say \"help\" to hear what I can do.",
            "I'm not sure how to do that yet. Try saying \"help\".",
        ],
        "service_down": "I can't reach the speech recognition service. Please check your internet connection.",
        "no_mic": "No microphone found, so I'll read typed commands instead.",
        "skill_error": "Something went wrong with that request, but I'm still here.",
        "help": (
            "You can ask me the time or the date, to open YouTube, Google or any website, "
            "to search Google or Wikipedia, to play music, to tell a joke, to take a screenshot, "
            "to take a note or read your notes, to speak French, "
            "or to shut down or restart the computer. Say goodbye to stop me."
        ),
        "time": "It's {time}.",
        "date": "Today is {date}.",
        "opening": "Opening {site}.",
        "which_site": "Which website should I open?",
        "browser_failed": "I couldn't open a web browser on this computer.",
        "searching_google": "Here are the Google results for {query}.",
        "searching_youtube": "Here's YouTube for {query}.",
        "what_search": "What should I search for?",
        "wiki_searching": "Searching Wikipedia for {query}...",
        "wiki_what": "What would you like me to look up on Wikipedia?",
        "wiki_none": "I couldn't find anything on Wikipedia about {query}.",
        "wiki_offline": "I couldn't reach Wikipedia. Please check your internet connection.",
        "according_wiki": "According to Wikipedia: {summary}",
        "music_no_dir": "I couldn't find your music folder at {path}.",
        "music_none": "I couldn't find any music files.",
        "music_no_match": "I couldn't find a song matching {query}.",
        "music_playing": "Playing {song}.",
        "music_open_failed": "I found the song but couldn't open a music player.",
        "screenshot_saved": "Screenshot saved in your {folder} folder.",
        "screenshot_failed": "Sorry, I couldn't take a screenshot on this system.",
        "note_what": "What should I write down?",
        "note_saved": "Got it. I've saved your note.",
        "note_cancelled": "I didn't catch anything, so no note was saved.",
        "notes_none": "You don't have any notes yet.",
        "notes_reading": "Here are your latest notes: {notes}",
        "note_failed": "Sorry, I couldn't save your note.",
        "confirm_shutdown": "Are you sure you want me to shut down the computer?",
        "confirm_restart": "Are you sure you want me to restart the computer?",
        "shutting_down": "Shutting down the computer. Goodbye.",
        "restarting": "Restarting the computer. See you soon.",
        "power_cancelled": "Okay, cancelled.",
        "power_failed": "I couldn't do that. You may need administrator permissions.",
        "language_switched": "Okay, I'll speak English. Say \"bilingual mode\" to use both languages again.",
        "bilingual_mode": "Okay, I'll understand both English and French.",
        "goodbye": ["Going offline. Have a great day{user}!", "Goodbye{user}. Orion signing off."],
        "repeat": "Sorry, could you repeat that?",
    },
    "fr": {
        "morning": "Bonjour",
        "afternoon": "Bon après-midi",
        "evening": "Bonsoir",
        "night": "Bonsoir, vous travaillez tard",
        "intro": "Je suis {name}, votre assistant vocal. Comment puis-je vous aider ?",
        "hello": ["Bonjour{user} ! Que puis-je faire pour vous ?", "Salut{user}, je vous écoute."],
        "thanks": ["Je vous en prie.", "Avec plaisir.", "De rien."],
        "listening": "À l'écoute...",
        "thinking": "Réflexion...",
        "speaking": "Je parle...",
        "idle": "Prêt",
        "not_understood": [
            "Désolé, je n'ai pas compris. Dites « aide » pour savoir ce que je peux faire.",
            "Je ne sais pas encore faire ça. Essayez de dire « aide ».",
        ],
        "service_down": "Je n'arrive pas à joindre le service de reconnaissance vocale. Vérifiez votre connexion internet.",
        "no_mic": "Aucun micro détecté, je vais donc lire les commandes tapées au clavier.",
        "skill_error": "Un problème est survenu avec cette demande, mais je suis toujours là.",
        "help": (
            "Vous pouvez me demander l'heure ou la date, d'ouvrir YouTube, Google ou n'importe quel site, "
            "de chercher sur Google ou Wikipédia, de jouer de la musique, de raconter une blague, "
            "de faire une capture d'écran, de prendre une note ou de lire vos notes, de parler anglais, "
            "ou d'éteindre ou redémarrer l'ordinateur. Dites au revoir pour m'arrêter."
        ),
        "time": "Il est {time}.",
        "date": "Nous sommes le {date}.",
        "opening": "J'ouvre {site}.",
        "which_site": "Quel site dois-je ouvrir ?",
        "browser_failed": "Je n'ai pas pu ouvrir de navigateur sur cet ordinateur.",
        "searching_google": "Voici les résultats Google pour {query}.",
        "searching_youtube": "Voici YouTube pour {query}.",
        "what_search": "Que dois-je chercher ?",
        "wiki_searching": "Je cherche {query} sur Wikipédia...",
        "wiki_what": "Que voulez-vous que je cherche sur Wikipédia ?",
        "wiki_none": "Je n'ai rien trouvé sur Wikipédia à propos de {query}.",
        "wiki_offline": "Je n'arrive pas à joindre Wikipédia. Vérifiez votre connexion internet.",
        "according_wiki": "D'après Wikipédia : {summary}",
        "music_no_dir": "Je ne trouve pas votre dossier de musique : {path}.",
        "music_none": "Je n'ai trouvé aucun fichier de musique.",
        "music_no_match": "Je n'ai trouvé aucune chanson correspondant à {query}.",
        "music_playing": "Lecture de {song}.",
        "music_open_failed": "J'ai trouvé la chanson, mais je n'ai pas pu ouvrir de lecteur.",
        "screenshot_saved": "Capture d'écran enregistrée dans votre dossier {folder}.",
        "screenshot_failed": "Désolé, je n'ai pas pu faire de capture d'écran sur ce système.",
        "note_what": "Que dois-je noter ?",
        "note_saved": "C'est noté.",
        "note_cancelled": "Je n'ai rien entendu, aucune note n'a été enregistrée.",
        "notes_none": "Vous n'avez encore aucune note.",
        "notes_reading": "Voici vos dernières notes : {notes}",
        "note_failed": "Désolé, je n'ai pas pu enregistrer votre note.",
        "confirm_shutdown": "Voulez-vous vraiment que j'éteigne l'ordinateur ?",
        "confirm_restart": "Voulez-vous vraiment que je redémarre l'ordinateur ?",
        "shutting_down": "J'éteins l'ordinateur. Au revoir.",
        "restarting": "Je redémarre l'ordinateur. À tout de suite.",
        "power_cancelled": "D'accord, j'annule.",
        "power_failed": "Je n'ai pas pu le faire. Il faut peut-être des droits administrateur.",
        "language_switched": "D'accord, je parle français. Dites « mode bilingue » pour utiliser les deux langues.",
        "bilingual_mode": "D'accord, je comprends l'anglais et le français.",
        "goodbye": ["Je passe hors ligne. Bonne journée{user} !", "Au revoir{user}. Orion se déconnecte."],
        "repeat": "Pardon, pouvez-vous répéter ?",
    },
}

MONTHS = {
    "en": ["January", "February", "March", "April", "May", "June", "July",
           "August", "September", "October", "November", "December"],
    "fr": ["janvier", "février", "mars", "avril", "mai", "juin", "juillet",
           "août", "septembre", "octobre", "novembre", "décembre"],
}
WEEKDAYS = {
    "en": ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"],
    "fr": ["lundi", "mardi", "mercredi", "jeudi", "vendredi", "samedi", "dimanche"],
}


def t(key: str, lang: str, **kwargs: object) -> str:
    """Translate ``key`` into ``lang`` (falling back to English)."""
    value = STRINGS.get(lang, {}).get(key) or STRINGS["en"][key]
    if isinstance(value, list):
        value = random.choice(value)
    return value.format(**kwargs) if kwargs else value
