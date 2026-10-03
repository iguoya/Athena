	.def	@feat.00;
	.scl	3;
	.type	0;
	.endef
	.globl	@feat.00
@feat.00 = 0
	.intel_syntax noprefix
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
	test	edx, edx
	jle	.LBB0_1
# %bb.2:
	mov	r8d, edx
	cmp	edx, 8
	jae	.LBB0_4
# %bb.3:
	xor	edx, edx
	xor	eax, eax
	jmp	.LBB0_7
.LBB0_1:
	xor	eax, eax
	ret
.LBB0_4:
	mov	edx, r8d
	and	edx, 2147483640
	mov	eax, r8d
	shr	eax, 3
	and	eax, 268435455
	shl	rax, 5
	pxor	xmm0, xmm0
	xor	r9d, r9d
	pxor	xmm1, xmm1
	.p2align	4
.LBB0_5:                                # =>This Inner Loop Header: Depth=1
	movdqu	xmm2, xmmword ptr [rcx + r9]
	paddd	xmm1, xmm2
	movdqu	xmm2, xmmword ptr [rcx + r9 + 16]
	paddd	xmm0, xmm2
	add	r9, 32
	cmp	rax, r9
	jne	.LBB0_5
# %bb.6:
	paddd	xmm0, xmm1
	pshufd	xmm1, xmm0, 238                 # xmm1 = xmm0[2,3,2,3]
	paddd	xmm1, xmm0
	pshufd	xmm0, xmm1, 85                  # xmm0 = xmm1[1,1,1,1]
	paddd	xmm0, xmm1
	movd	eax, xmm0
	cmp	edx, r8d
	je	.LBB0_8
	.p2align	4
.LBB0_7:                                # =>This Inner Loop Header: Depth=1
	add	eax, dword ptr [rcx + 4*rdx]
	inc	rdx
	cmp	r8, rdx
	jne	.LBB0_7
.LBB0_8:
	ret
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
