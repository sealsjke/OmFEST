section .text
global xor_with_prev

xor_with_prev:
    test rdx, rdx
    jz .done

    xor ecx, ecx              ; prev = 0

.loop:
    movzx eax, byte [rdi]     ; b = *in
    mov r8d, ecx
    add r8d, 0x19
    and r8d, 0xFF             ; (prev + 0x19) & 0xFF
    xor r8d, eax              ; b ^ ((prev + 0x19) & 0xFF)
    mov [rsi], r8b            ; *out = result

    mov ecx, eax              ; prev = b

    inc rdi
    inc rsi
    dec rdx
    jnz .loop

.done:
    ret

section .note.GNU-stack noalloc noexec nowrite progbits
