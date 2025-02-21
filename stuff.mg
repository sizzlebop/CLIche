CLIche: Turn your terminal into a wise-cracking genius with a snarky, all-knowing LLM assistant

Overview:
  This project turns your terminal into a genius-level oracle that responds
  to your command line queries. Just type your question, and this bad boy will spit out the wisdom you crave.
  Example:
$ cliche "How do I make a virtual environment in Python?" 

Features:
  - Intuitive CLI with Click
  - Plug-and-play integration with an LLM (API or local)
  - Witty error messages, snarky remarks, and one-liners (because life’s too short for boring outputs)
  - "cliche ansi" Generates a random ansi image on command
  - Starts apps on command
  - Gives system information on command
  - Can list servers running and kill processes on command
  - "cliche roastme" for a quick jab to the ego
  - Easy configuration for API keys and/or host urls and model settings
  - editable config file for personalized responses

Notes:
  - Write a function that sends query to the API (e.g., OpenAI’s endpoint) and handles responses.
  - Manage API keys securely (env variables, config files, etc.).
  - Integrate with a local model runner (like llama.cpp) by either calling a subprocess or using a Python binding.