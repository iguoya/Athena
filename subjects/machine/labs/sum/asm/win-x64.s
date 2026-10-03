# Windows x64 (Microsoft ABI)，Intel 语法（ADR 0007：win-x64 的默认语法）。
#
# 调用约定：第 1 个整数参数在 rcx，第 2 个在 edx，返回值在 eax。
# 对应 C：int asm_sum(const int *a, int n)
        .intel_syntax noprefix
        .text
        .globl  asm_sum
asm_sum:
        xor     eax, eax                # sum = 0
        xor     r8d, r8d                # i = 0
        jmp     .Lcheck
.Lloop:
        add     eax, dword ptr [rcx + r8*4]     # sum += a[i]
        inc     r8d                     # i++
.Lcheck:
        cmp     r8d, edx                # i < n ?
        jl      .Lloop
        ret
