	.file	"fn.c"
	.text
	.globl	c_sum                           // -- Begin function c_sum
	.p2align	2
	.type	c_sum,@function
c_sum:                                  // @c_sum
// %bb.0:
	cmp	w1, #1
	b.lt	.LBB0_3
// %bb.1:
	cmp	w1, #4
	mov	w9, w1
	b.hs	.LBB0_4
// %bb.2:
	mov	x10, xzr
	mov	w8, wzr
	b	.LBB0_13
.LBB0_3:
	mov	w8, wzr
	mov	w0, w8
	ret
.LBB0_4:
	cmp	w1, #16
	b.hs	.LBB0_6
// %bb.5:
	mov	x10, xzr
	mov	w8, wzr
	b	.LBB0_10
.LBB0_6:
	movi	v0.2d, #0000000000000000
	movi	v1.2d, #0000000000000000
	and	x11, x9, #0xc
	movi	v2.2d, #0000000000000000
	movi	v3.2d, #0000000000000000
	and	x10, x9, #0x7ffffff0
	add	x8, x0, #32
	and	x12, x9, #0x7ffffff0
.LBB0_7:                                // =>This Inner Loop Header: Depth=1
	ldp	q4, q5, [x8, #-32]
	subs	x12, x12, #16
	ldp	q6, q7, [x8], #64
	add	v0.4s, v4.4s, v0.4s
	add	v1.4s, v5.4s, v1.4s
	add	v2.4s, v6.4s, v2.4s
	add	v3.4s, v7.4s, v3.4s
	b.ne	.LBB0_7
// %bb.8:
	add	v0.4s, v1.4s, v0.4s
	cmp	x10, x9
	add	v0.4s, v2.4s, v0.4s
	add	v0.4s, v3.4s, v0.4s
	addv	s0, v0.4s
	fmov	w8, s0
	b.eq	.LBB0_15
// %bb.9:
	cbz	x11, .LBB0_13
.LBB0_10:
	movi	v0.2d, #0000000000000000
	mov	x11, x10
	and	x10, x9, #0x7ffffffc
	mov	v0.s[0], w8
	add	x8, x0, x11, lsl #2
	sub	x11, x11, x10
.LBB0_11:                               // =>This Inner Loop Header: Depth=1
	ldr	q1, [x8], #16
	adds	x11, x11, #4
	add	v0.4s, v1.4s, v0.4s
	b.ne	.LBB0_11
// %bb.12:
	addv	s0, v0.4s
	cmp	x10, x9
	fmov	w8, s0
	b.eq	.LBB0_15
.LBB0_13:
	add	x11, x0, x10, lsl #2
	sub	x9, x9, x10
.LBB0_14:                               // =>This Inner Loop Header: Depth=1
	ldr	w10, [x11], #4
	subs	x9, x9, #1
	add	w8, w10, w8
	b.ne	.LBB0_14
.LBB0_15:
	mov	w0, w8
	ret
.Lfunc_end0:
	.size	c_sum, .Lfunc_end0-c_sum
                                        // -- End function
	.section	".note.GNU-stack","",@progbits
	.addrsig
