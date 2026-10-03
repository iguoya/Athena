# System V x86-64 (Linux)，AT&T 语法（ADR 0007：sysv-x64 的默认语法）。
#
# 调用约定：第 1 个整数参数在 rdi，第 2 个在 esi，返回值在 eax。
# 对应 C：int asm_sum(const int *a, int n)
        .text
        .globl  asm_sum
        .type   asm_sum, @function
asm_sum:
        xorl    %eax, %eax              # sum = 0
        xorl    %ecx, %ecx              # i = 0
        jmp     .Lcheck
.Lloop:
        addl    (%rdi,%rcx,4), %eax     # sum += a[i]
        incl    %ecx                    # i++
.Lcheck:
        cmpl    %esi, %ecx              # i < n ?
        jl      .Lloop
        ret
        .size   asm_sum, .-asm_sum
        .section .note.GNU-stack,"",@progbits
