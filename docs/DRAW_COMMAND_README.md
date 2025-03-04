# CLIche Draw Command

## Overview

The `draw` command in CLIche provides an interactive terminal-based ASCII and ANSI art editor. Powered by Durdraw, it gives you a powerful yet intuitive interface for creating text-based art directly from your terminal.

> **Note**: Installation of the draw command requires sudo privileges. Make sure to run the installation script with sudo: `sudo ./install.sh`

```
cliche draw
```

![Durdraw Editor Screenshot](https://github.com/user-attachments/assets/3bdb0c46-7f21-4514-9b48-ac00ca62e68e)

## Features

- Full-featured terminal-based ASCII and ANSI art editor
- 256 color and 16 color modes
- Block selection and manipulation tools
- Line and box drawing tools
- Animation capabilities with frame-by-frame editing
- Copy/paste functionality
- Multiple brush and character set options
- Export to various formats

## Basic Usage

```bash
# Start the drawing editor with default settings
cliche draw

# Start with ASCII mode (text characters)
cliche draw --ascii

# Start with ANSI mode (colored blocks)
cliche draw --ansi

# Set custom canvas size
cliche draw -w 100 -h 40
```

## Command Options

| Option | Description |
|--------|-------------|
| `--width`, `-w` | Set canvas width (default: 80) |
| `--height`, `-h` | Set canvas height (default: 24) |
| `--output`, `-o` | Output file path |
| `--ascii`, `-a` | Use ASCII art mode (text characters) |
| `--ansi`, `-n` | Use ANSI art mode (colored blocks) |

## Drawing Modes

### ASCII Art Mode (--ascii)

Uses text characters like `#@*+` for simple text art. This mode is perfect for:
- Creating art that works in any terminal
- Simple logos and text banners
- Art that needs to be shared in plain text

### ANSI Art Mode (--ansi)

Uses colored block characters (`█▓▒░`) with up to 256 colors for detailed pixel art. This mode is ideal for:
- Creating colorful, detailed images
- Pixel art style drawings
- More visually complex compositions

## Keyboard Shortcuts

### Art Editing

| Key | Function |
|-----|----------|
| F1-F10 | Insert character |
| esc-1 to esc-0 | Same as F1-F10 |
| esc-space | Insert draw character |
| esc-c / tab | Color picker |
| esc-left | Next foreground color |
| esc-right | Previous foreground color |
| esc-up | Change color up |
| esc-down | Change color down |
| esc-/ | Insert line |
| esc-' | Delete line |
| esc-. | Insert column |
| esc-, | Delete column |
| esc-] | Next character group |
| esc-[ | Previous character group |
| esc-S | Change character set |
| esc-L | Replace color |
| esc-y | Eyedrop (pick up color) |
| esc-P | Pick up character |
| esc-l | Color character |
| shift-arrows | Select for copy |
| esc-K | Mark selection |
| esc-v | Paste |

### Animation Controls

| Key | Function |
|-----|----------|
| esc-k | Next frame |
| esc-j | Previous frame |
| esc-p | Start/stop playback |
| esc-n | Clone frame |
| esc-N | Append empty frame |
| esc-d | Delete frame |
| esc-D | Set frame delay |
| esc-+ / esc-- | Faster/slower |
| esc-R | Set playback/edit range |
| esc-g | Go to frame # |
| esc-M | Move frame |
| esc-{ | Shift frames left |
| esc-} | Shift frames right |

### UI/Misc

| Key | Function |
|-----|----------|
| esc-m | Main menu |
| esc-a | Animation menu |
| esc-t | Mouse tools |
| esc-z | Undo |
| esc-r | Redo |
| esc-V | View mode |
| esc-i | File/canvas info |
| esc-I | Character inspector |
| esc-F | Search/find string |
| ctrl-l | Redraw screen |
| esc-h | Help |
| esc-q | Quit |

### Canvas Size Adjustment

| Key | Function |
|-----|----------|
| esc-" | Insert line |
| esc-: | Delete line |
| esc-> | Insert column |
| esc-< | Delete column |

### File Operations

| Key | Function |
|-----|----------|
| esc-C | New/clear canvas |
| esc-o | Open |
| esc-s | Save |

## Advanced Features

### Brushes

To create a custom brush:
1. Use shift-arrow or esc-K to make a selection
2. Press b to save the selection as a brush
3. Click the Mouse Tools menu (esc-t) and select Paint (P)
4. Use the mouse to paint with your custom brush

### Animation

The draw command supports frame-based animation:
- Use esc-n to add new frames
- Use esc-j and esc-k to navigate between frames
- Use esc-p to start/stop playback
- Adjust playback speed with esc-+ and esc--
- Set frame delay with esc-D

## Tips & Tricks

1. **Use the Mouse**: Click on highlighted areas of the screen for faster navigation.

2. **Character Sets**: Press esc-S to cycle through different character sets.

3. **Help Anytime**: Press esc-h to access the built-in help system.

4. **View Mode**: Press esc-V to enter view mode which hides the UI for a cleaner preview.

5. **Color Replacement**: Use esc-L to replace one color with another throughout your drawing.

## Examples

```bash
# Create a colorful ANSI banner
cliche draw --ansi -w 100 -h 10 -o banner.dur

# Make ASCII art for a README
cliche draw --ascii -o project_logo.dur

# Create a large drawing canvas
cliche draw -w 120 -h 40
```

## Troubleshooting

### Installation Issues

1. **Permission Errors**: If you encounter permission errors during installation or when running the draw command, ensure you installed CLIche with sudo privileges:
   ```bash
   sudo ./install.sh
   ```

2. **Command Not Found**: If the draw command is not found or Durdraw components cannot be loaded:
   ```bash
   # Reinstall with sudo
   sudo ./install.sh
   
   # Or manually install Durdraw
   cd /opt/cliche/draw
   sudo pip install -e .
   ```

3. **Module Import Errors**: If you see Python import errors related to Durdraw, the installation might be incomplete:
   ```bash
   # Check if Durdraw is properly installed
   cd /opt/cliche/draw
   sudo pip install -e .
   ```

### Runtime Issues

1. **Display Problems**: If the editor displays incorrectly, try a different terminal or adjust your terminal settings.

2. **Color Issues**: If colors aren't displaying correctly, ensure your terminal supports 256 colors:
   ```bash
   # Check terminal color support
   echo $TERM
   # Should show something like xterm-256color
   ```

3. **Mouse Support**: If mouse interaction doesn't work, verify that your terminal supports mouse events.

---

For more detailed information about Durdraw (the underlying editor), please refer to the [Durdraw documentation](https://github.com/cmang/durdraw). 