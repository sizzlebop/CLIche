"""
LLM interaction commands
"""
import asyncio
import click
from ..core import cli, CLIche

@cli.command()
@click.argument('query', nargs=-1)
def ask(query):
    """Ask CLIche anything"""
    if not query:
        click.echo("Error: No query provided, genius. Please type something!")
        return

    query_str = " ".join(query)
    click.echo("🤔 CLIche is pondering (and judging)...")
    
    assistant = CLIche()
    response = asyncio.run(assistant.ask_llm(f"Respond to this query in plain text format without markdown formatting: {query_str}"))
    click.echo(f"\n💡 {response}")