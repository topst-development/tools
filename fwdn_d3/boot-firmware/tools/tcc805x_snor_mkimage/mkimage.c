/****************************************************************************

One line to give the program's name and a brief idea of what it does.

Copyright (C) 2013 Telechips Inc.

 

This program is free software; you can redistribute it and/or modify it under the terms

of the GNU General Public License as published by the Free Software Foundation;

either version 2 of the License, or (at your option) any later version.

 

This program is distributed in the hope that it will be useful, but WITHOUT ANY WARRANTY;

without even the implied warranty of MERCHANTABILITY or FITNESS FOR A PARTICULAR

PURPOSE. See the GNU General Public License for more details.

 

You should have received a copy of the GNU General Public License along with

this program; if not, write to the Free Software Foundation, Inc., 59 Temple Place,

Suite 330, Boston, MA 02111-1307 USA

****************************************************************************/


#include <stdio.h>
#include <stdlib.h>
#include <string.h>

#include "mkimage.h"
#include "ecc.h"


#define SNOR_PAGE_SIZE				(256)

/* ES: 0, CS: 1 */
unsigned int chip_rev;
/* Quad SPI: 0, Octa SPI: 1 */
unsigned int opi_mode;
/* ECC table address */
unsigned int ecc_table_addr;

static const unsigned long int CRC32_TABLE[256] = {
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
};


// Quad SPI 4READ3B & 4READ4B Commands (STR)
sSFQPI_InitHeader stCODE_4READ3B = {
	0x00000090,		// code;	//80Mhz, PLL0:800, Div: 9+1
	0x00140300,		// timing;
	0x00000500,		// delay_so;
	0x00000000,		// dc_clk;
	0x00000000,		// dc_wbd0;
	0x00000000,		// dc_wbd1;
	0x00000000,		// dc_rbd0;
	0x00000000,		// dc_rbd1;
	0x00000000,		// dc_woebd0;
	0x00000000,		// dc_woebd1;
	0x00000818,		// dc_base_addr_manu_0;
	0x0000081C,		// dc_base_addr_manu_1;
	0x00000800,		// dc_base_addr_auto;
	0x00000011,		// run_mode;
	0x00000000,		// ecc_table_addr;
	{
		0x00000000,		// reserved[0]
		0x00000000,		// reserved[1]
	},
					// read_3b
	{
		0x840000EB,	// 0x800	// 4READ 3B
		0x4A000001,	// 0x804
		0x86000000,	// 0x808
		0x46002000,	// 0x80C
		0x2A000000,	// 0x810
		0xF4000000,	// 0x814	// STOP

		0xF4000000, // 0x818	// STOP
		0xF4000000, // 0x81C	// STOP
	},
	0x00000077		// crc
};

sSFQPI_InitHeader stCODE_4READ4B = {
	0x00000090,		// code;	//80Mhz, PLL0:800, Div: 9+1
	0x00140300,		// timing;
	0x00000500,		// delay_so;
	0x00000000,		// dc_clk;
	0x00000000,		// dc_wbd0;
	0x00000000,		// dc_wbd1;
	0x00000000,		// dc_rbd0;
	0x00000000,		// dc_rbd1;
	0x00000000,		// dc_woebd0;
	0x00000000,		// dc_woebd1;
	0x00000818,		// dc_base_addr_manu_0;
	0x0000081C,		// dc_base_addr_manu_1;
	0x00000800,		// dc_base_addr_auto;
	0x00000011,		// run_mode;
	0x00000000,		// ecc_table_addr;
	{
		0x00000000,		// reserved[0]
		0x00000000,		// reserved[1]
	},
					// read_4b
	{
		0x840000EC,	// 0x800	// 4READ 4B
		0x4A000000,	// 0x804
		0x86000000,	// 0x808
		0x46002000,	// 0x80C
		0x2A000000,	// 0x810
		0xF4000000,	// 0x814	// STOP

		0xA40000B7, // 0x818	// EN4B
		0xF4000000, // 0x81C	// STOP
		0xF4000000, // 0x820	// STOP
	},
	0x00000077		// crc
};

// Quad SPI 4READ3B & 4READ4B Commands (STR)
sSFQPI_InitHeader stCODE_4READ3B_CS = {
	0x000000E0,		// code;	//80Mhz, PLL0:1200, Div: 14+1
	0x00140300,		// timing;
	0x00000500,		// delay_so;
	0x00000000,		// dc_clk;
	0x00000000,		// dc_wbd0;
	0x00000000,		// dc_wbd1;
	0x00000000,		// dc_rbd0;
	0x00000000,		// dc_rbd1;
	0x00000000,		// dc_woebd0;
	0x00000000,		// dc_woebd1;
	0x00000818,		// dc_base_addr_manu_0;
	0x0000081C,		// dc_base_addr_manu_1;
	0x00000800,		// dc_base_addr_auto;
	0x00000011,		// run_mode;
	0x00000000,		// ecc_table_addr;
	{
		0x00000000,		// reserved[0]
		0x00000000,		// reserved[1]
	},
					// read_3b
	{
		0x840000EB,	// 0x800	// 4READ 3B
		0x4A000001,	// 0x804
		0x86000000,	// 0x808
		0x46002000,	// 0x80C
		0x2A000000,	// 0x810
		0xF4000000,	// 0x814	// STOP

		0xF4000000, // 0x818	// STOP
		0xF4000000, // 0x81C	// STOP
	},
	0x00000077		// crc
};

sSFQPI_InitHeader stCODE_4READ4B_CS = {
	0x000000E0,		// code;	//80Mhz, PLL0:1200, Div: 14+1
	0x00140300,		// timing;
	0x00000500,		// delay_so;
	0x00000000,		// dc_clk;
	0x00000000,		// dc_wbd0;
	0x00000000,		// dc_wbd1;
	0x00000000,		// dc_rbd0;
	0x00000000,		// dc_rbd1;
	0x00000000,		// dc_woebd0;
	0x00000000,		// dc_woebd1;
	0x00000818,		// dc_base_addr_manu_0;
	0x0000081C,		// dc_base_addr_manu_1;
	0x00000800,		// dc_base_addr_auto;
	0x00000011,		// run_mode;
	0x00000000,		// ecc_table_addr;
	{
		0x00000000,		// reserved[0]
		0x00000000,		// reserved[1]
	},
					// read_4b
	{
		0x840000EC,	// 0x800	// 4READ 4B
		0x4A000000,	// 0x804
		0x86000000,	// 0x808
		0x46002000,	// 0x80C
		0x2A000000,	// 0x810
		0xF4000000,	// 0x814	// STOP

		0xA40000B7, // 0x818	// EN4B
		0xF4000000, // 0x81C	// STOP
		0xF4000000, // 0x820	// STOP
	},
	0x00000077		// crc
};

sSFQPI_InitHeader stCODE_4DTRD3B_CS = {
	0x000000E0,		// code;	//80Mhz, PLL0:1200, Div: 14+1
	0x00040004,		// timing;
	0x00000100,		// delay_so;
	0x00002011,		// dc_clk;
	0x00000000,		// dc_wbd0;
	0x00000000,		// dc_wbd1;
	0x00000000,		// dc_rbd0;
	0x00000000,		// dc_rbd1;
	0x00000000,		// dc_woebd0;
	0x00000000,		// dc_woebd1;
	0x00000818,		// dc_base_addr_manu_0;
	0x0000081C,		// dc_base_addr_manu_1;
	0x00000800,		// dc_base_addr_auto;
	0x00000001,		// run_mode;
	0x00000000,		// ecc_table_addr;
	{
		0x00000000,		// reserved[0]
		0x00000000,		// reserved[1]
	},
					// code
	{
		0x840000ED,	// 0x800	// 4DTRD 3B
		0x5A000001,	// 0x804
		0x96000000,	// 0x808
		0x56008000,	// 0x80C
		0x3A000000,	// 0x810
		0xF4000000,	// 0x814	// STOP

		0xF4000000, // 0x818	// STOP
		0xF4000000, // 0x81C	// STOP
	},
	0x00000077		// crc
};

sSFQPI_InitHeader stCODE_4DTRD4B_CS = {
	0x000000E0,		// code;	//80Mhz, PLL0:1200, Div: 14+1
	0x00040004,		// timing;
	0x00000100,		// delay_so;
	0x00002111,		// dc_clk;
	0x00000000,		// dc_wbd0;
	0x00000000,		// dc_wbd1;
	0x00000000,		// dc_rbd0;
	0x00000000,		// dc_rbd1;
	0x00000000,		// dc_woebd0;
	0x00000000,		// dc_woebd1;
	0x00000818,		// dc_base_addr_manu_0;
	0x00000820,		// dc_base_addr_manu_1;
	0x00000800,		// dc_base_addr_auto;
	0x00000001,		// run_mode;
	0x00000000,		// ecc_table_addr;
	{
		0x00000000,		// reserved[0]
		0x00000000,		// reserved[1]
	},
					// code
	{
		0x840000EE,	// 0x800	// 4DTRD 4B
		0x5A000000,	// 0x804
		0x96000000,	// 0x808
		0x56008000,	// 0x80C
		0x3A000000,	// 0x810
		0xF4000000,	// 0x814	// STOP
		0xA40000B7, // 0x818	// EN4B
		0xF4000000, // 0x81C	// STOP
		0xF4000000, // 0x820	// STOP
	},
	0x00000077		// crc
};

sSFQPI_InitHeader stCODE_8READ_CS = {
//	0x000000E3,		// code;	//80Mhz, PLL0:1200, Div: 14+1
	0x00000113,		// code;	//66.66Mhz, PLL0:1200, Div: 17+1
//	0x00140434,		// timing;
	0x00140330,		// timing;
	0x00000500,		// delay_so;
//	0x00000000,		// dc_clk;
	0x0000000C,		// dc_clk;
	0x00000000,		// dc_wbd0;
	0x00000000,		// dc_wbd1;
	0x00000000,		// dc_rbd0;
	0x00000000,		// dc_rbd1;
	0x00000000,		// dc_woebd0;
	0x00000000,		// dc_woebd1;
	0x00000814,		// dc_base_addr_manu_0;
	0x0000081C,		// dc_base_addr_manu_1;
	0x00000800,		// dc_base_addr_auto;
	0x00000011,		// run_mode;
	0x00000000,		// ecc_table_addr;
	{
		0x00000000,		// reserved[0]
		0x00000000,		// reserved[1]
	},
	{
		0x8B00EC13,	// 0x800	// 8READ
		0x4B000000,	// 0x804
		0x47014000,	// 0x808
		0x2B000000,	// 0x80C
		0xF4000000,	// 0x810	// STOP

		0xA4000006, // 0x814	// WRITE Enable
		0xF4000000, // 0x818	// STOP

		0x84000072, // 0x81C	// STR-OPI Enable
		0x8C000000, // 0x820
		0xA8000001, // 0x824
		0xF4000000, // 0x828	// STOP

	},
	0x00000077		// crc
};

static unsigned int FWUG_CalcCrc8(unsigned char *base, unsigned int length)
{
	unsigned int crcout = 0;
	unsigned int cnt;
	unsigned char	code, tmp;

	for(cnt=0; cnt<length; cnt++)
	{
		code = base[cnt];
		tmp = code^crcout;
		crcout = (crcout>>8)^CRC32_TABLE[tmp&0xFF];
	}
	return crcout;
}

static int SNOR_MIO_BOOT_Write_Header(unsigned char *pucRomFile_Buffer, unsigned int snor_size)
{
	sSFQPI_InitHeader sfInitHeader;
	unsigned int 	uiHeaderSize;
	unsigned char	*pucRomFile = pucRomFile_Buffer;
	unsigned int	uiRomFileIndex;
	sSFQPI_InitHeader *init_data;

	printf("\n");
	printf("\x1b[1;32m<<SNOR_MAP: 0x%08x ++0x%08x>>\x1b[0m\n", SFMC_INIT_HEAD0_OFFSET, SFMC_INIT_HEAD_SIZE*2);
	printf("[Make SFMC Read CMD Header...]\n");
	//=====================================================
	// Write Boot Header
	//=====================================================
	uiHeaderSize = SFMC_INIT_HEAD_SIZE * 2;
	printf("Header Size: %d byte\n", uiHeaderSize);

	//=====================================================
	// Make SFMC InitHeader Info
	//=====================================================
	memset(&sfInitHeader, 0x00, sizeof(sSFQPI_InitHeader));

	switch (chip_rev) {
		case 0: /* ES */
			if (opi_mode == 0) {
				if (snor_size < 32)
					init_data = &stCODE_4READ3B;
				else
					init_data = &stCODE_4READ4B;
			}
			else {
				printf("Octa SPI Command cannot be supported on ES chip.\n");
				return -1;
			}
			break;
		default: /* CS */
			if (opi_mode == 0) {
				if (snor_size < 32)
					init_data = &stCODE_4READ3B_CS;
				else
					init_data = &stCODE_4READ4B_CS;
			}
			else {
				init_data = &stCODE_8READ_CS;
			}
	}
	memcpy(&sfInitHeader, init_data, sizeof(sSFQPI_InitHeader));

	/* The ECC table is located at the end of SNOR ROM.
	 * The ratio of Data:ECC is 8:1.
	 * ECC table is generated in units of 64bytes. */
	sfInitHeader.ecc_table_addr = ecc_table_addr;

	printf("(0) FAST READ CMD Set for Chipboot (SPI)\n");
	{
		printf("\tCode:        0x%08X\n", sfInitHeader.code);
		printf("\tTiming:      0x%08X\n", sfInitHeader.timing);
		printf("\tDelay_s:     0x%08X\n", sfInitHeader.delay_so);
		printf("\tDc_clk:      0x%08X\n", sfInitHeader.dc_clk);
		printf("\tRun_mode:    0x%08X\n", sfInitHeader.run_mode);
		printf("\tECC address: 0x%08X\n", sfInitHeader.ecc_table_addr);
		printf("\tRead_cmd:    0x%08X 0x%08X 0x%08X 0x%08X 0x%08X\n",
									sfInitHeader.code_vlu[0],
									sfInitHeader.code_vlu[1],
									sfInitHeader.code_vlu[2],
									sfInitHeader.code_vlu[3],
									sfInitHeader.code_vlu[4]);
	}

	sfInitHeader.ulCRC = FWUG_CalcCrc8((unsigned char*)&sfInitHeader, sizeof(sSFQPI_InitHeader) - 4);
	printf("\tCMD CRC:     0x%08X\n", sfInitHeader.ulCRC);

	uiRomFileIndex = 0;
	memcpy(&pucRomFile[uiRomFileIndex], &sfInitHeader, sizeof(sSFQPI_InitHeader));
	printf("\tCMD address: 0x%08X\n", SFMC_INIT_HEAD0_OFFSET);

	uiRomFileIndex = SFMC_INIT_HEAD_SIZE;
	memcpy(&pucRomFile[uiRomFileIndex], &sfInitHeader, sizeof(sSFQPI_InitHeader));

	return 0;
}

static int fill_ecc_data(unsigned char *rom_buf, unsigned int data_len)
{
	int ret = -1;
	unsigned char *ecc_buf;
    unsigned char ecc_byte              = 0;
    unsigned int loop_num               = 0;
    unsigned int loop_cnt               = 0;
    unsigned int ecc_idx                = 0;
    unsigned int byte_idx               = 0;
    unsigned int upper, lower;
#ifdef ECC_ERR_TEST
    unsigned int err_addr[3]            = {0x00000000, 0x00200000, 0x00210000};
    unsigned int t_idx;
#endif

    ecc_buf = (unsigned char*)malloc(ECC_DATA_BLOCK);
    if(!ecc_buf) {
        printf("[%s: %d] Low memory(cannot allocate memory for verify)\n", __func__, __LINE__);
        return ret;
    }
    else {
        loop_num = data_len / ECC_DATA_BLOCK;
        ecc_idx = ecc_table_addr;
		loop_cnt = 0;

		while(loop_cnt < loop_num) {
			memset(ecc_buf, 0x00, ECC_DATA_BLOCK);
			memcpy((void *)ecc_buf, (const void *)(rom_buf + (loop_cnt * ECC_DATA_BLOCK)), ECC_DATA_BLOCK);
			ecc_byte = 0;
			for( byte_idx = 0 ; (byte_idx << 2) < ECC_DATA_BLOCK ; byte_idx += 2 ) {
				lower = *(unsigned int *)(ecc_buf + (byte_idx << 2));
				upper = *(unsigned int *)(ecc_buf + ((byte_idx + 1) << 2));
#ifdef ECC_ERR_TEST
				for(t_idx = 0; t_idx < 3; t_idx++) {
					if(loop_cnt * ECC_DATA_BLOCK + (4 * byte_idx) == err_addr[t_idx]) {
						printf("[ADDR : 0x%08X] read data: 0x%08X \t", err_addr[t_idx], lower);
						if(t_idx == 0) {
							lower ^= (0x01 << (t_idx + 1) * 8);
						}
						else {
							lower ^= (0x01 << (t_idx + 1) * 8);
							lower ^= (0x01 << (t_idx) * 4);
						}
						printf("change : 0x%08X\n", lower);
					}
					else if(loop_cnt * ECC_DATA_BLOCK + (4 * (byte_idx + 1)) == err_addr[t_idx]) {
						printf("[ADDR : 0x%08X] read data: 0x%08X \t", err_addr[t_idx], upper);
						if(t_idx == 0) {
							upper ^= (0x01 << (t_idx + 1) * 8);
						}
						else {
							upper ^= (0x01 << (t_idx + 1) * 8);
							upper ^= (0x01 << (t_idx) * 4);
						}
						printf("change : 0x%08X\n", upper);
					}
				}
#endif
				gen_parity(upper, lower, &ecc_byte);
				rom_buf[ecc_idx++] = ecc_byte;
			}

			loop_cnt++;
		}

		if(loop_cnt < loop_num) {
			printf("Fail ECC calculation\n");
		}
		else {
			printf("Complete ECC calculation\n");
			ret = 0;
		}

		free(ecc_buf);
	}

	return ret;
}

BOOL write_sfmc_init_header(FILE *dest_fd, unsigned int snor_size)
{
	unsigned char *headers_buf;

    if (dest_fd) {
		//=========================================
		// Prepare: Header buffer
		//=========================================
		headers_buf = malloc(SFMC_INIT_HEAD_SIZE * 2);
		if (!headers_buf) {
			printf("[%s: %d] Low memory(cannot allocate memory for verify)\n", __func__, __LINE__);
			return FALSE;
		}

        memset(headers_buf, 0xFF, SFMC_INIT_HEAD_SIZE * 2);


		//=========================================
		// Make
		//=========================================
		if (SNOR_MIO_BOOT_Write_Header((unsigned char *)headers_buf, snor_size) != 0)
			return FALSE;

		fseek(dest_fd, SFMC_INIT_HEAD0_OFFSET, SEEK_SET);
		if (fwrite(headers_buf, 1, SFMC_INIT_HEAD_SIZE * 2, dest_fd) != (SFMC_INIT_HEAD_SIZE * 2)) {
			free(headers_buf);
			printf("%s - file write fail\n", __func__);
			return FALSE;
		} else {
			free(headers_buf);
			printf("%s - success\n", __func__);
			return TRUE;
		}
    }
    return FALSE;
}

BOOL write_master_certificate(FILE *dest_fd, FILE *mcert_bin_fd, unsigned int *mcert_size)
{
    unsigned int len = 0;
    unsigned char *mcert_area_buf;
	BOOL ret = FALSE;

	printf("\n");
	printf("\x1b[1;32m<<SNOR_MAP: 0x%08x ++0x%08x>>\x1b[0m\n", HSM_MCERT_AREA0_OFFSET, HSM_MCERT_AREA_SIZE*2);
	printf("[Write Master Certificate...]\n");

	mcert_area_buf = malloc(HSM_MCERT_AREA_SIZE);
	if (!mcert_area_buf) {
		printf("[%s: %d] Low memory(cannot allocate memory for verify)\n", __func__, __LINE__);
		return FALSE;
	}
	memset(mcert_area_buf, 0xFF, HSM_MCERT_AREA_SIZE);

	fseek(mcert_bin_fd, 0, SEEK_END);
	len = ftell(mcert_bin_fd);
	if (len > HSM_MCERT_AREA_SIZE) {
		printf("The file size is larger than area size - write fail\n");
		free(mcert_area_buf);
		return FALSE;
	}
//	*mcert_size = len;

	fseek(mcert_bin_fd, 0, SEEK_SET);
	fread(mcert_area_buf, 1, len , mcert_bin_fd);

	fseek(dest_fd, HSM_MCERT_AREA0_OFFSET, SEEK_SET);
	if (fwrite(mcert_area_buf, 1, HSM_MCERT_AREA_SIZE, dest_fd) != HSM_MCERT_AREA_SIZE) {
		free(mcert_area_buf);
		printf("%s - 0 write fail\n", __func__);
		return FALSE;
	}

	fseek(dest_fd, HSM_MCERT_AREA1_OFFSET, SEEK_SET);
	if (fwrite(mcert_area_buf, 1, HSM_MCERT_AREA_SIZE, dest_fd) != HSM_MCERT_AREA_SIZE) {
		printf("%s - 1 write fail\n", __func__);
	}
	else {
		printf("%s - success\n", __func__);
		ret = TRUE;
	}

	free(mcert_area_buf);

	return ret;
}

BOOL write_hsm_image(FILE *dest_fd, FILE *hsm_bin_fd, unsigned int *hsm_size)
{
	unsigned int len = 0;
	unsigned char *hsm_area_buf;
	BOOL ret = FALSE;

	printf("\n");
	printf("\x1b[1;32m<<SNOR_MAP: 0x%08x ++0x%08x>>\x1b[0m\n", HSM_AREA0_OFFSET, HSM_AREA_SIZE*2);
	printf("[Write HSM F/W Image ...]\n");

	hsm_area_buf = malloc(HSM_AREA_SIZE);
	if (!hsm_area_buf) {
		printf("[%s: %d] Low memory(cannot allocate memory for verify)\n", __func__, __LINE__);
		return FALSE;
	}
	memset(hsm_area_buf, 0xff, HSM_AREA_SIZE);

	fseek(hsm_bin_fd, 0, SEEK_END);
	len = ftell(hsm_bin_fd);
	if (len > HSM_AREA_SIZE) {
		printf("The file size is larger than area size - write fail\n");
		free(hsm_area_buf);
		return FALSE;
	}
	*hsm_size = len;

	fseek(hsm_bin_fd, 0, SEEK_SET);
	fread(hsm_area_buf, 1, len , hsm_bin_fd);

	fseek(dest_fd, HSM_AREA0_OFFSET, SEEK_SET);
	if (fwrite(hsm_area_buf, 1, HSM_AREA_SIZE, dest_fd) != HSM_AREA_SIZE) {
		free(hsm_area_buf);
		printf("%s - 0 write fail\n", __func__);
		return FALSE;
	}

	fseek(dest_fd, HSM_AREA1_OFFSET, SEEK_SET);
	if (fwrite(hsm_area_buf, 1, HSM_AREA_SIZE, dest_fd) != HSM_AREA_SIZE) {
		printf("%s - 1 write fail\n", __func__);
	}
	else {
		printf("%s - success\n", __func__);
		ret = TRUE;
	}

	free(hsm_area_buf);

	return ret;
}

BOOL write_r5_bl1_image(FILE *dest_fd, FILE *r5bl1_bin_fd, unsigned int *r5bl1_size)
{
    unsigned int len = 0;
    unsigned char *bl1_area_buf;
	BOOL ret = FALSE;

	printf("\n");
	printf("\x1b[1;32m<<SNOR_MAP: 0x%08x ++0x%08x>>\x1b[0m\n", R5_BL1_AREA0_OFFSET, R5_BL1_AREA_SIZE*2);
	printf("[Write R5-BL1 Image ...]\n");

	bl1_area_buf = malloc(R5_BL1_AREA_SIZE);
	if (!bl1_area_buf) {
		printf("[%s: %d] Low memory(cannot allocate memory for verify)\n", __func__, __LINE__);
		return FALSE;
	}
	memset(bl1_area_buf, 0xff, R5_BL1_AREA_SIZE);

	fseek(r5bl1_bin_fd, 0, SEEK_END);
	len = ftell(r5bl1_bin_fd);
	if (len > R5_BL1_AREA_SIZE) {
		printf("The file size is larger than area size - write fail\n");
		free(bl1_area_buf);
		return FALSE;
	}
	*r5bl1_size = len;

	fseek(r5bl1_bin_fd, 0, SEEK_SET);
	fread(bl1_area_buf, 1, len , r5bl1_bin_fd);

	fseek(dest_fd, R5_BL1_AREA0_OFFSET, SEEK_SET);
	if(fwrite(bl1_area_buf, 1, R5_BL1_AREA_SIZE, dest_fd) != R5_BL1_AREA_SIZE) {
		free(bl1_area_buf);
		printf("%s - file write fail\n", __func__);
		return FALSE;
	}

	fseek(dest_fd, R5_BL1_AREA1_OFFSET, SEEK_SET);
	if(fwrite(bl1_area_buf, 1, R5_BL1_AREA_SIZE, dest_fd) != R5_BL1_AREA_SIZE) {
		printf("%s - file write fail\n", __func__);
	}
	else {
		printf("%s - success\n", __func__);
		return TRUE;
	}

	free(bl1_area_buf);

	return ret;
}

BOOL write_micom_sub_fw_image(FILE *dest_fd, FILE *update_bin_fd, unsigned int *updater_size)
{
	unsigned int image_size = 0;
	unsigned char *micom_sub_img_buf;
	unsigned char *micom_sub_area_buf;

	printf("\n");
	printf("\x1b[1;32m<<SNOR_MAP: 0x%08x ++0x%08x>>\x1b[0m\n", MICOM_SUB_FW_HEADER_OFFSET, MICOM_SUB_FW_AREA_SIZE);
	printf("[Write Micom SubFW Image ...]\n");

    if (dest_fd && update_bin_fd) {

		fseek(update_bin_fd, 0, SEEK_END);
		image_size = ftell(update_bin_fd);
		micom_sub_img_buf = malloc(image_size);
		if (!micom_sub_img_buf) {
			printf("[%s: %d] Low memory(cannot allocate memory for verify)\n", __func__, __LINE__);
			return FALSE;
		}
		else {
			memset(micom_sub_img_buf, 0xff, image_size);
		}

		fseek(update_bin_fd, 0, SEEK_SET);
		fread(micom_sub_img_buf, 1, image_size, update_bin_fd);


		printf("MICOM Sub f/w size: 0x%x\n", image_size);
		printf("MICOM Sub f/w target addr: 0x%08x\n", MICOM_SUB_FW_IMAGE_OFFSET);
		micom_sub_area_buf = malloc(MICOM_SUB_FW_AREA_SIZE);
		if (!micom_sub_area_buf) {
			printf("[%s: %d] Low memory(cannot allocate memory for verify)\n", __func__, __LINE__);
			return FALSE;
		}
		else {
			memset(micom_sub_area_buf, 0xFF, MICOM_SUB_FW_AREA_SIZE);
		}

		memcpy(&micom_sub_area_buf[0], (unsigned char *)micom_sub_img_buf, image_size);

        fseek(dest_fd, MICOM_SUB_FW_HEADER_OFFSET, SEEK_SET);
		if (fwrite(micom_sub_area_buf, 1, MICOM_SUB_FW_AREA_SIZE, dest_fd) != MICOM_SUB_FW_AREA_SIZE) {
			free(micom_sub_img_buf);
			free(micom_sub_area_buf);
			printf("%s - file write fail\n", __func__);
			return FALSE;
		} else {
			free(micom_sub_img_buf);
			free(micom_sub_area_buf);
			*updater_size = image_size + MICOM_SUB_FW_HEADER_SIZE;
			printf("%s - success\n", __func__);
			return TRUE;
		}

    }
    return FALSE;
}

BOOL write_micom_rom(FILE *dest_fd, FILE *micom_bin_fd, unsigned int *micom_size, unsigned int secured)
{
	unsigned int len = 0;
	unsigned char *micom_rom_header_buf;

	printf("\n");
	printf("\x1b[1;32m<<SNOR_MAP: 0x%08x ++0x%08x>>\x1b[0m\n", MICOM_HEADER_0_OFFSET, MICOM_ROM_AREA_SIZE*2);
	printf("[Write %s Micom FW Image ...]\n", secured? "Secure": "Non-Secure");

    if (dest_fd && micom_bin_fd) {

		fseek(micom_bin_fd, 0, SEEK_END);
		len = ftell(micom_bin_fd);
		printf("MICOM ROM size: 0x%x\n", len);
		micom_rom_header_buf = malloc(len);
		if (!micom_rom_header_buf) {
			printf("[%s: %d] Low memory(cannot allocate memory for verify)\n", __func__, __LINE__);
			return FALSE;
		}

		fseek(micom_bin_fd, 0, SEEK_SET);
		fread(micom_rom_header_buf, 1, len, micom_bin_fd);


		/* Non-Secure image has no header */
		if (secured)
			fseek(dest_fd, MICOM_HEADER_0_OFFSET, SEEK_SET);
		else
			fseek(dest_fd, MICOM_HEADER_0_OFFSET + MICOM_ROM_HEADER_SIZE, SEEK_SET);

		if (fwrite(micom_rom_header_buf, 1, len, dest_fd) != len) {
			free(micom_rom_header_buf);
			printf("%s - file write fail\n", __func__);
			return FALSE;
		}
#if defined(INCLUDE_SECONDARY_R5_FW)
		if (secured)
			fseek(dest_fd, MICOM_HEADER_1_OFFSET, SEEK_SET);
		else
			fseek(dest_fd, MICOM_HEADER_1_OFFSET + MICOM_ROM_HEADER_SIZE, SEEK_SET);

		if (fwrite(micom_rom_header_buf, 1, len, dest_fd) != len) {
			free(micom_rom_header_buf);
			printf("%s - file write fail\n", __func__);
			return FALSE;
		} else {
			free(micom_rom_header_buf);
			*micom_size = len;
			printf("%s - success\n", __func__);
			return TRUE;
		}
#else
		*micom_size = len;
		return TRUE;
#endif

    }

    return FALSE;
}

BOOL write_rom_header(FILE *dest_fd, unsigned int lun, snor_rom_info_t *snor_info)
{
    if (dest_fd) {
        unsigned char *rom_header_buf;

		if (lun == 0) {
			printf("\n");
			printf("\x1b[1;32m<<SNOR_MAP: 0x%08x ++0x%08x>>\x1b[0m\n", SNOR_ROM_HEADER_OFFSET, SNOR_ROM_HEADER_SIZE*2);
			printf("[Make SNOR ROM Header...]\n");
		}

		rom_header_buf = malloc(SNOR_ROM_HEADER_SIZE);
		if (!rom_header_buf) {
			printf("[%s: %d] Low memory(cannot allocate memory for verify)\n", __func__, __LINE__);
			return FALSE;
		}
		memset(rom_header_buf, 0xff, SNOR_ROM_HEADER_SIZE);


		snor_info->rom_id = SNOR_ROM_ID;
		snor_info->crc = FWUG_CalcCrc8((unsigned char*)(snor_info), sizeof(sSFQPI_InitHeader) - 4);

        printf("SNOR ROM Header CRC: 0x%08X\n", snor_info->crc);

		memcpy(rom_header_buf, snor_info, sizeof(snor_rom_info_t));


		if (lun == 0)
			fseek(dest_fd, SNOR_ROM_HEADER_OFFSET, SEEK_SET);
		else
			fseek(dest_fd, SNOR_ROM_HEADER_OFFSET + SNOR_ROM_HEADER_SIZE, SEEK_SET);

		if (fwrite(rom_header_buf, 1, SNOR_ROM_HEADER_SIZE, dest_fd) != SNOR_ROM_HEADER_SIZE) {
			free(rom_header_buf);
			printf("%s - file write fail\n", __func__);
			return FALSE;
		} else {
			free(rom_header_buf);
			printf("%s - success\n", __func__);
			return TRUE;
		}
    }
    return FALSE;
}

BOOL create_final_rom(FILE *out_rom_fd, unsigned int snor_size)
{
	unsigned char *rom_buf;
	unsigned int data_len;
	unsigned int out_rom_size;
	size_t read_size = 0;

	out_rom_size = (snor_size * 1024 * 1024);

	fseek(out_rom_fd, 0, SEEK_END);
	data_len = ftell(out_rom_fd);
	fseek(out_rom_fd, 0, SEEK_SET);

	if (ecc_table_addr) {
		if (ecc_table_addr < data_len) {
			printf("[%s: %d] Error: The data size exceeded the maximum size.\n", __func__, __LINE__);
			printf("Data size: 0x%X Maximum size(without ECC size): 0x%X\n", data_len, ecc_table_addr);
			return FALSE;
		}
	}
	else {
		if (out_rom_size < data_len) {
			printf("[%s: %d] Error: The data size exceeded the SNOR size.\n", __func__, __LINE__);
			return FALSE;
		}
	}

	rom_buf = malloc(out_rom_size);
	if (!rom_buf) {
		printf("[%s: %d] Low memory(cannot allocate memory for verify)\n", __func__, __LINE__);
		return FALSE;
	}
	memset(rom_buf, 0xff, out_rom_size);

	read_size = fread(rom_buf, 1, data_len, out_rom_fd);
	if (read_size != data_len) {
		printf("[%s: %d] File read error\n", __func__, __LINE__);
		free(rom_buf);
		return FALSE;
	}

	if (ecc_table_addr) {
		if (fill_ecc_data(rom_buf, data_len)) {
			printf("[%s: %d] Error: Fail to generate ECC table.\n", __func__, __LINE__);
			free(rom_buf);
			return FALSE;
		}
	}

	printf("Total Image Size: %d byte\n", (unsigned int)(out_rom_size));

	fseek(out_rom_fd, 0, SEEK_SET);

	if (fwrite(rom_buf, 1, out_rom_size, out_rom_fd) != out_rom_size) {
		free(rom_buf);
		printf("%s - file write fail\n", __func__);
		return FALSE;
	} else {
		free(rom_buf);
		printf("%s - success\n", __func__);
		return TRUE;
	}

	return FALSE;
}
