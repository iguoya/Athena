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
	subq	$24, %rsp
	movl	%edx, 20(%rsp)
	movq	%rcx, 8(%rsp)
	movl	$0, 4(%rsp)
	movl	$0, (%rsp)
.LBB0_1:                                # =>This Inner Loop Header: Depth=1
	movl	(%rsp), %eax
	cmpl	20(%rsp), %eax
	jge	.LBB0_4
# %bb.2:                                #   in Loop: Header=BB0_1 Depth=1
	movq	8(%rsp), %rax
	movslq	(%rsp), %rcx
	movl	(%rax,%rcx,4), %eax
	addl	4(%rsp), %eax
	movl	%eax, 4(%rsp)
# %bb.3:                                #   in Loop: Header=BB0_1 Depth=1
	movl	(%rsp), %eax
	addl	$1, %eax
	movl	%eax, (%rsp)
	jmp	.LBB0_1
.LBB0_4:
	movl	4(%rsp), %eax
	addq	$24, %rsp
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
