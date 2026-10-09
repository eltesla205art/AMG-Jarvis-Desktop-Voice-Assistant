"""Conversation basics: hello, thanks, help, language switch, goodbye."""

from __future__ import annotations

from . import skill


@skill("hello", en=["hello", "hi", "hey", "good morning", "good evening"],
       fr=["bonjour", "salut", "bonsoir", "coucou"])
def hello(ctx, req):
    ctx.say("hello", user=ctx.user_suffix)


@skill("thanks", en=["thank you", "thanks"], fr=["merci"])
def thanks(ctx, req):
    ctx.say("thanks")


@skill("help",
       en=["help", "what can you do", "commands"],
       fr=["aide", "aide moi", "que sais tu faire", "que peux tu faire", "qu est ce que tu sais faire"])
def help_(ctx, req):
    ctx.say("help")


@skill("speak_english",
       en=["speak english", "english please", "switch to english"],
       fr=["parle anglais", "parle en anglais", "passe en anglais"])
def speak_english(ctx, req):
    ctx.set_language("en")
    ctx.say("language_switched")


@skill("speak_french",
       en=["speak french", "french please", "switch to french"],
       fr=["parle francais", "parle en francais", "passe en francais"])
def speak_french(ctx, req):
    ctx.set_language("fr")
    ctx.say("language_switched")


@skill("bilingual",
       en=["bilingual mode", "detect my language", "detect language", "both languages"],
       fr=["mode bilingue", "detecte ma langue", "deux langues", "les deux langues"])
def bilingual(ctx, req):
    ctx.set_language("auto")
    ctx.say("bilingual_mode")


@skill("goodbye",
       en=["goodbye", "good bye", "bye", "exit", "quit", "go offline", "stop listening", "go to sleep"],
       fr=["au revoir", "quitte", "quitter", "arrete toi", "deconnecte toi", "bonne nuit", "dors"])
def goodbye(ctx, req):
    ctx.say("goodbye", user=ctx.user_suffix)
    ctx.stop()
