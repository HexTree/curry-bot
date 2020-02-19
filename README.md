# curry-bot
Discord bot for the Azure Dreams community

Steps to get this up and running locally:

1) Clone git project

2) Copy the Bot token from Discordapp developers page, and paste it into a JSON file called "creds.json" in the discord_tools folder. Should look like:

{
  "token" : "..."
}

3) Create a new Service Account key from Google Cloud Platform for your spreadsheet. Save as "creds.json" in Bingo folder.

After downloading all requirements listed in requirements.py, the bot should now run when executing curry_bot.py
