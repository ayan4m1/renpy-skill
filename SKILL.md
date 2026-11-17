---
name: renpy
description: Expert help for building visual novels and story games with the Ren'Py engine — writing and debugging .rpy scripts (dialogue, characters, labels, menus, choices, branching, variables), images and sprites, transforms and ATL animation, transitions, screens and screen language UI, GUI customization, styles, audio, save/load/rollback, persistent data, translation, Python inside Ren'Py, lint and automated testing, and building/distributing for PC, Android, iOS, and web. Use this skill whenever the user is working on a Ren'Py project or mentions Ren'Py, RenPy, .rpy/.rpyc files, `label start`, Character(), `screen` code, ATL, a visual novel / VN / dating sim / kinetic novel in Python, or a traceback.txt from a game — even if they don't name Ren'Py explicitly.
---

# Ren'Py Game Development

This skill helps write, fix, and ship Ren'Py games. The official Ren'Py
documentation (https://www.renpy.org/doc/html/) is the source of truth. A
Markdown mirror of it lives in `references/docs/`, one file per doc page, with a
table of contents in `references/docs/INDEX.md`.

## How to work

1. **Ground everything in the docs.** Ren'Py has a lot of specific syntax, and
   its APIs change between versions. Model memory of it is often out of date,
   or mixed up with similar engines. Before you write code that uses a
   statement, screen property, transform property, action, config variable, or
   `renpy.*` function you aren't certain about, look it up in
   `references/docs/`. Grep is the fastest way, because every documented
   function and variable appears as a bold signature line:
   - `Grep "renpy.show_screen" references/docs` or `Grep "config.rollback" references/docs`
   - Definitions look like ``**`define config.name = default`**`` and
     ``**`renpy.func(args)`**``, so grepping for ``\*\*`renpy\.notify`` finds
     the definition and not just mentions.
   - The pages are long. Read just the section you need (Grep with `-n`,
     then Read with offset/limit). Don't load a whole 100 KB page.
   - Use the topic map below to pick the right page.
   If the docs and your memory disagree, trust the docs. If the user's project
   targets an older Ren'Py, check `incompatible.md` and `changelog.md` for when
   a feature appeared or changed.

2. **Look at the project before writing code.** A typical project looks like
   this:
   ```
   <project>/
     game/
       script.rpy      # story; `label start:` lives here by default
       options.rpy     # config.*/build.* settings (name, version, save_directory)
       gui.rpy         # gui.* variables (fonts, colors, sizes) from the GUI generator
       screens.rpy     # the default screens (say, choice, main_menu, preferences…)
       images/  audio/  gui/  tl/   # auto-imported images, sound, GUI art, translations
     traceback.txt / errors.txt / lint.txt    # written when something goes wrong
   ```
   Follow the conventions already used in the project: its character variable
   names, its image naming scheme, its use of `gui.*` variables vs. raw values,
   and its file layout. Ren'Py loads every `.rpy` under `game/`, so new code
   can go in a new file. Don't cram it into `script.rpy`.

3. **Verify.** When a Ren'Py SDK is available, run lint after making changes,
   and run the game or tests if they're relevant (see *Tooling* below). Lint
   catches undefined images, bad jumps, missing characters, and a lot more.
   Ren'Py reports parse and runtime errors in `traceback.txt`/`errors.txt` in
   the project directory, so read those when a run fails.

## Topic map (task → doc page in `references/docs/`)

| Task | Pages |
|---|---|
| New to Ren'Py / overall flow | `quickstart.md`, `language_basics.md`, `lifecycle.md` |
| Dialogue, characters, text speed, NVL | `dialogue.md`, `nvl_mode.md`, `multiple.md`, `bubble.md`, `character_callbacks.md` |
| Labels, jump/call/return, special labels (`splashscreen`, `after_load`…) | `label.md` |
| Choices/menus, if/while | `menus.md`, `conditional.md` |
| Variables, `define` vs `default`, `init python`, stores, pip packages | `python.md`, `statement_equivalents.md`, `ren_py.md` |
| Showing images, `scene`/`show`/`hide`, image tags/attributes, images dir | `displaying_images.md` |
| Layered sprites (outfits/expressions) | `layeredimage.md`, `side_image.md` |
| Displayables (Image, Solid, Composite, Frame, Movie, ConditionSwitch…) | `displayables.md` |
| Transforms & ATL animation; position/zoom/alpha properties | `transforms.md`, `transform_properties.md` |
| Transitions (`with dissolve`, Fade, ImageDissolve, MoveTransition) | `transitions.md` |
| Text tags, interpolation `[var]`, fonts, ruby, outlines | `text.md`, `custom_text_tags.md`, `textshaders.md` |
| Screens/UI: textbutton, imagebutton, vbox, viewport, bar, input | `screens.md`, `screen_actions.md`, `screen_python.md`, `screen_special.md`, `screen_optimization.md` |
| Restyling menus/textbox; GUI generator variables | `gui.md`, `gui_advanced.md`, `style.md`, `style_properties.md` |
| `config.*` / `preferences.*` / store variables | `config.md`, `preferences.md`, `store_variables.md` |
| Music, sound, voice, movies | `audio.md`, `audio_filters.md`, `voice.md`, `movie.md` |
| Save/load, rollback, persistent unlocks | `save_load_rollback.md`, `persistent.md` |
| Gallery, music room, replays, achievements, history log | `rooms.md`, `achievement.md`, `history.md` |
| Text input, drag-and-drop, keymap, mouse cursors, gestures | `input.md`, `drag_drop.md`, `keymap.md`, `mouse.md`, `gesture.md` |
| Translation / localization | `translation.md` |
| Colors, shaders, matrixcolor, 3D stage, Live2D | `color_class.md`, `matrixcolor.md`, `model.md`, `3dstage.md`, `live2d.md` |
| Custom displayables / statements | `cdd.md`, `cds.md` |
| Misc `renpy.*` functions (random, notify, pause, quit…) | `other.md`, `file_python.md` |
| Debugging, console, reload, warp, lint | `developer_tools.md`, `director.md`, `problems.md` |
| Automated tests | `testcases.md` |
| CLI automation / CI | `cli.md`, `launcher.md` |
| Build & distribute (PC/Mac/Linux), archives, updater | `build.md`, `updater.md`, `splashscreen_presplash.md` |
| Mobile & web | `android.md`, `ios.md`, `web.md`, `chromeos.md`, `downloader.md`, `iap.md` |
| Accessibility, self-voicing | `self_voicing.md` |
| Version differences / upgrading old projects | `incompatible.md`, `changelog.md` |

## Core language essentials

These are the rules people get wrong most often. Each one points to the page
that explains it.

**Indentation & blocks** (`language_basics.md`): Ren'Py script works like
Python. A line ending in `:` opens a block, and the block must be indented
(4 spaces by convention). Unlike Python, a string can run over several lines.
Script strings don't support the `f`/`u`/`b` prefixes, so use `[var]`
interpolation instead of f-strings. Triple-quoted strings behave specially
(monologue mode), so don't use them as ordinary strings.

**`define` vs `default`** (`python.md`, `save_load_rollback.md`):
- `define x = ...` runs at init time and is treated as a **constant**. It isn't
  saved and shouldn't be changed later. Use it for `Character`s, config,
  transforms, and lookup tables.
- `default x = ...` declares **game state**. It's saved, loaded, and rolled
  back. Every variable the story changes (points, flags, inventory) should be
  declared with `default`. Don't introduce state with `$ x = 0` inside
  `label start`: old saves loaded into a newer build won't have the variable.
  `default` also covers the `after_load` case.
- Changing a `define`d object (`$ lookup["k"] = 1`) or setting a `config.*`
  variable after init leads to bugs that don't survive a save/load. Config
  variables and styles aren't saved.

**Characters & dialogue** (`dialogue.md`):
```renpy
define e = Character("Eileen", color="#c8ffc8", image="eileen")

label start:
    scene bg room
    show eileen happy
    e "Hello, [player_name]!"          # [ ] interpolates variables
    "Narration has no speaker."
    e happy "Say-with-attribute changes the sprite."
    e "Literal brackets/braces need doubling: [[ and {{."
    return
```

**Control flow** (`label.md`): `jump` goes to a label and doesn't come back.
`call` returns to the caller when the label hits `return`. A `return` with no
caller ends the game and goes back to the main menu. Labels that start with
`.` are local to the global label above them. `label start` is the entry
point.

**Menus** (`menus.md`):
```renpy
menu:
    "Where should we go?"            # optional say statement, shown with the choices
    "The park" if met_eileen:        # a condition hides the choice when false
        $ affection += 1
        jump park
    "Home":
        pass
```

**Images** (`displaying_images.md`): An image name is a *tag* followed by
*attributes* (`eileen happy`). Showing an image with the same tag replaces the
old one. Files in `game/images/` (and its subfolders) are defined
automatically: the extension and folder are dropped and the name is
lowercased, so `images/eileen/Eileen Happy.png` becomes `eileen happy`.
Usually no `image` statement is needed. `scene` clears the layer, `show … at left` positions an
image, and `with dissolve` applies a transition. Prefer WEBP/AVIF/PNG, and
check `displaying_images.md` for the formats the target version supports.

**Transforms & ATL** (`transforms.md`, `transform_properties.md`):
```renpy
transform bounce:
    yoffset 0
    easein 0.3 yoffset -30
    easeout 0.3 yoffset 0
    repeat
show eileen happy at center, bounce
```
Look up the exact property names and warpers in the docs.

**Screens** (`screens.md`, `screen_actions.md`): Screens are declarative. They
get re-evaluated many times, so screen code must have **no side effects**. Put
state changes in actions (`SetVariable`, `SetScreenVariable`, `ToggleVariable`,
`Function`, `Return`, `Jump`, `Show`, `Hide`). Don't call functions that
change state in the screen body. Use `call screen` when the screen should
block and return a value, and `show screen` for overlays/HUDs. Declare screen
parameters (`screen stats(char):`) and local state (`default page = 0`) inside
the screen. To restyle the default UI (say box, choice buttons, main menu),
edit `gui.rpy` variables first, then `screens.rpy`. Check the "Special Screen
Names" page so you keep the screen names and `id`s Ren'Py requires.

**Python** (`python.md`): `$ one_liner`, `python:` blocks run at that point in
the story, and `init python:` blocks run at startup (for defining
functions/classes). Ren'Py 8 runs Python 3. For randomness that has to work
with rollback, use `renpy.random` instead of `random` (`other.md`). Put
pure-Python third-party packages in `game/python-packages/`. Classes whose
instances end up in saves must be picklable, and they should be defined at
init time so loading saves still works (`save_load_rollback.md`).

**Persistent data** (`persistent.md`): `persistent.x` survives across
playthroughs, for things like unlocks, endings seen, and gallery state. Give
it a default with `default persistent.x = ...`. Unset fields read as `None`.

**Translation** (`translation.md`): Wrap UI and Python strings in `_()` so
they can be extracted. Generate `game/tl/<language>/` with the launcher or
`translate <language>` in the CLI. Dialogue is translated automatically by
statement identity.

## Writing good Ren'Py code

- Use small labels. Split long routes across files (`chapter1.rpy`,
  `route_eileen.rpy`) and connect them with `jump`/`call`.
- Name images consistently (`bg park day`, `eileen casual smile`) so
  attribute replacement works and lint can check them. For characters with
  many outfit/expression combinations, use `layeredimage` instead of
  exporting every combination as its own file.
- Keep magic numbers in `gui.*`/`define` so the game can be restyled in one
  place.
- Put helper functions and classes in `init python` blocks or `_ren.py` files.
  Avoid huge `python:` blocks in the middle of story labels.
- Respect rollback and saving. Story state lives in `default` variables, and
  it isn't hidden in module globals or `define`d mutable objects.
- When the user asks for a feature that Ren'Py already has (a gallery, music
  room, history screen, text input, achievements, drag-and-drop, NVL mode,
  side images, speech bubbles), use the built-in feature and its documented
  actions instead of reimplementing it.

## Tooling

`scripts/renpy_cli.py` wraps the SDK's command line on any OS. It finds the
SDK (the folder that contains `renpy.py`) from `--sdk <dir>`, else the
`RENPY_SDK` environment variable, else the newest `renpy-*-sdk` folder in
common locations. Run `python scripts/renpy_cli.py --where` to see which SDK
it picked. If it can't find one, ask the user where their SDK is. Don't
download one yourself without asking.

```bash
python scripts/renpy_cli.py <project> lint --error-code   # static check
python scripts/renpy_cli.py <project> compile             # force recompile
python scripts/renpy_cli.py <project> test                # run testcases
python scripts/renpy_cli.py <project> run --warp script.rpy:42
python scripts/renpy_cli.py launcher distribute <project> --destination <out>
```

The wrapper prints `traceback.txt`/`errors.txt` when a run writes them. Lint
output goes to stdout. Some lint findings are warnings or statistics, so read
them before calling something an error. Running the game opens a window, so
only do that when the user wants it or it's the only way to check something.
In that case, `--warp file:line` jumps straight to the code you changed
(this needs `config.developer`, whose default `"auto"` turns it on in an
unpackaged project).

For in-game debugging, point users to Shift+R (reload the script), Shift+O
(console), Shift+D (developer menu), and Shift+I (style inspector), all
described in `developer_tools.md`.

## Keeping the docs current

The mirror was generated from the Ren'Py version shown at the top of
`references/docs/INDEX.md`. To refresh it from the website (stdlib Python
only; it also rebuilds the index), run:

```bash
python scripts/sync_docs.py                  # all pages
python scripts/sync_docs.py screens config   # selected pages
python scripts/sync_docs.py --base-url https://www.renpy.org/dev-doc/html/   # nightly docs
```

If the user's SDK version is much newer than the mirror, or they're using a
feature the mirror doesn't cover, refresh the mirror or read the live page at
`https://www.renpy.org/doc/html/<page>.html`.
