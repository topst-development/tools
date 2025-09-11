#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <getopt.h>
#include "jatom.h"
#include "mkimage.h"

static char *jmalloc_string(char *sz)
{
    char *ret_str = NULL;
    unsigned int len = 0;

    if (sz) {
        len = strlen(sz);
        ret_str = (char *)malloc((len * sizeof(char)) + sizeof(char));
        if (ret_str) {
            strcpy(ret_str, sz);
        }
    }
    return ret_str;
}

static void help_msg(char *prog_name)
{
	printf(	"------------------------------------------------------------\n"
			"|  TCC_MK_SNOR_BOOT: Make up SNOR Master Image\n"
			"|  [USAGE]\n"
			"|  -i : input cfg file name\n"
			"|  -o : output file name\n"
			"|\n"
			"| * example \n"
			"| $ %s -i tcc8050.cfg -o snor_master.rom\n"
			"| $ %s -i tcc8059.cfg -o snor_master.rom\n"
			"|\n"
			"| * Build Date: %s (%s)\n"
			"------------------------------------------------------------\n",
			prog_name, prog_name, __DATE__, __TIME__);
}

static BOOL parse_cfg(int argc, char *argv[], tcc_input_info_x *p_input_info)
{
    BOOL ret = FALSE;
	FILE *fd = NULL;
	char buf[1024], key[64], value[512];
	char *cfg_file = NULL, *sp, *ep;
    static struct option long_options[] = {
        {"cfg_name", 1, 0, 'c'},
        {"dest_name", 1, 0, 'o'},
        {0, 0, 0, 0}
    };

    if (!p_input_info) {
        return FALSE;
    }

    while (1) {
        int c = 0;
        int option_index = 0;

        c = getopt_long(argc, argv, "i:o:", long_options, &option_index);
        if (c == -1) { break; }

        switch (c) {
        case 0:
            break;
		case 'i':
			cfg_file = jmalloc_string(optarg);
			break;
        case 'o':
            p_input_info->dest_name = jmalloc_string(optarg);
            break;
        default:
            printf("invalid argument: optarg[%s]\n", optarg);
            break;
        }
    }

	fd = fopen(cfg_file, "r");
	if (!fd)
		return FALSE;

	while (!feof(fd)) {
		memset(key, 0x00, 64);
		memset(value, 0x00, 512);

		fgets(buf, 1024, fd);

		if (buf[0] == '#')
			continue;
		else if (strstr(buf, "=")) {
			sp = strstr(buf, "=");
			ep = strstr(buf, "\n");
			memcpy(key, buf, sp - buf);
			memcpy(value, sp + 1, ep - sp - 1);

			if (!strcmp(key, "SNOR_SIZE"))
				p_input_info->snor_size = (unsigned int)atol(value);
			else if (!strcmp(key, "DEBUG_ENABLE"))
				p_input_info->debug_enable = (unsigned int)atol(value)? 1: 0;
			else if (!strcmp(key, "DEBUG_PORT"))
				p_input_info->debug_port = (unsigned int)atol(value);
			else if (!strcmp(key, "MCERT_BIN"))
				p_input_info->mcert_bin_name = jmalloc_string(value);
			else if (!strcmp(key, "HSM_BIN"))
				p_input_info->hsm_bin_name = jmalloc_string(value);
			else if (!strcmp(key, "R5BL1_BIN"))
				p_input_info->r5bl1_bin_name = jmalloc_string(value);
			else if (!strcmp(key, "UPDATE_BIN"))
				p_input_info->update_bin_name = jmalloc_string(value);
			else if (!strcmp(key, "MICOM_BIN"))
				p_input_info->micom_bin_name = jmalloc_string(value);
			else if (!strcmp(key, "REVISION"))
				chip_rev = (unsigned int)atol(value)? 1: 0;
			else if (!strcmp(key, "OCTA_SPI"))
				opi_mode = (unsigned int)atol(value)? 1: 0;
			else if (!strcmp(key, "ECC_ENABLE")){
				ecc_table_addr =(unsigned int)atol(value)?
					(((p_input_info->snor_size * 1024 * 1024 / 9) >> 3) << 6): 0;
			}
		}
	}

	if( (p_input_info->dest_name != 0)
		&& (p_input_info->snor_size >= 4)
		&& (p_input_info->mcert_bin_name != 0)
		&& (p_input_info->hsm_bin_name != 0)
		&& (p_input_info->r5bl1_bin_name != 0)
		&& (p_input_info->update_bin_name != 0)
		&& (p_input_info->micom_bin_name != 0)) {
		ret = TRUE;
	}

	return ret;
}

static BOOL exist_file(char *name)
{
    FILE *fd = NULL;
    return FALSE;
    if (name) {
        fd = fopen(name, "r");
        if (fd) {
            fclose(fd);
            return TRUE;
        } else {
        }
    }
    return FALSE;
}

static BOOL tcc_sfmc_mk_bootrom(tcc_input_info_x *p_input_info)
{
	snor_rom_info_t rom_header[2];
	unsigned int hsm_size = 0, r5_bl1_size = 0, updater_size = 0, micom_size = 0;
	BOOL ret = FALSE;
	char *dest_name			= p_input_info->dest_name;
	char *mcert_bin_name	= p_input_info->mcert_bin_name;
	char *hsm_bin_name		= p_input_info->hsm_bin_name;
	char *r5bl1_bin_name	= p_input_info->r5bl1_bin_name;
	char *update_bin_name	= p_input_info->update_bin_name;
	char *micom_bin_name	= p_input_info->micom_bin_name;
	FILE *dest_fd		= NULL;
	FILE *mcert_bin_fd	= NULL;
	FILE *hsm_bin_fd	= NULL;
	FILE *r5bl1_bin_fd	= NULL;
	FILE *update_bin_fd	= NULL;
	FILE *micom_bin_fd	= NULL;
	unsigned int secured;
	unsigned int micom_offset;

	if (dest_name) {
		if (!exist_file(dest_name)) {
			dest_fd			= fopen(dest_name, "w+b");
			mcert_bin_fd	= fopen(mcert_bin_name, "rb");
			hsm_bin_fd		= fopen(hsm_bin_name, "rb");
			r5bl1_bin_fd	= fopen(r5bl1_bin_name, "rb");
			update_bin_fd	= fopen(update_bin_name, "rb");
			micom_bin_fd	= fopen(micom_bin_name, "rb");

			memset(&rom_header[0], 0x00, sizeof(snor_rom_info_t));
			memset(&rom_header[1], 0x00, sizeof(snor_rom_info_t));

			if (dest_fd && mcert_bin_fd && hsm_bin_fd && r5bl1_bin_fd
					&& update_bin_fd && micom_bin_fd) {
			} else {
				printf("\x1b[1;31mFailed to open file\x1b[0m\n");
				printf("(%s) : %s\n", mcert_bin_name, mcert_bin_fd? "\x1b[1;32mOK\x1b[0m": "\x1b[1;31mFailure\x1b[0m");
				printf("(%s) : %s\n", hsm_bin_name, hsm_bin_fd? "\x1b[1;32mOK\x1b[0m": "\x1b[1;31mFailure\x1b[0m");
				printf("(%s) : %s\n", r5bl1_bin_name, r5bl1_bin_fd? "\x1b[1;32mOK\x1b[0m": "\x1b[1;31mFailure\x1b[0m");
				printf("(%s) : %s\n", update_bin_name, update_bin_fd? "\x1b[1;32mOK\x1b[0m": "\x1b[1;31mFailure\x1b[0m");
				printf("(%s) : %s\n", micom_bin_name, micom_bin_fd? "\x1b[1;32mOK\x1b[0m": "\x1b[1;31mFailure\x1b[0m");
				printf("(%s) file exist!!!\n", dest_name);
				goto close;
			}

			//===================================
			// Write SFMC Init Header 0 & 1 (4 Kbyte * 2) : 0x00002000 ~ 0x00004000
			//===================================
			ret = write_sfmc_init_header(dest_fd, p_input_info->snor_size);
			if (ret == FALSE)
				goto close;

			//===================================
			// Master Certificate 0 & 1 Write (256 Kbyte * 2) : 0x00004000 ~ 0x00006000
			//===================================
			ret = write_master_certificate(dest_fd, mcert_bin_fd, NULL);
			if (ret == FALSE)
				goto close;

			//===================================
			// HSM rom 0 & 1 Write (256 Kbyte * 2) : 0x00006000 ~ 0x0000E000
			//===================================
			ret = write_hsm_image(dest_fd, hsm_bin_fd, &hsm_size);
			if (ret == FALSE)
				goto close;

			//===================================
			// BL1 rom 0 & 1 Write (512 Kbyte * 2) : 0x00016000 ~ 0x00096000
			//===================================
			ret = write_r5_bl1_image(dest_fd, r5bl1_bin_fd, &r5_bl1_size);
			if (ret == FALSE)
				goto close;

			//===================================
			// R5 Sub f/w rom 0 Write (64 Kbyte) : 0x00116000 ~ 0x00196000
			//===================================
			ret = write_micom_sub_fw_image(dest_fd, update_bin_fd, &updater_size);
			if (ret == FALSE)
				goto close;

			//===================================
			//R5 Main rom 0 & 1 write : 0x0200000 ~
			//===================================
			if (strstr(micom_bin_name, ".bin")) {
				secured = 0;
				micom_offset = MICOM_ROM_HEADER_SIZE;
			}
			else if (strstr(micom_bin_name, ".rom")) {
				secured = 1;
				micom_offset = 0;
			}
			else {
				secured = 1;
				micom_offset = 0;
			}

			ret = write_micom_rom(dest_fd, micom_bin_fd, &micom_size, secured);
			if (ret == FALSE)
				goto close;

			//===================================
			// ROM Header 0 (4kbyte) : 0x00000000 ~ 0x00001000
			//===================================
			/* SNOR ROM Header 0 */
			rom_header[0].section_info[SNOR_SFMC_INIT_HEADER_ID].offset			= SFMC_INIT_HEAD0_OFFSET;
			rom_header[0].section_info[SNOR_SFMC_INIT_HEADER_ID].section_size	= SFMC_INIT_HEAD_SIZE;
			rom_header[0].section_info[SNOR_SFMC_INIT_HEADER_ID].data_size		= sizeof(sSFQPI_InitHeader);

			rom_header[0].section_info[SNOR_MASTER_CERTI_ID].offset				= HSM_MCERT_AREA0_OFFSET;
			rom_header[0].section_info[SNOR_MASTER_CERTI_ID].section_size		= HSM_MCERT_AREA_SIZE;
			rom_header[0].section_info[SNOR_MASTER_CERTI_ID].data_size			= 512;

			rom_header[0].section_info[SNOR_HSM_BINARY_ID].offset				= HSM_AREA0_OFFSET;
			rom_header[0].section_info[SNOR_HSM_BINARY_ID].section_size			= HSM_AREA_SIZE;
			rom_header[0].section_info[SNOR_HSM_BINARY_ID].data_size			= hsm_size;

			rom_header[0].section_info[SNOR_BL1_BINARY_ID].offset				= R5_BL1_AREA0_OFFSET;
			rom_header[0].section_info[SNOR_BL1_BINARY_ID].section_size			= R5_BL1_AREA_SIZE;
			rom_header[0].section_info[SNOR_BL1_BINARY_ID].data_size			= r5_bl1_size;

			rom_header[0].section_info[SNOR_MICOM_SUB_BINARY_ID].offset			= MICOM_SUB_FW_HEADER_OFFSET;
			rom_header[0].section_info[SNOR_MICOM_SUB_BINARY_ID].section_size	= MICOM_SUB_FW_AREA_SIZE;
			rom_header[0].section_info[SNOR_MICOM_SUB_BINARY_ID].data_size		= updater_size;

			rom_header[0].section_info[SNOR_UPDATE_FLAG_ID].offset				= MICOM_SUB_FW_FLAG_OFFSET;
			rom_header[0].section_info[SNOR_UPDATE_FLAG_ID].section_size		= MICOM_SUB_FW_FLAG_SIZE;
			rom_header[0].section_info[SNOR_UPDATE_FLAG_ID].data_size			= 0;

			rom_header[0].section_info[SNOR_MICOM_BINARY_ID].offset				= MICOM_HEADER_0_OFFSET + micom_offset;
			rom_header[0].section_info[SNOR_MICOM_BINARY_ID].section_size		= MICOM_ROM_AREA_SIZE;
			rom_header[0].section_info[SNOR_MICOM_BINARY_ID].data_size			= micom_size;

			rom_header[0].debug_enable = (p_input_info->debug_enable == 0)? 0: 1;
			rom_header[0].debug_port = p_input_info->debug_port;

			ret = write_rom_header(dest_fd, 0, &rom_header[0]);
			if (ret == FALSE)
				goto close;

			//===================================
			// ROM Header 1 (4kbyte) : 0x00001000 ~ 0x00002000
			//===================================
			/* SNOR ROM Header 1 */
			rom_header[1].section_info[SNOR_SFMC_INIT_HEADER_ID].offset			= SFMC_INIT_HEAD1_OFFSET;
			rom_header[1].section_info[SNOR_SFMC_INIT_HEADER_ID].section_size	= SFMC_INIT_HEAD_SIZE;
			rom_header[1].section_info[SNOR_SFMC_INIT_HEADER_ID].data_size		= sizeof(sSFQPI_InitHeader);

			rom_header[1].section_info[SNOR_MASTER_CERTI_ID].offset				= HSM_MCERT_AREA0_OFFSET;
			rom_header[1].section_info[SNOR_MASTER_CERTI_ID].section_size		= HSM_MCERT_AREA_SIZE;
			rom_header[1].section_info[SNOR_MASTER_CERTI_ID].data_size			= 512;

			rom_header[1].section_info[SNOR_HSM_BINARY_ID].offset				= HSM_AREA1_OFFSET;
			rom_header[1].section_info[SNOR_HSM_BINARY_ID].section_size			= HSM_AREA_SIZE;
			rom_header[1].section_info[SNOR_HSM_BINARY_ID].data_size			= hsm_size;

			rom_header[1].section_info[SNOR_BL1_BINARY_ID].offset				= R5_BL1_AREA1_OFFSET;
			rom_header[1].section_info[SNOR_BL1_BINARY_ID].section_size			= R5_BL1_AREA_SIZE;
			rom_header[1].section_info[SNOR_BL1_BINARY_ID].data_size			= r5_bl1_size;

			rom_header[1].section_info[SNOR_MICOM_SUB_BINARY_ID].offset			= MICOM_SUB_FW_HEADER_OFFSET;
			rom_header[1].section_info[SNOR_MICOM_SUB_BINARY_ID].section_size	= MICOM_SUB_FW_AREA_SIZE;
			rom_header[1].section_info[SNOR_MICOM_SUB_BINARY_ID].data_size		= updater_size;

			rom_header[1].section_info[SNOR_UPDATE_FLAG_ID].offset				= MICOM_SUB_FW_FLAG_OFFSET;
			rom_header[1].section_info[SNOR_UPDATE_FLAG_ID].section_size		= MICOM_SUB_FW_FLAG_SIZE;
			rom_header[1].section_info[SNOR_UPDATE_FLAG_ID].data_size			= 0;

#if defined(INCLUDE_SECONDARY_R5_FW)
			rom_header[1].section_info[SNOR_MICOM_BINARY_ID].offset				= MICOM_HEADER_1_OFFSET + micom_offset;
			rom_header[1].section_info[SNOR_MICOM_BINARY_ID].section_size		= MICOM_ROM_AREA_SIZE;
			rom_header[1].section_info[SNOR_MICOM_BINARY_ID].data_size			= micom_size;
#else
			rom_header[1].section_info[SNOR_MICOM_BINARY_ID].offset				= 0;
			rom_header[1].section_info[SNOR_MICOM_BINARY_ID].section_size		= 0;
			rom_header[1].section_info[SNOR_MICOM_BINARY_ID].data_size			= 0;
#endif

			rom_header[1].debug_enable = (p_input_info->debug_enable == 0)? 0: 1;
			rom_header[1].debug_port = p_input_info->debug_port;

			ret = write_rom_header(dest_fd, 1, &rom_header[1]);
			if (ret == FALSE)
				goto close;

			/* Create size-aligned final ROM file */
			ret = create_final_rom(dest_fd, p_input_info->snor_size);
			if (ret == FALSE)
				goto close;

			fflush(dest_fd);
		}
	}
close:
	CLOSE_HANDLE(mcert_bin_fd, NULL, fclose);
	CLOSE_HANDLE(hsm_bin_fd, NULL, fclose);
	CLOSE_HANDLE(r5bl1_bin_fd, NULL, fclose);
	CLOSE_HANDLE(update_bin_fd, NULL, fclose);
	CLOSE_HANDLE(micom_bin_fd, NULL, fclose);
	CLOSE_HANDLE(dest_fd, NULL, fclose);

	if (ret == FALSE)
		remove(dest_name);

	return ret;
}

int main(int argc, char *argv[])
{
    int ret = -1;
    tcc_input_info_x param;

    memset(&param, 0x0, sizeof(tcc_input_info_x));

	if (parse_cfg(argc, argv, &param) == TRUE) {
		printf("MCERT file: (%s)\n", param.mcert_bin_name );
		printf("HSM binary file: (%s)\n", param.hsm_bin_name );
		printf("R5-BL1 binary file: (%s)\n", param.r5bl1_bin_name );
		printf("update binary file: (%s)\n", param.update_bin_name );
		printf("MICOM binary file: (%s)\n", param.micom_bin_name );
		printf("SNOR ROM size: (%d MByte)\n", param.snor_size);
		printf("R5 UART port enable: (%d)\n", param.debug_enable);
		printf("R5 UART port for debug: (%d)\n", param.debug_port);
		printf("Output file: (%s)\n", param.dest_name );

	    if (!tcc_sfmc_mk_bootrom(&param)) {
	        printf("make fail!!! \n");
	    } else {
	        ret = 0;
	    }
	} else {
		help_msg(argv[0]);
	}

    return ret;
}

