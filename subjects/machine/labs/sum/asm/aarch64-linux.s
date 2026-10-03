// AArch64 (Linux, AAPCS64)。
//
// 调用约定：第 1 个整数参数在 x0，第 2 个在 w1，返回值在 w0。
// 对应 C：int asm_sum(const int *a, int n)
        .text
        .globl  asm_sum
        .type   asm_sum, %function
asm_sum:
        mov     w2, #0                  // sum = 0
        mov     w3, #0                  // i = 0
        b       .Lcheck
.Lloop:
        ldr     w4, [x0, w3, uxtw #2]   // w4 = a[i]
        add     w2, w2, w4              // sum += a[i]
        add     w3, w3, #1              // i++
.Lcheck:
        cmp     w3, w1                  // i < n ?
        b.lt    .Lloop
        mov     w0, w2
        ret
        .size   asm_sum, .-asm_sum
        .section .note.GNU-stack,"",@progbits
