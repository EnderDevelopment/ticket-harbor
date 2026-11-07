import os
import re

import discord
from discord import app_commands
from discord.ext import commands
from dotenv import load_dotenv

load_dotenv()

TOKEN = os.getenv("DISCORD_TOKEN", "")
TICKET_CATEGORY_ID = int(os.getenv("TICKET_CATEGORY_ID", "0"))
SUPPORT_ROLE_ID = int(os.getenv("SUPPORT_ROLE_ID", "0"))

intents = discord.Intents.default()


def ticket_owner_id(channel: discord.TextChannel) -> int | None:
    match = re.search(r"ticket-owner:(\d+)", channel.topic or "")
    return int(match.group(1)) if match else None


def is_support(member: discord.Member) -> bool:
    return member.guild_permissions.manage_channels or (
        SUPPORT_ROLE_ID != 0
        and any(role.id == SUPPORT_ROLE_ID for role in member.roles)
    )


class TicketReasonModal(discord.ui.Modal, title="Open a support ticket"):
    reason = discord.ui.TextInput(
        label="How can we help?",
        placeholder="Describe your issue or question",
        style=discord.TextStyle.paragraph,
        min_length=5,
        max_length=1000,
    )

    async def on_submit(self, interaction: discord.Interaction) -> None:
        if interaction.guild is None or not isinstance(interaction.user, discord.Member):
            await interaction.response.send_message("Tickets can only be opened in a server.", ephemeral=True)
            return

        await interaction.response.defer(ephemeral=True)
        guild = interaction.guild
        for channel in guild.text_channels:
            if ticket_owner_id(channel) == interaction.user.id:
                await interaction.followup.send(
                    f"You already have an open ticket: {channel.mention}", ephemeral=True
                )
                return

        category = guild.get_channel(TICKET_CATEGORY_ID) if TICKET_CATEGORY_ID else None
        if category is not None and not isinstance(category, discord.CategoryChannel):
            category = None

        overwrites: dict[discord.Role | discord.Member, discord.PermissionOverwrite] = {
            guild.default_role: discord.PermissionOverwrite(view_channel=False),
            interaction.user: discord.PermissionOverwrite(
                view_channel=True, send_messages=True, read_message_history=True
            ),
        }
        support_role = guild.get_role(SUPPORT_ROLE_ID) if SUPPORT_ROLE_ID else None
        if support_role:
            overwrites[support_role] = discord.PermissionOverwrite(
                view_channel=True, send_messages=True, read_message_history=True
            )

        safe_name = re.sub(r"[^a-z0-9-]+", "-", interaction.user.name.lower()).strip("-")
        channel = await guild.create_text_channel(
            name=f"ticket-{safe_name[:70] or interaction.user.id}",
            category=category,
            overwrites=overwrites,
            topic=f"ticket-owner:{interaction.user.id}",
            reason=f"Support ticket opened by {interaction.user} ({interaction.user.id})",
        )
        await channel.send(
            f"{interaction.user.mention} Thanks for contacting support.\n"
            f"**Issue:** {self.reason.value}",
            view=TicketControls(),
        )
        await interaction.followup.send(
            f"Your ticket is ready: {channel.mention}", ephemeral=True
        )


class TicketPanel(discord.ui.View):
    def __init__(self) -> None:
        super().__init__(timeout=None)

    @discord.ui.button(
        label="Create a ticket", style=discord.ButtonStyle.primary,
        emoji="🎫", custom_id="tickets:create",
    )
    async def create_ticket(
        self, interaction: discord.Interaction, button: discord.ui.Button
    ) -> None:
        await interaction.response.send_modal(TicketReasonModal())


class TicketControls(discord.ui.View):
    def __init__(self) -> None:
        super().__init__(timeout=None)

    @discord.ui.button(
        label="Close ticket", style=discord.ButtonStyle.danger,
        emoji="🔒", custom_id="tickets:close",
    )
    async def close_ticket(
        self, interaction: discord.Interaction, button: discord.ui.Button
    ) -> None:
        await self._set_closed(interaction, True)

    @discord.ui.button(
        label="Reopen ticket", style=discord.ButtonStyle.success,
        emoji="🔓", custom_id="tickets:reopen",
    )
    async def reopen_ticket(
        self, interaction: discord.Interaction, button: discord.ui.Button
    ) -> None:
        await self._set_closed(interaction, False)

    async def _set_closed(self, interaction: discord.Interaction, closed: bool) -> None:
        channel = interaction.channel
        if not isinstance(channel, discord.TextChannel) or not isinstance(interaction.user, discord.Member):
            await interaction.response.send_message("This action only works in a ticket channel.", ephemeral=True)
            return
        owner_id = ticket_owner_id(channel)
        if owner_id is None:
            await interaction.response.send_message("This is not a recognized ticket channel.", ephemeral=True)
            return
        if interaction.user.id != owner_id and not is_support(interaction.user):
            await interaction.response.send_message("Only the ticket owner or support staff can do that.", ephemeral=True)
            return

        owner = channel.guild.get_member(owner_id)
        if owner is None:
            try:
                owner = await channel.guild.fetch_member(owner_id)
            except discord.HTTPException:
                owner = None
        if owner is not None:
            await channel.set_permissions(
                owner,
                overwrite=discord.PermissionOverwrite(
                    view_channel=True,
                    send_messages=not closed,
                    read_message_history=True,
                ),
                reason=f"Ticket {'closed' if closed else 'reopened'} by {interaction.user}",
            )
        new_name = channel.name
        if closed and not new_name.startswith("closed-"):
            new_name = f"closed-{new_name}"[:100]
        elif not closed and new_name.startswith("closed-"):
            new_name = new_name[len("closed-"):]
        await channel.edit(name=new_name)
        await interaction.response.send_message(
            f"Ticket {'closed' if closed else 'reopened'} by {interaction.user.mention}.",
            allowed_mentions=discord.AllowedMentions(users=True),
        )


class TicketBot(commands.Bot):
    async def setup_hook(self) -> None:
        self.add_view(TicketPanel())
        self.add_view(TicketControls())
        await self.tree.sync()


bot = TicketBot(command_prefix="!", intents=intents)


@bot.tree.command(name="ticketpanel", description="Post the ticket creation panel")
@app_commands.checks.has_permissions(manage_guild=True)
async def ticketpanel(interaction: discord.Interaction) -> None:
    embed = discord.Embed(
        title="Support tickets",
        description="Click the button below to open a private ticket with the support team.",
        color=discord.Color.blurple(),
    )
    await interaction.channel.send(embed=embed, view=TicketPanel())
    await interaction.response.send_message("Ticket panel posted.", ephemeral=True)


@ticketpanel.error
async def ticketpanel_error(
    interaction: discord.Interaction, error: app_commands.AppCommandError
) -> None:
    if isinstance(error, app_commands.MissingPermissions):
        message = "You need Manage Server permission to post the ticket panel."
    else:
        message = "I could not post the ticket panel. Check my channel permissions and try again."
    if interaction.response.is_done():
        await interaction.followup.send(message, ephemeral=True)
    else:
        await interaction.response.send_message(message, ephemeral=True)


@bot.event
async def on_ready() -> None:
    print(f"Logged in as {bot.user} (ID: {bot.user.id})")


if not TOKEN:
    raise RuntimeError("Set DISCORD_TOKEN in your .env file before starting the bot.")

bot.run(TOKEN)
