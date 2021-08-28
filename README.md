# Intel Atom Microcode - Ghidra Processor Module
Ghidra Processor Module to disassemble and decompile the x86 Intel Atom microcode provided in [chip-red-pill/uCodeDisasm](https://github.com/chip-red-pill/uCodeDisasm).

<img src="https://user-images.githubusercontent.com/18199462/131227675-5c65de2e-6370-4996-80ab-6294e7d674b7.png" width="1920px">

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

For example, `cpuid_xlat` is at address 0x0be0 in the originally published ucode, while at address 0x0be00 in Ghidra (see Screenshot).

### Instructions

Each ghidra instruction will be composed by a microcode instruction and possibly by a sequence word, that either influences control flow after the instruction execution (`eflow`), or sets up some of synchronization before execution. 


## Open Problems

Most of the instructions' semantics is correctly defined, and decompilation should generally work.  
There are a few remaining open problems to tackle. PR and issues to discuss them are welcomed.

- We identify function calls as instructions doing `saveuip + jmp` (usually combining instructions and sequence words), but this may not always be true.
- How do function calls return values? Seems a mix of temporary registers, but not always the same registers.
- Load and store operations have modifiers with unclear semantics (`PPHYS`, `TICKLE`, `PPHYSTICKLE`). What do they mean?
- There is still unclear semantics on some operations (uflow parameters, arithmetic flags operations, segment selectors packing, ...) marked by `TODO` in the `.slaspec` file

There is also some missing implementation details: 

- All registers are assumed to be 64 bits, which is in general false. Disassembled instruction include the operand size, but not the decompiled view.
- No SSE/AVX instruction is currently supported.
- Temporary register aliasing is not modeled (`ROVR`).
- Indirect jumps are rarely resolved by ghidra.
- Functions return using jumps trough the `UIP0/1` register (see (`uCodeDisasm`)[https://github.com/chip-red-pill/uCodeDisasm]) which decreases decompilation quality.
