📚 StudyBot – A Discord Bot to Keep You Focused
StudyBot is a productivity-focused Discord bot that helps users manage study sessions, track progress, and hit their weekly goals—all inside a Discord server. It’s built to keep studying simple, gamified, and consistent.

✨ What StudyBot Can Do
Track Sessions
Use !start to begin a study session and !stop to end it. The bot logs your time and gives you a session summary.

View Stats
Use !stats to see how many sessions you’ve completed, how much time you’ve studied in total, and your average session length.

Set Custom Study/Break Durations
Use !set_break <study> <break> to adjust your preferred study and break lengths. Use !my_settings to view your current setup.

Create and Track Weekly Goals
Use !goals <hours> to set a weekly study goal. Use !progress to view your progress toward that goal with a visual progress bar.

Interactive Buttons
When you start a session, a "🛑 Stop Session" button appears so you can easily end your session with a click.

Persistent Logs
StudyBot stores session data using both a JSON file and an SQLite database, so your history is never lost between restarts.

🧠 Commands Overview
!start – Starts a study session timer

!stop – Stops the session and logs your time

!stats – Shows total time, session count, and average duration

!set_break <study> <break> – Customizes your study/break cycle

!my_settings – Shows your current study/break configuration

!goals <hours> – Sets a weekly study goal in hours

!progress – Displays how close you are to meeting your goal

🛠 How It Works (Behind the Scenes)
The bot is built in Python using the discord.py library.

It uses an .env file to securely store the Discord bot token and channel ID.

Study sessions are saved to a session_logs.json file and a sessions.db SQLite database.

User-specific goals and settings are stored in the database.

Each command is asynchronous and uses Discord embeds for clean messages.

🔒 Safety and Best Practices
Secrets like BOT_TOKEN and CHANNEL_ID are stored in a .env file and never committed to version control.

Database actions are wrapped in helper functions to ensure easy maintenance and future error handling.

🚀 Future Features
!chart command that generates pie or bar charts of weekly time

XP and streak tracking system with !rank to gamify studying

Daily reminder DMs if a user hasn’t studied by 7pm

Flask-based dashboard to view session history visually

CSV export option for all study sessions

🙋‍♂️ About the Project
This bot was created as a personal productivity tool and learning project. It combines technical skill building with a passion for self-discipline and student success.

Built by Dawit Bonga – a student developer, first-gen college student, and productivity nerd.