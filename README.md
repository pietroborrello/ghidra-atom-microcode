# Intel Atom Microcode - Ghidra Processor Module
Ghidra Processor Module to disassemble and decompile the x86 Intel Atom microcode provided in [chip-red-pill/uCodeDisasm](https://github.com/chip-red-pill/uCodeDisasm).

![Screenshot](/images/Screenshot1.png)


## Install and Run
This module has been tested on Ghidra 9.2.

1. Clone this repo in `<ghidra install dir>/Ghidra/Processors/`
2. `git clone https://github.com/chip-red-pill/uCodeDisasm`  and copy `lib/txt2ghidra.py` from this repo to the `uCodeDisasm` folder.
3. run `./txt2ghidra.py ../ucode/ms_array0.txt`, which will produce a `glm.ucode` binary file
4. Run Ghidra and load `glm.ucode` selecting `x86ucode` as Language for the binary



## Details

From [chip-red-pill/uCodeDisasm](https://github.com/chip-red-pill/uCodeDisasm):
> The microcode of the Intel Atom CPUs consists from two large chunks of data – Microcode Triads and Sequence Words. These data are kept in the ROM area of a functional block inside CPU core that is called Microcode Sequencer (MS).

We encourage to read the `uCodeDisasm` readme and source code to understand ucode internals mechanisms.

### Addressing

The `txt2ghidra.py` simply packs together Microcode Triads and Sequence words into 16-bytes ucode instructions that will be analyzed by our Ghidra Processor Module. During the process it additionally transforms and inserts metadata into the instructions to make ghidra's life easier.

Since instructions are now 16 bytes long and Ghidra does not currently support word sizes bigger than 8 bytes, the ucode address scheme in Ghidra is different from what one would expect from reading the `uCodeDisasm` repo, and all the code addresses must be multiplied by 0x10.

For example `cpuid_xlat` is at address 0x0be0 in the originally published ucode, while at address 0x0be00 in Ghidra (see Screenshot).

### Instructions

Each ghidra instruction will be composed by a microcode instruction and possibly by a sequence word, that either influences control flow after the instruction execution (`eflow`), or sets up some of synchronization before execution. 


## TODOs

Most of the instructions' semantics is correctly defined, and decompilation should generally work. 
We recommend paying attention to the following details:

- all registers are assumed to be 64 bits, which is in general false
- no SSE/AVX instruction is currently supported
- temporary register aliasing is not modeled (`ROVR`)
- indirect jumps are rarely resolved by ghidra
- decompiled functions may return using jumps trough the `UIP0/1` register (see (`uCodeDisasm`)[https://github.com/chip-red-pill/uCodeDisasm])
- load and store operations have modifiers with unclear semantics (`PPHYS`, `TICKLE`, `PPHYSTICKLE`)
- understand how function calls may return values
- unclear semantics on some operations (uflow, flags operations, selectors packing, ...) marked by `TODO` in the `.slaspec` file