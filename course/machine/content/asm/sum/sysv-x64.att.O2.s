	.att_syntax
	.file	"fn.c"
	.text
	.globl	c_sum                           # -- Begin function c_sum
	.prefalign	4, .Lfunc_end0, nop
	.type	c_sum,@function
c_sum:                                  # @c_sum
# %bb.0:
	testl	%esi, %esi
	jle	.LBB0_1
# %bb.2:
	movl	%esi, %ecx
	cmpl	$8, %esi
	jae	.LBB0_4
# %bb.3:
	xorl	%edx, %edx
	xorl	%eax, %eax
	jmp	.LBB0_7
.LBB0_1:
	xorl	%eax, %eax
	retq
.LBB0_4:
	movl	%ecx, %edx
	andl	$2147483640, %edx               # imm = 0x7FFFFFF8
	movl	%ecx, %eax
	shrl	$3, %eax
	andl	$268435455, %eax                # imm = 0xFFFFFFF
	shlq	$5, %rax
	pxor	%xmm0, %xmm0
	xorl	%esi, %esi
	pxor	%xmm1, %xmm1
	.p2align	4
.LBB0_5:                                # =>This Inner Loop Header: Depth=1
	movdqu	(%rdi,%rsi), %xmm2
	paddd	%xmm2, %xmm1
	movdqu	16(%rdi,%rsi), %xmm2
	paddd	%xmm2, %xmm0
	addq	$32, %rsi
	cmpq	%rsi, %rax
	jne	.LBB0_5
# %bb.6:
	paddd	%xmm1, %xmm0
	pshufd	$238, %xmm0, %xmm1              # xmm1 = xmm0[2,3,2,3]
	paddd	%xmm0, %xmm1
	pshufd	$85, %xmm1, %xmm0               # xmm0 = xmm1[1,1,1,1]
	paddd	%xmm1, %xmm0
	movd	%xmm0, %eax
	cmpl	%ecx, %edx
	je	.LBB0_8
	.p2align	4
.LBB0_7:                                # =>This Inner Loop Header: Depth=1
	addl	(%rdi,%rdx,4), %eax
	incq	%rdx
	cmpq	%rdx, %rcx
	jne	.LBB0_7
.LBB0_8:
	retq
.Lfunc_end0:
	.size	c_sum, .Lfunc_end0-c_sum
                                        # -- End function
	.section	".note.GNU-stack","",@progbits
	.addrsig
