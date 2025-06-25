import sys
import argparse
import xml.etree.ElementTree as elemTree
from collections import OrderedDict

input_data= None
output_data = None
out_file = ""
reverse_mode = False

# indices
idx_range_start=0
idx_range_end=1

# Classes
# This is an interface for the 2 types for options.
class tag_option:
    def __init__(self, name, start_bit, end_bit, chk_validity_cb):
        self.name = name
        self.start_bit = start_bit
        self.end_bit = end_bit
        self.chk_validity_cb = chk_validity_cb

    def get_text_value(self, int_value):
        pass

    def get_int_value(self, text_value):
        pass

    def print_option(self, int_value):
        pass

# Text options have mappings between integer values in the binary file and text values in the XML file
# For example, in the 'sdmmc' tag, 'buswidth' option is represented as '8':0x2, '4':0x1, '1':0x0.
class text_option(tag_option):
    def __init__(self, name, start_bit, end_bit, text_mapping, chk_validity_cb=None):
        #super(text_option, self).__init__(name, start_bit, end_bit)
        if (chk_validity_cb == None):
            chk_validity_cb = self.text_opt_chk_validity
        tag_option.__init__(self, name, start_bit, end_bit, chk_validity_cb)
        self.text_mapping = text_mapping

    # if you want to add chk_validity_cb function to text_option, you should define a function and pass it to the last parameter of the initializer for each option
    # for example,
    #def chk_opmode_option(self, val):
    #    if (val in self.text_mapping): # Check if 'val' as a key is in the text_mapping which maps the valid keys to valid integer values
    #        return True
    #    else:
    #        return False
    #ufs_tag.options.append(text_option('opmode', 0, 0, {'pio':0, 'dma':1}, chk_opmode_option)) # and pass the defined funtion to initializer of the option
    def text_opt_chk_validity(self, val):
        ret = None
        if (type(val) == str):
            ret = self.get_int_value(val)
        else:
            ret = self.get_text_value(val)

        if (ret == None):
            return False
        else:
            return True

    def get_text_value(self, int_value):
        for text, (desc, val) in self.text_mapping.items():
            if (val == int_value):
                return text
        return None

    def get_int_value(self, text_value):
        for text, (desc, val) in self.text_mapping.items():
            if (text == text_value):
                return val
        return None

    def print_option(self, int_value):
        for text, (desc, val) in self.text_mapping.items():
            if (val == int_value):
                return desc

        return desc

# Range options are limited in their own range
# For example, in the 'scfw/mmc' tag, 'speed' option has its own range(maybe 0~0xff?).
class range_option(tag_option):
    def __init__(self, name, start_bit, end_bit, value_range, chk_validity_cb=None):
        #super(range_option, self).__init__(name, start_bit, end_bit)
        if (chk_validity_cb == None):
            chk_validity_cb = self.range_opt_chk_validity
        tag_option.__init__(self, name, start_bit, end_bit, chk_validity_cb)
        self.value_range = value_range

    # if you want to add chk_validity_cb function to range_option, you should define a function and pass it to the last parameter of the initializer for each option
    # for example,
    #def chk_speed_option(self, val):
    #    if (val >= 0 and val >= self.value_range[idx_range_start] and value <= self.value_range[idx_range_end]): # Check if 'val' is in the valid range which you want
    #        return True
    #    else:
    #        return False
    #scfw_mmc_tag.options.append(range_option('speed', 0, 7, (0, 0xff), chk_speed_option)) # and pass the defined funtion to initializer of the option
    def range_opt_chk_validity(self, val):
        ret = None
        if (type(val) == str):
            ret = self.get_int_value(val)
        else:
            ret = self.get_text_value(val)

        if (ret == None):
            return False
        else:
            return True

    def get_text_value(self, int_value):
        #print("\'" + self.name + "\'" + " tag range: (" + str(self.value_range[idx_range_start]) + ", " + str(self.value_range[idx_range_end]) + ")")
        if (int_value >= self.value_range[idx_range_start] and int_value <= self.value_range[idx_range_end]):
                return str(int_value)
        return None

    def get_int_value(self, text_value):
        int_value = int(text_value)
        if (int_value >= self.value_range[idx_range_start] and int_value <= self.value_range[idx_range_end]):
                return int_value
        return None

    def print_option(self, int_value):
        return self.name + " " + str(int_value)

class bconf_tag:
    def __init__(self, name, offset, size, parent=None):
        self.name = name
        self.offset = offset
        self.size = size
        self.child_tags = []
        self.options = []
        self.parent = parent

    def find_child_tag(self, name):
        for child in self.child_tags:
            if (name == child.name):
                return child
        return None

    def find_option(self, name):
        for opt in self.options:
            if (name == opt.name):
                return opt
        return None

# Root node of the XML tree hierarchy
root_tag = bconf_tag('boot_config_data', -1, -1)

# Global Utility Functions
def print_xml_head():
    global output_data

    output_data = "<?xml version=\"1.0\" encoding=\"UTF-8\"?>\n\n"

def print_text_tag(tag, level):
    global input_data, output_data

    for i in range(level):
        output_data += "\t"

    output_data += ("<" + tag.name)

    whole_val = 0
    shift = 0
    # Because the input_data is just a byte array and it is not possible to cast it to an integer value,
    # we should read the value of tag.size bytes from tag.offset in the binary file.
    for i in range(tag.size):
        whole_val |= (input_data[tag.offset + i] << shift)
        shift += 8
    #print("[" + tag.name + "] " + "value: " + hex(whole_val) + ", offset: " + hex(tag.offset) + ", size: " + hex(tag.size))

    # For all options of the tag,
    for opt in tag.options:
        # filter binary value of only the option we want from the whole value of the tag
        opt_val = (whole_val >> opt.start_bit)&((1<<(opt.end_bit-opt.start_bit+1))-1)
        #print("option \'" + opt.name + "\': " + str(opt.start_bit) + ", " + str(opt.end_bit) + ", " + str(opt_val))
        output_data += " " + opt.name + "=\"" + opt.get_text_value(opt_val) + "\"" # with the value we extracted, we can achieve the text we neede for each option

    if (len(tag.child_tags) > 0): # when there is/are a child/children tag(s) of current 'tag'
        output_data += ">\n"
        for child_tag in tag.child_tags:
            print_text_tag(child_tag, level+1)

        for i in range(level):
            output_data += "\t"
        output_data += "</" + tag.name + ">\n"
    else: # when there is no child tag of current 'tag'
        output_data += "/>\n"

def print_binary_tag(node, tag):
    global output_data

    offset = tag.offset
    size = tag.size

    # make binary options
    raw = 0

    for opt_name, opt_val in node.attrib.items():
        try:
            opt = tag.find_option(opt_name)
            int_value = opt.get_int_value(opt_val)
            raw |= (int_value << opt.start_bit)
            if (tag.parent == None):
                print("%s: %s" %(tag.name, opt.print_option(int_value)))
            else:
                print("%s/%s: %s" %(tag.parent.name, tag.name, opt.print_option(int_value)))
        except:
            print("%s: invalid value '%s' for property '%s'"
                    %(tag.name, opt_val, opt_name))

    # print the binary options made above into 'boot_data' written to the 'out_file'
    if (size > 0):
        for i in range(offset, offset+size):
            output_data[i] = output_data[i] | (raw & 0xff)
            raw = raw >> 8

    for child_node in node:
        print_binary_tag(child_node, tag.find_child_tag(child_node.tag))

def build_tag_struct():
    global root_tag

    # add 'sdmmc' tag
    sdmmc_tag = bconf_tag('sdmmc', 0x10, 0x10)
    root_tag.child_tags.append(sdmmc_tag)
    # add options for 'sdmmc' tag
    sdmmc_tag.options = [
        text_option('buswidth', 0, 1, {'1':('buswidth 1', 0), '4':('buswidth 4', 1), '8':('buswidth 8', 2)}),
        text_option('speed', 2, 2, {'normal':('normal speed mode 25MHz', 0), 'high':('high speed mode 50MHz', 1)}),
        text_option('opmode', 3, 3, {'pio':('pio mode', 0), 'dma':('dma mode', 1)})
    ]

    # add 'ufs' tag
    ufs_tag = bconf_tag('ufs', 0x20, 0x10)
    root_tag.child_tags.append(ufs_tag)
    # add options for 'ufs' tag
    ufs_tag.options = [
        text_option('opmode', 0, 0, {'pio':('pio mode', 0), 'dma':('dma mode', 1)}),
        text_option('speed', 1, 2, {'pwm':('pwm mode', 0), 'g1':('high speed Gear 1 mode', 1), 'g2':('high speed Gear 2 mode', 2), 'g3':('high speed Gear 3 mode', 3) }),
        text_option('lane', 3, 3, {'1lane':('1 data lane', 0), '2lane':('2 data lanes', 1)}),
        text_option('hs_series', 4, 4, {'rateB':('Use HS RATE B', 0), 'rateA':('Use HS RATE A', 1)}),
        text_option('read_cmd', 5, 5, {'read10':('Use READ10 command', 0), 'read16':('Use READ16 command', 1)})
    ]

    # add 'bootconfig' tag
    bootconfig_tag = bconf_tag('bootconfig', 0x30, 0x8)
    root_tag.child_tags.append(bootconfig_tag)
    # add options for 'bootconfig' tag
    bootconfig_tag.options = [
        text_option('bootsel', 0, 0, {'dual':('boot with main/sub cores', 0), 'single':('boot with only main core', 1)}),
        text_option('imgmaptype', 4, 5, {'0':('image map type 0', 0), '1':('image map type 1', 1), '2':('image map type 2', 2)}),
        text_option('maincore', 8, 9, {'ca72':('primary core ca72', 0), 'ca53':('primary core ca53', 1), 'ctrl':('primary core decided by mcu', 2)}),
        text_option('corerst', 12, 12, {'enable':('enable core reset', 0), 'disable':('disable core reset', 1)}),
        text_option('apsysrst', 13, 13, {'enable':('enable AP system reset', 0), 'disable':('disable AP system reset', 1)})
    ]

    # add 'scfw' tag
    scfw_tag = bconf_tag('scfw', 0x38, 0x8)
    root_tag.child_tags.append(scfw_tag)
    # add options for 'scfw' tag
    scfw_tag.options = [
        text_option('protect', 0, 0, {'enable':('enable storage sub-system protect', 0), 'disable':('disable storage sub-system protect', 1)})
    ]

    # add 'mmc' tag below 'scfw' tag
    scfw_mmc_tag = bconf_tag('mmc', 0x44, 0x4, scfw_tag)
    scfw_tag.child_tags.append(scfw_mmc_tag)
    # add options for the 'mmc' tag
    scfw_mmc_tag.options = [
        range_option('speed', 0, 7, (0, 0xff)),
        text_option('speed_mode', 8, 10, {'hs400':('hs400', 0), 'hs200':('hs200', 1), 'ddr':('ddr', 2), 'high':('high', 3), 'default':('default', 4)}),
        range_option('otap', 11, 15, (0, 0x1f)),
        range_option('hs400_rx_pos', 16, 19, (0, 0xf)),
        range_option('hs400_rx_neg', 20, 23, (0, 0xf)),
        range_option('clk_tap', 24, 31, (0, 0x1f))
    ]

    # add 'ckc' tag below the 'scfw' tag
    scfw_ckc_tag = bconf_tag('ckc', 0x80, 0x8, scfw_tag)
    scfw_tag.child_tags.append(scfw_ckc_tag)
    # add options for 'scfw/ckc' tag
    scfw_ckc_tag.options = [
        range_option('pll_p', 0, 5, (0, 0x3f)),
        range_option('pll_m', 6, 15, (0, 0x3ff)),
        range_option('pll_s', 16, 18, (0, 0x7)),
        range_option('sub_clk', 32, 47, (0, 0xffff))
    ]

    # add 'debug' tag
    debug_tag = bconf_tag('debug', -1, -1)
    root_tag.child_tags.append(debug_tag)

    # add 'main' tag below the 'debug' tag
    debug_main_tag = bconf_tag('main', 0x40, 0x2, debug_tag)
    debug_tag.child_tags.append(debug_main_tag)
    # add options for 'main' tag
    debug_main_tag.options = [
        text_option('enable', 0, 0, {'0':('disable debug log', 0), '1':('enable debug log', 1)}),
    ]

    # add 'ipc' tag
    ipc_tag = bconf_tag('ipc', 0x48, 0x8)
    root_tag.child_tags.append(ipc_tag)
    # add options for 'ipc' tag
    ipc_tag.options = [
        text_option('device', 0, 1, {'none':('AP-MCU IPC not set', 0), 'uart':('AP-MCU IPC by UART', 1), 'gpsb':('AP-MCU IPC by GPSB', 2)}),
        range_option('port', 8, 31, (0, 0xffffff)),
        range_option('baudrate', 32, 63, (0, 0xffffffff))
    ]

    # add 'ab_update' tag
    ab_update_tag = bconf_tag('ab_update', -1, -1)
    root_tag.child_tags.append(ab_update_tag)

    # add 'main' tag below the 'ab_update' tag
    ab_update_main_tag = bconf_tag('main', 0x50, 0x10, ab_update_tag)
    ab_update_tag.child_tags.append(ab_update_main_tag)
    # add options for the 'main' tag
    ab_update_main_tag.options = [
        text_option('enable', 0, 0, {'0':('disable ab_update', 0), '1':('enable ab_update', 1)}),
        text_option('type', 1, 2, {'0':('ab_update type 0', 0), '1':('ab_update type 1', 1), '2':('ab_update type 2', 2)})
    ]

    # add 'pm' tag
    pm_tag = bconf_tag('pm', 0x70, 0x4)
    root_tag.child_tags.append(pm_tag)
    # add options for 'pm' tag
    pm_tag.options = [
        text_option('str', 16, 16, {'enable':('enable STR', 0), 'disable':('disable STR', 1)})
    ]

    # add 'strmode' tag below the 'pm' tag
    pm_strmode_tag = bconf_tag('strmode', 0x74, 0x4, pm_tag)
    pm_tag.child_tags.append(pm_strmode_tag)
    # add options for the 'strmode' tag
    pm_strmode_tag.options = [
        range_option('reg', 0, 3, (0, 0xff)),
        range_option('pin', 16, 20, (0, 0x1f)),
        text_option('cfg', 31, 31, {'disable':('disable STR mode config', 0), 'enable':('enable STR mode config', 1)})
    ]

def init_parsing():
    global input_data, output_data, out_file, reverse_mode

    parser = argparse.ArgumentParser(description='TCC805x Boot Configuration Header (Reverse) Maker V1.00')
    parser.add_argument('-r', '--reverse_mode',
                    required=False,
                    action='count',
                    default=0,
                    help='Whether Reverse mode (default: not applied)')
    parser.add_argument('-c', '--config',
                    required=False,
                    nargs=1,
                    default=None,
                    type=str,
                    help='(Legacy) Configuration XML File (default: tcc805x_bconf.xml). This options is automatically disabled when -r option(reverse mode) is applied')
    parser.add_argument('-i', '--input_file',
                    required=False,
                    nargs=1,
                    default=None,
                    type=str,
                    help='Input File (default: tcc805x_bconf.xml). Note that when the input file is XML format, the file is a XML-formatted boot configuration file otherwise, the file is a binary file parsed from the XML file.')
    parser.add_argument('-o', '--output_file',
                    required=False,
                    nargs=1,
                    default=None,
                    type=str,
                    help='Output File Name (default: bconf.bin)')
    args = parser.parse_args()

    if (args.reverse_mode == 0):
        reverse_mode = False
        if (args.config != None):
            if (args.input_file == None):
               in_file = args.config[0]
            else:
                print("Error: -c(config) option cannot be used with '-i' option simultaneously")
                sys.exit(-1)
        else:
            if (args.input_file == None):
                in_file = 'tcc805x_bconf.xml' # default value
            else:
                in_file = args.input_file[0]

        if (args.output_file != None):
            out_file = args.output_file[0]
        else:
            out_file = 'bconf.bin' # default value

        input_data = elemTree.parse(in_file)
        output_data = bytearray(512)
        #print("in_file: "+ in_file + ", out_file: " + out_file + "\n")
    else:
        reverse_mode = True
        if (args.config != None):
            print("Error: -c(config) option is only enabled when the '-r' option is not applied")
            sys.exit(-1)

        if (args.input_file != None):
            in_file = args.input_file[0]
        else:
            in_file = 'bconf.bin' # default value

        f = open(in_file, 'rb')
        # read the entire binary file into the 'input_buff' as bytearray type, in advance
        input_data = bytearray(f.read()) # can be accessed by each one byte
        f.close()

        if (args.output_file != None):
            out_file = args.output_file[0]
        else:
            out_file = 'reverse_bconf.xml'

        #print("Reverse mode!")
        #print("in_file: "+ in_file + ", out_file: " + out_file + "\n")
        print_xml_head()

def initialize():
    init_parsing()
    build_tag_struct()

def crc16(data):
    crcTable = [
        0x0000, 0x1021, 0x2042, 0x3063, 0x4084, 0x50a5, 0x60c6, 0x70e7,
        0x8108, 0x9129, 0xa14a, 0xb16b, 0xc18c, 0xd1ad, 0xe1ce, 0xf1ef,
        0x1231, 0x0210, 0x3273, 0x2252, 0x52b5, 0x4294, 0x72f7, 0x62d6,
        0x9339, 0x8318, 0xb37b, 0xa35a, 0xd3bd, 0xc39c, 0xf3ff, 0xe3de,
        0x2462, 0x3443, 0x0420, 0x1401, 0x64e6, 0x74c7, 0x44a4, 0x5485,
        0xa56a, 0xb54b, 0x8528, 0x9509, 0xe5ee, 0xf5cf, 0xc5ac, 0xd58d,
        0x3653, 0x2672, 0x1611, 0x0630, 0x76d7, 0x66f6, 0x5695, 0x46b4,
        0xb75b, 0xa77a, 0x9719, 0x8738, 0xf7df, 0xe7fe, 0xd79d, 0xc7bc,
        0x48c4, 0x58e5, 0x6886, 0x78a7, 0x0840, 0x1861, 0x2802, 0x3823,
        0xc9cc, 0xd9ed, 0xe98e, 0xf9af, 0x8948, 0x9969, 0xa90a, 0xb92b,
        0x5af5, 0x4ad4, 0x7ab7, 0x6a96, 0x1a71, 0x0a50, 0x3a33, 0x2a12,
        0xdbfd, 0xcbdc, 0xfbbf, 0xeb9e, 0x9b79, 0x8b58, 0xbb3b, 0xab1a,
        0x6ca6, 0x7c87, 0x4ce4, 0x5cc5, 0x2c22, 0x3c03, 0x0c60, 0x1c41,
        0xedae, 0xfd8f, 0xcdec, 0xddcd, 0xad2a, 0xbd0b, 0x8d68, 0x9d49,
        0x7e97, 0x6eb6, 0x5ed5, 0x4ef4, 0x3e13, 0x2e32, 0x1e51, 0x0e70,
        0xff9f, 0xefbe, 0xdfdd, 0xcffc, 0xbf1b, 0xaf3a, 0x9f59, 0x8f78,
        0x9188, 0x81a9, 0xb1ca, 0xa1eb, 0xd10c, 0xc12d, 0xf14e, 0xe16f,
        0x1080, 0x00a1, 0x30c2, 0x20e3, 0x5004, 0x4025, 0x7046, 0x6067,
        0x83b9, 0x9398, 0xa3fb, 0xb3da, 0xc33d, 0xd31c, 0xe37f, 0xf35e,
        0x02b1, 0x1290, 0x22f3, 0x32d2, 0x4235, 0x5214, 0x6277, 0x7256,
        0xb5ea, 0xa5cb, 0x95a8, 0x8589, 0xf56e, 0xe54f, 0xd52c, 0xc50d,
        0x34e2, 0x24c3, 0x14a0, 0x0481, 0x7466, 0x6447, 0x5424, 0x4405,
        0xa7db, 0xb7fa, 0x8799, 0x97b8, 0xe75f, 0xf77e, 0xc71d, 0xd73c,
        0x26d3, 0x36f2, 0x0691, 0x16b0, 0x6657, 0x7676, 0x4615, 0x5634,
        0xd94c, 0xc96d, 0xf90e, 0xe92f, 0x99c8, 0x89e9, 0xb98a, 0xa9ab,
        0x5844, 0x4865, 0x7806, 0x6827, 0x18c0, 0x08e1, 0x3882, 0x28a3,
        0xcb7d, 0xdb5c, 0xeb3f, 0xfb1e, 0x8bf9, 0x9bd8, 0xabbb, 0xbb9a,
        0x4a75, 0x5a54, 0x6a37, 0x7a16, 0x0af1, 0x1ad0, 0x2ab3, 0x3a92,
        0xfd2e, 0xed0f, 0xdd6c, 0xcd4d, 0xbdaa, 0xad8b, 0x9de8, 0x8dc9,
        0x7c26, 0x6c07, 0x5c64, 0x4c45, 0x3ca2, 0x2c83, 0x1ce0, 0x0cc1,
        0xef1f, 0xff3e, 0xcf5d, 0xdf7c, 0xaf9b, 0xbfba, 0x8fd9, 0x9ff8,
        0x6e17, 0x7e36, 0x4e55, 0x5e74, 0x2e93, 0x3eb2, 0x0ed1, 0x1ef0
    ]

    _crc = 0x0000
    crc = bytearray(2)
    for datnum in data:
        temp = ((_crc >> 8) ^ datnum) & 0xFF
        _crc = crcTable[temp] ^ (_crc << 8)

    crc[0] = _crc & 0xff
    crc[1] = (_crc >> 8) & 0xFF
    return crc

def write_data():
    global output_data, out_file, reverse_mode

    if (reverse_mode == False):
        res = crc16(output_data)
        res2 = res[0] * 256 + res[1]
        output_data[510:512] = res[0:2]
        print("Calculate CRC16: 0x%x (%d)" %(res2, res2))
        f = open(out_file, 'w+b')
    else:
        f = open(out_file, 'w+t')

    f.write(output_data)
    if (reverse_mode == False):
        print("Output: ", f)
    f.close()

def main():
    global out_file, root_tag, input_data, output_data

    initialize()
    if (reverse_mode == False):
        root_node = input_data.getroot()
        print_binary_tag(root_node, root_tag)
        write_data()
    else:
        print_text_tag(root_tag, 0)
        write_data()

if (__name__ == "__main__"):
    main()
