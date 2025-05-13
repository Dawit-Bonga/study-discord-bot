from discord.ext import commands, tasks
import datetime
import discord
from dataclasses import dataclass
import sqlite3
import time
from discord.ui import View, Button
import json
import os
from dotenv import load_dotenv
from functools import lru_cache
import asyncio



load_dotenv()

BOT_TOKEN = os.getenv("BOT_TOKEN")
CHANNEL_ID = int(os.getenv("CHANNEL_ID"))





MAX_SESSION_TIME = 30
active_tasks = {}

SESSION_LOG_FILE = "session_logs.json"


if os.path.exists(SESSION_LOG_FILE):
    with open(SESSION_LOG_FILE, "r") as f:
        session_logs = json.load(f)
        # convert string keys back to ints, and timestamps back to floats
        session_logs = {
            int(k): [(float(s), float(e)) for s, e in v]
            for k, v in session_logs.items()
        }
else:
    session_logs = {}



async def run_study_session(ctx, user_id, study_minutes, break_minutes):
    try:
        while True:
            # Study session
            await ctx.send(f"<@{user_id}> 📚 Study for {study_minutes} minutes now.")
            await asyncio.sleep(study_minutes * 60)

            # Break time
            await ctx.send(f"<@{user_id}> 🧘 Time for a {break_minutes}-minute break!")
            await asyncio.sleep(break_minutes * 60)

    except asyncio.CancelledError:
        await ctx.send(f"<@{user_id}> 🛑 Your study/break cycle has been stopped.")


class StopButtonView(View):
    def __init__(self, timeout=None):
        super().__init__(timeout=timeout)

    @discord.ui.button(label="🛑 Stop Session", style=discord.ButtonStyle.red)
    async def stop_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        user_id = interaction.user.id

        if get_last_start_time(user_id) is None:
            await interaction.response.send_message("No active session to stop.", ephemeral=True)
            return

        session_length = interaction.created_at.timestamp() - get_last_start_time(user_id)
        stop_session(user_id)  # Assuming you have a function for this
        human_readable_duration = str(datetime.timedelta(seconds=session_length))

        embed = discord.Embed(
            title="⏹️ Study Session Ended",
            description=f"<@{user_id}> your session has ended.",
            color=discord.Color.red()
        )
        embed.add_field(name="Duration", value=human_readable_duration, inline=False)
        embed.set_footer(text="Good job today!")
        embed.timestamp = interaction.created_at

        await interaction.response.send_message(embed=embed)

def start_sessions(user_id):
    conn = sqlite3.connect("sessions.db")
    cursor = conn.cursor()

    start = time.time()
    cursor.execute(
        "INSERT INTO study_sessions (user_id, start_time) VALUES (?,?)",
        (user_id, start)
    )

    conn.commit()
    conn.close()


def stop_session(user_id):
    conn = sqlite3.connect("sessions.db")
    cursor = conn.cursor()

    stop = time.time()
    cursor.execute(
        "UPDATE study_sessions SET end_time = ? WHERE user_id = ? AND end_time IS NULL",
        (stop, user_id)
    )

    conn.commit()
    conn.close()

    return stop 

def get_last_start_time(user_id):
    conn = sqlite3.connect("sessions.db")
    cursor = conn.cursor()

    cursor.execute(
        "SELECT start_time FROM study_sessions WHERE user_id = ? and end_time is NULL ORDER BY start_time DESC LIMIT 1",
        (user_id,)
    )

    row = cursor.fetchone()
    conn.close()
    
    return row[0] if row else None

def set_user_settings(user_id, study_minutes, break_minutes):
    conn = sqlite3.connect("sessions.db")
    cursor = conn.cursor()

    cursor.execute('''
        INSERT INTO user_settings (user_id, study_minutes, break_minutes)
        VALUES (?, ? , ?)
        on CONFLICT(user_id) DO UPDATE SET
        study_minutes = excluded.study_minutes,
        break_minutes = excluded.break_minutes
''',(user_id, study_minutes, break_minutes)
    )

    conn.commit()
    conn.close()

@lru_cache(maxsize=128)
def get_user_settings(user_id):
    conn = sqlite3.connect("sessions.db")
    cursor = conn.cursor()

    cursor.execute(
        "SELECT study_minutes, break_minutes FROM user_settings WHERE user_id = ?",
        (user_id,)
    )

    row = cursor.fetchone()
    conn.close()

    if row:
        return row[0], row[1]
    else:
        return 25, 5


def set_goal(user_id, num_of_hours):
    conn = sqlite3.connect("sessions.db")
    cursor = conn.cursor()

    weekly_goal_seconds = num_of_hours * 3600
    now = int(time.time())

    cursor.execute('''
        INSERT INTO study_goals (user_id, weekly_goal, weekly_start)
        VALUES (?, ?, ?)
        on CONFLICT(user_id) DO UPDATE SET
        weekly_goal = excluded.weekly_goal,
        weekly_start = excluded.weekly_start
        ''', (user_id, weekly_goal_seconds, now)
    )

    conn.commit()
    conn.close()


def get_goal_progress(user_id):
    conn = sqlite3.connect("sessions.db")
    cursor = conn.cursor()

    cursor.execute("SELECT weekly_goal, weekly_start FROM study_goals WHERE user_id = ?", (user_id,))

    row = cursor.fetchone()

    if not row:
        conn.close()
        return None, None, None  # No goal set
    
    weekly_goal = row[0]
    weekly_start = row[1]

    cursor.execute(
        '''
        SELECT start_time, end_time from study_sessions
        WHERE user_id = ? AND start_time >= ? AND end_time IS NOT NULL

''', (user_id, weekly_start)
    )

    total_time = sum(end - start for start, end in cursor.fetchall())

    conn.close()


    return weekly_goal, total_time, weekly_start







bot = commands.Bot(command_prefix='!', intents=discord.Intents.all())
# session = {} #key = player_id, value: Sessions INstance


@bot.event
async def on_ready():
    # print("Hello! Studyi can Bot is on and ready to help!")
    channel = bot.get_channel(CHANNEL_ID)
    if channel:
        await channel.send(
            "**📚 Study Bot is online!**\n\n"
            "Here are the available commands:\n"
            "• `!start` – Start a study session and timer\n"
            "• `!stop` – End your session and get the total time\n"
            "• `!stats` – View your study session history\n"
            "• `!my_settings` – View your current study/break preferences\n"
            "• `!set_break <study> <break>` – Set your preferred durations (in minutes)\n"
            "• `!goals <hours>` – Set a weekly study goal\n"
            "• `!progress` – Track your progress toward your weekly goal 📊\n"
            "\n"
            "**Example:** `!set_break 25 5` → 25 min study, 5 min break\n"
            "Stay focused and good luck! 💪"
        )

# @tasks.loop(minutes=MAX_SESSION_TIME, count=2)
# async def break_reminder():
#     #ignore the first current count
#     if break_reminder.current_loop == 0:
#         return

#     channel = bot.get_channel(CHANNEL_ID)
#     await channel.send(f"Take a break! You've been studying for {MAX_SESSION_TIME} minutes")


@bot.command()
async def start(ctx):
    user_id = ctx.author.id

    if get_last_start_time(user_id) is not None or user_id in active_tasks:
        await ctx.send("A session is already active.")
        return

    study_minutes, break_minutes = get_user_settings(user_id)
    start_sessions(user_id)

    embed = discord.Embed(
        title="📚 Study Session Started",
        description=f"<@{user_id}>, your session has begun!",
        color=discord.Color.green()
    )
    embed.add_field(name="Study Time", value=f"{study_minutes} min", inline=True)
    embed.add_field(name="Break Time", value=f"{break_minutes} min", inline=True)
    embed.set_footer(text="Focus up 💪")
    embed.timestamp = ctx.message.created_at

    await ctx.send(embed=embed, view=StopButtonView())

    task = asyncio.create_task(run_study_session(ctx, user_id, study_minutes, break_minutes))
    active_tasks[user_id] = task




@bot.command()
async def stop(ctx):
    user_id = ctx.author.id

    start_time = get_last_start_time(user_id)
    if start_time is None:
        await ctx.send("There is no active sessions right now")
        return
    
    # if break_reminder.is_running():
    #     break_reminder.stop()
    
    end_time = stop_session(user_id)
    session_length = end_time - start_time
    human_readable_duration = str(datetime.timedelta(seconds=session_length))

    if user_id not in session_logs:
        session_logs[user_id] = []

    session_logs[user_id].append((start_time, end_time))

    with open(SESSION_LOG_FILE, "w") as f:
        json.dump(session_logs, f)

    embed = discord.Embed(
        title="📚 Study Sessions Ended",
        description=f"<@{user_id}>, your session is now concluded.",
        color=discord.Color.red()
    )
    embed.add_field(name="Duration", value=human_readable_duration, inline=False)
    embed.add_field(name="Status", value="🔴 Done", inline=True)
    embed.set_footer(text="Good Job 💪")
    embed.timestamp = ctx.message.created_at

    if user_id in active_tasks:
        active_tasks[user_id].cancel()
        del active_tasks[user_id]


    await ctx.send(embed=embed)


@bot.command()
async def set_break(ctx, study_minutes: int, break_minutes: int):
    user_id = ctx.author.id

    if study_minutes < 5 or break_minutes < 1 or study_minutes < break_minutes:
        await ctx.send("Please be reasonable with your times so 20 min studying, 5 min break , etc")
    
    set_user_settings(user_id, study_minutes, break_minutes)
    await ctx.send(f"<@{user_id}> your settings have been saved: {study_minutes} min study/ {break_minutes} min break.")



@bot.command()
async def my_settings(ctx):
    user_id = ctx.author.id

    study_minutes, break_minutes = get_user_settings(user_id)

    await ctx.send(
        f"<@{user_id}> Your current settings: \n"
        f"• Study time: {study_minutes} minutes\n"
        f"• Break time: {break_minutes} minutes\n"
    )


@bot.command()
async def stats(ctx):
    user_id = ctx.author.id
    if user_id not in session_logs or not session_logs[user_id]:
        await ctx.send("No session history found.")
        return
    
    sessions = session_logs[user_id]
    total_time = sum(end - start for start, end in sessions)
    session_count = len(sessions)
    average_time = total_time / session_count

    embed = discord.Embed(
        title="📈 Your Study Stats",
        description=f"<@{user_id}>'s session summary",
        color=discord.Color.blurple()
    )
    embed.add_field(name="Total Sessions", value=str(session_count), inline=False)
    embed.add_field(name="Total Time", value=str(datetime.timedelta(seconds=int(total_time))), inline=False)
    embed.add_field(name="Average Session", value=str(datetime.timedelta(seconds=int(average_time))), inline=False)

    await ctx.send(embed=embed)


@bot.command()
async def goals(ctx, hours: int):
    user_id = ctx.author.id

    if hours < 1 or hours > 100:
        await ctx.send("Please pick hours between 1 and 100")
        return
    
    set_goal(user_id, hours)
    await ctx.send(f"🎯 Goal set! You're aiming to study {hours} hours this week. Let's go!")



@bot.command()
async def progress(ctx):
    user_id = ctx.author.id

    goal, total, _ = get_goal_progress(user_id)

    if goal is None:
        await ctx.send("You haven't set a goal yet. Please set a goal and refer back to this!")
        return
    
    percent = round((total / goal) * 100, 1)
    hours_done = round(total / 3600, 2)
    hours_goal = round(goal / 3600, 2)

    blocks = int(percent // 10)
    progress_bar = "▮" * blocks + "▯" * (10 - blocks)

    await ctx.send(
        f"📊 **Goal Progress** for <@{user_id}>:\n"
        f"`{progress_bar}` {percent}%\n"
        f"🕒 {hours_done} / {hours_goal} hours studied this week."
    )













bot.run(BOT_TOKEN)

