	.att_syntax
	.file	"fn.c"
	.text
	.globl	c_sum                           # -- Begin function c_sum
	.prefalign	4, .Lfunc_end0, nop
	.type	c_sum,@function
c_sum:                                  # @c_sum
# %bb.0:
	pushq	%rbp
	movq	%rsp, %rbp
	movq	%rdi, -8(%rbp)
	movl	%esi, -12(%rbp)
	movl	$0, -16(%rbp)
	movl	$0, -20(%rbp)
.LBB0_1:                                # =>This Inner Loop Header: Depth=1
	movl	-20(%rbp), %eax
	cmpl	-12(%rbp), %eax
	jge	.LBB0_4
# %bb.2:                                #   in Loop: Header=BB0_1 Depth=1
	movq	-8(%rbp), %rax
	movslq	-20(%rbp), %rcx
	movl	(%rax,%rcx,4), %eax
	addl	-16(%rbp), %eax
	movl	%eax, -16(%rbp)
# %bb.3:                                #   in Loop: Header=BB0_1 Depth=1
	movl	-20(%rbp), %eax
	addl	$1, %eax
	movl	%eax, -20(%rbp)
	jmp	.LBB0_1
.LBB0_4:
	movl	-16(%rbp), %eax
	popq	%rbp
	retq
.Lfunc_end0:
	.size	c_sum, .Lfunc_end0-c_sum
                                        # -- End function
	.section	".note.GNU-stack","",@progbits
	.addrsig
