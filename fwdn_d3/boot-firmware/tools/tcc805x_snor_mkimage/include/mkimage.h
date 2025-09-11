
#ifndef __MKIMAGE_H__
#define __MKIMAGE_H__

#include "jatom.h"

/***************************** SNOR Flash Memory Map *****************************/
#define SNOR_ROM_HEADER_SIZE	(4 * 1024)
#define SNOR_ROM_HEADER_OFFSET	(0x00000000)

#define SFMC_INIT_HEAD_SIZE		(4 * 1024)
#define SFMC_INIT_HEAD0_OFFSET	(0x00002000)
#define SFMC_INIT_HEAD1_OFFSET	(0x00003000)

#define HSM_MCERT_AREA_SIZE		(4 * 1024)
#define HSM_MCERT_AREA0_OFFSET	(0x00004000)
#define HSM_MCERT_AREA1_OFFSET	(0x00005000)

#define HSM_AREA_SIZE			(32 * 1024)
#define HSM_AREA0_OFFSET		(0x00006000)
#define HSM_AREA1_OFFSET		(0x0000E000)

#define R5_BL1_AREA_SIZE		(512 * 1024)
#define R5_BL1_AREA0_OFFSET		(0x00016000)
#define R5_BL1_AREA1_OFFSET		(0x00096000)

#define MICOM_SUB_FW_AREA_SIZE		(64 * 1024)
#define MICOM_SUB_FW_HEADER_SIZE	(512)
#define MICOM_SUB_FW_HEADER_OFFSET	(0x00116000)
#define MICOM_SUB_FW_IMAGE_OFFSET	(MICOM_SUB_FW_HEADER_OFFSET + MICOM_SUB_FW_HEADER_SIZE)

#define MICOM_SUB_FW_FLAG_SIZE		(4 * 1024)
#define MICOM_SUB_FW_FLAG_OFFSET	(MICOM_SUB_FW_HEADER_OFFSET + MICOM_SUB_FW_AREA_SIZE)

//#define INCLUDE_SECONDARY_R5_FW
#undef INCLUDE_SECONDARY_R5_FW

#define MICOM_ROM_AREA_SIZE		(0x00100000)
#define MICOM_ROM_HEADER_SIZE	(0x00001000)
#define MICOM_HEADER_0_OFFSET 	(0x001FF000)
#if defined(INCLUDE_SECONDARY_R5_FW)
#define MICOM_HEADER_1_OFFSET 	(MICOM_HEADER_0_OFFSET + MICOM_ROM_AREA_SIZE)
#endif

/*********************************************************************************/

/* SNOR ROM Header */
#define SNOR_ROM_ID				0x524F4E53 // 'SNOR'
#define SNOR_SECTION_MAX_COUNT	30

enum SNOR_SECTION_ID {
	SNOR_SFMC_INIT_HEADER_ID = 0,
	SNOR_MASTER_CERTI_ID,
	SNOR_HSM_BINARY_ID,
	SNOR_BL1_BINARY_ID,
	SNOR_MICOM_SUB_BINARY_ID,
	SNOR_UPDATE_FLAG_ID,
	SNOR_MICOM_BINARY_ID,
	SNOR_SECTION_ID_END,
};

typedef struct snor_section_info {
	unsigned int offset;
	unsigned int section_size;
	unsigned int data_size;
	unsigned int reserved;
} snor_section_info_t;

typedef struct snor_rom_info {
	snor_section_info_t	section_info[SNOR_SECTION_MAX_COUNT];
	unsigned int		reserved[4];
	unsigned int		debug_enable;
	unsigned int		debug_port;
	unsigned int 		rom_id; //= SNOR_ROM_ID;
	unsigned int		crc;
} snor_rom_info_t; /* total 512byte */


/* SFMC Init Header */
#define CODE_VLU_SIZE	46

typedef	struct {
	unsigned int	code;
				//[1:0]   -> sflash_mode_sel        => 0x0 : SPI(fixed) 0x1: QPI, 0x2: QPI-DUAL 0x3: OPI (0x0 to 0x2 are the same)
			    //[2]     -> str/dtr                => 0x0: STR(fixed), 0x1: DTR
			    //[3]     -> auto/manu              => 0x0: AUTO(fixed), 0x1: MANU
			    //[11:4]  -> fclk_div(fin=800MHz)   => 0x1f: 25MHz, 0x1d: 26MHz, 0x1b: 28MHz, 0x19: 30MHz, 0x17:33MHz,  0x15:36MHz,  0x13: 40MHz,  0x11:44MHz,
			    //					  				   0x0f: 50MHz, 0x0d: 57MHz, 0x0b: 66MHz, 0x09: 80MHz, 0x07:100MHz, 0x05:133MHz, 0x03: 200MHz, 0x01: 400MHz.
			    //[13:12] -> fclk_sel               => 0x0: PLL0(800Mhz, fixed)
			    //[31]    -> reserved
	unsigned int	timing;
	unsigned int	delay_so;
	unsigned int	dc_clk;
	unsigned int	dc_wbd0;
	unsigned int	dc_wbd1;
	unsigned int	dc_rbd0;
	unsigned int	dc_rbd1;
	unsigned int	dc_woebd0;
	unsigned int	dc_woebd1;
	unsigned int	dc_base_addr_manu_0;
	unsigned int	dc_base_addr_manu_1;
	unsigned int	dc_base_addr_auto;
	unsigned int	run_mode;
	unsigned int	ecc_table_addr;
	unsigned int	ulReserved[2];
	unsigned int	code_vlu[CODE_VLU_SIZE];
	unsigned int	ulCRC;
} sSFQPI_InitHeader;

/* Input files information structure */
typedef struct _tcc_input_info_x {
    char *dest_name;
	char *mcert_bin_name;
	char *hsm_bin_name;
	char *r5bl1_bin_name;
    char *update_bin_name;
    char *micom_bin_name;
	unsigned int debug_enable;
	unsigned int debug_port;
	unsigned int snor_size;
	unsigned int micom_rom_bass_addr;
} tcc_input_info_x;

extern unsigned int chip_rev;	/* ES: 0, CS: 1 */
extern unsigned int opi_mode;
extern unsigned int ecc_table_addr;

extern BOOL write_sfmc_init_header(FILE *dest_fd, unsigned int snor_size);
extern BOOL write_master_certificate(FILE *dest_fd, FILE *mcert_bin_fd, unsigned int *mcert_size);
extern BOOL write_hsm_image(FILE *dest_fd, FILE *hsm_bin_fd, unsigned int *hsm_size);
extern BOOL write_r5_bl1_image(FILE *dest_fd, FILE *r5bl1_bin_fd, unsigned int *r5bl1_size);
extern BOOL write_micom_sub_fw_image(FILE *dest_fd, FILE *micom_sub_img_fd, unsigned int *micom_subr_size);
extern BOOL write_micom_rom(FILE *dest_fd, FILE *micom_rom_fd, unsigned int *micom_size, unsigned int secured);
extern BOOL write_rom_header(FILE *out_rom_fd, unsigned int lun, snor_rom_info_t *snor_info);
extern BOOL create_final_rom(FILE *out_rom_fd, unsigned int snor_size);

#endif /* __MKIMAGE_H__ */
