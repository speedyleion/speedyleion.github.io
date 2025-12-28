---
layout: post
title:  "Developing Arduino Sketches with Neovim"
date:   2025-12-21 13:00:03 -0800
categories: mice electronics arduino
---

The code in the previous posts for the [Atmega][atmega] board were authored in
the Arduino IDE. Being an avid [neovim][neovim]/[Vim][vim] user, I quickly felt
slowed down trying to move around and make edits. I decided to look into what it
would take to develop with neovim. 

Doing a search online for "vim arduino", one of the first results is
[vim-arduino][vim-arduino]. From the README, this plugin allows for
compiling and uploading of sketches. I also want language server support, syntax
highlighting and go to definition. My neovim setup makes use of 
[nvim-lspconfig](https://github.com/neovim/nvim-lspconfig). Doing a quick search
through its 
[help docs](https://github.com/neovim/nvim-lspconfig/blob/master/doc/configs.md#arduino_language_server)
shows support for the [Arduino language server][arduino language server].

The vim-arduino plugin can use the Arduino IDE or the
[Arduino CLI][arduino-cli]. However, the language server requires the
Arduino CLI, as well as clangd.

# Arduino CLI

The first step was to get the [Arduino CLI][arduino-cli] installed and working.
The Arduino CLI provides 
[installation instructions](https://docs.arduino.cc/arduino-cli/installation/)
for the supported platforms. I'm on a Mac with [homebrew](https://brew.sh/)
installed, so I did:

```sh
brew install arduino-cli
```

I then utilized the instructions on the 
[getting started](https://docs.arduino.cc/arduino-cli/getting-started/)
page from the Arduino CLI. I didn't quite follow them in order or to the letter.

## Creating a Config File

The getting started docs say that the Arduino CLI doesn't need a configuration
file and that it's a convenience. However, the Arduino language server does
require a config file. Be sure and save the path to the config file that the
command returns.

```sh
arduino-cli config init
```

The above command gave the following output:

```
Config file written to: /Users/nick/Library/Arduino15/arduino-cli.yaml
```
## Installing Board Dependencies

Prior to compiling and uploading, the board needs to be connected and its
dependencies installed. 

First the index should be updated. I didn't find this step necessary, but did it
just in case.

```sh
arduino-cli core update-index
```

After connecting the board to my computer I listed the board:

```sh
arduino-cli board list
```

This provided the following output:

```
Port                            Protocol Type              Board Name       FQBN                 Core
/dev/cu.Bluetooth-Incoming-Port serial   Serial Port       Unknown
/dev/cu.debug-console           serial   Serial Port       Unknown
/dev/cu.usbmodemHIDGD1          serial   Serial Port (USB) Arduino Leonardo arduino:avr:leonardo arduino:avr
```

The last line happened to be the one of interest. The main columns to save are
the Port, FQBN, and Core. FQBN stands for "Fully Qualified Board Name".

Then I installed the core for the board based on the `Core` column of the above
board list.

```sh
arduino-cli core install arduino:avr
```

## Compile and Upload a Sketch

To ensure the CLI can correctly communicate with the board a simple sketch was
created. This sketch was then be compiled and uploaded to the Atmega board.

In a directory that was okay to create subdirectories in, I created a new
sketch and used a slightly modified version of the example sketch from the
getting started docs.

```sh
arduino-cli sketch new test
cd test
echo 'void setup() {
    pinMode(LED_BUILTIN_RX, OUTPUT);
}

void loop() {
    digitalWrite(LED_BUILTIN_RX, HIGH);
    delay(1000);
    digitalWrite(LED_BUILTIN_RX, LOW);
    delay(1000);
}' > test.ino
```

A thing to note about Arduino sketches and the CLI, the directory name of the
sketch must match the name of the primary `.ino` file. This is captured somewhat
in the
[sketch build process](https://docs.arduino.cc/arduino-cli/sketch-build-process/)
documentation.

> All .ino [...] files in the sketch folder (shown in the Arduino IDE as tabs
> with no extension) are concatenated together, starting with the file that
> matches the folder name followed by the others in alphabetical order.  

Compiling and uploading are two separate commands. I can't stress this enough. I
kept only compiling, wondering why I wasn't seeing changes. The Port
and FQBN are required from the board listing above for these commands.

```sh
arduino-cli compile -p /dev/cu.usbmodemHIDGD1 --fqbn arduino:avr:leonardo 
arduino-cli upload -p /dev/cu.usbmodemHIDGD1 --fqbn arduino:avr:leonardo 
```

Watch out for the port changing on first upload. I got the following output
after the first upload. This required me to change the port for subsequent
uploads to `-p /dev/cu.usbmodem2101`.

```
New upload port: /dev/cu.usbmodem2101 (serial)
```

The port isn't actually needed for the compile command, but I put it there so I
can quickly toggle and update the command for compile versus upload.

The board should have a blinking led now.

# Arduino Language Server

In order to use the Arduino language server it and its dependencies need to be
installed. The Arduino CLI was already installed above. The language server is a
go module that can be installed:

```sh
go install github.com/arduino/arduino-language-server@latest
```

I happened to have go set up where the installed modules are in my path.

`clangd` is required. I had LLVM installed already via brew which provided
`clangd`. If LLVM/`clangd` is not installed yet then it can be done with brew.

```sh
brew install llvm
```

## Enabling in neovim

Getting the Arduino language server to work with neovim took a bit of work.

Initially I only enabled it in my `init.lua` file:

```lua
vim.lsp.enable('arduino_language_server')
```

However when I tried to open the above `test.ino` file up in neovim I got an error message:

> Client arduino_language_server quit with exit code 1 and and signal 0. Check log for errors: /Users/nick/.local/state/nvim/lsp.log

Instead of navigating to the `~/.local` dir I opened the log up in neovim with
the `:LspLog` command. At the bottom of the log there was: 

> [ERROR][2025-12-28 21:02:25] ...p/_transport.lua:36	"rpc"	"arduino-language-server"	"stderr"	"21:02:25.970684 Path to ArduinoCLI config file must be set.\n"

I was a little surprised. There clearly was a _default_ location
for the CLI config file, yet the language server required it to be explicitly
called out. There is an 
[example invocation](https://github.com/arduino/arduino-language-server?tab=readme-ov-file#usage)
in the Arduino language server README which says:

> To start the language server the IDE may provide the path to Arduino CLI and clangd 

```sh
./arduino-language-server \
 -clangd /usr/local/bin/clangd \
 -cli /usr/local/bin/arduino-cli \
 -cli-config $HOME/.arduino15/arduino-cli.yaml \
 -fqbn arduino:mbed:nanorp2040connect
```

The **may** part indicates the paths are optional, but left the CLI config file
in a bit of an unknown state.

I created `after/lsp/arduino_language_server.lua` in my neovim directory with the
following contents:

```lua
  return {
    cmd = {
        "arduino-language-server",
        "-cli-config", 
        vim.fn.expand("~/Library/Arduino15/arduino-cli.yaml"),
        "-fqbn",
        "arduino:avr:leonardo"
    }
  }
```

This provided the board FQBN and CLI config file from earlier, but left the CLI
and clangd to be found in the system path. Restarting neovim and opening the
`test.ino` file gave me syntax highlighting and I was able to go to the
definition of `OUTPUT` and other defines.

I would like to find a way to populate the FQBN based on the sketch directory or
similar, but figured hardcoding is acceptable for now since I'll mostly be
working with the Atmega board, which happens to work as a leonardo board.

# vim-arduino

My neovim setup uses [lazy.nvim](https://github.com/folke/lazy.nvim).
I added `lua/plugins/arduino.lua` to my neovim files with the following content.

```lua
return { "stevearc/vim-arduino", name = "arduino" }
```

This installed the `vim-arduino` plugin. I could now see the help docs, 
`:help ArduinoVerify`, but I was not able to run the commands. I would get:

> E492: Not an editor command: ArduinoVerify

Doing some digging it appears to be an issue with `lazy.nvim` and a pure
vimscript plugin. I found, 
[https://github.com/stevearc/vim-arduino/issues/59](https://github.com/stevearc/vim-arduino/issues/59)
which mentions explicitly listing all the commands to get them to load.

```lua
return { 
    "stevearc/vim-arduino",
    name = "arduino",
    cmd = {
    "ArduinoAttach",
    "ArduinoChooseBoard",
    "ArduinoChooseProgrammer",
    "ArduinoChoosePort",
    "ArduinoVerify",
    "ArduinoUpload",
    "ArduinoSerial",
    "ArduinoUploadAndSerial",
    "ArduinoInfo",
    },
}
```

After this I was able to execute the commands.

# Sketch Project File

The Arduino CLI documentation mentions a 
[sketch project file](https://docs.arduino.cc/arduino-cli/sketch-project-file/).
This file allows project specific settings and build profiles. 

My main use case is to minimize command line arguments and avoiding choosing a
board and port when using vim-arduino. In the `test` sketch directory I created
a `sketch.yml` file.

```sh
echo 'default_fqbn: arduino:avr:leonardo
default_port: /dev/cu.usbmodem2101' > sketch.yml
```

After this I was able to reduce my command line invocation to:

```sh
arduino-cli compile
arduino-cli upload
```

I was also able to use the the `:ArduinoVerify` and `:ArduinoUpload` commands
from vim-arduino without needing to configure the board or the port.

[atmega]: https://www.amazon.com/Atmega32U4-Programming-Development-Micro-Controller-Compatible/dp/B0D83FBYPD
[vim]: https://www.vim.org/
[neovim]: https://neovim.io/
[arduino-cli]: https://docs.arduino.cc/arduino-cli/
[vim-arduino]: https://github.com/stevearc/vim-arduino
[arduino language server]: https://github.com/arduino/arduino-language-server