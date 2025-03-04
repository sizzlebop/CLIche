"""
Command helper utilities for creating consistent command patterns across CLIche.

This module provides helper functions and decorators to standardize the way
commands are implemented throughout the application, particularly for implementing
the dual command pattern (flag-based and subcommand-based).
"""
import click
import functools
from typing import Callable, Dict, List, Any, Optional, Union


def create_dual_command(name: str, help_text: str, 
                       options: Dict[str, Dict[str, Any]],
                       command_functions: Dict[str, Callable]) -> click.Group:
    """
    Create a command that supports both flag-based and subcommand-based invocation.
    
    This helper creates a Click command group where each operation can be invoked
    either via a flag (--option) or as a subcommand (option).
    
    Args:
        name: The name of the command
        help_text: The help text for the command
        options: Dictionary mapping option names to their Click option configurations
        command_functions: Dictionary mapping option names to their implementation functions
    
    Returns:
        A Click group command with the dual invocation pattern implemented
    
    Example:
        ```python
        # Define command functions
        def show_items():
            click.echo("Showing items")
            
        def create_item():
            click.echo("Creating item")
        
        # Define options
        options = {
            "show": {"is_flag": True, "help": "Show all items"},
            "create": {"is_flag": True, "help": "Create a new item"}
        }
        
        # Create the dual command
        dual_cmd = create_dual_command(
            name="items",
            help_text="Manage your items",
            options=options,
            command_functions={"show": show_items, "create": create_item}
        )
        
        # Register with your CLI
        cli.add_command(dual_cmd)
        ```
    """
    @click.group(name=name, help=help_text, invoke_without_command=True)
    @click.pass_context
    def command_group(ctx, **kwargs):
        # Handle flag-based invocation
        for option_name, func in command_functions.items():
            if option_name in kwargs and kwargs[option_name]:
                func()
                return
        
        # If no flags used and no subcommand, show help
        if ctx.invoked_subcommand is None:
            click.echo(ctx.get_help())
    
    # Add options to the command group
    for option_name, option_config in options.items():
        param_decls = [f"--{option_name}"]
        command_group = click.option(*param_decls, **option_config)(command_group)
    
    # Add subcommands
    for option_name, func in command_functions.items():
        # Skip special options that shouldn't be subcommands
        if option_name.startswith('_'):
            continue
            
        @command_group.command(name=option_name, help=options[option_name].get("help", ""))
        @functools.wraps(func)
        def command_wrapper(*args, **kwargs):
            func()
    
    return command_group


def dual_command(name: str, help_text: str):
    """
    Decorator for creating a dual command (flag-based and subcommand-based).
    
    This is a more decorator-friendly approach to creating dual commands.
    
    Example:
        ```python
        @dual_command("items", "Manage your items")
        class ItemCommands:
            @option("--show", is_flag=True, help="Show all items")
            def show(self):
                click.echo("Showing items")
                
            @option("--create", is_flag=True, help="Create a new item")
            def create(self):
                click.echo("Creating item")
        
        # Register with your CLI
        cli.add_command(ItemCommands)
        ```
    """
    def decorator(cls):
        options = {}
        command_functions = {}
        
        for attr_name in dir(cls):
            if attr_name.startswith('_'):
                continue
                
            attr = getattr(cls, attr_name)
            if callable(attr) and hasattr(attr, '_click_option'):
                options[attr_name] = attr._click_option
                command_functions[attr_name] = attr
        
        return create_dual_command(name, help_text, options, command_functions)
    
    return decorator


def option(*param_decls, **attrs):
    """
    Decorator for marking methods for dual command pattern.
    
    This decorates methods in a class used with @dual_command.
    """
    def decorator(f):
        f._click_option = attrs
        return f
    
    return decorator 