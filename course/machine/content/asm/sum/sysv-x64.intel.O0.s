	.intel_syntax noprefix
	.file	"fn.c"
	.text
	.globl	c_sum                           # -- Begin function c_sum
	.prefalign	4, .Lfunc_end0, nop
	.type	c_sum,@function
c_sum:                                  # @c_sum
# %bb.0:
	push	rbp
	mov	rbp, rsp
	mov	qword ptr [rbp - 8], rdi
	mov	dword ptr [rbp - 12], esi
	mov	dword ptr [rbp - 16], 0
	mov	dword ptr [rbp - 20], 0
.LBB0_1:                                # =>This Inner Loop Header: Depth=1
	mov	eax, dword ptr [rbp - 20]
	cmp	eax, dword ptr [rbp - 12]
	jge	.LBB0_4
# %bb.2:                                #   in Loop: Header=BB0_1 Depth=1
	mov	rax, qword ptr [rbp - 8]
	movsxd	rcx, dword ptr [rbp - 20]
	mov	eax, dword ptr [rax + 4*rcx]
	add	eax, dword ptr [rbp - 16]
	mov	dword ptr [rbp - 16], eax
# %bb.3:                                #   in Loop: Header=BB0_1 Depth=1
	mov	eax, dword ptr [rbp - 20]
	add	eax, 1
	mov	dword ptr [rbp - 20], eax
	jmp	.LBB0_1
.LBB0_4:
	mov	eax, dword ptr [rbp - 16]
	pop	rbp
	ret
.Lfunc_end0:
	.size	c_sum, .Lfunc_end0-c_sum
                                        # -- End function
	.section	".note.GNU-stack","",@progbits
	.addrsig
