	.def	@feat.00;
	.scl	3;
	.type	0;
	.endef
	.globl	@feat.00
@feat.00 = 0
	.att_syntax
	.file	"fn.c"
	.def	c_sum;
	.scl	2;
	.type	32;
	.endef
	.text
	.globl	c_sum                           # -- Begin function c_sum
	.p2align	4
c_sum:                                  # @c_sum
# %bb.0:
	testl	%edx, %edx
	jle	.LBB0_1
# %bb.2:
	movl	%edx, %r8d
	cmpl	$8, %edx
	jae	.LBB0_4
# %bb.3:
	xorl	%edx, %edx
	xorl	%eax, %eax
	jmp	.LBB0_7
.LBB0_1:
	xorl	%eax, %eax
	retq
.LBB0_4:
	movl	%r8d, %edx
	andl	$2147483640, %edx               # imm = 0x7FFFFFF8
	movl	%r8d, %eax
	shrl	$3, %eax
	andl	$268435455, %eax                # imm = 0xFFFFFFF
	shlq	$5, %rax
	pxor	%xmm0, %xmm0
	xorl	%r9d, %r9d
	pxor	%xmm1, %xmm1
	.p2align	4
.LBB0_5:                                # =>This Inner Loop Header: Depth=1
	movdqu	(%rcx,%r9), %xmm2
	paddd	%xmm2, %xmm1
	movdqu	16(%rcx,%r9), %xmm2
	paddd	%xmm2, %xmm0
	addq	$32, %r9
	cmpq	%r9, %rax
	jne	.LBB0_5
# %bb.6:
	paddd	%xmm1, %xmm0
	pshufd	$238, %xmm0, %xmm1              # xmm1 = xmm0[2,3,2,3]
	paddd	%xmm0, %xmm1
	pshufd	$85, %xmm1, %xmm0               # xmm0 = xmm1[1,1,1,1]
	paddd	%xmm1, %xmm0
	movd	%xmm0, %eax
	cmpl	%r8d, %edx
	je	.LBB0_8
	.p2align	4
.LBB0_7:                                # =>This Inner Loop Header: Depth=1
	addl	(%rcx,%rdx,4), %eax
	incq	%rdx
	cmpq	%rdx, %r8
	jne	.LBB0_7
.LBB0_8:
	retq
                                        # -- End function
	.section	.debug$S,"dr"
	.p2align	2, 0x0
	.long	4                               # Debug section magic
	.long	241
	.long	.Ltmp1-.Ltmp0                   # Subsection size
.Ltmp0:
	.short	.Ltmp3-.Ltmp2                   # Record length
.Ltmp2:
	.short	4353                            # Record kind: S_OBJNAME
	.long	0                               # Signature
	.byte	0                               # Object name
	.p2align	2, 0x0
.Ltmp3:
	.short	.Ltmp5-.Ltmp4                   # Record length
.Ltmp4:
	.short	4412                            # Record kind: S_COMPILE3
	.long	0                               # Flags and language
	.short	208                             # CPUType
	.short	0                               # Frontend version
	.short	0
	.short	0
	.short	0
	.short	23011                           # Backend version
	.short	0
	.short	0
	.short	0
	.byte	0                               # Null-terminated compiler version string
	.p2align	2, 0x0
.Ltmp5:
.Ltmp1:
	.p2align	2, 0x0
	.addrsig
