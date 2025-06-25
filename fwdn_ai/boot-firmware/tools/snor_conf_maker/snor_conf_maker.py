# SNOR_CONF_MAKER v0.0

import sys
import argparse
import xml.etree.ElementTree as elemTree
import struct
import hashlib
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
        int_value = int(text_value, 0)
        if (int_value >= self.value_range[idx_range_start] and int_value <= self.value_range[idx_range_end]):
                return int_value
        return None

    def print_option(self, int_value):
        return self.name + " " + hex(int_value)

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
        int_value = int(text_value, 0)
        if (int_value >= self.value_range[idx_range_start] and int_value <= self.value_range[idx_range_end]):
                return int_value
        return None

    def print_option(self, int_value):
        return self.name + " " + hex(int_value)

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
root_tag = bconf_tag('snor_config_data', -1, -1)

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

def print_snor_code_data():
    global output_data

    # Test
    print("SNOR Code Data")
    code_mem = input_data.find("./code")
    code_mem_spl = code_mem.text.split(",")

    o_index = 68
    code_index = 0x800
    for index, code_temp in enumerate(code_mem_spl):
        code_mem_spl[index] = code_temp.strip()
        int_value = int(code_mem_spl[index], 0)
        if (int_value >= 0x0 and int_value <= 0xFFFFFFFF):
            for b_index in range(4):
                shift = (b_index * 8)
                d_index = o_index + b_index
                byte_value = (int_value >> shift) & 0xFF
                output_data[d_index] = byte_value

            print("CodeIndex= " + index.__str__() +
                    " CodeOffset= " + hex(o_index) +
                    "(" + hex(code_index) + ")" +
                  " Code= " + hex(int_value))
            o_index = o_index + 4
            code_index = code_index + 4
        else:
            print("Wrong code value\n" +
                  "Code Index= " + index.__str__(), +
                  " Code= " + hex(int_value))
            return False

    return True

def build_tag_struct():
    global root_tag

    snor_tag = bconf_tag('snor', 0x0, 0x4)
    root_tag.child_tags.append(snor_tag)
    snor_tag.options = [
        text_option('num_io', 0, 1, {'spi':('num_io 1', 0), 'qpi':('num_io 4', 1), 'opi':('num_io 8', 3)}),
        text_option('mode_io', 2, 2, {'str':('str mode', 0), 'dtr':('dtr mode', 1)}),
        range_option('clk_div', 4, 11, (0, 0xff)),
        range_option('clk_src', 12, 13, (0, 0x3)),
        text_option('gpio_ds_enable', 14, 14, {'enable':('enable to set gpio ds', 1), 'disable':('set gpio ds to default value', 0)}),
        range_option('gpio_ds', 15, 16, (0, 0x3))
    ]

    timing = bconf_tag('timing', 0x4, 0x4)
    root_tag.child_tags.append(timing)
    timing.options = [
        range_option('value', 0, 31, (0, 0xffffffff))
    ]

    delay_so = bconf_tag('delay_so', 0x8, 0x4)
    root_tag.child_tags.append(delay_so)
    delay_so.options = [
        range_option('value', 0, 31, (0, 0xffffffff))
    ]

    dc_clk = bconf_tag('dc_clk', 0xc, 0x4)
    root_tag.child_tags.append(dc_clk)
    dc_clk.options = [
        range_option('value', 0, 31, (0, 0xffffffff))
    ]

    dc_wbd0 = bconf_tag('dc_wbd0', 0x10, 0x4)
    root_tag.child_tags.append(dc_wbd0)
    dc_wbd0.options = [
        range_option('value', 0, 31, (0, 0xffffffff))
    ]

    dc_wbd1 = bconf_tag('dc_wbd1', 0x14, 0x4)
    root_tag.child_tags.append(dc_wbd1)
    dc_wbd1.options = [
        range_option('value', 0, 31, (0, 0xffffffff))
    ]

    dc_rbd0 = bconf_tag('dc_rbd0', 0x18, 0x4)
    root_tag.child_tags.append(dc_rbd0)
    dc_rbd0.options = [
        range_option('value', 0, 31, (0, 0xffffffff))
    ]

    dc_rbd1 = bconf_tag('dc_rbd1', 0x1C, 0x4)
    root_tag.child_tags.append(dc_rbd1)
    dc_rbd1.options = [
        range_option('value', 0, 31, (0, 0xffffffff))
    ]

    dc_woebd0 = bconf_tag('dc_woebd0', 0x20, 0x4)
    root_tag.child_tags.append(dc_woebd0)
    dc_woebd0.options = [
        range_option('value', 0, 31, (0, 0xffffffff))
    ]

    dc_woebd1 = bconf_tag('dc_woebd1', 0x24, 0x4)
    root_tag.child_tags.append(dc_woebd1)
    dc_woebd1.options = [
        range_option('value', 0, 31, (0, 0xffffffff))
    ]

    man_base0 = bconf_tag('man_base0', 0x28, 0x4)
    root_tag.child_tags.append(man_base0)
    man_base0.options = [
        range_option('value', 0, 31, (0, 0xffffffff))
    ]

    man_base1 = bconf_tag('man_base1', 0x2c, 0x4)
    root_tag.child_tags.append(man_base1)
    man_base1.options = [
        range_option('value', 0, 31, (0, 0xffffffff))
    ]

    auto_base = bconf_tag('auto_base', 0x30, 0x4)
    root_tag.child_tags.append(auto_base)
    auto_base.options = [
        range_option('value', 0, 31, (0, 0xffffffff))
    ]

    mode = bconf_tag('mode', 0x34, 0x4)
    root_tag.child_tags.append(mode)
    mode.options = [
        range_option('value', 0, 31, (0, 0xffffffff))
    ]

    ecc_base = bconf_tag('ecc_base', 0x38, 0x4)
    root_tag.child_tags.append(ecc_base)
    ecc_base.options = [
        range_option('value', 0, 31, (0, 0xffffffff))
    ]
    code_data = bconf_tag('code', 0x44, 0x4)
    root_tag.child_tags.append(code_data)
    code_data.options = [
        # skip code
    ]


def init_parsing():
    global input_data, output_data, out_file, reverse_mode

    parser = argparse.ArgumentParser(description='TCC750x SNOR Configuration Header Maker V1.00')
    parser.add_argument('-r', '--reverse_mode',
                    required=False,
                    action='count',
                    default=0,
                    help='Whether Reverse mode (Not support now)')
    parser.add_argument('-c', '--config',
                    required=False,
                    nargs=1,
                    default=None,
                    type=str,
                    help='(Legacy) Configuration XML File (default: tcc750x_snor_conf.xml). This options is automatically disabled when -r option(reverse mode) is applied')
    parser.add_argument('-i', '--input_file',
                    required=False,
                    nargs=1,
                    default=None,
                    type=str,
                    help='Input File (default: tcc750x_snor_conf.xml). Note that when the input file is XML format, the file is a XML-formatted boot configuration file otherwise, the file is a binary file parsed from the XML file.')
    parser.add_argument('-o', '--output_file',
                    required=False,
                    nargs=1,
                    default=None,
                    type=str,
                    help='Output File Name (default: snor_conf.bin)')
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
                in_file = 'tcc750x_snor_conf.xml' # default value
            else:
                in_file = args.input_file[0]

        if (args.output_file != None):
            out_file = args.output_file[0]
        else:
            out_file = 'snor_conf.bin' # default value

        input_data = elemTree.parse(in_file)
        output_data = bytearray([0x00] * 256)
        #print("in_file: "+ in_file + ", out_file: " + out_file + "\n")
    else:
        reverse_mode = True
        if (args.config != None):
            print("Error: -c(config) option is only enabled when the '-r' option is not applied")
            sys.exit(-1)

        if (args.input_file != None):
            in_file = args.input_file[0]
        else:
            in_file = 'snor_conf.bin' # default value

        f = open(in_file, 'rb')
        # read the entire binary file into the 'input_buff' as bytearray type, in advance
        input_data = bytearray(f.read()) # can be accessed by each one byte
        f.close()

        if (args.output_file != None):
            out_file = args.output_file[0]
        else:
            out_file = 'reverse_snor_conf.xml'

        #print("Reverse mode!")
        #print("in_file: "+ in_file + ", out_file: " + out_file + "\n")
        print_xml_head()

def initialize():
    init_parsing()
    build_tag_struct()

def crc32(data):
    crcTable32 = [
            0x00000000, 0x90910101, 0x91210201, 0x01B00300,
            0x92410401, 0x02D00500, 0x03600600, 0x93F10701,
            0x94810801, 0x04100900, 0x05A00A00, 0x95310B01,
            0x06C00C00, 0x96510D01, 0x97E10E01, 0x07700F00,
            0x99011001, 0x09901100, 0x08201200, 0x98B11301,
            0x0B401400, 0x9BD11501, 0x9A611601, 0x0AF01700,
            0x0D801800, 0x9D111901, 0x9CA11A01, 0x0C301B00,
            0x9FC11C01, 0x0F501D00, 0x0EE01E00, 0x9E711F01,
            0x82012001, 0x12902100, 0x13202200, 0x83B12301,
            0x10402400, 0x80D12501, 0x81612601, 0x11F02700,
            0x16802800, 0x86112901, 0x87A12A01, 0x17302B00,
            0x84C12C01, 0x14502D00, 0x15E02E00, 0x85712F01,
            0x1B003000, 0x8B913101, 0x8A213201, 0x1AB03300,
            0x89413401, 0x19D03500, 0x18603600, 0x88F13701,
            0x8F813801, 0x1F103900, 0x1EA03A00, 0x8E313B01,
            0x1DC03C00, 0x8D513D01, 0x8CE13E01, 0x1C703F00,
            0xB4014001, 0x24904100, 0x25204200, 0xB5B14301,
            0x26404400, 0xB6D14501, 0xB7614601, 0x27F04700,
            0x20804800, 0xB0114901, 0xB1A14A01, 0x21304B00,
            0xB2C14C01, 0x22504D00, 0x23E04E00, 0xB3714F01,
            0x2D005000, 0xBD915101, 0xBC215201, 0x2CB05300,
            0xBF415401, 0x2FD05500, 0x2E605600, 0xBEF15701,
            0xB9815801, 0x29105900, 0x28A05A00, 0xB8315B01,
            0x2BC05C00, 0xBB515D01, 0xBAE15E01, 0x2A705F00,
            0x36006000, 0xA6916101, 0xA7216201, 0x37B06300,
            0xA4416401, 0x34D06500, 0x35606600, 0xA5F16701,
            0xA2816801, 0x32106900, 0x33A06A00, 0xA3316B01,
            0x30C06C00, 0xA0516D01, 0xA1E16E01, 0x31706F00,
            0xAF017001, 0x3F907100, 0x3E207200, 0xAEB17301,
            0x3D407400, 0xADD17501, 0xAC617601, 0x3CF07700,
            0x3B807800, 0xAB117901, 0xAAA17A01, 0x3A307B00,
            0xA9C17C01, 0x39507D00, 0x38E07E00, 0xA8717F01,
            0xD8018001, 0x48908100, 0x49208200, 0xD9B18301,
            0x4A408400, 0xDAD18501, 0xDB618601, 0x4BF08700,
            0x4C808800, 0xDC118901, 0xDDA18A01, 0x4D308B00,
            0xDEC18C01, 0x4E508D00, 0x4FE08E00, 0xDF718F01,
            0x41009000, 0xD1919101, 0xD0219201, 0x40B09300,
            0xD3419401, 0x43D09500, 0x42609600, 0xD2F19701,
            0xD5819801, 0x45109900, 0x44A09A00, 0xD4319B01,
            0x47C09C00, 0xD7519D01, 0xD6E19E01, 0x46709F00,
            0x5A00A000, 0xCA91A101, 0xCB21A201, 0x5BB0A300,
            0xC841A401, 0x58D0A500, 0x5960A600, 0xC9F1A701,
            0xCE81A801, 0x5E10A900, 0x5FA0AA00, 0xCF31AB01,
            0x5CC0AC00, 0xCC51AD01, 0xCDE1AE01, 0x5D70AF00,
            0xC301B001, 0x5390B100, 0x5220B200, 0xC2B1B301,
            0x5140B400, 0xC1D1B501, 0xC061B601, 0x50F0B700,
            0x5780B800, 0xC711B901, 0xC6A1BA01, 0x5630BB00,
            0xC5C1BC01, 0x5550BD00, 0x54E0BE00, 0xC471BF01,
            0x6C00C000, 0xFC91C101, 0xFD21C201, 0x6DB0C300,
            0xFE41C401, 0x6ED0C500, 0x6F60C600, 0xFFF1C701,
            0xF881C801, 0x6810C900, 0x69A0CA00, 0xF931CB01,
            0x6AC0CC00, 0xFA51CD01, 0xFBE1CE01, 0x6B70CF00,
            0xF501D001, 0x6590D100, 0x6420D200, 0xF4B1D301,
            0x6740D400, 0xF7D1D501, 0xF661D601, 0x66F0D700,
            0x6180D800, 0xF111D901, 0xF0A1DA01, 0x6030DB00,
            0xF3C1DC01, 0x6350DD00, 0x62E0DE00, 0xF271DF01,
            0xEE01E001, 0x7E90E100, 0x7F20E200, 0xEFB1E301,
            0x7C40E400, 0xECD1E501, 0xED61E601, 0x7DF0E700,
            0x7A80E800, 0xEA11E901, 0xEBA1EA01, 0x7B30EB00,
            0xE8C1EC01, 0x7850ED00, 0x79E0EE00, 0xE971EF01,
            0x7700F000, 0xE791F101, 0xE621F201, 0x76B0F300,
            0xE541F401, 0x75D0F500, 0x7460F600, 0xE4F1F701,
            0xE381F801, 0x7310F900, 0x72A0FA00, 0xE231FB01,
            0x71C0FC00, 0xE151FD01, 0xE0E1FE01, 0x7070FF00
    ]

    _crc = 0x00000000
    crc = bytearray(4)
    for datnum in data:
        temp = (_crc ^ datnum) & 0xFF
        _crc = crcTable32[temp] ^ (_crc >> 8)

    crc[0] = _crc & 0xff
    crc[1] = (_crc >> 8) & 0xFF
    crc[2] = (_crc >> 16) & 0xFF
    crc[3] = (_crc >> 24) & 0xFF

    #print("CRC32: 0x" + crc.hex())
    return crc

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

    #print("CRC16: 0x" + crc.hex())
    return crc

def write_data():
    global output_data, out_file, reverse_mode

    if (reverse_mode == False):
        # SNOR Config is actually only 256 byte
        res = crc32(output_data[0:252])
        output_data[252:256] = res[0:4]
        print("Calculate CRC32 for output[0:252]  (LSB first): " + res.hex())
        f = open(out_file, 'w+b')
    else:
        f = open(out_file, 'w+t')

    f.write(output_data)
    f.write(bytearray([0xFF] * 256))
    if (reverse_mode == False):
        print("Output: ", f)
    f.close()

def mkrom(romname, imagename, version, offset, target):
    image = open(imagename, 'rb')
    buf = image.read()
    length = (((len(buf) + 0x3F) >> 6) << 6)
    image.close()

    rom = open(romname, 'wb')
    make_tcc_image(rom, buf.ljust(length, b'\0'), version, offset, target)
    rom.close()
    return 0

def main():
    global out_file, root_tag, input_data, output_data

    initialize()

    print("TCC750x SNOR Configuration Maker");
    if (reverse_mode == False):
        root_node = input_data.getroot()
        print_binary_tag(root_node, root_tag)
        print_snor_code_data()
        write_data()
    else:
        print_text_tag(root_tag, 0)
        write_data()

if (__name__ == "__main__"):
    main()
