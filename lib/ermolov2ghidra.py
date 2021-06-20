#!/usr/bin/env python3

import sys
import os
from struct import pack

def load_ms_array_str_data(file_name):
    fi = open(file_name, "r")
    str_array = fi.read()
    fi.close()
    
    array_vals = []
    str_lines = str_array.split("\n")
    for str_line in str_lines:
        addr_four_vals = str_line.split(":")
        if len(addr_four_vals) != 2:
            continue
        four_vals = addr_four_vals[1].strip()
        four_vals_seq = four_vals.split()
        if len(four_vals_seq) != 4:
            continue
        for val in four_vals_seq:
            array_vals.append(int(val, 16))
    return array_vals

def get_uop_opcode(uop):
    return (uop >> 32) & 0xfff

def is_uop_testustate(uop):
    opcode = get_uop_opcode(uop)
    return (opcode & 0xf3f) == 0x00a

def dump_seqword(seqword):
    uop_ctrl = (seqword & 0x3c) >> 2 # eflow -> URET, UEND, SAVEUIP
    uop_ctrl_uidx = seqword & 0x03   # up0
    
    tetrad_ctrl_uidx = (seqword & 0xc0) >> 6           # up1
    tetrad_ctrl_next_uaddr = (seqword & 0x7fff00) >> 8 # uaddr -> GOTO
    
    sync_ctrl = (seqword & 0xe000000) >> 25      # sync
    sync_ctrl_uidx = (seqword & 0x1800000) >> 23 # up2

    dump =  f'''
+------+-----+---------+-----+-------+-----+
|  {sync_ctrl:02x}  | {sync_ctrl_uidx:02x}  |  {tetrad_ctrl_next_uaddr:04x}   | {tetrad_ctrl_uidx:02x}  | {uop_ctrl:02x}    | {uop_ctrl_uidx:02x}  |
| sync | up2 |  uaddr  | up1 | eflow | up0 |
+------+-----+---------+-----+-------+-----+
'''
    return dump.strip()

# filter the seqword to keep only relevant part for the particular uop and not 
# the whole tetrad
# -> set the bit 1 in the upX part of the seqword when the control is enabled
def filter_seqword(uaddr, uop, seqword):
    uop_ctrl = (seqword & 0x3c) >> 2 # eflow -> URET, UEND, SAVEUIP
    uop_ctrl_uidx = seqword & 0x03   # up0
    
    tetrad_ctrl_uidx = (seqword & 0xc0) >> 6           # up1
    tetrad_ctrl_next_uaddr = (seqword & 0x7fff00) >> 8 # uaddr -> GOTO
    
    sync_ctrl = (seqword & 0xe000000) >> 25      # sync
    sync_ctrl_uidx = (seqword & 0x1800000) >> 23 # up2

    uret_uop_ctrls = (2, 3)
    uend_uop_ctrls = (0xc, 0xd, 0xe, 0xf)
    exec_flow_uop_ctrls = uret_uop_ctrls + uend_uop_ctrls
    save_uip_uop_ctrls = (4, 5, 6, 7)
    save_uip_reg_ovr_uop_ctrls = (6, 7)
    misc_exec_ctrl_uop_ctrls = (8, 9, 0xb)
    
    lfence_sync_ctrls = (1, 2, 3)
    oooe_sync_ctrls = (4, 5, 6, 7)

    uidx = uaddr & 0x03
    if(uidx == 0x03):
        return 0x0

    assert(uop_ctrl != 1 and uop_ctrl_uidx != 0x03)
    assert(sync_ctrl_uidx != 0x03 or sync_ctrl == 0)
    assert(uop_ctrl_uidx == 0 or uop_ctrl != 0)

    # pass the operations only when the uop will make use of it
    # -> i.e. when the idx match the uidx
    if sync_ctrl_uidx == uidx:
        out_sync = sync_ctrl
        enable_sync = 1
    else:
        out_sync = 0
        enable_sync = 0

    if uop_ctrl_uidx == uidx:
        out_ctrl = uop_ctrl
        enable_ctrl = 1
    else:
        out_ctrl = 0
        enable_ctrl = 0

    is_testustate_uop = is_uop_testustate(uop)
    special_tetrad_ctrl_case = uidx == 2 and tetrad_ctrl_uidx == 3 and is_testustate_uop and \
        (uop_ctrl_uidx != 2 or (uop_ctrl not in exec_flow_uop_ctrls))
    if tetrad_ctrl_uidx == uidx or special_tetrad_ctrl_case:
        out_tetrad_ctrl = tetrad_ctrl_next_uaddr
        enable_tetrad_ctrl = 1
    else:
        out_tetrad_ctrl = 0
        enable_tetrad_ctrl = 0

    return (enable_ctrl << 0) | (out_ctrl << 2) | (enable_tetrad_ctrl << 6) | (out_tetrad_ctrl <<  8) | (enable_sync << 23) | (out_sync << 25)

def get_uop_opcode(uop):
    return (uop >> 32) & 0xfff

def get_src0_sel(uop):
    return uop & 0x3f

def get_src1_sel(uop):
    return (uop >> 6) & 0x3f

def get_dst_sel(uop):
    return (uop >> 12) & 0x3f

def is_src_imm_sel(sel):
    imm_sels = [0x08, 0x09, 0x0a, 0x0b, 0x0c, 0x0d, 0x0e, 0x0f, 0x10, \
                0x18, 0x19, 0x1a, 0x1b, 0x1c, 0x1d, 0x1e, 0x1f]
    return sel in imm_sels

# collect some metadata that will go in the upper 16 bits of the uop
def get_metadata(uop):
    src0_sel = get_src0_sel(uop)
    src1_sel = get_src1_sel(uop)
    dst_sel = get_dst_sel(uop)
    
    is_src0 = src0_sel != 0x00
    is_src1 = src1_sel != 0x00
    # is_src2 = is_uop_dst_src2(uop)
    # is_dst = not is_src2 and dst_sel != 0x00 and dst_sel != 0x10
    
    is_src0_imm = 1 if is_src_imm_sel(src0_sel) else 0
    is_src1_imm = 1 if is_src_imm_sel(src1_sel) else 0

    return (is_src0_imm << 0) | (is_src1_imm << 1)
    

def ucode_dump(arrays_dump_dir):
    ucode = load_ms_array_str_data(arrays_dump_dir + "/ms_array0.txt")
    msrom_seqwords = load_ms_array_str_data(arrays_dump_dir + "/ms_array1.txt")
    assert(len(ucode) == len(msrom_seqwords))
    msram_seqwords = load_ms_array_str_data(arrays_dump_dir + "/ms_array2.txt")

    with open('glm.ucode', 'wb') as f:
        for uaddr, uop in enumerate(ucode):
            seqword = msrom_seqwords[uaddr // 4 * 4]
            if uaddr >= 0x7c00:
                msram_addr = uaddr - (0x7e00 if uaddr >= 0x7e00 else 0x7c00)
                seqword = msram_seqwords[msram_addr // 4]

            filtered_seqword = filter_seqword(uaddr, uop, seqword)
            # print(dump_seqword(filtered_seqword))

            # collect uop medatata to ease ghidra disassembly
            meta_uop = get_metadata(uop)

            # 48 bits for the uop rounded up to 64
            packed_uop = pack('<Q', uop | (meta_uop << 48))

            # 30 bits rounded to 64 for sanity for the seqword
            packed_seqword = pack('<Q', filtered_seqword)

            # 128 bit per uop to have nicer addresses
            f.write(packed_uop + packed_seqword)
    
    print(f"[+] written {len(ucode)} uops")


def main():
    if len(sys.argv) < 2:
        print("Usage: %s <ms_array0_file_path>" % sys.argv[0])
        return -1
    
    ucode_dump(os.path.split(sys.argv[1])[0])

if __name__ == "__main__":
    main()