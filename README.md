# Discord Ticket Bot

TicketHarbor is a Discord support-ticket bot built with discord.py that creates private ticket channels, collects issue descriptions through a modal, restricts access to the ticket owner and support staff, and supports closing and reopening tickets with persistent buttons.

## Install

1. Create a Discord application and bot in the Discord Developer Portal.
2. Invite the bot with the `bot` and `applications.commands` scopes.
3. Grant the bot these permissions:
   - View Channels
   - Send Messages
   - Embed Links
   - Read Message History
   - Manage Channels
   - Manage Roles
4. Copy `.env.example` to `.env`.
5. Configure the environment variables:

```env
DISCORD_TOKEN=your_bot_token_here
TICKET_CATEGORY_ID=0
SUPPORT_ROLE_ID=0
```

6. Set `TICKET_CATEGORY_ID` to the Discord category ID where new tickets should be created. Leave it as `0` to create tickets without a category.
7. Set `SUPPORT_ROLE_ID` to the support team's role ID. Leave it as `0` if support staff will be identified through the Manage Channels permission.
8. Install the dependencies:

```bash
python -m pip install -r requirements.txt
```

## Use

1. Start the bot:

```bash
python main.py
```

2. In your Discord server, run `/ticketpanel` in the channel where users should open tickets. The person using the command must have Manage Server permission.
3. Users select Create a ticket and submit an issue description of 5 to 1,000 characters.
4. The bot creates a private text channel for the user and configured support role.
5. Use the Close ticket button to prevent the ticket owner from sending messages and add the `closed-` prefix to the channel name.
6. Use the Reopen ticket button to restore the owner's ability to send messages and remove the prefix.
7. Ticket controls continue working after bot restarts because the bot registers persistent Discord component views.

The bot allows each user to have one open ticket at a time. Ticket ownership is recorded in the channel topic.

---

More Discord bot projects by EnderDevelopment: https://github.com/EnderDevelopment

Project page: https://dash.enderdevelopment.com/community/683147a4-8d09-4783-ae9b-27673683e393?utm_source=github&utm_medium=readme&utm_campaign=auto_publish&utm_content=683147a4-8d09-4783-ae9b-27673683e393
