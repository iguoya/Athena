	.file	"fn.c"
	.text
	.globl	c_sum                           // -- Begin function c_sum
	.p2align	2
	.type	c_sum,@function
c_sum:                                  // @c_sum
// %bb.0:
	sub	sp, sp, #32
	str	x0, [sp, #24]
	str	w1, [sp, #20]
	str	wzr, [sp, #16]
	str	wzr, [sp, #12]
	b	.LBB0_1
.LBB0_1:                                // =>This Inner Loop Header: Depth=1
	ldr	w8, [sp, #12]
	ldr	w9, [sp, #20]
	subs	w8, w8, w9
	b.lt	.LBB0_2
	b	.LBB0_4
.LBB0_2:                                //   in Loop: Header=BB0_1 Depth=1
	ldr	x8, [sp, #24]
	ldrsw	x9, [sp, #12]
	ldr	w9, [x8, x9, lsl #2]
	ldr	w8, [sp, #16]
	add	w8, w8, w9
	str	w8, [sp, #16]
	b	.LBB0_3
.LBB0_3:                                //   in Loop: Header=BB0_1 Depth=1
	ldr	w8, [sp, #12]
	add	w8, w8, #1
	str	w8, [sp, #12]
	b	.LBB0_1
.LBB0_4:
	ldr	w0, [sp, #16]
	add	sp, sp, #32
	ret
.Lfunc_end0:
	.size	c_sum, .Lfunc_end0-c_sum
                                        // -- End function
	.section	".note.GNU-stack","",@progbits
	.addrsig
