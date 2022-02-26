import discord
import os
from discord.ext import commands, tasks
import discord.client
import random
import json
import keep_alive
from PIL import Image
from itertools import cycle
##from discord_slash import SlashCommand
from discord_buttons_plugin import Button, ButtonType 
import DiscordUtils
from discord_components import DiscordComponents
from io import BytesIO


def get_prefix(client, message):  #Saves the prefixes on the JSON file
    with open('prefixes.json', 'r') as f:
        prefixes = json.load(f)

    return prefixes[str(message.guild.id)]


intents = discord.Intents().all()
client = commands.Bot(command_prefix=get_prefix, intents=intents)
music = DiscordUtils.Music()
#ddb = DiscordButton(client)

status = cycle(['Watching Youtube', 'Watching a movie', 'Having fun', '$help'])


@tasks.loop(seconds=15)
async def status_swap():
    await client.change_presence(activity=discord.Game(next(status)))


@client.event  #Shows the bot is up and running
async def on_ready():
    print('Monster is online')
    status_swap.start()
    DiscordComponents(client)


@client.event
async def on_guild_join(guild):
    with open('prefixes.json', 'r') as f:
        prefixes = json.load(f)

    prefixes[str(guild.id)] = '$'

    with open('prefixes.json', 'w') as f:
        json.dump(prefixes, f, indent=4)


@client.event
async def on_member_join(member):  #Welcome message and updating on users.json
    welcomeEmbed = discord.Embed(
        title=f"New Member!",
        description=f"{member.name} has joined the server",
        color=discord.Color.blue())
    await client.get_channel(762771362137768006).send(embed=welcomeEmbed)
    with open('users.json', 'r') as f:
        users = json.load(f)

    await update_data(users, member)

    with open('users.json', 'w') as f:
        json.dump(users, f, indent=4)


@client.event
async def on_guild_remove(guild):  #When the bot leaves delete prefixes
    with open('prefixes.json', 'r') as f:
        prefixes = json.load(f)

    prefixes.pop(str(guild.id))

    with open('prefixes.json', 'w') as f:
        json.dump(prefixes, f, indent=4)


@client.event
async def on_message(message):
    if message.author.bot is False:
        with open('users.json', 'r') as f:
            users = json.load(f)

        await update_data(users, message.author)
        await add_experience(users, message.author, 5)
        await level_up(users, message.author, message)
        with open('users.json', 'w') as f:
            json.dump(users, f, indent=4)

    await client.process_commands(message)


##slash = SlashCommand(client, sync_commands=True)

#@slash.slash(description="Showes the bots latency")
#async def ping(ctx):
# await ctx.send(f'Bot Speed - {round(client.latency * 1000)}ms')

#@client.command()
#async def button(ctx):
# m = await ctx.send(

#"Button Command Ran!",
#buttons=[
#Button(style=ButtonStyle.blue, label="Click Me!"),
#Button(style=ButtonStyle.URL, label="Invite!", #url="https://discord.gg/nDkJ5C23Pc")

#],
#)
#res = await ddb.wait_for_button_click(m)
#await res.respond(
#type=InteractionType.ChannelMessageWithSource,
#ontent=f'{res.button.label} has been clicked!'
#)


@client.command()
async def queue(ctx):
    player = music.get_player(guild_id=ctx.guild.id)
    await ctx.send(
        f"{','.join([song.name for song in player.current_queue()])}")


@client.command()
async def pause(ctx):
    player = music.get_player(guild_id=ctx.guild.id)
    song = await player.pause()
    await ctx.send(f'Paused {song.name}')


@client.command()
async def resume(ctx):
    player = music.get_player(guild_id=ctx.guild.id)
    song = await player.resume()
    await ctx.send(f'Resumed {song.name}')


@client.command()
async def button(ctx):
    await ctx.send(
        "This is a Button!",
        components=[Button(style=ButtonType().Primary, label='Click Me!')])
    interaction = await client.wait_for(
        "button_click", check=lambda i: i.component.label.startswith('Click'))
    await interaction.respond(content="Button Clicked!")


@client.command()
async def play(ctx, *, url):
    player = music.get_player(guild_id=ctx.guild.id)
    if not player:
        player = music.create_player(ctx, ffnpeg_error_betterfix=True)
    if not ctx.voice_client.is_playing():
        await player.queue(url, search=True)
        song = await player.play()
        await ctx.send(f'I have started playing {song.name}')
    else:
        song = await player.queue(url, search=True)
        await ctx.send(f'{song.name} has been added to the playlist')


@client.command()
async def join(ctx):
    voicetrue = ctx.author.voice
    if voicetrue is None:
        return await ctx.send('You are not currently in a voice channel')
    await ctx.author.voice.channel.connect()
    await ctx.send('Joined your voice channel')


@client.command()
async def leave(ctx):
    voicetrue = ctx.author.voice
    mevoicetrue = ctx.guild.me.voice
    if voicetrue is None:
        return await ctx.send('You are not currently in a voice channel')
    if mevoicetrue is None:
        return await ctx.send('I am not currently in a voice channel')
    await ctx.voice_client.disconnect()
    await ctx.send('Left your voice channel')


@client.command()
async def level(ctx, member: discord.Member = None):
    if not member:
        id = ctx.message.author.id
        with open('users.json', 'r') as f:
            users = json.load(f)
        level = users[str(id)]['level']
        await ctx.send(f'You are at level {level}!')
    else:
        id = member.id
        with open('users.json', 'r') as f:
            users = json.load(f)
        level = users[str(id)]['level']
        await ctx.send(f'{member} is at level {level}!')


@client.command(aliases=['prefix'])  #Set prefix command
async def setprefix(ctx, prefixset=None):
    if (not ctx.author.guild_permissions.administrator):
        await ctx.send('This command requires administrative role')
        return

    if (prefixset is None):
        prefixset = '$'

    with open('prefixes.json', 'r') as f:
        prefixes = json.load(f)

    prefixes[str(ctx.guild.id)] = prefixset

    with open('prefixes.json', 'w') as f:
        json.dump(prefixes, f, indent=4)

    await ctx.send(f'The bot prefix has been changed to "{prefixset}"')


client.remove_command("help")


@client.command()  #Request help center
async def help(ctx):
    helpEmbed = discord.Embed(title="Help center", color=discord.Color.blue())
    helpEmbed.add_field(name="Moderation Options",
                        value="Ban, Kick, Mute, Unmute, Clear, setprefix")
    helpEmbed.add_field(name="Fun", value="wanted")
    await ctx.send(embed=helpEmbed)


@client.command()  #See the profile picture
async def avatar(ctx, member: discord.Member = None):
    if member is None:
        member = ctx.author
    memberAvatar = member.avatar_url

    avaEmbed = discord.Embed(title=f"{member.name}'s Avatar")
    avaEmbed.set_image(url=memberAvatar)

    await ctx.send(embed=avaEmbed)


@client.command(aliases=['boot'])  # Request Kick
async def kick(ctx, member: discord.Member, *, reason=None):
    if (not ctx.author.guild_permissions.kick_members):
        await ctx.send('This command requires ' 'כריש' '')
        return
    await member.kick(reason=reason)
    await ctx.send(f'{member.mention} has been kicked')


@client.command(aliases=['hammer'])  # Request Ban
async def ban(ctx, member: discord.Member, *, reason=None):
    if (not ctx.author.guild_permissions.ban_members):
        await ctx.send('This command requires ' 'כריש' '')
        return
    await member.ban(reason=reason)
    await ctx.send(f'{member.mention} has been banned')


@client.command(aliases=['forgive'])  # Request ban cancelation
async def unban(ctx, *, member):
    if (not ctx.author.guild_permissions.ban_members):
        await ctx.send('This command requires ' 'כריש' '')
        return
    banned_users = await ctx.guild.bans()
    member_name, member_discriminator = member.split('#')

    for ban_entry in banned_users:
        user = ban_entry.user

        if (user.name, user.discriminator) == (member_name,
                                               member_discriminator):
            await ctx.guild.unban(user)
            await ctx.send(f'Unbanned {user.mention}')
            return


@client.command(aliases=['purge'])  #Delete an amount of messages <100
async def clear(ctx, amount=11):
    if (not ctx.author.guild_permissions.manage_messages):
        await ctx.send('This command requires ' 'כריש' '')
        return
    if amount > 101:
        await ctx.send('Can not delete more than 100 messages')
    else:
        await ctx.channel.purge(limit=amount)
        await ctx.send('Cleared Messages')


@client.command()
async def mute(ctx, member: discord.Member, *, reason=None):  #Mute a member
    if (not ctx.author.guild_permissions.administrator):
        await ctx.send('This command requires an administrative role')
        return
    guild = ctx.guild
    muteRole = discord.utils.get(guild.roles, name="Muted")

    if not muteRole:
        muteRole = await guild.create_role(name="Muted")

        for channel in guild.channels:
            await ctx.send(
                'No mute role has been found. Creating a new role...')
            await channel.set_permissions(muteRole,
                                          speak=False,
                                          send_messages=False,
                                          read_message_history=True,
                                          read_messages=False)

    await member.add_roles(muteRole, reason=reason)
    await ctx.send('User is muted')
    await member.send(
        f"You have been muted from **{guild.name}** | Reason: **{reason}**")


@client.command()  #Slowmode enable and disable
async def slowmode(ctx, time: int):
    if (not ctx.author.guild_permissions.manage_messages):
        await ctx.send('This command requires ' 'כריש' '')
        return
    try:
        if time == 0:
            await ctx.send('Slowmode off')
            await ctx.channel.edit(slowmode_delay=0)
        elif time > 2160:
            await ctx.send('You can not set the slowmode above 6 hours')
            return
        else:
            await ctx.channel.edit(slowmode_delay=time)
            await ctx.send(f'Slowmode set to {time} seconds!')
    except Exception:
        await print('Oops!')


@client.command()
async def serverinfo(ctx):  #Server Info
    role_count = len(ctx.guild.roles)
    list_of_bots = [bot.mention for bot in ctx.guild.members if bot.bot]

    serverInfoEmbed = discord.Embed(timestamp=ctx.message.created_at,
                                    color=ctx.author.color)
    serverInfoEmbed.add_field(name='Name',
                              value=ctx.guild.member_count,
                              inline=False)
    serverInfoEmbed.add_field(name='Member Count',
                              value=f"{ctx.guild.member_count}",
                              inline=False)
    serverInfoEmbed.add_field(name='Verification Level',
                              value=str(ctx.guild.verification_level),
                              inline=False)
    serverInfoEmbed.add_field(name='Highest Role',
                              value=ctx.guild.roles[-2],
                              inline=False)
    serverInfoEmbed.add_field(name='Number of Roles',
                              value=str(role_count),
                              inline=False)
    serverInfoEmbed.add_field(name='Bots',
                              value=','.join(list_of_bots),
                              inline=False)

    await ctx.send(embed=serverInfoEmbed)


@client.command()  #Load the wanted template with the profilepic
async def wanted(ctx, member: discord.Member = None):
    if member is None:
        member = ctx.author
    wanted = Image.open("wanted.jpg")

    asset = member.avatar_url_as(size=128)
    data = BytesIO(await asset.read())
    profilepic = Image.open(data)

    profilepic = profilepic.resize((110, 110))

    wanted.paste(profilepic, (57, 72))

    wanted.save("wantedpic.jpg")

    await ctx.send(file=discord.File("wantedpic.jpg"))

    os.remove("wantedpic.jpg")


@client.command()  #Make the bot say something
async def say(ctx, saymsg=None):
    if saymsg is None:
        return await ctx.send('You must tell me the message to say!')
    await ctx.send(saymsg)
    sayEmbed = discord.Embed(title=f"{ctx.author} Says",
                             description=f"{saymsg}")
    await ctx.send(embed=sayEmbed)


@client.command()
async def unmute(ctx,
                 member: discord.Member,
                 *,
                 reason=None):  #Unmute a member
    if (not ctx.author.guild_permissions.administrator):
        await ctx.send('This command requires an administrative role')
        return
    guild = ctx.guild
    muteRole = discord.utils.get(guild.roles, name="Muted")

    if not muteRole:
        await ctx.send("The muted role has not been found.")
        return

    await member.remove_roles(muteRole, reason=reason)
    await ctx.send('User is unmuted')
    await member.send(
        f"You have been unmuted from **{guild.name}** | Reason: **{reason}**")


async def update_data(users, user):
    if not f'{user.id}' in users:
        users[f'{user.id}'] = {}
        users[f'{user.id}']['experience'] = 0
        users[f'{user.id}']['level'] = 1


async def add_experience(users, user, exp):
    users[f'{user.id}']['experience'] += exp


async def level_up(users, user, message):
    with open('levels.json', 'r') as g:
        levels = json.load(g)
    experience = users[f'{user.id}']['experience']
    level_start = users[f'{user.id}']['level']
    level_end = int(experience**(1 / 4))
    if level_start < level_end:
        await message.channel.send(
            f'{user.mention} has leveled up! **LEVEL - {level_end}')
        users[f'{user.id}']['level'] = level_end


'''''' '''''' '''''' '''''' ''''error handling''' '''''' '''''' ''''''


@kick.error
async def kick_error(ctx, error):
    if isinstance(error, commands.MissingRequiredArgument):
        await ctx.send("Please include a member")
    elif isinstance(error, commands.MemberNotFound):
        await ctx.send("Member is not found")


@ban.error
async def ban_error(ctx, error):
    if isinstance(error, commands.MissingRequiredArgument):
        await ctx.send("Please include a member")
    elif isinstance(error, commands.MemberNotFound):
        await ctx.send("Member is not found")


@mute.error
async def mute_error(ctx, error):
    if isinstance(error, commands.MissingRequiredArgument):
        await ctx.send("Please include a member")
    elif isinstance(error, commands.MemberNotFound):
        await ctx.send("Member is not found")


@unmute.error
async def ummute_error(ctx, error):
    if isinstance(error, commands.MissingRequiredArgument):
        await ctx.send("Please include a member")
    elif isinstance(error, commands.MemberNotFound):
        await ctx.send("Member is not found")


@setprefix.error
async def setprefix_error(ctx, error):
    if isinstance(error, commands.MissingRequiredArgument):
        await ctx.send("Please include a prefix")


keep_alive.keep_alive()
client.run(os.environ['TOKEN'])

#I like your skechers, you like me too, bring yourself all of us in the pool, bad lil bitch all my drip make you drool, I just want to make you mine, hope inside the ride, I promise you it will be Fine. shawty bad with the sketchers on, wann'na hold your hand, make you my girl, light up light up skechers, light up light up my world
