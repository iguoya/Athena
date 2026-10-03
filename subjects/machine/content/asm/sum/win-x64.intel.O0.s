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
	sub	rsp, 24
	mov	dword ptr [rsp + 20], edx
	mov	qword ptr [rsp + 8], rcx
	mov	dword ptr [rsp + 4], 0
	mov	dword ptr [rsp], 0
.LBB0_1:                                # =>This Inner Loop Header: Depth=1
	mov	eax, dword ptr [rsp]
	cmp	eax, dword ptr [rsp + 20]
	jge	.LBB0_4
# %bb.2:                                #   in Loop: Header=BB0_1 Depth=1
	mov	rax, qword ptr [rsp + 8]
	movsxd	rcx, dword ptr [rsp]
	mov	eax, dword ptr [rax + 4*rcx]
	add	eax, dword ptr [rsp + 4]
	mov	dword ptr [rsp + 4], eax
# %bb.3:                                #   in Loop: Header=BB0_1 Depth=1
	mov	eax, dword ptr [rsp]
	add	eax, 1
	mov	dword ptr [rsp], eax
	jmp	.LBB0_1
.LBB0_4:
	mov	eax, dword ptr [rsp + 4]
	add	rsp, 24
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
