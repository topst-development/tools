#!/usr/bin/env python3
from argparse import ArgumentParser
from collections import namedtuple
from math import ceil, floor
import struct
import hashlib
import os

# Timing parameter
from argparse import ArgumentParser
from collections import namedtuple, OrderedDict
from math import ceil, floor
from orbit_defines import *

# PMS table
from pms_table import *

def make_tcc_image(rom, image, version, offset, target):
        # Certificate
        rom.write('CERT'.encode())
        rom.write(bytearray(252))

        # Header
        rom.write('HDR'.encode().ljust(4, b'\0'))     # MARKER
        rom.write(struct.pack("<L", len(image) + 128)) # Image and Appendix Length
        rom.write(struct.pack("<L", offset))           # Image Offset
        rom.write(bytearray(4))                        # Header Format Version
        rom.write('750x'.encode())                     # SoC Name
        rom.write('DCP'.encode().ljust(12, b'\0'))    # Image name
        rom.write(version.encode().ljust(16, b'\0'))  # Image version
        rom.write(struct.pack("<Q", target))           # Target Address
        rom.write(bytearray(40))
        rom.write(hashlib.sha256(image).digest())      # HASH
        rom.write(bytearray(128))                      # Reserved for SignTool
        if offset > 512:
                rom.write(bytearray(offset - 512))

        # Image
        rom.write(image)

        # Appendix
        rom.write(bytearray(128))

        return 0

def mkrom(romname, imagename, version, offset, target):
        image = open(imagename, 'rb')
        buf = image.read()
        length = (((len(buf) + 0x3F) >> 6) << 6)
        image.close()

        rom = open(romname, 'wb')
        make_tcc_image(rom, buf.ljust(length, b'\0'), version, offset, target)
        rom.close()
        return 0

version = 0x1111111E

##############################################################
#
#
# User DRAM Config
#
#
##############################################################
# 1. DDR Speed option
speed = 4264

# 2. DDR density configuration option.
manual_dram_num_config = 1
manual_dram_num = 1 
# manual_dram_num value is activated with manual_dram_num_config is set.
# manual_dram_num = 2 : Number of DRAM mounted in board is 2.
# manual_dram_num = 1 : Number of DRAM mounted in board is 1.


# Select byte mode for primary/seconadry dram
byte_mode = 0
sec_byte_mode = 0

# 3. DDR impedance option.
# read DQ impedance setting.
lpddr4_dq_dds = 6
soc_dq_odt = 6

# write DQ impedance setting.
soc_dq_dds = 7
lpddr4_dq_odt = 4

# write CA/CS/CK impedance setting
ca_dds = 7
rank0_ca_odt = 2
rank1_ca_odt = 2
clock_dds = 7

# Vref setting.
ca_vref = 0x29
soc_vref = 0xC
dram_vref = 0x10
soc_vref_train = 1
dram_vref_train = 1

# 4. LPDDR4/4X setting.
lpddr4_type = 0 # 0: lpddr4x, 1: lpddr4


##############################################################
#
#
# Unless there is a special purpose, do not modify the parameters below.
#
#
##############################################################

# search LPDDR4X phy PMS/PLL value
phypms=get_phy_pms(phypmss, speed)
pll_en=1
pll_value=phypms.pll_value

# size info(deprecated)
dram_size = 1024 
place_holder = 1024 
rank_num = 2
initial_size = 2048 
size_per_rank = 8
density_per_rank = 8 # Gb unit
num_bg_per_rank = 0
num_bank_per_rank = 3
num_row_per_rank = 16
num_col_per_rank = 10
rank_interleaving = 0
rank_interleaving_size = 256

# ca/ck delay 
prim_ck_delay = 0
sec_ck_delay = 0
ca_delay = 0x0

# refresh rate control
mr4_sensing_enable = 1
mr4_sensing_period = 32000
t_refiab = 3904000
t_refipb = 488000
adv_target_ref = 0
sw_refrate = 3 # thie value is valid when MR4 sensing is disabled.
abr_en_value = 0
abr_en_en = 1

# dram option
read_dbi = 1
write_dbi = 1
rpste = 0
wpste = 0
robust_dqs_mode = 1
init_zq_calibration = 1
dynamic_power_down = 0
dynamic_power_down_threshold = 0
dynamic_self_refresh = 0
dynamic_self_refresh_threshold = 0
regional_clock_gating = 1
phy_clock_gating = 1
dram_clock_gating = 1
zq_calibration = 1
zq_calibration_period = 48000 # us
periodic_training = 1
periodic_training_period = 24000 # us
extra_rtw = 0
fixed_odt_cs = 3

# fixed option
meso_synchronizer = 1
mrr_byte_lane0 = 1
mrr_byte_lane1 = 2
rclk_t_ck = 41666 # us
t_zqcal = 1000000
adv_al = 1
pipe_depth = 0
phy_freq_ratio = 4
tctrlupd_interval = 0
sec_param_sentinel = 0x7

temp_freq = int(speed/2)
temp_t_ck = int(((float(1)/float(temp_freq))*float(1000000)))
if temp_t_ck > 937:
	lpddr4_rpre = 0 # Static
else:
	lpddr4_rpre = 1 # Toggle

lpddr4_wpre = 1  # 2* tCK Fixed by JEDEC
reqq_depth = 32

# dram test option
test_pattern_high = 0xaaaaaaaa
test_pattern_low = 0xaaaaaaaa
dchk_size = 2048
test_result = 0

# ecc option
scrambler_on = 0
fsecc_en = 0
num_of_ecc_region = 0

ecc_region0_base_low = 0
ecc_region0_base_high = 0
ecc_region1_base_low = 0
ecc_region1_base_high = 0
ecc_region2_base_low = 0
ecc_region2_base_high = 0
ecc_region3_base_low = 0
ecc_region3_base_high = 0
ecc_region4_base_low = 0
ecc_region4_base_high = 0
ecc_region5_base_low = 0
ecc_region5_base_high = 0
ecc_region6_base_low = 0
ecc_region6_base_high = 0
ecc_region7_base_low = 0
ecc_region7_base_high = 0

ecc_region0_top_low = 0
ecc_region0_top_high = 0
ecc_region1_top_low = 0
ecc_region1_top_high = 0
ecc_region2_top_low = 0
ecc_region2_top_high = 0
ecc_region3_top_low = 0
ecc_region3_top_high = 0
ecc_region4_top_low = 0
ecc_region4_top_high = 0
ecc_region5_top_low = 0
ecc_region5_top_high = 0
ecc_region6_top_low = 0
ecc_region6_top_high = 0
ecc_region7_top_low = 0
ecc_region7_top_high = 0

# dqs delay and write leveling
omc_dqs_delay_en = 1
omc0_byte0_dqs_delay = 0xa
omc0_byte1_dqs_delay = 0x0
omc1_byte0_dqs_delay = 0x0
omc1_byte1_dqs_delay = 0xa
omc2_byte0_dqs_delay = 0x0
omc2_byte1_dqs_delay = 0x0
omc3_byte0_dqs_delay = 0x0
omc3_byte1_dqs_delay = 0x0
write_leveling = 0

# Membus speed
membus_pll_en = 0
membus_pll_val = 0
membus_speed = 933
memcore_div = 0
memsub_div = 0
lpddr4_peri_div = 0
lpddr4_user_div = 0

# Membus Qos 
qos_cfg0_en = 1
qos_cfg1_en = 0
qos_cfg2_en = 0
qos_cfg3_en = 0
qos_cfg0_val = 0xFF00
qos_cfg1_val = 0
qos_cfg2_val = 0
qos_cfg3_val = 0


# MR22 setting
# 	LPDDR4
# 	ODTE-CK/CS/CA setting is for override ODT_CA pad

# 	LPDDR4X
# 	ODTE-CK/CS/CA setting is for enable/disable CA bus ODT

# 	For Byte mode dram CA bus ODT.
# 	x8ODTD lower: [7:0] Byte select
# 	x8ODTD upper: [15:8] Byte select

if lpddr4_type == 0:
	rank0_odte_ck = 0
	rank0_odte_cs = 0
	rank0_odte_ca = 0

	rank0_x8odtd_lower = 0
	rank0_x8odtd_upper = 0

	if byte_mode == 1:
		rank0_x8odtd_lower = 1

	rank1_odte_ck = 1
	rank1_odte_cs = 0
	rank1_odte_ca = 1

	rank1_x8odtd_lower = 0
	rank1_x8odtd_upper = 0

	if byte_mode == 1:
		rank1_x8odtd_lower = 1
else:
	rank0_odte_ck = 0
	rank0_odte_cs = 0
	rank0_odte_ca = 0

	rank0_x8odtd_lower = 0
	rank0_x8odtd_upper = 0

	if byte_mode == 1:
		rank0_x8odtd_lower = 1

	rank1_odte_ck = 0
	rank1_odte_cs = 1
	rank1_odte_ca = 0

	rank1_x8odtd_lower = 0
	rank1_x8odtd_upper = 0

	if byte_mode == 1:
		rank1_x8odtd_lower = 1

rank0_ca_odt_cfg = (rank0_x8odtd_upper << 7)|(rank0_x8odtd_lower << 6)|(rank0_odte_ca << 5)|(rank0_odte_cs << 4)|(rank0_odte_ck << 3)
rank1_ca_odt_cfg = (rank1_x8odtd_upper << 7)|(rank1_x8odtd_lower << 6)|(rank1_odte_ca << 5)|(rank1_odte_cs << 4)|(rank1_odte_ck << 3)

dmc_init_cfg = 0x0

if membus_pll_en == 0:
	if membus_speed not in [933, 800, 700]:
		print('WHen membus_pll_en is low, MEMBUS speed must be in 933, 800, 700')
		exit(1)

# manual dram num config.
if manual_dram_num_config != 0:
    channel_set_en = 1
    channel_num = manual_dram_num * 2

    if not (channel_num == 2 or channel_num == 4):
        print('manual dram num setting is wrong. manual_dram_num must be 2 or 4')
        exit(1)
else:
    channel_set_en = 0
    channel_num = 4 # No meaningful. Just keep legacy value.

# Timing parameter
class Timing(namedtuple('Timing', 'min_ns min_nck is_mclk')):
    def __add__(self, other):
        if type(other) in [int, float]:
            return Timing(self.min_ns + other, self.min_nck, self.is_mclk)
        elif type(other) is Timing:
            return Timing(self.min_ns + other.min_ns, max(self.min_nck, other.min_nck), self.is_mclk)
        else:
            raise Exception('type %s is not supported yet' % type(other))
    def __sub__(self, other):
        if type(other) in [int, float]:
            return Timing(self.min_ns - other, self.min_nck, self.is_mclk)
        elif type(other) is Timing:
            return Timing(self.min_ns - other.min_ns, self.min_nck, self.is_mclk)
        else:
            raise Exception('type %s is not supported yet' % type(other))
    def __rsub__(self, other):
        return Timing(other - self.min_ns, 0, self.is_mclk)
    def __truediv__(self, other):
        if type(other) in [int, float]:
            return Timing(self.min_ns/other, self.min_nck, self.is_mclk)
        else:
            raise Exception('type %s is not supported yet' % type(other))
    def __floordiv__(self, other):
        if type(other) in [int, float]:
            return Timing(self.min_ns//other, self.min_nck, self.is_mclk)
        else:
            raise Exception('type %s is not supported yet' % type(other))

    def calc_ceil(self, t_ck):
        return int(max(ceil(self.min_ns*1000/t_ck), self.min_nck))
    def calc_floor(self, t_ck):
        return int(max(floor(self.min_ns*1000/t_ck), self.min_nck))

Memcfg = namedtuple('Memcfg', 'min_freq, max_t_ck, max_freq, min_t_ck, rl, rl_dbi, wl, odtlon, odtloff')


def lpddr4_encode_rl(rl, dbi, lpddr4_byte_mode):
    encoded = {
        0: {
            0: {
                 6: int('000',2),
                10: int('001',2),
                14: int('010',2),
                20: int('011',2),
                24: int('100',2),
                28: int('101',2),
                32: int('110',2),
                36: int('111',2),
            },
            1: {
                 6: int('000',2),
                12: int('001',2),
                16: int('010',2),
                22: int('011',2),
                28: int('100',2),
                32: int('101',2),
                36: int('110',2),
                40: int('111',2),
            }
        },
        1: {
            0: {
                 6: int('000',2),
                10: int('001',2),
                16: int('010',2),
                22: int('011',2),
                26: int('100',2),
                32: int('101',2),
                36: int('110',2),
                40: int('111',2),
            },
            1: {
                 6: int('000',2),
                12: int('001',2),
                18: int('010',2),
                24: int('011',2),
                30: int('100',2),
                36: int('101',2),
                40: int('110',2),
                44: int('111',2),
            }
        }
    }
    return encoded[lpddr4_byte_mode][dbi][rl]

def lpddr4_encode_wl(wl, wl_set=0):
    encoded = {
        0: {
             4: int('000',2),
             6: int('001',2),
             8: int('010',2),
            10: int('011',2),
            12: int('100',2),
            14: int('101',2),
            16: int('110',2),
            18: int('111',2),
        },
        1: {
             4: int('000',2),
             8: int('001',2),
            12: int('010',2),
            18: int('011',2),
            22: int('100',2),
            26: int('101',2),
            30: int('110',2),
            34: int('111',2),
        }
    }
    return encoded[wl_set][wl]

def lpddr4_encode_wr(t_wr, lpddr4_byte_mode):
    if lpddr4_byte_mode == 0:
        if wr <=  6: return int('000',2)
        if wr <= 10: return int('001',2)
        if wr <= 16: return int('010',2)
        if wr <= 20: return int('011',2)
        if wr <= 24: return int('100',2)
        if wr <= 30: return int('101',2)
        if wr <= 34: return int('110',2)
        if wr <= 40: return int('111',2)
    else:
        if wr <=  6: return int('000',2)
        if wr <= 12: return int('001',2)
        if wr <= 16: return int('010',2)
        if wr <= 22: return int('011',2)
        if wr <= 28: return int('100',2)
        if wr <= 32: return int('101',2)
        if wr <= 38: return int('110',2)
        if wr <= 44: return int('111',2)

def lpddr4_decode_wr(wr, lpddr4_byte_mode):
    decoded = {
        0: {
            int('000',2):  6,
            int('001',2): 10,
            int('010',2): 16,
            int('011',2): 20,
            int('100',2): 24,
            int('101',2): 30,
            int('110',2): 34,
            int('111',2): 40,
        },
        1: {
            int('000',2):  6,
            int('001',2): 12,
            int('010',2): 16,
            int('011',2): 22,
            int('100',2): 28,
            int('101',2): 32,
            int('110',2): 38,
            int('111',2): 44,
        }
    }
    return decoded[lpddr4_byte_mode][wr]

def lpddr4_decode_rtp(rtp):
    decoded = {
      int('000',2):  8,
      int('001',2):  8,
      int('010',2):  8,
      int('011',2):  8,
      int('100',2): 10,
      int('101',2): 12,
      int('110',2): 14,
      int('111',2): 16,
    }
    return decoded[rtp]

def search_memcfgs(memcfgs, t_ck):
    for memcfg in memcfgs:
        if memcfg.max_t_ck > t_ck and t_ck >= memcfg.min_t_ck:
            return memcfg
    raise Exception('invalid target clock period: %f ps' % t_ck)

if __name__ == '__main__':

    dmc_list = ['primary', 'secondary']
    t_param_prim = []
    t_param_sec = []

    for dmc in dmc_list:
            parser = ArgumentParser()
            parser.add_argument('-d', '--dram-type', default='lpddr4', choices=['ddr3', 'ddr4', 'lpddr3', 'lpddr4'], help='target memory type')
            parser.add_argument('--densities', type=str, nargs='+', help='list of target densities as Gb. It should be 1 in case of DDR3.')
            parser.add_argument('--phy-name', default='sphy-v8', type=str, help='name of phy')
            parser.add_argument('--project-name', type=str, help='name of project')
            parser.add_argument('-l', '--langugage', choices=['c'], default='c', help='target language')
            parser.add_argument('-o', '--output', default='orbit_timing_params.h', help='output file name')
            parser.add_argument('-p', '--pipe-depth', default=0, type=int, help='pipe line differences between command channel and data channel')
            parser.add_argument('-s', '--speed-bin', default=4266, type=str, help='speed-bin of DDR3 or DDR4 dram devices')
            parser.add_argument('-w', '--dq-width', default=16, type=int, choices=[4, 8, 16, 32], help='DQ width of "A" device.')
            parser.add_argument('--read-dbi-upto', type=int, default=0, help='maximum clock period as nano-seconds to be allowed to enable read DBI')
            parser.add_argument('--lp4-micron-org', type=int, default=0, help='apply the timing param of original micron model')
            parser.add_argument('--rpste-upto', type=int, default=0, help='maximum clock period as nano-seconds to be allowed to enable extended read post-amble (LPDDR4 only)')
            parser.add_argument('--wpste-upto', type=int, default=0, help='maximum clock period as nano-seconds to be allowed to enable extended write post-amble (LPDDR4 only)')
            parser.add_argument('--wire-length', default=10, type=float, help='maximum length of DQ and DQS wires from PHY I/O to DRAM I/O')
            parser.add_argument('--omc-freq-ratio', default=2, type=int, help='Clock ratio of dfi_clk and memory clock in terms of OMC')
            parser.add_argument('--phy-freq-ratio', default=4, type=int, help='Clock ratio of dfi_clk and memory clock in terms of PHY')
            parser.add_argument('--meso-synchronizer', default=True, action='store_true', help='meso-synchronizer is implemented')
            parser.add_argument('--pl-en', default=0, type=int, help='parity latency enable')
            parser.add_argument('--wdqs-ctrl-mode', default=1, type=int, help='Enable WDQS control mode')
            parser.add_argument('--lpddr4-byte-mode', default=0, type=int, help='Enable lpddr4 Byte mode (LPDDR4 only)')
            parser.add_argument('--sec-lpddr4-byte-mode', default=0, type=int, help='Secondary Enable lpddr4 Byte mode (LPDDR4 only)')
            parser.add_argument('--periods', default=469, type=int, nargs='+', help='list of target clock period of DRAM as pico-seconds')


            # Timing parameter for primary dram and secondary dram.
            # dmc_list = ['primary', 'secondary']

            # generate timing parameter for both primary and secondary dmc.
            # for dmc in dmc_list:

            args = parser.parse_args()

            # get option from dram parameter and give ti to args.type variable.
            # speed
            freq = int(speed/2)
            t_ck = int(((float(1)/float(freq))*float(1000000)))
            args.periods=[t_ck]

            # robust dqs mode
            args.wdqs_ctrl_mode = robust_dqs_mode

            # Byte mode timing parameter for both primary and secondary
            if dmc == 'primary':
                args.lpddr4_byte_mode = byte_mode
            elif dmc == 'secondary':
                args.lpddr4_byte_mode = sec_byte_mode

            # fixed option
            args.meso_synchronizer = meso_synchronizer
            args.phy_freq_ratio = phy_freq_ratio
            args.pipe_depth = pipe_depth

            WODT = 1
            NO_WODT = 0

            memcfgs = []

            if args.dram_type in ('lpddr3', 'ddr3', 'ddr4') and 'dq_width' not in args:
                parser.error('DQ width of each device should be specified if type of DRAM is DDR3 or DDR4')

            p_t_xsr = OrderedDict()
        #    p_t_refdpr = OrderedDict()

            if args.dram_type == 'lpddr4':
                if args.lpddr4_byte_mode == 0:
                    memcfgs.append(Memcfg( 10,100000,  266, 3750,  6,  6,  4, -1, -1))
                    memcfgs.append(Memcfg( 266, 3750,  533, 1875, 10, 12,  6, -1, -1))
                    memcfgs.append(Memcfg( 533, 1875,  801, 1250, 14, 16,  8, -1, -1))
                    memcfgs.append(Memcfg( 801, 1250, 1068,  938, 20, 22, 10,  4, 20))
                # 2400 Timing setting
                    memcfgs.append(Memcfg(1068,  938, 1200,  833, 24, 28, 12,  4, 22))
                # 2400 Timing setting, WL is 4264
                    # memcfgs.append(Memcfg(1068,  938, 1200,  833, 24, 28, 18,  4, 22))
                # 4264 Timing setting
                    # memcfgs.append(Memcfg(1068,  938, 1200,  833, 36, 40, 18,  8, 28))
                    memcfgs.append(Memcfg(1200,  833, 1336,  750, 24, 28, 12,  4, 22))
                    memcfgs.append(Memcfg(1336,  750, 1602,  625, 28, 32, 14,  6, 24))
                    memcfgs.append(Memcfg(1602,  625, 1872,  535, 32, 36, 16,  6, 26))
                    memcfgs.append(Memcfg(1872,  535, 2133,  468, 36, 40, 18,  8, 28))
                else:
                    memcfgs.append(Memcfg( 10,100000,  266, 3750,  6,  6,  4, -1, -1))
                    memcfgs.append(Memcfg( 266, 3750,  533, 1875, 10, 12,  6, -1, -1))
                    memcfgs.append(Memcfg( 533, 1875,  801, 1250, 16, 18,  8, -1, -1))
                    memcfgs.append(Memcfg( 801, 1250, 1068,  938, 22, 24, 10,  4, 20))
                    memcfgs.append(Memcfg(1068,  938, 1200,  833, 26, 30, 12,  4, 22))
                    memcfgs.append(Memcfg(1200,  833, 1336,  750, 26, 30, 12,  4, 22))
                    memcfgs.append(Memcfg(1336,  750, 1602,  625, 32, 36, 14,  6, 24))
                    memcfgs.append(Memcfg(1602,  625, 1872,  535, 36, 40, 16,  6, 26))
                    memcfgs.append(Memcfg(1872,  535, 2133,  468, 40, 44, 18,  8, 28))

                if args.densities:
                    densities = args.densities
                else:
                    densities = (2, 3, 4, 6, 8, 12, 16)

                p_t_rfcpb = OrderedDict(sorted({
                     2: Timing( 60,0,0),
                     3: Timing( 90,0,0),
                     4: Timing( 90,0,0),
                     6: Timing(140,0,0),
                     8: Timing(140,0,0),
                    12: Timing(190,0,0),
                    16: Timing(190,0,0),
                }.items()))

                p_t_rfcab = OrderedDict(sorted({
                     2: Timing(130,0,0),
                     3: Timing(180,0,0),
                     4: Timing(180,0,0),
                     6: Timing(280,0,0),
                     8: Timing(280,0,0),
                    12: Timing(380,0,0),
                    16: Timing(380,0,0),
                }.items()))

                p_t_pbr2pbr = OrderedDict(sorted({
                     2: Timing(60, 0, 0),
                     3: Timing(60, 0, 0),
                     4: Timing(90, 0, 0),
                     6: Timing(90, 0, 0),
                     8: Timing(90, 0, 0),
                     12: Timing(90, 0, 0),
                     16: Timing(90, 0, 0),
                }.items()))

                p_t_xsr_add = Timing(7.5, 2, 0)
                for d in densities:
                    p_t_xsr[d] = p_t_rfcab[d] + p_t_xsr_add;
        #            p_t_refdpr[d] = p_t_rfcab[d]/2

                if int(args.speed_bin) >= 4266:
                    p_t_rrd = Timing(7.5, 4, 0)
                    p_t_faw = Timing(30, 0, 0)
                else:
                    p_t_rrd = Timing(10, 4, 0)
                    p_t_faw = Timing(40, 0, 0)

                p_t_rppb = Timing(18, 4, 0)
                p_t_rpab = Timing(21, 4, 0)
                p_t_cke = Timing(7.5, 4, 0)
                p_t_cmdcke = Timing(1.75, 3, 0)
                p_t_ckesr = Timing(15, 3, 0)
                p_t_ckelck = Timing(5.0, 5, 0)
                p_t_xp = Timing(7.5, 5, 0)
                p_t_ras = Timing(42, 3, 0)
        #        p_t_rc = p_t_ras+p_t_rppb
                p_t_rc = Timing(p_t_ras.min_ns+p_t_rppb.min_ns, 7, 0)
                p_t_rtp = Timing(7.5, 8, 0)
                p_t_rcd = Timing(18, 4, 0)

                if args.lpddr4_byte_mode == 0:
                    p_t_wr = Timing(18, 6, 0)
                    p_t_wtr = Timing(10, 8, 0)
                else:
                    p_t_wr = Timing(20, 6, 0)
                    p_t_wtr = Timing(12, 8, 0)

                p_t_mrw = Timing(10, 10, 0)
                p_t_mrd = Timing(14, 10, 0)
                p_t_mrr = Timing(0, 8, 0)
                p_t_rcd_derate = p_t_rcd + 1.875
                p_t_rc_derate = p_t_rc + 3.7
                p_t_ras_derate = p_t_ras + 1.875
                p_t_rrd_derate = p_t_rrd + 1.875
                p_t_rpab_derate = p_t_rpab + 1.875
                p_t_rppb_derate = p_t_rppb + 1.875
                p_t_zqreset = Timing(50, 3, 0)
                p_t_zqcs = Timing(90, 0, 0)
                p_t_zqcl = Timing(30, 8, 0)
                p_t_dqsckmax = Timing(3.5, 0, 0)
                p_t_dqsckmin = Timing(1.5, 0, 0)
                p_t_dqsck_r2r = Timing(2.0, 0, 0)
                p_t_odtonmax = Timing(3.5, 0, 0)
                p_t_odtonmin = Timing(1.5, 0, 0)
                p_t_odtoffmax = Timing(3.5, 0, 0)
                p_t_odtoffmin = Timing(1.5, 0, 0)
                p_t_vref_ca = Timing(250, 0, 0)

                t_wpre = 2
                t_rpre = 2
                t_dqss = 1
                t_ccdmw = 32

                rd_pst = 0
                wr_pst = 0

                dll_enable = 0
                bl = 16;


            # c_values = []
            # t_param_prim = []
            # t_param_sec = []

            for t_ck in args.periods:
                t_ck_ns = t_ck/1000

                # FIXME only for LPDDR4
                #p_t_wr_p   = p_t_wr_pd_pre + 0.25*t_ck # 0.25*tCK from tDQSS
                #p_t_wr_p   = p_t_wr_p_pre # 0.25*tCK from tDQSS

                memcfg = search_memcfgs(memcfgs, t_ck)
                freq = int(1000000/t_ck)

                # User select read_dbi option
                # read_dbi = args.dram_type in ('ddr4', 'lpddr4') and args.read_dbi_upto >= t_ck
                # read_dbi = args.dram_type in ('ddr4', 'lpddr4')

                # User select rpste and wpste
                # rpste = args.rpste_upto >= t_ck
                # wpste = args.wpste_upto >= t_ck

                read_latency = memcfg.rl_dbi if read_dbi else memcfg.rl
                write_latency = memcfg.wl

                if args.dram_type == 'ddr4':
                    if args.pl_en == 1:
                        if t_ck >= 937:
                            pl = 4
                        elif t_ck >= 750:
                            pl = 5
                        else:
                            pl = 6
                    else:
                        pl = 0
                else:
                    pl = 0
                read_latency_pl = read_latency + pl
                write_latency_pl = write_latency + pl

                pipe_freq_ratio = 2
                if args.phy_name in ('sphy-v5', 'sphy-v6r3', 'sphy-v8'):
                    trddata_en = read_latency_pl + (p_t_dqsckmax
                                              + 0.350
                                              + 0.07*args.wire_length
                                              + 0.04
                                              + 0.07*args.wire_length
                                              + 0.072
                                              + 2.53
                                              + (0.25+args.phy_freq_ratio)*t_ck/1000).calc_ceil(t_ck) - args.pipe_depth*2

                    #if args.dram_type == 'lpddr4':
                    #    trddata_en += 1
                    #    trddata_en += trddata_en%args.phy_freq_ratio
                    #    trddata_en -= 1
                    #else:
                    #    trddata_en += trddata_en%args.phy_freq_ratio
                    if args.dram_type == 'lpddr4':
                        if args.phy_freq_ratio == 2:
                            trddata_en += 1
                            trddata_en += trddata_en%args.phy_freq_ratio
                            trddata_en -= 1
                        else:
                            trddata_en += 1 if trddata_en%2 == 0 else 0
                            trddata_en += trddata_en%args.phy_freq_ratio
                            trddata_en -= 1
                    else:
                        trddata_en += trddata_en%args.phy_freq_ratio
                    tphy_rdlat   = 4
                    tphy_wrdata  = args.phy_freq_ratio
                    tphy_wrlat = max(memcfg.wl + 1 - tphy_wrdata - args.pipe_depth*2,0)


                twrdata_delay = args.pipe_depth*2*pipe_freq_ratio + (32 if args.dram_type == 'lpddr4' else 8)//2 + (wr_pst+1) + tphy_wrdata
                if not args.phy_freq_ratio == args.omc_freq_ratio:
                    twrdata_delay += args.omc_freq_ratio
                if args.meso_synchronizer:
                    twrdata_delay += 4*args.phy_freq_ratio

                if args.phy_name in ('sphy-v5', 'sphy-v6r3', 'sphy-v8'):
                    twrdata_delay += 4

                t_rfcpb = OrderedDict()
                t_rfcab = OrderedDict()
                t_refdpr = OrderedDict()
                t_pbr2pbr = OrderedDict()
                t_xsr = OrderedDict()
                t_xsdll = OrderedDict()
                t_xs_fast = OrderedDict()

                if args.lp4_micron_org == 1 and args.dram_type == 'lpddr4':
                    if int(args.speed_bin) >= 4266:
                        if t_ck >= 535:
                            p_t_rrd = Timing(10, 4, 0)
                            p_t_faw = Timing(40, 0, 0)
                        else:
                            p_t_rrd = Timing(7.5, 4, 0)
                            p_t_faw = Timing(30, 0, 0)
                    else:
                        p_t_rrd = Timing(10, 4, 0)
                        p_t_faw = Timing(40, 0, 0)
                    p_t_rrd_derate = p_t_rrd + 1.875

                    p_t_xsr_add2 = Timing(t_ck_ns*2, 0, 0)
                    for d in densities:
                        p_t_xsr[d] = p_t_xsr[d] + p_t_xsr_add2;

                for d in densities:
                    t_rfcab[d] = p_t_rfcab[d].calc_ceil(t_ck)
                    t_xsr  [d] = p_t_xsr  [d].calc_ceil(t_ck)
        #            t_refdpr[d] = p_t_refdpr[d].calc_ceil(t_ck)
                    t_refdpr[d] = t_rfcab[d]//2
                    t_rfcpb[d] = 0
                    t_pbr2pbr[d] = p_t_pbr2pbr[d].calc_ceil(t_ck)
                    t_xsdll[d] = 0
                    t_xs_fast[d] = 0
                    if t_refdpr[d] > 255:
                        t_refdpr[d] = 255
                    elif t_refdpr[d] < 10:
                        t_refdpr[d] = 0
                    else:
                        t_refdpr[d] -= 10

                t_rppb = p_t_rppb.calc_ceil(t_ck)
                t_rpab = p_t_rpab.calc_ceil(t_ck)
                t_cke = p_t_cke.calc_ceil(t_ck)
                t_cmdcke = p_t_cmdcke.calc_ceil(t_ck)
                t_ckelck = p_t_ckelck.calc_ceil(t_ck)
                t_xp = p_t_xp.calc_ceil(t_ck)
                t_rc = p_t_rc.calc_ceil(t_ck)
                t_ras = p_t_ras.calc_ceil(t_ck)
                t_rtp = p_t_rtp.calc_ceil(t_ck)
                t_rcd = p_t_rcd.calc_ceil(t_ck)
                t_wr = p_t_wr.calc_ceil(t_ck)
                t_rrd = p_t_rrd.calc_ceil(t_ck)
                t_faw = p_t_faw.calc_ceil(t_ck)
                t_mrw = p_t_mrw.calc_ceil(t_ck)
                t_mrd = p_t_mrd.calc_ceil(t_ck)
                t_mrd_pl = t_mrd + pl;
                t_rtrcr = p_t_dqsck_r2r.calc_ceil(t_ck) + t_rpre + rpste
                t_zqcs = p_t_zqcs.calc_ceil(t_ck)
                t_zqcl = p_t_zqcl.calc_ceil(t_ck)

                t_rtw = [0 for x in range(2)]
                t_wtwcr = [0 for x in range(2)]

                if args.dram_type == 'lpddr4':
                    p_t_ckckeh = Timing(1.75 + t_ck_ns,  3, 0)
        #            p_t_wr_p = p_t_wr + 0.25*t_ck_ns+0.8
                    p_t_wr_p = Timing(p_t_wr.min_ns + 0.25*t_ck_ns+0.8,6,0)
                    p_n_wr_p = Timing(0.25*t_ck_ns+0.8, 0, 0)
                    p_t_tmp = Timing(7.5, 8, 0)

                    t_cmdcke = p_t_cmdcke.calc_ceil(t_ck)
                    t_ckesr = p_t_ckesr.calc_ceil(t_ck)
                    t_ckckeh = p_t_ckckeh.calc_ceil(t_ck)
                    t_mrr = p_t_mrr.calc_ceil(t_ck)
                    t_rcd_derate = p_t_rcd_derate.calc_ceil(t_ck)
                    t_rc_derate = p_t_rc_derate.calc_ceil(t_ck)
                    t_ras_derate = p_t_ras_derate.calc_ceil(t_ck)
                    t_rrd_derate = p_t_rrd_derate.calc_ceil(t_ck)
                    t_rpab_derate = p_t_rpab_derate.calc_ceil(t_ck)
                    t_rppb_derate = p_t_rppb_derate.calc_ceil(t_ck)
                    t_zqreset = p_t_zqreset.calc_ceil(t_ck)
                    t_dqsckmax = p_t_dqsckmax.calc_ceil(t_ck)
                    t_dqsckmin = p_t_dqsckmin.calc_floor(t_ck)
                    t_vref_ca = p_t_vref_ca.calc_ceil(t_ck)

                    for d in densities:
                        if args.project_name == 'techwin-wn7':
                            t_xsr[d] += 3
                            t_rfcab[d] += 2
                        t_rfcpb[d] = p_t_rfcpb[d].calc_ceil(t_ck)
                        t_pbr2pbr[d] = t_rfcpb[d] - t_pbr2pbr[d]
        #                # un-used parameters
        #                t_xsdll[d] = 0
        #                t_xs_fast[d] = 0
        #                t_pbr2pbr[d] = 0

                    t_rtw[WODT] = read_latency + p_t_dqsckmax.calc_ceil(t_ck) + bl//2 + rd_pst - memcfg.odtlon - p_t_odtonmin.calc_floor(t_ck) + 1
                    t_rtw[NO_WODT] = read_latency + p_t_dqsckmax.calc_ceil(t_ck) + bl//2 + rd_pst - write_latency + 2

                    ## memcfg.odtloff and memcfg.odtlon value is N/A when speed is below 1600 Mbps.
                    ## Hence, we set wtwcr value based on TCC803x history.
                    if speed <= 1602:
                        t_wtwcr[WODT] = 8
                    else:
                        t_wtwcr[WODT] =  memcfg.odtloff - memcfg.odtlon - bl//2
                    t_wtwcr[NO_WODT] = 8

                    if args.phy_name.startswith('sphy-v8'):
                        readduradj = 7 if t_ck < 937 else 5
                        if args.wdqs_ctrl_mode:
                            # t_rtw[WODT] = t_rtw[WODT] + readduradj + 8 - p_t_dqsckmax.calc_ceil(t_ck)
                            t_rtw[WODT] = t_rtw[WODT] + readduradj + 12 - p_t_dqsckmax.calc_ceil(t_ck)
                            # t_rtw[WODT] = t_rtw[WODT] + readduradj + 16 - p_t_dqsckmax.calc_ceil(t_ck)
                            # t_rtw[WODT] = t_rtw[WODT] + readduradj + 22 - p_t_dqsckmax.calc_ceil(t_ck)
                            # t_rtw[WODT] = t_rtw[WODT] + readduradj + 60 - p_t_dqsckmax.calc_ceil(t_ck)
                            t_rtw[NO_WODT] = t_rtw[NO_WODT] + readduradj + 12 - p_t_dqsckmax.calc_ceil(t_ck)
                        elif readduradj + 4 > p_t_dqsckmax.calc_ceil(t_ck):
                            t_rtw[WODT] = t_rtw[WODT] + readduradj + 4 - p_t_dqsckmax.calc_ceil(t_ck)
                            t_rtw[NO_WODT] = t_rtw[NO_WODT] + readduradj + 4 - p_t_dqsckmax.calc_ceil(t_ck)

                    t_rdidle = read_latency + p_t_dqsckmax.calc_ceil(t_ck) + bl//2 + rd_pst + p_t_tmp.calc_ceil(t_ck);
                    t_rtrrd = t_rdidle

                    t_wtr_a = write_latency + 1 + bl//2 + p_t_wtr.calc_ceil(t_ck)
                    t_wtrcr = max(write_latency - read_latency + 1 + bl//2 + wr_pst + 2 + (Timing(t_ck_ns*0.25,0,0) - p_t_dqsckmin).calc_ceil(t_ck), 0)

                    t_wr_a = write_latency + 1 + bl//2 + t_wr
                    t_wr_p = write_latency + 1 + bl//2 + p_t_wr_p.calc_ceil(t_ck)
                    t_wrwtr = write_latency + 1 + bl//2 + p_t_tmp.calc_ceil(t_ck)
                    t_xp_mrri = t_xp + t_rcd + 3

                    mr_rl = lpddr4_encode_rl(read_latency, read_dbi, args.lpddr4_byte_mode)
                    mr_wl = lpddr4_encode_wl(memcfg.wl)
                    mr_wr = mr_rl
                    n_wr = lpddr4_decode_wr(mr_wr, args.lpddr4_byte_mode)
                    n_rtp = lpddr4_decode_rtp(mr_rl)

                    n_wr_a = write_latency + 1 + bl//2 + n_wr
                    n_wr_p = write_latency + 1 + bl//2 + p_n_wr_p.calc_ceil(t_ck) + n_wr + 2

                    # Not used parameters
                    mr_tccd_l = 0
                    mr_cal = 0
                    t_zqinit = 0
                    t_wtr_a_l = 0
                    t_rrd_l = 0
                    t_ccd_l = 0
                    t_sync_gear = 0
                    t_cmd_gear = 0
                    odtl_on = 0
                    odtl_off = 0


                timing_param = [0 for x in range(14)]
                timing_param[0] = (t_cmdcke  << T_CMDCKE_SHIFT |
                                   t_ckckeh  << T_CKCKEH_SHIFT |
                                   t_rppb    << T_RPPB_SHIFT   |
                                   t_rpab    << T_RPAB_SHIFT   )
                timing_param[1] = (t_cke     << T_CKE_SHIFT    |
                                   t_ckesr   << T_CKESR_SHIFT  |
                                   t_ckelck  << T_CKELCK_SHIFT |
                                   t_xp      << T_XP_SHIFT     )
                timing_param[2] = (t_rc      << T_RC_SHIFT     |
                                   t_ras     << T_RAS_SHIFT    |
                                   t_rtp     << T_RTP_SHIFT    |
                                   0         << ADV_AL_SHIFT   |
                                   t_rcd     << T_RCD_SHIFT    )
                timing_param[3] = (t_wr_a    << T_WR_A_SHIFT   |
                                   t_wtr_a   << T_WTR_A_SHIFT  |
                                   t_rrd     << T_RRD_SHIFT    |
                                   t_faw     << T_FAW_SHIFT    )
                timing_param[4] = (t_rtrrd   << T_RTRRD_SHIFT         |
                                   t_wrwtr   << T_WRWTR_SHIFT         |
                                   read_latency_pl << T_READ_LATENCY_SHIFT  |
                                   write_latency_pl << T_WRITE_LATENCY_SHIFT )
        #                           read_latency << T_READ_LATENCY_SHIFT  |
        #                           memcfg.wl << T_WRITE_LATENCY_SHIFT )
                timing_param[5] = 0
                timing_param[6] = (t_ccdmw << T_CCDMW_SHIFT |
                                   t_mrd_pl   << T_MRW_SHIFT   |
                                   t_mrd_pl   << T_MRD_SHIFT   |
                                   t_mrr   << T_MRR_SHIFT   )
                timing_param[7] = (t_rdidle          << T_RDIDLE_SHIFT   |
                                   max(n_wr_p - n_wr_a, 0) << N_ADD_WR_P_SHIFT |
                                   max(t_wr_p - t_wr_a, 0) << T_ADD_WR_P_SHIFT |
                                   #t_wtwcr           << T_WTWCR          |
                                   t_rtrcr           << T_RTRCR_SHIFT    )
                timing_param[8] = (#t_xsr << T_XSR_SHIFT # density
                                   t_xp_mrri << T_XP_MRRI_SHIFT )
                                   #t_refdpr  << T_REFDPR_SHIFT # density
                timing_param[9] = (t_wtrcr << T_WTRCR_SHIFT)
                timing_param[10] = 0#(t_xsdll   << T_XSDLL_SHIFT   |
                                    #t_xs_fast << T_XS_FAST_SHIFT |
                                    #t_pbr2pbr << T_PBR2PBR_SHIFT )
                timing_param[11] = (n_rtp  << N_RTP_SHIFT  |
                                    n_wr_a << N_WR_A_SHIFT |
                                    n_wr   << N_WR_SHIFT   )
                timing_param[12] = (t_wtr_a_l << T_WTR_A_L_SHIFT |
                                    t_rrd_l   << T_RRD_L_SHIFT   |
                                    t_ccd_l   << T_CCD_L_SHIFT   )
                timing_param[13] = (t_sync_gear  << T_SYNC_GEAR_SHIFT  |
                                    t_cmd_gear   << T_CMD_GEAR_SHIFT   )
                timing_param_derate = [0 for x in range(2)]
                timing_param_derate[0] = (t_rcd_derate << T_RCD_DERATE_SHIFT |
                                          t_rc_derate  << T_RC_DERATE_SHIFT  |
                                          t_ras_derate << T_RAS_DERATE_SHIFT |
                                          t_rrd_derate << T_RRD_DERATE_SHFIT )
                timing_param_derate[1] = (t_rppb_derate << T_RPPB_DERATE_SHIFT |
                                          t_rpab_derate << T_RPAB_DERATE_SHIFT )

                timing_zqcal = [0 for x in range(1)]
                #timing_zqcal[0] = (t_zqreset << T_ZQRESET_SHIFT |
                #                   t_zqinit  << T_ZQINIT_SHIFT  )
                timing_zqcal[0] = (t_zqcs << T_ZQCS_SHIFT |
                                   t_zqcl << T_ZQCL_SHIFT )

                # c_value = '''{{{freq:d},

                if dmc == 'primary':
                        t_param_prim = '''{{{freq:d},
                          {t_ck:d},
                          {{{timing_param:s}}},
                          {{{timing_derate:s}}},
                          {{{timing_zqcal:s}}},
                          {{{t_rfcab:s}}},
                          {{{t_rfcpb:s}}},
                          {{{t_refdpr:s}}},
                          {{{t_pbr2pbr:s}}},
                          {{{t_xsr:s}}},
                          {{{t_xsdll:s}}},
                          {{{t_xs_fast:s}}},
                          {trddata_en:d},
                          {tphy_rdlat:d},
                          {tphy_wrlat:d},
                          {tphy_wrdata:d},
                          {twrdata_delay:d},
                          {{{t_wtwcr:s}}},
                          {{{t_rtw:s}}},
                          {dll_enable:d},
                          {read_dbi:d},
                          {wpste:d},
                          {wpste:d},
                          {rl:d},
                          {wl:d},
                          {mr_rl:d},
                          {mr_wl:d},
                          {mr_wr:d},
                          {mr_rtp:d},
                          {mr_cal:d},
                          {mr_tccd_l:d}
                        }}'''.format(
                          freq=freq,
                          t_ck=t_ck,
                          dll_enable=dll_enable,
                          read_dbi=read_dbi,
                          wpste=wpste,
                          rpste=rpste,
                          timing_param=', '.join(['0x{:08x}'.format(x) for x in timing_param]),
                          timing_derate=', '.join(['0x{:08x}'.format(x) for x in timing_param_derate]),
                          timing_zqcal=', '.join(['0x{:08x}'.format(x) for x in timing_zqcal]),
                          trddata_en=trddata_en,
                          tphy_rdlat=tphy_rdlat,
                          tphy_wrlat=tphy_wrlat,
                          tphy_wrdata=tphy_wrdata,
                          twrdata_delay=twrdata_delay,
                          t_wtwcr=', '.join(['{:d}'.format(x) for x in t_wtwcr]),
                          t_rtw=', '.join(['{:d}'.format(x) for x in t_rtw]),
                          t_rfcab=', '.join(['{:d}'.format(x) for x in t_rfcab.values()]),
                          t_rfcpb=', '.join(['{:d}'.format(x) for x in t_rfcpb.values()]),
                          t_refdpr=', '.join(['{:d}'.format(x) for x in t_refdpr.values()]),
                          t_pbr2pbr=', '.join(['{:d}'.format(x) for x in t_pbr2pbr.values()]),
                          t_xsr=', '.join(['{:d}'.format(x) for x in t_xsr.values()]),
                          t_xsdll=', '.join(['{:d}'.format(x) for x in t_xsdll.values()]),
                          t_xs_fast=', '.join(['{:d}'.format(x) for x in t_xs_fast.values()]),
                          rl=read_latency_pl,
                          wl=memcfg.wl,
                          mr_rl=mr_rl,
                          mr_wl=mr_wl,
                          mr_wr=mr_wr,
                          mr_rtp=mr_wr,
                          mr_cal=mr_cal,
                          mr_tccd_l=mr_tccd_l
                        )
                elif dmc == 'secondary':
                        t_param_sec = '''{{{freq:d},
                          {t_ck:d},
                          {{{timing_param:s}}},
                          {{{timing_derate:s}}},
                          {{{timing_zqcal:s}}},
                          {{{t_rfcab:s}}},
                          {{{t_rfcpb:s}}},
                          {{{t_refdpr:s}}},
                          {{{t_pbr2pbr:s}}},
                          {{{t_xsr:s}}},
                          {{{t_xsdll:s}}},
                          {{{t_xs_fast:s}}},
                          {trddata_en:d},
                          {tphy_rdlat:d},
                          {tphy_wrlat:d},
                          {tphy_wrdata:d},
                          {twrdata_delay:d},
                          {{{t_wtwcr:s}}},
                          {{{t_rtw:s}}},
                          {dll_enable:d},
                          {read_dbi:d},
                          {wpste:d},
                          {wpste:d},
                          {rl:d},
                          {wl:d},
                          {mr_rl:d},
                          {mr_wl:d},
                          {mr_wr:d},
                          {mr_rtp:d},
                          {mr_cal:d},
                          {mr_tccd_l:d}
                        }}'''.format(
                          freq=freq,
                          t_ck=t_ck,
                          dll_enable=dll_enable,
                          read_dbi=read_dbi,
                          wpste=wpste,
                          rpste=rpste,
                          timing_param=', '.join(['0x{:08x}'.format(x) for x in timing_param]),
                          timing_derate=', '.join(['0x{:08x}'.format(x) for x in timing_param_derate]),
                          timing_zqcal=', '.join(['0x{:08x}'.format(x) for x in timing_zqcal]),
                          trddata_en=trddata_en,
                          tphy_rdlat=tphy_rdlat,
                          tphy_wrlat=tphy_wrlat,
                          tphy_wrdata=tphy_wrdata,
                          twrdata_delay=twrdata_delay,
                          t_wtwcr=', '.join(['{:d}'.format(x) for x in t_wtwcr]),
                          t_rtw=', '.join(['{:d}'.format(x) for x in t_rtw]),
                          t_rfcab=', '.join(['{:d}'.format(x) for x in t_rfcab.values()]),
                          t_rfcpb=', '.join(['{:d}'.format(x) for x in t_rfcpb.values()]),
                          t_refdpr=', '.join(['{:d}'.format(x) for x in t_refdpr.values()]),
                          t_pbr2pbr=', '.join(['{:d}'.format(x) for x in t_pbr2pbr.values()]),
                          t_xsr=', '.join(['{:d}'.format(x) for x in t_xsr.values()]),
                          t_xsdll=', '.join(['{:d}'.format(x) for x in t_xsdll.values()]),
                          t_xs_fast=', '.join(['{:d}'.format(x) for x in t_xs_fast.values()]),
                          rl=read_latency_pl,
                          wl=memcfg.wl,
                          mr_rl=mr_rl,
                          mr_wl=mr_wl,
                          mr_wr=mr_wr,
                          mr_rtp=mr_wr,
                          mr_cal=mr_cal,
                          mr_tccd_l=mr_tccd_l
                        )

            # freq = int(speed/2)
            # t_ck = int(((float(1)/float(freq))*float(1000000)))
            temp_list = [freq, t_ck, dll_enable, read_dbi, write_dbi, wpste, rpste, trddata_en, tphy_rdlat, tphy_wrlat, tphy_wrdata, twrdata_delay, read_latency_pl, memcfg.wl, mr_rl, mr_wl, mr_wr, mr_cal, mr_tccd_l]


            temp_list2 = []
            temp_list2 = timing_param + timing_param_derate + timing_zqcal + t_wtwcr + t_rtw

            # concatenate list1 and list2
            # c_values = temp_list + temp_list2
            if dmc == 'primary':
                    t_param_prim = temp_list + temp_list2
            elif dmc == 'secondary':
                    t_param_sec = temp_list + temp_list2


            # values() append
            temp_list3 = []
            for x in t_rfcab.values():
                temp_list3.append(x)

            # c_values = c_values + temp_list3
            if dmc == 'primary':
                    t_param_prim = t_param_prim + temp_list3
            elif dmc == 'secondary':
                    t_param_sec = t_param_sec + temp_list3


            # values() append
            temp_list3 = []
            for x in t_rfcpb.values():
                temp_list3.append(x)

            # c_values = c_values + temp_list3
            if dmc == 'primary':
                    t_param_prim = t_param_prim + temp_list3
            elif dmc == 'secondary':
                    t_param_sec = t_param_sec + temp_list3

            # values() append
            temp_list3 = []
            for x in t_refdpr.values():
                temp_list3.append(x)

            # c_values = c_values + temp_list3
            if dmc == 'primary':
                    t_param_prim = t_param_prim + temp_list3
            elif dmc == 'secondary':
                    t_param_sec = t_param_sec + temp_list3

            # values() append
            temp_list3 = []
            for x in t_pbr2pbr.values():
                temp_list3.append(x)

            # c_values = c_values + temp_list3
            if dmc == 'primary':
                    t_param_prim = t_param_prim + temp_list3
            elif dmc == 'secondary':
                    t_param_sec = t_param_sec + temp_list3

            # values() append
            temp_list3 = []
            for x in t_xsr.values():
                temp_list3.append(x)

            # c_values = c_values + temp_list3
            if dmc == 'primary':
                    t_param_prim = t_param_prim + temp_list3
            elif dmc == 'secondary':
                    t_param_sec = t_param_sec + temp_list3

            # values() append
            temp_list3 = []
            for x in t_xsdll.values():
                temp_list3.append(x)

            # c_values = c_values + temp_list3
            if dmc == 'primary':
                    t_param_prim = t_param_prim + temp_list3
            elif dmc == 'secondary':
                    t_param_sec = t_param_sec + temp_list3

            # values() append
            temp_list3 = []
            for x in t_xs_fast.values():
                temp_list3.append(x)

            # c_values = c_values + temp_list3
            if dmc == 'primary':
                    t_param_prim = t_param_prim + temp_list3
            elif dmc == 'secondary':
                    t_param_sec = t_param_sec + temp_list3

            parameters = OrderedDict({
                    'OMC_NUM_TIMING_PARAMS': 14,
                    'OMC_NUM_DERATE_PARAMS': 2,
                    'OMC_NUM_DENSITIES': len(densities),
                    'OMC_NUM_ZQ_PARAMS': 2,
                    })

# with open(args.output, 'w') as f:
    # f.write('struct timing_param_timing_params[] = {\n')
    # f.write(',\n'.join([x.replace('\n', '').replace(' ', '') for x in c_values]))
    # f.write('\n};\n')

# print(t_param_prim)
# print("\n")
# print(t_param_sec)

binfile = open('tmp_dp_in.bin', 'wb')
array = [version, speed, pll_en, pll_value, soc_dq_dds, soc_dq_odt, lpddr4_dq_dds, lpddr4_dq_odt, clock_dds, ca_dds, rank0_ca_odt, rank1_ca_odt, ca_vref, soc_vref, dram_vref, soc_vref_train, dram_vref_train, ca_delay, channel_set_en, channel_num, dram_size, place_holder, rank_num, initial_size, size_per_rank, density_per_rank, num_bg_per_rank, num_bank_per_rank, num_row_per_rank, num_col_per_rank, mr4_sensing_enable, mr4_sensing_period, t_refiab, t_refipb, robust_dqs_mode, byte_mode, rank_interleaving, rank_interleaving_size, init_zq_calibration, dynamic_power_down, dynamic_power_down_threshold, dynamic_self_refresh, dynamic_self_refresh_threshold, regional_clock_gating, phy_clock_gating, dram_clock_gating, zq_calibration, zq_calibration_period, periodic_training, periodic_training_period, extra_rtw, fixed_odt_cs, meso_synchronizer, mrr_byte_lane0, mrr_byte_lane1, rclk_t_ck, t_zqcal, adv_al, pipe_depth, phy_freq_ratio, tctrlupd_interval, lpddr4_rpre, lpddr4_wpre, reqq_depth]

# Timing parameter for Pirmary dmc.
array = array + t_param_prim

ec_array = [test_pattern_high, test_pattern_low, dchk_size, test_result, scrambler_on, fsecc_en, num_of_ecc_region, ecc_region0_base_low, ecc_region0_base_high, ecc_region1_base_low, ecc_region1_base_high, ecc_region2_base_low, ecc_region2_base_high, ecc_region3_base_low, ecc_region3_base_high, ecc_region4_base_low, ecc_region4_base_high, ecc_region5_base_low, ecc_region5_base_high, ecc_region6_base_low, ecc_region6_base_high, ecc_region7_base_low, ecc_region7_base_high, ecc_region0_top_low, ecc_region0_top_high, ecc_region1_top_low, ecc_region1_top_high, ecc_region2_top_low, ecc_region2_top_high, ecc_region3_top_low, ecc_region3_top_high, ecc_region4_top_low, ecc_region4_top_high, ecc_region5_top_low, ecc_region5_top_high, ecc_region6_top_low, ecc_region6_top_high, ecc_region7_top_low, ecc_region7_top_high]

array = array + ec_array

array_add = [omc_dqs_delay_en, omc0_byte0_dqs_delay, omc0_byte1_dqs_delay, omc1_byte0_dqs_delay, omc1_byte1_dqs_delay, omc2_byte0_dqs_delay, omc2_byte1_dqs_delay, omc3_byte0_dqs_delay, omc3_byte1_dqs_delay, write_leveling]

array = array + array_add

array_add = [membus_pll_en, membus_pll_val, membus_speed, memcore_div, memsub_div, lpddr4_peri_div, lpddr4_user_div]

array = array + array_add

array_add = [qos_cfg0_en, qos_cfg1_en, qos_cfg2_en, qos_cfg3_en, qos_cfg0_val, qos_cfg1_val, qos_cfg2_val, qos_cfg3_val]

array = array + array_add

array_add = [rank0_ca_odt_cfg, rank1_ca_odt_cfg, dmc_init_cfg, sec_byte_mode, prim_ck_delay, sec_ck_delay]

array = array + array_add

# Additional config
array_add = [adv_target_ref, sw_refrate, abr_en_value, abr_en_en]
array = array + array_add


# DRAM parameter pointer.
array_add = [sec_param_sentinel]

array = array + array_add

# Timing parameter for Secondary dmc
array = array + t_param_sec

# Secondary denstiy parameter
array_add = [dram_size, place_holder, rank_num, initial_size, size_per_rank,
          density_per_rank, num_bg_per_rank, num_bank_per_rank, num_row_per_rank, num_col_per_rank, mr4_sensing_enable, mr4_sensing_period, t_refiab, t_refipb, robust_dqs_mode, byte_mode, rank_interleaving, rank_interleaving_size]


array = array + array_add

# Secondary  MR paramter 
array_add = [rank0_ca_odt_cfg, rank1_ca_odt_cfg]
#
array = array + array_add

for num in array:
    data = struct.pack('I', num)
    binfile.write(data)

binfile.close()


imageversion = '0.0.0'
imageoffset = 512
targetaddress = 0
iname = 'tmp_dp_in.bin'
oname = '../../prebuilt/dram_params.bin'
# oname = 'tmp_dp_out.bin'

mkrom(oname, iname, imageversion, imageoffset, targetaddress)
os.remove("tmp_dp_in.bin")
