	.intel_syntax noprefix
	.file	"fn.c"
	.text
	.globl	c_sum                           # -- Begin function c_sum
	.prefalign	4, .Lfunc_end0, nop
	.type	c_sum,@function
c_sum:                                  # @c_sum
# %bb.0:
	test	esi, esi
	jle	.LBB0_1
# %bb.2:
	mov	ecx, esi
	cmp	esi, 8
	jae	.LBB0_4
# %bb.3:
	xor	edx, edx
	xor	eax, eax
	jmp	.LBB0_7
.LBB0_1:
	xor	eax, eax
	ret
.LBB0_4:
	mov	edx, ecx
	and	edx, 2147483640
	mov	eax, ecx
	shr	eax, 3
	and	eax, 268435455
	shl	rax, 5
	pxor	xmm0, xmm0
	xor	esi, esi
	pxor	xmm1, xmm1
	.p2align	4
.LBB0_5:                                # =>This Inner Loop Header: Depth=1
	movdqu	xmm2, xmmword ptr [rdi + rsi]
	paddd	xmm1, xmm2
	movdqu	xmm2, xmmword ptr [rdi + rsi + 16]
	paddd	xmm0, xmm2
	add	rsi, 32
	cmp	rax, rsi
	jne	.LBB0_5
# %bb.6:
	paddd	xmm0, xmm1
	pshufd	xmm1, xmm0, 238                 # xmm1 = xmm0[2,3,2,3]
	paddd	xmm1, xmm0
	pshufd	xmm0, xmm1, 85                  # xmm0 = xmm1[1,1,1,1]
	paddd	xmm0, xmm1
	movd	eax, xmm0
	cmp	edx, ecx
	je	.LBB0_8
	.p2align	4
.LBB0_7:                                # =>This Inner Loop Header: Depth=1
	add	eax, dword ptr [rdi + 4*rdx]
	inc	rdx
	cmp	rcx, rdx
	jne	.LBB0_7
.LBB0_8:
	ret
.Lfunc_end0:
	.size	c_sum, .Lfunc_end0-c_sum
                                        # -- End function
	.section	".note.GNU-stack","",@progbits
	.addrsig
