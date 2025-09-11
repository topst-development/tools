#ifndef _ECC_H_
#define _ECC_H_

#include <stdlib.h>
#include <stdint.h>
#include <stdio.h>

#define ECC_DATA_BLOCK (64UL)

void gen_parity (uint32_t upper, uint32_t lower, uint8_t *ecc);

#endif
