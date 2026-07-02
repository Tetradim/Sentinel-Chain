from __future__ import annotations

import os

import discord
from discord import app_commands

from .engine import TradingEngine
from .signals import SignalValidationError, normalize_signal


def build_discord_client(engine: TradingEngine | None = None) -> discord.Client:
    """Create a minimal Discord control client.

    The bot uses slash commands instead of arbitrary message parsing by default,
    which avoids requiring privileged message-content access for the MVP.
    """

    intents = discord.Intents.default()
    client = discord.Client(intents=intents)
    tree = app_commands.CommandTree(client)
    trading_engine = engine or TradingEngine()

    @tree.command(name="health", description="Show Sentinel Chain health and paper-order count.")
    async def health(interaction: discord.Interaction) -> None:
        await interaction.response.send_message(
            f"Sentinel Chain online. Paper orders: {len(trading_engine.exchange.orders)}",
            ephemeral=True,
        )

    @tree.command(name="signal_test", description="Validate and paper-trade a crypto signal.")
    async def signal_test(
        interaction: discord.Interaction,
        symbol: str,
        side: str,
        quote_amount: str,
        price: str,
        stop_loss_pct: str,
        take_profit_pct: str = "",
    ) -> None:
        payload = {
            "symbol": symbol,
            "side": side,
            "quote_amount": quote_amount,
            "price": price,
            "stop_loss_pct": stop_loss_pct,
            "take_profit_pct": take_profit_pct,
        }
        try:
            signal = normalize_signal(payload, source="discord")
            result = trading_engine.process_signal(signal)
        except SignalValidationError as exc:
            await interaction.response.send_message(f"Rejected: {exc}", ephemeral=True)
            return
        await interaction.response.send_message(
            f"Status: {result.status} | Symbol: {signal.symbol} | Mode: paper",
            ephemeral=True,
        )

    @client.event
    async def on_ready() -> None:
        await tree.sync()

    return client


def run_from_env() -> None:
    token = os.getenv("DISCORD_BOT_TOKEN")
    if not token:
        raise RuntimeError("DISCORD_BOT_TOKEN is required")
    build_discord_client().run(token)

